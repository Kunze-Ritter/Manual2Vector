# Laravel ↔ Python Upload Flow Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken Laravel ↔ Python document upload flow by adding 8 missing Python endpoints, correcting URL/field mismatches in KraiEngineService, and wiring Docker env vars.

**Architecture:** A new `backend/api/routes/document_processing.py` router is mounted in `app.py` under `/api/v1`, providing the endpoints Laravel calls. All responses are wrapped in `SuccessResponse`. `KraiEngineService.php` is updated to call the correct URLs and read `$data['data'][...]`. App startup stores pipeline/storage services in `app.state` for use by the new router.

**Tech Stack:** FastAPI (Python), asyncpg, KRMasterPipeline, Laravel HTTP client (PHP), PHPUnit with `Http::fake()`

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `backend/api/routes/document_processing.py` | **Create** | 8 new Python endpoints |
| `backend/api/routes/response_models.py` | **Modify** | Add `DocumentProcessingStatusResponse` |
| `backend/api/app.py` | **Modify** | Add `language` Form param to upload; mount new router; store `pipeline`/`storage_service` in `app.state` |
| `backend/tests/test_document_processing_routes.py` | **Create** | Python route tests |
| `laravel-admin/app/Services/KraiEngineService.php` | **Modify** | Fixes 1-7 (URLs, field paths, Content-Type, timeout) |
| `laravel-admin/app/Providers/AppServiceProvider.php` | **Modify** | Pass `$uploadTimeout` to KraiEngineService constructor |
| `laravel-admin/config/krai.php` | **Modify** | Add `upload_timeout` key |
| `laravel-admin/app/Filament/Resources/Documents/Pages/EditDocument.php` | **Modify** | Update 2 caller sites (lines 101, 153) |
| `laravel-admin/tests/Feature/KraiEngineServiceFixesTest.php` | **Create** | PHP service tests |
| `docker-compose.yml` | **Modify** | Add 3 env vars to laravel-admin block |
| `laravel-admin/.env.example` | **Modify** | Add admin credential vars |
| `.env.example` | **Modify** | Add hint comment above `KRAI_SERVICE_JWT` |

---

## Task 1: Add `DocumentProcessingStatusResponse` model, router skeleton, and app.py wiring

**Files:**
- Modify: `backend/api/routes/response_models.py`
- Create: `backend/api/routes/document_processing.py`
- Modify: `backend/api/app.py` (startup + include_router)

### Background

This task lays the foundation all other Python tasks build on. Do not implement any endpoint logic yet — just the model, router skeleton, and wiring.

In `app.py`:
- `app.state.db_adapter` (DatabaseAdapter) is already stored during startup
- You need to also store `app.state.pipeline` (KRMasterPipeline) and `app.state.storage_service` (ObjectStorageService) during startup for use by the new router

---

- [ ] **Step 1: Add `DocumentProcessingStatusResponse` to response_models.py**

Add after the existing `DocumentStatusResponse` class at the top of `backend/api/routes/response_models.py`:

```python
class DocumentProcessingStatusResponse(BaseModel):
    """Processing status response for the new /api/v1/documents/{id}/status endpoint.
    Distinct from DocumentStatusResponse (which has field 'document_status')."""
    document_id: str
    status: str = Field(..., description="pending|processing|completed|failed")
    current_stage: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    queue_position: int = Field(default=0)
    total_queue_items: int = Field(default=0)
```

- [ ] **Step 2: Create router skeleton**

Create `backend/api/routes/document_processing.py`:

```python
"""
Document processing endpoints — stage control, reprocess, status.
Mounted under /api/v1 in app.py.
All responses wrapped in SuccessResponse. Laravel reads $data['data'][...].
"""
from __future__ import annotations

import logging
from typing import Optional

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from api.dependencies.database import get_database_pool
from api.middleware.auth_middleware import require_permission
from api.routes.response_models import (
    StageListResponse,
    StageProcessingRequest,
    StageProcessingResponse,
    StageStatusResponse,
    SuccessResponse,
    ThumbnailGenerationRequest,
    VideoProcessingRequest,
    DocumentProcessingStatusResponse,
)
from models.document import CANONICAL_STAGES

logger = logging.getLogger("krai.api.document_processing")

router = APIRouter(tags=["document-processing"])
```

- [ ] **Step 3: Wire router and app.state services in app.py**

Open `backend/api/app.py`. Find the `startup_events` function (around line 867). After `app.state.db_adapter = db_adapter`, add:

```python
    # Services for document_processing router
    from services.storage_factory import create_storage_service
    from pipeline.master_pipeline import KRMasterPipeline
    try:
        app.state.storage_service = create_storage_service()
    except Exception as exc:
        logger.warning("Object storage not available: %s — thumbnail endpoint will fail", exc)
        app.state.storage_service = None
    app.state.pipeline = KRMasterPipeline(
        database_adapter=db_adapter,
        force_continue_on_errors=True,
    )
```

Find the router include block (around line 1184) and add before `app.include_router(openai_compat_router)`:

```python
from api.routes.document_processing import router as document_processing_router
app.include_router(document_processing_router, prefix="/api/v1")
```

- [ ] **Step 4: Write a smoke test**

