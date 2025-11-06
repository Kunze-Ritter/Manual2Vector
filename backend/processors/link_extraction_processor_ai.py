"""Link Extraction Processor (AI) - Extract links using AI assistance and enrichment.

Supports Firecrawl-based link enrichment for improved context and structured extraction.
"""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.core.base_processor import BaseProcessor, Stage
from .link_extractor import LinkExtractor
from .text_extractor import TextExtractor
from backend.services.context_extraction_service import ContextExtractionService
from backend.services.link_enrichment_service import LinkEnrichmentService
from backend.services.config_service import ConfigService
from backend.services.web_scraping_service import create_web_scraping_service
from backend.services.structured_extraction_service import StructuredExtractionService


class LinkExtractionProcessorAI(BaseProcessor):
    """Stage 6 processor: Extract links and videos using heuristics + AI support."""

    def __init__(
        self,
        database_service=None,
        ai_service=None,
        youtube_api_key: Optional[str] = None,
        link_enrichment_service: Optional[LinkEnrichmentService] = None,
        config_service: Optional[ConfigService] = None,
    ):
        super().__init__(name="link_extraction_processor")
        self.stage = Stage.LINK_EXTRACTION
        self.database_service = database_service
        self.ai_service = ai_service
        self.config_service = config_service

        # Prefer explicit API key, fallback to environment variable
        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        self.link_extractor = LinkExtractor(youtube_api_key=self.youtube_api_key)

        enable_ocr = os.getenv("ENABLE_OCR_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
        pdf_engine = os.getenv("PDF_ENGINE", "pymupdf")
        self.text_extractor = TextExtractor(prefer_engine=pdf_engine, enable_ocr_fallback=enable_ocr)

        # Phase 5: Context extraction configuration
        self.context_service = ContextExtractionService()
        self.enable_context_extraction = os.getenv('ENABLE_CONTEXT_EXTRACTION', 'true').lower() == 'true'

        self.enable_link_enrichment = os.getenv('ENABLE_LINK_ENRICHMENT', 'false').lower() == 'true'
        self.link_enrichment_service = link_enrichment_service

        if self.enable_link_enrichment and not self.link_enrichment_service and self.database_service:
            scraper_service = create_web_scraping_service(config_service=self.config_service)
            self.link_enrichment_service = LinkEnrichmentService(
                web_scraping_service=scraper_service,
                database_service=self.database_service,
                config_service=self.config_service,
            )

        # Initialize structured extraction service if enrichment is enabled
        self.enable_structured_extraction = os.getenv('ENABLE_STRUCTURED_EXTRACTION', 'false').lower() == 'true'
        self.structured_extraction_service: Optional[StructuredExtractionService] = None
        if self.enable_structured_extraction and self.enable_link_enrichment and self.link_enrichment_service:
            self.structured_extraction_service = StructuredExtractionService(
                web_scraping_service=self.link_enrichment_service._scraper,
                database_service=self.database_service,
                config_service=self.config_service,
            )

        self.logger.info(
            "Link enrichment: %s",
            "enabled" if self.enable_link_enrichment and self.link_enrichment_service else "disabled",
        )
        self.logger.info(
            "Structured extraction: %s",
            "enabled" if self.enable_structured_extraction and self.structured_extraction_service else "disabled",
        )

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

            # Phase 5: Extract context for links and videos (NEW!)
            if self.enable_context_extraction and context:
                page_texts = await self._load_page_texts(context, file_path, adapter)
                if page_texts:
                    enriched_links = self._extract_link_contexts(
                        links=enriched_links,
                        page_texts=page_texts,
                        adapter=adapter,
                        document_id=document_id  # Pass document ID for related chunks
                    )

            # Phase 5: Extract context for videos (NEW!)
            if self.enable_context_extraction and page_texts:
                enriched_videos = self._extract_video_contexts(
                    videos=enriched_videos,
                    page_texts=page_texts,
                    adapter=adapter,
                    document_id=document_id  # Pass document ID for related chunks
                )

            link_id_map = await self._save_links_to_db(enriched_links, str(document_id), adapter)
            await self._save_videos_to_db(enriched_videos, link_id_map, adapter)

            if self.enable_link_enrichment and self.link_enrichment_service:
                await self._enrich_document_links(enriched_links, adapter)
                adapter.info("Link enrichment completed")

            return self._create_result(
                True,
                "Link extraction completed",
                {
                    "links_found": len(enriched_links),
                    "videos_found": len(enriched_videos)
                }
            )
    async def _enrich_document_links(
        self,
        links: List[Dict],
        adapter,
    ) -> None:
        """Enrich links with scraped content using LinkEnrichmentService."""

        if not self.link_enrichment_service:
            return

        link_data = [
            (link.get("id"), link.get("url"))
            for link in links
            if link.get("id") and link.get("url")
        ]

        if not link_data:
            adapter.debug("No links to enrich")
            return

        adapter.info("Enriching %s links with scraped content", len(link_data))

        try:
            result = await self.link_enrichment_service.enrich_links_batch(
                link_ids=[link_id for link_id, _ in link_data],
                max_concurrent=3,
            )

            adapter.info(
                "Link enrichment complete: %s enriched, %s failed, %s skipped",
                result.get("enriched", 0),
                result.get("failed", 0),
                result.get("skipped", 0),
            )

            # Trigger structured extraction for enriched links if enabled
            if self.enable_structured_extraction and self.structured_extraction_service:
                await self._run_structured_extraction_on_links(link_data, adapter)
        except Exception as exc:  # pragma: no cover - defensive guard
            adapter.error(f"Link enrichment failed: {exc}")

    async def _run_structured_extraction_on_links(
        self,
        link_data: List[Tuple[str, str]],
        adapter,
    ) -> None:
        """Run structured extraction batch on enriched links."""
        if not self.structured_extraction_service:
            return

        link_ids = [link_id for link_id, _ in link_data if link_id]
        if not link_ids:
            adapter.debug("No link IDs available for structured extraction")
            return

        adapter.info("Running structured extraction on %s enriched links", len(link_ids))

        try:
            extraction_result = await self.structured_extraction_service.batch_extract(
                source_ids=link_ids,
                source_type="link",
                max_concurrent=2,
            )
            adapter.info(
                "Structured extraction complete: %s completed, %s failed, %s total",
                extraction_result.get("completed", 0),
                extraction_result.get("failed", 0),
                extraction_result.get("total", 0),
            )
        except Exception as exc:
            adapter.error("Structured extraction batch failed: %s", exc)

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
                    "related_error_codes": link.get("related_error_codes") or [],
                    # Phase 5: Context extraction fields
                    "context_description": link.get("context_description"),
                    "page_header": link.get("page_header"),
                    "related_products": link.get("related_products", []),
                    "related_chunks": link.get("related_chunks", []),  # Add related chunks
                    "scrape_status": link.get("scrape_status", "pending"),
                    "scraped_at": link.get("scraped_at"),
                    "scraped_content": link.get("scraped_content"),
                    "scraped_metadata": link.get("scraped_metadata", {}),
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
                    link["id"] = existing.data[0]["id"]
                elif link_id:
                    link_id_map[url] = link_id
                    link["id"] = link_id

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
                    "series_id": video.get("series_id"),
                    # Phase 5: Context extraction fields
                    "context_description": video.get("context_description"),
                    "page_number": video.get("page_number"),
                    "page_header": video.get('page_header'),  # Add page_header field
                    "related_error_codes": video.get("related_error_codes", []),
                    "related_products": video.get("related_products", []),
                    "related_chunks": video.get("related_chunks", [])  # Add related chunks
                }

                if video.get("youtube_id"):
                    existing = supabase.table("vw_videos").select("id").eq("youtube_id", video["youtube_id"]).limit(1).execute()
                    if existing.data:
                        supabase.table("vw_videos").update(video_payload).eq("id", existing.data[0]["id"]).execute()
                        continue

                supabase.table("vw_videos").insert(video_payload).execute()

            except Exception as exc:
                adapter.warning("Failed to persist video %s: %s", video.get("title"), exc)

    def _extract_link_contexts(
        self, 
        links: List[Dict], 
        page_texts: Dict[int, str], 
        adapter,
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Extract context for all links using ContextExtractionService.
        
        Args:
            links: List of link dictionaries
            page_texts: Dict mapping page_number to page_text
            adapter: Logger adapter
            document_id: Optional document ID for related chunks extraction
            
        Returns:
            List of links with context metadata added
        """
        links_with_context = []
        
        for link in links:
            page_number = link.get('page_number')
            if not page_number or page_number not in page_texts:
                adapter.warning("No page text available for link on page %d", page_number)
                links_with_context.append(link)
                continue
            
            page_text = page_texts[page_number]
            link_url = link.get('url')
            
            try:
                # Extract context using ContextExtractionService
                context_data = self.context_service.extract_link_context(
                    page_text=page_text,
                    page_number=page_number,
                    link_url=link_url
                )
                
                # Add context data to link dict
                link['context_description'] = context_data['context_description']
                link['page_header'] = context_data['page_header']
                link['related_products'] = context_data.get('related_products', [])
                link['related_chunks'] = self._get_related_chunks(page_number, document_id, adapter)  # Add related chunks
                # related_error_codes already exists in link enrichment
                
                links_with_context.append(link)
                
            except Exception as e:
                adapter.error("Failed to extract context for link on page %d: %s", page_number, e)
                links_with_context.append(link)
        
        adapter.info("Extracted context for %d links", len(links_with_context))
        return links_with_context
    
    def _get_related_chunks(self, page_number: int, document_id: UUID, adapter) -> List[str]:
        """
        Extract related chunk IDs for a given page number.
        
        Args:
            page_number: Page number to find chunks for
            document_id: Document ID to query chunks
            adapter: Logger adapter
            
        Returns:
            List of chunk IDs that include the given page
        """
        if not self.database_service or not document_id:
            return []
        
        try:
            # Query chunks that overlap with the given page
            result = self.database_service.client.table("vw_chunks").select(
                "id"
            ).eq(
                "document_id", str(document_id)
            ).or_(
                f"page_start.lte.{page_number},page_end.gte.{page_number}"
            ).execute()
            
            if result.data:
                chunk_ids = [chunk['id'] for chunk in result.data]
                adapter.debug(f"Found {len(chunk_ids)} related chunks for page {page_number}")
                return chunk_ids
            
            return []
            
        except Exception as e:
            adapter.warning(f"Failed to get related chunks for page {page_number}: {e}")
            return []

    def _extract_video_contexts(
        self, 
        videos: List[Dict], 
        page_texts: Dict[int, str], 
        adapter,
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Extract context for all videos using ContextExtractionService.
        
        Args:
            videos: List of video dictionaries
            page_texts: Dict mapping page_number to page_text
            adapter: Logger adapter
            document_id: Optional document ID for related chunks extraction
            
        Returns:
            List of videos with context metadata added
        """
        videos_with_context = []
        
        for video in videos:
            page_number = video.get('page_number')
            if not page_number or page_number not in page_texts:
                adapter.warning("No page text available for video on page %d", page_number)
                videos_with_context.append(video)
                continue
            
            page_text = page_texts[page_number]
            video_url = video.get('source_url') or video.get('url')
            
            try:
                # Extract context using ContextExtractionService
                context_data = self.context_service.extract_video_context(
                    page_text=page_text,
                    page_number=page_number,
                    video_url=video_url
                )
                
                # Add context data to video dict
                video['context_description'] = context_data['context_description']
                video['page_header'] = context_data['page_header']
                video['related_error_codes'] = context_data.get('related_error_codes', [])
                video['related_products'] = context_data.get('related_products', [])
                video['related_chunks'] = self._get_related_chunks(page_number, document_id, adapter)  # Add related chunks
                
                videos_with_context.append(video)
                
            except Exception as e:
                adapter.error("Failed to extract context for video on page %d: %s", page_number, e)
                videos_with_context.append(video)
        
        adapter.info("Extracted context for %d videos", len(videos_with_context))
        return videos_with_context

    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        class Result:
            def __init__(self, success: bool, message: str, data: Dict):
                self.success = success
                self.message = message
                self.data = data

        return Result(success, message, data)
