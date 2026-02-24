import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from backend.core.types import Stage
from scripts.quality_validator import QualityValidator
from scripts.report_generator import ReportGenerator


def test_report_generator_uses_expected_stage_records_and_caps_success_rate():
    generator = ReportGenerator("test_results")
    report_path = generator.generate(
        {
            "test_run_id": "test_1",
            "started_at": "2026-02-18T10:00:00",
            "ended_at": "2026-02-18T10:00:10",
            "duration_seconds": 10.0,
            "document_ids": ["doc-a", "doc-b"],
            "pdf_paths": ["a.pdf", "b.pdf"],
            "quality_results": {
                "status": "PASS",
                "metrics": {
                    "stage_status": {
                        "expected_stage_records": 32,
                        "completed_stages": 40,
                    }
                },
            },
            "errors": [],
        }
    )

    try:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        summary = report["summary"]

        assert summary["total_stages"] == 32
        assert summary["completed_stages"] <= summary["total_stages"]
        assert summary["success_rate"] <= 1.0
    finally:
        Path(report_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_quality_validator_stage_status_uses_dynamic_stage_count(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "true")
    monkeypatch.setenv("ENABLE_SVG_EXTRACTION", "true")
    stage_count = len(list(Stage))
    doc_ids = ["doc-a", "doc-b"]
    expected = len(doc_ids) * stage_count

    rows = []
    for index in range(expected):
        rows.append(
            {
                "document_id": doc_ids[index // stage_count],
                "stage_number": (index % stage_count) + 1,
                "stage_name": f"stage_{index % stage_count}",
                "status": "completed",
                "metadata": {},  # metadata is required because the validator expects the SQL rows to include it
            }
        )

    mock_db_adapter = AsyncMock()
    mock_db_adapter.fetch_all = AsyncMock(return_value=rows)

    validator = QualityValidator(mock_db_adapter, thresholds={})
    result = await validator._check_stage_status(doc_ids)

    assert result["expected_stage_records"] == expected
    assert result["total_stage_records"] == expected
    assert result["completed_stages"] == expected
    assert result["status"] == "PASS"


@pytest.mark.asyncio
async def test_quality_validator_stage_status_respects_disabled_video_stage(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "false")
    monkeypatch.setenv("ENABLE_SVG_EXTRACTION", "true")

    doc_ids = ["doc-a"]
    enabled_stage_names = [stage.value for stage in Stage if stage.value != Stage.VIDEO_ENRICHMENT.value]
    rows = [
        {
            "document_id": "doc-a",
            "stage_number": index + 1,
            "stage_name": stage_name,
            "status": "completed",
            "metadata": {},
        }
        for index, stage_name in enumerate(enabled_stage_names)
    ]

    mock_db_adapter = AsyncMock()
    mock_db_adapter.fetch_all = AsyncMock(return_value=rows)

    validator = QualityValidator(mock_db_adapter, thresholds={})
    result = await validator._check_stage_status(doc_ids)

    assert result["expected_stage_records"] == len(enabled_stage_names)
    assert result["total_stage_records"] == len(enabled_stage_names)
    assert result["completed_stages"] == len(enabled_stage_names)
    assert result["status"] == "PASS"


@pytest.mark.asyncio
async def test_quality_validator_stage_status_counts_skipped_as_completed(monkeypatch):
    monkeypatch.setenv("ENABLE_BRIGHTCOVE_ENRICHMENT", "true")
    monkeypatch.setenv("ENABLE_SVG_EXTRACTION", "true")

    stage_names = [stage.value for stage in Stage]
    rows = []
    for index, stage_name in enumerate(stage_names):
        status = "completed"
        metadata = {}
        if stage_name == Stage.VIDEO_ENRICHMENT.value:
            status = "skipped"
            metadata = {"skipped": True, "skip_reason": "feature disabled"}
        rows.append(
            {
                "document_id": "doc-a",
                "stage_number": index + 1,
                "stage_name": stage_name,
                "status": status,
                "metadata": metadata,
            }
        )

    mock_db_adapter = AsyncMock()
    mock_db_adapter.fetch_all = AsyncMock(return_value=rows)

    validator = QualityValidator(mock_db_adapter, thresholds={})
    result = await validator._check_stage_status(["doc-a"])

    assert result["expected_stage_records"] == len(stage_names)
    assert result["total_stage_records"] == len(stage_names)
    assert result["completed_stages"] == len(stage_names)
    assert result["status"] == "PASS"
