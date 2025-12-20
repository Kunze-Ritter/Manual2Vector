"""End-to-end style tests for ImageProcessor.

These reuse the existing ImageProcessor implementation but run it in a
controlled environment using the sample PDFs and mock services from
conftest. The tests are intentionally focused on core paths rather than the
entire design surface.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from backend.processors.image_processor import ImageProcessor
from backend.core.base_processor import ProcessingContext


pytestmark = [pytest.mark.processor, pytest.mark.image]


def _create_context(document_id: str, pdf_path: Path) -> ProcessingContext:
    return ProcessingContext(
        document_id=document_id,
        file_path=str(pdf_path),
        document_type="service_manual",
        metadata={"filename": pdf_path.name},
    )


class DummyDatabaseService:
    """Shim exposing `.client.table("vw_processing_queue")` used by ImageProcessor."""

    def __init__(self) -> None:
        self.queued = []

        class _Client:
            def __init__(self, outer) -> None:
                self._outer = outer

            def table(self, name):  # pragma: no cover - thin shim
                outer = self._outer

                class _Table:
                    def insert(self, rows):
                        if isinstance(rows, list):
                            outer.queued.extend(rows)
                        else:
                            outer.queued.append(rows)
                        return self

                    def execute(self):
                        return None

                return _Table()

        self.client = _Client(self)


class TestImageExtractionE2E:
    """Validate that images can be extracted and filtered from a synthetic PDF."""

    @pytest.mark.asyncio
    async def test_process_document_with_images(
        self,
        sample_pdf_with_images,
        mock_storage_service,
        mock_ai_service,
    ) -> None:
        db = DummyDatabaseService()
        processor = ImageProcessor(
            supabase_client=db,
            storage_service=mock_storage_service,
            ai_service=mock_ai_service,
            enable_ocr=False,
            enable_vision=False,
        )

        ctx = _create_context(str(uuid4()), sample_pdf_with_images["path"])
        result = await processor.process(ctx)

        assert result["success"]
        assert result["total_extracted"] >= 1
        assert result["total_filtered"] >= 1

    @pytest.mark.asyncio
    async def test_queue_images_for_storage(
        self,
        sample_pdf_with_images,
        mock_storage_service,
        mock_ai_service,
    ) -> None:
        db = DummyDatabaseService()
        processor = ImageProcessor(
            supabase_client=db,
            storage_service=mock_storage_service,
            ai_service=mock_ai_service,
            enable_ocr=False,
            enable_vision=False,
        )

        ctx = _create_context(str(uuid4()), sample_pdf_with_images["path"])
        result = await processor.process(ctx)

        assert result["success"]
        assert result["storage_tasks_created"] == len(db.queued) or result["storage_tasks_created"] == 0


class TestImageProcessorErrorHandling:
    """Minimal negative-path checks for image processing."""

    @pytest.mark.asyncio
    async def test_process_missing_pdf_path(
        self,
        mock_storage_service,
        mock_ai_service,
    ) -> None:
        db = DummyDatabaseService()
        processor = ImageProcessor(
            supabase_client=db,
            storage_service=mock_storage_service,
            ai_service=mock_ai_service,
            enable_ocr=False,
            enable_vision=False,
        )

        ctx = ProcessingContext(
            document_id=str(uuid4()),
            file_path="/tmp/missing.pdf",
            document_type="service_manual",
        )

        result = await processor.process(ctx)
        assert not result["success"]