Create `backend/tests/test_document_processing_routes.py`:

```python
"""Tests for document_processing router."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _stub_modules():
    """Register minimal stubs so document_processing.py can be imported without full app."""
    api_pkg = types.ModuleType("api")
    api_pkg.__path__ = [str(ROOT / "api")]
    sys.modules.setdefault("api", api_pkg)

    routes_pkg = types.ModuleType("api.routes")
    routes_pkg.__path__ = [str(ROOT / "api" / "routes")]
    sys.modules.setdefault("api.routes", routes_pkg)

    dep_pkg = types.ModuleType("api.dependencies")
    dep_pkg.__path__ = [str(ROOT / "api" / "dependencies")]
    sys.modules.setdefault("api.dependencies", dep_pkg)

    mw_pkg = types.ModuleType("api.middleware")
    mw_pkg.__path__ = [str(ROOT / "api" / "middleware")]
    sys.modules.setdefault("api.middleware", mw_pkg)

    auth_mod = types.ModuleType("api.middleware.auth_middleware")
    auth_mod.require_permission = lambda _perm: (lambda: {"id": "test"})
    sys.modules["api.middleware.auth_middleware"] = auth_mod


def test_router_imports_cleanly():
    _stub_modules()
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "api.routes.document_processing",
        ROOT / "api" / "routes" / "document_processing.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "router")
    assert mod.router is not None
```

- [ ] **Step 5: Run test**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py::test_router_imports_cleanly -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/routes/response_models.py \
        backend/api/routes/document_processing.py \
        backend/api/app.py \
        backend/tests/test_document_processing_routes.py
git commit -m "[Upload] Add DocumentProcessingStatusResponse model and document_processing router skeleton"
```

---

## Task 2: GET endpoints — status, stage status, stage names

**Files:**
- Modify: `backend/api/routes/document_processing.py`
- Modify: `backend/tests/test_document_processing_routes.py`

### Background

Three read-only GET endpoints. All query `asyncpg.Pool` directly (raw SQL). The `/stages/names` endpoint returns `CANONICAL_STAGES` — no DB needed. The status endpoint reads `stage_status` (JSONB) to derive `current_stage` and `progress` — do NOT read from `krai_system.stage_tracking`.

`CANONICAL_STAGES` in `backend/models/document.py` is a plain Python list of stage name strings. It has 15 entries including "upload" (total 15, not 16 as the spec example shows — use `len(CANONICAL_STAGES)` dynamically).

---

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_document_processing_routes.py`:

```python
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI


def _make_test_app():
    """Create a minimal FastAPI app with the document_processing router and a mock pool."""
    _stub_modules()
    from api.routes.document_processing import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))

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
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": "doc-123",
        "processing_status": "completed",
        "stage_status": json.dumps({"embedding": "completed", "text_extraction": "completed"}),
    })
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
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": "doc-123",
        "stage_status": json.dumps({"text_extraction": "completed", "embedding": "pending"}),
    })
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -k "stages_names or document_status or document_stages" -v
```

Expected: FAIL (endpoints not implemented yet)

- [ ] **Step 3: Implement the three GET endpoints**

Add to `backend/api/routes/document_processing.py`:

```python
@router.get("/stages/names")
async def get_stage_names(
    _: dict = Depends(require_permission("documents:read")),
) -> SuccessResponse[StageListResponse]:
    """Return the global list of canonical stage names (not document-scoped)."""
    return SuccessResponse(data=StageListResponse(stages=CANONICAL_STAGES, total=len(CANONICAL_STAGES)))


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:read")),
) -> SuccessResponse[DocumentProcessingStatusResponse]:
    """Return document processing status. Derives current_stage/progress from stage_status JSONB."""
    import json as _json

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, processing_status, stage_status FROM krai_core.documents WHERE id = $1",
            document_id,
        )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    raw_stage_status: dict = {}
    if row["stage_status"]:
        raw = row["stage_status"]
        raw_stage_status = _json.loads(raw) if isinstance(raw, str) else raw

    # Derive current_stage: last stage that is not 'completed'
    current_stage: Optional[str] = None
    completed_count = 0
    for stage in CANONICAL_STAGES:
        stage_val = raw_stage_status.get(stage, "")
        if stage_val == "completed":
            completed_count += 1
        elif stage_val in ("processing", "pending", "failed"):
            current_stage = stage
            break
    progress = round(completed_count / len(CANONICAL_STAGES), 4) if CANONICAL_STAGES else 0.0

    return SuccessResponse(data=DocumentProcessingStatusResponse(
        document_id=document_id,
        status=row["processing_status"] or "unknown",
        current_stage=current_stage,
        progress=progress,
        queue_position=0,
        total_queue_items=0,
    ))


@router.get("/documents/{document_id}/stages")
async def get_document_stages(
    document_id: str,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:read")),
) -> SuccessResponse[StageStatusResponse]:
    """Return per-stage status from stage_status JSONB. Returns found=false (not 404) when missing."""
    import json as _json

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, stage_status FROM krai_core.documents WHERE id = $1",
            document_id,
        )
    if row is None:
        return SuccessResponse(data=StageStatusResponse(
            document_id=document_id, stage_status={}, found=False,
        ))

    raw = row["stage_status"]
    stage_status = (_json.loads(raw) if isinstance(raw, str) else raw) or {}
    return SuccessResponse(data=StageStatusResponse(
        document_id=document_id, stage_status=stage_status, found=True,
    ))
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -k "stages_names or document_status or document_stages" -v
```

