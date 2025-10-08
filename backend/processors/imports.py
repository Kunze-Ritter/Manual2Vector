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
    
    # Load environment
    env_path = backend_dir.parent / '.env'
    load_dotenv(env_path)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    
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
