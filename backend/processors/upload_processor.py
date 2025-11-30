"""
Stage 1: Upload Processor

Handles document ingestion, validation, deduplication, and queue management.
"""

import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from backend.core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, Stage, ProcessingError
from backend.core.data_models import DocumentModel, ProcessingQueueModel, ProcessingStatus, DocumentType
from backend.services.database_adapter import DatabaseAdapter
from .stage_tracker import StageTracker


class UploadProcessor(BaseProcessor):
    """
    Stage 1: Document Upload & Validation
    
    Responsibilities:
    1. File validation (format, size, corruption)
    2. Duplicate detection (hash-based)
    3. Database record creation
    4. Processing queue management
    """
    
    def __init__(
        self,
        database_adapter: DatabaseAdapter,
        max_file_size_mb: int = 500,
        allowed_extensions: list = None
    ):
        """
        Initialize upload processor
        
        Args:
            database_adapter: Database adapter instance
            max_file_size_mb: Maximum file size in MB
            allowed_extensions: List of allowed file extensions
        """
        super().__init__(name="upload_processor")
        self.stage = Stage.UPLOAD
        self.database = database_adapter
        
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or ['.pdf']

        # Stage tracking with database adapter
        self.stage_tracker = StageTracker(database_adapter) if database_adapter else None
    
    async def process(self, context) -> ProcessingResult:
        """Async entrypoint used by the pipeline framework.

        Wraps the synchronous ``process_upload`` helper and returns a
        ``ProcessingResult`` so that :meth:`BaseProcessor.safe_process` can
        attach timing information and logging without errors.
        """
        if not hasattr(context, "file_path"):
            raise ProcessingError(
                "Processing context must provide 'file_path'",
                self.name,
                "MISSING_FILE_PATH",
            )

        file_path = Path(context.file_path)
        # Treat missing or empty document_type as default 'service_manual' for robustness
        document_type = getattr(context, "document_type", None) or "service_manual"
        force_reprocess = getattr(context, "force_reprocess", False)

        # Use DatabaseAdapter path
        raw_result = await self._process_with_adapter(
            file_path=file_path,
            document_type=document_type,
            force_reprocess=force_reprocess,
            context=context,
        )

        if not isinstance(raw_result, dict):
            raise ProcessingError(
                "Upload processor returned unexpected result type",
                self.name,
                "INVALID_RESULT_TYPE",
            )

        metadata: Dict[str, Any] = {
            "document_id": raw_result.get("document_id"),
            "file_path": str(file_path),
            "stage": self.stage.value,
        }

        if raw_result.get("success"):
            return self.create_success_result(data=raw_result, metadata=metadata)

        error_message = raw_result.get("error") or "Upload failed"
        error = ProcessingError(error_message, self.name, "UPLOAD_FAILED")
        return self.create_error_result(error=error, metadata=metadata)

    async def _process_with_adapter(
        self,
        file_path: Path,
        document_type: str,
        force_reprocess: bool,
        context: Optional[ProcessingContext] = None,
    ) -> Dict[str, Any]:
        """Adapter-based upload path using DatabaseService/DatabaseAdapter (e.g. PostgreSQLAdapter)."""

        with self.logger_context(stage=self.stage, document_id=None, file=file_path.name) as adapter:
            adapter.info("Processing upload: %s", file_path.name)

        # Step 1: Validate file
        validation_result = self._validate_file(file_path)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'document_id': None
            }

        # Step 2: Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        self.logger.debug(f"File hash: {file_hash}")

        # Step 3: Extract basic metadata
        metadata = self._extract_basic_metadata(file_path)

        # Step 4: Check for duplicates via adapter
        existing_doc = None
        if hasattr(self.database, "get_document_by_hash"):
            existing_doc = await self.database.get_document_by_hash(file_hash)

        if existing_doc and not force_reprocess:
            document_id = str(existing_doc.get('id') or existing_doc.get('document_id'))
            with self.logger_context(stage=self.stage, document_id=document_id) as adapter:
                adapter.info("Duplicate found - skipping reprocess")
            return {
                'success': True,
                'document_id': document_id,
                'status': 'duplicate',
                'existing_document': existing_doc,
                'reprocessing': False
            }

        language = getattr(context, "language", "en") if context is not None else "en"

        # Step 5: Create or update database record via adapter
        if existing_doc and force_reprocess:
            # Update existing record
            document_id = str(existing_doc.get('id') or existing_doc.get('document_id'))
            with self.logger_context(stage=self.stage, document_id=document_id) as adapter:
                adapter.info("Reprocessing existing document")

            # Only update columns that are known to exist in krai_core.documents
            updates = {
                'file_hash': file_hash,
                'file_size': metadata['file_size_bytes'],
                'processing_status': ProcessingStatus.PENDING.value,
            }
            if hasattr(self.database, "update_document"):
                await self.database.update_document(document_id, updates)
            status = 'reprocessing'
        else:
            # Create new record
            document_type_value = document_type
            try:
                document_type_value = DocumentType(document_type).value
            except Exception:
                # Fallback to raw string if enum conversion fails
                document_type_value = document_type

            doc_model = DocumentModel(
                filename=file_path.name,
                original_filename=file_path.name,
                file_size=metadata['file_size_bytes'],
                file_hash=file_hash,
                document_type=document_type_value,
                language=language,
                processing_status=ProcessingStatus.PENDING,
                storage_path=str(file_path),
            )

            document_id = await self.database.create_document(doc_model)
            status = 'new'
            self.logger.success(f"Created document record: {document_id}")

        # Step 6: Add to processing queue via adapter (non-critical)
        try:
            queue_item = ProcessingQueueModel(
                document_id=document_id,
                processor_name=self.name,
                status=ProcessingStatus.PENDING,
                priority=5,
            )
            if hasattr(self.database, "create_processing_queue_item"):
                await self.database.create_processing_queue_item(queue_item)
        except Exception as e:
            # Non-critical: queue table may not exist or schema mismatch
            self.logger.debug(f"Processing queue entry skipped (non-critical): {e}")

        # Step 7: Mark upload stage as completed (only when tracker is available)
        if self.stage_tracker is not None:
            await self.stage_tracker.complete_stage(
                document_id=document_id,
                stage_name=self.stage,
                metadata={
                    'file_hash': file_hash,
                    'file_size': metadata['file_size_bytes'],
                    'page_count': metadata.get('page_count', 0)
                }
            )

        return {
            'success': True,
            'document_id': document_id,
            'status': status,
            'file_hash': file_hash,
            'metadata': metadata
        }

    
    def _validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate file format and size"""
        
        # Debug logging for file validation
        self.logger.debug(
            "Validating file: %s (suffix=%r) allowed=%s",
            file_path,
            file_path.suffix,
            self.allowed_extensions,
        )

        # Check if file exists
        if not file_path.exists():
            return {'valid': False, 'error': f"File not found: {file_path}"}
        
        # Check file extension
        if file_path.suffix.lower() not in self.allowed_extensions:
            return {
                'valid': False,
                'error': f"Invalid file type '{file_path.suffix}'. Allowed: {self.allowed_extensions}"
            }
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return {
                'valid': False,
                'error': f"File too large: {actual_mb:.1f}MB (max: {max_mb}MB)"
            }
        
        # Check if file is corrupted (basic check - can be opened)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()
            
            if page_count == 0:
                return {'valid': False, 'error': "PDF has no pages"}
            
        except Exception as e:
            return {'valid': False, 'error': f"Corrupted or invalid PDF: {str(e)}"}
        
        return {'valid': True, 'error': None}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    
    def _extract_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata from PDF"""
        import fitz  # PyMuPDF
        
        metadata = {
            'filename': file_path.name,
            'file_size_bytes': file_path.stat().st_size,
            'file_modified_at': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        try:
            doc = fitz.open(file_path)
            
            # PDF metadata
            pdf_meta = doc.metadata
            metadata.update({
                'page_count': len(doc),
                'title': pdf_meta.get('title', '') or file_path.stem,
                'author': pdf_meta.get('author', ''),
                'subject': pdf_meta.get('subject', ''),
                'creator': pdf_meta.get('creator', ''),
                'producer': pdf_meta.get('producer', ''),
                'creation_date': pdf_meta.get('creationDate', ''),
                'modification_date': pdf_meta.get('modDate', '')
            })
            
            doc.close()
            
        except Exception as e:
            self.logger.warning(f"Could not extract PDF metadata: {e}")
            metadata['page_count'] = 0
            metadata['title'] = file_path.stem
        
        return metadata
    
    
    


class BatchUploadProcessor:
    """Process multiple documents in batch"""
    
    def __init__(self, database_adapter: DatabaseAdapter, max_file_size_mb: int = 500):
        """Initialize batch processor"""
        self.upload_processor = UploadProcessor(database_adapter, max_file_size_mb)
        self.logger = get_logger()
    
    async def process_directory(
        self,
        directory: Path,
        document_type: str = "service_manual",
        recursive: bool = False,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process all PDFs in a directory
        
        Args:
            directory: Directory containing PDFs
            document_type: Type of documents
            recursive: If True, search subdirectories
            force_reprocess: If True, reprocess existing documents
            
        Returns:
            Dict with processing results
        """
        self.logger.section(f"Batch Upload: {directory}")
        
        # Find all PDFs
        if recursive:
            pdf_files = list(directory.rglob("*.pdf"))
        else:
            pdf_files = list(directory.glob("*.pdf"))
        
        self.logger.info(f"Found {len(pdf_files)} PDF files")
        
        results = {
            'total': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'reprocessed': 0,
            'documents': []
        }
        
        for pdf_file in pdf_files:
            try:
                result = await self.upload_processor.process(
                    ProcessingContext(
                        file_path=pdf_file,
                        document_type=document_type,
                        force_reprocess=force_reprocess
                    )
                )
                
                if result.success:
                    results['successful'] += 1
                    
                    if result.data.get('status') == 'duplicate':
                        results['duplicates'] += 1
                    elif result.data.get('status') == 'reprocessing':
                        results['reprocessed'] += 1
                    
                    results['documents'].append({
                        'filename': pdf_file.name,
                        'document_id': result.data.get('document_id'),
                        'status': result.data.get('status')
                    })
                else:
                    results['failed'] += 1
                    results['documents'].append({
                        'filename': pdf_file.name,
                        'error': str(result.error) if result.error else 'Processing failed'
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {e}")
                results['failed'] += 1
                results['documents'].append({
                    'filename': pdf_file.name,
                    'error': str(e)
                })
        
        # Summary
        self.logger.section("Batch Upload Summary")
        self.logger.info(f"Total: {results['total']}")
        self.logger.success(f"Successful: {results['successful']}")
        if results['duplicates'] > 0:
            self.logger.info(f"Duplicates skipped: {results['duplicates']}")
        if results['reprocessed'] > 0:
            self.logger.info(f"Reprocessed: {results['reprocessed']}")
        if results['failed'] > 0:
            self.logger.warning(f"Failed: {results['failed']}")
        
        return results
