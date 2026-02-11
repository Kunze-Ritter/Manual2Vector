"""
Tests for PerformanceCollector: metrics collection, aggregation, baseline storage,
improvement tracking, and buffer flushing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.services.performance_service import PerformanceCollector
from backend.core.types import ProcessingResult, ProcessingStatus


class MockDatabaseAdapter:
    """Mock DatabaseAdapter for PerformanceCollector tests."""

    def __init__(self):
        self.queries = []
        self.query_results = {}

    async def execute_query(self, query: str, params=None):
        self.queries.append(("execute", query, params))
        if "INSERT" in query or "UPDATE" in query:
            return self.query_results.get("mutation", [{"id": "baseline-123"}])
        if "SELECT" in query:
            return self.query_results.get("select", [])
        return self.query_results.get("default", [])

    async def fetch_one(self, query: str, params=None):
        self.queries.append(("fetch_one", query, params))
        return self.query_results.get("fetch_one")


# --- 1.1 Metrics collection ---


@pytest.mark.asyncio
async def test_collect_stage_metrics_buffers_processing_result():
    """Test collect_stage_metrics() buffers metrics from ProcessingResult."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    result = ProcessingResult(
        success=True,
        processor="classification",
        status=ProcessingStatus.COMPLETED,
        data={},
        metadata={"document_id": "doc-1", "correlation_id": "req-1"},
        processing_time=1.234,
    )
    await collector.collect_stage_metrics("classification", result)
    assert "classification" in collector._metrics_buffer
    assert collector._metrics_buffer["classification"] == [1.234]
    assert "classification" in collector._outcomes_buffer
    assert collector._outcomes_buffer["classification"] == [True]


@pytest.mark.asyncio
async def test_collect_stage_metrics_records_success_and_failure():
    """Test that both success and failure outcomes are recorded for rate calculation."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    result_ok = ProcessingResult(
        success=True,
        processor="classification",
        status=ProcessingStatus.COMPLETED,
        data={},
        metadata={"document_id": "doc-1"},
        processing_time=1.0,
    )
    result_fail = ProcessingResult(
        success=False,
        processor="classification",
        status=ProcessingStatus.FAILED,
        data={},
        metadata={"document_id": "doc-2"},
        processing_time=0.5,
        error=Exception("test error"),
    )
    await collector.collect_stage_metrics("classification", result_ok)
    await collector.collect_stage_metrics("classification", result_fail)
    assert collector._metrics_buffer["classification"] == [1.0, 0.5]
    assert collector._outcomes_buffer["classification"] == [True, False]


@pytest.mark.asyncio
async def test_collect_db_query_metrics():
    """Test collect_db_query_metrics() buffers DB query timing."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    await collector.collect_db_query_metrics("get_chunks", 0.05)
    await collector.collect_db_query_metrics("get_chunks", 0.06)
    assert collector._db_buffer["get_chunks"] == [0.05, 0.06]


@pytest.mark.asyncio
async def test_collect_api_response_metrics():
    """Test collect_api_response_metrics() buffers API timing."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    await collector.collect_api_response_metrics("ollama_embed", 0.8)
    await collector.collect_api_response_metrics("ollama_embed", 0.9)
    assert collector._api_buffer["ollama_embed"] == [0.8, 0.9]


# --- 1.2 Metrics aggregation ---


@pytest.mark.asyncio
async def test_aggregate_metrics_empty_returns_zeros():
    """Test aggregate_metrics() with empty list returns zeros."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    out = await collector.aggregate_metrics("test", [])
    assert out == {
        "avg_seconds": 0.0,
        "p50_seconds": 0.0,
        "p95_seconds": 0.0,
        "p99_seconds": 0.0,
    }


@pytest.mark.asyncio
async def test_aggregate_metrics_single_value():
    """Test aggregate_metrics() with single value."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    out = await collector.aggregate_metrics("test", [2.5])
    assert out["avg_seconds"] == 2.5
    assert out["p50_seconds"] == 2.5
    assert out["p95_seconds"] == 2.5
    assert out["p99_seconds"] == 2.5


@pytest.mark.asyncio
async def test_aggregate_metrics_rounding_three_decimals():
    """Test that aggregates are rounded to 3 decimal places."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    durations = [1.1111, 2.2222, 3.3333, 4.4444, 5.5555]
    out = await collector.aggregate_metrics("test", durations)
    for key in ("avg_seconds", "p50_seconds", "p95_seconds", "p99_seconds"):
        assert isinstance(out[key], float)
        s = str(out[key]).split(".")
        assert len(s) == 2 and len(s[1]) <= 3


