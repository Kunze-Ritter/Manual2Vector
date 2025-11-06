"""
Object Storage Factory

Factory pattern for creating object storage services based on configuration.
Supports multiple S3-compatible backends: MinIO, AWS S3, Cloudflare R2, Wasabi, Backblaze B2.
"""

import os
import logging
from typing import Optional

from backend.services.object_storage_service import ObjectStorageService


logger = logging.getLogger("krai.storage.factory")


def create_storage_service(
    storage_type: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    public_url_documents: Optional[str] = None,
    public_url_error: Optional[str] = None,
    public_url_parts: Optional[str] = None,
    use_ssl: Optional[bool] = None,
    region: Optional[str] = None,
    bucket_documents: Optional[str] = None,
    bucket_images: Optional[str] = None,
    bucket_videos: Optional[str] = None,
    bucket_error: Optional[str] = None,
    bucket_parts: Optional[str] = None,
    bucket_temp: Optional[str] = None
) -> ObjectStorageService:
    """
    Create an object storage service based on the specified type.
    
    Args:
        storage_type: Type of storage backend ('s3', 'minio', 'r2', 'wasabi', etc.)
                      If None, reads from OBJECT_STORAGE_TYPE environment variable (default: 's3')
        endpoint_url: Storage endpoint URL (overrides environment)
        access_key: Access key (overrides environment)
        secret_key: Secret key (overrides environment)
        public_url_documents: Public URL for documents bucket (overrides environment)
        public_url_error: Public URL for error bucket (overrides environment)
        public_url_parts: Public URL for parts bucket (overrides environment)
        use_ssl: Use SSL connection (overrides environment)
        region: Storage region (overrides environment)
        bucket_documents: Documents bucket name (overrides environment)
        bucket_images: Images bucket name (overrides environment)
        bucket_videos: Videos bucket name (overrides environment)
        bucket_error: Error bucket name (overrides environment)
        bucket_parts: Parts bucket name (overrides environment)
        bucket_temp: Temporary bucket name (overrides environment)
    
    Returns:
        ObjectStorageService: Configured storage service instance
    
    Raises:
        ValueError: If required configuration is missing
    
    Environment Variables:
        OBJECT_STORAGE_TYPE: Storage backend type (default: 's3')
        OBJECT_STORAGE_ENDPOINT: Storage endpoint URL
        OBJECT_STORAGE_ACCESS_KEY: Storage access key
        OBJECT_STORAGE_SECRET_KEY: Storage secret key
        OBJECT_STORAGE_PUBLIC_URL_DOCUMENTS: Public URL for documents
        OBJECT_STORAGE_PUBLIC_URL_ERROR: Public URL for error images
        OBJECT_STORAGE_PUBLIC_URL_PARTS: Public URL for parts images
        OBJECT_STORAGE_USE_SSL: Use SSL connection (default: 'true')
        OBJECT_STORAGE_REGION: Storage region (default: 'auto')
        OBJECT_STORAGE_BUCKET_DOCUMENTS: Documents bucket name
        OBJECT_STORAGE_BUCKET_ERROR: Error bucket name
        OBJECT_STORAGE_BUCKET_PARTS: Parts bucket name
        
        # Deprecated variables (still supported with warnings)
        R2_ENDPOINT_URL: Legacy endpoint URL
        R2_ACCESS_KEY_ID: Legacy access key
        R2_SECRET_ACCESS_KEY: Legacy secret key
        R2_PUBLIC_URL_*: Legacy public URLs
        R2_BUCKET_NAME_*: Legacy bucket names
    """
    
    # Determine storage type from parameter or environment
    if storage_type is None:
        storage_type = os.getenv("OBJECT_STORAGE_TYPE", "s3").lower()
    else:
        storage_type = storage_type.lower()
    
    logger.info(f"Creating object storage service: {storage_type}")
    
    # Helper function to get env var with fallback and deprecation warning
    def get_env_var(new_var: str, old_var: str, default: str = None) -> str:
        value = (os.getenv(new_var) or 
                os.getenv(old_var) or 
                default)
        if not os.getenv(new_var) and os.getenv(old_var):
            _log_deprecation_warning(old_var, new_var)
        return value
    
    # Load configuration from parameters or environment
    endpoint = (endpoint_url or 
                get_env_var('OBJECT_STORAGE_ENDPOINT', 'R2_ENDPOINT_URL'))
    
    access_key = (access_key or 
                  get_env_var('OBJECT_STORAGE_ACCESS_KEY', 'R2_ACCESS_KEY_ID'))
    
    secret_key = (secret_key or 
                  get_env_var('OBJECT_STORAGE_SECRET_KEY', 'R2_SECRET_ACCESS_KEY'))
    
    public_url_documents = (public_url_documents or 
                            get_env_var('OBJECT_STORAGE_PUBLIC_URL_DOCUMENTS', 'R2_PUBLIC_URL_DOCUMENTS', ''))
    
    public_url_error = (public_url_error or 
                        get_env_var('OBJECT_STORAGE_PUBLIC_URL_ERROR', 'R2_PUBLIC_URL_ERROR', ''))
    
    public_url_parts = (public_url_parts or 
                        get_env_var('OBJECT_STORAGE_PUBLIC_URL_PARTS', 'R2_PUBLIC_URL_PARTS', ''))
    
    use_ssl_val = (use_ssl if use_ssl is not None else 
                   get_env_var('OBJECT_STORAGE_USE_SSL', 'R2_USE_SSL', 'true'))
    use_ssl = str(use_ssl_val).lower() == 'true'
    
    region = (region or 
              get_env_var('OBJECT_STORAGE_REGION', 'R2_REGION', 'auto'))
    
    # Extract bucket names (with fallback to R2 variables)
    bucket_documents = (bucket_documents or 
                        get_env_var('OBJECT_STORAGE_BUCKET_DOCUMENTS', 'R2_BUCKET_NAME_DOCUMENTS', 'documents'))
    bucket_error = (bucket_error or 
                    get_env_var('OBJECT_STORAGE_BUCKET_ERROR', 'R2_BUCKET_NAME_ERROR', 'error'))
    bucket_parts = (bucket_parts or 
                    get_env_var('OBJECT_STORAGE_BUCKET_PARTS', 'R2_BUCKET_NAME_PARTS', 'parts'))
    
    # Validate required configuration
    if not endpoint:
        raise ValueError("OBJECT_STORAGE_ENDPOINT is required for object storage")
    if not access_key:
        raise ValueError("OBJECT_STORAGE_ACCESS_KEY is required for object storage")
    if not secret_key:
        raise ValueError("OBJECT_STORAGE_SECRET_KEY is required for object storage")
    
    # Log configuration summary
    logger.info(f"Storage endpoint: {endpoint}")
    logger.info(f"SSL enabled: {use_ssl}")
    logger.info(f"Region: {region}")
    logger.info(f"Buckets: documents, error, parts")
    
    # Create service with bucket name parameters
    return ObjectStorageService(
        access_key_id=access_key,
        secret_access_key=secret_key,
        endpoint_url=endpoint,
        public_url_documents=public_url_documents,
        public_url_error=public_url_error,
        public_url_parts=public_url_parts,
        use_ssl=use_ssl,
        region=region,
        bucket_documents=bucket_documents,
        bucket_error=bucket_error,
        bucket_parts=bucket_parts
    )  

    logger.info(f"Created {storage_type} object storage service at {endpoint}")


def _log_deprecation_warning(old_var: str, new_var: str):
    """Log deprecation warning for old environment variables."""
    logger.warning(f"Environment variable {old_var} is deprecated. Use {new_var} instead.")


class StorageFactory:
    """
    Factory class for creating object storage services.
    
    This class provides a static interface to the create_storage_service function
    for compatibility with existing code that expects a class-based factory.
    """
    
    @staticmethod
    def create_storage_service(**kwargs) -> ObjectStorageService:
        """
        Create an object storage service.
        
        This is a static wrapper around the create_storage_service function.
        """
        return create_storage_service(**kwargs)
