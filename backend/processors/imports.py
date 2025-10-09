"""Centralized Import Module

Handles all imports for processors to avoid path issues.
Use this instead of direct imports in processor files.

Uses lazy imports - functions are imported only when called.
"""

from pathlib import Path
import sys
import os

# Setup paths once
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Lazy import functions - import only when called
def get_supabase_client():
    """Create and return Supabase client"""
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    
    # Find project root (where .env is located)
    # Try multiple locations to be robust
    project_root = backend_dir.parent  # Default: backend/../
    env_path = project_root / '.env'
    
    # If .env not found, search upwards
    if not env_path.exists():
        current = Path.cwd()
        for _ in range(5):  # Search up to 5 levels
            test_path = current / '.env'
            if test_path.exists():
                env_path = test_path
                project_root = current
                break
            current = current.parent
    
    # Load environment
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        # Try loading from current directory as fallback
        load_dotenv(override=True)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            f"SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env\n"
            f"Searched for .env in: {env_path}\n"
            f"Current directory: {Path.cwd()}\n"
            f"Project root: {project_root}"
        )
    
    return create_client(supabase_url, supabase_key)

def get_logger():
    """Lazy import of get_logger"""
    from processors.logger import get_logger as _get_logger
    return _get_logger()

def extract_parts(text):
    """Lazy import of extract_parts"""
    from utils.parts_extractor import extract_parts as _extract
    return _extract(text)

def extract_parts_with_context(text, manufacturer_key=None, max_parts=20):
    """Lazy import of extract_parts_with_context"""
    from utils.parts_extractor import extract_parts_with_context as _extract
    return _extract(text, manufacturer_key, max_parts)

def detect_series(model_number, manufacturer_name):
    """Lazy import of detect_series"""
    from utils.series_detector import detect_series as _detect
    return _detect(model_number, manufacturer_name)

__all__ = [
    'get_supabase_client',
    'get_logger',
    'extract_parts',
    'extract_parts_with_context',
    'detect_series'
]
