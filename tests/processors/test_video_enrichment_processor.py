import pytest

from backend.core.base_processor import ProcessingContext
from backend.processors.video_enrichment_processor import VideoEnrichmentProcessor


class FakeDatabase:
    def __init__(self):
        self.updated = []
        self.failed = []
        self.last_force = None

    async def get_videos_needing_enrichment(self, document_id, limit=100, force=False):
        self.last_force = force
        return [
            {
                "id": "v-1",
                "video_url": "https://players.brightcove.net/123/default_default/index.html?videoId=abc",
                "metadata": {"needs_enrichment": True},
            },
            {
                "id": "v-2",
                "video_url": "https://players.brightcove.net/123/default_default/index.html?videoId=def",
                "metadata": {"needs_enrichment": True},
            },
        ]

    async def update_video_enrichment(self, video_id, metadata_dict):
        self.updated.append((video_id, metadata_dict))
        return True

    async def mark_video_enrichment_failed(self, video_id, error_message):
        self.failed.append((video_id, error_message))
        return True


@pytest.mark.asyncio
async def test_processor_initialization_flag(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "false")
    processor = VideoEnrichmentProcessor(database_service=FakeDatabase())
    assert processor.enabled is False


@pytest.mark.asyncio
async def test_processor_enriches_and_fails_individually(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "true")
    db = FakeDatabase()
    processor = VideoEnrichmentProcessor(database_service=db)

    calls = {"count": 0}

    async def fake_enrich_video(url, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "title": "Brightcove Title",
                "description": "Desc",
                "duration": 42,
                "thumbnail_url": "https://example.com/thumb.jpg",
                "published_at": "2025-01-01T00:00:00Z",
                "tags": ["a", "b"],
                "metadata": {"needs_enrichment": False},
            }
        return {"error": "api failure"}

    processor.enricher.enrich_video = fake_enrich_video

    context = ProcessingContext(
        document_id="00000000-0000-0000-0000-000000000001",
        file_path="dummy.pdf",
        document_type="service_manual",
        processing_config={},
    )

    result = await processor.process(context)

    assert result.success is True
    assert result.data["enriched"] == 1
    assert result.data["failed"] == 1
    assert len(db.updated) == 1
    assert len(db.failed) == 1


@pytest.mark.asyncio
async def test_processor_skips_when_credentials_missing(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "true")
    db = FakeDatabase()
    processor = VideoEnrichmentProcessor(database_service=db)

    async def fake_enrich_video(url, **kwargs):
        return {
            "metadata": {"needs_enrichment": True, "credentials_missing": True},
            "enrichment_error": None,
        }

    processor.enricher.enrich_video = fake_enrich_video

    context = ProcessingContext(
        document_id="00000000-0000-0000-0000-000000000001",
        file_path="dummy.pdf",
        document_type="service_manual",
        processing_config={"force_video_reenrichment": True},
    )

    result = await processor.process(context)

    assert result.success is False
    assert result.data["skipped"] == 2
    assert db.last_force is True
    assert len(db.updated) == 2
    assert len(db.failed) == 0


@pytest.mark.asyncio
async def test_processor_idempotency_no_videos(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "true")

    class EmptyDatabase(FakeDatabase):
        async def get_videos_needing_enrichment(self, document_id, limit=100, force=False):
            self.last_force = force
            return []

    db = EmptyDatabase()
    processor = VideoEnrichmentProcessor(database_service=db)

    context = ProcessingContext(
        document_id="00000000-0000-0000-0000-000000000001",
        file_path="dummy.pdf",
        document_type="service_manual",
        processing_config={},
    )

    result = await processor.process(context)

    assert result.success is True
    assert result.data["videos_found"] == 0
