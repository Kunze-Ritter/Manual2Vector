"""Storage Processor - Persist generated assets to storage and database."""

from __future__ import annotations

import asyncio
import base64
import json
import os
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
            images = getattr(context, 'images', None) or []
            if images:
                stored = await self._store_images_from_context(context, adapter)
                return self._create_result(
                    success=True,
                    message="Storage stage completed",
                    data={"saved_items": stored, "errors": []},
                )

            adapter.info("No pending artifacts to store")
            return self._create_result(True, "No pending artifacts", {"saved_items": 0})

    async def _store_images_from_context(self, context, adapter) -> int:
        if not self.storage_service:
            adapter.debug("Storage service not configured - skipping image upload")
            return 0

        images = getattr(context, 'images', None) or []
        if not images:
            return 0

        stored = 0
        document_id = str(getattr(context, 'document_id'))
        output_dir = getattr(context, 'output_dir', None)

        for index, image in enumerate(images):
            image_id = image.get('id')
            if not image_id:
                continue

            temp_path = image.get('temp_path') or image.get('path')
            if not temp_path:
                continue

            path_obj = Path(temp_path)
            if not path_obj.exists():
                continue

            with open(path_obj, 'rb') as fp:
                content_bytes = fp.read()

            original_filename = image.get('filename') or path_obj.name
            metadata = {
                'document_id': document_id,
                'image_id': str(image_id),
                'page_number': image.get('page_number'),
                'image_index': int(image.get('image_index') or index),
                'width': image.get('width'),
                'height': image.get('height'),
                'format': image.get('format'),
                'extracted_at': image.get('extracted_at'),
            }

            result = await self.storage_service.upload_image(
                content=content_bytes,
                filename=original_filename,
                bucket_type='document_images',
                metadata={k: v for k, v in metadata.items() if v is not None},
            )

            if not result.get('success'):
                continue

            # Use presigned URL when configured (MinIO private buckets); else public URL
            use_presigned = os.getenv('OBJECT_STORAGE_USE_PRESIGNED_URLS', 'false').lower() == 'true'
            presigned_url = result.get('presigned_url')
            storage_url = (
                presigned_url
                if use_presigned and presigned_url
                else result.get('url') or result.get('public_url') or result.get('storage_url')
            )
            storage_path = result.get('storage_path') or result.get('key')
            file_hash = result.get('file_hash')

            db_filename = storage_path or original_filename

            image['storage_url'] = storage_url
            image['storage_path'] = storage_path
            image['file_hash'] = file_hash
            if presigned_url:
                image['presigned_url'] = presigned_url

            if self.database_service:
                if not storage_url:
                    adapter.warning(
                        "Skipping DB insert for image %s because storage_url is missing (storage_path=%s)",
                        image_id,
                        storage_path,
                    )
                    continue
                await self.database_service.execute_query(
                    """
                    INSERT INTO krai_content.images (
                        id, document_id, filename, original_filename,
                        storage_path, storage_url, file_size, image_format,
                        width_px, height_px, page_number, image_index,
                        image_type, ai_description, ai_confidence,
                        contains_text,
                        ocr_text, ocr_confidence,
                        manual_description,
                        tags,
                        file_hash,
                        figure_number, figure_context
                    ) VALUES (
                        $1::uuid, $2::uuid, $3, $4,
                        $5, $6, $7, $8,
                        $9, $10, $11, $12,
                        $13, $14, $15,
                        $16,
                        $17, $18,
                        $19,
                        $20::text[],
                        $21,
                        $22, $23
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        storage_path = EXCLUDED.storage_path,
                        storage_url = EXCLUDED.storage_url,
                        file_hash = EXCLUDED.file_hash,
                        ai_description = EXCLUDED.ai_description,
                        ai_confidence = EXCLUDED.ai_confidence,
                        contains_text = EXCLUDED.contains_text,
                        ocr_text = EXCLUDED.ocr_text,
                        ocr_confidence = EXCLUDED.ocr_confidence,
                        manual_description = EXCLUDED.manual_description,
                        tags = EXCLUDED.tags,
                        figure_number = EXCLUDED.figure_number,
                        figure_context = EXCLUDED.figure_context,
                        updated_at = NOW()
                    """.strip(),
                    [
                        str(image_id),
                        document_id,
                        db_filename,
                        original_filename,
                        storage_path,
                        storage_url,
                        image.get('size_bytes'),
                        image.get('format'),
                        image.get('width'),
                        image.get('height'),
                        image.get('page_number'),
                        int(image.get('image_index') or index),
                        image.get('image_type') or image.get('type') or 'diagram',
                        image.get('ai_description'),
                        image.get('ai_confidence'),
                        bool(image.get('contains_text') or False),
                        image.get('ocr_text'),
                        image.get('ocr_confidence'),
                        image.get('manual_description'),
                        image.get('tags') or [],
                        file_hash,
                        image.get('figure_number'),
                        image.get('figure_context'),
                    ],
                )

            stored += 1

        if os.getenv('IMAGE_PROCESSOR_CLEANUP', '1') != '0' and output_dir:
            try:
                output_path = Path(output_dir)
                if output_path.exists():
                    for item in output_path.iterdir():
                        if item.is_file():
                            item.unlink()
                    output_path.rmdir()
            except Exception:
                pass

        return stored

    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        class Result:
            def __init__(self, success: bool, message: str, data: Dict):
                self.success = success
                self.message = message
                self.data = data

        return Result(success, message, data)
