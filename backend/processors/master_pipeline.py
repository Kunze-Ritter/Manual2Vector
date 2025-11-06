"""Compatibility shim for legacy MasterPipeline imports.

This module preserves the previous import path while the canonical
implementation lives in ``backend.pipeline.master_pipeline``.
"""

from pipeline.master_pipeline import KRMasterPipeline

__all__ = ["MasterPipeline", "KRMasterPipeline"]

# Backwards compatibility alias
MasterPipeline = KRMasterPipeline
