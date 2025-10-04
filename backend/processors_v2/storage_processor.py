"""
Storage Processor - Cloudflare R2 Integration

Handles document storage, presigned URLs, and lifecycle management.
Cloudflare R2 is S3-compatible, so we use boto3.

Features:
- Upload PDFs to R2
- Generate presigned URLs
- File organization (by manufacturer/year)
- Storage statistics
- Cleanup & lifecycle management
"""

import os
from pathlib import Path as FilePath
from dotenv import load_dotenv

# Load .env from project root (2 levels up from this file)
env_path = FilePath(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
import hashlib
import mimetypes

from .logger import get_logger
from .stage_tracker import StageTracker, StageContext


class StorageProcessor:
    """
    Stage 6: Storage Processor
    
    Handles document storage in Cloudflare R2.
    """
    
    def __init__(
        self,
        supabase_client=None,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        """
        Initialize storage processor
        
        Args:
            supabase_client: Supabase client for stage tracking
            bucket_name: R2 bucket name (default: from env)
            endpoint_url: R2 endpoint URL (default: from env)
            access_key: R2 access key (default: from env)
            secret_key: R2 secret key (default: from env)
        """
        self.logger = get_logger()
        self.supabase = supabase_client
        
        # Load R2 credentials
        # Try multiple bucket name options for backward compatibility
        self.bucket_name = bucket_name or os.getenv('R2_BUCKET_NAME') or os.getenv('R2_BUCKET_NAME_DOCUMENTS', 'krai-documents-images')
        self.endpoint_url = endpoint_url or os.getenv('R2_ENDPOINT_URL')
        self.access_key = access_key or os.getenv('R2_ACCESS_KEY_ID')
        self.secret_key = secret_key or os.getenv('R2_SECRET_ACCESS_KEY')
        
        # Validate configuration
        if not all([self.endpoint_url, self.access_key, self.secret_key]):
            self.logger.warning("R2 credentials not fully configured!")
            self.logger.warning("Set R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
            self.r2_client = None
        else:
            # Initialize R2 client (S3-compatible)
            self.r2_client = self._create_r2_client()
        
        # Stage tracker
        if supabase_client:
            self.stage_tracker = StageTracker(supabase_client)
        else:
            self.stage_tracker = None
    
    def _create_r2_client(self):
        """Create boto3 S3 client for R2"""
        try:
            client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'path'}
                ),
                region_name='auto'  # R2 uses 'auto'
            )
            
            self.logger.success("R2 client initialized")
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to create R2 client: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if R2 is properly configured"""
        return self.r2_client is not None
    
    def upload_document(
        self,
        document_id: UUID,
        file_path: Path,
        manufacturer: Optional[str] = None,
        document_type: str = "service_manual",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload document to R2
        
        Args:
            document_id: Document UUID
            file_path: Local file path
            manufacturer: Manufacturer name
            document_type: Type of document
            metadata: Additional metadata
            
        Returns:
            Dict with upload result
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'R2 not configured',
                'storage_url': None,
                'storage_path': None
            }
        
        # Start stage tracking
        if self.stage_tracker:
            self.stage_tracker.start_stage(str(document_id), 'storage')
        
        try:
            # Generate storage path
            storage_path = self._generate_storage_path(
                document_id,
                file_path.name,
                manufacturer,
                document_type
            )
            
            self.logger.info(f"Uploading to R2: {storage_path}")
            
            # Prepare metadata
            upload_metadata = {
                'document-id': str(document_id),
                'document-type': document_type,
                'original-filename': file_path.name,
                'upload-timestamp': datetime.utcnow().isoformat()
            }
            
            if manufacturer:
                upload_metadata['manufacturer'] = manufacturer
            
            if metadata:
                # Add custom metadata (flatten to strings)
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float)):
                        upload_metadata[f'custom-{key}'] = str(value)
            
            # Determine content type
            content_type = mimetypes.guess_type(file_path)[0] or 'application/pdf'
            
            # Upload file
            with open(file_path, 'rb') as f:
                self.r2_client.upload_fileobj(
                    f,
                    self.bucket_name,
                    storage_path,
                    ExtraArgs={
                        'Metadata': upload_metadata,
                        'ContentType': content_type
                    }
                )
            
            self.logger.success(f"Uploaded to R2: {storage_path}")
            
            # Generate storage URL
            storage_url = f"{self.endpoint_url}/{self.bucket_name}/{storage_path}"
            
            # Update stage tracking
            if self.stage_tracker:
                self.stage_tracker.complete_stage(
                    str(document_id),
                    'storage',
                    metadata={
                        'storage_path': storage_path,
                        'storage_url': storage_url,
                        'file_size': file_path.stat().st_size
                    }
                )
            
            return {
                'success': True,
                'storage_url': storage_url,
                'storage_path': storage_path,
                'bucket': self.bucket_name,
                'file_size': file_path.stat().st_size
            }
            
        except ClientError as e:
            error_msg = f"R2 upload failed: {e}"
            self.logger.error(error_msg)
            
            if self.stage_tracker:
                self.stage_tracker.fail_stage(
                    str(document_id),
                    'storage',
                    error_msg
                )
            
            return {
                'success': False,
                'error': error_msg,
                'storage_url': None,
                'storage_path': None
            }
        
        except Exception as e:
            error_msg = f"Upload error: {e}"
            self.logger.error(error_msg)
            
            if self.stage_tracker:
                self.stage_tracker.fail_stage(
                    str(document_id),
                    'storage',
                    error_msg
                )
            
            return {
                'success': False,
                'error': error_msg,
                'storage_url': None,
                'storage_path': None
            }
    
    def _generate_storage_path(
        self,
        document_id: UUID,
        filename: str,
        manufacturer: Optional[str],
        document_type: str
    ) -> str:
        """
        Generate organized storage path
        
        Format: {document_type}/{manufacturer}/{year}/{document_id}/{filename}
        Example: service_manual/hp/2024/abc-123/manual.pdf
        """
        year = datetime.utcnow().year
        
        # Sanitize manufacturer name
        if manufacturer:
            manufacturer_clean = manufacturer.lower().replace(' ', '_').replace('/', '_')
        else:
            manufacturer_clean = 'unknown'
        
        # Sanitize document type
        doc_type_clean = document_type.lower().replace(' ', '_')
        
        # Create path
        path = f"{doc_type_clean}/{manufacturer_clean}/{year}/{document_id}/{filename}"
        
        return path
    
    def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access
        
        Args:
            storage_path: Path in R2 bucket
            expiration: URL expiration in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None
        """
        if not self.is_configured():
            self.logger.warning("Cannot generate presigned URL: R2 not configured")
            return None
        
        try:
            url = self.r2_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_path
                },
                ExpiresIn=expiration
            )
            
            self.logger.debug(f"Generated presigned URL for: {storage_path}")
            return url
            
        except ClientError as e:
            self.logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def download_document(
        self,
        storage_path: str,
        local_path: Path
    ) -> bool:
        """
        Download document from R2
        
        Args:
            storage_path: Path in R2 bucket
            local_path: Local destination path
            
        Returns:
            True if successful
        """
        if not self.is_configured():
            self.logger.error("Cannot download: R2 not configured")
            return False
        
        try:
            self.logger.info(f"Downloading from R2: {storage_path}")
            
            # Create parent directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.r2_client.download_file(
                self.bucket_name,
                storage_path,
                str(local_path)
            )
            
            self.logger.success(f"Downloaded to: {local_path}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Download failed: {e}")
            return False
    
    def delete_document(
        self,
        storage_path: str
    ) -> bool:
        """
        Delete document from R2
        
        Args:
            storage_path: Path in R2 bucket
            
        Returns:
            True if successful
        """
        if not self.is_configured():
            self.logger.error("Cannot delete: R2 not configured")
            return False
        
        try:
            self.logger.info(f"Deleting from R2: {storage_path}")
            
            self.r2_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            
            self.logger.success(f"Deleted: {storage_path}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Delete failed: {e}")
            return False
    
    def list_documents(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List documents in R2
        
        Args:
            prefix: Filter by prefix (e.g., 'service_manual/hp/')
            max_keys: Maximum number of results
            
        Returns:
            List of document info dicts
        """
        if not self.is_configured():
            self.logger.error("Cannot list: R2 not configured")
            return []
        
        try:
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                params['Prefix'] = prefix
            
            response = self.r2_client.list_objects_v2(**params)
            
            documents = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    documents.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })
            
            self.logger.info(f"Found {len(documents)} documents")
            return documents
            
        except ClientError as e:
            self.logger.error(f"List failed: {e}")
            return []
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dict with statistics
        """
        if not self.is_configured():
            return {
                'configured': False,
                'total_documents': 0,
                'total_size_bytes': 0
            }
        
        try:
            # List all objects
            documents = self.list_documents(max_keys=10000)
            
            total_size = sum(doc['size'] for doc in documents)
            
            # Group by document type
            by_type = {}
            for doc in documents:
                doc_type = doc['key'].split('/')[0]
                if doc_type not in by_type:
                    by_type[doc_type] = {'count': 0, 'size': 0}
                by_type[doc_type]['count'] += 1
                by_type[doc_type]['size'] += doc['size']
            
            return {
                'configured': True,
                'total_documents': len(documents),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'by_type': by_type,
                'bucket': self.bucket_name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {
                'configured': True,
                'error': str(e)
            }


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    
    # Initialize storage processor
    storage = StorageProcessor()
    
    if storage.is_configured():
        print("✅ R2 Storage configured")
        
        # Get statistics
        stats = storage.get_storage_statistics()
        print(f"\n📊 Storage Statistics:")
        print(f"   Total Documents: {stats.get('total_documents', 0)}")
        print(f"   Total Size: {stats.get('total_size_mb', 0)} MB")
    else:
        print("⚠️  R2 Storage not configured")
        print("\nSet environment variables:")
        print("  R2_ENDPOINT_URL")
        print("  R2_ACCESS_KEY_ID")
        print("  R2_SECRET_ACCESS_KEY")
        print("  R2_BUCKET_NAME (optional)")