@pytest.mark.asyncio
async def test_aggregate_metrics_sample_sizes():
    """Test aggregate_metrics() with < 5, 5-100, > 100 samples."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    # < 5: p95/p99 use max
    out_small = await collector.aggregate_metrics("small", [1.0, 2.0, 3.0])
    assert out_small["p95_seconds"] == 3.0 and out_small["p99_seconds"] == 3.0
    # 5-100
    mid = list(range(1, 50))
    out_mid = await collector.aggregate_metrics("mid", [float(x) for x in mid])
    assert out_mid["avg_seconds"] == 25.0
    assert 1 <= out_mid["p95_seconds"] <= 49
    # > 100: quantiles are interpolated, so p95/p99 in expected range
    large = [float(i) for i in range(1, 101)]
    out_large = await collector.aggregate_metrics("large", large)
    assert out_large["avg_seconds"] == 50.5
    assert 90 <= out_large["p95_seconds"] <= 100
    assert 95 <= out_large["p99_seconds"] <= 100


# --- 1.3 Buffer flushing ---


@pytest.mark.asyncio
async def test_flush_metrics_buffer_all_stages():
    """Test flush_metrics_buffer() clears stage buffer and returns aggregates with success/failure counts."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    collector._metrics_buffer["classification"] = [1.0, 2.0, 3.0]
    collector._outcomes_buffer["classification"] = [True, True, False]
    collector._metrics_buffer["chunking"] = [0.5, 0.5]
    collector._outcomes_buffer["chunking"] = [True, True]
    out = await collector.flush_metrics_buffer()
    assert "classification" in out and "chunking" in out
    assert out["classification"]["avg_seconds"] == 2.0
    assert out["classification"]["success_count"] == 2
    assert out["classification"]["failure_count"] == 1
    assert out["classification"]["success_rate"] == pytest.approx(2 / 3)
    assert out["chunking"]["avg_seconds"] == 0.5
    assert out["chunking"]["success_count"] == 2
    assert out["chunking"]["failure_count"] == 0
    assert out["chunking"]["success_rate"] == 1.0
    assert len(collector._metrics_buffer) == 0
    assert len(collector._outcomes_buffer) == 0


@pytest.mark.asyncio
async def test_flush_metrics_buffer_single_stage():
    """Test flush_metrics_buffer(stage_name) flushes only that stage."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    collector._metrics_buffer["classification"] = [1.0, 2.0]
    collector._outcomes_buffer["classification"] = [True, True]
    collector._metrics_buffer["chunking"] = [0.5]
    collector._outcomes_buffer["chunking"] = [True]
    out = await collector.flush_metrics_buffer("classification")
    assert list(out.keys()) == ["classification"]
    assert "chunking" in collector._metrics_buffer and len(collector._metrics_buffer["chunking"]) == 1
    assert "classification" not in collector._metrics_buffer


@pytest.mark.asyncio
async def test_flush_db_buffer():
    """Test flush_db_buffer() aggregates and clears DB buffer."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    collector._db_buffer["get_chunks"] = [0.1, 0.2, 0.3]
    out = await collector.flush_db_buffer()
    assert "get_chunks" in out
    assert out["get_chunks"]["avg_seconds"] == 0.2
    assert "get_chunks" not in collector._db_buffer


@pytest.mark.asyncio
async def test_flush_api_buffer():
    """Test flush_api_buffer() aggregates and clears API buffer."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    collector._api_buffer["ollama_embed"] = [0.5, 1.0]
    out = await collector.flush_api_buffer()
    assert "ollama_embed" in out
    assert out["ollama_embed"]["avg_seconds"] == 0.75
    assert "ollama_embed" not in collector._api_buffer


# --- 2.1 Baseline storage ---


@pytest.mark.asyncio
async def test_store_baseline_inserts():
    """Test store_baseline() inserts baseline record."""
    adapter = MockDatabaseAdapter()
    adapter.query_results["mutation"] = [{"id": "baseline-1"}]
    collector = PerformanceCollector(adapter)
    metrics = {
        "avg_seconds": 1.234,
        "p50_seconds": 1.1,
        "p95_seconds": 2.5,
        "p99_seconds": 3.0,
    }
    ok = await collector.store_baseline(
        "classification",
        metrics,
        test_document_ids=["doc-1", "doc-2"],
        notes="Baseline after optimization",
    )
    assert ok is True
    assert any("INSERT" in q[1] and "performance_baselines" in q[1] for q in adapter.queries)


@pytest.mark.asyncio
async def test_store_baseline_validates_metrics():
    """Test store_baseline() rejects invalid metrics."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    ok = await collector.store_baseline(
        "classification",
        {"avg_seconds": 1.0},  # missing p50, p95, p99
        ["doc-1"],
        None,
    )
    assert ok is False
    assert len(adapter.queries) == 0


