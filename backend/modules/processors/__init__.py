# 🚀 KR-AI-Engine - Processing Modules
"""
Specialized document processing modules

Each processor handles a specific aspect of document analysis:
- TextProcessor: PDF text extraction and chunking
- ImageProcessor: Image extraction, OCR, and vision AI
- EmbeddingProcessor: Vector generation and management  
- ClassificationProcessor: Document type and metadata classification
- StorageProcessor: Database and storage operations
"""

from .text_processor import TextProcessor
from .image_processor import ImageProcessor
from .embedding_processor import EmbeddingProcessor
from .classification_processor import ClassificationProcessor  
from .storage_processor import StorageProcessor

__all__ = [
    "TextProcessor",
    "ImageProcessor", 
    "EmbeddingProcessor",
    "ClassificationProcessor",
    "StorageProcessor"
]
