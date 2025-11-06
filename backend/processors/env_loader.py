"""
Environment Loader - Loads all .env.* files

Loads configuration from modular .env files:
- .env.database - Database configuration
- .env.storage - Object storage (R2)
- .env.pipeline - Processing pipeline settings
- .env.ai - AI service configuration
- .env.external - External APIs and tunnels
- .env - Main config (fallback, loads all if modular files don't exist)
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_all_env_files(project_root: Path = None):
    """
    Load all .env.* files in order
    
    Args:
        project_root: Project root directory (auto-detected if None)
    """
    if project_root is None:
        # Auto-detect project root (where .env files are)
        current = Path(__file__).parent
        while current.parent != current:
            if (current / '.env').exists() or (current / '.env.database').exists():
                project_root = current
                break
            current = current.parent
        
        if project_root is None:
            project_root = Path.cwd()
    
    # Order matters: later files can override earlier ones
    env_files = [
        '.env.database',   # Database first (core dependency)
        '.env.storage',    # Storage configuration
        '.env.ai',         # AI services
        '.env.pipeline',   # Pipeline settings
        '.env.external',   # External APIs
        '.env',            # Main config (fallback/overrides)
    ]
    
    loaded_files = []
    
    for env_file in env_files:
        env_path = project_root / env_file
        if env_path.exists():
            load_dotenv(env_path, override=True)
            loaded_files.append(env_file)
    
    return loaded_files


def get_env_summary() -> dict:
    """Get summary of loaded environment variables"""
    return {
        'database': {
            'supabase_url': os.getenv('SUPABASE_URL', 'Not set'),
            'has_service_key': bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY')),
        },
        'storage': {
            'configured': bool(os.getenv('OBJECT_STORAGE_ACCESS_KEY') or os.getenv('R2_ACCESS_KEY_ID')),
            'type': os.getenv('OBJECT_STORAGE_TYPE', 'r2'),
            'endpoint': os.getenv('OBJECT_STORAGE_ENDPOINT') or os.getenv('R2_ENDPOINT_URL', 'Not set'),
            'upload_images': os.getenv('UPLOAD_IMAGES_TO_STORAGE') or os.getenv('UPLOAD_IMAGES_TO_R2', 'false'),
            'upload_documents': os.getenv('UPLOAD_DOCUMENTS_TO_STORAGE') or os.getenv('UPLOAD_DOCUMENTS_TO_R2', 'false'),
        },
        'ai': {
            'ollama_url': os.getenv('OLLAMA_URL', 'Not set'),
            'embedding_model': os.getenv('OLLAMA_MODEL_EMBEDDING', 'Not set'),
            'vision_model': os.getenv('OLLAMA_MODEL_VISION', 'Not set'),
            'visual_embedding_model': os.getenv('AI_VISUAL_EMBEDDING_MODEL', 'Not set'),
            'visual_embeddings_enabled': os.getenv('ENABLE_VISUAL_EMBEDDINGS', 'false'),
            'table_extraction_enabled': os.getenv('ENABLE_TABLE_EXTRACTION', 'false'),
            'embeddings_v2_enabled': os.getenv('ENABLE_EMBEDDINGS_V2', 'false'),
        },
        'context_extraction': {
            'enabled': os.getenv('ENABLE_CONTEXT_EXTRACTION', 'true'),
            'mode': os.getenv('CONTEXT_EXTRACTION_MODE', 'enhanced'),
            'image_context': os.getenv('ENABLE_IMAGE_CONTEXT', 'true'),
            'video_context': os.getenv('ENABLE_VIDEO_CONTEXT', 'true'),
            'link_context': os.getenv('ENABLE_LINK_CONTEXT', 'true'),
            'context_embeddings': os.getenv('ENABLE_CONTEXT_EMBEDDINGS', 'true'),
            'error_code_extraction': os.getenv('ENABLE_ERROR_CODE_EXTRACTION', 'true'),
            'product_extraction': os.getenv('ENABLE_PRODUCT_EXTRACTION', 'true'),
        },
        'pipeline': {
            'products': os.getenv('ENABLE_PRODUCT_EXTRACTION', 'true'),
            'parts': os.getenv('ENABLE_PARTS_EXTRACTION', 'true'),
            'error_codes': os.getenv('ENABLE_ERROR_CODE_EXTRACTION', 'true'),
            'images': os.getenv('ENABLE_IMAGE_EXTRACTION', 'true'),
            'embeddings': os.getenv('ENABLE_EMBEDDINGS', 'true'),
        },
        'phase6': {
            'hierarchical_chunking': os.getenv('ENABLE_HIERARCHICAL_CHUNKING', 'false'),
            'detect_error_code_sections': os.getenv('DETECT_ERROR_CODE_SECTIONS', 'true'),
            'link_chunks': os.getenv('LINK_CHUNKS', 'true'),
            'multimodal_search': os.getenv('ENABLE_MULTIMODAL_SEARCH', 'true'),
            'two_stage_search': os.getenv('ENABLE_TWO_STAGE_SEARCH', 'true'),
            'svg_extraction': os.getenv('ENABLE_SVG_EXTRACTION', 'false'),
            'context_aware_search': os.getenv('ENABLE_CONTEXT_AWARE_SEARCH', 'true'),
            'semantic_reranking': os.getenv('ENABLE_SEMANTIC_RERANKING', 'true'),
        },
        'external': {
            'youtube_api': bool(os.getenv('YOUTUBE_API_KEY')),
        }
    }


# Auto-load on import
load_all_env_files()