Expected: all 5 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/routes/document_processing.py backend/tests/test_document_processing_routes.py
git commit -m "[Upload] Add GET status, stage status, stage names endpoints"
```

---

## Task 3: POST reprocess + single stage endpoints

**Files:**
- Modify: `backend/api/routes/document_processing.py`
- Modify: `backend/tests/test_document_processing_routes.py`

### Background

Both endpoints launch work as `BackgroundTask`s (async fire-and-forget). The endpoint returns immediately once the DB is updated and the task is queued. The pipeline (`app.state.pipeline`) runs stages asynchronously.

The `processStage` endpoint validates the stage name against `CANONICAL_STAGES` — raise 400 if invalid.

The reprocess steps per spec:
1. `UPDATE krai_core.documents SET processing_status='pending', stage_status='{}'::jsonb WHERE id=$1`
2. `DELETE FROM krai_system.stage_tracking WHERE document_id=$1` (guard: catch if table doesn't exist)
3. `DELETE FROM krai_system.completion_markers WHERE document_id=$1` (guard: try/except)
4. `BackgroundTasks.add_task(run_pipeline, document_id, pipeline)`

---

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_document_processing_routes.py`:

```python
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
```

- [ ] **Step 2: Verify tests fail**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -k "reprocess or single_stage" -v
```

Expected: FAIL

- [ ] **Step 3: Implement reprocess and single-stage endpoints**

Add to `backend/api/routes/document_processing.py`:

```python
async def _run_pipeline_stages(document_id: str, stages: list[str], pipeline) -> None:
    """Background task: run pipeline stages for a document."""
    try:
        await pipeline.run_stages(document_id, stages)
    except Exception as exc:
        logger.error("Background pipeline failed for %s: %s", document_id, exc)


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:write")),
):
    """Reset document state and trigger full pipeline reprocessing."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM krai_core.documents WHERE id = $1", document_id
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        await conn.execute(
            "UPDATE krai_core.documents SET processing_status = 'pending', stage_status = '{}'::jsonb WHERE id = $1",
            document_id,
        )
        try:
            await conn.execute(
                "DELETE FROM krai_system.stage_tracking WHERE document_id = $1", document_id
            )
        except Exception:
            pass  # table may not exist in all environments
        try:
            await conn.execute(
                "DELETE FROM krai_system.completion_markers WHERE document_id = $1", document_id
            )
        except Exception:
            pass

    pipeline = request.app.state.pipeline
    background_tasks.add_task(_run_pipeline_stages, document_id, CANONICAL_STAGES, pipeline)

    return SuccessResponse(data={"message": "Reprocessing queued", "document_id": document_id, "status": "pending"})


@router.post("/documents/{document_id}/process/stage/{stage_name}")
async def process_single_stage(
    document_id: str,
    stage_name: str,
    request: Request,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:write")),
):
    """Queue a single pipeline stage as a background task."""
    if stage_name not in CANONICAL_STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown stage '{stage_name}'. Valid: {', '.join(CANONICAL_STAGES)}",
        )
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM krai_core.documents WHERE id = $1", document_id
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    pipeline = request.app.state.pipeline
    background_tasks.add_task(_run_pipeline_stages, document_id, [stage_name], pipeline)

    return SuccessResponse(data={"stage": stage_name, "status": "queued", "document_id": document_id})
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -k "reprocess or single_stage" -v
```

Expected: all 4 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/routes/document_processing.py backend/tests/test_document_processing_routes.py
git commit -m "[Upload] Add POST reprocess and single-stage endpoints"
```

---

## Task 4: POST multiple-stages, video, and thumbnail endpoints

**Files:**
- Modify: `backend/api/routes/document_processing.py`
- Modify: `backend/tests/test_document_processing_routes.py`

### Background

**Multiple stages** (`POST /process/stages`): Synchronous — runs stages sequentially and returns per-stage results. Uses `pool` for DB + `request.app.state.pipeline`. Request body: `StageProcessingRequest` (already in response_models.py).

**Video** (`POST /process/video`): Uses `VideoEnrichmentService()` — no-arg constructor, reads from env. Runs synchronously.

**Thumbnail** (`POST /process/thumbnail`): Uses `ThumbnailProcessor(db_adapter, storage_service)` — reads from `request.app.state.db_adapter` and `request.app.state.storage_service`. Request body: `ThumbnailGenerationRequest` (already in response_models.py). `page` field is 0-indexed.

---

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_document_processing_routes.py`:

```python
@pytest.mark.asyncio
async def test_process_multiple_stages_returns_stage_results():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value={"id": "doc-123"})
    mock_pipeline = MagicMock()
    mock_pipeline.run_stages = AsyncMock(return_value={
        "success": True, "total_stages": 2, "successful": 2, "failed": 0,
        "success_rate": 1.0,
        "stage_results": [
            {"stage": "text_extraction", "success": True, "processing_time": 1.1, "data": {}},
            {"stage": "embedding", "success": True, "processing_time": 2.2, "data": {}},
        ],
    })
    app.state.pipeline = mock_pipeline
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/documents/doc-123/process/stages",
            json={"stages": ["text_extraction", "embedding"], "stop_on_error": True},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["total_stages"] == 2
    assert len(body["data"]["stage_results"]) == 2


@pytest.mark.asyncio
async def test_process_multiple_stages_rejects_invalid_stage():
    app, mock_conn = _make_test_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/documents/doc-123/process/stages",
            json={"stages": ["fake_stage"], "stop_on_error": True},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_process_video_returns_video_metadata():
    app, mock_conn = _make_test_app()
    with patch("api.routes.document_processing.VideoEnrichmentService") as MockVES:
        mock_ves = MagicMock()
        mock_ves.enrich_video_url = AsyncMock(return_value={
            "video_id": "vid-1", "title": "Test", "platform": "youtube",
            "thumbnail_url": "https://img", "duration": 120, "channel_title": "Chan",
        })
        MockVES.return_value = mock_ves
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/documents/doc-123/process/video",
                json={"video_url": "https://youtube.com/watch?v=abc", "manufacturer_id": None},
                headers={"Authorization": "Bearer test-token"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["platform"] == "youtube"


@pytest.mark.asyncio
async def test_process_thumbnail_returns_url():
    app, mock_conn = _make_test_app()
    mock_conn.fetchrow = AsyncMock(return_value={"id": "doc-123", "file_path": "/docs/test.pdf"})
    with patch("api.routes.document_processing.ThumbnailProcessor") as MockTP:
        mock_processor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"thumbnail_url": "https://minio/thumbnails/doc-123.png", "file_size": 48000}
        mock_result.error = None
        mock_processor.process = AsyncMock(return_value=mock_result)
        MockTP.return_value = mock_processor
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/documents/doc-123/process/thumbnail",
                json={"size": [300, 400], "page": 0},
                headers={"Authorization": "Bearer test-token"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["thumbnail_url"] == "https://minio/thumbnails/doc-123.png"
    assert body["data"]["file_size"] == 48000
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -k "multiple_stages or video or thumbnail" -v
```

Expected: FAIL

- [ ] **Step 3: Implement the three endpoints**

First, add these two imports to the **import block at the top** of `backend/api/routes/document_processing.py` (alongside the existing imports from Task 1, not mid-file):

```python
from services.video_enrichment_service import VideoEnrichmentService
from processors.thumbnail_processor import ThumbnailProcessor
```

Then add the three route functions to the bottom of the file:

```python
@router.post("/documents/{document_id}/process/stages")
async def process_multiple_stages(
    document_id: str,
    body: StageProcessingRequest,
    request: Request,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:write")),
) -> SuccessResponse[StageProcessingResponse]:
    """Run multiple pipeline stages synchronously; returns per-stage results."""
    invalid = [s for s in body.stages if s not in CANONICAL_STAGES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown stages: {', '.join(invalid)}. Valid: {', '.join(CANONICAL_STAGES)}",
        )
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM krai_core.documents WHERE id = $1", document_id
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    pipeline = request.app.state.pipeline
    raw = await pipeline.run_stages(document_id, body.stages)

    # Normalise pipeline result into StageProcessingResponse shape
    stage_results = raw.get("stage_results", [])
    successful = sum(1 for r in stage_results if r.get("success"))
    failed = len(stage_results) - successful
    resp_data = StageProcessingResponse(
        success=raw.get("success", False),
        total_stages=len(stage_results),
        successful=successful,
        failed=failed,
        stage_results=stage_results,
        success_rate=successful / len(stage_results) if stage_results else 0.0,
    )
    return SuccessResponse(data=resp_data)


@router.post("/documents/{document_id}/process/video")
async def process_video(
    document_id: str,
    body: VideoProcessingRequest,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:write")),
):
    """Trigger VideoEnrichmentService for the document and return metadata."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM krai_core.documents WHERE id = $1", document_id
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    ves = VideoEnrichmentService()
    result = await ves.enrich_video_url(str(body.video_url), document_id=document_id, manufacturer_id=body.manufacturer_id)
    return SuccessResponse(data=result)


