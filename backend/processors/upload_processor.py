"""
Upload Processor for KR-AI-Engine
Stage 1: Document upload and validation (Database only)
"""

import hashlib
import mimetypes
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import DocumentModel, DocumentType
from services.database_service import DatabaseService

class UploadProcessor(BaseProcessor):
    """
    Upload Processor - Stage 1 of the processing pipeline
    
    Responsibilities:
    - Document upload and validation
    - File hash generation for deduplication
    - Document metadata extraction
    - Database storage (NO Object Storage for documents!)
    
    Output: krai_core.documents (Database only)
    """
    
    def __init__(self, database_service: DatabaseService):
        super().__init__("upload_processor")
        self.database_service = database_service
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for upload processor"""
        return ['file_path', 'filename']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from upload processor"""
        return ['document_id', 'file_hash', 'document_type', 'file_size']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_core.documents']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for upload processor"""
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
        Process document upload
        
        Args:
            context: Processing context with file information
            
        Returns:
            ProcessingResult: Upload processing result
        """
        try:
            # Validate file exists
            file_path = Path(context.file_path)
            if not file_path.exists():
                raise ProcessingError(
                    f"File not found: {context.file_path}",
                    self.name,
                    "FILE_NOT_FOUND"
                )
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Generate file hash for deduplication
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Get file metadata
            file_size = len(file_content)
            content_type = mimetypes.guess_type(context.file_path)[0] or 'application/octet-stream'
            
            # Get filename from processing config
            filename = context.processing_config.get('filename', os.path.basename(context.file_path))
            
            # Detect document type from filename
            document_type = self._detect_document_type(filename)
            
            # Create document model
            document = DocumentModel(
                filename=filename,
                original_filename=filename,
                file_size=file_size,
                file_hash=file_hash,
                document_type=document_type,
                language=context.language,
                processing_status='pending',
                manufacturer=context.manufacturer,
                series=context.series,
                models=context.model.split(',') if context.model else [],
                version=context.version
            )
            
            # Store in database (NO Object Storage!)
            document_id = await self.database_service.create_document(document)
            
            # Log audit event
            await self.database_service.log_audit(
                action="document_uploaded",
                entity_type="document",
                entity_id=document_id,
                details={
                    'filename': filename,
                    'file_size': file_size,
                    'file_hash': file_hash,
                    'document_type': document_type.value
                }
            )
            
            # Return success result
            data = {
                'document_id': document_id,
                'file_hash': file_hash,
                'document_type': document_type.value,
                'file_size': file_size,
                'content_type': content_type
            }
            
            metadata = {
                'original_filename': filename,
                'processing_status': 'pending',
                'upload_timestamp': datetime.utcnow().isoformat()
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Upload processing failed: {str(e)}",
                    self.name,
                    "UPLOAD_FAILED"
                )
    
    def _detect_document_type(self, filename: str) -> DocumentType:
        """
        Detect document type from filename
        
        Args:
            filename: Original filename
            
        Returns:
            DocumentType: Detected document type
        """
        filename_lower = filename.lower()
        
        # Service Manual patterns
        if any(keyword in filename_lower for keyword in ['service', 'manual', 'repair', 'troubleshooting', 'sm_', '_sm', 'sm.']):
            return DocumentType.SERVICE_MANUAL
        
        # Parts Catalog patterns
        elif any(keyword in filename_lower for keyword in ['parts', 'catalog', 'spare', 'replacement', 'parts guide', 'parts manual', 'parts list', 'parts guide manual']):
            return DocumentType.PARTS_CATALOG
        
        # Technical Bulletin patterns
        elif any(keyword in filename_lower for keyword in ['bulletin', 'technical', 'update', 'notice']):
            return DocumentType.TECHNICAL_BULLETIN
        
        # CPMD Database patterns
        elif any(keyword in filename_lower for keyword in ['cpmd', 'database', 'error', 'code']):
            return DocumentType.CPMD_DATABASE
        
        # User Manual patterns
        elif any(keyword in filename_lower for keyword in ['user', 'guide', 'manual', 'instructions']):
            return DocumentType.USER_MANUAL
        
        # Installation Guide patterns
        elif any(keyword in filename_lower for keyword in ['installation', 'setup', 'install', 'config']):
            return DocumentType.INSTALLATION_GUIDE
        
        # Troubleshooting Guide patterns
        elif any(keyword in filename_lower for keyword in ['troubleshoot', 'diagnostic', 'problem', 'issue']):
            return DocumentType.TROUBLESHOOTING_GUIDE
        
        
        # Default to service manual
        else:
            return DocumentType.SERVICE_MANUAL
    
    def _extract_metadata_from_filename(self, filename: str) -> Dict[str, str]:
        """
        Extract metadata from filename
        
        Args:
            filename: Original filename
            
        Returns:
            Dict with extracted metadata
        """
        metadata = {}
        
        # Extract manufacturer (common patterns)
        manufacturer_patterns = ['hp', 'konica', 'minolta', 'lexmark', 'utax', 'canon', 'xerox']
        for pattern in manufacturer_patterns:
            if pattern in filename.lower():
                metadata['manufacturer'] = pattern.upper()
                break
        
        # Extract model numbers (alphanumeric patterns)
        import re
        model_patterns = re.findall(r'[A-Z]{2,}\d{2,}[A-Z]?\d*', filename.upper())
        if model_patterns:
            metadata['models'] = model_patterns
        
        # Extract version (version patterns)
        version_patterns = re.findall(r'v\d+\.\d+|\d+\.\d+', filename)
        if version_patterns:
            metadata['version'] = version_patterns[0]
        
        return metadata
