"""Compatibility shim for MetadataProcessorAI.

This module exists to provide the historical import path
`backend.processors.metadata_processor.MetadataProcessorAI` while the
actual implementation lives in `metadata_processor_ai.py`.
"""

from .metadata_processor_ai import MetadataProcessorAI  # noqa: F401
