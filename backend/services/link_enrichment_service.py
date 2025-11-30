"""Link enrichment service for scraping external URLs linked in documents.

This module orchestrates scraping of external links referenced in processed
PDFs. It leverages :class:`~backend.services.web_scraping_service.WebScrapingService`
for fetching content (Firecrawl primary, BeautifulSoup fallback) and persists the
resulting artefacts into ``krai_content.links`` enrichment fields.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from .config_service import ConfigService
from .web_scraping_service import (
    FirecrawlUnavailableError,
    WebScrapingService,
)


class LinkEnrichmentService:
    """Service responsible for scraping and enriching stored link records."""

    def __init__(
        self,
        web_scraping_service: WebScrapingService,
        database_service: Any,
        config_service: Optional[ConfigService] = None,
    ) -> None:
        self._scraper = web_scraping_service
        self._database_service = database_service
        self._config_service = config_service
        self._logger = logging.getLogger("krai.services.link_enrichment")

        cfg = self._load_config()
        self._max_concurrent_enrichments = cfg.get("max_concurrent_enrichments", 3)
        self._enrichment_timeout = cfg.get("enrichment_timeout", 30)
        self._retry_failed_after_hours = cfg.get("retry_failed_after_hours", 24)
        self._enabled = cfg.get("enable_link_enrichment", True)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def enrich_link(
        self,
        link_id: str,
        url: str,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Scrape a single link and persist enrichment artefacts.

        Args:
            link_id: UUID identifier for the link row.
            url: URL to scrape.
            force_refresh: When ``True`` scraping is performed even when a
                successful enrichment already exists.

        Returns:
            Dict[str, Any]: Summary payload describing enrichment outcome.
        """

        if not self._enabled:
            return {"success": False, "link_id": link_id, "error": "link enrichment disabled"}

        client = self._get_db_client()
        if client is None:
            return {"success": False, "link_id": link_id, "error": "database client unavailable"}

        existing = (
            client.table("links", schema="krai_content")
            .select("id, scrape_status, scraped_content, scraped_metadata, content_hash")
            .eq("id", str(link_id))
            .limit(1)
            .execute()
        )
        row = existing.data[0] if existing.data else None

        if not row:
            return {"success": False, "link_id": link_id, "error": "link record not found"}

        scrape_status = row.get("scrape_status")
        scraped_content = row.get("scraped_content")
        content_hash = row.get("content_hash")

        if (
            scrape_status == "success"
            and scraped_content
            and content_hash
            and not force_refresh
        ):
            self._logger.debug("Link %s already enriched; skipping", link_id)
            return {"success": True, "link_id": link_id, "skipped": True}

        metadata = row.get("scraped_metadata") or {}
        retry_count = int(metadata.get("retry_count", 0))

        try:
            result = await asyncio.wait_for(
                self._scraper.scrape_url(url),
                timeout=self._enrichment_timeout + 5,
            )
        except FirecrawlUnavailableError as exc:  # pragma: no cover - defensive
            self._logger.warning("Firecrawl unavailable for %s: %s", url, exc)
            result = await self._scraper.scrape_url(url, force_backend="beautifulsoup")
        except asyncio.TimeoutError as exc:
            self._logger.warning("Scrape timed out for %s", url)
            self._mark_link_failed(
                link_id,
                error_message=f"Scrape timeout: {exc}",
                metadata=metadata,
            )
            return {"success": False, "link_id": link_id, "error": "timeout"}
        except Exception as exc:  # pragma: no cover - safety net
            self._logger.exception("Unexpected scraping failure for %s", url)
            self._mark_link_failed(
                link_id,
                error_message=str(exc),
                metadata=metadata,
            )
            return {"success": False, "link_id": link_id, "error": str(exc)}

        if not result.get("success"):
            error_message = result.get("error", "scrape failed")
            self._logger.debug("Scrape failed for %s: %s", url, error_message)
            metadata["retry_count"] = retry_count + 1
            self._mark_link_failed(
                link_id,
                error_message=error_message,
                metadata=metadata,
            )
            return {"success": False, "link_id": link_id, "error": error_message}

        content: Optional[str] = result.get("content")
        html: Optional[str] = result.get("html")
        backend = result.get("backend")
        scrape_metadata = result.get("metadata") or {}

        if not content:
            metadata["retry_count"] = retry_count + 1
            self._mark_link_failed(
                link_id,
                error_message="No content returned by scraper",
                metadata=metadata,
            )
            return {"success": False, "link_id": link_id, "error": "empty content"}

        content_hash = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
        metadata.update(
            {
                "backend": backend,
                "status_code": scrape_metadata.get("status_code"),
                "content_type": scrape_metadata.get("content_type"),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "retry_count": 0,
            }
        )

        try:
            client.table("links", schema="krai_content").update(
                {
                    "scraped_content": content,
                    "scraped_html": html,
                    "scraped_metadata": metadata,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "scrape_status": "success",
                    "scrape_error": None,
                    "content_hash": content_hash,
                }
            ).eq("id", str(link_id)).execute()
        except Exception as exc:  # pragma: no cover - Supabase error handling
            self._logger.error("Failed to persist enrichment for %s: %s", link_id, exc)
            return {"success": False, "link_id": link_id, "error": str(exc)}

        self._logger.info(
            "Enriched link %s using %s (content %s chars)",
            link_id,
            backend,
            len(content),
        )
        return {
            "success": True,
            "link_id": link_id,
            "backend": backend,
            "content_length": len(content),
        }

    async def enrich_links_batch(
        self,
        link_ids: Sequence[str],
        *,
        max_concurrent: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Enrich multiple links concurrently while respecting concurrency limits."""

        if not link_ids:
            return {"total": 0, "enriched": 0, "failed": 0, "skipped": 0, "results": []}

        client = self._get_db_client()
        if client is None:
            return {"total": 0, "enriched": 0, "failed": len(link_ids), "skipped": 0, "results": []}

        query = (
            client.table("links", schema="krai_content")
            .select("id, url, scrape_status, scraped_content, content_hash")
        )
        if not force_refresh:
            query = query.in_("scrape_status", ["pending", "failed"])
        records = query.in_("id", [str(link_id) for link_id in link_ids]).execute()
        links = {row["id"]: row for row in records.data or []}

        semaphore = asyncio.Semaphore(max_concurrent or self._max_concurrent_enrichments)
        results: List[Dict[str, Any]] = []

        async def _worker(link_id: str) -> None:
            link = links.get(link_id)
            if not link:
                results.append({"success": False, "link_id": link_id, "error": "link record missing"})
                return

            if (
                link.get("scrape_status") == "success"
                and link.get("scraped_content")
                and link.get("content_hash")
                and not force_refresh
            ):
                results.append({"success": True, "link_id": link_id, "skipped": True})
                return

            async with semaphore:
                outcome = await self.enrich_link(link_id, link.get("url"), force_refresh=force_refresh)
                results.append(outcome)

        await asyncio.gather(*[_worker(str(link_id)) for link_id in link_ids])

        enriched = sum(1 for item in results if item.get("success") and not item.get("skipped"))
        skipped = sum(1 for item in results if item.get("skipped"))
        failed = sum(1 for item in results if not item.get("success"))

        return {
            "total": len(link_ids),
            "enriched": enriched,
            "failed": failed,
            "skipped": skipped,
            "results": results,
        }

    async def enrich_document_links(self, document_id: str) -> Dict[str, Any]:
        """Enrich all links belonging to the supplied document identifier."""

        client = self._get_db_client()
        if client is None:
            return {"total": 0, "enriched": 0, "failed": 0, "skipped": 0, "results": []}

        response = (
            client.table("links", schema="krai_content")
            .select("id")
            .eq("document_id", str(document_id))
            .in_("scrape_status", ["pending", "failed"])
            .execute()
        )
        link_ids = [row["id"] for row in response.data or []]
        return await self.enrich_links_batch(link_ids)

    async def refresh_stale_links(self, days_old: int = 90) -> Dict[str, Any]:
        """Re-enrich links whose content is older than the configured threshold."""

        client = self._get_db_client()
        if client is None:
            return {"total": 0, "enriched": 0, "failed": 0, "skipped": 0, "results": []}

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        response = (
            client.table("links", schema="krai_content")
            .select("id")
            .lt("scraped_at", cutoff.isoformat())
            .eq("scrape_status", "success")
            .execute()
        )
        link_ids = [row["id"] for row in response.data or []]
        return await self.enrich_links_batch(link_ids, force_refresh=True)

    async def retry_failed_links(self, max_retries: int = 3) -> Dict[str, Any]:
        """Retry enrichment for links that previously failed within retry budget."""

        client = self._get_db_client()
        if client is None:
            return {"total": 0, "enriched": 0, "failed": 0, "skipped": 0, "results": []}

        response = (
            client.table("links", schema="krai_content")
            .select("id, scraped_metadata")
            .eq("scrape_status", "failed")
            .execute()
        )

        eligible_ids: List[str] = []
        threshold = datetime.now(timezone.utc) - timedelta(hours=self._retry_failed_after_hours)
        for row in response.data or []:
            metadata = row.get("scraped_metadata") or {}
            retries = int(metadata.get("retry_count", 0))
            last_error_iso = metadata.get("last_error_at")
            last_error_at = None
            if last_error_iso:
                try:
                    last_error_at = datetime.fromisoformat(last_error_iso)
                except ValueError:
                    last_error_at = None
            if retries < max_retries and (last_error_at is None or last_error_at <= threshold):
                metadata["retry_count"] = retries + 1
                try:
                    client.table("links", schema="krai_content").update(
                        {"scraped_metadata": metadata}
                    ).eq("id", row["id"]).execute()
                except Exception as exc:  # pragma: no cover - defensive
                    self._logger.debug(
                        "Failed updating retry counter for %s: %s", row["id"], exc
                    )
                eligible_ids.append(row["id"])

        return await self.enrich_links_batch(eligible_ids)

    async def get_enrichment_stats(self) -> Dict[str, Any]:
        """Return aggregated statistics for monitoring dashboards."""

        client = self._get_db_client()
        if client is None:
            return {}

        totals = (
            client.table("links", schema="krai_content")
            .select("id", count="exact")
            .execute()
        )
        success = (
            client.table("links", schema="krai_content")
            .select("id", count="exact")
            .eq("scrape_status", "success")
            .execute()
        )
        pending = (
            client.table("links", schema="krai_content")
            .select("id", count="exact")
            .eq("scrape_status", "pending")
            .execute()
        )
        failed = (
            client.table("links", schema="krai_content")
            .select("id", count="exact")
            .eq("scrape_status", "failed")
            .execute()
        )
        avg_length_response = (
            client.table("links", schema="krai_content")
            .select("avg_length=avg(char_length(scraped_content))")
            .neq("scraped_content", None)
            .execute()
        )
        average_content_length = 0
        if avg_length_response.data:
            avg_row = avg_length_response.data[0]
            average_content_length = int(avg_row.get("avg_length") or 0)

        backend_distribution: Dict[str, int] = {}
        backend_rows = (
            client.table("links", schema="krai_content")
            .select("scraped_metadata")
            .neq("scraped_metadata", None)
            .execute()
        )
        for row in backend_rows.data or []:
            metadata = row.get("scraped_metadata") or {}
            backend = metadata.get("backend") or "unknown"
            backend_distribution[backend] = backend_distribution.get(backend, 0) + 1

        return {
            "total_links": totals.count or 0,
            "enriched_links": success.count or 0,
            "pending_links": pending.count or 0,
            "failed_links": failed.count or 0,
            "average_content_length": average_content_length,
            "backend_distribution": backend_distribution,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_db_client(self):
        client = getattr(self._database_service, "service_client", None)
        if client is None:
            client = getattr(self._database_service, "client", None)
        if client is None:
            self._logger.error("Database service client unavailable for link enrichment")
        return client

    def _load_config(self) -> Dict[str, Any]:
        if self._config_service:
            try:
                config = self._config_service.get_scraping_config()
                return {
                    "enable_link_enrichment": config.get("enable_link_enrichment", False),
                    "max_concurrent_enrichments": config.get("max_concurrency", 3),
                    "enrichment_timeout": int(config.get("scrape_timeout", 30)),
                    "retry_failed_after_hours": int(config.get("retry_failed_after_hours", 24)),
                }
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.debug("Failed loading scraping config: %s", exc)
        return {
            "enable_link_enrichment": True,
            "max_concurrent_enrichments": 3,
            "enrichment_timeout": 30,
            "retry_failed_after_hours": 24,
        }

    def _mark_link_failed(
        self,
        link_id: str,
        *,
        error_message: str,
        metadata: Dict[str, Any],
    ) -> None:
        client = self._get_db_client()
        if client is None:
            return

        metadata = metadata or {}
        metadata["last_error_at"] = datetime.now(timezone.utc).isoformat()
        try:
            client.table("links", schema="krai_content").update(
                {
                    "scrape_status": "failed",
                    "scrape_error": error_message,
                    "scraped_metadata": metadata,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", str(link_id)).execute()
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.debug("Failed updating failure state for %s: %s", link_id, exc)
