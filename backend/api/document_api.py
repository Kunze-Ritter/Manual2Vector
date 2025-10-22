"""
Document API for KR-AI-Engine
FastAPI endpoints for document processing
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime

from backend.core.data_models import DocumentUploadRequest, DocumentUploadResponse, DocumentType
from backend.services.database_service import DatabaseService
from backend.services.object_storage_service import ObjectStorageService
from backend.services.ai_service import AIService
from backend.processors.upload_processor import UploadProcessor
from backend.processors.master_pipeline import MasterPipeline

class DocumentAPI:
    """
    Document API for KR-AI-Engine
    
    Uses MasterPipeline for full production processing with all optimizations:
    - Pre-compiled regex patterns (60x faster error code enrichment)
    - LLM-based product extraction (configurable via LLM_MAX_PAGES)
    - OCR optimization (2x faster, no duplicate calls)
    - Series detection and product type mapping
    - Image processing with Vision AI
    - Embeddings generation
    - R2 storage integration
    
    Endpoints:
    - POST /documents/upload: Upload document
    - GET /documents/{document_id}: Get document info
    - GET /documents/{document_id}/status: Get processing status
    - POST /documents/{document_id}/reprocess: Reprocess document
    """
    
    def __init__(self, 
                 database_service: DatabaseService,
                 storage_service: ObjectStorageService,
                 ai_service: AIService):
        self.database_service = database_service
        self.storage_service = storage_service
        self.ai_service = ai_service
        self.logger = logging.getLogger("krai.api.document")
        self._setup_logging()
        
        # Initialize upload processor (for initial file handling)
        self.upload_processor = UploadProcessor(database_service)
        # Processing is done via MasterPipeline (same as process_production.py)
        
        # Create router
        self.router = APIRouter(prefix="/documents", tags=["documents"])
        self._setup_routes()
    
    def _setup_logging(self):
        """Setup logging for document API"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - DocumentAPI - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/upload", response_model=DocumentUploadResponse)
        async def upload_document(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            document_type: Optional[DocumentType] = None,
            language: str = "en"
        ):
            """Upload and process document"""
            try:
                # Read file content
                file_content = await file.read()
                
                # Create processing context
                from core.base_processor import ProcessingContext
                context = ProcessingContext(
                    document_id="",  # Will be set by upload processor
                    file_path="",  # Will be set by upload processor
                    file_hash="",  # Will be set by upload processor
                    document_type=document_type.value if document_type else "service_manual",
                    manufacturer=None,
                    model=None,
                    series=None,
                    version=None,
                    language=language
                )
                
                # Process upload
                result = await self.upload_processor.safe_process(context)
                
                if not result.success:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Upload failed: {result.error.message}"
                    )
                
                # Start background processing
                background_tasks.add_task(
                    self._process_document_background,
                    result.data['document_id'],
                    file_content,
                    file.filename
                )
                
                return DocumentUploadResponse(
                    document_id=result.data['document_id'],
                    status='pending',
                    message='Document uploaded successfully. Processing started.',
                    processing_time=result.processing_time
                )
                
            except Exception as e:
                self.logger.error(f"Document upload failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/{document_id}")
        async def get_document(document_id: str):
            """Get document information"""
            try:
                document = await self.database_service.get_document(document_id)
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                return {
                    'document_id': document.id,
                    'filename': document.filename,
                    'file_size': document.file_size,
                    'document_type': document.document_type,
                    'processing_status': document.processing_status,
                    'manufacturer': document.manufacturer,
                    'series': document.series,
                    'models': document.models,
                    'version': document.version,
                    'created_at': document.created_at,
                    'updated_at': document.updated_at
                }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get document {document_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/{document_id}/status")
        async def get_document_status(document_id: str):
            """Get document processing status"""
            try:
                document = await self.database_service.get_document(document_id)
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                # Get processing queue status
                queue_items = await self.database_service.get_pending_queue_items("all")
                processing_status = {
                    'document_status': document.processing_status,
                    'queue_position': len([item for item in queue_items if item.document_id == document_id]),
                    'total_queue_items': len(queue_items)
                }
                
                return processing_status
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get document status {document_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/{document_id}/reprocess")
        async def reprocess_document(document_id: str):
            """Reprocess document"""
            try:
                document = await self.database_service.get_document(document_id)
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                # Reset processing status
                await self.database_service.update_document(
                    document_id,
                    {'processing_status': 'pending'}
                )
                
                # Add to processing queue
                from core.data_models import ProcessingQueueModel
                queue_item = ProcessingQueueModel(
                    document_id=document_id,
                    processor_name="upload_processor",
                    status="pending",
                    priority=1
                )
                await self.database_service.create_processing_queue_item(queue_item)
                
                return {
                    'message': 'Document queued for reprocessing',
                    'document_id': document_id,
                    'status': 'pending'
                }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to reprocess document {document_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/{document_id}/chunks")
        async def get_document_chunks(document_id: str, limit: int = 100, offset: int = 0):
            """Get document chunks"""
            try:
                # This would typically query the database for chunks
                # For now, return a placeholder
                return {
                    'document_id': document_id,
                    'chunks': [],
                    'total_count': 0,
                    'limit': limit,
                    'offset': offset
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get document chunks {document_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/{document_id}/images")
        async def get_document_images(document_id: str):
            """Get document images"""
            try:
                # This would typically query the database for images
                # For now, return a placeholder
                return {
                    'document_id': document_id,
                    'images': [],
                    'total_count': 0
                }
            except Exception as e:
                self.logger.error(f"Failed to get document images {document_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_document_background(self, document_id: str, file_content: bytes, filename: str):
        """Background document processing using MasterPipeline"""
        try:
            self.logger.info(f"Starting background processing for document {document_id}")
            
            # Save file temporarily
            import tempfile
            import os
            from pathlib import Path
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = Path(temp_file.name)
            
            try:
                # Initialize MasterPipeline with FULL PRODUCTION settings
                # This uses ALL the optimized processors (error_code_extractor, product_extractor, etc.)
                self.logger.info("Initializing MasterPipeline with production settings...")
                
                # Read settings from environment
                upload_images = os.getenv('UPLOAD_IMAGES_TO_R2', 'false').lower() == 'true'
                upload_documents = os.getenv('UPLOAD_DOCUMENTS_TO_R2', 'false').lower() == 'true'
                
                pipeline = MasterPipeline(
                    supabase_client=self.database_service.supabase,
                    manufacturer="AUTO",  # Auto-detect manufacturer
                    enable_images=True,          # Extract images
                    enable_ocr=True,              # OCR on images
                    enable_vision=True,           # Vision AI analysis
                    upload_images_to_r2=upload_images,      # Upload images to R2 (from .env)
                    upload_documents_to_r2=upload_documents,  # Upload PDFs to R2 (from .env)
                    enable_embeddings=True,       # Generate embeddings
                    max_retries=2
                )
                
                self.logger.info("Processing document through MasterPipeline...")
                
                # Process through MasterPipeline (same as process_production.py!)
                result = pipeline.process_document(
                    file_path=temp_file_path,
                    document_type="service_manual",
                    manufacturer="AUTO"  # Auto-detect
                )
                
                if result['success']:
                    self.logger.info(f"✅ Document {document_id} processed successfully")
                    self.logger.info(f"   Products: {result.get('products_extracted', 0)}")
                    self.logger.info(f"   Error Codes: {result.get('error_codes_extracted', 0)}")
                    self.logger.info(f"   Parts: {result.get('parts_extracted', 0)}")
                    self.logger.info(f"   Images: {result.get('images_processed', 0)}")
                    self.logger.info(f"   Chunks: {result.get('chunks_created', 0)}")
                else:
                    self.logger.error(f"❌ Document {document_id} processing failed: {result.get('error')}")
                
            finally:
                # Clean up temporary file
                if temp_file_path.exists():
                    temp_file_path.unlink()
        
        except Exception as e:
            self.logger.error(f"Background processing failed for document {document_id}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Update document status to failed
            try:
                await self.database_service.update_document(
                    document_id,
                    {'processing_status': 'failed'}
                )
            except:
                pass
