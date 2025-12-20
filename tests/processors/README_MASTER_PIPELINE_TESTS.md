# Master Pipeline Test Suite (KRMasterPipeline)

This document describes the pytest-based test suite for the KRAI master
pipeline (`KRMasterPipeline`). It focuses on orchestration, smart
processing, batch/concurrency behaviour, error recovery and stage/status
tracking.

## Test Files

- `tests/processors/test_master_pipeline.py`
  - Unit/config tests for `KRMasterPipeline` helpers
  - Initialization and service wiring
  - Processor registry coverage for all core stages
  - `run_single_stage` / `run_stages` behaviour
  - `get_available_stages` and invalid-stage handling

- `tests/processors/test_master_pipeline_e2e.py`
  - E2E-style tests on top of mocks
  - `process_single_document_full_pipeline` for new documents
  - Duplicate upload path → `process_document_smart_stages`
  - Smart-processing of missing stages only (based on DB-derived status)

- `tests/processors/test_master_pipeline_batch.py`
  - Batch and concurrency tests for
    `process_batch_hardware_waker`
  - All-success path (aggregation of results)
  - Concurrency limit enforcement via semaphore
  - Mixed success/failure/exception scenarios

- `tests/processors/test_master_pipeline_error_recovery.py`
  - Error handling for `run_single_stage` when processors raise
  - Upload failure path in
    `process_single_document_full_pipeline`
  - Exceptions in later stages bubbling up as clean error dicts

- `tests/processors/test_master_pipeline_status.py`
  - `get_document_stage_status` flags derived from DB adapter
  - `get_stage_status` view-based status lookup
  - Smart-processing status + quality handling
  - Document status updates (`completed` / `failed`)

- `backend/tests/integration/test_full_pipeline_integration.py`
  - Existing full-pipeline integration tests (text/chunks/SVG/tables/context/embeddings/search)
  - **New tests** using the real `KRMasterPipeline` (`test_pipeline` fixture):
    - Full document run via `process_single_document_full_pipeline`
    - Smart reprocessing via `process_document_smart_stages`
    - Stage-status verification via `get_stage_status`

## Fixtures

The master pipeline tests reuse and extend the shared processor fixtures
in `tests/processors/conftest.py`:

- `mock_database_adapter`
  - In-memory implementation of the database layer
  - Documents, chunks, links, images and embeddings are stored in
    Python dicts/lists
- `mock_storage_service`
- `mock_ai_service`
- `mock_quality_service`
  - Lightweight stand-in for `QualityCheckService`
  - Always returns a passing quality result with a deterministic score
- `mock_master_pipeline`
  - `KRMasterPipeline` wired entirely against the mock services
  - Processor registry filled with stub processors that return simple,
    deterministic `ProcessingResult`-like objects

Integration tests use the fixtures from
`backend/tests/integration/conftest.py`:

- `test_database` – real PostgreSQL test database
- `test_storage` – object storage service (MinIO/S3)
- `test_ai_service` – AI/embedding backend
- `test_pipeline` – `KRMasterPipeline` fully initialized against the
  real test services
- `sample_test_document` – PDF metadata and file path for integration
  runs

## Pytest Markers

The following markers are used by the master-pipeline-related tests and
are registered in `pytest.ini`:

- `master_pipeline` – all tests that exercise the `KRMasterPipeline`
- `batch` – batch processing and hardware-waker tests
- `concurrency` – semaphore/enforced parallelism behaviour
- `error_recovery` – error handling and recovery scenarios
- `status_tracking` – stage/status tracking and quality checks
- `unit` – fast, isolated tests (e.g. configuration helpers)
- `e2e` – heavier end-to-end style tests on top of mocks
- `integration` / `slow` – full integration runs against real services

## How to Run

Some useful command lines (from the project root):

- Run all master-pipeline unit + config tests:

  ```bash
  pytest tests/processors/test_master_pipeline.py -m "master_pipeline and unit"
  ```

- Run E2E-style master-pipeline tests (mocked services):

  ```bash
  pytest tests/processors/test_master_pipeline_e2e.py -m "master_pipeline and e2e"
  ```

- Run batch/concurrency tests only:

  ```bash
  pytest tests/processors/test_master_pipeline_batch.py -m "master_pipeline and batch"
  ```

- Run error-recovery tests only:

  ```bash
  pytest tests/processors/test_master_pipeline_error_recovery.py -m "master_pipeline and error_recovery"
  ```

- Run status/quality tests only:

  ```bash
  pytest tests/processors/test_master_pipeline_status.py -m "master_pipeline and status_tracking"
  ```

- Run all master-pipeline tests (processors + integration):

  ```bash
  pytest -m "master_pipeline"
  ```

- Run full integration tests including KRMasterPipeline end-to-end:

  ```bash
  pytest backend/tests/integration/test_full_pipeline_integration.py -m "integration and slow"
  ```

## Notes

- Processor-level tests are designed to be fast and deterministic by
  default. They should not hit real external services.
- Integration tests (`backend/tests/integration`) require a running
  PostgreSQL test database and object storage.
- Use markers to keep the default local test runs fast (for example,
  run only `unit` or `master_pipeline and not integration`).