@router.post("/documents/{document_id}/process/thumbnail")
async def process_thumbnail(
    document_id: str,
    body: ThumbnailGenerationRequest,
    request: Request,
    pool: asyncpg.Pool = Depends(get_database_pool),
    _: dict = Depends(require_permission("documents:write")),
):
    """Generate a thumbnail for the document via PyMuPDF, save to MinIO, return URL."""
    from core.base_processor import ProcessingContext

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, file_path FROM krai_core.documents WHERE id = $1", document_id
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    db_adapter = request.app.state.db_adapter
    storage_service = request.app.state.storage_service
    if storage_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Object storage not available")

    processor = ThumbnailProcessor(db_adapter, storage_service)
    ctx = ProcessingContext(
        document_id=document_id,
        file_path=row["file_path"] or "",
        file_hash="",
        document_type="",
        manufacturer=None, model=None, series=None, version=None,
        language="en",
    )
    ctx.thumbnail_page = body.page
    ctx.thumbnail_size = body.size
    result = await processor.process(ctx)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error))

    data = result.data or {}
    return SuccessResponse(data={
        "thumbnail_url": data.get("thumbnail_url"),
        "size": body.size,
        "file_size": data.get("file_size"),
    })
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -k "multiple_stages or video or thumbnail" -v
```

Expected: all 4 PASS

- [ ] **Step 5: Run all document_processing tests**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/routes/document_processing.py backend/tests/test_document_processing_routes.py
git commit -m "[Upload] Add POST process/stages, process/video, process/thumbnail endpoints"
```

