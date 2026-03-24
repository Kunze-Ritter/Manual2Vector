"""Tests for document_processing router."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _stub_modules():
    """Register minimal stubs so document_processing.py can be imported without full app."""
    # Top-level package stubs with __path__ so sub-modules resolve
    for name, path_fragment in [
        ("api", "api"),
        ("api.routes", "api/routes"),
        ("api.dependencies", "api/dependencies"),
        ("api.middleware", "api/middleware"),
    ]:
        pkg = types.ModuleType(name)
        pkg.__path__ = [str(ROOT / path_fragment)]
        sys.modules.setdefault(name, pkg)

    # auth_middleware stub
    auth_mod = types.ModuleType("api.middleware.auth_middleware")
    auth_mod.require_permission = lambda _perm: (lambda: {"id": "test"})
    sys.modules["api.middleware.auth_middleware"] = auth_mod

    # api.dependencies.database stub (avoids deep services import chain)
    db_dep_mod = types.ModuleType("api.dependencies.database")
    db_dep_mod.get_database_pool = lambda: None
    sys.modules["api.dependencies.database"] = db_dep_mod

    # asyncpg stub
    asyncpg_mod = types.ModuleType("asyncpg")
    sys.modules.setdefault("asyncpg", asyncpg_mod)

    # models.document stub with CANONICAL_STAGES
    models_pkg = types.ModuleType("models")
    models_pkg.__path__ = [str(ROOT / "models")]
    sys.modules.setdefault("models", models_pkg)

    doc_mod = types.ModuleType("models.document")
    doc_mod.CANONICAL_STAGES = [
        "upload", "text_extraction", "table_extraction", "svg_processing",
        "image_processing", "visual_embedding", "link_extraction",
        "video_enrichment", "chunk_preprocessing", "classification",
        "metadata_extraction", "parts_extraction", "series_detection",
        "storage", "embedding", "search_indexing",
    ]
    sys.modules["models.document"] = doc_mod


# Run once at module import time so tests don't clobber sys.modules on each call
_stub_modules()


def test_router_imports_cleanly():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "api.routes.document_processing",
        ROOT / "api" / "routes" / "document_processing.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from fastapi import APIRouter
    assert hasattr(mod, "router")
    assert mod.router is not None
    assert isinstance(mod.router, APIRouter)
