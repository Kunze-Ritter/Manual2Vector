# Verification Report: Error Handling and Resilience

## Executive Summary

The KRAI pipeline resilience infrastructure is built on four core components: **RetryEngine** (hybrid sync/async retry with exponential backoff), **ErrorLoggingService** (dual-target logging to PostgreSQL and JSON), **IdempotencyChecker** (SHA-256 hash-based duplicate prevention), and **StageTracker** (PostgreSQL RPC-based stage status). This report documents verification of the database schema, component tests, integration behaviour, transient/permanent error handling, advisory locks, and correlation ID tracking. Verification scripts and an operational runbook are provided for ongoing validation and operations.

**Overall status:** Schema and components are verified via automated scripts and pytest. Manual simulation steps are documented for transient/permanent error scenarios.

---

## Database Schema Verification

**Objective:** Confirm migration 008 is applied and all required tables, indexes, and RPC functions exist.

**Verification script:** `scripts/verify_error_handling_schema.py`

**Checks performed:**
- Migration `008_pipeline_resilience_schema` present in `krai_system.migrations` with description referencing stage_completion_markers and pipeline_errors
- Table `krai_system.stage_completion_markers` with columns: document_id, stage_name, completed_at, data_hash, metadata
- Table `krai_system.pipeline_errors` with columns: error_id, document_id, stage_name, error_type, error_category, error_message, stack_trace, context, retry_count, max_retries, status, is_transient, correlation_id, next_retry_at, resolved_at, resolved_by, resolution_notes
- Table `krai_system.retry_policies` with expected columns and default policies for firecrawl, database, ollama, minio
- Indexes on pipeline_errors: idx_pipeline_errors_document, idx_pipeline_errors_stage, idx_pipeline_errors_status, idx_pipeline_errors_correlation
- Indexes on stage_completion_markers: idx_completion_markers_document, idx_completion_markers_stage
- RPC functions in krai_core: start_stage, complete_stage, fail_stage, update_stage_progress
- RPC execution test: create test document, start_stage → update_stage_progress → complete_stage, then fail_stage on second stage; verify stage_status JSONB and error_message updated; cleanup test document

**Expected results:** All checks pass; default retry policies seeded; RPCs update documents.stage_status correctly.

---

## Component Test Results

### ErrorClassifier

- **Test command:** `pytest backend/tests/test_retry_engine.py::TestErrorClassifier -v --tb=short`
- **Transient:** HTTP 5xx, 408, 429; ConnectionError; TimeoutError; asyncio.TimeoutError; httpx.TimeoutException, ConnectError
- **Permanent:** HTTP 4xx (except 408/429); ValueError; AuthenticationError; AuthorizationError; unknown types (fail-safe)
- **Nested exceptions:** Classification traverses __cause__ chain

### RetryPolicyManager

- **Test command:** `pytest backend/tests/test_retry_engine.py::TestRetryPolicyManager -v --tb=short`
- Cache key format: `{service_name}:{stage_name or '*'}`
- Code-level defaults: firecrawl (3 retries, 2s base), database (5, 1s), ollama (3, 2s), minio (4, 1.5s), default (3, 1s)
- Single-flight pattern for concurrent policy loading; cache invalidation via clear_cache()

### RetryOrchestrator

- **Test command:** `pytest backend/tests/test_retry_engine.py::TestRetryOrchestrator -v --tb=short`
- Correlation ID format: `{request_id}.stage_{stage_name}.retry_{retry_attempt}`
- Exponential backoff: min(base_delay * exp_base^attempt, max_delay); jitter ±20% when enabled
- Advisory lock: pg_try_advisory_lock(lock_id), lock_id = SHA256(document_id:stage_name)[:8] % (2^63-1)
- Background retry: asyncio.create_task(_background_retry_task); lock acquired before retry, released in finally

### ErrorLogger

- **Test command:** `pytest backend/tests/test_error_logging.py -v --tb=short`
- Dual target: INSERT into krai_system.pipeline_errors; StructuredLogger.log_error() for JSON
- Error ID format: err_{16 hex chars}; correlation_id stored and queryable
- update_error_status(), mark_error_resolved(); context sanitization for sensitive fields

### IdempotencyChecker

- **Test command:** `pytest backend/tests/test_idempotency.py -v --tb=short`
- compute_context_hash() / compute_data_hash(): SHA-256 of document_id, file_path, file_hash, file_size, manufacturer, model, series, version
- check_completion_marker(), set_completion_marker() (upsert); cleanup_old_data()

### StageTracker

- **Test command:** `pytest tests/test_stage_tracker.py -v --tb=short`
- start_stage, update_progress, complete_stage, fail_stage, skip_stage → krai_core.* RPCs
- stage_status JSONB updated; progress normalized 0–100; graceful degradation when RPC missing

---

## Integration Test Results

### BaseProcessor (safe_process)

