"""Storage Processor - Persist generated assets to storage and database."""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.base_processor import BaseProcessor, Stage


class StorageProcessor(BaseProcessor):
    """Stage 8 processor responsible for persisting generated artifacts."""

    def __init__(self, database_service=None, storage_service=None, ai_service=None):
        super().__init__(name="storage_processor")
        self.stage = Stage.STORAGE
        self.database_service = database_service
        self.storage_service = storage_service
        self.ai_service = ai_service  # reserved for future use

        if not self.database_service:
            self.logger.warning("StorageProcessor initialized without database service")
        if not self.storage_service:
            self.logger.warning("StorageProcessor initialized without object storage service")

    async def process(self, context) -> Any:
        """Store pending artifacts for the given document."""
        document_id = getattr(context, "document_id", None)
        if not document_id:
            raise ValueError("Processing context must include 'document_id'")

        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            pending_artifacts = await self._load_pending_artifacts(str(document_id), adapter)
            if not pending_artifacts:
                adapter.info("No pending artifacts to store")
                return self._create_result(True, "No pending artifacts", {"saved_items": 0})

            saved_items = 0
            errors: List[str] = []

            for artifact in pending_artifacts:
                try:
                    artifact_type = artifact.get("artifact_type")
                    adapter.debug("Processing artifact %s of type %s", artifact.get("id"), artifact_type)

                    if artifact_type == "link":
                        await self._store_link_artifact(artifact, adapter)
                    elif artifact_type == "video":
                        await self._store_video_artifact(artifact, adapter)
                    elif artifact_type == "chunk":
                        await self._store_chunk_artifact(artifact, adapter)
                    elif artifact_type == "embedding":
                        await self._store_embedding_artifact(artifact, adapter)
                    elif artifact_type == "image":
                        await self._store_image_artifact(artifact, adapter)
                    else:
                        adapter.debug("Unsupported artifact type: %s", artifact_type)
                        continue

                    saved_items += 1
                except Exception as exc:
                    error_msg = f"Failed to store artifact {artifact.get('id')}: {exc}"
                    errors.append(error_msg)
                    adapter.warning(error_msg)

            adapter.info("Storage stage complete: %s items stored, %s errors", saved_items, len(errors))

            return self._create_result(
                success=len(errors) == 0,
                message="Storage stage completed" if not errors else "Storage stage completed with errors",
                data={
                    "saved_items": saved_items,
                    "errors": errors
                }
            )

    async def _load_pending_artifacts(self, document_id: str, adapter) -> List[Dict]:
        """Retrieve pending storage tasks for a document."""
        if not self.database_service or not getattr(self.database_service, "client", None):
            return []

        try:
            result = self.database_service.client.table("vw_processing_queue").select("*").eq(
                "document_id", document_id
            ).eq("stage", "storage").eq("status", "pending").execute()

            artifacts: List[Dict] = []
            for row in result.data or []:
                payload = row.get("payload")
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except json.JSONDecodeError:
                        payload = {}

                artifacts.append({
                    "id": row.get("id"),
                    "artifact_type": row.get("artifact_type"),
                    "payload": payload or {},
                    "created_at": row.get("created_at")
                })

            return artifacts
        except Exception as exc:
            adapter.warning("Failed to load pending artifacts: %s", exc)
            return []

    async def _store_link_artifact(self, artifact: Dict, adapter):
        """Persist link artifact to database."""
        if not self.database_service or not getattr(self.database_service, "client", None):
            return

        payload = artifact.get("payload", {})
        link_data = {
            "document_id": payload.get("document_id"),
            "url": payload.get("url"),
            "description": payload.get("description"),
            "link_type": payload.get("link_type", "external"),
            "link_category": payload.get("link_category", "external"),
            "page_number": payload.get("page_number"),
            "position_data": payload.get("position_data"),
            "confidence_score": payload.get("confidence_score", 0.5),
            "manufacturer_id": payload.get("manufacturer_id"),
            "series_id": payload.get("series_id"),
            "related_error_codes": payload.get("related_error_codes") or []
        }

        self.database_service.client.table("vw_links").insert(link_data).execute()
        adapter.debug("Stored link artifact %s", artifact.get("id"))

    async def _store_video_artifact(self, artifact: Dict, adapter):
        """Persist video artifact to database."""
        if not self.database_service or not getattr(self.database_service, "client", None):
            return

        payload = artifact.get("payload", {})
        video_data = {
            "link_id": payload.get("link_id"),
            "document_id": payload.get("document_id"),
            "youtube_id": payload.get("youtube_id"),
            "title": payload.get("title"),
            "description": payload.get("description"),
            "thumbnail_url": payload.get("thumbnail_url"),
            "duration": payload.get("duration"),
            "platform": payload.get("platform", "youtube"),
            "metadata": payload.get("metadata") or {},
            "manufacturer_id": payload.get("manufacturer_id"),
            "series_id": payload.get("series_id")
        }

        self.database_service.client.table("vw_videos").insert(video_data).execute()
        adapter.debug("Stored video artifact %s", artifact.get("id"))

    async def _store_chunk_artifact(self, artifact: Dict, adapter):
        """Persist chunk artifact to database."""
        if not self.database_service or not getattr(self.database_service, "client", None):
            return

        payload = artifact.get("payload", {})
        chunk_data = {
            "document_id": payload.get("document_id"),
            "chunk_index": payload.get("chunk_index"),
            "page_start": payload.get("page_start"),
            "page_end": payload.get("page_end"),
            "content": payload.get("content"),
            "content_hash": payload.get("content_hash"),
            "char_count": payload.get("char_count"),
            "metadata": payload.get("metadata") or {}
        }

        self.database_service.client.table("vw_chunks").insert(chunk_data).execute()
        adapter.debug("Stored chunk artifact %s", artifact.get("id"))

    async def _store_embedding_artifact(self, artifact: Dict, adapter):
        """Persist embedding artifact to database."""
        if not self.database_service or not getattr(self.database_service, "client", None):
            return

        payload = artifact.get("payload", {})
        embedding_data = {
            "document_id": payload.get("document_id"),
            "chunk_id": payload.get("chunk_id"),
            "embedding": payload.get("embedding"),
            "model": payload.get("model"),
            "embedding_type": payload.get("embedding_type", "document"),
            "metadata": payload.get("metadata") or {}
        }

        self.database_service.client.table("vw_embeddings").insert(embedding_data).execute()
        adapter.debug("Stored embedding artifact %s", artifact.get("id"))

    async def _store_image_artifact(self, artifact: Dict, adapter):
        """Upload image content to storage and persist metadata."""
        if not self.storage_service or not getattr(self.storage_service, "client", None):
            self.logger.debug("Storage service not configured - skipping image upload")
            return

        payload = artifact.get("payload", {})
        content_bytes = payload.get("content")
        filename = payload.get("filename") or "image.bin"
        bucket_type = payload.get("bucket_type", "document_images")
        metadata = payload.get("metadata") or {}

        if not content_bytes:
            adapter.debug("No content found for image artifact %s", artifact.get("id"))
            return

        encoding = payload.get("content_encoding")
        if isinstance(content_bytes, str) and encoding == "base64":
            try:
                content_bytes = base64.b64decode(content_bytes)
            except Exception as exc:
                adapter.warning("Failed to decode base64 image content for artifact %s: %s", artifact.get("id"), exc)
                return

        result = await self.storage_service.upload_image(
            content=content_bytes,
            filename=filename,
            bucket_type=bucket_type,
            metadata=metadata
        )

        if result.get("success") and self.database_service and getattr(self.database_service, "client", None):
            image_record = {
                "document_id": payload.get("document_id"),
                "page_number": payload.get("page_number"),
                "image_type": payload.get("image_type", "diagram"),
                "storage_url": result.get("url"),
                "storage_path": result.get("storage_path"),
                "file_hash": result.get("file_hash"),
                "metadata": metadata
            }
            self.database_service.client.table("vw_images").insert(image_record).execute()
            adapter.debug("Stored image artifact %s", artifact.get("id"))

    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        class Result:
            def __init__(self, success: bool, message: str, data: Dict):
                self.success = success
                self.message = message
                self.data = data

        return Result(success, message, data)
