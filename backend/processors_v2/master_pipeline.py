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
        enable_r2_storage: bool = False,  # Images to R2
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
            enable_r2_storage: Enable R2 storage for images
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
        self.enable_r2_storage = enable_r2_storage
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
        
        self.logger.success("Master Pipeline initialized!")
        self._log_configuration()
    
    def _log_configuration(self):
        """Log pipeline configuration"""
        self.logger.info("Pipeline Configuration:")
        self.logger.info(f"  Manufacturer: {self.manufacturer}")
        self.logger.info(f"  Image Processing: {'[ON]' if self.enable_images else '[OFF]'}")
        self.logger.info(f"  OCR: {'[ON]' if self.enable_ocr else '[OFF]'}")
        self.logger.info(f"  Vision AI: {'[ON]' if self.enable_vision else '[OFF]'}")
        self.logger.info(f"  R2 Storage: {'[ON]' if self.enable_r2_storage else '[OFF]'}")
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
                    document_id=document_id
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
            if self.enable_r2_storage and images:
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
            # STAGE 9: Embedding Generation (Optional)
            # ==========================================
            if self.enable_embeddings and chunks:
                stage_result = self._run_stage(
                    stage_name="embeddings",
                    stage_func=lambda: self.document_processor.generate_embeddings(
                        document_id=document_id,
                        chunks=chunks
                    ),
                    optional=True
                )
                results['embeddings'] = stage_result
            
            # ==========================================
            # STAGE 10: Save extracted entities to DB
            # ==========================================
            processing_result = results.get('processing', {})
            
            # Save error codes
            error_codes = processing_result.get('error_codes', [])
            if error_codes:
                self._save_error_codes(document_id, error_codes)
            
            # Save products to products table AND document_products relationship
            products = processing_result.get('products', [])
            if products:
                self._save_products(document_id, products)
                self._save_document_products(document_id, products)
            
            # ==========================================
            # Update document metadata (manufacturer, models, etc.)
            # ==========================================
            self._update_document_metadata(document_id, processing_result)
            
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
            for error_code in error_codes:
                # Convert ExtractedErrorCode to dict if needed
                ec_data = error_code if isinstance(error_code, dict) else {
                    'error_code': getattr(error_code, 'error_code', ''),
                    'error_description': getattr(error_code, 'error_description', ''),
                    'solution_text': getattr(error_code, 'solution_text', None),
                    'confidence': getattr(error_code, 'confidence', 0.0),
                    'page_number': getattr(error_code, 'page_number', None),
                    'context': getattr(error_code, 'context', None)
                }
                
                # Build metadata with context if available
                metadata = {
                    'extracted_at': datetime.utcnow().isoformat()
                }
                if ec_data.get('context'):
                    metadata['context'] = ec_data.get('context')
                
                record = {
                    'document_id': str(document_id),
                    'error_code': ec_data.get('error_code'),
                    'error_description': ec_data.get('error_description'),
                    'solution_text': ec_data.get('solution_text'),
                    'confidence_score': ec_data.get('confidence', 0.8),
                    'page_number': ec_data.get('page_number'),
                    'metadata': metadata
                }
                
                self.supabase.table('error_codes').insert(record).execute()
            
            self.logger.success(f"Saved {len(error_codes)} error codes to DB")
            
        except Exception as e:
            self.logger.error(f"Failed to save error codes: {e}")
    
    def _save_products(self, document_id: UUID, products: list):
        """Save products to krai_core.products table"""
        try:
            for product in products:
                # Convert ExtractedProduct to dict if needed
                prod_data = product if isinstance(product, dict) else {
                    'model_number': getattr(product, 'model_number', ''),
                    'series': getattr(product, 'series', None),
                    'manufacturer': getattr(product, 'manufacturer', None),
                    'product_type': getattr(product, 'product_type', 'printer'),
                    'confidence': getattr(product, 'confidence', 0.0)
                }
                
                # Try to find manufacturer_id
                manufacturer_id = None
                if prod_data.get('manufacturer'):
                    try:
                        mfr_result = self.supabase.table('manufacturers') \
                            .select('id') \
                            .ilike('name', f"%{prod_data['manufacturer']}%") \
                            .limit(1) \
                            .execute()
                        if mfr_result.data:
                            manufacturer_id = mfr_result.data[0]['id']
                    except:
                        pass
                
                record = {
                    'model_number': prod_data.get('model_number'),
                    'manufacturer_id': manufacturer_id,
                    'product_type': prod_data.get('product_type', 'printer'),
                    'metadata': {
                        'confidence': prod_data.get('confidence', 0.8),
                        'series': prod_data.get('series'),
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
                    # Insert into krai_core.products (not the view)
                    result = self.supabase.schema('krai_core').table('products').insert(record).execute()
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
                    self.supabase.schema('krai_core').table('document_products').insert(relationship).execute()
                    saved_count += 1
            
            self.logger.success(f"Saved {saved_count} document-product relationships")
            
        except Exception as e:
            self.logger.error(f"Failed to save document_products: {e}")
    
    def _update_document_metadata(self, document_id: UUID, processing_result: Dict):
        """Update document with extracted manufacturer, models, series"""
        try:
            products = processing_result.get('products', [])
            if not products:
                return
            
            # Extract manufacturer from first product
            manufacturer = None
            models = []
            series_set = set()
            
            for product in products:
                prod_data = product if isinstance(product, dict) else {
                    'manufacturer': getattr(product, 'manufacturer', None),
                    'model_number': getattr(product, 'model_number', ''),
                    'series': getattr(product, 'series', None)
                }
                
                if prod_data.get('manufacturer') and not manufacturer:
                    manufacturer = prod_data['manufacturer']
                
                if prod_data.get('model_number'):
                    models.append(prod_data['model_number'])
                
                if prod_data.get('series'):
                    series_set.add(prod_data['series'])
            
            # Update document
            update_data = {}
            if manufacturer:
                update_data['manufacturer'] = manufacturer
            if models:
                update_data['models'] = models
            if series_set:
                update_data['series'] = ','.join(sorted(series_set))  # Join multiple series
            
            if update_data:
                self.supabase.table('documents').update(update_data).eq(
                    'id', str(document_id)
                ).execute()
                
                self.logger.success(f"Updated document metadata: {manufacturer}, {len(models)} models")
        
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
