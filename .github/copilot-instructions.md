# GitHub Copilot Instructions for KRAI

KRAI (Knowledge Retrieval and Intelligence) is a multimodal AI document processing pipeline. It ingests technical PDFs, extracts text/images/tables/links, classifies content by manufacturer/product, generates embeddings, and indexes everything for semantic search.

**Stack:** FastAPI (Python) · PostgreSQL 15+ with pgvector · MinIO (object storage) · Ollama (local LLM/embeddings) · Laravel 12 + Filament 4 (dashboard UI at `laravel-admin/`)

---

## Commands

```bash
# Start infrastructure (PostgreSQL, MinIO, Redis, Ollama)
docker-compose -f docker-compose.simple.yml up -d

# Run backend API (dev with reload)
python -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000

# All tests
python -m pytest backend/tests/ -v

# Single test file
python -m pytest backend/tests/integration/test_link_enrichment_e2e.py -v

# Tests by marker
python -m pytest backend/tests/ -v -m "processor and not slow"
python -m pytest backend/tests/ -v -m "unit"
python -m pytest backend/tests/ -v -m "postgresql"

# With coverage
python -m pytest backend/tests/ --cov=backend --cov-report=html

# Validate environment
python scripts/validate_env.py --verbose

# Production stack
docker-compose -f docker-compose.production.yml up --build -d
# Benchmarks/staging ONLY (never production)
docker-compose -f docker-compose.staging.yml up -d
```

Test discovery paths (from `pytest.ini`): `backend/tests`, `tests/processors`, `tests/verification`.

---

## Pipeline Architecture

The 16-stage pipeline is orchestrated by `KRMasterPipeline` in `backend/pipeline/master_pipeline.py`:

```
UPLOAD → TEXT_EXTRACTION → TABLE_EXTRACTION → SVG_PROCESSING → IMAGE_PROCESSING
→ VISUAL_EMBEDDING → LINK_EXTRACTION → VIDEO_ENRICHMENT → CHUNK_PREPROCESSING
→ CLASSIFICATION → METADATA_EXTRACTION → PARTS_EXTRACTION → SERIES_DETECTION
→ STORAGE → EMBEDDING → SEARCH_INDEXING
```

- Each processor lives in `backend/processors/` and inherits from `BaseProcessor` (`backend/core/base_processor.py`)
- Processing is invoked via `safe_process()` — **never** implement custom retry loops
- All processors **must** be registered unconditionally in `master_pipeline.py`'s `self.processors` dict; processors handle their own enabled/disabled state internally. A `None` processor causes "Processor not available for stage" errors.

---

## Database

Six PostgreSQL schemas — **always read `DATABASE_SCHEMA.md` before writing queries**:

| Schema | Purpose |
|---|---|
| `krai_core` | documents, products, manufacturers, series |
| `krai_intelligence` | chunks (with `embedding vector(768)`), error_codes, solutions |
| `krai_content` | images, links, videos, tables |
| `krai_parts` | parts_catalog, accessories |
| `krai_system` | alerts, retries, metrics, stage_tracking |
| `krai_users` | users |

Views use `vw_` prefix in the `public` schema. `vw_embeddings` is an alias for `vw_chunks`.

**Known column name traps** (historically caused bugs):

| Wrong | Correct | Table |
|---|---|---|
| `chunk_text` | `text_chunk` | `krai_intelligence.chunks` |
| `enrichment_error` | `metadata->>'enrichment_error'` | `krai_content.videos` (JSONB, no column) |
| `tags` | `metadata->>'tags'` | `krai_content.videos` (JSONB, no column) |

Migrations go in `database/migrations_postgresql/` as sequential SQL files (currently up to `023_*.sql`).

To update `DATABASE_SCHEMA.md` after schema changes:
```bash
cd scripts && python generate_db_doc_from_csv.py
```

---

## Key Conventions

### Error Handling

- Raise `ProcessingError` from `backend/processors/exceptions.py` with processor name and original exception
- Classify errors via `ErrorClassifier` (`backend/core/retry_engine.py`):
  - **Transient** (will retry): HTTP 5xx, 429, `ConnectionError`, `TimeoutError`, DB connection errors
  - **Permanent** (no retry): HTTP 4xx, `ValidationError`, `AuthenticationError`, malformed input
- Never use `time.sleep()` for retry delays — `safe_process()` handles hybrid sync/async retry
- Acquire PostgreSQL advisory locks **always** in try-finally blocks

### Logging & Correlation IDs

Every log entry must include a correlation ID in format: `req_{uuid}.stage_{name}.retry_{n}`

### Notifications

Queue alerts via `AlertService.queue_alert()` — never send emails/Slack directly.

### Manufacturer Name Mapping

Manufacturer names must be normalized before any DB lookup. Key mappings:

```python
manufacturer_name_mapping = {
    'HP Inc.': 'Hewlett Packard',
    'HP': 'Hewlett Packard',
    'Hewlett-Packard': 'Hewlett Packard',
    'Brother Industries': 'Brother',
    'Konica Minolta Business Solutions': 'Konica Minolta',
}
```

Use `ManufacturerVerificationService` (`backend/services/manufacturer_verification_service.py`) for lookups.

### Error Code Hierarchy

Error codes in `krai_intelligence.error_codes` use two columns added in migration 018:
- `parent_code` — references the parent category's `error_code` value
- `is_category` — `true` for category/grouping entries

Manufacturer regex patterns and hierarchy rules live in `backend/config/error_code_patterns.json`. Hierarchy strategies: `first_n_segments` (HP, Xerox) or `prefix_digits` (Konica Minolta, Ricoh).

### Idempotency

Check `stage_completion_markers` before processing. Compute SHA-256 data hash for duplicate detection. Set completion markers after successful processing.

### Commit Messages

Format: `[Component] What was changed`  
Example: `[Pipeline] Add idempotency checks to ChunkPreprocessor`

### Test File Naming

- `test_*.py` — unit/integration tests
- `test_*_integration.py` — explicit integration tests  
- `test_*_e2e.py` — end-to-end tests
- `check_*.py` — verification scripts (not collected by pytest)

### Never Do

- Implement custom retry loops (use `safe_process()`)
- Guess DB column/table names (check `DATABASE_SCHEMA.md`)
- Run benchmarks against production (use staging)
- Conditionally set a processor to `None` in `master_pipeline.py`
- Catch generic `Exception` without re-raising as `ProcessingError`
- Acquire advisory locks without try-finally
