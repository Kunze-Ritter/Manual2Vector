"""
Master Pipeline - Orchestrates all processing stages

The complete end-to-end document processing pipeline.

Stages:
1. Upload & Validation
2. Text Extraction
3. Image Processing
4. Product Extraction
5. Error Code Extraction
6. Version Extraction
7. Chunking
8. Image Storage (R2)
9. Embedding Generation
10. Database Storage

Features:
- Sequential stage processing
- Error handling & recovery
- Progress tracking
- Configurable stage enabling/disabling
- Retry logic
- Performance metrics
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime

from .logger import get_logger
from .upload_processor import UploadProcessor
from .document_processor import DocumentProcessor
from .image_storage_processor import ImageStorageProcessor
from .embedding_processor import EmbeddingProcessor
from .stage_tracker import StageTracker
from .__version__ import __version__, __commit__, __date__


class MasterPipeline:
    """
    Master Pipeline - Orchestrates all document processing stages
    """
    
    def __init__(
        self,
        supabase_client,
        manufacturer: str = "AUTO",
        enable_images: bool = True,
        enable_ocr: bool = True,
        enable_vision: bool = True,
        upload_images_to_r2: bool = False,  # Images to R2
        upload_documents_to_r2: bool = False,  # PDFs to R2
        enable_embeddings: bool = True,
        max_retries: int = 2
    ):
        """
        Initialize master pipeline
        
        Args:
            supabase_client: Supabase client for database
            manufacturer: Default manufacturer name
            enable_images: Enable image extraction
            enable_ocr: Enable OCR on images
            enable_vision: Enable Vision AI
            upload_images_to_r2: Upload extracted images to R2 storage
            upload_documents_to_r2: Upload original PDFs to R2 storage
            enable_embeddings: Enable embedding generation
            max_retries: Maximum retries per stage on failure
        """
        self.logger = get_logger()
        self.supabase = supabase_client
        self.manufacturer = manufacturer
        self.max_retries = max_retries
        
        # Stage flags
        self.enable_images = enable_images
        self.enable_ocr = enable_ocr
        self.enable_vision = enable_vision
        self.upload_images_to_r2 = upload_images_to_r2
        self.upload_documents_to_r2 = upload_documents_to_r2
        self.enable_embeddings = enable_embeddings
        
        # Initialize processors
        self.logger.info("Initializing Master Pipeline...")
        
        self.upload_processor = UploadProcessor(
            supabase_client=supabase_client
        )
        
        self.document_processor = DocumentProcessor(
            manufacturer=manufacturer,
            supabase_client=supabase_client
        )
        
        self.image_storage = ImageStorageProcessor(
            supabase_client=supabase_client
        )
        
        self.embedding_processor = EmbeddingProcessor(
            supabase_client=supabase_client
        )
        
        self.stage_tracker = StageTracker(supabase_client)
        
        self.logger.success(f"Master Pipeline v{__version__} initialized!")
        self.logger.info(f"Build: {__commit__} | Date: {__date__}")
        self._log_configuration()
    
    def _log_configuration(self):
        """Log pipeline configuration"""
        self.logger.info("Pipeline Configuration:")
        self.logger.info(f"  Manufacturer: {self.manufacturer}")
        self.logger.info(f"  Image Processing: {'[ON]' if self.enable_images else '[OFF]'}")
        self.logger.info(f"  OCR: {'[ON]' if self.enable_ocr else '[OFF]'}")
        self.logger.info(f"  Vision AI: {'[ON]' if self.enable_vision else '[OFF]'}")
        self.logger.info(f"  Upload Images to R2: {'[ON]' if self.upload_images_to_r2 else '[OFF]'}")
        self.logger.info(f"  Upload Documents to R2: {'[ON]' if self.upload_documents_to_r2 else '[OFF]'}")
        self.logger.info(f"  Embeddings: {'[ON]' if self.enable_embeddings else '[OFF]'}")
    
    def process_document(
        self,
        file_path: Path,
        document_type: str = "service_manual",
        manufacturer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline
        
        Args:
            file_path: Path to PDF file
            document_type: Type of document
            manufacturer: Manufacturer name (overrides default)
            
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        if not file_path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'document_id': None
            }
        
        manufacturer = manufacturer or self.manufacturer
        
        self.logger.info("="*80)
        self.logger.info(f">>> MASTER PIPELINE START")
        self.logger.info(f"File: {file_path.name}")
        self.logger.info(f"Manufacturer: {manufacturer}")
        self.logger.info("="*80)
        
        document_id = None
        results = {}
        
        try:
            # ==========================================
            # STAGE 1: Upload & Validation
            # ==========================================
            stage_result = self._run_stage(
                stage_name="upload",
                stage_func=lambda: self.upload_processor.process_upload(
                    file_path=file_path,
                    document_type=document_type
                )
            )
            
            if not stage_result['success']:
                return self._create_failed_result("Upload failed", results, start_time)
            
            document_id = UUID(stage_result['document_id'])
            results['upload'] = stage_result
            
            # ==========================================
            # STAGE 2-7: Document Processing
            # ==========================================
            stage_result = self._run_stage(
                stage_name="document_processing",
                stage_func=lambda: self.document_processor.process_document(
                    pdf_path=file_path,
                    document_id=document_id,
                    enable_log_file=True  # Create .log.txt file next to PDF
                )
            )
            
            if not stage_result['success']:
                return self._create_failed_result("Document processing failed", results, start_time, document_id)
            
            results['processing'] = stage_result
            chunks = stage_result.get('chunks', [])
            images = stage_result.get('images', []) if self.enable_images else []
            
            # ==========================================
            # STAGE 8: Image Storage (Optional)
            # ==========================================
            if not self.upload_images_to_r2:
                self.logger.info("⏭️  STAGE 8: Image Storage - SKIPPED (UPLOAD_IMAGES_TO_R2=false)")
                results['image_storage'] = {'success': True, 'skipped': True, 'reason': 'UPLOAD_IMAGES_TO_R2=false'}
            elif not images:
                self.logger.info("⏭️  STAGE 8: Image Storage - SKIPPED (no images extracted)")
                results['image_storage'] = {'success': True, 'skipped': True, 'reason': 'No images'}
            else:
                stage_result = self._run_stage(
                    stage_name="image_storage",
                    stage_func=lambda: self.document_processor.upload_images_to_storage(
                        document_id=document_id,
                        images=images,
                        document_type=document_type
                    ),
                    optional=True
                )
                results['image_storage'] = stage_result
            
            # ==========================================
            # STAGE 9: Embedding Generation
            # ==========================================
            if not self.enable_embeddings:
                self.logger.info("⏭️  STAGE 9: Embedding Generation - SKIPPED (disabled in config)")
                results['embeddings'] = {'success': True, 'skipped': True, 'reason': 'Disabled'}
            elif not chunks:
                self.logger.info("⏭️  STAGE 9: Embedding Generation - SKIPPED (no chunks)")
                results['embeddings'] = {'success': True, 'skipped': True, 'reason': 'No chunks'}
            elif self.enable_embeddings and chunks:
                self.logger.info("=" * 60)
                self.logger.info("🔍 CHECKING EMBEDDING CONFIGURATION...")
                
                # Check configuration before running
                emb_status = self.document_processor.embedding_processor.get_configuration_status()
                
                if emb_status['is_configured']:
                    self.logger.success("✅ Embedding processor configured and ready")
                    self.logger.info(f"   • Ollama: {emb_status['ollama_url']}")
                    self.logger.info(f"   • Model: {emb_status['model_name']} ({emb_status['embedding_dimension']}D)")
                else:
                    self.logger.error("❌ EMBEDDING PROCESSOR NOT CONFIGURED!")
                    self.logger.error("=" * 60)
                    if not emb_status['ollama_available']:
                        self.logger.error("   ❌ Ollama is NOT running or model not installed")
                        self.logger.info(f"      Fix: ollama serve && ollama pull {emb_status['model_name']}")
                    if not emb_status['supabase_configured']:
                        self.logger.error("   ❌ Supabase client NOT configured")
                    self.logger.error("=" * 60)
                    self.logger.warning("⚠️  Embeddings will be SKIPPED!")
                    self.logger.warning("⚠️  Semantic search will NOT work without embeddings!")
                
                stage_result = self._run_stage(
                    stage_name="embeddings",
                    stage_func=lambda: self.document_processor.generate_embeddings(
                        document_id=document_id,
                        chunks=chunks
                    ),
                    optional=True  # Don't fail pipeline if embeddings fail
                )
                results['embeddings'] = stage_result
                
                # Warn if embeddings failed
                if not stage_result.get('success'):
                    self.logger.error("❌ EMBEDDING GENERATION FAILED!")
                    self.logger.error(f"   Error: {stage_result.get('error', 'Unknown error')}")
                    if stage_result.get('skipped'):
                        self.logger.warning("   → Embeddings were skipped due to configuration")
            elif self.enable_embeddings and not chunks:
                self.logger.warning("⚠️  No chunks to embed (empty document?)")
            
            # ==========================================
            # STAGE 9.5: Link Images to Chunks
            # ==========================================
            if images and chunks:
                self.logger.info("🔗 Linking images to chunks...")
                linked_count = self._link_images_to_chunks(document_id)
                if linked_count > 0:
                    self.logger.success(f"✅ Linked {linked_count} images to chunks")
            
            # ==========================================
            # STAGE 9.6: Link Error Codes to Chunks & Images
            # ==========================================
            processing_result = results.get('processing', {})  # Get processing result
            error_codes = processing_result.get('error_codes', [])
            if error_codes and chunks:
                self.logger.info("🔗 Linking error codes to chunks & images...")
                linked_count = self._link_error_codes_to_chunks_and_images(document_id)
                if linked_count > 0:
                    self.logger.success(f"✅ Linked {linked_count} error codes")
            
            # ==========================================
            # STAGE 10: Save extracted entities to DB
            # ==========================================
            
            # Error codes are saved immediately after extraction (see document_processor.py Step 3)
            # No need to save again here
            
            # Save products to products table AND document_products relationship
            products = processing_result.get('products', [])
            if products:
                self._save_products(document_id, products)
                self._save_document_products(document_id, products)
            
            # Save parts (spare parts from parts catalogs)
            parts = processing_result.get('parts', [])
            if parts:
                self._save_parts(document_id, parts)
            
            # ==========================================
            # Update document metadata (manufacturer, models, etc.)
            # ==========================================
            self._update_document_metadata(document_id, processing_result, manufacturer)
            
            # ==========================================
            # Update document status with processing_results
            # ==========================================
            self._update_document_status(
                document_id=document_id,
                status='completed',
                results=processing_result  # Save clean processing result
            )
            
            # ==========================================
            # Summary
            # ==========================================
            processing_time = time.time() - start_time
            
            self.logger.info("="*80)
            self.logger.success(">>> PIPELINE COMPLETE!")
            self.logger.info(f"Total Time: {processing_time:.1f}s")
            self.logger.info(f"Results:")
            self.logger.info(f"   Documents: 1")
            self.logger.info(f"   Pages: {results['processing'].get('metadata', {}).get('page_count', 0)}")
            self.logger.info(f"   Chunks: {len(chunks)}")
            self.logger.info(f"   Products: {len(results['processing'].get('products', []))}")
            self.logger.info(f"   Parts: {len(results['processing'].get('parts', []))}")
            self.logger.info(f"   Error Codes: {len(results['processing'].get('error_codes', []))}")
            self.logger.info(f"   Versions: {len(results['processing'].get('versions', []))}")
            self.logger.info(f"   Images: {len(images)}")
            
            if self.enable_embeddings and 'embeddings' in results:
                emb_result = results['embeddings']
                if emb_result.get('success'):
                    self.logger.info(f"   Embeddings: {emb_result.get('embeddings_created', 0)}")
            
            self.logger.info("="*80)
            
            return {
                'success': True,
                'document_id': str(document_id),
                'processing_time': processing_time,
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}", exc=e)
            
            if document_id:
                self._update_document_status(
                    document_id=document_id,
                    status='failed',
                    error=str(e)
                )
            
            return self._create_failed_result(str(e), results, start_time, document_id)
    
    def _run_stage(
        self,
        stage_name: str,
        stage_func,
        optional: bool = False,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Run a pipeline stage with error handling and retry
        
        Args:
            stage_name: Name of the stage
            stage_func: Function to execute
            optional: If True, failures won't stop pipeline
            retry_count: Current retry count
            
        Returns:
            Stage result dict
        """
        self.logger.info(f"\n>>> Stage: {stage_name.upper()}")
        
        try:
            result = stage_func()
            
            # Handle skipped optional stages
            if result.get('skipped'):
                self.logger.info(f">> {stage_name} skipped (optional)")
                return result
            
            # Check success
            if result.get('success'):
                self.logger.success(f"[OK] {stage_name} complete")
                return result
            else:
                error = result.get('error', 'Unknown error')
                self.logger.warning(f"[!] {stage_name} failed: {error}")
                
                # Retry logic
                if retry_count < self.max_retries:
                    self.logger.info(f"[RETRY] {stage_name} ({retry_count + 1}/{self.max_retries})...")
                    time.sleep(1)  # Brief delay before retry
                    return self._run_stage(stage_name, stage_func, optional, retry_count + 1)
                
                # If optional, continue pipeline
                if optional:
                    self.logger.warning(f"[SKIP] Skipping optional stage: {stage_name}")
                    return result
                
                # Otherwise, stage has failed
                return result
                
        except Exception as e:
            self.logger.error(f"[ERROR] {stage_name} exception: {e}")
            
            # Retry on exception
            if retry_count < self.max_retries:
                self.logger.info(f"[RETRY] {stage_name} ({retry_count + 1}/{self.max_retries})...")
                time.sleep(1)
                return self._run_stage(stage_name, stage_func, optional, retry_count + 1)
            
            return {
                'success': False,
                'error': str(e),
                'stage': stage_name
            }
    
    def _save_error_codes(self, document_id: UUID, error_codes: list):
        """Save error codes to krai_intelligence.error_codes table"""
        try:
            # Get manufacturer from document and find manufacturer_id
            doc_result = self.supabase.table('documents') \
                .select('manufacturer') \
                .eq('id', str(document_id)) \
                .limit(1) \
                .execute()
            
            manufacturer_id = None
            if doc_result.data and doc_result.data[0].get('manufacturer'):
                manufacturer_name = doc_result.data[0]['manufacturer']
                
                # Find manufacturer_id by name
                mfr_result = self.supabase.table('manufacturers') \
                    .select('id') \
                    .ilike('name', f"%{manufacturer_name}%") \
                    .limit(1) \
                    .execute()
                
                if mfr_result.data:
                    manufacturer_id = mfr_result.data[0]['id']
            
            saved_count = 0
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
                
                # Build metadata with smart matching info
                metadata = {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'extraction_method': ec_data.get('extraction_method', 'regex_pattern')
                }
                if ec_data.get('context_text'):
                    metadata['context'] = ec_data.get('context_text')
                
                # USE RPC FUNCTION to bypass PostgREST schema cache!
                # Direct INSERT via PostgREST fails due to cache issues
                result = self.supabase.rpc('insert_error_code', {
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
            
            self.logger.success(f"Saved {saved_count} error codes to DB")
            
        except Exception as e:
            self.logger.error(f"Failed to save error codes: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def _save_products(self, document_id: UUID, products: list):
        """Save products to krai_core.products table"""
        try:
            for product in products:
                # Convert ExtractedProduct to dict if needed
                prod_data = product if isinstance(product, dict) else {
                    'model_number': getattr(product, 'model_number', ''),
                    'series': getattr(product, 'product_series', None),
                    'manufacturer_name': getattr(product, 'manufacturer_name', None),
                    'product_type': getattr(product, 'product_type', 'printer'),
                    'confidence': getattr(product, 'confidence', 0.0)
                }
                
                # Find or create manufacturer
                manufacturer_id = None
                manufacturer_name = prod_data.get('manufacturer_name')
                if manufacturer_name:
                    try:
                        # Try to find existing manufacturer
                        mfr_result = self.supabase.table('manufacturers') \
                            .select('id') \
                            .ilike('name', f"%{manufacturer_name}%") \
                            .limit(1) \
                            .execute()
                        
                        if mfr_result.data:
                            # Manufacturer exists
                            manufacturer_id = mfr_result.data[0]['id']
                            self.logger.info(f"✅ Found manufacturer: {manufacturer_name}")
                        else:
                            # Create new manufacturer (only name is required)
                            new_mfr = self.supabase.table('manufacturers').insert({
                                'name': manufacturer_name
                            }).execute()
                            
                            if new_mfr.data:
                                manufacturer_id = new_mfr.data[0]['id']
                                self.logger.info(f"✅ Created new manufacturer: {manufacturer_name}")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to find/create manufacturer '{manufacturer_name}': {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                
                # Skip product if no manufacturer_id (required field)
                if not manufacturer_id:
                    self.logger.warning(f"❌ Skipping product {prod_data.get('model_number')} - no manufacturer_id")
                    continue
                
                # Find or create product series
                series_id = None
                series_name = prod_data.get('series')
                
                self.logger.debug(f"Product '{prod_data.get('model_number')}' - Series: {series_name or 'None'}")
                
                if series_name and manufacturer_id:
                    try:
                        # Try to find existing series
                        series_result = self.supabase.table('product_series') \
                            .select('id') \
                            .eq('manufacturer_id', manufacturer_id) \
                            .ilike('series_name', series_name) \
                            .limit(1) \
                            .execute()
                        
                        if series_result.data:
                            series_id = series_result.data[0]['id']
                            self.logger.debug(f"Found series: {series_name}")
                        else:
                            # Create new series
                            new_series = self.supabase.table('product_series').insert({
                                'manufacturer_id': manufacturer_id,
                                'series_name': series_name
                            }).execute()
                            
                            if new_series.data:
                                series_id = new_series.data[0]['id']
                                self.logger.info(f"✅ Created new series: {series_name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to find/create series '{series_name}': {e}")
                
                record = {
                    'model_number': prod_data.get('model_number'),
                    'manufacturer_id': manufacturer_id,
                    'series_id': series_id,  # Added series_id FK!
                    'product_type': prod_data.get('product_type', 'printer'),
                    'metadata': {
                        'manufacturer_name': manufacturer_name,
                        'confidence': prod_data.get('confidence', 0.8),
                        'series': series_name,  # Keep in metadata too for reference
                        'extracted_from_document': str(document_id),
                        'extracted_at': datetime.utcnow().isoformat()
                    }
                }
                
                # Check if product already exists (use krai_core schema)
                existing = self.supabase.table('products') \
                    .select('id') \
                    .eq('model_number', record['model_number']) \
                    .limit(1) \
                    .execute()
                
                if not existing.data:
                    # Insert via public schema (PostgREST default)
                    result = self.supabase.table('products').insert(record).execute()
                    # Store product_id for document_products relationship
                    if result.data:
                        prod_data['_db_id'] = result.data[0]['id']
                else:
                    # Use existing product ID
                    prod_data['_db_id'] = existing.data[0]['id']
            
            self.logger.success(f"Saved {len(products)} products to DB")
            
        except Exception as e:
            self.logger.error(f"Failed to save products: {e}")
    
    def _save_document_products(self, document_id: UUID, products: list):
        """Save document-product relationships to krai_core.document_products"""
        try:
            saved_count = 0
            for idx, product in enumerate(products):
                # Get product_id from previous save
                prod_data = product if isinstance(product, dict) else {
                    'model_number': getattr(product, 'model_number', ''),
                    'confidence': getattr(product, 'confidence', 0.0),
                    'extraction_method': getattr(product, 'extraction_method', 'pattern'),
                    'page_numbers': getattr(product, 'page_numbers', [])
                }
                
                # Get DB product_id (was set in _save_products)
                product_id = prod_data.get('_db_id')
                if not product_id:
                    self.logger.warning(f"No product_id for {prod_data.get('model_number')}, skipping relationship")
                    continue
                
                # Create document_product relationship
                relationship = {
                    'document_id': str(document_id),
                    'product_id': str(product_id),
                    'is_primary_product': (idx == 0),  # First product is primary
                    'confidence_score': min(prod_data.get('confidence', 0.8), 1.0),
                    'extraction_method': prod_data.get('extraction_method', 'pattern'),
                    'page_numbers': prod_data.get('page_numbers', [])
                }
                
                # Check if relationship already exists
                existing = self.supabase.table('document_products') \
                    .select('id') \
                    .eq('document_id', relationship['document_id']) \
                    .eq('product_id', relationship['product_id']) \
                    .limit(1) \
                    .execute()
                
                if not existing.data:
                    self.supabase.table('document_products').insert(relationship).execute()
                    saved_count += 1
            
            self.logger.success(f"Saved {saved_count} document-product relationships")
            
        except Exception as e:
            self.logger.error(f"Failed to save document_products: {e}")
    
    def _save_parts(self, document_id: UUID, parts: list):
        """Save spare parts to krai_parts.parts_catalog table"""
        try:
            saved_count = 0
            for part in parts:
                # Convert ExtractedPart to dict if needed
                part_data = part if isinstance(part, dict) else {
                    'part_number': getattr(part, 'part_number', ''),
                    'part_name': getattr(part, 'part_name', None),
                    'part_description': getattr(part, 'part_description', None),
                    'part_category': getattr(part, 'part_category', None),
                    'manufacturer_name': getattr(part, 'manufacturer_name', None),
                    'unit_price_usd': getattr(part, 'unit_price_usd', None),
                    'confidence': getattr(part, 'confidence', 0.0),
                    'pattern_name': getattr(part, 'pattern_name', None),
                    'page_number': getattr(part, 'page_number', None)
                }
                
                # Find or create manufacturer
                manufacturer_id = None
                manufacturer_name = part_data.get('manufacturer_name')
                
                if manufacturer_name:
                    try:
                        # Try to find existing manufacturer
                        mfr_result = self.supabase.table('manufacturers') \
                            .select('id') \
                            .ilike('name', f"%{manufacturer_name}%") \
                            .limit(1) \
                            .execute()
                        
                        if mfr_result.data:
                            manufacturer_id = mfr_result.data[0]['id']
                        else:
                            # Create new manufacturer
                            new_mfr = self.supabase.table('manufacturers').insert({
                                'name': manufacturer_name
                            }).execute()
                            
                            if new_mfr.data:
                                manufacturer_id = new_mfr.data[0]['id']
                                self.logger.info(f"✅ Created manufacturer: {manufacturer_name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to find/create manufacturer '{manufacturer_name}': {e}")
                
                # Skip if no manufacturer_id (required field)
                if not manufacturer_id:
                    self.logger.warning(f"❌ Skipping part {part_data.get('part_number')} - no manufacturer_id")
                    continue
                
                # Prepare record for database
                record = {
                    'manufacturer_id': manufacturer_id,
                    'part_number': part_data.get('part_number'),
                    'part_name': part_data.get('part_name'),
                    'part_description': part_data.get('part_description'),
                    'part_category': part_data.get('part_category'),
                    'unit_price_usd': part_data.get('unit_price_usd')
                }
                
                # Check if part already exists
                existing = self.supabase.table('parts_catalog') \
                    .select('id') \
                    .eq('part_number', record['part_number']) \
                    .eq('manufacturer_id', manufacturer_id) \
                    .limit(1) \
                    .execute()
                
                if not existing.data:
                    # Insert new part via public schema
                    self.supabase.table('parts_catalog').insert(record).execute()
                    saved_count += 1
            
            self.logger.success(f"Saved {saved_count} parts to database")
            
        except Exception as e:
            self.logger.error(f"Failed to save parts: {e}")
    
    def _link_images_to_chunks(self, document_id: UUID) -> int:
        """
        Link images to chunks based on page numbers
        
        Runs AFTER embedding so chunks are in database
        Links images where: chunk.page_start <= image.page_number <= chunk.page_end
        
        Args:
            document_id: Document UUID
            
        Returns:
            Number of images successfully linked
        """
        try:
            # SQL to update images with matching chunk_id
            # Note: We use raw SQL here because Supabase PostgREST doesn't support
            # complex UPDATE with subqueries easily
            result = self.supabase.rpc('link_images_to_chunks_for_document', {
                'p_document_id': str(document_id)
            }).execute()
            
            if result.data:
                return result.data
            return 0
            
        except Exception as e:
            # Fallback: Try direct SQL if RPC doesn't exist
            try:
                from supabase import create_client
                # Execute raw SQL update
                query = f"""
                    UPDATE krai_content.images i
                    SET chunk_id = (
                        SELECT c.id 
                        FROM krai_intelligence.chunks c
                        WHERE c.document_id = i.document_id
                          AND c.page_start <= i.page_number 
                          AND c.page_end >= i.page_number
                        LIMIT 1
                    )
                    WHERE i.chunk_id IS NULL 
                      AND i.document_id = '{document_id}'
                      AND i.page_number IS NOT NULL
                    RETURNING id
                """
                
                # Use PostgREST query (fallback approach)
                result = self.supabase.rpc('exec_sql', {'sql_text': query}).execute()
                return len(result.data) if result.data else 0
                
            except Exception as e2:
                self.logger.warning(f"Image-to-chunk linking failed: {e2}")
                self.logger.info("   Images can still be found by page_number")
                return 0
    
    def _link_error_codes_to_chunks_and_images(self, document_id: UUID) -> int:
        """
        Link error codes to chunks and images with SMART MATCHING
        
        For each error code on page X:
        - SMART: Try to find image where ai_description contains error code
        - FALLBACK: Use first image on page X
        - Link to chunk where chunk.page_start <= X <= chunk.page_end
        
        Args:
            document_id: Document UUID
            
        Returns:
            Number of error codes successfully linked
        """
        try:
            # ==========================================
            # PHASE 1: SMART IMAGE MATCHING via Vision AI
            # ==========================================
            
            # Get all error codes for this document (without image_id)
            error_codes = self.supabase.table('error_codes') \
                .select('id, error_code, page_number') \
                .eq('document_id', str(document_id)) \
                .is_('image_id', 'null') \
                .execute()
            
            smart_matches = 0
            fallback_matches = 0
            
            if error_codes.data:
                for ec in error_codes.data:
                    error_code_text = ec['error_code']
                    page_num = ec['page_number']
                    
                    if not page_num:
                        continue
                    
                    # Get images on same page with Vision AI descriptions
                    images = self.supabase.table('images') \
                        .select('id, ai_description, image_index') \
                        .eq('document_id', str(document_id)) \
                        .eq('page_number', page_num) \
                        .order('image_index') \
                        .execute()
                    
                    if not images.data:
                        continue
                    
                    matched_image_id = None
                    match_confidence = 0.5  # Default for fallback
                    
                    # SMART MATCH: Look for error code in Vision AI description
                    for img in images.data:
                        if img.get('ai_description'):
                            description = img['ai_description'].lower()
                            error_variations = [
                                error_code_text.lower(),
                                error_code_text.replace('-', '').lower(),
                                error_code_text.replace('.', '').lower()
                            ]
                            
                            # Check if any variation appears in description
                            if any(var in description for var in error_variations):
                                matched_image_id = img['id']
                                match_confidence = 0.95
                                smart_matches += 1
                                self.logger.debug(f"   ✨ Smart match: {error_code_text} → Image {img['image_index']}")
                                break
                    
                    # FALLBACK: First image on page
                    if not matched_image_id and images.data:
                        matched_image_id = images.data[0]['id']
                        match_confidence = 0.5
                        fallback_matches += 1
                    
                    # Update error code with matched image
                    if matched_image_id:
                        self.supabase.table('error_codes') \
                            .update({
                                'image_id': matched_image_id,
                                'metadata': {
                                    'image_match_method': 'smart_vision_ai' if match_confidence > 0.9 else 'fallback_first_on_page',
                                    'image_match_confidence': match_confidence
                                }
                            }) \
                            .eq('id', ec['id']) \
                            .execute()
            
            if smart_matches > 0:
                self.logger.info(f"   ✨ Smart matches: {smart_matches} | Fallback: {fallback_matches}")
            
            # ==========================================
            # PHASE 2: CHUNK & FALLBACK IMAGE LINKING via SQL Function
            # ==========================================
            # This also links images for error codes that Phase 1 didn't match
            # (e.g., when Vision AI description doesn't mention error code)
            
            result = self.supabase.rpc('link_error_codes_to_chunks_and_images', {
                'p_document_id': str(document_id)
            }).execute()
            
            chunk_links = 0
            remaining_image_links = 0
            
            if result.data and len(result.data) > 0:
                chunk_links = result.data[0].get('linked_to_chunks', 0)
                remaining_image_links = result.data[0].get('linked_to_images', 0)
                
                self.logger.debug(f"   Chunks: {chunk_links} | Remaining images: {remaining_image_links}")
            
            total_links = smart_matches + fallback_matches + chunk_links + remaining_image_links
            
            return total_links
            
        except Exception as e:
            self.logger.warning(f"Error code linking failed: {e}")
            self.logger.info("   Error codes can still be found by page_number")
            return 0
    
    def _update_document_metadata(self, document_id: UUID, processing_result: Dict, initial_manufacturer: Optional[str] = None):
        """Update document with extracted manufacturer, models, series, version"""
        try:
            products = processing_result.get('products', [])
            versions = processing_result.get('versions', [])
            
            # Extract manufacturer, models, series from products
            manufacturer = None
            models = []
            series_set = set()
            
            if products:
                for product in products:
                    prod_data = product if isinstance(product, dict) else {
                        'manufacturer': getattr(product, 'manufacturer', None),
                        'model_number': getattr(product, 'model_number', ''),
                        'series': getattr(product, 'product_series', None)  # Fixed: use product_series
                    }
                    
                    if prod_data.get('manufacturer') and not manufacturer:
                        manufacturer = prod_data['manufacturer']
                    
                    if prod_data.get('model_number'):
                        models.append(prod_data['model_number'])
                    
                    if prod_data.get('series'):
                        series_set.add(prod_data['series'])
            
            # Use initial_manufacturer as fallback if no manufacturer found in products
            if not manufacturer and initial_manufacturer and initial_manufacturer != "AUTO":
                manufacturer = initial_manufacturer
                self.logger.info(f"Using initial manufacturer (no products extracted): {manufacturer}")
            
            # Extract BEST version (highest confidence, first match)
            document_version = None
            if versions:
                # Sort by confidence (highest first)
                sorted_versions = sorted(
                    versions,
                    key=lambda v: v.get('confidence', 0) if isinstance(v, dict) else getattr(v, 'confidence', 0),
                    reverse=True
                )
                # Take first (highest confidence)
                best_version = sorted_versions[0]
                document_version = best_version.get('version_string') if isinstance(best_version, dict) else getattr(best_version, 'version_string', None)
            
            # Update document
            update_data = {}
            if manufacturer:
                update_data['manufacturer'] = manufacturer
            if models:
                update_data['models'] = models
            if series_set:
                update_data['series'] = ','.join(sorted(series_set))  # Join multiple series
            if document_version:
                update_data['version'] = document_version
            
            if update_data:
                self.supabase.table('documents').update(update_data).eq(
                    'id', str(document_id)
                ).execute()
                
                version_msg = f", version: {document_version}" if document_version else ""
                self.logger.success(f"Updated document metadata: {manufacturer}, {len(models)} models{version_msg}")
        
        except Exception as e:
            self.logger.error(f"Failed to update document metadata: {e}")
    
    def _update_document_status(
        self,
        document_id: UUID,
        status: str,
        results: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update document processing status in database"""
        try:
            update_data = {
                'processing_status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if error:
                update_data['processing_error'] = error
            
            if results:
                # Clean the results for JSONB storage
                clean_results = {
                    'metadata': results.get('metadata', {}),
                    'statistics': results.get('statistics', {}),
                    'products': [self._serialize_entity(p) for p in results.get('products', [])],
                    'error_codes': [self._serialize_entity(ec) for ec in results.get('error_codes', [])],
                    'versions': [self._serialize_entity(v) for v in results.get('versions', [])],
                    'validation_errors': results.get('validation_errors', []),
                    'processing_time_seconds': results.get('processing_time_seconds', 0)
                }
                # Add processing_results (requires Migration 12!)
                update_data['processing_results'] = clean_results
            
            self.supabase.table('documents').update(update_data).eq(
                'id', str(document_id)
            ).execute()
            
            self.logger.success(f"Updated document status: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update document status: {e}")
    
    def _serialize_entity(self, entity):
        """Serialize Pydantic model or dict to dict"""
        if hasattr(entity, 'model_dump'):
            return entity.model_dump()
        elif hasattr(entity, 'dict'):
            return entity.dict()
        else:
            return entity
    
    def _create_failed_result(
        self,
        error: str,
        results: Dict,
        start_time: float,
        document_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Create failed result dict"""
        processing_time = time.time() - start_time
        
        self.logger.error("="*80)
        self.logger.error(f"[FAILED] PIPELINE FAILED")
        self.logger.error(f"Time: {processing_time:.1f}s")
        self.logger.error(f"Error: {error}")
        self.logger.error("="*80)
        
        return {
            'success': False,
            'error': error,
            'document_id': str(document_id) if document_id else None,
            'processing_time': processing_time,
            'results': results
        }
    
    def process_batch(
        self,
        file_paths: List[Path],
        document_type: str = "service_manual",
        manufacturer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process multiple documents (sequential for now)
        
        Args:
            file_paths: List of PDF paths
            document_type: Type of documents
            manufacturer: Manufacturer name
            
        Returns:
            Dict with batch results
        """
        self.logger.info("="*80)
        self.logger.info(f"BATCH PROCESSING: {len(file_paths)} documents")
        self.logger.info("="*80)
        
        start_time = time.time()
        
        results = []
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(file_paths, 1):
            self.logger.info(f"\nProcessing {i}/{len(file_paths)}: {file_path.name}")
            
            result = self.process_document(
                file_path=file_path,
                document_type=document_type,
                manufacturer=manufacturer
            )
            
            results.append(result)
            
            if result['success']:
                successful += 1
            else:
                failed += 1
        
        total_time = time.time() - start_time
        
        self.logger.info("\n" + "="*80)
        self.logger.info("BATCH COMPLETE")
        self.logger.info(f"Successful: {successful}/{len(file_paths)}")
        self.logger.info(f"Failed: {failed}/{len(file_paths)}")
        self.logger.info(f"Total Time: {total_time:.1f}s")
        self.logger.info(f"Avg Time: {total_time/len(file_paths):.1f}s per document")
        self.logger.info("="*80)
        
        return {
            'success': failed == 0,
            'total': len(file_paths),
            'successful': successful,
            'failed': failed,
            'processing_time': total_time,
            'results': results
        }


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    
    # Load environment
    load_dotenv()
    
    # Initialize Supabase (mock for example)
    print("🚀 Master Pipeline Example")
    print("\nTo use:")
    print("  from master_pipeline import MasterPipeline")
    print("  pipeline = MasterPipeline(supabase_client)")
    print("  result = pipeline.process_document(Path('manual.pdf'))")