---

## Task 5: Python upload language fix

**Files:**
- Modify: `backend/api/app.py` (lines ~778–820)

### Background

The `POST /upload` endpoint (around line 778) currently hardcodes `language="en"` in `ProcessingContext`. Laravel sends the `language` field in the multipart form. Add `language: str = Form("en")` to the endpoint signature and pass it to `ProcessingContext`.

Note: `Form` is already imported from `fastapi` at the top of app.py.

---

- [ ] **Step 1: Write a failing test**

Add to `backend/tests/test_document_processing_routes.py`:

```python
def test_upload_endpoint_accepts_language_form_param():
    """The /upload endpoint signature must accept a 'language' Form field."""
    import inspect
    import importlib.util
    import ast

    app_path = ROOT / "api" / "app.py"
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Find upload_document function definition
    upload_fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "upload_document":
            upload_fn = node
            break

    assert upload_fn is not None, "upload_document function not found in app.py"

    # Check that 'language' appears as a parameter with Form default
    fn_source = ast.get_source_segment(source, upload_fn)
    assert "language" in fn_source, "upload_document must have a 'language' parameter"
    assert "Form" in fn_source, "language parameter must use Form()"
    assert 'language="en"' not in fn_source or "Form" in fn_source, "language must not be hardcoded"
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py::test_upload_endpoint_accepts_language_form_param -v
```

Expected: FAIL

- [ ] **Step 3: Edit app.py upload endpoint**

In `backend/api/app.py`, find the `upload_document` function (around line 780). Add `language: str = Form("en")` to its parameters, and change the `ProcessingContext` call to use `language=language or "en"`:

```python
# BEFORE
async def upload_document(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    document_type: str = "service_manual",
    force_reprocess: bool = False,
    processor: UploadProcessor = Depends(get_upload_processor),
    current_user: dict = Depends(require_permission('documents:write'))
):

# AFTER
async def upload_document(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    document_type: str = "service_manual",
    language: str = Form("en"),
    force_reprocess: bool = False,
    processor: UploadProcessor = Depends(get_upload_processor),
    current_user: dict = Depends(require_permission('documents:write'))
):
```

Also change the `ProcessingContext` instantiation at line ~819:

```python
# BEFORE
language="en",

# AFTER
language=language or "en",
```

Note: `document_type` and `force_reprocess` are left as plain parameters (FastAPI sends them as query params for multipart requests). Only `language` needs `Form()` because Laravel sends it as a multipart form field. Do NOT convert the others.

- [ ] **Step 4: Run test**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py::test_upload_endpoint_accepts_language_form_param -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py backend/tests/test_document_processing_routes.py
git commit -m "[Upload] Read language from multipart Form field in upload endpoint"
```

---

## Task 6: KraiEngineService PHP fixes (Fixes 1–7)

**Files:**
- Modify: `laravel-admin/app/Services/KraiEngineService.php`
- Modify: `laravel-admin/app/Providers/AppServiceProvider.php`
- Modify: `laravel-admin/app/Filament/Resources/Documents/Pages/EditDocument.php`
- Create: `laravel-admin/tests/Feature/KraiEngineServiceFixesTest.php`

### Background

All changes are in `KraiEngineService.php` and two of its callers. The methods to update:

| Fix | Method | What changes |
|-----|--------|-------------|
| Fix 1 | `createHttpClient()` | Remove `Content-Type: application/json` |
| Fix 1 (cont) | `processMultipleStages`, `processVideo`, `generateThumbnail` | Add `->asJson()` before `->post()` |
| Fix 2 | `uploadDocument` | URL `/documents/upload` → `/upload` |
| Fix 3 | `getDocumentStatus` | URL + field path `$data[...]` → `$data['data'][...]` |
| Fix 4 | `getStageStatus` | URL + field paths + remove 404 branch |
| Fix 5 | `getAvailableStages` | URL to global `/api/v1/stages/names` + remove `$documentId` param |
| Fix 6 | `reprocessDocument`, `processStage`, `processMultipleStages`, `processVideo`, `generateThumbnail` | URL + field paths |
| Fix 7 | constructor | Add `$uploadTimeout = 600` param |

**Callers to update after Fix 3 and Fix 6:**
- `EditDocument.php:101` — `$result['document_status']` → `$result['status']`
- `EditDocument.php:153` — sprintf with `$result['processing_time']` → static message (background task, no timing)

After all changes, verify with `grep -r "document_status\|getDocumentStatus" laravel-admin/` that no other callers are missed.

---

- [ ] **Step 1: Write tests first**

Create `laravel-admin/tests/Feature/KraiEngineServiceFixesTest.php`:

```php
<?php

