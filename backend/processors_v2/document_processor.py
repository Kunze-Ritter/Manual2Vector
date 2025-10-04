"""
Main Document Processor - Orchestrates everything

Coordinates text extraction, chunking, product/error extraction.
"""

from pathlib import Path
from typing import Optional, Dict, List
from uuid import UUID, uuid4
import time
from .logger import get_logger, log_processing_summary
from .models import ProcessingResult, DocumentMetadata
from .text_extractor import TextExtractor
from .product_extractor import ProductExtractor
from .error_code_extractor import ErrorCodeExtractor
from .version_extractor import VersionExtractor
from .image_storage_processor import ImageStorageProcessor
from .chunker import SmartChunker


class DocumentProcessor:
    """Main document processor - orchestrates all extraction"""
    
    def __init__(
        self,
        manufacturer: str = "AUTO",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        pdf_engine: str = "pymupdf",
        debug: bool = False
    ):
        """
        Initialize document processor
        
        Args:
            manufacturer: Manufacturer name (HP, Canon, AUTO, etc.)
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            pdf_engine: PDF extraction engine
            debug: Enable debug logging for product extraction
        """
        self.manufacturer = manufacturer
        self.debug = debug
        self.logger = get_logger()
        
        # Initialize extractors
        self.text_extractor = TextExtractor(prefer_engine=pdf_engine)
        self.product_extractor = ProductExtractor(manufacturer_name=manufacturer, debug=debug)
        self.error_code_extractor = ErrorCodeExtractor()
        self.version_extractor = VersionExtractor()
        self.image_storage = ImageStorageProcessor()  # R2 for images only
        self.chunker = SmartChunker(
            chunk_size=chunk_size,
            overlap_size=chunk_overlap
        )
        
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
        document_id: Optional[UUID] = None
    ) -> ProcessingResult:
        """
        Process complete document
        
        Args:
            pdf_path: Path to PDF file
            document_id: Optional document UUID (generates if None)
            
        Returns:
            ProcessingResult with all extracted data
        """
        if document_id is None:
            document_id = uuid4()
        
        start_time = time.time()
        
        self.logger.section(f"Processing Document: {pdf_path.name}")
        self.logger.info(f"Document ID: {document_id}")
        
        validation_errors = []
        
        try:
            # Step 1: Extract text
            self.logger.info("Step 1/5: Extracting text from PDF...")
            page_texts, metadata = self.text_extractor.extract_text(pdf_path, document_id)
            
            if not page_texts:
                self.logger.error("No text extracted from PDF!")
                return self._create_failed_result(
                    document_id,
                    "Text extraction failed",
                    time.time() - start_time
                )
            
            self.logger.success(f"Extracted {len(page_texts)} pages")
            
            # Step 2: Extract products (from first page primarily)
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
            
            # Step 3: Extract error codes
            self.logger.info("Step 3/5: Extracting error codes...")
            error_codes = []
            
            with self.logger.progress_bar(page_texts.items(), "Scanning for error codes") as progress:
                task = progress.add_task("Scanning pages", total=len(page_texts))
                
                for page_num, text in page_texts.items():
                    page_codes = self.error_code_extractor.extract_from_text(
                        text, page_number=page_num
                    )
                    error_codes.extend(page_codes)
                    progress.update(task, advance=1)
            
            # Validate error codes
            for error_code in error_codes:
                errors = self.error_code_extractor.validate_extraction(error_code)
                if errors:
                    validation_errors.extend([str(e) for e in errors])
            
            self.logger.success(f"Extracted {len(error_codes)} error codes")
            
            # Step 3b: Extract versions
            self.logger.info("Step 3b/6: Extracting document versions...")
            versions = []
            
            # Extract from first few pages (versions usually on title page)
            for page_num in sorted(page_texts.keys())[:5]:
                page_versions = self.version_extractor.extract_from_text(
                    page_texts[page_num],
                    manufacturer=self.manufacturer,
                    page_number=page_num
                )
                versions.extend(page_versions)
            
            # Get best version (highest confidence)
            if versions:
                best_version = max(versions, key=lambda v: v.confidence)
                self.logger.success(f"Extracted version: {best_version.version_string} (confidence: {best_version.confidence:.2f})")
            else:
                self.logger.info("No version found")
            
            # Step 4: Create chunks
            self.logger.info("Step 4/6: Chunking text...")
            chunks = self.chunker.chunk_document(page_texts, document_id)
            
            # Deduplicate
            chunks = self.chunker.deduplicate_chunks(chunks)
            
            self.logger.success(f"Created {len(chunks)} chunks")
            
            # Step 5: Statistics
            self.logger.info("Step 5/6: Calculating statistics...")
            statistics = self._calculate_statistics(
                page_texts, products, error_codes, versions, chunks
            )
            
            # Create result
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                document_id=document_id,
                success=True,
                metadata=metadata,
                chunks=chunks,
                products=products,
                error_codes=error_codes,
                versions=versions,
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
            
            return result
        
        except Exception as e:
            self.logger.error(f"Processing failed: {e}", exc=e)
            processing_time = time.time() - start_time
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
    
    def _calculate_statistics(
        self,
        page_texts: dict,
        products: list,
        error_codes: list,
        versions: list,
        chunks: list
    ) -> dict:
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
        
        return {
            'total_pages': len(page_texts),
            'total_characters': total_chars,
            'total_words': total_words,
            'total_chunks': len(chunks),
            'total_products': len(products),
            'total_error_codes': len(error_codes),
            'total_versions': len(versions),
            'avg_product_confidence': round(avg_product_conf, 2),
            'avg_error_code_confidence': round(avg_error_conf, 2),
            'avg_version_confidence': round(avg_version_conf, 2),
            'chunk_types': chunk_types,
            'avg_chunk_size': round(total_chars / len(chunks), 0) if chunks else 0
        }
    
    def _create_failed_result(
        self,
        document_id: UUID,
        error_message: str,
        processing_time: float
    ) -> ProcessingResult:
        """Create failed processing result"""
        from .models import DocumentMetadata
        
        # Create minimal metadata
        metadata = DocumentMetadata(
            document_id=document_id,
            page_count=0,
            file_size_bytes=0,
            document_type="service_manual"
        )
        
        return ProcessingResult(
            document_id=document_id,
            success=False,
            metadata=metadata,
            validation_errors=[error_message],
            processing_time_seconds=processing_time,
            statistics={'error': error_message}
        )


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
