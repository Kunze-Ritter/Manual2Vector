from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest

from backend.processors.upload_processor import UploadProcessor


class FakeDatabaseAdapter:
    def __init__(self) -> None:
        self.created_document = None
        self.queue_items: list[object] = []

    async def get_document_by_hash(self, file_hash: str):
        return None

    async def create_document(self, document):
        self.created_document = document
        return "doc-123"

    async def update_document(self, document_id: str, updates: dict):
        return True

    async def create_processing_queue_item(self, queue_item):
        self.queue_items.append(queue_item)
        return "queue-123"

    async def execute_rpc(self, function_name: str, params: dict | None = None):
        return None


class FakeStorageService:
    def __init__(self) -> None:
        self.connected = False
        self.upload_calls: list[dict[str, object]] = []

    async def connect(self) -> None:
        self.connected = True

    async def upload_file(
        self, content: bytes, filename: str, bucket_type: str = "documents", metadata: dict | None = None
    ):
        self.upload_calls.append(
            {
                "content": content,
                "filename": filename,
                "bucket_type": bucket_type,
                "metadata": metadata or {},
            }
        )
        return {
            "success": True,
            "storage_path": "documents/test-hash",
            "storage_url": "http://minio.example/documents/test-hash",
            "file_hash": "test-hash",
        }


def _create_pdf(path: Path) -> None:
    doc = fitz.open()
    doc.new_page()
    doc.save(path)
    doc.close()


@pytest.mark.asyncio
async def test_upload_processor_uploads_pdf_to_object_storage(tmp_path: Path):
    pdf_path = tmp_path / "manual.pdf"
    _create_pdf(pdf_path)

    db = FakeDatabaseAdapter()
    storage = FakeStorageService()
    processor = UploadProcessor(
        database_adapter=db,
        storage_service=storage,
        upload_documents_to_storage=True,
    )

    context = SimpleNamespace(
        file_path=str(pdf_path),
        document_type="service_manual",
        force_reprocess=False,
        language="en",
    )

    result = await processor.process(context)

    assert result.success is True
    assert storage.connected is True
    assert len(storage.upload_calls) == 1
    assert storage.upload_calls[0]["bucket_type"] == "documents"
    assert db.created_document is not None
    assert db.created_document.storage_path == "documents/test-hash"
    assert db.created_document.storage_url == "http://minio.example/documents/test-hash"
    assert result.data["metadata"]["storage_url"] == "http://minio.example/documents/test-hash"