namespace Tests\Feature;

use App\Services\KraiEngineService;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class KraiEngineServiceFixesTest extends TestCase
{
    private string $baseUrl = 'http://krai-engine:8000';

    private function makeService(int $uploadTimeout = 600): KraiEngineService
    {
        return new KraiEngineService($this->baseUrl, 'test-token', 120, 60, $uploadTimeout);
    }

    /** @test */
    public function upload_document_calls_correct_url(): void
    {
        Http::fake([
            "{$this->baseUrl}/upload" => Http::response([
                'document_id' => 'doc-123',
                'filename' => 'test.pdf',
                'document_type' => 'service_manual',
                'language' => 'de',
                'status' => 'uploaded',
            ], 200),
        ]);

        $file = \Illuminate\Http\UploadedFile::fake()->create('test.pdf', 100, 'application/pdf');
        $service = $this->makeService();
        $result = $service->uploadDocument($file, 'service_manual', 'de');

        $this->assertTrue($result['success']);
        Http::assertSent(fn($req) => str_contains($req->url(), '/upload') && !str_contains($req->url(), '/documents/upload'));
    }

    /** @test */
    public function get_document_status_reads_from_data_wrapper(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/status" => Http::response([
                'success' => true,
                'data' => [
                    'document_id' => 'doc-123',
                    'status' => 'completed',
                    'current_stage' => null,
                    'progress' => 1.0,
                    'queue_position' => 0,
                    'total_queue_items' => 0,
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->getDocumentStatus('doc-123');

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('status', $result);
        $this->assertArrayNotHasKey('document_status', $result);
        $this->assertEquals('completed', $result['status']);
    }

    /** @test */
    public function get_stage_status_reads_from_data_wrapper_and_has_found(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/stages" => Http::response([
                'success' => true,
                'data' => [
                    'document_id' => 'doc-123',
                    'stage_status' => ['text_extraction' => 'completed'],
                    'found' => true,
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->getStageStatus('doc-123');

        $this->assertTrue($result['success']);
        $this->assertTrue($result['found']);
        $this->assertIsArray($result['stage_status']);
    }

    /** @test */
    public function get_available_stages_calls_global_endpoint_without_document_id(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/stages/names" => Http::response([
                'success' => true,
                'data' => ['stages' => ['text_extraction', 'embedding'], 'total' => 2],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->getAvailableStages();

        $this->assertTrue($result['success']);
        $this->assertIsArray($result['stages']);
        Http::assertSent(fn($req) => $req->url() === "{$this->baseUrl}/api/v1/stages/names");
    }

    /** @test */
    public function reprocess_document_reads_from_data_wrapper(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/reprocess" => Http::response([
                'success' => true,
                'data' => ['message' => 'Reprocessing queued', 'document_id' => 'doc-123', 'status' => 'pending'],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->reprocessDocument('doc-123');

        $this->assertTrue($result['success']);
        $this->assertEquals('pending', $result['status']);
        $this->assertEquals('doc-123', $result['document_id']);
    }

    /** @test */
    public function process_stage_returns_stage_and_document_id(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/process/stage/embedding" => Http::response([
                'success' => true,
                'data' => ['stage' => 'embedding', 'status' => 'queued', 'document_id' => 'doc-123'],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->processStage('doc-123', 'embedding');

        $this->assertTrue($result['success']);
        $this->assertEquals('embedding', $result['stage']);
        $this->assertArrayNotHasKey('processing_time', $result);
    }

    /** @test */
    public function process_multiple_stages_uses_upload_timeout(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/process/stages" => Http::response([
                'success' => true,
                'data' => [
                    'total_stages' => 1, 'successful' => 1, 'failed' => 0,
                    'success_rate' => 1.0, 'stage_results' => [],
                ],
            ], 200),
        ]);

        $service = $this->makeService(uploadTimeout: 600);
        $result = $service->processMultipleStages('doc-123', ['embedding']);

        $this->assertTrue($result['success']);
        $this->assertEquals(1, $result['total_stages']);
    }
}
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd laravel-admin && php artisan test --compact tests/Feature/KraiEngineServiceFixesTest.php
```

Expected: most tests FAIL

- [ ] **Step 3: Apply Fix 7 — Add `$uploadTimeout` to constructor**

In `KraiEngineService.php`, update the constructor:

```php
private int $uploadTimeout;

public function __construct(
    string $baseUrl,
    string $serviceToken,
    int $defaultTimeout = 120,
    int $queryTimeout = 60,
    int $uploadTimeout = 600
) {
    $this->baseUrl = rtrim($baseUrl, '/');
    $this->serviceToken = $serviceToken;
    $this->defaultTimeout = $defaultTimeout;
    $this->queryTimeout = $queryTimeout;
    $this->uploadTimeout = $uploadTimeout;
}
```

- [ ] **Step 4: Apply Fix 1 — Remove Content-Type from createHttpClient**

In `createHttpClient()`, replace:

```php
// BEFORE
$client = Http::timeout($timeout ?? $this->defaultTimeout)
    ->withHeaders([
        'Content-Type' => 'application/json',
        'Accept' => 'application/json',
    ]);