- **Test command:** `pytest backend/tests/test_retry_engine.py::TestBaseProcessorIntegration -v --tb=short`
- Hybrid retry: first retry synchronous, subsequent async (background tasks)
- Idempotency check before process; completion marker set on success; advisory lock prevents concurrent retries
- Error classification and ErrorLogger integration; request_id auto-generated when missing; max retries exceeded → status FAILED, resolution_notes set

---

## Transient Error Simulation Results

**Script:** `scripts/test_transient_errors.py` (runs pytest and/or prints simulation steps)

- Ollama down: ConnectionError → transient → retry with backoff; restart → retry succeeds
- MinIO down: same pattern for storage stage
- PostgreSQL timeout: TimeoutError → transient → retry
- HTTP 503/429: classified transient; retry with backoff
- Retry exhaustion: max_retries=2 → attempts 0,1,2 → status failed, resolution_notes set
- Correlation IDs: req_{id}.stage_{name}.retry_0, retry_1, retry_2
- Advisory lock: second attempt for same document/stage while retry in progress returns retry_in_progress

---

## Permanent Error Handling Results

**Script:** `scripts/test_permanent_errors.py`

- ValueError, HTTP 401/403, FileNotFoundError, ValidationError → permanent; no retry
- Error logged with is_transient=False, status=failed, retry_count=0
- Correlation ID: single req_{id}.stage_{name}.retry_0

---

## Advisory Lock Behavior Results

**Script:** `scripts/test_advisory_locks.py`

- Lock ID deterministic from SHA256(document_id:stage_name), within bigint range
- pg_try_advisory_lock / pg_advisory_unlock; second acquisition fails while first holds; release in finally
- Session-based locks: process crash releases locks; pg_locks shows advisory locks when held

---

## Correlation ID Tracking Results

**Script:** `scripts/test_correlation_ids.py`

- Format: `{request_id}.stage_{stage_name}.retry_{retry_attempt}`
- Stored in pipeline_errors.correlation_id and JSON logs; queryable by prefix (e.g. WHERE correlation_id LIKE 'req_<id>%')
- Retry chain linked by same request_id and incrementing retry_attempt

---

## Known Issues and Workarounds

- **Ollama connection errors:** Restart Ollama (e.g. `docker start ollama` or `systemctl start ollama`)
- **MinIO upload errors:** Check MinIO service and OBJECT_STORAGE_* credentials
- **PostgreSQL connection pool exhaustion:** Increase pool size or reduce concurrency
- **Advisory lock leaks:** Query `pg_locks WHERE locktype = 'advisory'`; session end releases locks automatically
- **Stuck retries:** Update status to failed after timeout (see Operational Runbook)

---

## Performance Benchmarks

- Retry overhead: dominated by backoff delay and one DB round-trip per lock/status update
- Advisory lock: single pg_try_advisory_lock call
- Error logging: one INSERT (pipeline_errors) plus JSON write per error
- Idempotency: one SELECT for check; one INSERT/UPDATE for set_completion_marker

---

## Test Execution Commands

| Purpose | Command |
|--------|--------|
| Schema verification | `python scripts/verify_error_handling_schema.py` |
| ErrorClassifier | `pytest backend/tests/test_retry_engine.py::TestErrorClassifier -v --tb=short` |
| RetryPolicyManager | `pytest backend/tests/test_retry_engine.py::TestRetryPolicyManager -v --tb=short` |
| RetryOrchestrator | `pytest backend/tests/test_retry_engine.py::TestRetryOrchestrator -v --tb=short` |
| ErrorLogger | `pytest backend/tests/test_error_logging.py -v --tb=short` |
| IdempotencyChecker | `pytest backend/tests/test_idempotency.py -v --tb=short` |
| StageTracker | `pytest tests/test_stage_tracker.py -v --tb=short` |
| BaseProcessor integration | `pytest backend/tests/test_retry_engine.py::TestBaseProcessorIntegration -v --tb=short` |
| Transient errors (script) | `python scripts/test_transient_errors.py` |
| Permanent errors (script) | `python scripts/test_permanent_errors.py` |
| Advisory locks (script) | `python scripts/test_advisory_locks.py` |
| Correlation IDs (script) | `python scripts/test_correlation_ids.py` |

---

## Verification Checklist

- [x] Database schema verified (tables, indexes, RPC functions)
- [x] ErrorClassifier tests (transient/permanent classification)
- [x] RetryPolicyManager tests (caching, fallback, single-flight)
- [x] RetryOrchestrator tests (backoff, locks, background retries)
- [x] ErrorLogger tests (dual-target logging, correlation IDs)
- [x] IdempotencyChecker tests (hash, markers, cleanup)
- [x] StageTracker tests (RPC, WebSocket, graceful degradation)
- [x] BaseProcessor integration tests (safe_process orchestration)
- [x] Transient error simulation documented and scripted
- [x] Permanent error handling verified
- [x] Advisory locks prevent concurrent retries
- [x] Correlation ID format and tracking verified
- [x] Verification report created
- [x] Operational runbook created (see docs/OPERATIONAL_RUNBOOK_ERROR_HANDLING.md)
