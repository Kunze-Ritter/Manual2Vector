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