// AFTER
$client = Http::timeout($timeout ?? $this->defaultTimeout)
    ->withHeaders([
        'Accept' => 'application/json',
    ]);
```

- [ ] **Step 5: Apply Fix 2 — Upload URL**

In `uploadDocument()`, change:
```php
// BEFORE
$endpoint = "/documents/upload";

// AFTER
$endpoint = "/upload";
```

- [ ] **Step 6: Apply Fix 3 — getDocumentStatus URL + fields**

```php
// URL
$endpoint = "/api/v1/documents/{$documentId}/status";

// Success return
return [
    'success' => true,
    'status' => $data['data']['status'] ?? 'unknown',
    'current_stage' => $data['data']['current_stage'] ?? null,
    'progress' => $data['data']['progress'] ?? 0,
    'queue_position' => $data['data']['queue_position'] ?? 0,
    'total_queue_items' => $data['data']['total_queue_items'] ?? 0,
];
```

- [ ] **Step 7: Apply Fix 4 — getStageStatus URL + fields + remove 404 branch**

```php
// URL
$endpoint = "/api/v1/documents/{$documentId}/stages";

// Success return
return [
    'success' => true,
    'document_id' => $data['data']['document_id'] ?? $documentId,
    'stage_status' => $data['data']['stage_status'] ?? [],
    'found' => $data['data']['found'] ?? false,
];

