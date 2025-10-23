"""
Image Storage Processor V2 - WITH HASH DEDUPLICATION

Handles EXTRACTED IMAGE storage on Cloudflare R2 with:
- MD5 hash-based deduplication (no duplicate uploads!)
- Flat storage structure: {hash}.{extension}
- Database tracking in krai_content.images
- Automatic metadata extraction
- Integration with Supabase

Storage Structure:
    OLD: documents/{doc_id}/images/page_0001_diagram_img.png
    NEW: a1b2c3d4e5f6.png (just the hash!)

Deduplication Flow:
    1. Calculate MD5 hash of image
    2. Check if hash exists in DB
    3. If exists: Return existing URL (skip upload)
    4. If new: Upload to R2 + Insert to DB
"""

import os
from pathlib import Path as FilePath
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda *args, **kwargs: None  # Fallback accepts any args

# Load .env
env_path = FilePath(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import hashlib
import mimetypes

from .logger import get_logger


class ImageStorageProcessor:
    """
    Image Storage with Hash-based Deduplication
    
    Features:
    - MD5 hash calculation
    - Automatic deduplication
    - R2 storage (Cloudflare)
    - Database tracking (krai_content.images)
    - Flat structure (no folders)
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize image storage processor
        
        Args:
            supabase_client: Supabase client for DB tracking
        """
        self.logger = get_logger()
        self.supabase = supabase_client
        
        # R2 Configuration
        self.access_key = os.getenv('R2_ACCESS_KEY_ID')
        self.secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
        self.endpoint_url = os.getenv('R2_ENDPOINT_URL')
        self.bucket_name = os.getenv('R2_BUCKET_NAME_DOCUMENTS')
        self.public_url = os.getenv('R2_PUBLIC_URL_DOCUMENTS')
        
        # Initialize R2 client
        self.r2_client = None
        if all([self.access_key, self.secret_key, self.endpoint_url, self.bucket_name]):
            try:
                self.r2_client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    config=Config(signature_version='s3v4'),
                    region_name='auto'
                )
                self.logger.info("R2 client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize R2 client: {e}")
        else:
            self.logger.warning("R2 credentials incomplete - storage disabled")
    
    def is_configured(self) -> bool:
        """Check if R2 and Supabase are configured"""
        return self.r2_client is not None and self.supabase is not None
    
    def calculate_image_hash(self, image_path: Path) -> str:
        """
        Calculate MD5 hash of image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            MD5 hash as hex string
        """
        md5_hash = hashlib.md5()
        
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    def check_image_exists(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if image with this hash already exists in DB
        
        Args:
            file_hash: MD5 hash of image
            
        Returns:
            Existing image record or None
        """
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('vw_images') \
                .select('*') \
                .eq('file_hash', file_hash) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error checking image existence: {e}")
            return None
    
    def upload_image(
        self,
        image_path: Path,
        document_id: UUID,
        page_number: int,
        image_type: str = "diagram",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload single image with deduplication
        
        Args:
            image_path: Path to image file
            document_id: Document UUID
            page_number: Page number
            image_type: Type of image
            metadata: Additional metadata
            
        Returns:
            Result dict with storage_url
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Storage not configured',
                'storage_url': None,
                'deduplicated': False
            }
        
        try:
            # 1. Calculate hash
            file_hash = self.calculate_image_hash(image_path)
            
            # 2. Check if already exists
            existing = self.check_image_exists(file_hash)
            
            if existing:
                # Image already exists - just create new mapping
                self.logger.debug(f"Image deduplicated: {file_hash[:8]}... (already exists)")
                
                # Create new document_image mapping if needed
                return {
                    'success': True,
                    'storage_url': existing['storage_url'],
                    'storage_path': existing['storage_path'],
                    'file_hash': file_hash,
                    'deduplicated': True,
                    'existing_id': existing['id']
                }
            
            # 3. New image - upload to R2
            extension = image_path.suffix.lstrip('.')
            storage_path = f"{file_hash}.{extension}"
            
            # Upload to R2
            with open(image_path, 'rb') as f:
                self.r2_client.upload_fileobj(
                    f,
                    self.bucket_name,
                    storage_path,
                    ExtraArgs={
                        'Metadata': {
                            'document-id': str(document_id),
                            'page-number': str(page_number),
                            'image-type': image_type,
                            'file-hash': file_hash,
                            'upload-timestamp': datetime.utcnow().isoformat()
                        },
                        'ContentType': mimetypes.guess_type(image_path)[0] or 'image/png'
                    }
                )
            
            # Generate public URL
            if self.public_url:
                storage_url = f"{self.public_url}/{storage_path}"
            else:
                storage_url = f"{self.endpoint_url}/{self.bucket_name}/{storage_path}"
            
            # 4. Insert to database
            image_record = {
                'document_id': str(document_id),
                'filename': storage_path,
                'storage_path': storage_path,
                'storage_url': storage_url,
                'file_hash': file_hash,
                'file_size': image_path.stat().st_size,
                'image_format': extension.upper(),
                'page_number': page_number,
                'image_type': image_type,
            }
            
            # Add metadata if provided
            if metadata:
                if 'width' in metadata:
                    image_record['width_px'] = metadata['width']
                if 'height' in metadata:
                    image_record['height_px'] = metadata['height']
                if 'ai_description' in metadata:
                    image_record['ai_description'] = metadata['ai_description']
                if 'ai_confidence' in metadata:
                    image_record['ai_confidence'] = metadata['ai_confidence']
                if 'contains_text' in metadata:
                    image_record['contains_text'] = metadata['contains_text']
                if 'ocr_text' in metadata:
                    image_record['ocr_text'] = metadata['ocr_text']
                if 'ocr_confidence' in metadata:
                    image_record['ocr_confidence'] = metadata['ocr_confidence']
            
            db_result = self.supabase.table('vw_images').insert(image_record).execute()
            
            self.logger.debug(f"Uploaded new image: {file_hash[:8]}... -> {storage_path}")
            
            return {
                'success': True,
                'storage_url': storage_url,
                'storage_path': storage_path,
                'file_hash': file_hash,
                'deduplicated': False,
                'db_id': db_result.data[0]['id'] if db_result.data else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            return {
                'success': False,
                'error': str(e),
                'storage_url': None,
                'deduplicated': False
            }
    
    def upload_images(
        self,
        document_id: UUID,
        images: List[Dict[str, Any]],
        document_type: str = "service_manual"
    ) -> Dict[str, Any]:
        """
        Upload multiple images with deduplication
        
        Args:
            document_id: Document UUID
            images: List of dicts with 'path', 'page_num', 'type', etc.
            document_type: Type of document
            
        Returns:
            Dict with upload results
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Storage not configured',
                'uploaded_count': 0,
                'deduplicated_count': 0,
                'urls': []
            }
        
        uploaded_count = 0
        deduplicated_count = 0
        failed_count = 0
        urls = []
        
        self.logger.info(f"Uploading {len(images)} images to R2 (with deduplication)...")
        
        for idx, image_info in enumerate(images):
            image_path = Path(image_info.get('path'))
            
            if not image_path.exists():
                failed_count += 1
                continue
            
            # Upload with deduplication
            result = self.upload_image(
                image_path=image_path,
                document_id=document_id,
                page_number=image_info.get('page_num', 0),
                image_type=image_info.get('type', 'diagram'),
                metadata=image_info.get('metadata')
            )
            
            if result['success']:
                if result['deduplicated']:
                    deduplicated_count += 1
                else:
                    uploaded_count += 1
                
                urls.append({
                    'page_num': image_info.get('page_num'),
                    'type': image_info.get('type'),
                    'url': result['storage_url'],
                    'hash': result['file_hash'],
                    'deduplicated': result['deduplicated']
                })
            else:
                failed_count += 1
            
            # Progress logging every 500 images
            if (idx + 1) % 500 == 0:
                self.logger.info(
                    f"Progress: {idx + 1}/{len(images)} "
                    f"(Uploaded: {uploaded_count}, Deduplicated: {deduplicated_count})"
                )
        
        total_processed = uploaded_count + deduplicated_count
        
        self.logger.success(
            f"Processed {total_processed}/{len(images)} images "
            f"(New: {uploaded_count}, Deduplicated: {deduplicated_count}, Failed: {failed_count})"
        )
        
        return {
            'success': failed_count == 0,
            'uploaded_count': uploaded_count,
            'deduplicated_count': deduplicated_count,
            'failed_count': failed_count,
            'total_processed': total_processed,
            'urls': urls
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics from DB
        
        Returns:
            Dict with statistics
        """
        if not self.supabase:
            return {}
        
        try:
            # Total images
            total_result = self.supabase.table('vw_images') \
                .select('id', count='exact') \
                .execute()
            
            total_images = total_result.count if hasattr(total_result, 'count') else 0
            
            # Unique hashes (deduplicated images)
            unique_result = self.supabase.rpc('count_unique_image_hashes').execute()
            unique_hashes = unique_result.data if unique_result.data else 0
            
            # Total size
            size_result = self.supabase.rpc('sum_image_sizes').execute()
            total_size = size_result.data if size_result.data else 0
            
            return {
                'total_images': total_images,
                'unique_images': unique_hashes,
                'deduplication_rate': round((1 - unique_hashes / max(total_images, 1)) * 100, 2),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            }
            
        except Exception as e:
            self.logger.debug(f"Error getting storage stats: {e}")
            return {}
    
    def cleanup_orphaned_images(self) -> Dict[str, Any]:
        """
        Cleanup images not referenced by any document
        
        Returns:
            Cleanup results
        """
        # TODO: Implement cleanup logic
        pass


# Convenience function
def upload_images_to_r2(
    document_id: UUID,
    images: List[Dict[str, Any]],
    supabase_client=None
) -> Dict[str, Any]:
    """
    Convenience function to upload images
    
    Args:
        document_id: Document UUID
        images: List of image dicts
        supabase_client: Supabase client
        
    Returns:
        Upload results
    """
    processor = ImageStorageProcessor(supabase_client=supabase_client)
    return processor.upload_images(document_id, images)
