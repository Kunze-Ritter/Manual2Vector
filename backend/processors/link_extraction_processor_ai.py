"""Link Extraction Processor (AI) - Extract links using AI assistance."""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.core.base_processor import BaseProcessor, Stage
from .link_extractor import LinkExtractor
from .text_extractor import TextExtractor


class LinkExtractionProcessorAI(BaseProcessor):
    """Stage 6 processor: Extract links and videos using heuristics + AI support."""

    def __init__(self, database_service=None, ai_service=None, youtube_api_key: Optional[str] = None):
        super().__init__(name="link_extraction_processor")
        self.stage = Stage.LINK_EXTRACTION
        self.database_service = database_service
        self.ai_service = ai_service

        # Prefer explicit API key, fallback to environment variable
        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        self.link_extractor = LinkExtractor(youtube_api_key=self.youtube_api_key)

        enable_ocr = os.getenv("ENABLE_OCR_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
        pdf_engine = os.getenv("PDF_ENGINE", "pymupdf")
        self.text_extractor = TextExtractor(prefer_engine=pdf_engine, enable_ocr_fallback=enable_ocr)

        if not self.database_service:
            self.logger.warning("LinkExtractionProcessorAI initialized without database service")
        else:
            self.logger.info("LinkExtractionProcessorAI initialized")

    async def process(self, context) -> Any:
        """Extract links for the provided processing context."""
        file_path = Path(context.file_path)
        document_id = getattr(context, "document_id", None)

        if not document_id:
            raise ValueError("Processing context must include 'document_id'")

        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            adapter.info("Starting link extraction")

            if not file_path.exists():
                adapter.error("File not found: %s", file_path)
                return self._create_result(False, f"File not found: {file_path}", {})

            page_texts = await self._load_page_texts(context, file_path, adapter)
            if not page_texts:
                adapter.warning("No page texts available for link extraction")
                return self._create_result(False, "No page texts available for link extraction", {})

            extraction_result = self.link_extractor.extract_from_document(
                pdf_path=file_path,
                page_texts=page_texts,
                document_id=document_id
            )

            links = extraction_result.get("links", [])
            videos = extraction_result.get("videos", [])

            if not links and not videos:
                adapter.info("No links or videos found")
                return self._create_result(True, "No links found", {"links_found": 0, "videos_found": 0})

            self.logger.success(f"Extracted {len(links)} links and {len(videos)} videos")

            manufacturer_id, series_id = await self._get_document_manufacturer_series(str(document_id), adapter)
            enriched_links = self._enrich_links(links, context, manufacturer_id, series_id)
            enriched_videos = self._enrich_videos(videos, manufacturer_id, series_id, document_id)

            link_id_map = await self._save_links_to_db(enriched_links, str(document_id), adapter)
            await self._save_videos_to_db(enriched_videos, link_id_map, adapter)

            return self._create_result(
                True,
                "Link extraction completed",
                {
                    "links_found": len(enriched_links),
                    "videos_found": len(enriched_videos)
                }
            )

    async def _load_page_texts(self, context, file_path: Path, adapter) -> Dict[int, str]:
        """Load page texts from context, database, or by re-extracting from PDF."""
        if hasattr(context, "page_texts") and context.page_texts:
            return context.page_texts

        # Attempt to rebuild from chunks stored in the database
        if self.database_service and getattr(self.database_service, "client", None):
            try:
                result = self.database_service.client.table("chunks").select("page_start, content").eq(
                    "document_id", context.document_id
                ).order("chunk_index").execute()

                page_texts: Dict[int, List[str]] = {}
                for row in result.data or []:
                    page = row.get("page_start")
                    content = row.get("content") or ""
                    if page is not None and content:
                        page_texts.setdefault(page, []).append(content)

                if page_texts:
                    return {page: "\n".join(parts) for page, parts in page_texts.items()}
            except Exception as exc:
                adapter.debug("Failed to load page texts from database: %s", exc)

        # Fallback: Re-run text extraction on the PDF
        try:
            page_texts, _ = self.text_extractor.extract_text(file_path)
            return page_texts
        except Exception as exc:
            adapter.error("Failed to extract text for link stage: %s", exc)
            return {}

    async def _get_document_manufacturer_series(self, document_id: str, adapter) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve manufacturer_id and series_id for the document."""
        if not self.database_service or not getattr(self.database_service, "client", None):
            return None, None

        try:
            result = self.database_service.client.table("document_products").select("product_id").eq(
                "document_id", document_id
            ).limit(1).execute()

            if result.data:
                product_id = result.data[0].get("product_id")
                if product_id:
                    product = self.database_service.client.table("products").select(
                        "manufacturer_id, series_id"
                    ).eq("id", product_id).limit(1).execute()
                    if product.data:
                        product_row = product.data[0]
                        return product_row.get("manufacturer_id"), product_row.get("series_id")
        except Exception as exc:
            adapter.debug("Failed to fetch manufacturer/series: %s", exc)

        return None, None

    def _enrich_links(
        self,
        links: List[Dict],
        context,
        manufacturer_id: Optional[str],
        series_id: Optional[str]
    ) -> List[Dict]:
        """Attach document metadata to links and derive related error codes."""
        if not links:
            return []

        for link in links:
            link.setdefault("document_id", str(context.document_id))
            link.setdefault("manufacturer", context.manufacturer)
            link["manufacturer_id"] = manufacturer_id
            link["series_id"] = series_id

            related_codes = self._extract_error_codes_from_link(link, context)
            if related_codes:
                link["related_error_codes"] = related_codes

        return links

    def _enrich_videos(
        self,
        videos: List[Dict],
        manufacturer_id: Optional[str],
        series_id: Optional[str],
        document_id: str
    ) -> List[Dict]:
        """Attach additional metadata for video records."""
        if not videos:
            return []

        for video in videos:
            video["manufacturer_id"] = manufacturer_id
            video["series_id"] = series_id
            video.setdefault("document_id", str(document_id))

        return videos

    def _extract_error_codes_from_link(self, link: Dict, context) -> List[str]:
        """Extract error codes from context or link description."""
        codes: List[str] = []

        if hasattr(context, "error_codes") and context.error_codes:
            for code_info in context.error_codes:
                if isinstance(code_info, dict) and code_info.get("code"):
                    codes.append(code_info["code"])

        description = link.get("description") or ""
        if description:
            matches = re.findall(r"\b[A-Z]-?\d{3,4}\b", description)
            codes.extend(matches)

        seen = set()
        unique_codes = []
        for code in codes:
            if code not in seen:
                unique_codes.append(code)
                seen.add(code)

        return unique_codes

    async def _save_links_to_db(self, links: List[Dict], document_id: str, adapter) -> Dict[str, str]:
        """Persist links to the database. Returns a URL → link_id map."""
        if not links or not self.database_service or not getattr(self.database_service, "client", None):
            return {}

        link_id_map: Dict[str, str] = {}
        supabase = self.database_service.client

        for link in links:
            try:
                url = link.get("url")
                if not url:
                    continue

                existing = supabase.table("vw_links").select("id").eq("document_id", document_id).eq("url", url).limit(1).execute()

                link_payload = {
                    "document_id": document_id,
                    "url": url,
                    "description": link.get("description"),
                    "link_type": link.get("link_type", "external"),
                    "link_category": link.get("link_category", "external"),
                    "page_number": link.get("page_number"),
                    "position_data": link.get("position_data"),
                    "confidence_score": link.get("confidence_score", 0.5),
                    "manufacturer_id": link.get("manufacturer_id"),
                    "series_id": link.get("series_id"),
                    "related_error_codes": link.get("related_error_codes") or []
                }

                if existing.data:
                    link_id = existing.data[0]["id"]
                    supabase.table("vw_links").update(link_payload).eq("id", link_id).execute()
                else:
                    insert_result = supabase.table("vw_links").insert(link_payload).execute()
                    link_id = insert_result.data[0]["id"] if insert_result.data else None

                    if link_id:
                        try:
                            supabase.rpc(
                                "auto_link_resource_to_document",
                                {
                                    "p_resource_table": "krai_content.links",
                                    "p_resource_id": link_id,
                                    "p_document_id": document_id
                                }
                            ).execute()
                        except Exception as rpc_error:
                            self.logger.debug(f"Auto-link RPC failed: {rpc_error}")

                if existing.data:
                    link_id_map[url] = existing.data[0]["id"]
                elif link_id:
                    link_id_map[url] = link_id

            except Exception as exc:
                adapter.warning("Failed to persist link %s: %s", link.get("url"), exc)

        return link_id_map

    async def _save_videos_to_db(self, videos: List[Dict], link_id_map: Dict[str, str], adapter):
        """Persist associated videos to the database."""
        if not videos or not self.database_service or not getattr(self.database_service, "client", None):
            return

        supabase = self.database_service.client

        for video in videos:
            try:
                url = video.get("source_url") or video.get("url")
                link_id = link_id_map.get(url) if url else video.get("link_id")

                video_payload = {
                    "link_id": link_id,
                    "document_id": video.get("document_id"),
                    "youtube_id": video.get("youtube_id"),
                    "title": video.get("title"),
                    "description": video.get("description"),
                    "thumbnail_url": video.get("thumbnail_url"),
                    "duration": video.get("duration"),
                    "platform": video.get("link_category") or video.get("platform") or "youtube",
                    "metadata": video.get("metadata") or {},
                    "manufacturer_id": video.get("manufacturer_id"),
                    "series_id": video.get("series_id")
                }

                if video.get("youtube_id"):
                    existing = supabase.table("vw_videos").select("id").eq("youtube_id", video["youtube_id"]).limit(1).execute()
                    if existing.data:
                        supabase.table("vw_videos").update(video_payload).eq("id", existing.data[0]["id"]).execute()
                        continue

                supabase.table("vw_videos").insert(video_payload).execute()

            except Exception as exc:
                adapter.warning("Failed to persist video %s: %s", video.get("title"), exc)

    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        class Result:
            def __init__(self, success: bool, message: str, data: Dict):
                self.success = success
                self.message = message
                self.data = data

        return Result(success, message, data)
