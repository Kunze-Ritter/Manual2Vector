"""
KR-AI-Engine Core Module
Base interfaces and data models for the processing pipeline
"""

from .base_processor import BaseProcessor, ProcessingResult, ProcessingError
from .data_models import DocumentModel, ChunkModel, ImageModel, ErrorCodeModel

__all__ = [
    'BaseProcessor',
    'ProcessingResult', 
    'ProcessingError',
    'DocumentModel',
    'ChunkModel',
    'ImageModel',
    'ErrorCodeModel'
]
