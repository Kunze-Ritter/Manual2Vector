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
            manufacturer=manufacturer
        )
        
        self.image_storage = ImageStorageProcessor()
        
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
        self.logger.info(f"🚀 MASTER PIPELINE START")
        self.logger.info(f"📄 File: {file_path.name}")
        self.logger.info(f"🏭 Manufacturer: {manufacturer}")
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
                    file_path=file_path,
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
            # Update document status
            # ==========================================
            self._update_document_status(
                document_id=document_id,
                status='completed',
                results=results
            )
            
            # ==========================================
            # Summary
            # ==========================================
            processing_time = time.time() - start_time
            
            self.logger.info("="*80)
            self.logger.success("🎉 PIPELINE COMPLETE!")
            self.logger.info(f"⏱️  Total Time: {processing_time:.1f}s")
            self.logger.info(f"📊 Results:")
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
        self.logger.info(f"\n▶️  Stage: {stage_name.upper()}")
        
        try:
            result = stage_func()
            
            # Handle skipped optional stages
            if result.get('skipped'):
                self.logger.info(f"⏭️  {stage_name} skipped (optional)")
                return result
            
            # Check success
            if result.get('success'):
                self.logger.success(f"✅ {stage_name} complete")
                return result
            else:
                error = result.get('error', 'Unknown error')
                self.logger.warning(f"⚠️  {stage_name} failed: {error}")
                
                # Retry logic
                if retry_count < self.max_retries:
                    self.logger.info(f"🔄 Retrying {stage_name} ({retry_count + 1}/{self.max_retries})...")
                    time.sleep(1)  # Brief delay before retry
                    return self._run_stage(stage_name, stage_func, optional, retry_count + 1)
                
                # If optional, continue pipeline
                if optional:
                    self.logger.warning(f"⏭️  Skipping optional stage: {stage_name}")
                    return result
                
                # Otherwise, stage has failed
                return result
                
        except Exception as e:
            self.logger.error(f"❌ {stage_name} exception: {e}")
            
            # Retry on exception
            if retry_count < self.max_retries:
                self.logger.info(f"🔄 Retrying {stage_name} ({retry_count + 1}/{self.max_retries})...")
                time.sleep(1)
                return self._run_stage(stage_name, stage_func, optional, retry_count + 1)
            
            return {
                'success': False,
                'error': str(e),
                'stage': stage_name
            }
    
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
                update_data['processing_results'] = results
            
            self.supabase.table('documents').update(update_data).eq(
                'id', str(document_id)
            ).execute()
            
        except Exception as e:
            self.logger.error(f"Failed to update document status: {e}")
    
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
        self.logger.error(f"❌ PIPELINE FAILED")
        self.logger.error(f"⏱️  Time: {processing_time:.1f}s")
        self.logger.error(f"💥 Error: {error}")
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
        self.logger.info(f"📦 BATCH PROCESSING: {len(file_paths)} documents")
        self.logger.info("="*80)
        
        start_time = time.time()
        
        results = []
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(file_paths, 1):
            self.logger.info(f"\n📄 Processing {i}/{len(file_paths)}: {file_path.name}")
            
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
        self.logger.info("📊 BATCH COMPLETE")
        self.logger.info(f"✅ Successful: {successful}/{len(file_paths)}")
        self.logger.info(f"❌ Failed: {failed}/{len(file_paths)}")
        self.logger.info(f"⏱️  Total Time: {total_time:.1f}s")
        self.logger.info(f"⚡ Avg Time: {total_time/len(file_paths):.1f}s per document")
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
