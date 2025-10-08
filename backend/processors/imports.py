"""Centralized Import Module

Handles all imports for processors to avoid path issues.
Use this instead of direct imports in processor files.
"""

from pathlib import Path
import sys

# Setup paths once
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import and re-export everything processors need
from database.supabase_client import get_supabase_client
from processors.logger import get_logger
from utils.parts_extractor import extract_parts, extract_parts_with_context
from utils.series_detector import detect_series

__all__ = [
    'get_supabase_client',
    'get_logger',
    'extract_parts',
    'extract_parts_with_context',
    'detect_series'
]
