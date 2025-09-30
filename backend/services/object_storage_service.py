"""
Object Storage Service for KR-AI-Engine
Cloudflare R2 integration for image storage only
"""

import asyncio
import logging
import hashlib
import mimetypes
from typing import Dict, List, Optional, Any, Union, BinaryIO
from datetime import datetime, timezone
import os
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from botocore.client import Config
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception
    Config = None
    BOTO3_AVAILABLE = False

class ObjectStorageService:
    """
    Object Storage service for Cloudflare R2 integration
    
    Handles image storage for KR-AI-Engine:
    - krai-document-images: Images extracted from documents
    - krai-error-images: Defect detection images
    - krai-parts-images: Parts catalog images
    
    IMPORTANT: Documents are NOT stored in object storage (Database only!)
    """
    
    def __init__(self, 
                 r2_access_key_id: str,
                 r2_secret_access_key: str,
                 r2_endpoint_url: str,
                 r2_public_url_documents: str,
                 r2_public_url_error: str,
                 r2_public_url_parts: str):
        self.access_key_id = r2_access_key_id
        self.secret_access_key = r2_secret_access_key
        self.endpoint_url = r2_endpoint_url
        self.public_urls = {
            'documents': r2_public_url_documents,
            'error': r2_public_url_error,
            'parts': r2_public_url_parts
        }
        self.client = None
        self.logger = logging.getLogger("krai.storage")
        self._setup_logging()
        
        # Bucket configurations
        self.buckets = {
            'document_images': 'krai-documents-images',
            'error_images': 'krai-error-images', 
            'parts_images': 'krai-parts-images'
        }
    
    def _setup_logging(self):
        """Setup logging for storage service"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - Storage - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def connect(self):
        """Connect to Cloudflare R2"""
        try:
            if not BOTO3_AVAILABLE:
                self.logger.warning("Boto3 not available. Running in mock mode.")
                return
            
            # Create S3-compatible client for R2
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='auto',
                config=Config(signature_version='s3v4')
            )
            
            self.logger.info("Connected to Cloudflare R2")
            
            # Ensure buckets exist
            await self._ensure_buckets_exist()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to R2: {e}")
            raise
    
    async def _ensure_buckets_exist(self):
        """Ensure all required buckets exist"""
        if self.client is None:
            self.logger.info("Skipping bucket creation (mock mode)")
            return
            
        for bucket_type, bucket_name in self.buckets.items():
            try:
                await self._create_bucket_if_not_exists(bucket_name)
                self.logger.info(f"Bucket {bucket_name} ready")
            except Exception as e:
                self.logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
                raise
    
    async def _create_bucket_if_not_exists(self, bucket_name: str):
        """Create bucket if it doesn't exist"""
        try:
            if self.client is None:
                self.logger.info(f"Bucket {bucket_name} creation skipped (mock mode)")
                return
                
            self.client.head_bucket(Bucket=bucket_name)
            self.logger.debug(f"Bucket {bucket_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                self.client.create_bucket(Bucket=bucket_name)
                self.logger.info(f"Created bucket {bucket_name}")
            else:
                raise
    
    def _generate_file_hash(self, content: bytes) -> str:
        """Generate SHA256 hash for file content"""
        return hashlib.sha256(content).hexdigest()
    
    def _generate_storage_path(self, filename: str, bucket_type: str = 'document_images') -> str:
        """Generate storage path - just the filename (hash-based)"""
        # No folder structure - just use the hash-based filename directly
        return filename
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for file"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    async def upload_image(self, 
                          content: bytes, 
                          filename: str, 
                          bucket_type: str = 'document_images',
                          metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload image to R2 storage
        
        Args:
            content: Image file content as bytes
            filename: Original filename
            bucket_type: Type of bucket (document_images, error_images, parts_images)
            metadata: Additional metadata
            
        Returns:
            Dict with storage information
        """
        try:
            if self.client is None:
                # Mock mode for testing
                file_hash = hashlib.sha256(content).hexdigest()
                # No folder structure - just use the hash-based filename directly
                storage_path = filename
                
                # Generate public URL based on bucket type
                if bucket_type == 'document_images':
                    public_url = f"{self.public_urls['documents']}/{storage_path}"
                elif bucket_type == 'error_images':
                    public_url = f"{self.public_urls['error']}/{storage_path}"
                elif bucket_type == 'parts_images':
                    public_url = f"{self.public_urls['parts']}/{storage_path}"
                else:
                    public_url = f"{self.public_urls['documents']}/{storage_path}"
                
                result = {
                    'success': True,
                    'bucket': self.buckets.get(bucket_type, 'krai-documents'),
                    'key': storage_path,
                    'storage_path': storage_path,
                    'public_url': public_url,
                    'url': public_url,
                    'file_hash': file_hash,
                    'size': len(content),
                    'content_type': self._get_content_type(filename),
                    'metadata': metadata or {}
                }
                
                self.logger.info(f"Uploaded image {filename} to {bucket_type}/{storage_path} (mock)")
                return result
            
            if bucket_type not in self.buckets:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            bucket_name = self.buckets[bucket_type]
            
            # Generate file hash for deduplication
            file_hash = self._generate_file_hash(content)
            
            # Check for duplicate file by hash
            duplicate = await self.check_duplicate(file_hash, bucket_type)
            if duplicate:
                self.logger.info(f"Duplicate file found with hash {file_hash[:16]}...: {duplicate['key']}")
                return {
                    'success': True,
                    'file_hash': file_hash,
                    'storage_path': duplicate['key'],
                    'storage_url': duplicate['url'],
                    'bucket': duplicate['bucket'],
                    'is_duplicate': True
                }
            
            # Generate storage path
            storage_path = self._generate_storage_path(filename, bucket_type)
            
            # Prepare metadata (all values must be strings for S3)
            file_metadata = {
                'original_filename': filename,
                'file_hash': file_hash,
                'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                'content_type': self._get_content_type(filename)
            }
            
            if metadata:
                # Convert all metadata values to strings
                for key, value in metadata.items():
                    if isinstance(value, (int, float, bool)):
                        file_metadata[key] = str(value)
                    elif isinstance(value, str):
                        file_metadata[key] = value
                    else:
                        file_metadata[key] = str(value)
            
            # Upload to R2
            self.client.put_object(
                Bucket=bucket_name,
                Key=storage_path,
                Body=content,
                ContentType=self._get_content_type(filename),
                Metadata=file_metadata
            )
            
            # Generate public URL based on bucket type
            if bucket_type == 'document_images':
                public_url = f"{self.public_urls['documents']}/{storage_path}"
            elif bucket_type == 'error_images':
                public_url = f"{self.public_urls['error']}/{storage_path}"
            elif bucket_type == 'parts_images':
                public_url = f"{self.public_urls['parts']}/{storage_path}"
            else:
                public_url = f"{self.public_urls['documents']}/{storage_path}"
            
            result = {
                'success': True,
                'bucket': bucket_name,
                'key': storage_path,
                'storage_path': storage_path,
                'public_url': public_url,
                'url': public_url,
                'storage_url': public_url,
                'file_hash': file_hash,
                'is_duplicate': False,
                'size': len(content),
                'content_type': self._get_content_type(filename),
                'metadata': file_metadata
            }
            
            self.logger.info(f"Uploaded image {filename} to {bucket_name}/{storage_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to upload image {filename}: {e}")
            raise
    
    async def download_image(self, bucket_type: str, key: str) -> bytes:
        """
        Download image from R2 storage
        
        Args:
            bucket_type: Type of bucket
            key: Storage key/path
            
        Returns:
            Image content as bytes
        """
        try:
            if self.client is None:
                self.logger.warning("Object storage client not available. Cannot download in mock mode.")
                return b""
            
            if bucket_type not in self.buckets:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            bucket_name = self.buckets[bucket_type]
            
            response = self.client.get_object(Bucket=bucket_name, Key=key)
            content = response['Body'].read()
            
            self.logger.info(f"Downloaded image from {bucket_name}/{key}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to download image {bucket_type}/{key}: {e}")
            raise
    
    async def delete_image(self, bucket_type: str, key: str) -> bool:
        """
        Delete image from R2 storage
        
        Args:
            bucket_type: Type of bucket
            key: Storage key/path
            
        Returns:
            True if deleted successfully
        """
        try:
            if self.client is None:
                self.logger.warning("Object storage client not available. Cannot delete in mock mode.")
                return True  # Assume success in mock mode
            
            if bucket_type not in self.buckets:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            bucket_name = self.buckets[bucket_type]
            
            self.client.delete_object(Bucket=bucket_name, Key=key)
            
            self.logger.info(f"Deleted image from {bucket_name}/{key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete image {bucket_type}/{key}: {e}")
            raise
    
    async def get_image_metadata(self, bucket_type: str, key: str) -> Dict[str, Any]:
        """
        Get image metadata from R2 storage
        
        Args:
            bucket_type: Type of bucket
            key: Storage key/path
            
        Returns:
            Image metadata
        """
        try:
            if self.client is None:
                self.logger.warning("Object storage client not available. Cannot get metadata in mock mode.")
                return {}
            
            if bucket_type not in self.buckets:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            bucket_name = self.buckets[bucket_type]
            
            response = self.client.head_object(Bucket=bucket_name, Key=key)
            
            metadata = {
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {})
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {bucket_type}/{key}: {e}")
            raise
    
    async def list_images(self, bucket_type: str, prefix: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List images in bucket
        
        Args:
            bucket_type: Type of bucket
            prefix: Optional prefix filter
            limit: Maximum number of results
            
        Returns:
            List of image information
        """
        try:
            if self.client is None:
                self.logger.warning("Object storage client not available. Cannot list images in mock mode.")
                return []
            
            if bucket_type not in self.buckets:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            bucket_name = self.buckets[bucket_type]
            
            kwargs = {
                'Bucket': bucket_name,
                'MaxKeys': limit
            }
            
            if prefix:
                kwargs['Prefix'] = prefix
            
            response = self.client.list_objects_v2(**kwargs)
            
            images = []
            for obj in response.get('Contents', []):
                images.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': f"{self.public_url}/{bucket_name}/{obj['Key']}"
                })
            
            self.logger.info(f"Listed {len(images)} images from {bucket_name}")
            return images
            
        except Exception as e:
            self.logger.error(f"Failed to list images from {bucket_type}: {e}")
            raise
    
    async def check_duplicate(self, file_hash: str, bucket_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Check for duplicate file by hash
        
        Args:
            file_hash: SHA256 hash of file content
            bucket_type: Optional bucket type to search
            
        Returns:
            Duplicate file info if found, None otherwise
        """
        try:
            if self.client is None:
                self.logger.warning("Object storage client not available. Cannot check duplicates in mock mode.")
                return None
            
            buckets_to_search = [bucket_type] if bucket_type else list(self.buckets.values())
            
            for bucket_name in buckets_to_search:
                try:
                    # List all objects and check metadata for hash
                    response = self.client.list_objects_v2(Bucket=bucket_name)
                    
                    for obj in response.get('Contents', []):
                        # Get object metadata
                        head_response = self.client.head_object(Bucket=bucket_name, Key=obj['Key'])
                        metadata = head_response.get('Metadata', {})
                        
                        if metadata.get('file_hash') == file_hash:
                            return {
                                'bucket': bucket_name,
                                'key': obj['Key'],
                                'url': f"{self.public_url}/{bucket_name}/{obj['Key']}",
                                'size': obj['Size'],
                                'last_modified': obj['LastModified']
                            }
                            
                except ClientError:
                    # Bucket might not exist or be accessible
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to check for duplicate {file_hash}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform storage health check"""
        try:
            if self.client is None:
                return {
                    "status": "mock_mode",
                    "response_time_ms": 0,
                    "buckets": list(self.buckets.values()),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            start_time = datetime.now(timezone.utc)
            
            # Test basic operation
            self.client.head_bucket(Bucket=self.buckets['document_images'])
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000,
                "buckets": list(self.buckets.values()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
