"""
Storage Processor for KR-AI-Engine
Stage 6: Object storage management (NUR Bilder!)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService

class StorageProcessor(BaseProcessor):
    """
    Storage Processor - Stage 6 of the processing pipeline
    
    Responsibilities:
    - Object storage management (NUR Bilder!)
    - File deduplication
    - Storage optimization
    
    Output: Cloudflare R2 (NUR Bilder!)
    """
    
    def __init__(self, database_service: DatabaseService, storage_service: ObjectStorageService):
        super().__init__("storage_processor")
        self.database_service = database_service
        self.storage_service = storage_service
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for storage processor"""
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from storage processor"""
        return ['storage_urls', 'deduplication_results']
    
    def get_storage_buckets(self) -> List[str]:
        """Get storage buckets this processor uses"""
        return ['krai-documents', 'krai-error-images', 'krai-parts-images']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['image_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for storage processor"""
        return {
            'cpu_intensive': False,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 0.5,
            'estimated_gpu_gb': 0.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process storage operations
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Storage processing result
        """
        try:
            # Get document info
            document = await self.database_service.get_document(context.document_id)
            if not document:
                raise ProcessingError(
                    f"Document not found: {context.document_id}",
                    self.name,
                    "DOCUMENT_NOT_FOUND"
                )
            
            # IMPORTANT: Documents are NOT stored in Object Storage!
            # Only images are stored in Object Storage
            
            # Check for duplicate files
            file_hash = document.file_hash
            duplicate_check = await self.storage_service.check_duplicate(file_hash)
            
            if duplicate_check:
                self.logger.info(f"Duplicate file found: {duplicate_check['url']}")
                storage_urls = [duplicate_check['url']]
            else:
                # No duplicates found
                storage_urls = []
            
            # Log audit event
            await self.database_service.log_audit(
                action="storage_processed",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'file_hash': file_hash,
                    'duplicate_found': bool(duplicate_check),
                    'storage_urls': storage_urls
                }
            )
            
            # Return success result
            data = {
                'storage_urls': storage_urls,
                'deduplication_results': {
                    'duplicate_found': bool(duplicate_check),
                    'file_hash': file_hash
                }
            }
            
            metadata = {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'storage_provider': 'cloudflare_r2'
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Storage processing failed: {str(e)}",
                    self.name,
                    "STORAGE_PROCESSING_FAILED"
                )
