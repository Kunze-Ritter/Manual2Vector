"""
Stage 1: Upload Processor

Handles document ingestion, validation, deduplication, and queue management.
"""

import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .logger import get_logger
from .stage_tracker import StageTracker


class UploadProcessor:
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
        supabase_client,
        max_file_size_mb: int = 500,
        allowed_extensions: list = None
    ):
        """
        Initialize upload processor
        
        Args:
            supabase_client: Supabase client instance
            max_file_size_mb: Maximum file size in MB
            allowed_extensions: List of allowed file extensions
        """
        self.supabase = supabase_client
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or ['.pdf']
        self.logger = get_logger()
        self.stage_tracker = StageTracker(supabase_client)
    
    def process_upload(
        self,
        file_path: Path,
        document_type: str = "service_manual",
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process a document upload
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (service_manual, parts_catalog, user_guide)
            force_reprocess: If True, reprocess even if document exists
            
        Returns:
            Dict with status, document_id, and metadata
        """
        self.logger.info(f"Processing upload: {file_path.name}")
        
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
        
        # Step 3: Check for duplicates
        existing_doc = self._check_duplicate(file_hash)
        
        if existing_doc and not force_reprocess:
            self.logger.info(f"Duplicate found: {existing_doc['id']}")
            return {
                'success': True,
                'document_id': existing_doc['id'],
                'status': 'duplicate',
                'existing_document': existing_doc,
                'reprocessing': False
            }
        
        # Step 4: Extract basic metadata
        metadata = self._extract_basic_metadata(file_path)
        
        # Step 5: Create or update database record
        if existing_doc and force_reprocess:
            # Update existing record
            document_id = existing_doc['id']
            self.logger.info(f"Reprocessing document: {document_id}")
            self._update_document_record(document_id, metadata, file_hash)
            status = 'reprocessing'
        else:
            # Create new record
            document_id = self._create_document_record(
                file_path,
                file_hash,
                document_type,
                metadata
            )
            status = 'new'
            self.logger.success(f"Created document record: {document_id}")
        
        # Step 6: Add to processing queue
        self._add_to_queue(document_id, file_path)
        
        # Step 7: Mark upload stage as completed
        self.stage_tracker.complete_stage(
            document_id=document_id,
            stage_name='upload',
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
        
        # Check if file exists
        if not file_path.exists():
            return {'valid': False, 'error': f"File not found: {file_path}"}
        
        # Check file extension
        if file_path.suffix.lower() not in self.allowed_extensions:
            return {
                'valid': False,
                'error': f"Invalid file type. Allowed: {self.allowed_extensions}"
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
    
    def _check_duplicate(self, file_hash: str) -> Optional[Dict]:
        """Check if document with same hash already exists"""
        try:
            result = self.supabase.table("vw_documents") \
                .select("*") \
                .eq("file_hash", file_hash) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking duplicates: {e}")
            return None
    
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
    
    def _create_document_record(
        self,
        file_path: Path,
        file_hash: str,
        document_type: str,
        metadata: Dict
    ) -> str:
        """Create new document record in database"""
        
        document_id = str(uuid4())
        
        # Extract version from PDF metadata if available
        version_string = None
        if 'title' in metadata:
            # Try to extract version from title
            from .version_extractor import VersionExtractor
            version_extractor = VersionExtractor()
            versions = version_extractor.extract_from_text(metadata['title'])
            if versions:
                version_string = versions[0].version_string
        
        record = {
            'id': document_id,
            'filename': file_path.name,
            'original_filename': file_path.name,
            'storage_path': str(file_path),  # Use storage_path instead of file_path
            'file_hash': file_hash,
            'file_size': metadata['file_size_bytes'],  # Use file_size not file_size_bytes
            'document_type': document_type,
            'version': version_string,  # Add version if found
            'page_count': metadata.get('page_count', 0),
            'processing_status': 'uploaded',  # Use processing_status not status
            'extracted_metadata': {  # Use extracted_metadata not metadata
                'pdf_metadata': metadata,
                'validation': {
                    'validated_at': datetime.utcnow().isoformat(),
                    'valid': True
                },
                'uploaded_at': datetime.utcnow().isoformat()
            }
        }
        
        try:
            self.supabase.table("vw_documents").insert(record).execute()
            return document_id
            
        except Exception as e:
            self.logger.error(f"Failed to create document record: {e}")
            raise
    
    def _update_document_record(
        self,
        document_id: str,
        metadata: Dict,
        file_hash: str
    ):
        """Update existing document record for reprocessing"""
        
        update_data = {
            'file_hash': file_hash,
            'file_size': metadata['file_size_bytes'],
            'page_count': metadata.get('page_count', 0),
            'processing_status': 'reprocessing',
            'extracted_metadata': {
                'pdf_metadata': metadata,
                'validation': {
                    'validated_at': datetime.utcnow().isoformat(),
                    'valid': True
                },
                'reprocessed_at': datetime.utcnow().isoformat()
            }
        }
        
        try:
            self.supabase.table("vw_documents") \
                .update(update_data) \
                .eq("id", document_id) \
                .execute()
                
        except Exception as e:
            self.logger.error(f"Failed to update document record: {e}")
            raise
    
    def _add_to_queue(self, document_id: str, file_path: Path):
        """Add document to processing queue"""
        
        queue_record = {
            'document_id': document_id,
            'task_type': 'text_extraction',  # Use task_type instead of current_stage
            'status': 'pending',
            'priority': 5  # Default priority (1=highest, 10=lowest)
        }
        
        try:
            self.supabase.table("vw_processing_queue").insert(queue_record).execute()
            self.logger.debug(f"Added to queue: {document_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to add to queue: {e}")
            # Non-critical error, document record exists


class BatchUploadProcessor:
    """Process multiple documents in batch"""
    
    def __init__(self, supabase_client, max_file_size_mb: int = 500):
        """Initialize batch processor"""
        self.upload_processor = UploadProcessor(supabase_client, max_file_size_mb)
        self.logger = get_logger()
    
    def process_directory(
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
                result = self.upload_processor.process_upload(
                    pdf_file,
                    document_type,
                    force_reprocess
                )
                
                if result['success']:
                    results['successful'] += 1
                    
                    if result['status'] == 'duplicate':
                        results['duplicates'] += 1
                    elif result['status'] == 'reprocessing':
                        results['reprocessed'] += 1
                    
                    results['documents'].append({
                        'filename': pdf_file.name,
                        'document_id': result['document_id'],
                        'status': result['status']
                    })
                else:
                    results['failed'] += 1
                    results['documents'].append({
                        'filename': pdf_file.name,
                        'error': result['error']
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
