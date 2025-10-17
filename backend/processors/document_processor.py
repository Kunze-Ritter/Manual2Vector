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
from .exceptions import ManufacturerNotFoundError


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
        
        # Use existing image_processor for Vision AI (initialized below)
        # We'll pass it to parts_extractor after initialization
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
        
        # Handle .pdfz (compressed) files
        working_pdf = pdf_path
        temp_decompressed = None
        
        if pdf_path.suffix.lower() == '.pdfz':
            self.logger.info("🗜️  Decompressing .pdfz file...")
            temp_decompressed = pdf_path.with_suffix('.pdf')
            try:
                import gzip
                import shutil
                with gzip.open(pdf_path, 'rb') as f_in:
                    with open(temp_decompressed, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                working_pdf = temp_decompressed
                self.logger.success(f"✅ Decompressed to: {working_pdf.name}")
            except Exception as e:
                # Not gzipped - treat as normal PDF
                with open(pdf_path, 'rb') as f:
                    header = f.read(4)
                    if header.startswith(b'%PDF'):
                        self.logger.info("⚠️  Not gzipped - treating as normal PDF")
                        shutil.copy(pdf_path, temp_decompressed)
                        working_pdf = temp_decompressed
                    else:
                        raise ValueError(f"Invalid PDF file: {pdf_path.name}")
        
        validation_errors = []
        
        try:
            # Step 1: Extract text
            self.logger.info("Step 1/5: Extracting text from PDF...")
            page_texts, metadata = self.text_extractor.extract_text(working_pdf, document_id)
            
            # CRITICAL: Detect manufacturer EARLY from 3 sources (filename, metadata, document text)
            # This ensures _save_error_codes_to_db can find the manufacturer
            detected_manufacturer = self.manufacturer
            if detected_manufacturer == "AUTO":
                self.logger.info("🔍 Auto-detecting manufacturer from multiple sources...")
                
                # Source 1: Filename
                filename_lower = pdf_path.stem.lower()
                self.logger.info(f"   📄 Filename: '{pdf_path.stem}'")
                
                # Source 2: PDF Metadata (Title)
                title_lower = (metadata.title or "").lower() if metadata else ""
                if metadata and metadata.title:
                    self.logger.info(f"   📋 Title: '{metadata.title}'")
                else:
                    self.logger.info(f"   📋 Title: (none)")
                
                # Source 3: PDF Metadata (Author)
                author_lower = (metadata.author or "").lower() if metadata else ""
                if metadata and metadata.author:
                    self.logger.info(f"   ✍️  Author: '{metadata.author}'")
                else:
                    self.logger.info(f"   ✍️  Author: (none)")
                
                # Source 4: First 3 pages of document text
                first_pages_text = ""
                if page_texts:
                    first_page_keys = sorted(page_texts.keys())[:3]
                    first_pages_text = ' '.join([page_texts[p] for p in first_page_keys])
                    first_pages_text = first_pages_text[:2000].lower()  # Limit to 2000 chars
                    self.logger.info(f"   📖 Text sample: First 3 pages ({len(first_pages_text)} chars)")
                
                # Use manufacturer normalizer for comprehensive patterns
                from utils.manufacturer_normalizer import MANUFACTURER_MAP
                
                # Build detection patterns from normalizer (lowercase for matching)
                mfr_patterns = {}
                for canonical, aliases in MANUFACTURER_MAP.items():
                    # Use canonical name as key, all aliases as patterns
                    key = canonical.lower().replace(' ', '_')
                    patterns = [alias.lower() for alias in aliases]
                    mfr_patterns[key] = patterns
                
                # Weighted validation: Filename > Author > Title > Text
                # Use scoring system to prioritize more reliable sources
                detection_scores = {}
                for mfr_key, keywords in mfr_patterns.items():
                    score = 0
                    sources = []
                    
                    # Check filename (highest weight - most reliable)
                    filename_match = any(kw in filename_lower for kw in keywords)
                    if filename_match:
                        score += 10  # Strong signal
                        sources.append("filename")
                    
                    # Check metadata author (very high weight - very reliable!)
                    author_match = any(kw in author_lower for kw in keywords)
                    if author_match:
                        score += 8  # Very strong signal (e.g., "Lexmark International")
                        sources.append("author")
                    
                    # Check metadata title (medium weight)
                    title_match = any(kw in title_lower for kw in keywords)
                    if title_match:
                        score += 5  # Medium signal
                        sources.append("title")
                    
                    # Check document text - first 3 pages only (lowest weight)
                    # Count occurrences to distinguish between main manufacturer and mentions
                    text_matches = sum(1 for kw in keywords if kw in first_pages_text)
                    if text_matches > 0:
                        # Only add score if manufacturer appears multiple times (not just mentioned)
                        if text_matches >= 3:
                            score += 3  # Multiple mentions
                            sources.append(f"text({text_matches}x)")
                        elif text_matches >= 2:
                            score += 2  # Few mentions
                            sources.append(f"text({text_matches}x)")
                        else:
                            score += 1  # Single mention (weak signal)
                            sources.append(f"text({text_matches}x)")
                    
                    if score > 0:
                        detection_scores[mfr_key] = {'score': score, 'sources': sources}
                
                # Select manufacturer with highest score
                if detection_scores:
                    self.logger.info("")
                    self.logger.info("📊 Detection Results:")
                    
                    # Show top 3 candidates
                    sorted_scores = sorted(detection_scores.items(), key=lambda x: x[1]['score'], reverse=True)
                    for i, (mfr, data) in enumerate(sorted_scores[:3], 1):
                        icon = "🏆" if i == 1 else "  "
                        mfr_display = mfr.replace('_', ' ').title()
                        
                        # Format sources with details
                        source_details = []
                        for src in data['sources']:
                            if 'filename' in src:
                                source_details.append("📄 Filename")
                            elif 'author' in src:
                                source_details.append("✍️  Author")
                            elif 'title' in src:
                                source_details.append("📋 Title")
                            elif src.startswith('text('):
                                count = src[5:-2]
                                source_details.append(f"📖 Text ({count} mentions)")
                        
                        self.logger.info(f"   {icon} {mfr_display}: {data['score']} points")
                        self.logger.info(f"      Sources: {', '.join(source_details)}")
                    
                    # Select best match
                    best_match = max(detection_scores.items(), key=lambda x: x[1]['score'])
                    mfr_key = best_match[0]
                    score = best_match[1]['score']
                    sources = best_match[1]['sources']
                    
                    # Convert to canonical name using normalizer
                    from utils.manufacturer_normalizer import normalize_manufacturer
                    
                    # First get the display name
                    detected_manufacturer = mfr_key.upper().replace('_', ' ').title()
                    
                    # Then normalize it to canonical form
                    canonical_name = normalize_manufacturer(detected_manufacturer)
                    if canonical_name:
                        detected_manufacturer = canonical_name
                    
                    self.logger.info("")
                    self.logger.success(f"✅ Selected: {detected_manufacturer} (score: {score})")
                    
                    # Confidence levels based on score
                    if score >= 18:  # Filename + Author + Title
                        self.logger.success(f"   ✅ Excellent confidence (filename + author + title)")
                    elif score >= 15:  # Filename + Author or Filename + Title + Text
                        self.logger.success(f"   ✅ Very high confidence (multiple sources)")
                    elif score >= 10:  # Filename match
                        self.logger.success(f"   ✅ High confidence (filename match)")
                    elif score >= 8:  # Author match
                        self.logger.success(f"   ✅ High confidence (author metadata)")
                    elif score >= 5:  # Title match
                        self.logger.info(f"   ℹ️  Medium confidence (title match)")
                    else:  # Text only
                        self.logger.warning(f"   ⚠️  Low confidence (text only)")
                    
                    # NOTE: Do NOT update self.manufacturer here!
                    # That would affect ALL subsequent documents in batch processing.
                    # Use detected_manufacturer as local variable instead.
            
            # Save manufacturer to document IMMEDIATELY (with manufacturer_id!)
            if detected_manufacturer and detected_manufacturer != "AUTO":
                try:
                    from supabase import create_client
                    import os
                    from dotenv import load_dotenv
                    
                    load_dotenv()
                    supabase_url = os.getenv('SUPABASE_URL')
                    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    
                    if supabase_url and supabase_key:
                        supabase = create_client(supabase_url, supabase_key)
                        
                        # Ensure manufacturer exists and get ID
                        try:
                            manufacturer_id = self._ensure_manufacturer_exists(detected_manufacturer, supabase)
                            
                            # Use RPC function to bypass PostgREST schema cache issues
                            supabase.rpc('update_document_manufacturer', {
                                'p_document_id': str(document_id),
                                'p_manufacturer': detected_manufacturer,
                                'p_manufacturer_id': str(manufacturer_id)
                            }).execute()
                            
                            self.logger.info(f"✅ Set document manufacturer: {detected_manufacturer} (ID: {manufacturer_id})")
                        except Exception as mfr_error:
                            # Fallback: Just set manufacturer string via table update
                            try:
                                supabase.table('vw_documents').update({
                                    'manufacturer': detected_manufacturer
                                }).eq('id', str(document_id)).execute()
                                self.logger.warning(f"Set manufacturer string only (RPC failed): {mfr_error}")
                            except Exception as fallback_error:
                                self.logger.error(f"Failed to set manufacturer: {fallback_error}")
                except Exception as e:
                    self.logger.warning(f"Failed to set manufacturer early: {e}")
            
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
                manufacturer_name=detected_manufacturer,
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
                
                # CONFIGURABLE: Scan first N pages (default: 20)
                # Why limit? LLM is slow (~8s/page). For 278 pages = 37 minutes!
                # Product info is usually in first 20 pages (specs, features, models)
                # Pages 21+ are mostly error codes, maintenance, parts (no new products)
                # 
                # To scan ALL pages: Set LLM_MAX_PAGES=0 in environment
                # To scan more: Set LLM_MAX_PAGES=50 (or any number)
                import os
                llm_max_pages_env = os.getenv('LLM_MAX_PAGES', '20')
                self.logger.debug(f"🔍 DEBUG: LLM_MAX_PAGES env var = '{llm_max_pages_env}'")
                max_pages = int(llm_max_pages_env)
                self.logger.debug(f"🔍 DEBUG: max_pages parsed = {max_pages}")
                pages_to_scan = len(page_texts) if max_pages == 0 else min(max_pages, len(page_texts))
                self.logger.debug(f"🔍 DEBUG: pages_to_scan = {pages_to_scan}, total pages = {len(page_texts)}")
                
                if pages_to_scan < len(page_texts):
                    self.logger.info(f"   → Scanning first {pages_to_scan} pages (set LLM_MAX_PAGES=0 to scan all {len(page_texts)} pages)")
                else:
                    self.logger.info(f"   → Scanning all {pages_to_scan} pages")
                
                # Progress tracking for LLM extraction
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
                
                pages_to_process = sorted(page_texts.keys())[:pages_to_scan]
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=None
                ) as progress:
                    task = progress.add_task(
                        f"[cyan]LLM scanning pages...",
                        total=len(pages_to_process)
                    )
                    
                    for page_num in pages_to_process:
                        # Skip if too short (likely not product info)
                        if len(page_texts[page_num]) < 500:
                            progress.update(task, advance=1)
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
                        
                        progress.update(task, advance=1)
                
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
            
            # Save products to database
            if products:
                saved_products = self._save_products_to_db(document_id, products)
                
                # Step 2b: Series Detection (immediately after products!)
                if saved_products:
                    self.logger.info(f"Step 2b/5: Detecting and linking series for {len(saved_products)} products...")
                    series_stats = self._detect_and_link_series(saved_products)
                    self.logger.info(f"   Series stats: {series_stats['series_detected']} detected, {series_stats['series_created']} created, {series_stats['products_linked']} linked")
                    if series_stats['series_created'] > 0 or series_stats['products_linked'] > 0:
                        self.logger.success(f"✅ Series: {series_stats['series_created']} created, {series_stats['products_linked']} products linked")
                        
                        # Step 2b.1: Update product types after series linking
                        self.logger.info("   🔄 Updating product types based on series...")
                        self._update_product_types_after_series(saved_products)
                    elif series_stats['series_detected'] == 0:
                        self.logger.info("   ℹ️  No series patterns detected in product models")
                else:
                    self.logger.debug("   ⏭️  Skipped series detection (no products saved)")
            
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
            elif detected_manufacturer and detected_manufacturer != "AUTO":
                part_manufacturer = detected_manufacturer
            
            # Extract parts from all pages (best results for parts_catalog/service_manual)
            if doc_type in ["parts_catalog", "service_manual"]:
                self.logger.info(f"📦 Document type '{doc_type}' - extracting parts with high confidence")
            else:
                self.logger.info(f"📄 Document type '{doc_type}' - attempting parts extraction (may find fewer results)")
            
            parts_count = 0
            with self.logger.progress_bar(page_texts.items(), "Scanning for parts") as progress:
                task = progress.add_task(f"Parts found: {parts_count}", total=len(page_texts))
                
                for page_num, text in page_texts.items():
                    page_parts = self.parts_extractor.extract_parts(
                        text=text,
                        manufacturer_name=part_manufacturer,
                        page_number=page_num
                    )
                    parts.extend(page_parts)
                    parts_count = len(parts)
                    progress.update(task, advance=1, description=f"Parts found: {parts_count}")
            
            if parts:
                # TODO: Vision AI enrichment for parts (requires analyze_page method in image_processor)
                # For now, rely on improved pattern matching
                parts_without_names = sum(1 for p in parts if not p.part_name)
                if parts_without_names > 0:
                    self.logger.info(f"ℹ️  {parts_without_names} parts without names (Vision AI not yet implemented)")
                
                self.logger.success(f"✅ Extracted {len(parts)} spare parts")
                # Save parts immediately (like error codes)
                self._save_parts_to_db(document_id, parts, detected_manufacturer)
            else:
                self.logger.info(f">> No parts found (document type: {doc_type})")
            
            # Step 3: Extract error codes
            self.logger.info("Step 3/5: Extracting error codes...")
            error_codes = []
            
            # Get manufacturer for error code patterns
            error_manufacturer = None
            if products:
                error_manufacturer = products[0].manufacturer_name
            elif detected_manufacturer and detected_manufacturer != "AUTO":
                error_manufacturer = detected_manufacturer
            
            error_codes_count = 0
            page_count = 0
            update_interval = max(1, len(page_texts) // 50)  # Update progress bar max 50 times
            
            with self.logger.progress_bar(page_texts.items(), "Scanning for error codes") as progress:
                task = progress.add_task(f"Error codes found: {error_codes_count}", total=len(page_texts))
                
                for page_num, text in page_texts.items():
                    page_codes = self.error_code_extractor.extract_from_text(
                        text=text,
                        page_number=page_num,
                        manufacturer_name=error_manufacturer
                    )
                    error_codes.extend(page_codes)
                    error_codes_count = len(error_codes)
                    page_count += 1
                    
                    # PERFORMANCE: Only update progress bar every N pages to avoid UI overhead
                    if page_count % update_interval == 0 or page_count == len(page_texts):
                        progress.update(task, advance=update_interval, description=f"Error codes found: {error_codes_count}")
            
            # Enrich error codes with full details from entire document
            if error_codes:
                self.logger.info(f"Enriching {len(error_codes)} error codes with full document context...")
                full_text = '\n\n'.join(page_texts.values())
                
                # Extract product series for OEM detection
                product_series = None
                if products:
                    # Use first product's series or model for OEM detection
                    first_product = products[0]
                    product_series = first_product.product_series or first_product.model_number
                
                error_codes = self.error_code_extractor.enrich_error_codes_from_document(
                    error_codes=error_codes,
                    full_document_text=full_text,
                    manufacturer_name=error_manufacturer,
                    product_series=product_series
                )
                self.logger.success(f"Enriched error codes with detailed solutions")
            
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
                    manufacturer=detected_manufacturer,
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
                pdf_path=working_pdf
            )
            
            if image_result['success']:
                images = image_result['images']
                self.logger.success(f"✅ Image processing complete: {len(images)} images ready")
                
                # Save images to database (AFTER Vision AI has run!)
                # Vision AI adds ai_description, ai_confidence, contains_text
                if images:
                    self._save_images_to_db(document_id, images)
                    self.logger.debug(f"Saved {len(images)} images with Vision AI descriptions to DB")
            else:
                self.logger.warning(f"Image extraction failed: {image_result.get('error')}")
            
            # Step 3d: Extract links and videos
            self.logger.info("Step 3d/8: Extracting links and videos...")
            links_result = self.link_extractor.extract_from_document(
                pdf_path=working_pdf,
                page_texts=page_texts,
                document_id=document_id
            )
            links = links_result.get('links', [])
            videos = links_result.get('videos', [])
            
            # Analyze video thumbnails with OCR and Vision AI
            if videos:
                self.logger.info(f"   → Analyzing {len(videos)} video thumbnails...")
                analyzed_count = 0
                failed_count = 0
                
                with self.logger.progress_bar(videos, "Analyzing video thumbnails") as progress:
                    task = progress.add_task(f"Analyzed: {analyzed_count} videos", total=len(videos))
                    
                    for idx, video in enumerate(videos, 1):
                        video_title = video.get('title', video.get('youtube_id', 'Unknown'))[:50]
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
                            failed_count += 1
                            self.logger.warning(f"      Failed to analyze video: {e}")
                        
                        # Update progress
                        progress.update(task, advance=1, description=f"Analyzed: {analyzed_count} videos")
                
                # Summary
                if analyzed_count > 0:
                    self.logger.success(f"   ✅ Video thumbnail analysis: {analyzed_count} successful, {failed_count} failed, {len(videos) - analyzed_count - failed_count} skipped")
            
            if links:
                self.logger.success(f"Extracted {len(links)} links ({len(videos)} videos)")
            
            # Step 4: Create chunks
            self.logger.info("Step 4/8: Chunking text...")
            chunks = self.chunker.chunk_document(page_texts, document_id)
            
            # Deduplicate
            chunks = self.chunker.deduplicate_chunks(chunks)
            
            self.logger.success(f"Created {len(chunks)} chunks")
            
            # Step 4b: Link error codes to chunks (now that chunks exist!)
            if error_codes:
                self.logger.info("Step 4b/8: Linking error codes to chunks...")
                linked_count = self._link_error_codes_to_chunks(document_id)
                if linked_count > 0:
                    self.logger.success(f"✅ Linked {linked_count} error codes to chunks")
            
            # Step 5: Save links and videos to database (links FIRST!)
            self.logger.info("Step 5/8: Saving links and videos...")
            # Save links FIRST because videos reference link_id
            link_id_map = {}
            if links:
                link_id_map = self._save_links_to_db(links)
            # Then save videos (which have link_id foreign key)
            if videos:
                self._save_videos_to_db(videos, link_id_map)
            
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
            
            # Step 7: Save document to database
            self.logger.info("Step 7/8: Saving document to database...")
            self._save_document_to_db(
                document_id=document_id,
                pdf_path=pdf_path,
                metadata=metadata,
                statistics=statistics,
                detected_manufacturer=detected_manufacturer
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
        
        finally:
            # Cleanup temporary decompressed file
            if temp_decompressed and temp_decompressed.exists():
                try:
                    temp_decompressed.unlink()
                    self.logger.debug(f"Cleaned up temporary file: {temp_decompressed.name}")
                except Exception as cleanup_error:
                    self.logger.debug(f"Could not cleanup temp file: {cleanup_error}")
    
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
    
    def _ensure_manufacturer_exists(self, manufacturer_name: str, supabase) -> Optional[UUID]:
        """
        Ensure manufacturer exists in database, create if needed
        
        Args:
            manufacturer_name: Name of manufacturer (e.g., "HP", "Konica Minolta", "hp inc", "KM")
            supabase: Supabase client instance
            
        Returns:
            manufacturer_id (UUID) if found/created, None if failed
            
        Raises:
            ManufacturerNotFoundError: If manufacturer cannot be created
        """
        if not manufacturer_name:
            return None
        
        try:
            # Normalize manufacturer name first
            from utils.manufacturer_normalizer import normalize_manufacturer
            canonical_name = normalize_manufacturer(manufacturer_name)
            if canonical_name:
                self.logger.debug(f"Normalized '{manufacturer_name}' -> '{canonical_name}'")
                manufacturer_name = canonical_name
            
            # 1. Try to find existing manufacturer (case-insensitive exact match on canonical name)
            result = supabase.table('vw_manufacturers') \
                .select('id, name') \
                .ilike('name', manufacturer_name) \
                .limit(1) \
                .execute()
            
            if result.data:
                manufacturer_id = result.data[0]['id']
                existing_name = result.data[0]['name']
                self.logger.debug(f"Found existing manufacturer: '{existing_name}' (ID: {manufacturer_id})")
                return manufacturer_id
            
            # 2. Manufacturer not found - create new entry
            self.logger.info(f"📝 Creating new manufacturer entry: {manufacturer_name}")
            
            create_result = supabase.table('vw_manufacturers') \
                .insert({'name': manufacturer_name}) \
                .execute()
            
            if create_result.data:
                manufacturer_id = create_result.data[0]['id']
                self.logger.success(f"✅ Created manufacturer: {manufacturer_name} (ID: {manufacturer_id})")
                return manufacturer_id
            else:
                # Creation failed
                raise ManufacturerNotFoundError(
                    manufacturer=manufacturer_name,
                    reason="Database insert returned no data"
                )
        
        except Exception as e:
            if isinstance(e, ManufacturerNotFoundError):
                raise
            
            self.logger.error(f"Failed to ensure manufacturer exists: {e}")
            raise ManufacturerNotFoundError(
                manufacturer=manufacturer_name,
                reason=str(e)
            )
    
    def _save_links_to_db(self, links: List[Dict]) -> Dict[str, str]:
        """
        Save extracted links to database with auto-linked manufacturer/series
        
        Returns:
            Dict mapping original link URLs to their database IDs (for video linking)
        """
        link_id_map = {}  # url -> link_id mapping
        
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping link storage")
                return link_id_map
            
            supabase = create_client(supabase_url, supabase_key)
            
            for link in links:
                # Check for duplicate
                existing = supabase.table('vw_links') \
                    .select('id') \
                    .eq('document_id', link['document_id']) \
                    .eq('url', link['url']) \
                    .limit(1) \
                    .execute()
                
                if existing.data:
                    # Link already exists - use existing ID
                    link_id = existing.data[0]['id']
                    link_id_map[link['url']] = link_id
                else:
                    # Insert new link
                    result = supabase.table('vw_links').insert(link).execute()
                    
                    if result.data and len(result.data) > 0:
                        link_id = result.data[0]['id']
                        link_id_map[link['url']] = link_id
                        
                        # Auto-link manufacturer/series from document
                        try:
                            supabase.rpc('auto_link_resource_to_document', {
                                'p_resource_table': 'krai_content.links',
                                'p_resource_id': link_id,
                                'p_document_id': link['document_id']
                            }).execute()
                        except Exception as link_error:
                            self.logger.debug(f"Could not auto-link manufacturer/series: {link_error}")
            
            self.logger.success(f"Saved {len(links)} links to database")
            return link_id_map
            
        except Exception as e:
            self.logger.error(f"Failed to save links: {e}")
            return link_id_map
    
    def _save_videos_to_db(self, videos: List[Dict], link_id_map: Dict[str, str] = None):
        """
        Save video metadata to database with auto-linked manufacturer/series
        
        Args:
            videos: List of video metadata dicts
            link_id_map: Dict mapping URLs to link IDs (from _save_links_to_db)
        """
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
                    existing = supabase.table('vw_videos') \
                        .select('id') \
                        .eq('youtube_id', video['youtube_id']) \
                        .limit(1) \
                        .execute()
                    should_insert = not existing.data
                else:
                    should_insert = True
                
                if should_insert:
                    # Update link_id from link_id_map if available
                    if link_id_map and video.get('url'):
                        correct_link_id = link_id_map.get(video['url'])
                        if correct_link_id:
                            video['link_id'] = correct_link_id
                    
                    # Verify link_id exists before inserting
                    if video.get('link_id'):
                        link_check = supabase.table('vw_links').select('id').eq('id', video['link_id']).execute()
                        if not link_check.data:
                            self.logger.debug(f"Skipping video {video.get('youtube_id')} - link_id not found")
                            continue
                    
                    # Only insert fields that exist in videos table
                    # Remove thumbnail analysis fields if they don't exist in schema
                    video_data = {k: v for k, v in video.items() 
                                  if k not in ['thumbnail_ocr_text', 'thumbnail_ai_description']}
                    
                    result = supabase.table('vw_videos').insert(video_data).execute()
                    
                    # Auto-link manufacturer/series via link_id (videos → links → document)
                    if result.data and len(result.data) > 0 and video.get('link_id'):
                        video_id = result.data[0]['id']
                        try:
                            # Get document_id from link
                            link_result = supabase.table('vw_links').select('document_id').eq('id', video['link_id']).single().execute()
                            if link_result.data:
                                supabase.rpc('auto_link_resource_to_document', {
                                    'p_resource_table': 'krai_content.videos',
                                    'p_resource_id': video_id,
                                    'p_document_id': link_result.data['document_id']
                                }).execute()
                        except Exception as video_error:
                            self.logger.debug(f"Could not auto-link manufacturer/series: {video_error}")
                        
                        # Link video to products (extract from title/description)
                        try:
                            self._link_video_to_products(supabase, video_id, video)
                        except Exception as link_error:
                            self.logger.debug(f"Could not link video to products: {link_error}")
            
            self.logger.success(f"Saved {len(videos)} videos to database")
        except Exception as e:
            self.logger.error(f"Failed to save videos: {e}")
    
    def _link_video_to_products(self, supabase, video_id: str, video: Dict):
        """
        Link video to products by extracting model numbers from title/description
        
        Args:
            supabase: Supabase client
            video_id: Video UUID
            video: Video metadata dict with title, description
        """
        # Extract text to search for products
        search_text = ""
        if video.get('title'):
            search_text += video['title'] + " "
        if video.get('description'):
            search_text += video['description']
        
        if not search_text:
            return
        
        # Use ProductExtractor to find model numbers
        from .product_extractor import ProductExtractor
        
        # Get manufacturer from video metadata or document
        manufacturer = video.get('manufacturer_name') or self.manufacturer
        if manufacturer == "AUTO":
            manufacturer = None
        
        extractor = ProductExtractor(manufacturer_name=manufacturer or "HP")
        
        # Extract products from video text
        products = extractor.extract_from_text(search_text, page_number=0)
        
        if not products:
            return
        
        # Link each found product to video
        linked_count = 0
        for product in products:
            try:
                # Find product in database by model_number
                product_result = supabase.table('vw_products') \
                    .select('id') \
                    .eq('model_number', product.model_number) \
                    .limit(1) \
                    .execute()
                
                if product_result.data:
                    product_id = product_result.data[0]['id']
                    
                    # Check if link already exists
                    existing = supabase.table('vw_video_products') \
                        .select('id') \
                        .eq('video_id', video_id) \
                        .eq('product_id', product_id) \
                        .limit(1) \
                        .execute()
                    
                    if not existing.data:
                        # Create link
                        supabase.table('vw_video_products').insert({
                            'video_id': video_id,
                            'product_id': product_id
                        }).execute()
                        linked_count += 1
            except Exception as e:
                self.logger.debug(f"Could not link product {product.model_number} to video: {e}")
        
        if linked_count > 0:
            self.logger.info(f"   ✓ Linked video to {linked_count} product(s)")
    
    def _save_products_to_db(self, document_id: UUID, products: List) -> List[str]:
        """
        Save extracted products to database
        
        Returns:
            List of product IDs (UUIDs as strings)
        """
        product_ids = []
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping product storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            saved_count = 0
            updated_count = 0
            
            # Progress bar for saving products
            with self.logger.progress_bar(products, "Saving products") as progress:
                task = progress.add_task(f"Saved: {saved_count}, Updated: {updated_count}", total=len(products))
                
                for product in products:
                    # Convert ExtractedProduct to dict if needed
                    product_data = product if isinstance(product, dict) else {
                        'model_number': getattr(product, 'model_number', ''),
                        'manufacturer_name': getattr(product, 'manufacturer_name', ''),
                        'product_name': getattr(product, 'product_name', None),
                        'series_name': getattr(product, 'series_name', None),
                        'confidence': getattr(product, 'confidence', 0.0)
                    }
                
                # Get manufacturer_id (inherit from document if not specified)
                manufacturer_name = product_data.get('manufacturer_name') or self.manufacturer
                manufacturer_id = None
                
                if manufacturer_name and manufacturer_name != "AUTO":
                    try:
                        manufacturer_id = self._ensure_manufacturer_exists(manufacturer_name, supabase)
                    except Exception as e:
                        self.logger.debug(f"Could not get manufacturer_id: {e}")
                
                # Check if product already exists
                existing = supabase.table('vw_products').select('id').eq(
                    'model_number', product_data['model_number']
                ).limit(1).execute()
                
                if existing.data:
                    # Update existing product
                    product_id = existing.data[0]['id']
                    
                    # Get current product_type to check if we should update
                    current_result = supabase.table('vw_products').select('product_type').eq('id', product_id).single().execute()
                    current_type = current_result.data.get('product_type') if current_result.data else None
                    
                    update_data = {
                        'manufacturer_id': str(manufacturer_id) if manufacturer_id else None
                    }
                    
                    # Detect product_type (always try to improve)
                    from utils.product_type_mapper import get_product_type
                    detected_type = get_product_type(
                        series_name=product_data.get('series_name', ''),
                        model_number=product_data['model_number']
                    )
                    
                    # Log detection result
                    self.logger.debug(f"Product Type Detection for {product_data['model_number']}:")
                    self.logger.debug(f"  Current: {current_type or 'NULL'}")
                    self.logger.debug(f"  Detected: {detected_type or 'None'}")
                    self.logger.debug(f"  Series: {product_data.get('series_name', 'None')}")
                    
                    # Update if we have a better type
                    if detected_type:
                        # Always update if NULL or generic fallback types
                        should_update = (
                            not current_type or 
                            current_type in ['multifunction', 'laser_multifunction', 'printer']
                        )
                        
                        # Or if detected type is more specific (e.g., production_printer vs laser_multifunction)
                        if should_update or (detected_type != current_type and detected_type != 'laser_multifunction'):
                            update_data['product_type'] = detected_type
                            if current_type and current_type != detected_type:
                                self.logger.info(f"✓ Updated product_type: {current_type} → {detected_type} for {product_data['model_number']}")
                            else:
                                self.logger.info(f"✓ Set product_type: {detected_type} for {product_data['model_number']}")
                        else:
                            self.logger.debug(f"  Skipped: Already correct or not better")
                    
                    supabase.table('vw_products').update(update_data).eq('id', product_id).execute()
                    updated_count += 1
                    product_ids.append(product_id)
                else:
                    # Create new product
                    # Determine product_type from series_name + model_number
                    product_type = 'laser_multifunction'  # Default fallback
                    
                    # Try to detect product_type (works even without series_name)
                    from utils.product_type_mapper import get_product_type
                    detected_type = get_product_type(
                        series_name=product_data.get('series_name', ''),
                        model_number=product_data['model_number']
                    )
                    
                    if detected_type:
                        product_type = detected_type
                        self.logger.info(f"✓ New product type: {product_type} for {product_data['model_number']}")
                    else:
                        self.logger.debug(f"Using default product_type: {product_type} for {product_data['model_number']}")
                    
                    insert_data = {
                        'model_number': product_data['model_number'],
                        'manufacturer_id': str(manufacturer_id) if manufacturer_id else None,
                        'product_type': product_type
                    }
                    result = supabase.table('vw_products').insert(insert_data).execute()
                    if result.data:
                        product_ids.append(result.data[0]['id'])
                    saved_count += 1
                    
                    # Update progress
                    progress.update(task, advance=1, description=f"Saved: {saved_count}, Updated: {updated_count}")
            
            self.logger.success(f"💾 Saved {saved_count} new products, updated {updated_count} existing")
            
            # Update products with OEM information
            if product_ids:
                try:
                    from utils.oem_sync import update_product_oem_info
                    oem_updated = 0
                    
                    for product_id in product_ids:
                        # Get product info (with series via JOIN)
                        product_result = supabase.table('vw_products').select(
                            'id,model_number,manufacturer_id,series_id,product_series(series_name)'
                        ).eq('id', product_id).single().execute()
                        
                        if product_result.data:
                            product = product_result.data
                            
                            # Get manufacturer name
                            if product.get('manufacturer_id'):
                                mfr_result = supabase.table('vw_manufacturers').select('name').eq(
                                    'id', product['manufacturer_id']
                                ).single().execute()
                                
                                if mfr_result.data:
                                    manufacturer_name = mfr_result.data['name']
                                    # Get series name from JOIN or use model_number
                                    series_name = None
                                    if product.get('product_series'):
                                        series_name = product['product_series'].get('series_name')
                                    model_or_series = series_name or product.get('model_number')
                                    
                                    # Update OEM info
                                    if update_product_oem_info(supabase, product_id, manufacturer_name, model_or_series):
                                        oem_updated += 1
                    
                    if oem_updated > 0:
                        self.logger.info(f"🔄 Updated {oem_updated} products with OEM information")
                except Exception as e:
                    self.logger.debug(f"Could not update OEM info: {e}")
            
            return product_ids
        except Exception as e:
            error_msg = str(e)
            
            # Check for common constraint violations and provide helpful messages
            if 'product_type_check' in error_msg:
                self.logger.error(f"❌ Failed to save products: Invalid product_type value!")
                self.logger.error(f"")
                self.logger.error(f"📋 ALLOWED VALUES:")
                self.logger.error(f"   Printer: laser_printer, inkjet_printer, production_printer, solid_ink_printer")
                self.logger.error(f"   MFP: laser_multifunction, inkjet_multifunction")
                self.logger.error(f"   Plotter: inkjet_plotter, latex_plotter")
                self.logger.error(f"   Generic: printer, scanner, multifunction, copier, plotter")
                self.logger.error(f"   Other: accessory, option, consumable, finisher, feeder")
                self.logger.error(f"")
                self.logger.error(f"💡 TO FIX:")
                self.logger.error(f"   1. Check backend/utils/product_type_mapper.py")
                self.logger.error(f"   2. Make sure all values match allowed list above")
                self.logger.error(f"   3. OR add new value to database/migrations/48_expand_product_type_values.sql")
                self.logger.error(f"")
                self.logger.error(f"🔍 Error details: {error_msg}")
            elif 'not-null constraint' in error_msg:
                self.logger.error(f"❌ Failed to save products: Required field is NULL!")
                self.logger.error(f"")
                self.logger.error(f"💡 TO FIX:")
                self.logger.error(f"   Check which field is NULL in the error message")
                self.logger.error(f"   Make sure all required fields have values")
                self.logger.error(f"")
                self.logger.error(f"🔍 Error details: {error_msg}")
            else:
                self.logger.error(f"❌ Failed to save products: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
            
            return []
    
    def _detect_and_link_series(self, product_ids: List[str]) -> Dict:
        """
        Detect and link series for products
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            Dict with statistics
        """
        from processors.series_processor import SeriesProcessor
        
        stats = {
            'products_processed': 0,
            'series_detected': 0,
            'series_created': 0,
            'products_linked': 0
        }
        
        series_processor = SeriesProcessor()
        
        for product_id in product_ids:
            try:
                result = series_processor.process_product(product_id)
                stats['products_processed'] += 1
                
                if result:
                    if result.get('series_detected'):
                        stats['series_detected'] += 1
                    if result.get('series_created'):
                        stats['series_created'] += 1
                    if result.get('product_linked'):
                        stats['products_linked'] += 1
            except Exception as e:
                self.logger.debug(f"Series detection failed for product {product_id}: {e}")
        
        return stats
    
    def _link_error_codes_to_chunks(self, document_id: UUID) -> int:
        """
        Link error codes to chunks based on page numbers
        
        Updates error_codes.chunk_id where:
        chunk.page_start <= error_code.page_number <= chunk.page_end
        
        Args:
            document_id: Document UUID
            
        Returns:
            Number of error codes successfully linked
        """
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping chunk linking")
                return 0
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Get all error codes for this document without chunk_id
            error_codes = supabase.table('vw_error_codes') \
                .select('id, page_number') \
                .eq('document_id', str(document_id)) \
                .is_('chunk_id', 'null') \
                .execute()
            
            if not error_codes.data:
                return 0
            
            linked_count = 0
            
            for ec in error_codes.data:
                page_num = ec.get('page_number')
                if not page_num:
                    continue
                
                # Find chunk that contains this page
                chunk = supabase.table('vw_chunks') \
                    .select('id') \
                    .eq('document_id', str(document_id)) \
                    .lte('page_start', page_num) \
                    .gte('page_end', page_num) \
                    .limit(1) \
                    .execute()
                
                if chunk.data:
                    chunk_id = chunk.data[0]['id']
                    
                    # Update error code with chunk_id
                    supabase.table('vw_error_codes') \
                        .update({'chunk_id': chunk_id}) \
                        .eq('id', ec['id']) \
                        .execute()
                    
                    linked_count += 1
            
            return linked_count
            
        except Exception as e:
            self.logger.warning(f"Failed to link error codes to chunks: {e}")
            return 0
    
    def _update_product_types_after_series(self, saved_products: list):
        """
        Update product types after series linking
        
        Now that series_name is known, we can determine more accurate product types.
        For example: AccurioPress → production_printer (not laser_multifunction)
        
        Args:
            saved_products: List of dicts with product_id and model_number
        """
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            from utils.product_type_mapper import get_product_type
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping product type update")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            updated_count = 0
            
            for product_id in saved_products:
                # saved_products is a list of UUIDs, not dicts!
                # Get current product with series info (JOIN with product_series)
                # products.series_id → product_series.id → product_series.series_name
                result = supabase.table('vw_products') \
                    .select('product_type, model_number, series_id, product_series(series_name)') \
                    .eq('id', product_id) \
                    .limit(1) \
                    .execute()
                
                if not result.data:
                    continue
                
                current_type = result.data[0].get('product_type')
                model_number = result.data[0].get('model_number')
                
                # Extract series_name from joined table
                series_data = result.data[0].get('product_series')
                series_name = series_data.get('series_name') if series_data else None
                
                # Detect product type with series_name
                detected_type = get_product_type(
                    series_name=series_name or '',
                    model_number=model_number
                )
                
                # Update if detected type is different and more specific
                if detected_type and detected_type != current_type:
                    # Only update if new type is more specific (not laser_multifunction fallback)
                    if detected_type != 'laser_multifunction' or not current_type:
                        supabase.table('vw_products') \
                            .update({'product_type': detected_type}) \
                            .eq('id', product_id) \
                            .execute()
                        
                        self.logger.info(f"   ✓ Updated product_type: {current_type} → {detected_type} for {model_number}")
                        updated_count += 1
            
            if updated_count > 0:
                self.logger.success(f"   ✅ Updated {updated_count} product types")
            else:
                self.logger.debug("   ℹ️  No product type updates needed")
                
        except Exception as e:
            self.logger.warning(f"Failed to update product types after series: {e}")
    
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
            
            # Get manufacturer from document
            # Note: Use only 'manufacturer' since view might not have manufacturer_id
            # The document might not be in DB yet if we're saving error codes during processing
            try:
                doc_result = supabase.table('vw_documents') \
                    .select('manufacturer') \
                    .eq('id', str(document_id)) \
                    .limit(1) \
                    .execute()
            except Exception as db_error:
                self.logger.debug(f"Could not query document from DB: {db_error}")
                doc_result = None
            
            manufacturer_id = None
            manufacturer_name = None
            
            # Debug: Log what we got from document
            if doc_result and doc_result.data:
                manufacturer_name = doc_result.data[0].get('manufacturer')
                self.logger.debug(f"Document manufacturer field: '{manufacturer_name}'")
            else:
                self.logger.debug(f"Document not yet in DB or no manufacturer field - will use detected manufacturer")
            
            # Get manufacturer name and ensure it exists
            if manufacturer_name:
                # Use unified helper to ensure manufacturer exists
                try:
                    manufacturer_id = self._ensure_manufacturer_exists(manufacturer_name, supabase)
                    
                    # Update document with manufacturer_id using RPC
                    try:
                        supabase.rpc('update_document_manufacturer', {
                            'p_document_id': str(document_id),
                            'p_manufacturer': manufacturer_name,
                            'p_manufacturer_id': str(manufacturer_id)
                        }).execute()
                        self.logger.info(f"✅ Updated document with manufacturer_id: {manufacturer_id}")
                    except Exception as update_error:
                        self.logger.error(f"❌ Could not update manufacturer_id via RPC: {update_error}")
                        # Try to continue anyway - we have the manufacturer_id for this session
                        self.logger.warning(f"   Continuing with manufacturer_id in memory only")
                    
                except ManufacturerNotFoundError as e:
                    self.logger.error(f"Failed to ensure manufacturer exists: {e}")
                    return
            else:
                self.logger.debug(f"Document has no manufacturer field - using detected manufacturer")
                self.logger.info(f"Using detected manufacturer: {self.manufacturer}")
                
                # Try to use the detected manufacturer from document processing
                if self.manufacturer and self.manufacturer != "AUTO":
                    try:
                        self.logger.info(f"🔍 Attempting to ensure manufacturer exists: '{self.manufacturer}'")
                        manufacturer_id = self._ensure_manufacturer_exists(self.manufacturer, supabase)
                        self.logger.info(f"✅ Using detected manufacturer: {self.manufacturer} (ID: {manufacturer_id})")
                        
                        # Update document with manufacturer_id using RPC
                        try:
                            supabase.rpc('update_document_manufacturer', {
                                'p_document_id': str(document_id),
                                'p_manufacturer': self.manufacturer,
                                'p_manufacturer_id': str(manufacturer_id)
                            }).execute()
                            self.logger.info(f"✅ Updated document with detected manufacturer_id: {manufacturer_id}")
                        except Exception as update_error:
                            self.logger.error(f"❌ Could not update manufacturer_id via RPC: {update_error}")
                            self.logger.warning(f"   Continuing with manufacturer_id in memory only")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to use detected manufacturer '{self.manufacturer}': {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
            
            # CRITICAL: Skip if no manufacturer_id found
            if not manufacturer_id:
                self.logger.error(f"❌ No manufacturer_id for document {document_id}")
                self.logger.error(f"   Document manufacturer field: {doc_result.data[0].get('manufacturer') if doc_result.data else 'N/A'}")
                self.logger.error(f"   Detected manufacturer: {self.manufacturer}")
                self.logger.error(f"   CANNOT SAVE ERROR CODES WITHOUT MANUFACTURER!")
                return
            
            saved_count = 0
            skipped_duplicates = 0
            
            for error_code in error_codes:
                # Convert ExtractedErrorCode to dict if needed
                ec_data = error_code if isinstance(error_code, dict) else {
                    'error_code': getattr(error_code, 'error_code', ''),
                    'error_description': getattr(error_code, 'error_description', ''),
                    'solution_text': getattr(error_code, 'solution_text', None),
                    'confidence': getattr(error_code, 'confidence', 0.0),
                    'page_number': getattr(error_code, 'page_number', None),
                    'context_text': getattr(error_code, 'context_text', None),
                    'severity_level': getattr(error_code, 'severity_level', 'medium'),
                    'requires_technician': getattr(error_code, 'requires_technician', False),
                    'requires_parts': getattr(error_code, 'requires_parts', False)
                }
                
                # DEDUPLICATION: Check if this exact error code already exists
                # Must match the unique constraint: error_code + manufacturer_id + document_id
                try:
                    existing = supabase.table('vw_error_codes') \
                        .select('id') \
                        .eq('error_code', ec_data['error_code']) \
                        .eq('manufacturer_id', str(manufacturer_id)) \
                        .eq('document_id', str(document_id)) \
                        .limit(1) \
                        .execute()
                    
                    if existing.data:
                        skipped_duplicates += 1
                        self.logger.debug(f"Skipping duplicate: {ec_data['error_code']} (already in DB)")
                        continue
                except Exception as dup_check_error:
                    self.logger.debug(f"Duplicate check failed: {dup_check_error}")
                    # Continue with insert if check fails
                
                # Build metadata with smart matching info
                metadata = {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'extraction_method': ec_data.get('extraction_method', 'regex_pattern')
                }
                if ec_data.get('context_text'):
                    metadata['context'] = ec_data.get('context_text')
                
                # USE RPC FUNCTION to bypass PostgREST schema cache!
                # Direct INSERT via PostgREST fails due to cache issues
                # Retry on network errors (gateway errors, timeouts)
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
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
                        break  # Success, exit retry loop
                        
                    except Exception as retry_error:
                        error_msg = str(retry_error)
                        # Check if it's a network/gateway error
                        if ('gateway error' in error_msg.lower() or 
                            'network connection' in error_msg.lower() or
                            'timeout' in error_msg.lower()):
                            if attempt < max_retries - 1:
                                self.logger.warning(f"⚠️  Network error, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                continue
                            else:
                                self.logger.error(f"❌ Failed after {max_retries} attempts: {error_msg}")
                                raise
                        else:
                            # Not a network error, don't retry
                            raise
            
            if skipped_duplicates > 0:
                self.logger.info(f"⏭️  Skipped {skipped_duplicates} duplicate error codes")
            self.logger.success(f"💾 Saved {saved_count} error codes to DB")
            
        except Exception as e:
            # Check if it's a duplicate key error (which is expected on re-processing)
            error_str = str(e)
            if 'duplicate key' in error_str.lower() or '23505' in error_str:
                self.logger.info(f"ℹ️  Error codes already exist in database (duplicate key)")
                self.logger.debug(f"   This is expected when re-processing a document")
            else:
                self.logger.error(f"Failed to save error codes: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
    
    def _save_images_to_db(self, document_id: UUID, images: List[Dict]):
        """
        Save extracted images to database (without R2 upload)
        
        Args:
            document_id: Document UUID
            images: List of image dicts with metadata
        """
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            import hashlib
            from datetime import datetime
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping image storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            saved_count = 0
            skipped_count = 0
            
            for img in images:
                try:
                    # Calculate file hash for deduplication
                    file_path = img.get('path')
                    if not file_path or not Path(file_path).exists():
                        continue
                    
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Check if image already exists
                    existing = supabase.table('vw_images') \
                        .select('id') \
                        .eq('file_hash', file_hash) \
                        .limit(1) \
                        .execute()
                    
                    if existing.data:
                        skipped_count += 1
                        continue
                    
                    # Prepare image record
                    image_record = {
                        'document_id': str(document_id),
                        'page_number': img.get('page_num'),
                        'image_index': img.get('image_index', 0),
                        'filename': Path(file_path).name,
                        'file_hash': file_hash,
                        'image_type': img.get('type', 'diagram'),
                        'width_px': img.get('width'),
                        'height_px': img.get('height'),
                        'file_size_bytes': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                        'storage_url': None,  # No R2 upload yet
                        'storage_path': None
                        # extracted_at removed - column doesn't exist (uses created_at instead)
                    }
                    
                    # Add optional fields with debug logging
                    if img.get('ai_description'):
                        image_record['ai_description'] = img['ai_description']
                        self.logger.debug(f"✓ AI description: {img.get('filename')} - {img['ai_description'][:50]}...")
                    if img.get('ai_confidence'):
                        image_record['ai_confidence'] = img['ai_confidence']
                    if img.get('ocr_text'):
                        image_record['ocr_text'] = img['ocr_text']
                        self.logger.debug(f"✓ OCR text: {img.get('filename')} - {len(img['ocr_text'])} chars")
                    if img.get('ocr_confidence'):
                        image_record['ocr_confidence'] = img['ocr_confidence']
                    if img.get('contains_text') is not None:
                        image_record['contains_text'] = img['contains_text']
                    
                    # Debug: Log what's in the img dict
                    if not img.get('ai_description') and not img.get('ocr_text'):
                        self.logger.debug(f"⚠️  No AI/OCR data for {img.get('filename')} - Keys: {list(img.keys())}")
                    
                    # Insert into database
                    result = supabase.table('vw_images').insert(image_record).execute()
                    
                    if result.data:
                        saved_count += 1
                        
                except Exception as img_error:
                    self.logger.debug(f"Failed to save image {img.get('path')}: {img_error}")
                    continue
            
            if saved_count > 0:
                self.logger.success(f"💾 Saved {saved_count} images to database")
            if skipped_count > 0:
                self.logger.info(f"⏭️  Skipped {skipped_count} duplicate images")
                
        except Exception as e:
            self.logger.error(f"Failed to save images to database: {e}")
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
    
    def _save_parts_to_db(self, document_id: UUID, parts: List, manufacturer: str = None):
        """
        Save extracted parts to database immediately
        
        Args:
            document_id: Document UUID
            parts: List of extracted parts
            manufacturer: Detected manufacturer name
        """
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping parts storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Get manufacturer_id from detected manufacturer
            manufacturer_id = None
            if manufacturer and manufacturer != "AUTO":
                try:
                    manufacturer_id = self._ensure_manufacturer_exists(manufacturer, supabase)
                except Exception as e:
                    self.logger.warning(f"Could not get manufacturer_id: {e}")
            
            if not manufacturer_id:
                self.logger.warning(f"⏭️  Skipping parts save - no manufacturer_id")
                return
            
            saved_count = 0
            duplicate_count = 0
            
            for part in parts:
                # Convert ExtractedPart to dict if needed
                part_data = part if isinstance(part, dict) else {
                    'part_number': getattr(part, 'part_number', ''),
                    'part_name': getattr(part, 'part_name', None),
                    'part_description': getattr(part, 'part_description', None),
                    'part_category': getattr(part, 'part_category', None),
                    'unit_price_usd': getattr(part, 'unit_price_usd', None),
                }
                
                # Prepare record
                record = {
                    'manufacturer_id': str(manufacturer_id),
                    'part_number': part_data.get('part_number'),
                    'part_name': part_data.get('part_name'),
                    'part_description': part_data.get('part_description'),
                    'part_category': part_data.get('part_category'),
                    'unit_price_usd': part_data.get('unit_price_usd')
                }
                
                # Check for duplicates
                existing = supabase.table('vw_parts') \
                    .select('id') \
                    .eq('part_number', record['part_number']) \
                    .eq('manufacturer_id', manufacturer_id) \
                    .limit(1) \
                    .execute()
                
                if not existing.data:
                    supabase.table('vw_parts').insert(record).execute()
                    saved_count += 1
                else:
                    duplicate_count += 1
            
            if duplicate_count > 0:
                self.logger.info(f"⏭️  Skipped {duplicate_count} duplicate parts")
            self.logger.success(f"💾 Saved {saved_count} parts to DB")
            
        except Exception as e:
            self.logger.error(f"Failed to save parts: {e}")
    
    def _save_document_to_db(
        self,
        document_id: UUID,
        pdf_path: Path,
        metadata: Any,
        statistics: Dict,
        detected_manufacturer: str
    ):
        """
        Save document metadata to database
        
        Args:
            document_id: Document UUID
            pdf_path: Path to PDF file
            metadata: PDF metadata
            statistics: Processing statistics
            detected_manufacturer: Detected manufacturer name
        """
        try:
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                self.logger.warning("Supabase not configured - skipping document storage")
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            # CRITICAL FIX: Ensure manufacturer_id is set BEFORE saving document
            manufacturer_id = None
            if detected_manufacturer and detected_manufacturer != "AUTO":
                try:
                    manufacturer_id = self._ensure_manufacturer_exists(detected_manufacturer, supabase)
                    self.logger.info(f"✅ Resolved manufacturer_id: {manufacturer_id} for '{detected_manufacturer}'")
                except Exception as mfr_error:
                    self.logger.warning(f"Could not resolve manufacturer_id: {mfr_error}")
            
            # Prepare document data (include BOTH manufacturer string AND manufacturer_id)
            document_data = {
                'id': str(document_id),
                'filename': pdf_path.name,
                'original_filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size if pdf_path.exists() else 0,
                'storage_path': str(pdf_path),
                'document_type': 'service_manual',  # Default
                'language': metadata.language if metadata and hasattr(metadata, 'language') else 'en',
                'page_count': statistics.get('page_count', 0),
                'word_count': statistics.get('word_count', 0),
                'character_count': statistics.get('character_count', 0),
                'processing_status': 'completed',
                'processing_results': statistics,
                'manufacturer': detected_manufacturer if detected_manufacturer != "AUTO" else None,
                'manufacturer_id': str(manufacturer_id) if manufacturer_id else None
            }
            
            # Use RPC function to bypass PostgREST schema cache issues
            try:
                result = supabase.rpc('upsert_document', {
                    'p_document_id': str(document_id),
                    'p_filename': document_data['filename'],
                    'p_original_filename': document_data['original_filename'],
                    'p_file_size': document_data['file_size'],
                    'p_storage_path': document_data['storage_path'],
                    'p_document_type': document_data['document_type'],
                    'p_language': document_data['language'],
                    'p_page_count': document_data['page_count'],
                    'p_word_count': document_data['word_count'],
                    'p_character_count': document_data['character_count'],
                    'p_processing_status': document_data['processing_status'],
                    'p_processing_results': document_data['processing_results'],
                    'p_manufacturer': document_data['manufacturer'],
                    'p_manufacturer_id': document_data['manufacturer_id']
                }).execute()
                self.logger.success(f"✅ Saved document to database via RPC")
            except Exception as rpc_error:
                # Fallback to direct table access (without manufacturer_id)
                self.logger.warning(f"RPC upsert failed, using fallback: {rpc_error}")
                document_data_fallback = {k: v for k, v in document_data.items() if k != 'manufacturer_id'}
                
                existing = supabase.table('vw_documents').select('id').eq(
                    'id', str(document_id)
                ).execute()
                
                if existing.data:
                    supabase.table('vw_documents').update(document_data_fallback).eq(
                        'id', str(document_id)
                    ).execute()
                else:
                    supabase.table('vw_documents').insert(document_data_fallback).execute()
                
                self.logger.success(f"✅ Saved document to database (fallback, without manufacturer_id)")
                
        except Exception as e:
            self.logger.error(f"Failed to save document to database: {e}")
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