@pytest.mark.asyncio
async def test_store_baseline_db_and_api_prefixes():
    """Test store_baseline() with db__ and api__ prefixes (structure only)."""
    adapter = MockDatabaseAdapter()
    adapter.query_results["mutation"] = [{"id": "x"}]
    collector = PerformanceCollector(adapter)
    metrics = {
        "avg_seconds": 0.1,
        "p50_seconds": 0.1,
        "p95_seconds": 0.15,
        "p99_seconds": 0.2,
    }
    await collector.store_baseline("db__get_chunks", metrics, ["doc-1"], "DB baseline")
    await collector.store_baseline("api__ollama_embed", metrics, ["doc-1"], "API baseline")
    assert len(adapter.queries) >= 2


# --- 2.2 Current metrics update ---


@pytest.mark.asyncio
async def test_update_current_metrics():
    """Test update_current_metrics() updates baseline and improvement_percentage in DB."""
    adapter = MockDatabaseAdapter()
    adapter.query_results["mutation"] = [{"id": "updated-1"}]
    collector = PerformanceCollector(adapter)
    metrics = {
        "avg_seconds": 0.9,
        "p50_seconds": 0.85,
        "p95_seconds": 1.8,
        "p99_seconds": 2.0,
    }
    ok = await collector.update_current_metrics("classification", metrics)
    assert ok is True
    assert any("UPDATE" in q[1] and "improvement_percentage" in q[1] for q in adapter.queries)


@pytest.mark.asyncio
async def test_update_current_metrics_no_result_returns_false():
    """Test update_current_metrics() returns False when no baseline found."""
    adapter = MockDatabaseAdapter()
    adapter.query_results["mutation"] = []
    collector = PerformanceCollector(adapter)
    metrics = {
        "avg_seconds": 0.9,
        "p50_seconds": 0.85,
        "p95_seconds": 1.8,
        "p99_seconds": 2.0,
    }
    ok = await collector.update_current_metrics("classification", metrics)
    assert ok is False


# --- 2.3 Improvement calculation ---


@pytest.mark.asyncio
async def test_calculate_improvement_returns_none_when_no_baseline():
    """Test calculate_improvement() returns None when no baseline."""
    adapter = MockDatabaseAdapter()
    adapter.query_results["fetch_one"] = None
    collector = PerformanceCollector(adapter)
    out = await collector.calculate_improvement("classification")
    assert out is None


@pytest.mark.asyncio
async def test_calculate_improvement_returns_all_percentages():
    """Test calculate_improvement() returns avg, p50, p95, p99 and overall_improvement_percent."""
    adapter = MockDatabaseAdapter()
    adapter.query_results["fetch_one"] = {
        "baseline_avg_seconds": 2.0,
        "current_avg_seconds": 1.6,
        "baseline_p50_seconds": 1.8,
        "current_p50_seconds": 1.5,
        "baseline_p95_seconds": 3.0,
        "current_p95_seconds": 2.4,
        "baseline_p99_seconds": 3.5,
        "current_p99_seconds": 2.8,
        "improvement_percentage": 20.0,
    }
    collector = PerformanceCollector(adapter)
    out = await collector.calculate_improvement("classification")
    assert out is not None
    assert out["stage_name"] == "classification"
    assert out["overall_improvement_percent"] == 20.0
    assert "improvement_avg_percent" in out
    assert "improvement_p50_percent" in out
    assert "improvement_p95_percent" in out
    assert "improvement_p99_percent" in out


@pytest.mark.asyncio
async def test_format_improvement_percent():
    """Test _format_improvement_percent() produces +/- and 2 decimals."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    assert collector._format_improvement_percent(15.23) == "+15.23%"
    assert collector._format_improvement_percent(-5.67) == "-5.67%"
    assert collector._format_improvement_percent(None) == "N/A"


# --- Clear buffer ---


def test_clear_buffer():
    """Test clear_buffer() clears all buffers."""
    adapter = MockDatabaseAdapter()
    collector = PerformanceCollector(adapter)
    collector._metrics_buffer["a"] = [1.0]
    collector._outcomes_buffer["a"] = [True]
    collector._db_buffer["b"] = [2.0]
    collector._api_buffer["c"] = [3.0]
    collector.clear_buffer()
    assert len(collector._metrics_buffer) == 0
    assert len(collector._outcomes_buffer) == 0
    assert len(collector._db_buffer) == 0
    assert len(collector._api_buffer) == 0
