"""
KRAI Document Processors V2

Clean, modular rewrite with proper validation and logging.
Based on lessons learned from V1.

Modules:
- document_processor: Main orchestration
- text_extractor: PDF text extraction
- product_extractor: Model number extraction with validation
- error_code_extractor: Error code extraction with strict patterns
- chunker: Smart text chunking with overlap
- validator: Data validation before DB insert
- logger: Beautiful logging setup
"""

from .logger import get_logger

__version__ = "0.50.0"
__all__ = [
    "get_logger",
]
