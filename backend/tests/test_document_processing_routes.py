"""Tests for document_processing router."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI

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

    # asyncpg stub — needs Pool attribute so FastAPI can resolve type annotations
    asyncpg_mod = types.ModuleType("asyncpg")
    asyncpg_mod.Pool = type("Pool", (), {})  # minimal class stub
    sys.modules["asyncpg"] = asyncpg_mod

    # models.document stub with CANONICAL_STAGES
    models_pkg = types.ModuleType("models")
    models_pkg.__path__ = [str(ROOT / "models")]
    sys.modules.setdefault("models", models_pkg)

    doc_mod = types.ModuleType("models.document")
    doc_mod.CANONICAL_STAGES = [
        "upload",
        "text_extraction",
        "table_extraction",
        "svg_processing",
        "image_processing",
        "visual_embedding",
        "link_extraction",
        "video_enrichment",
        "chunk_preprocessing",
        "classification",
        "metadata_extraction",
        "parts_extraction",
        "series_detection",
        "storage",
        "embedding",
        "search_indexing",
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


def _make_test_app():
    """Create a minimal FastAPI app with the document_processing router and a mock pool."""
    from api.routes.document_processing import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=False),
        )
    )

    async def override_pool():
        return mock_pool

    from api.dependencies.database import get_database_pool

    app.dependency_overrides[get_database_pool] = override_pool
    app.state.pipeline = MagicMock()
    app.state.storage_service = MagicMock()
    app.state.db_adapter = MagicMock()
    return app, mock_conn


@pytest.mark.asyncio
async def test_get_stages_names_returns_canonical_list():
    app, _ = _make_test_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/stages/names",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"]["stages"], list)
    assert len(body["data"]["stages"]) > 0
    assert body["data"]["total"] == len(body["data"]["stages"])


@pytest.mark.asyncio
async def test_get_document_status_returns_success_response():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(
        return_value={
            "id": "doc-123",
            "processing_status": "completed",
            "stage_status": json.dumps({"embedding": "completed", "text_extraction": "completed"}),
        }
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/documents/doc-123/status",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "completed"
    assert body["data"]["document_id"] == "doc-123"
    assert "current_stage" in body["data"]
    assert "progress" in body["data"]


@pytest.mark.asyncio
async def test_get_document_status_404_when_not_found():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/documents/missing-id/status",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_document_stages_returns_stage_status():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(
        return_value={
            "id": "doc-123",
            "stage_status": json.dumps({"text_extraction": "completed", "embedding": "pending"}),
        }
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/documents/doc-123/stages",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["found"] is True
    assert body["data"]["document_id"] == "doc-123"
    assert isinstance(body["data"]["stage_status"], dict)


@pytest.mark.asyncio
async def test_get_document_stages_returns_found_false_when_missing():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/documents/missing/stages",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["found"] is False
    assert body["data"]["stage_status"] == {}


@pytest.mark.asyncio
async def test_reprocess_document_returns_pending():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value={"id": "doc-123"})
    mock_conn.execute = AsyncMock()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/documents/doc-123/reprocess",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "pending"
    assert body["data"]["document_id"] == "doc-123"


@pytest.mark.asyncio
async def test_reprocess_document_404_when_not_found():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/documents/missing/reprocess",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_process_single_stage_valid_stage():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value={"id": "doc-123"})
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/documents/doc-123/process/stage/embedding",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["stage"] == "embedding"
    assert body["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_process_single_stage_invalid_stage_returns_400():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value={"id": "doc-123"})
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/documents/doc-123/process/stage/nonexistent_stage",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 400