// Remove the entire `elseif ($response->status() === 404)` branch
// (Python now returns 200+found:false instead of HTTP 404)
```

- [ ] **Step 8: Apply Fix 5 — getAvailableStages**

Change method signature and endpoint:

```php
// BEFORE
public function getAvailableStages(string $documentId): array {
    $endpoint = "/documents/{$documentId}/stages";
    // success: 'stages' => $data['stages'] ?? [], 'total' => $data['total'] ?? 0

// AFTER
public function getAvailableStages(): array {
    $endpoint = "/api/v1/stages/names";
    // success: 'stages' => $data['data']['stages'] ?? [], 'total' => $data['data']['total'] ?? 0
```

- [ ] **Step 9: Apply Fix 6 — remaining URL + field-path updates**

Update each method (URL + success return fields):

**`reprocessDocument`:**
```php
$endpoint = "/api/v1/documents/{$documentId}/reprocess";
// success return:
'message'     => $data['data']['message']     ?? 'Document reprocessing started',
'document_id' => $data['data']['document_id'] ?? $documentId,
'status'      => $data['data']['status']      ?? 'started',
```

**`processStage`:**
```php
$endpoint = "/api/v1/documents/{$documentId}/process/stage/{$stageName}";
// success return (remove 'data' => $data and 'processing_time'):
'stage'       => $data['data']['stage']       ?? $stageName,
'status'      => $data['data']['status']      ?? 'queued',
'document_id' => $data['data']['document_id'] ?? $documentId,
```

**`processMultipleStages`** (also add `->asJson()` and use `$this->uploadTimeout`):
```php
$endpoint = "/api/v1/documents/{$documentId}/process/stages";
$client = $this->createHttpClient($this->uploadTimeout);  // use upload timeout
$response = $client->asJson()->post($this->baseUrl . $endpoint, $payload);
// success return:
'total_stages'  => $data['data']['total_stages']  ?? count($stages),
'successful'    => $data['data']['successful']    ?? 0,
'failed'        => $data['data']['failed']        ?? 0,
'stage_results' => $data['data']['stage_results'] ?? [],
'success_rate'  => $data['data']['success_rate']  ?? 0,
```

**`processVideo`** (also add `->asJson()`):
```php
$endpoint = "/api/v1/documents/{$documentId}/process/video";
$response = $client->asJson()->post($this->baseUrl . $endpoint, $payload);
// success return:
'video_id'      => $data['data']['video_id']      ?? null,
'title'         => $data['data']['title']         ?? null,
'platform'      => $data['data']['platform']      ?? null,
'thumbnail_url' => $data['data']['thumbnail_url'] ?? null,
'duration'      => $data['data']['duration']      ?? null,
'channel_title' => $data['data']['channel_title'] ?? null,
```

**`generateThumbnail`** (also add `->asJson()`):
```php
$endpoint = "/api/v1/documents/{$documentId}/process/thumbnail";
$response = $client->asJson()->post($this->baseUrl . $endpoint, $payload);
// success return:
'thumbnail_url' => $data['data']['thumbnail_url'] ?? null,
'size'          => $data['data']['size']          ?? $size,
'file_size'     => $data['data']['file_size']     ?? null,
```

- [ ] **Step 10: Add `upload_timeout` to `config/krai.php`**

In `laravel-admin/config/krai.php`, add after the existing `'query_timeout'` line:

```php
'upload_timeout' => 600, // Timeout for multi-stage sync calls (seconds)
```

This ensures `config('krai.upload_timeout', 600)` resolves correctly rather than relying on the default fallback.

- [ ] **Step 10b: Update AppServiceProvider.php to pass $uploadTimeout**

In `AppServiceProvider.php`, the `KraiEngineService` singleton is constructed with just `engine_url` and `service_jwt`. Add the `$uploadTimeout` (use `config('krai.upload_timeout', 600)`):

```php
$this->app->singleton(KraiEngineService::class, function ($app) {
    return new KraiEngineService(
        config('krai.engine_url'),
        config('krai.service_jwt'),
        uploadTimeout: config('krai.upload_timeout', 600),
    );
});
```

- [ ] **Step 11: Update EditDocument.php callers**

**Line 101** — `$result['document_status']` → `$result['status']`:
```php
// BEFORE
$bodyLines[] = 'Dokumentenstatus: ' . $result['document_status'];

// AFTER
$bodyLines[] = 'Dokumentenstatus: ' . $result['status'];
```

**Line 153** — remove `$result['processing_time']` from sprintf:
```php
// BEFORE
->body(sprintf('Stage "%s" wurde in %.2fs verarbeitet', config('krai.stages.'.$data['stage'].'.label'), $result['processing_time']))

// AFTER
->body(sprintf('Stage "%s" wurde zur Verarbeitung eingereiht', config('krai.stages.'.$data['stage'].'.label')))
```

- [ ] **Step 12: Verify no other `document_status` or `getAvailableStages` callers missed**

```bash
grep -r "document_status\|getDocumentStatus" laravel-admin/ --include="*.php"
grep -r "getAvailableStages" laravel-admin/ --include="*.php"
```

Expected for `document_status`: only `KraiEngineService.php` (the old method definition, now removed) and `EditDocument.php` (already updated). If you see any other file reading `$result['document_status']`, update it.

Expected for `getAvailableStages`: only `KraiEngineService.php` itself. No callers should be passing a `$documentId` argument — the spec confirms none exist. If you see any caller with a string argument (e.g., `getAvailableStages($someId)`), update it to `getAvailableStages()` (no arg).

- [ ] **Step 13: Run PHP tests**

```bash
cd laravel-admin && php artisan test --compact tests/Feature/KraiEngineServiceFixesTest.php
```

Expected: all 7 PASS

- [ ] **Step 14: Run pint**

```bash
cd laravel-admin && vendor/bin/pint --dirty
```

- [ ] **Step 15: Commit**

```bash
git add laravel-admin/app/Services/KraiEngineService.php \
        laravel-admin/app/Providers/AppServiceProvider.php \
        laravel-admin/config/krai.php \
        laravel-admin/app/Filament/Resources/Documents/Pages/EditDocument.php \
        laravel-admin/tests/Feature/KraiEngineServiceFixesTest.php
git commit -m "[Upload] Fix KraiEngineService URLs, field paths, Content-Type, and timeout (Fixes 1-7)"
```

---

## Task 7: Docker + Environment files

**Files:**
- Modify: `docker-compose.yml`
- Modify: `laravel-admin/.env.example`
- Modify: `.env.example`

### Background

Three small env changes. No tests needed — these are configuration files.

The `docker-compose.yml` `laravel-admin` environment block currently uses list format (`- KEY=VALUE`). Use the same format. The block starts at line 52.

---

- [ ] **Step 1: Add env vars to docker-compose.yml**

In `docker-compose.yml`, find the `laravel-admin` → `environment:` block (around line 52–65). Add three lines at the end of the environment list, before `volumes:`:

```yaml
      - KRAI_SERVICE_JWT=${KRAI_SERVICE_JWT:-}
      - KRAI_ENGINE_ADMIN_USERNAME=${KRAI_ENGINE_ADMIN_USERNAME:-}
      - KRAI_ENGINE_ADMIN_PASSWORD=${KRAI_ENGINE_ADMIN_PASSWORD:-}
```

- [ ] **Step 2: Add admin creds to laravel-admin/.env.example**

In `laravel-admin/.env.example`, find the KRAI section (around line 78–83) and add:

```
KRAI_ENGINE_ADMIN_USERNAME=admin
KRAI_ENGINE_ADMIN_PASSWORD=changeme
```

- [ ] **Step 3: Add hint comment to root .env.example**

In `.env.example`, find the line `KRAI_SERVICE_JWT=` (around line 83). Add a comment above it:

```
# Service-to-service JWT for Laravel → Python API calls
# Generate with: python scripts/generate_service_token.py
KRAI_SERVICE_JWT=
```

- [ ] **Step 4: Verify docker-compose is valid YAML**

```bash
docker-compose config --quiet && echo "YAML valid"
```

Expected: `YAML valid` (no errors)

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml laravel-admin/.env.example .env.example
git commit -m "[Upload] Add KRAI_SERVICE_JWT and admin credentials to docker-compose and .env.example"
```

---

## Summary

| Task | Files | Tests |
|------|-------|-------|
| 1 | response_models.py, document_processing.py, app.py | 1 smoke test |
| 2 | document_processing.py | 5 GET endpoint tests |
| 3 | document_processing.py | 4 POST tests |
| 4 | document_processing.py | 3 POST tests |
| 5 | app.py | 1 AST test |
| 6 | KraiEngineService.php, AppServiceProvider.php, EditDocument.php | 7 PHP tests |
| 7 | docker-compose.yml, .env.example files | YAML validation |
