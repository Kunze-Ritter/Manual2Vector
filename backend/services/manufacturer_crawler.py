"""Manufacturer crawling service built on top of WebScrapingService.

This module coordinates scheduled manufacturer website crawls, persistence of
crawled pages, and downstream structured extraction for content discovered via
Firecrawl. It relies on ``krai_system.manufacturer_crawl_*`` tables introduced in
migration 122 and bridges across batch task scheduling, scraping, and
transformation layers.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

try:
    from croniter import croniter
except Exception:
    croniter = None

from .config_service import ConfigService
from .web_scraping_service import FirecrawlUnavailableError, WebScrapingService


class ManufacturerCrawler:
    """High-level coordinator for manufacturer crawling workflows."""

    def __init__(
        self,
        web_scraping_service: WebScrapingService,
        database_service: Any,
        config_service: Optional[ConfigService] = None,
        structured_extraction_service: Optional[Any] = None,
        batch_task_service: Optional[Any] = None,
    ) -> None:
        self._scraper = web_scraping_service
        self._database_service = database_service
        self._config_service = config_service
        self._structured_extraction_service = structured_extraction_service
        self._batch_task_service = batch_task_service
        self._logger = logging.getLogger("krai.services.manufacturer_crawler")

        self._config = self._load_config()
        self._enabled = self._config.get("enable_manufacturer_crawling", False)
        if not self._enabled:
            self._logger.info("Manufacturer crawler initialised but feature flag disabled")

    # ------------------------------------------------------------------
    # Schedule management
    # ------------------------------------------------------------------
    async def create_crawl_schedule(self, manufacturer_id: str, crawl_config: Dict[str, Any]) -> Optional[str]:
        if not self._enabled:
            self._logger.warning("Manufacturer crawling disabled; schedule not created")
            return None

        client = self._get_db_client()
        if client is None:
            return None

        payload = {
            "manufacturer_id": manufacturer_id,
            "crawl_type": crawl_config.get("crawl_type", "full_site"),
            "start_url": crawl_config["start_url"],
            "url_patterns": crawl_config.get("url_patterns"),
            "exclude_patterns": crawl_config.get("exclude_patterns"),
            "max_depth": crawl_config.get("max_depth", self._config.get("default_max_depth", 2)),
            "max_pages": crawl_config.get("max_pages", self._config.get("default_max_pages", 100)),
            "schedule_cron": crawl_config.get("schedule_cron"),
            "enabled": crawl_config.get("enabled", True),
            "crawl_options": crawl_config.get("crawl_options", {}),
            "next_run_at": self._calculate_next_run(crawl_config.get("schedule_cron")),
        }

        try:
            response = (
                client.table("manufacturer_crawl_schedules", schema="krai_system")
                .insert(payload)
                .execute()
            )
            schedule_id = response.data[0]["id"] if response.data else None
            self._logger.info("Created crawl schedule %s for manufacturer %s", schedule_id, manufacturer_id)
            return schedule_id
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.error("Failed to create crawl schedule: %s", exc)
            return None

    async def update_crawl_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        client = self._get_db_client()
        if client is None:
            return False

        if "schedule_cron" in updates:
            updates["next_run_at"] = self._calculate_next_run(updates.get("schedule_cron"))

        try:
            (
                client.table("manufacturer_crawl_schedules", schema="krai_system")
                .update(updates)
                .eq("id", str(schedule_id))
                .execute()
            )
            return True
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.error("Failed to update crawl schedule %s: %s", schedule_id, exc)
            return False

    async def delete_crawl_schedule(self, schedule_id: str) -> bool:
        client = self._get_db_client()
        if client is None:
            return False

        try:
            (
                client.table("manufacturer_crawl_schedules", schema="krai_system")
                .delete()
                .eq("id", str(schedule_id))
                .execute()
            )
            return True
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to delete crawl schedule %s: %s", schedule_id, exc)
            return False

    async def list_crawl_schedules(self, manufacturer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self._get_db_client()
        if client is None:
            return []

        query = client.table("manufacturer_crawl_schedules", schema="krai_system").select("*").order("created_at")
        if manufacturer_id:
            query = query.eq("manufacturer_id", str(manufacturer_id))
        response = query.execute()
        return response.data or []

    async def get_crawl_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        client = self._get_db_client()
        if client is None:
            return None
        response = (
            client.table("manufacturer_crawl_schedules", schema="krai_system")
            .select("*")
            .eq("id", str(schedule_id))
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    # ------------------------------------------------------------------
    # Job lifecycle
    # ------------------------------------------------------------------
    async def start_crawl_job(self, schedule_id: str) -> Optional[str]:
        if not self._enabled:
            self._logger.warning("Manufacturer crawling disabled; job not started")
            return None

        schedule = await self.get_crawl_schedule(schedule_id)
        if not schedule:
            self._logger.error("Schedule %s not found", schedule_id)
            return None

        client = self._get_db_client()
        if client is None:
            return None

        payload = {
            "schedule_id": schedule_id,
            "manufacturer_id": schedule["manufacturer_id"],
            "status": "queued",
            "crawl_metadata": {},
        }
        try:
            response = (
                client.table("manufacturer_crawl_jobs", schema="krai_system")
                .insert(payload)
                .execute()
            )
            job_id = response.data[0]["id"] if response.data else None
            self._logger.info("Queued crawl job %s for schedule %s", job_id, schedule_id)

            # Dispatch job via BatchTaskService if available, otherwise inline
            if job_id:
                await self._dispatch_crawl_job(job_id, schedule_id)

            return job_id
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.error("Failed to start crawl job: %s", exc)
            return None

    async def _dispatch_crawl_job(self, job_id: str, schedule_id: str) -> None:
        """Dispatch a crawl job for execution via BatchTaskService or inline background."""
        if self._batch_task_service:
            try:
                task_request = {
                    "operation_type": "manufacturer_crawl",
                    "priority": "medium",
                    "user_id": "system",
                    "payload": {"job_id": job_id, "schedule_id": schedule_id},
                }
                task_id = await self._batch_task_service.create_task(task_request)
                self._logger.info("Enqueued crawl job %s as batch task %s", job_id, task_id)
            except Exception as exc:
                self._logger.warning("Failed to enqueue crawl job %s, falling back to inline: %s", job_id, exc)
                # Fallback to inline execution
                asyncio.create_task(self.execute_crawl_job(job_id))
        else:
            self._logger.warning("BatchTaskService unavailable, running crawl job %s inline", job_id)
            asyncio.create_task(self.execute_crawl_job(job_id))

    async def execute_crawl_job(self, job_id: str) -> Dict[str, Any]:
        client = self._get_db_client()
        if client is None:
            return {"success": False, "error": "database client unavailable"}

        job = await self.get_crawl_job_status(job_id)
        if not job:
            return {"success": False, "error": "job not found"}

        schedule = await self.get_crawl_schedule(job["schedule_id"]) if job.get("schedule_id") else None
        if not schedule:
            return {"success": False, "error": "schedule not found"}

        await self._update_job(job_id, {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()})

        crawl_options = schedule.get("crawl_options", {}) or {}
        crawl_options.setdefault("limit", schedule.get("max_pages") or self._config.get("default_max_pages", 100))
        crawl_options.setdefault("maxDepth", schedule.get("max_depth") or self._config.get("default_max_depth", 2))

        try:
            response = await self._scraper.crawl_site(schedule.get("start_url"), options=crawl_options)
        except FirecrawlUnavailableError as exc:  # pragma: no cover
            await self._update_job(job_id, {"status": "failed", "error_message": str(exc)})
            return {"success": False, "error": str(exc)}
        except Exception as exc:  # pragma: no cover
            await self._update_job(job_id, {"status": "failed", "error_message": str(exc)})
            return {"success": False, "error": str(exc)}

        if not response.get("success"):
            await self._update_job(job_id, {"status": "failed", "error_message": response.get("error")})
            return {"success": False, "error": response.get("error")}

        pages = response.get("pages", [])
        persisted = await self._persist_crawled_pages(job_id, schedule.get("manufacturer_id"), pages)

        await self._update_job(
            job_id,
            {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "pages_discovered": len(pages),
                "pages_scraped": persisted["scraped"],
                "pages_failed": persisted["failed"],
                "crawl_metadata": {"backend": response.get("backend")},
            },
        )

        await self._update_schedule_run(schedule.get("id"))

        if self._structured_extraction_service:
            await self.process_crawled_pages(job_id)

        return {
            "success": True,
            "job_id": job_id,
            "pages_discovered": len(pages),
            "pages_scraped": persisted["scraped"],
            "pages_failed": persisted["failed"],
        }

    async def process_crawled_pages(self, job_id: str) -> Dict[str, Any]:
        if not self._structured_extraction_service:
            return {"processed": 0, "extractions": 0}

        client = self._get_db_client()
        if client is None:
            return {"processed": 0, "extractions": 0}

        response = (
            client.table("crawled_pages", schema="krai_system")
            .select("id, page_type")
            .eq("crawl_job_id", str(job_id))
            .eq("status", "scraped")
            .execute()
        )
        pages = response.data or []
        extraction_count = 0
        processed_ids = []
        failed_ids = []

        for page in pages:
            result = await self._structured_extraction_service.extract_from_crawled_page(page["id"])
            if result.get("success"):
                extraction_count += 1
                processed_ids.append(page["id"])
            else:
                failed_ids.append(page["id"])

        # Update pages individually based on extraction outcome
        if processed_ids:
            client.table("crawled_pages", schema="krai_system").update(
                {"status": "processed", "processed_at": datetime.now(timezone.utc).isoformat()}
            ).in_("id", processed_ids).execute()
        if failed_ids:
            client.table("crawled_pages", schema="krai_system").update(
                {"status": "failed", "processed_at": datetime.now(timezone.utc).isoformat()}
            ).in_("id", failed_ids).execute()

        return {"processed": len(processed_ids), "failed": len(failed_ids), "extractions": extraction_count}

    async def detect_content_changes(self, manufacturer_id: str) -> List[Dict[str, Any]]:
        client = self._get_db_client()
        if client is None:
            return []

        response = (
            client.table("crawled_pages", schema="krai_system")
            .select("url, content_hash, created_at")
            .eq("manufacturer_id", str(manufacturer_id))
            .order("url")
            .execute()
        )

        changes: Dict[str, Dict[str, Any]] = {}
        for row in response.data or []:
            url = row.get("url")
            url_hash = row.get("content_hash")
            created_at = row.get("created_at")
            if not url or not url_hash:
                continue
            if url not in changes:
                changes[url] = {"last_hash": url_hash, "last_seen": created_at, "changed": False}
            else:
                if changes[url]["last_hash"] != url_hash:
                    changes[url]["changed"] = True
                    changes[url]["previous_hash"] = changes[url]["last_hash"]
                    changes[url]["last_hash"] = url_hash
                    changes[url]["last_seen"] = created_at

        return [
            {
                "url": url,
                "changed": meta.get("changed", False),
                "last_hash": meta.get("last_hash"),
                "previous_hash": meta.get("previous_hash"),
                "last_seen": meta.get("last_seen"),
            }
            for url, meta in changes.items()
            if meta.get("changed")
        ]

    async def get_crawl_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        client = self._get_db_client()
        if client is None:
            return None

        response = (
            client.table("manufacturer_crawl_jobs", schema="krai_system")
            .select("*, crawl_metadata")
            .eq("id", str(job_id))
            .limit(1)
            .execute()
        )
        job = response.data[0] if response.data else None
        if job and job.get("pages_discovered"):
            discovered = job.get("pages_discovered", 0) or 0
            scraped = job.get("pages_scraped", 0) or 0
            job["progress_percent"] = 0 if discovered == 0 else round((scraped / discovered) * 100, 2)
        return job

    async def list_crawl_jobs(self, schedule_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self._get_db_client()
        if client is None:
            return []

        query = client.table("manufacturer_crawl_jobs", schema="krai_system").select("*").order("created_at", desc=True)
        if schedule_id:
            query = query.eq("schedule_id", str(schedule_id))
        if status:
            query = query.eq("status", status)
        response = query.execute()
        return response.data or []

    async def retry_failed_job(self, job_id: str) -> Optional[str]:
        job = await self.get_crawl_job_status(job_id)
        if not job or job.get("status") != "failed":
            return None
        schedule_id = job.get("schedule_id")
        if not schedule_id:
            return None
        return await self.start_crawl_job(schedule_id)

    async def get_crawled_pages(
        self,
        *,
        job_id: Optional[str] = None,
        manufacturer_id: Optional[str] = None,
        page_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        client = self._get_db_client()
        if client is None:
            return []

        query = client.table("crawled_pages", schema="krai_system").select("*").order("created_at", desc=True)
        if job_id:
            query = query.eq("crawl_job_id", str(job_id))
        if manufacturer_id:
            query = query.eq("manufacturer_id", str(manufacturer_id))
        if page_type:
            query = query.eq("page_type", page_type)

        response = query.execute()
        return response.data or []

    async def check_scheduled_crawls(self) -> List[str]:
        if not self._enabled:
            return []

        client = self._get_db_client()
        if client is None:
            return []

        now_iso = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("manufacturer_crawl_schedules", schema="krai_system")
            .select("id")
            .eq("enabled", True)
            .lte("next_run_at", now_iso)
            .execute()
        )

        job_ids: List[str] = []
        for row in response.data or []:
            schedule_id = row["id"]
            job_id = await self.start_crawl_job(schedule_id)
            if job_id:
                job_ids.append(job_id)
        return job_ids

    async def get_crawler_stats(self) -> Dict[str, Any]:
        client = self._get_db_client()
        if client is None:
            return {}

        schedules = client.table("manufacturer_crawl_schedules", schema="krai_system").select("id", count="exact").execute()
        active = (
            client.table("manufacturer_crawl_schedules", schema="krai_system")
            .select("id", count="exact")
            .eq("enabled", True)
            .execute()
        )
        jobs = client.table("manufacturer_crawl_jobs", schema="krai_system").select("id", count="exact").execute()
        running = (
            client.table("manufacturer_crawl_jobs", schema="krai_system")
            .select("id", count="exact")
            .eq("status", "running")
            .execute()
        )
        pages = client.table("crawled_pages", schema="krai_system").select("id", count="exact").execute()

        page_type_dist: Dict[str, int] = {}
        page_type_rows = (
            client.table("crawled_pages", schema="krai_system")
            .select("page_type")
            .neq("page_type", None)
            .execute()
        )
        for row in page_type_rows.data or []:
            typ = row.get("page_type") or "unknown"
            page_type_dist[typ] = page_type_dist.get(typ, 0) + 1

        return {
            "total_schedules": schedules.count or 0,
            "active_schedules": active.count or 0,
            "total_jobs": jobs.count or 0,
            "running_jobs": running.count or 0,
            "total_pages": pages.count or 0,
            "page_types": page_type_dist,
        }

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _get_db_client(self):
        client = getattr(self._database_service, "service_client", None)
        if client is None:
            client = getattr(self._database_service, "client", None)
        if client is None:
            self._logger.error("Database client unavailable for manufacturer crawler")
        return client

    async def _update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        client = self._get_db_client()
        if client is None:
            return
        try:
            client.table("manufacturer_crawl_jobs", schema="krai_system").update(updates).eq("id", str(job_id)).execute()
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.debug("Failed to update crawl job %s: %s", job_id, exc)

    async def _update_schedule_run(self, schedule_id: str) -> None:
        client = self._get_db_client()
        if client is None:
            return
        next_run = self._calculate_next_run(None)
        try:
            client.table("manufacturer_crawl_schedules", schema="krai_system").update(
                {
                    "last_run_at": datetime.now(timezone.utc).isoformat(),
                    "next_run_at": next_run,
                }
            ).eq("id", str(schedule_id)).execute()
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.debug("Failed to update schedule %s run metadata: %s", schedule_id, exc)

    async def _persist_crawled_pages(self, job_id: str, manufacturer_id: str, pages: Sequence[Dict[str, Any]]) -> Dict[str, int]:
        client = self._get_db_client()
        if client is None:
            return {"scraped": 0, "failed": len(pages)}

        scraped = 0
        failed = 0
        for page in pages:
            url = page.get("url")
            content = page.get("content")
            if not url:
                failed += 1
                continue
            url_hash = hashlib.sha256(url.encode("utf-8", errors="ignore")).hexdigest()
            content_hash = hashlib.sha256((content or "").encode("utf-8", errors="ignore")).hexdigest() if content else None
            page_type = self._determine_page_type(url)

            payload = {
                "crawl_job_id": job_id,
                "manufacturer_id": manufacturer_id,
                "url": url,
                "url_hash": url_hash,
                "content": content,
                "content_hash": content_hash,
                "html": page.get("html"),
                "page_title": (page.get("metadata") or {}).get("title"),
                "page_type": page_type,
                "depth": (page.get("metadata") or {}).get("depth"),
                "status": "scraped",
                "scrape_metadata": page.get("metadata") or {},
            }

            try:
                existing = (
                    client.table("crawled_pages", schema="krai_system")
                    .select("id")
                    .eq("crawl_job_id", str(job_id))
                    .eq("url_hash", url_hash)
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    client.table("crawled_pages", schema="krai_system").update(payload).eq("id", existing.data[0]["id"]).execute()
                else:
                    client.table("crawled_pages", schema="krai_system").insert(payload).execute()
                scraped += 1
            except Exception as exc:  # pragma: no cover - defensive logging
                failed += 1
                self._logger.debug("Failed to persist crawled page %s: %s", url, exc)

        return {"scraped": scraped, "failed": failed}

    def _determine_page_type(self, url: str) -> Optional[str]:
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ["product", "spec", "datasheet"]):
            return "product_page"
        if any(keyword in url_lower for keyword in ["error", "support", "troubleshoot"]):
            return "error_code_page"
        if any(keyword in url_lower for keyword in ["manual", "download", "pdf"]):
            return "manual_page"
        if "parts" in url_lower or "catalog" in url_lower:
            return "parts_page"
        return "unknown"

    def _calculate_next_run(self, cron_expression: Optional[str]) -> Optional[str]:
        if not cron_expression or croniter is None:
            return None
        try:
            iterator = croniter(cron_expression, datetime.now(timezone.utc))
            return iterator.get_next(datetime).isoformat()
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.debug("Invalid cron expression %s: %s", cron_expression, exc)
            return None

    def _load_config(self) -> Dict[str, Any]:
        if self._config_service:
            try:
                config = self._config_service.get_scraping_config()
                return {
                    "enable_manufacturer_crawling": config.get("enable_manufacturer_crawling", False),
                    "default_max_pages": config.get("crawler_default_max_pages", 100),
                    "default_max_depth": config.get("crawler_default_max_depth", 2),
                }
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.debug("Failed loading crawler config: %s", exc)
        return {
            "enable_manufacturer_crawling": False,
            "default_max_pages": 100,
            "default_max_depth": 2,
        }
