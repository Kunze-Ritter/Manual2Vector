"""
Document processing endpoints — stage control, reprocess, status.
Mounted under /api/v1 in app.py.
All responses wrapped in SuccessResponse. Laravel reads $data['data'][...].
"""

from __future__ import annotations

import json
import logging

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
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
        try:
            raw_stage_status = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            logger.warning("Malformed stage_status JSONB for document %s — treating as empty", document_id)
            raw_stage_status = {}

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
        elif stage_val and stage_val not in ("", "skipped"):
            logger.warning("Unknown stage status value '%s' for stage '%s' in document %s", stage_val, stage, document_id)
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
    try:
        stage_status = (json.loads(raw) if isinstance(raw, str) else raw) or {}
    except json.JSONDecodeError:
        logger.warning("Malformed stage_status JSONB for document %s — treating as empty", document_id)
        stage_status = {}
    return SuccessResponse(
        data=StageStatusResponse(
            document_id=document_id,
            stage_status=stage_status,
            found=True,
        )
    )


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
