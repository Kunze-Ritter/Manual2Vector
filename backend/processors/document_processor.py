"""
Main Document Processor - Orchestrates everything

Coordinates text extraction, chunking, product/error extraction.
"""

from pathlib import Path
from typing import Optional, Dict, List, Any
from uuid import UUID, uuid4
import time
import re
from .logger import get_logger, log_processing_summary
from .models import ProcessingResult, DocumentMetadata
from .text_extractor import TextExtractor
from .product_extractor import ProductExtractor
from .parts_extractor import PartsExtractor
from .error_code_extractor import ErrorCodeExtractor
from .version_extractor import VersionExtractor
from .image_storage_processor import ImageStorageProcessor
from .image_processor import ImageProcessor
from .embedding_processor import EmbeddingProcessor
from .chunker import SmartChunker
from .link_extractor import LinkExtractor


class DocumentProcessor:
    """Main document processor - orchestrates all extraction"""
    
    def __init__(
        self,
        manufacturer: str = "AUTO",
        chunk_size: int = 1000,
        youtube_api_key: Optional[str] = None,
        chunk_overlap: int = 100,
        pdf_engine: str = "pymupdf",
        debug: bool = False,
        supabase_client=None
    ):
        """
        Initialize document processor
        
        Args:
            manufacturer: Manufacturer name (HP, Canon, AUTO, etc.)
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            pdf_engine: PDF extraction engine
            debug: Enable debug logging for product extraction
            supabase_client: Supabase client for embeddings (optional)
        """
        self.manufacturer = manufacturer
        self.debug = debug
        self.logger = get_logger()
        
        # Initialize extractors
        self.text_extractor = TextExtractor(prefer_engine=pdf_engine)
        self.product_extractor = ProductExtractor(manufacturer_name=manufacturer, debug=debug)
        self.parts_extractor = PartsExtractor()
        self.error_code_extractor = ErrorCodeExtractor()
        self.version_extractor = VersionExtractor()
        self.image_processor = ImageProcessor(supabase_client=supabase_client)
        self.image_storage = ImageStorageProcessor(supabase_client=supabase_client)
        self.embedding_processor = EmbeddingProcessor(supabase_client=supabase_client)  # FIXED: Pass supabase client!
        self.chunker = SmartChunker(chunk_size=chunk_size, overlap_size=chunk_overlap)
        self.link_extractor = LinkExtractor(youtube_api_key=youtube_api_key)
        
        # LLM extractor (optional, for specification sections)
        try:
            from .llm_extractor import LLMProductExtractor
            self.llm_extractor = LLMProductExtractor(debug=debug)
            self.use_llm = True
        except Exception as e:
            self.logger.warning(f"LLM extractor not available: {e}")
            self.llm_extractor = None
            self.use_llm = False
        
        if manufacturer == "AUTO":
            self.logger.info("Initialized processor with AUTO manufacturer detection")
        else:
            self.logger.info(f"Initialized processor for {manufacturer}")
        self.logger.info(f"PDF Engine: {pdf_engine}, Chunk Size: {chunk_size}")
        if debug:
            self.logger.info("Debug mode: ENABLED")
    
    def process_document(
        self,
        pdf_path: Path,
        document_id: Optional[UUID] = None,
        enable_log_file: bool = True
    ) -> ProcessingResult:
        """
        Process complete document
        
        Args:
            pdf_path: Path to PDF file
            document_id: Optional document UUID (generates if None)
            enable_log_file: Create a .log.txt file next to the PDF (default: True)
            
        Returns:
            ProcessingResult with all extracted data
        """
        if document_id is None:
            document_id = uuid4()
        
        start_time = time.time()
        
        # Setup document-specific log file
        log_file_path = None
        file_handler = None
        
        if enable_log_file:
            log_file_path = pdf_path.parent / f"{pdf_path.stem}.log.txt"
            file_handler = self._add_file_handler(log_file_path)
        
        self.logger.section(f"Processing Document: {pdf_path.name}")
        self.logger.info(f"Document ID: {document_id}")
        
        if enable_log_file:
            self.logger.info(f"Log file: {log_file_path}")
        
        validation_errors = []
        
        try:
            # Step 1: Extract text
            self.logger.info("Step 1/5: Extracting text from PDF...")
            page_texts, metadata = self.text_extractor.extract_text(pdf_path, document_id)
            
            if not page_texts:
                self.logger.error("No text extracted from PDF!")
                try:
                    return self._create_failed_result(
                        document_id,
                        "Text extraction failed",
                        time.time() - start_time
                    )
                except Exception as e:
                    processing_time = time.time() - start_time
                    error_message = str(e)
                    
                    self.logger.error(f"Processing failed: {error_message}")
                    self.logger.error(f"Error type: {type(e).__name__}")
                    
                    # Remove file handler on error too
                    if file_handler:
                        self._remove_file_handler(file_handler)
                        self.logger.info(f"❌ Error log saved to: {log_file_path}")
            
            # Extract products (from first page primarily)
            self.logger.info("Step 2/5: Extracting product models...")
            products = []
            
            # Re-initialize product extractor with document title for context-based series detection
            document_title = metadata.title if metadata else None
            product_extractor = ProductExtractor(
                manufacturer_name=self.manufacturer,
                debug=self.product_extractor.debug,
                document_title=document_title
            )
            
            # Try first page
            if 1 in page_texts:
                first_page_products = product_extractor.extract_from_text(
                    page_texts[1], page_number=1
                )
                products.extend(first_page_products)
            
            # Scan additional pages if no products found
            if not products and len(page_texts) > 1:
                self.logger.info("No products on first page, scanning additional pages...")
                for page_num in sorted(page_texts.keys())[:5]:  # First 5 pages
                    page_products = product_extractor.extract_from_text(
                        page_texts[page_num], page_number=page_num
                    )
                    products.extend(page_products)
            
            # Step 2b: LLM extraction from ALL pages (not just spec sections)
            if self.use_llm and self.llm_extractor:
                self.logger.info("Running LLM extraction on all pages...")
                
                # Scan first 20 pages (or all if fewer)
                pages_to_scan = min(20, len(page_texts))
                
                for page_num in sorted(page_texts.keys())[:pages_to_scan]:
                    # Skip if too short (likely not product info)
                    if len(page_texts[page_num]) < 500:
                        continue
                    
                    llm_products = self.llm_extractor.extract_from_specification_section(
                        page_texts[page_num],
                        self.manufacturer if self.manufacturer != "AUTO" else "KONICA MINOLTA",
                        page_num
                    )
                    
                    # Fix manufacturer for AUTO detection
                    if llm_products:
                        # Get detected manufacturer from first regex product
                        detected_mfr = next(
                            (p.manufacturer_name for p in products if p.extraction_method.startswith("regex")),
                            "KONICA MINOLTA"
                        )
                        for prod in llm_products:
                            if prod.manufacturer_name == "AUTO" or self.manufacturer == "AUTO":
                                prod.manufacturer_name = detected_mfr
                    
                    if llm_products:
                        if self.debug:
                            self.logger.debug(f"  Page {page_num}: Found {len(llm_products)} products")
                        products.extend(llm_products)
                
                llm_count = sum(1 for p in products if p.extraction_method == "llm")
                if llm_count > 0:
                    self.logger.success(f"LLM extracted {llm_count} products with specifications")
            
            # Global deduplication across all pages
            if products:
                products = product_extractor._deduplicate(products)
            
            # Validate products
            for product in products:
                errors = product_extractor.validate_extraction(product)
                if errors:
                    validation_errors.extend([str(e) for e in errors])
            
            self.logger.success(f"Extracted {len(products)} products")
            
            # Step 2c: Extract parts (always attempt extraction)
            self.logger.info("Step 2c/5: Extracting spare parts...")
            parts = []
            
            # Get document type for logging
            doc_type = metadata.document_type if metadata else "unknown"
            
            # Get manufacturer name for pattern matching
            part_manufacturer = None
            if products:
                # Use manufacturer from first product
                part_manufacturer = products[0].manufacturer_name
            elif self.manufacturer and self.manufacturer != "AUTO":
                part_manufacturer = self.manufacturer
            
            # Extract parts from all pages (best results for parts_catalog/service_manual)
            if doc_type in ["parts_catalog", "service_manual"]:
                self.logger.info(f"📦 Document type '{doc_type}' - extracting parts with high confidence")
            else:
                self.logger.info(f"📄 Document type '{doc_type}' - attempting parts extraction (may find fewer results)")
            
            with self.logger.progress_bar(page_texts.items(), "Scanning for parts") as progress:
                task = progress.add_task("Scanning pages", total=len(page_texts))
                
                for page_num, text in page_texts.items():
                    page_parts = self.parts_extractor.extract_parts(
                        text=text,
                        manufacturer_name=part_manufacturer,
                        page_number=page_num
                    )
                    parts.extend(page_parts)
                    progress.update(task, advance=1)
            
            if parts:
                self.logger.success(f"✅ Extracted {len(parts)} spare parts")
            else:
                self.logger.info(f">> No parts found (document type: {doc_type})")
            
            # Step 3: Extract error codes
            self.logger.info("Step 3/5: Extracting error codes...")
            error_codes = []
            
            # Get manufacturer for error code patterns
            error_manufacturer = None
            if products:
                error_manufacturer = products[0].manufacturer_name
            elif self.manufacturer and self.manufacturer != "AUTO":
                error_manufacturer = self.manufacturer
            
            with self.logger.progress_bar(page_texts.items(), "Scanning for error codes") as progress:
                task = progress.add_task("Scanning pages", total=len(page_texts))
                
                for page_num, text in page_texts.items():
                    page_codes = self.error_code_extractor.extract_from_text(
                        text=text,
                        page_number=page_num,
                        manufacturer_name=error_manufacturer
                    )
                    error_codes.extend(page_codes)
                    progress.update(task, advance=1)
            
            # Validate error codes
            for error_code in error_codes:
                errors = self.error_code_extractor.validate_extraction(error_code)
                if errors:
                    validation_errors.extend([str(e) for e in errors])
            
            self.logger.success(f"Extracted {len(error_codes)} error codes")
            
            # Save error codes immediately (don't wait until end)
            if error_codes:
                self._save_error_codes_to_db(document_id, error_codes)
            
            # Step 3b: Extract versions
            self.logger.info("Step 3b/7: Extracting document versions...")
            versions = []
            
            # Extract from first few pages (versions usually on title page)
            for page_num in sorted(page_texts.keys())[:5]:
                page_versions = self.version_extractor.extract_from_text(
                    page_texts[page_num],
                    manufacturer=self.manufacturer,
                    page_number=page_num
                )
                versions.extend(page_versions)
            
            # Get best version (highest version number or latest date)
            if versions:
                # Filter to only 'version' type (not dates, firmware, etc)
                version_types = [v for v in versions if v.version_type == 'version']
                
                if version_types:
                    # Sort by version number (extract numeric part)
                    def get_version_number(v):
                        match = re.search(r'([0-9]+(?:\.[0-9]+)?)', v.version_string)
                        if match:
                            return float(match.group(1))
                        return 0.0
                    
                    best_version = max(version_types, key=get_version_number)
                    self.logger.success(f"Extracted version: {best_version.version_string} (highest from revision list)")
                else:
                    # Fallback to highest confidence if no version type found
                    best_version = max(versions, key=lambda v: v.confidence)
                    self.logger.success(f"Extracted version: {best_version.version_string} (confidence: {best_version.confidence:.2f})")
            else:
                self.logger.info("No version found")
            
            # Step 3c: Extract images
            self.logger.info("Step 3c/8: Extracting images...")
            images = []
            image_result = self.image_processor.process_document(
                document_id=document_id,
                pdf_path=pdf_path
            )
            
            if image_result['success']:
                images = image_result['images']
                self.logger.success(f"Extracted {len(images)} images")
            else:
                self.logger.warning(f"Image extraction failed: {image_result.get('error')}")
            
            # Step 3d: Extract links and videos
            self.logger.info("Step 3d/8: Extracting links and videos...")
            links_result = self.link_extractor.extract_from_document(
                pdf_path=pdf_path,
                page_texts=page_texts,
                document_id=document_id
            )
            links = links_result.get('links', [])
            videos = links_result.get('videos', [])
            
            # Analyze video thumbnails with OCR and Vision AI
            if videos:
                self.logger.info(f"Analyzing {len(videos)} video thumbnails...")
                analyzed_count = 0
                for video in videos:
                    try:
                        analyzed_video = self.link_extractor.analyze_video_thumbnail(
                            video_metadata=video,
                            enable_ocr=True,
                            enable_vision=True
                        )
                        # Update video with analysis results
                        video.update(analyzed_video)
                        
                        if 'thumbnail_ai_description' in analyzed_video or 'thumbnail_ocr_text' in analyzed_video:
                            analyzed_count += 1
                    except Exception as e:
                        self.logger.debug(f"Thumbnail analysis failed for video {video.get('youtube_id')}: {e}")
                
                if analyzed_count > 0:
                    self.logger.success(f"✅ Analyzed {analyzed_count}/{len(videos)} video thumbnails")
            
            if links:
                self.logger.success(f"Extracted {len(links)} links ({len(videos)} videos)")
            
            # Step 4: Create chunks
            self.logger.info("Step 4/8: Chunking text...")
            chunks = self.chunker.chunk_document(page_texts, document_id)
            
            # Deduplicate
            chunks = self.chunker.deduplicate_chunks(chunks)
            
            self.logger.success(f"Created {len(chunks)} chunks")
            
            # Step 5: Save links and videos to database
            self.logger.info("Step 5/8: Saving links and videos...")
            if links:
                self._save_links_to_db(links)
            if videos:
                self._save_videos_to_db(videos)
            
            # Step 6: Statistics
            self.logger.info("Step 6/8: Calculating statistics...")
            statistics = self._calculate_statistics(
                page_texts, products, error_codes, versions, images, chunks
            )
            statistics['links_count'] = len(links)
            statistics['videos_count'] = len(videos)
            statistics['parts_count'] = len(parts)
            
            # Create result
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                document_id=document_id,
                success=True,
                metadata=metadata,
                chunks=chunks,
                products=products,
                parts=parts,
                error_codes=error_codes,
                versions=versions,
                links=links,
                videos=videos,
                validation_errors=validation_errors,
                processing_time_seconds=processing_time,
                statistics=statistics
            )
            
            # Log summary
            log_processing_summary(
                self.logger,
                result.to_summary_dict(),
                processing_time
            )
            
            # Remove file handler
            if file_handler:
                self._remove_file_handler(file_handler)
                self.logger.info(f"✅ Log saved to: {log_file_path}")
            
            # Convert to dict for pipeline consumption
            result_dict = result.to_dict()
            
            # Add images to result
            result_dict['images'] = images
            
            return result_dict
        
        except Exception as e:
            self.logger.error(f"Processing failed: {e}", exc=e)
            processing_time = time.time() - start_time
            
            # Remove file handler on error
            if file_handler:
                self._remove_file_handler(file_handler)
                self.logger.info(f"❌ Error log saved to: {log_file_path}")
            
            return self._create_failed_result(
                document_id,
                str(e),
                processing_time
            )
    
    def upload_images_to_storage(
        self,
        document_id: UUID,
        images: List[Dict],
        document_type: str = "service_manual"
    ) -> Dict:
        """
        Upload extracted images to R2 storage
        
        Note: PDFs stay local! We only upload extracted images.
        
        Args:
            document_id: Document UUID
            images: List of extracted images with paths
            document_type: Type of document
            
        Returns:
            Dict with upload result
        """
        if not self.image_storage.is_configured():
            self.logger.info("Image storage not configured - skipping upload")
            return {
                'success': False,
                'error': 'R2 storage not configured',
                'skipped': True
            }
        
        try:
            self.logger.info(f"Uploading {len(images)} images to R2...")
            
            result = self.image_storage.upload_images(
                document_id=document_id,
                images=images,
                document_type=document_type
            )
            
            if result['success']:
                self.logger.success(f"Uploaded {result['uploaded_count']} images to R2")
            else:
                self.logger.warning(f"Some images failed: {result.get('failed_count', 0)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Image upload error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_embeddings(
        self,
        document_id: UUID,
        chunks: List[Dict]
    ) -> Dict:
        """
        Generate vector embeddings for chunks
        
        Note: This enables semantic search!
        
        Args:
            document_id: Document UUID
            chunks: List of chunks with text
            
        Returns:
            Dict with embedding result
        """
        if not self.embedding_processor.is_configured():
            # Get detailed status for debugging
            status = self.embedding_processor.get_configuration_status()
            
            self.logger.warning("⚠️  EMBEDDING PROCESSOR NOT CONFIGURED!")
            self.logger.warning("=" * 60)
            self.logger.warning("Configuration Status:")
            self.logger.warning(f"  • Ollama Available: {status['ollama_available']}")
            self.logger.warning(f"  • Ollama URL: {status['ollama_url']}")
            self.logger.warning(f"  • Model Name: {status['model_name']}")
            self.logger.warning(f"  • Supabase Configured: {status['supabase_configured']}")
            self.logger.warning("=" * 60)
            
            if not status['ollama_available']:
                self.logger.error("❌ Ollama is NOT available!")
                self.logger.info("   Fix: 1. Start Ollama: ollama serve")
                self.logger.info(f"        2. Install model: ollama pull {status['model_name']}")
                self.logger.info(f"        3. Check URL: {status['ollama_url']}")
            
            if not status['supabase_configured']:
                self.logger.error("❌ Supabase client is NOT configured!")
                self.logger.info("   Fix: Pass supabase_client to DocumentProcessor")
            
            self.logger.warning("⚠️  Embeddings will be SKIPPED - semantic search won't work!")
            
            return {
                'success': False,
                'error': 'Embedding processor not configured',
                'skipped': True,
                'status': status
            }
        
        try:
            self.logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            
            # Chunks might be objects OR dicts - handle both!
            chunks_dict = []
            for chunk in chunks:
                # Check if it's already a dict or an object
                if isinstance(chunk, dict):
                    # Already a dict, use as-is
                    chunk_dict = chunk
                else:
                    # It's a TextChunk object, convert to dict
                    chunk_dict = {
                        'chunk_id': str(chunk.chunk_id),
                        'text': chunk.text,
                        'chunk_index': chunk.chunk_index,
                        'page_start': chunk.page_start,
                        'page_end': chunk.page_end,
                        'chunk_type': chunk.chunk_type,
                        'fingerprint': chunk.fingerprint,
                        'metadata': chunk.metadata  # ← CRITICAL: This includes header metadata!
                    }
                chunks_dict.append(chunk_dict)
            
            result = self.embedding_processor.process_document(
                document_id=document_id,
                chunks=chunks_dict
            )
            
            if result['success']:
                self.logger.success(
                    f"Created {result['embeddings_created']} embeddings "
                    f"in {result['processing_time']:.1f}s"
                )
            else:
                self.logger.warning(f"Some chunks failed: {result.get('failed_count', 0)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Embedding generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_links_to_db(self, links: List[Dict]):
        """Save extracted links to database with auto-linked manufacturer/series"""
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping link storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            for link in links:
                # Check for duplicate
                existing = supabase.table('links') \
                    .select('id') \
                    .eq('document_id', link['document_id']) \
                    .eq('url', link['url']) \
                    .limit(1) \
                    .execute()
                
                if not existing.data:
                    # Insert link
                    result = supabase.table('links').insert(link).execute()
                    
                    # Auto-link manufacturer/series from document (Migration 28 helper function)
                    if result.data and len(result.data) > 0:
                        link_id = result.data[0]['id']
                        try:
                            supabase.rpc('auto_link_resource_to_document', {
                                'p_resource_table': 'krai_content.links',
                                'p_resource_id': link_id,
                                'p_document_id': link['document_id']
                            }).execute()
                        except Exception as link_error:
                            self.logger.debug(f"Could not auto-link manufacturer/series: {link_error}")
            
            self.logger.success(f"Saved {len(links)} links to database")
        except Exception as e:
            self.logger.error(f"Failed to save links: {e}")
    
    def _save_videos_to_db(self, videos: List[Dict]):
        """Save video metadata to database with auto-linked manufacturer/series"""
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping video storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            for video in videos:
                # Check for duplicate by youtube_id
                should_insert = False
                if video.get('youtube_id'):
                    existing = supabase.table('videos') \
                        .select('id') \
                        .eq('youtube_id', video['youtube_id']) \
                        .limit(1) \
                        .execute()
                    should_insert = not existing.data
                else:
                    should_insert = True
                
                if should_insert:
                    result = supabase.table('videos').insert(video).execute()
                    
                    # Auto-link manufacturer/series via link_id (videos → links → document)
                    if result.data and len(result.data) > 0 and video.get('link_id'):
                        video_id = result.data[0]['id']
                        try:
                            # Get document_id from link
                            link_result = supabase.table('links').select('document_id').eq('id', video['link_id']).single().execute()
                            if link_result.data:
                                supabase.rpc('auto_link_resource_to_document', {
                                    'p_resource_table': 'krai_content.videos',
                                    'p_resource_id': video_id,
                                    'p_document_id': link_result.data['document_id']
                                }).execute()
                        except Exception as video_error:
                            self.logger.debug(f"Could not auto-link manufacturer/series: {video_error}")
            
            self.logger.success(f"Saved {len(videos)} videos to database")
        except Exception as e:
            self.logger.error(f"Failed to save videos: {e}")
    
    def _save_error_codes_to_db(self, document_id: UUID, error_codes: list):
        """Save error codes immediately after extraction"""
        try:
            from supabase import create_client
            from datetime import datetime
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping error code storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            # AUTO-CREATE MANUFACTURER IF MISSING
            manufacturer_id = None
            if manufacturer_name:
                try:
                    # Check if manufacturer exists
                    result = supabase.table('krai_core.manufacturers').select('id').eq('name', manufacturer_name).execute()
                    if result.data:
                        manufacturer_id = result.data[0]['id']
                        self.logger.info(f"✅ Found existing manufacturer: {manufacturer_name} ({manufacturer_id})")
                    else:
                        # Auto-create manufacturer
                        result = supabase.table('krai_core.manufacturers').insert({
                            'name': manufacturer_name,
                            'description': f'Auto-created for {manufacturer_name} error code processing',
                            'is_active': True
                        }).execute()

                        if result.data:
                            manufacturer_id = result.data[0]['id']
                            self.logger.success(f"🔨 Auto-created manufacturer: {manufacturer_name} ({manufacturer_id})")

                except Exception as e:
                    self.logger.error(f"❌ Failed to get/create manufacturer '{manufacturer_name}': {e}")

            # CRITICAL: Skip if no manufacturer_id found
            if not manufacturer_id:
                self.logger.warning(f"⚠️ No manufacturer_id for manufacturer '{manufacturer_name}' - skipping error codes")
                saved_count = 0
                continue
            
            for error_code in error_codes:
                
                # Build metadata with smart matching info
                metadata = {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'extraction_method': ec_data.get('extraction_method', 'regex_pattern')
                if ec_data.get('context_text'):
                    metadata['context'] = ec_data.get('context_text')
                
                # USE RPC FUNCTION to bypass PostgREST schema cache!
                # Direct INSERT via PostgREST fails due to cache issues
                result = supabase.rpc('insert_error_code', {
                    'p_document_id': str(document_id),
                    'p_manufacturer_id': manufacturer_id,
                    'p_error_code': ec_data.get('error_code'),
                    'p_error_description': ec_data.get('error_description'),
                    'p_solution_text': ec_data.get('solution_text'),
                    'p_confidence_score': ec_data.get('confidence', 0.8),
                    'p_page_number': ec_data.get('page_number'),
                    'p_severity_level': ec_data.get('severity_level', 'medium'),
                    'p_extraction_method': ec_data.get('extraction_method', 'regex_pattern'),
                    'p_requires_technician': ec_data.get('requires_technician', False),
                    'p_requires_parts': ec_data.get('requires_parts', False),
                    'p_context_text': ec_data.get('context_text'),
                    'p_metadata': metadata
                }).execute()
                
                if result.data:
                    saved_count += 1
            
            self.logger.success(f"💾 Saved {saved_count} error codes to DB")
            
        except Exception as e:
            self.logger.error(f"Failed to save error codes: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def _calculate_statistics(
        self,
        page_texts: Dict[int, str],
        products: List,
        error_codes: List,
        versions: List,
        images: List[Dict],
        chunks: List
    ) -> Dict[str, Any]:
        """Calculate processing statistics"""
        total_chars = sum(len(text) for text in page_texts.values())
        total_words = sum(len(text.split()) for text in page_texts.values())
        
        # Chunk types distribution
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        # Product confidence
        avg_product_conf = (
            sum(p.confidence for p in products) / len(products)
            if products else 0
        )
        
        # Error code confidence
        avg_error_conf = (
            sum(e.confidence for e in error_codes) / len(error_codes)
            if error_codes else 0
        )
        
        # Version confidence
        avg_version_conf = (
            sum(v.confidence for v in versions) / len(versions)
            if versions else 0
        )
        
        # Image types distribution
        image_types = {}
        for img in images:
            img_type = img.get('type', 'unknown')
            image_types[img_type] = image_types.get(img_type, 0) + 1
        
        return {
            'total_pages': len(page_texts),
            'total_characters': total_chars,
            'total_words': total_words,
            'total_chunks': len(chunks),
            'total_products': len(products),
            'total_error_codes': len(error_codes),
            'total_versions': len(versions),
            'total_images': len(images),
            'avg_product_confidence': round(avg_product_conf, 2),
            'avg_error_code_confidence': round(avg_error_conf, 2),
            'avg_version_confidence': round(avg_version_conf, 2),
            'chunk_types': chunk_types,
            'image_types': image_types,
            'avg_chunk_size': round(total_chars / len(chunks), 0) if chunks else 0
        }
    
    def _add_file_handler(self, log_file_path: Path) -> 'logging.FileHandler':
        """Add file handler to logger for document-specific logging"""
        import logging
        
        # Ensure parent directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Format with timestamp
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add to logger
        self.logger.logger.addHandler(file_handler)
        
        return file_handler
    
    def _remove_file_handler(self, file_handler: 'logging.FileHandler'):
        """Remove file handler from logger"""
        if file_handler:
            file_handler.flush()
            file_handler.close()
            self.logger.logger.removeHandler(file_handler)
    
    def _create_failed_result(
        self,
        document_id: UUID,
        error_message: str,
        processing_time: float
    ) -> Dict[str, Any]:
        """Create failed processing result as dict"""
        return {
            'success': False,
            'document_id': str(document_id),
            'error': error_message,
            'metadata': {
                'page_count': 0,
                'file_size_bytes': 0,
            },
            'chunks': [],
            'products': [],
            'error_codes': [],
            'versions': [],
            'images': [],
            'statistics': {'error': error_message},
            'processing_time': processing_time
        }


# Convenience function
def process_pdf(
    pdf_path: Path,
    manufacturer: str = "HP",
    document_id: Optional[UUID] = None
) -> ProcessingResult:
    """
    Convenience function to process PDF
    
    Args:
        pdf_path: Path to PDF file
        manufacturer: Manufacturer name
        document_id: Optional document UUID
        
    Returns:
        ProcessingResult
    """
    processor = DocumentProcessor(manufacturer=manufacturer)
    return processor.process_document(pdf_path, document_id)
