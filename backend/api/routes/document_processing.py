"""
Document processing endpoints — stage control, reprocess, status.
Mounted under /api/v1 in app.py.
All responses wrapped in SuccessResponse. Laravel reads $data['data'][...].
"""

from __future__ import annotations

import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from models.document import CANONICAL_STAGES

from api.dependencies.database import get_database_pool
from api.middleware.auth_middleware import require_permission
from api.routes.response_models import (
    DocumentProcessingStatusResponse,
    StageListResponse,
    StageStatusResponse,
    SuccessResponse,
)

logger = logging.getLogger("krai.api.document_processing")

router = APIRouter(tags=["document-processing"])


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
    current_stage: str | None = None
    completed_count = 0
    for stage in CANONICAL_STAGES:
        stage_val = raw_stage_status.get(stage, "")
        if stage_val == "completed":
            completed_count += 1
        elif stage_val in ("processing", "pending", "failed"):
            current_stage = stage
            break
    progress = round(completed_count / len(CANONICAL_STAGES), 4) if CANONICAL_STAGES else 0.0

    return SuccessResponse(
        data=DocumentProcessingStatusResponse(
            document_id=document_id,
            status=row["processing_status"] or "unknown",
            current_stage=current_stage,
            progress=progress,
            queue_position=0,
            total_queue_items=0,
        )
    )


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
        return SuccessResponse(
            data=StageStatusResponse(
                document_id=document_id,
                stage_status={},
                found=False,
            )
        )

    raw = row["stage_status"]
    stage_status = (_json.loads(raw) if isinstance(raw, str) else raw) or {}
    return SuccessResponse(
        data=StageStatusResponse(
            document_id=document_id,
            stage_status=stage_status,
            found=True,
        )
    )
