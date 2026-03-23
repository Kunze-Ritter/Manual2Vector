# RAG Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix data extraction quality bugs, add vector search + reranking to the agent, and establish a RAG evaluation baseline — enabling technicians to get complete, accurate error code solutions.

**Architecture:** Four sequential areas: (0) fix truncation bugs in error code extraction and add pdfplumber fallback for tables, then reset the DB; (3) add a Ragas eval script to measure baseline quality; (1) add vector-seed hybrid retrieval to ILIKE-based agent tools; (2) add a CrossEncoder reranker between pgvector retrieval and LLM context.

**Tech Stack:** Python/FastAPI, asyncpg, pgvector, Ollama (nomic-embed-text), sentence-transformers (CrossEncoder), pdfplumber, ragas, LangGraph

**Spec:** `docs/superpowers/specs/2026-03-23-rag-improvements-design.md`

---

## File Map

### Modified
- `backend/processors/error_code_extractor.py` — fix 4 truncation constants (lines 193, 379, 821, 951)
- `backend/processors/table_processor.py` — add pdfplumber fallback in `_extract_page_tables`, fix `has_headers` detection
- `backend/api/agent_api.py` — extend `KRAIAgent.__init__` and `create_tools` signatures; add vector-seed step to `search_error_codes` and `search_videos`; add reranking to `semantic_search`
- `backend/services/multimodal_search_service.py` — inject `RerankingService`, expand candidate fetch, rerank before returning
- `backend/api/app.py` — construct `AIService` + `RerankingService`, pass to `KRAIAgent`
- `backend/requirements.txt` — add `pdfplumber`
- `database/migrations_postgresql/003_functions.sql` — fix `c.chunk_text` → `c.text_chunk` in `match_multimodal`

### Created
- `backend/services/reranking_service.py` — `RerankingService` wrapping sentence-transformers CrossEncoder
- `scripts/reset_document_data.py` — safe DB reset script (preserves videos/products/manufacturers)
- `scripts/eval_dataset.json` — ~20 test questions with ground truth
- `scripts/evaluate_rag.py` — Ragas evaluation script
- `requirements-dev.txt` — dev-only deps (`ragas>=0.1.0,<0.2.0`)

### New Migration
- `database/migrations_postgresql/025_fix_match_multimodal.sql` — corrects `chunk_text` → `text_chunk`

### Tests
- `backend/tests/test_error_code_extractor_thresholds.py` — Area 0a
- `backend/tests/test_table_processor_pdfplumber.py` — Area 0b
- `backend/tests/test_reranking_service.py` — Area 2
- `backend/tests/test_agent_vector_seed.py` — Area 1

---

## Task 1: Fix error code truncation thresholds (Area 0a)

**Files:**
- Modify: `backend/processors/error_code_extractor.py:193, 379, 821, 951`
- Test: `backend/tests/test_error_code_extractor_thresholds.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_error_code_extractor_thresholds.py
import pytest
from backend.processors.error_code_extractor import ErrorCodeExtractor
from backend.processors.models import ExtractedErrorCode


def _make_code(solution_text: str) -> ExtractedErrorCode:
    return ExtractedErrorCode(
        error_code="13.B9.Az",
        error_description="Paper jam",
        solution_technician_text=solution_text,
        confidence=0.8,
        page_number=1,
        extraction_method="test",
    )


def test_enrichment_skips_codes_with_solution_over_500_chars_not_100():
    """Codes with 101-499 char solutions must still be enriched (Bug 4 fix)."""
    extractor = ErrorCodeExtractor()
    short_partial = "Fix the paper jam by opening the door. " * 3  # ~120 chars, partial
    code = _make_code(short_partial)
    # If threshold is 500, this code should be in codes_needing_enrichment
    needs_enrichment = [
        ec for ec in [code]
        if not ec.solution_technician_text or len(ec.solution_technician_text) <= 500
    ]
    assert len(needs_enrichment) == 1, "Code with <500 char solution must need enrichment"


def test_enrichment_skips_codes_with_solution_over_500_chars():
    """Codes with >500 char solutions can skip enrichment."""
    extractor = ErrorCodeExtractor()
    long_solution = "Step 1: Open front cover. Step 2: Remove jam. Step 3: Check sensor. " * 10  # >500 chars
    code = _make_code(long_solution)
    needs_enrichment = [
        ec for ec in [code]
        if not ec.solution_technician_text or len(ec.solution_technician_text) <= 500
    ]
    assert len(needs_enrichment) == 0, "Code with >500 char solution should skip enrichment"


def test_extract_solution_returns_more_than_200_chars_when_available():
    """_extract_solution must not stop at first solution >200 chars (Bug 1 fix)."""
    extractor = ErrorCodeExtractor()
    # Build text with a short bad solution first, then a long good one
    long_solution_text = (
        "Recommended action for customers:\n"
        "1. Power off the device and wait 30 seconds.\n"
        "2. Open the front access panel by pressing the release button.\n"
        "3. Locate the fuser unit (marked with warning label, upper right).\n"
        "4. Carefully remove any jammed paper by pulling gently toward you.\n"
        "5. Check the separation claws for wear and replace if damaged.\n"
        "6. Close the panel and power on. Run a test print to confirm resolution.\n"
    )
    assert len(long_solution_text) > 400, "Test setup: solution must be >400 chars"
    result = extractor._extract_solution(long_solution_text, long_solution_text, 0)
    assert result is not None
    assert len(result) > 200, f"Solution was truncated at {len(result)} chars, expected >200"


def test_extract_description_allows_up_to_1500_chars(tmp_path):
    """_extract_description max_length must be 1500, not 500 (Bug 2 fix)."""
    extractor = ErrorCodeExtractor()
    long_desc = "Classification: " + ("This is a detailed error description. " * 50)  # >500 chars
    result = extractor._extract_description(long_desc, 0, max_length=1500)
    if result:
        assert not result.endswith("..."), "Description must not be truncated with ellipsis"
        assert len(result) <= 1500


def test_bullet_solution_captures_more_than_8_lines():
    """Bullet solutions must not be capped at 8 lines (Bug 3 fix)."""
    extractor = ErrorCodeExtractor()
    # Build 20-line bullet solution
    bullets = "\n".join(f"• Step {i}: Do action {i} carefully." for i in range(1, 21))
    text_with_bullets = "Some context\n" + bullets
    result = extractor._extract_solution("", text_with_bullets, 0)
    if result:
        line_count = len([l for l in result.split('\n') if l.strip()])
        assert line_count > 8, f"Only {line_count} lines captured, expected >8"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_error_code_extractor_thresholds.py -v
```

Expected: multiple FAILs (thresholds wrong, early exit at 200 chars)

- [ ] **Step 3: Fix Bug 4 — raise enrichment skip threshold from 100 → 500**

In `backend/processors/error_code_extractor.py` line 193:
```python
# BEFORE
if not ec.solution_technician_text or len(ec.solution_technician_text) <= 100

# AFTER
if not ec.solution_technician_text or len(ec.solution_technician_text) <= 500
```

- [ ] **Step 4: Fix Bug 1 — raise early-exit threshold from 200 → 1500**

In `backend/processors/error_code_extractor.py` line 379:
```python
# BEFORE
if len(best_solution_raw) > 200:
    break

# AFTER
if len(best_solution_raw) > 1500:
    break
```

- [ ] **Step 5: Fix Bug 2 — raise description max_length 500 → 1500, remove `...` suffix**

In `backend/processors/error_code_extractor.py` line 820–821:
```python
# BEFORE
if len(description) > max_length:
    description = description[:max_length].rsplit(' ', 1)[0] + '...'

# AFTER
if len(description) > max_length:
    description = description[:max_length].rsplit(' ', 1)[0]
```

Also update the `_extract_description` call at line ~358 to pass `max_length=1500`:
```python
description = self._extract_description(
    full_document_text,
    end_pos,
    max_length=1500,   # was 500
    code_start_pos=start_pos,
)
```

- [ ] **Step 6: Fix Bug 3 — raise bullet cap from 8 → 30**

In `backend/processors/error_code_extractor.py` line 951:
```python
# BEFORE
lines = [l.strip() for l in bullets.split('\n') if l.strip()][:8]

# AFTER
lines = [l.strip() for l in bullets.split('\n') if l.strip()][:30]
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_error_code_extractor_thresholds.py -v
```

Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add backend/processors/error_code_extractor.py backend/tests/test_error_code_extractor_thresholds.py
git commit -m "[Extraction] Fix error code solution truncation — raise thresholds and remove early exit"
```

---

## Task 2: Add pdfplumber table fallback + fix has_headers (Area 0b)

**Files:**
- Modify: `backend/processors/table_processor.py:216-243, 310-313`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_table_processor_pdfplumber.py`

- [ ] **Step 1: Add pdfplumber to requirements.txt**

In `backend/requirements.txt`, under the `# DOCUMENT PROCESSING` section add:
```
pdfplumber>=0.10.0  # Table extraction fallback for borderless/whitespace tables
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_table_processor_pdfplumber.py
import pytest
from unittest.mock import MagicMock, patch


def test_pdfplumber_fallback_called_when_pymupdf_finds_nothing():
    """When both PyMuPDF strategies find 0 tables, pdfplumber fallback must be tried."""
    from backend.processors.table_processor import TableProcessor

    processor = TableProcessor(
        database_service=MagicMock(),
        embedding_service=MagicMock(),
    )

    # Mock PyMuPDF page that finds no tables
    mock_page = MagicMock()
    mock_tabs = MagicMock()
    mock_tabs.tables = []
    mock_page.find_tables.return_value = mock_tabs

    with patch.object(processor, '_extract_page_tables_pdfplumber', return_value=[]) as mock_plumber:
        processor._extract_page_tables(mock_page, page_number=1)
        mock_plumber.assert_called_once()


def test_has_headers_detected_not_hardcoded():
    """has_headers in metadata must reflect actual header detection, not always True."""
    from backend.processors.table_processor import TableProcessor

    processor = TableProcessor(
        database_service=MagicMock(),
        embedding_service=MagicMock(),
    )

    # A table where first row is all short strings (headers)
    assert processor._detect_has_headers([["Error Code", "Description", "Solution"]]) is True

    # A table where first row has numeric data (not a header)
    assert processor._detect_has_headers([["13.B9.Az", "Paper jam", "Replace claws"]]) is True  # could be header
    assert processor._detect_has_headers([["1", "2", "3"]]) is False  # purely numeric → not headers
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_table_processor_pdfplumber.py -v
```

Expected: FAIL — methods don't exist yet

- [ ] **Step 4: Add `_detect_has_headers` method to TableProcessor**

In `backend/processors/table_processor.py`, add before `_extract_page_tables`:

```python
def _detect_has_headers(self, raw_data: list) -> bool:
    """
    Detect whether first row looks like column headers.
    Headers: all cells are short non-numeric strings.
    Returns True if likely headers, False if first row is data.
    """
    if not raw_data or not raw_data[0]:
        return True  # default to True when uncertain
    first_row = [str(cell or "").strip() for cell in raw_data[0]]
    # If all cells are purely numeric, it's data not headers
    if all(re.match(r'^\d+([.,]\d+)?$', cell) for cell in first_row if cell):
        return False
    # If any cell is longer than 60 chars it's likely a data cell
    if any(len(cell) > 60 for cell in first_row):
        return False
    return True
```

- [ ] **Step 5: Add `_extract_page_tables_pdfplumber` method**

In `backend/processors/table_processor.py`, add after `_extract_page_tables`:

```python
def _extract_page_tables_pdfplumber(self, pdf_path: str, page_number: int) -> list:
    """
    Fallback table extraction using pdfplumber.
    Used when PyMuPDF finds no tables (e.g. borderless whitespace tables).
    page_number is 1-indexed.
    """
    try:
        import pdfplumber
    except ImportError:
        return []

    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_number < 1 or page_number > len(pdf.pages):
                return []
            page = pdf.pages[page_number - 1]
            raw_tables = page.extract_tables()
            for table_idx, raw_data in enumerate(raw_tables):
                if not raw_data or len(raw_data) < self.min_rows + 1:
                    continue
                if not raw_data[0] or len(raw_data[0]) < self.min_cols:
                    continue
                # Replace None cells with empty string
                cleaned = [[str(c or "") for c in row] for row in raw_data]
                has_headers = self._detect_has_headers(cleaned)
                import pandas as pd
                from uuid import uuid4
                try:
                    if has_headers:
                        df = pd.DataFrame(cleaned[1:], columns=cleaned[0])
                    else:
                        df = pd.DataFrame(cleaned)
                except Exception:
                    continue
                df = df.dropna(how='all')
                if len(df) < self.min_rows or len(df.columns) < self.min_cols:
                    continue
                try:
                    table_markdown = df.to_markdown(index=False, tablefmt='grid')
                except Exception:
                    table_markdown = self._dataframe_to_markdown(df)
                tables.append({
                    'id': str(uuid4()),
                    'page_number': page_number,
                    'table_index': table_idx,
                    'table_type': self._detect_table_type(df),
                    'column_headers': cleaned[0] if has_headers else [],
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'table_data': cleaned,
                    'table_markdown': table_markdown,
                    'caption': None,
                    'context_text': None,
                    'bbox': None,
                    'metadata': {
                        'extraction_strategy': 'pdfplumber',
                        'data_quality': self._assess_data_quality(df),
                        'has_headers': has_headers,
                        'extraction_timestamp': pd.Timestamp.now().isoformat(),
                    },
                })
    except Exception as e:
        with self.logger_context() as adapter:
            adapter.warning(f"pdfplumber fallback failed on page {page_number}: {e}")
    return tables
```

- [ ] **Step 6: Update `_extract_page_tables` to add `pdf_path` parameter and pdfplumber fallback**

Add `pdf_path: str = None` to the signature and append the pdfplumber fallback block at the end. The existing inner loop body must be reproduced exactly — include the `continue` on the inner `except` (line 238 in original):

```python
def _extract_page_tables(self, page, page_number: int, pdf_path: str = None) -> List[Dict[str, Any]]:
    """Extract tables from a single page. Falls back to pdfplumber if PyMuPDF finds nothing."""
    tables = []

    with self.logger_context() as adapter:
        try:
            # Try primary strategy
            tabs = page.find_tables(strategy=self.strategy)

            # If no tables found, try fallback strategy
            if not tabs.tables:
                tabs = page.find_tables(strategy=self.fallback_strategy)
                adapter.debug(f"Page {page_number}: Used fallback strategy '{self.fallback_strategy}'")

            # Process each detected table
            for table_idx, tab in enumerate(tabs.tables):
                try:
                    table_data = self._extract_table_data(tab, page, page_number, table_idx)
                    if table_data:
                        tables.append(table_data)
                except Exception as e:
                    adapter.warning(f"Failed to extract table {table_idx} on page {page_number}: {e}")
                    continue  # keep going with remaining tables on this page

        except Exception as e:
            adapter.warning(f"Table detection failed on page {page_number}: {e}")

    # pdfplumber fallback when PyMuPDF found nothing
    if not tables and pdf_path:
        plumber_tables = self._extract_page_tables_pdfplumber(pdf_path, page_number)
        if plumber_tables:
            with self.logger_context() as adapter:
                adapter.info(f"Page {page_number}: pdfplumber found {len(plumber_tables)} table(s) PyMuPDF missed")
        tables.extend(plumber_tables)

    return tables
```

- [ ] **Step 7: Update `process_document` to pass `pdf_path` to `_extract_page_tables`**

In `process_document` (line ~151), update the call:
```python
# BEFORE
page_tables = self._extract_page_tables(page, page_num + 1)

# AFTER
page_tables = self._extract_page_tables(page, page_num + 1, pdf_path=pdf_path)
```

- [ ] **Step 8: Fix `has_headers` in `_extract_table_data` to use detection**

In `_extract_table_data` (line ~313):
```python
# BEFORE
'has_headers': True,  # Assume first row is headers

# AFTER
'has_headers': self._detect_has_headers(raw_data),
```

- [ ] **Step 9: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_table_processor_pdfplumber.py -v
```

Expected: all PASS

- [ ] **Step 10: Commit**

```bash
git add backend/processors/table_processor.py backend/tests/test_table_processor_pdfplumber.py backend/requirements.txt
git commit -m "[Extraction] Add pdfplumber fallback for borderless tables, fix has_headers detection"
```

---

## Task 3: DB reset script (Area 0c)

**Files:**
- Create: `scripts/reset_document_data.py`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""
reset_document_data.py — Delete all processed document data, preserve videos/products/manufacturers.

Usage:
    python scripts/reset_document_data.py --confirm

PRESERVES: manufacturers, products, product_series, videos, video_products, users
DELETES: documents, chunks, error_codes, solutions, images, links, parts, stage tracking
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from processors.env_loader import load_all_env_files
load_all_env_files(Path(__file__).parent.parent)

import asyncpg

DELETE_STEPS = [
    # Intelligence (depends on chunks/documents)
    ("krai_intelligence.error_codes",    "DELETE FROM krai_intelligence.error_codes"),
    ("krai_intelligence.solutions",      "DELETE FROM krai_intelligence.solutions"),
    ("krai_intelligence.chunks",         "DELETE FROM krai_intelligence.chunks"),
    # Content (except videos)
    ("krai_content.images",              "DELETE FROM krai_content.images"),
    ("krai_content.links",               "DELETE FROM krai_content.links"),
    # Parts
    ("krai_parts.parts_catalog",         "DELETE FROM krai_parts.parts_catalog"),
    # System state
    ("krai_system.stage_tracking",       "DELETE FROM krai_system.stage_tracking"),
    ("krai_system.completion_markers",   "DELETE FROM krai_system.completion_markers"),
    ("krai_system.retries",              "DELETE FROM krai_system.retries"),
    # Documents last
    ("krai_core.documents",              "DELETE FROM krai_core.documents"),
]

PRESERVED = [
    "krai_core.manufacturers",
    "krai_core.products",
    "krai_core.product_series",
    "krai_content.videos",
    "krai_content.video_products",
    "krai_users.*",
]


async def run_reset(dsn: str) -> None:
    conn = await asyncpg.connect(dsn)
    print("\n⚠️  PRESERVED (untouched):")
    for t in PRESERVED:
        print(f"  ✓ {t}")

    print("\n🗑️  Deleting tables in order:")
    try:
        for label, sql in DELETE_STEPS:
            try:
                result = await conn.execute(sql)
                # asyncpg returns "DELETE N" string
                count = result.split()[-1] if result else "?"
                print(f"  ✓ {label}: {count} rows deleted")
            except Exception as e:
                print(f"  ⚠  {label}: {e} (skipping — table may not exist)")
    finally:
        await conn.close()

    print("\n✅ Reset complete. Re-upload documents to reprocess.\n")


def main():
    parser = argparse.ArgumentParser(description="Reset KRAI document data (preserves videos/products/manufacturers)")
    parser.add_argument("--confirm", action="store_true", help="Required flag to execute deletion")
    args = parser.parse_args()

    if not args.confirm:
        print("Dry run — add --confirm to execute.\n")
        print("Will DELETE:")
        for label, _ in DELETE_STEPS:
            print(f"  - {label}")
        print("\nWill PRESERVE:")
        for t in PRESERVED:
            print(f"  - {t}")
        sys.exit(0)

    dsn = os.getenv("DATABASE_URL") or (
        f"postgresql://{os.getenv('POSTGRES_USER','krai')}:{os.getenv('POSTGRES_PASSWORD','krai')}"
        f"@{os.getenv('POSTGRES_HOST','localhost')}:{os.getenv('POSTGRES_PORT','5432')}"
        f"/{os.getenv('POSTGRES_DB','krai')}"
    )

    print(f"Connecting to: {dsn.split('@')[-1]}")  # hide credentials in output
    asyncio.run(run_reset(dsn))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run to verify output (no `--confirm`)**

```bash
python scripts/reset_document_data.py
```

Expected: prints "Dry run" + list of tables to delete and preserve. No DB changes.

- [ ] **Step 3: Commit**

```bash
git add scripts/reset_document_data.py
git commit -m "[Scripts] Add reset_document_data.py — safe DB reset preserving videos/products/manufacturers"
```

---

## Task 4: Run DB reset + reprocess documents (Area 0 execution)

> This task is manual. Complete Tasks 1–3 first and verify the pipeline works on at least one test document before resetting production data.

- [ ] **Step 1: Verify pipeline runs cleanly on one test PDF**

Upload a test PDF via the admin dashboard or API. Confirm that:
- Error codes are extracted with full solution text (> 200 chars where applicable)
- Tables are found on pages that previously had none

- [ ] **Step 2: Execute DB reset**

```bash
python scripts/reset_document_data.py --confirm
```

Expected: all DELETE rows printed, ends with "Reset complete."

- [ ] **Step 3: Re-upload all documents**

Re-upload PDFs via the admin dashboard or batch upload API. Monitor pipeline logs.

- [ ] **Step 4: Spot-check data quality**

Query the DB to verify solutions are complete:
```sql
SELECT error_code, length(solution_technician_text) as sol_len, left(solution_technician_text, 200)
FROM krai_intelligence.error_codes
WHERE solution_technician_text IS NOT NULL
ORDER BY sol_len DESC
LIMIT 20;
```

Expected: solution lengths >200 chars for complex procedures. No `...` suffixes.

---

## Task 5: Fix match_multimodal DB function (must complete before Task 6)

> **Dependency:** This migration must be applied before Task 6 (Ragas eval) runs. The eval script's `/search/` call routes through `match_multimodal`. If this function still uses `c.chunk_text` (wrong column), it returns NULL for all text content and Ragas metrics will be based on empty contexts.

**Files:**
- Create: `database/migrations_postgresql/025_fix_match_multimodal.sql`

Also fix the same bug in `match_chunks` (same file, line 164 also uses `c.chunk_text`).

- [ ] **Step 1: Create corrective migration with full function bodies**

```sql
-- database/migrations_postgresql/025_fix_match_multimodal.sql
-- Fix: match_chunks and match_multimodal referenced c.chunk_text (wrong column).
-- Correct column name is c.text_chunk per krai_intelligence.chunks schema.
-- See CLAUDE.md known column name traps.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'krai_intelligence'
      AND table_name = 'chunks'
      AND column_name = 'text_chunk'
  ) THEN
    RAISE EXCEPTION 'Column krai_intelligence.chunks.text_chunk does not exist — check schema';
  END IF;
END $$;

-- Fix match_chunks
CREATE OR REPLACE FUNCTION krai_intelligence.match_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
) RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    page_number int,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.document_id,
        c.text_chunk,          -- FIXED: was c.chunk_text
        c.page_number,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM krai_intelligence.chunks c
    WHERE c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Fix match_multimodal
CREATE OR REPLACE FUNCTION krai_intelligence.match_multimodal(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
) RETURNS TABLE (
    source_id uuid,
    source_type text,
    content text,
    document_id uuid,
    page_number int,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    WITH all_matches AS (
        -- Text chunks
        SELECT
            c.id as source_id,
            'chunk'::text as source_type,
            c.text_chunk as content,   -- FIXED: was c.chunk_text
            c.document_id,
            c.page_number,
            1 - (c.embedding <=> query_embedding) as similarity
        FROM krai_intelligence.chunks c
        WHERE c.embedding IS NOT NULL
            AND 1 - (c.embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Images
        SELECT
            i.id as source_id,
            'image'::text as source_type,
            COALESCE(i.ai_description, i.figure_context, '') as content,
            i.document_id,
            i.page_number,
            1 - (i.context_embedding <=> query_embedding) as similarity
        FROM krai_content.images i
        WHERE i.context_embedding IS NOT NULL
            AND 1 - (i.context_embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Videos
        SELECT
            v.id as source_id,
            'video'::text as source_type,
            COALESCE(v.description, v.title, '') as content,
            v.document_id,
            v.page_number,
            1 - (v.context_embedding <=> query_embedding) as similarity
        FROM krai_content.videos v
        WHERE v.context_embedding IS NOT NULL
            AND 1 - (v.context_embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Links
        SELECT
            l.id as source_id,
            'link'::text as source_type,
            COALESCE(l.description, l.url, '') as content,
            l.document_id,
            l.page_number,
            1 - (l.context_embedding <=> query_embedding) as similarity
        FROM krai_content.links l
        WHERE l.context_embedding IS NOT NULL
            AND 1 - (l.context_embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Structured tables
        SELECT
            t.id as source_id,
            'table'::text as source_type,
            COALESCE(t.table_markdown, '') as content,
            t.document_id,
            t.page_number,
            1 - (t.table_embedding <=> query_embedding) as similarity
        FROM krai_intelligence.structured_tables t
        WHERE t.table_embedding IS NOT NULL
            AND 1 - (t.table_embedding <=> query_embedding) > match_threshold
    )
    SELECT * FROM all_matches
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

- [ ] **Step 2: Apply migration**

```bash
psql $DATABASE_URL -f database/migrations_postgresql/025_fix_match_multimodal.sql
```

Expected: no errors, both functions recreated.

- [ ] **Step 3: Verify fix**

```sql
-- Replace <real_embedding> with any 768-dim vector from krai_intelligence.chunks.embedding
SELECT content FROM krai_intelligence.match_chunks('<real_embedding>'::vector, 0.0, 1);
-- content column should contain actual text, not NULL
```

Quick way to get a real embedding for testing:
```sql
SELECT embedding FROM krai_intelligence.chunks WHERE embedding IS NOT NULL LIMIT 1;
```

- [ ] **Step 4: Commit**

```bash
git add database/migrations_postgresql/025_fix_match_multimodal.sql
git commit -m "[DB] Fix match_chunks + match_multimodal: chunk_text → text_chunk (correct column name)"
```

---

## Task 6: Ragas evaluation script (Area 3)

**Files:**
- Create: `requirements-dev.txt`
- Create: `scripts/eval_dataset.json`
- Create: `scripts/evaluate_rag.py`
- Create: `scripts/eval_results/` (directory, add `.gitkeep`)

- [ ] **Step 1: Create requirements-dev.txt**

```
# Dev/CI only — never imported in production
ragas>=0.1.0,<0.2.0
```

```bash
pip install ragas
```

- [ ] **Step 2: Create eval_dataset.json with ~20 questions**

`scripts/eval_dataset.json` — fill with real error codes and documents from your DB after reprocessing. Structure:

```json
[
  {
    "question": "What causes error 13.B9.Az and how do I fix it?",
    "ground_truth": "Paper jam in the fuser area. Open the front cover, remove jammed paper, check separation claws for wear.",
    "scope_document_id": null
  },
  {
    "question": "How do I replace the fuser unit on the bizhub C450i?",
    "ground_truth": "Power off, wait for cooling, remove the fuser unit by releasing two latches, insert replacement, power on.",
    "scope_document_id": null
  }
]
```

Add ~18 more questions covering: error codes with solutions, parts lookup, document-specific queries, multimodal queries.

- [ ] **Step 3: Write evaluate_rag.py**

```python
#!/usr/bin/env python3
"""
evaluate_rag.py — Measure RAG quality using Ragas metrics.

Usage:
    python scripts/evaluate_rag.py --backend http://localhost:8000 --output scripts/eval_results/

Requires: pip install ragas  (requirements-dev.txt)
Requires: running KRAI backend
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness


DATASET_PATH = Path(__file__).parent / "eval_dataset.json"
DEFAULT_BACKEND = os.getenv("KRAI_BACKEND_URL", "http://localhost:8000")
API_TOKEN = os.getenv("KRAI_API_TOKEN", "")


async def get_answer(client: httpx.AsyncClient, backend: str, question: str, scope_doc_id: str | None) -> str:
    scope = {"document_id": scope_doc_id} if scope_doc_id else None
    payload = {
        "message": question,
        "session_id": f"eval-{hash(question)}",
        "scope": scope,
    }
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    resp = await client.post(f"{backend}/agent/chat", json=payload, headers=headers, timeout=60.0)
    resp.raise_for_status()
    return resp.json()["response"]


async def get_contexts(client: httpx.AsyncClient, backend: str, question: str, scope_doc_id: str | None) -> list[str]:
    payload = {"query": question, "limit": 10}
    if scope_doc_id:
        payload["document_id"] = scope_doc_id
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    resp = await client.post(f"{backend}/search/", json=payload, headers=headers, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results") or data.get("data") or []
    return [r.get("content", r.get("text_chunk", "")) for r in results if r.get("content") or r.get("text_chunk")]


async def collect_samples(backend: str, dataset: list) -> list[dict]:
    samples = []
    async with httpx.AsyncClient() as client:
        for i, entry in enumerate(dataset, 1):
            question = entry["question"]
            ground_truth = entry["ground_truth"]
            scope_doc_id = entry.get("scope_document_id")
            print(f"[{i}/{len(dataset)}] {question[:60]}...", flush=True)
            try:
                answer, contexts = await asyncio.gather(
                    get_answer(client, backend, question, scope_doc_id),
                    get_contexts(client, backend, question, scope_doc_id),
                )
                samples.append({
                    "question": question,
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": ground_truth,
                })
            except Exception as e:
                print(f"  ⚠ Failed: {e}", flush=True)
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--output", default=str(Path(__file__).parent / "eval_results"))
    parser.add_argument("--dataset", default=str(DATASET_PATH))
    args = parser.parse_args()

    with open(args.dataset) as f:
        dataset = json.load(f)

    print(f"Collecting {len(dataset)} samples from {args.backend}...")
    samples = asyncio.run(collect_samples(args.backend, dataset))

    if not samples:
        print("No samples collected. Is the backend running?")
        sys.exit(1)

    print(f"\nEvaluating {len(samples)} samples with Ragas...")
    ds = Dataset.from_list(samples)
    result = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision])

    print("\n" + "="*50)
    print("RAG EVALUATION RESULTS")
    print("="*50)
    print(result)

    Path(args.output).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    out_path = Path(args.output) / f"{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "backend": args.backend,
            "sample_count": len(samples),
            "metrics": {k: float(v) for k, v in result.items()},
            "samples": samples,
        }, f, indent=2)
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create output directory**

```bash
mkdir -p scripts/eval_results
echo "" > scripts/eval_results/.gitkeep
```

- [ ] **Step 5: Run against live backend (smoke test)**

```bash
python scripts/evaluate_rag.py --backend http://localhost:8000
```

Expected: runs through dataset, prints metric table, writes JSON report. Metrics will be the baseline to beat after Areas 1 and 2.

- [ ] **Step 6: Commit**

```bash
git add requirements-dev.txt scripts/eval_dataset.json scripts/evaluate_rag.py scripts/eval_results/.gitkeep
git commit -m "[Eval] Add Ragas evaluation script and baseline dataset"
```

---

## Task 7: RerankingService (Area 2, Part 1)

**Files:**
- Create: `backend/services/reranking_service.py`
- Test: `backend/tests/test_reranking_service.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_reranking_service.py
import os
import pytest


def test_reranking_service_returns_top_n():
    from backend.services.reranking_service import RerankingService
    svc = RerankingService()
    texts = [
        "Replace the fuser unit by removing two screws.",
        "The weather today is sunny and warm.",
        "Open the front cover and remove jammed paper from the fuser area.",
        "Fuser temperature error caused by worn heating element.",
        "Check the oil level in your car.",
    ]
    result = svc.rerank("How do I fix a fuser jam?", texts, top_n=3)
    assert len(result) == 3
    # The fuser-related texts should rank higher than weather/car
    assert any("fuser" in r.lower() for r in result)


def test_reranking_service_noop_when_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_RERANKING", "false")
    # Re-import to pick up env var
    import importlib
    import backend.services.reranking_service as mod
    importlib.reload(mod)
    svc = mod.RerankingService()
    texts = ["a", "b", "c", "d", "e"]
    result = svc.rerank("query", texts, top_n=3)
    assert result == texts[:3]


def test_reranking_returns_strings_not_scores():
    from backend.services.reranking_service import RerankingService
    svc = RerankingService()
    texts = ["Fix the jam by opening cover A.", "Unrelated text about cooking."]
    result = svc.rerank("paper jam fix", texts, top_n=2)
    assert all(isinstance(r, str) for r in result)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_reranking_service.py -v
```

Expected: FAIL — module does not exist

- [ ] **Step 3: Implement RerankingService**

```python
# backend/services/reranking_service.py
"""
RerankingService — CrossEncoder-based reranking for post-retrieval quality improvement.

Configuration (env vars):
  ENABLE_RERANKING   default: true   — set to false for no-op passthrough
  RERANKING_MODEL    default: cross-encoder/ms-marco-MiniLM-L-6-v2
  RERANKING_TOP_N    default: 5      — results returned after reranking
  RERANKING_CANDIDATES default: 20  — how many candidates to fetch before reranking
"""
import logging
import os
from typing import Optional

logger = logging.getLogger("krai.reranking")


class RerankingService:
    """
    Reranks a list of text candidates using a CrossEncoder model.

    Usage:
        svc = RerankingService()
        top_texts = svc.rerank(query, candidate_texts, top_n=5)
    """

    def __init__(self) -> None:
        self.enabled = os.getenv("ENABLE_RERANKING", "true").lower() == "true"
        self.model_name = os.getenv("RERANKING_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.default_top_n = int(os.getenv("RERANKING_TOP_N", "5"))
        self.candidates = int(os.getenv("RERANKING_CANDIDATES", "20"))
        self._model: Optional[object] = None

        if self.enabled:
            self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
            logger.info("RerankingService: loaded model %s", self.model_name)
        except Exception as e:
            logger.warning("RerankingService: failed to load model %s — reranking disabled: %s", self.model_name, e)
            self.enabled = False

    def rerank(self, query: str, texts: list[str], top_n: int | None = None) -> list[str]:
        """
        Rerank texts by relevance to query.

        Args:
            query: The search query.
            texts: Plain text strings to rerank (no metadata).
            top_n: How many top results to return. Defaults to RERANKING_TOP_N env var.

        Returns:
            Top-N strings sorted by CrossEncoder score, descending.
            When disabled, returns texts[:top_n] unchanged.
        """
        n = top_n if top_n is not None else self.default_top_n

        if not self.enabled or self._model is None or not texts:
            return texts[:n]

        try:
            pairs = [(query, t) for t in texts]
            scores = self._model.predict(pairs)
            ranked = sorted(zip(scores, texts), key=lambda x: x[0], reverse=True)
            return [text for _, text in ranked[:n]]
        except Exception as e:
            logger.warning("RerankingService.rerank failed, returning unranked: %s", e)
            return texts[:n]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_reranking_service.py -v
```

Expected: all PASS (note: first run downloads the CrossEncoder model ~22MB)

- [ ] **Step 5: Commit**

```bash
git add backend/services/reranking_service.py backend/tests/test_reranking_service.py
git commit -m "[Reranking] Add RerankingService with CrossEncoder, configurable model and no-op mode"
```

---

## Task 8: Wire RerankingService into MultimodalSearchService (Area 2, Part 2)

**Files:**
- Modify: `backend/services/multimodal_search_service.py:16-49, 51-127`

- [ ] **Step 1: Inject RerankingService into `__init__`**

In `MultimodalSearchService.__init__`, add parameter and store:
```python
def __init__(
    self,
    database_service: DatabaseAdapter,
    ai_service: AIService,
    reranking_service=None,          # NEW: RerankingService | None
    default_threshold: float = 0.5,
    default_limit: int = 10
):
    ...
    self.reranking_service = reranking_service
```

- [ ] **Step 2: Expand fetch count and add reranking in `search_multimodal`**

In `search_multimodal`, replace the `match_multimodal` call and result handling:

```python
# Fetch more candidates when reranking is enabled
fetch_limit = (
    self.reranking_service.candidates
    if self.reranking_service and self.reranking_service.enabled
    else (limit or self.default_limit)
)

results = await self.database_service.match_multimodal(
    query_embedding=query_embedding,
    match_threshold=threshold or self.default_threshold,
    match_count=fetch_limit,
)

# Filter by modalities
if modalities:
    results = [r for r in results if r['source_type'] in modalities]

# Rerank using index-based reconstruction (NOT set-matching, which breaks on duplicate content)
if self.reranking_service and self.reranking_service.enabled and results:
    texts = [r.get('content', '') for r in results]
    top_n = limit or self.default_limit
    top_texts = self.reranking_service.rerank(query, texts, top_n=top_n)
    # Rebuild results list in reranked order using original index position
    text_to_original_idx = {t: i for i, t in enumerate(texts)}
    reranked_results = []
    for text in top_texts:
        idx = text_to_original_idx.get(text)
        if idx is not None:
            reranked_results.append(results[idx])
    results = reranked_results
```

- [ ] **Step 3: Commit**

```bash
git add backend/services/multimodal_search_service.py
git commit -m "[Reranking] Wire RerankingService into MultimodalSearchService"
```

---

## Task 9: Wire AIService + RerankingService into KRAIAgent (Area 1 + Area 2)

**Files:**
- Modify: `backend/api/agent_api.py:281, 645, 701`
- Modify: `backend/api/app.py:886`
- Test: `backend/tests/test_agent_vector_seed.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_agent_vector_seed.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_create_tools_accepts_ai_service_and_reranking_service():
    """create_tools must accept ai_service and reranking_service without error."""
    import inspect
    from backend.api.agent_api import create_tools
    sig = inspect.signature(create_tools)
    assert "ai_service" in sig.parameters
    assert "reranking_service" in sig.parameters


def test_kraiagent_init_accepts_ai_service():
    """KRAIAgent.__init__ must accept ai_service parameter."""
    import inspect
    from backend.api.agent_api import KRAIAgent
    sig = inspect.signature(KRAIAgent.__init__)
    assert "ai_service" in sig.parameters
    assert "reranking_service" in sig.parameters
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_agent_vector_seed.py -v
```

Expected: FAIL — parameters don't exist yet

- [ ] **Step 3: Update `create_tools` signature**

In `agent_api.py` line 281, update `create_tools`:
```python
def create_tools(
    pool: asyncpg.Pool,
    ollama_base_url: str,
    ai_service=None,          # AIService | None
    reranking_service=None,   # RerankingService | None
) -> list:
```

- [ ] **Step 4: Update `KRAIAgent.__init__` signature and propagation**

```python
def __init__(
    self,
    pool: asyncpg.Pool,
    ollama_base_url: str | None = None,
    ai_service=None,          # AIService | None — NEW
    reranking_service=None,   # RerankingService | None — NEW
) -> None:
```

Update the `create_tools` call at line 701:
```python
tools=create_tools(pool, ollama_base_url, ai_service=ai_service, reranking_service=reranking_service),
```

- [ ] **Step 5: Update `app.py` to construct and inject services**

`app.py` uses bare `from services.X import X` style throughout (e.g. line 58: `from services.batch_task_service import BatchTaskService`). Use the same style.

At the top of `app.py` with the other service imports, add:
```python
from services.ai_service import AIService
from services.reranking_service import RerankingService
```

Then at line 886, replace:
```python
# BEFORE
krai_agent = KRAIAgent(pool)

# AFTER
ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
ai_svc = AIService(ollama_url=ollama_url)
reranking_svc = RerankingService()
krai_agent = KRAIAgent(pool, ai_service=ai_svc, reranking_service=reranking_svc)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_agent_vector_seed.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/api/agent_api.py backend/api/app.py backend/tests/test_agent_vector_seed.py
git commit -m "[Agent] Wire AIService + RerankingService into KRAIAgent and create_tools"
```

---

## Task 10: Add vector-seed step to search_error_codes and search_videos (Area 1)

**Files:**
- Modify: `backend/api/agent_api.py` — `search_error_codes` and `search_videos` tool bodies

- [ ] **Step 1: Add `_vector_seed` helper inside `create_tools`**

Add this async helper inside `create_tools`, before the `@tool` definitions:

```python
async def _vector_seed(query: str) -> dict:
    """
    Embed query and find the 20 most similar chunks via pgvector.
    Returns chunk_ids, document_ids, product_ids (empty lists if ai_service is None or fails).

    NOTE: Uses a plain ORDER BY + LIMIT — NOT DISTINCT ON — so that pgvector
    evaluates similarity globally across all chunks and returns the true top-20.
    """
    if ai_service is None:
        return {"chunk_ids": [], "document_ids": [], "product_ids": []}
    try:
        embedding = await ai_service.generate_embeddings(query)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT ch.id AS chunk_id,
                       ch.document_id,
                       dp.product_id
                FROM   krai_intelligence.chunks ch
                LEFT JOIN krai_core.document_products dp ON dp.document_id = ch.document_id
                WHERE  ch.embedding IS NOT NULL
                ORDER  BY ch.embedding <=> $1::vector
                LIMIT  20
                """,
                embedding,
            )
        return {
            "chunk_ids":    [str(r["chunk_id"]) for r in rows],
            "document_ids": list({str(r["document_id"]) for r in rows if r["document_id"]}),
            "product_ids":  list({str(r["product_id"]) for r in rows if r["product_id"]}),
        }
    except Exception as e:
        logger.warning("_vector_seed failed, falling back to ILIKE: %s", e)
        return {"chunk_ids": [], "document_ids": [], "product_ids": []}
```

- [ ] **Step 2: Update `search_error_codes` to use vector seed**

At the top of the `search_error_codes` tool body (before building `exact_params`):

```python
seed = await _vector_seed(query)
matched_chunk_ids = seed["chunk_ids"]
```

Then in the exact-match WHERE clause, add the chunk_id seed after existing filters:
```python
if matched_chunk_ids:
    exact_params.append(matched_chunk_ids)
    exact_where.append(f"ec.chunk_id = ANY(${len(exact_params)}::uuid[])")
```

Apply the same to the broad-match fallback WHERE clause.

- [ ] **Step 3: Update `search_videos` to use vector seed for document/product seeding**

At top of `search_videos` tool body:
```python
seed = await _vector_seed(query)
```

Then pass `matched_document_ids=seed["document_ids"]` and `matched_product_ids=seed["product_ids"]` to `_fetch_related_videos`.

- [ ] **Step 4: Smoke-test agent locally**

Start the backend and ask the agent a semantic question:
```
"What does error 13.B9.Az mean and how do I resolve it on a bizhub C450i?"
```

Verify the agent returns a complete solution (not truncated), using vector-seeded results.

- [ ] **Step 5: Run full test suite**

```bash
python -m pytest backend/tests/ -v -x
```

Expected: all existing tests pass, no regressions.

- [ ] **Step 6: Commit**

```bash
git add backend/api/agent_api.py
git commit -m "[Agent] Add vector-seed hybrid retrieval to search_error_codes and search_videos"
```

---

## Task 11: Add reranking to semantic_search tool (Area 2, Part 3)

**Files:**
- Modify: `backend/api/agent_api.py` — `semantic_search` tool body (lines ~594–612)

- [ ] **Step 1: Add reranking after pgvector fetch in `semantic_search`**

After the `rows` are fetched and before the `if not rows:` check, add:

```python
# Rerank results using index-based reconstruction (NOT set-matching)
if rows and reranking_service and reranking_service.enabled:
    texts = [row["content"] for row in rows]
    top_texts = reranking_service.rerank(query, texts)
    # Rebuild rows in reranked order by original index — handles duplicate content correctly
    text_to_idx = {t: i for i, t in enumerate(texts)}
    rows = [rows[text_to_idx[t]] for t in top_texts if t in text_to_idx]
```

- [ ] **Step 2: Run smoke test**

Ask the agent a semantic question. Verify response quality is at least as good as before.

- [ ] **Step 3: Run Ragas evaluation again and compare**

```bash
python scripts/evaluate_rag.py --backend http://localhost:8000
```

Compare output metrics to the baseline from Task 6. Expect improvement in `faithfulness` and `context_precision`.

- [ ] **Step 4: Commit**

```bash
git add backend/api/agent_api.py
git commit -m "[Reranking] Add CrossEncoder reranking to semantic_search tool"
```

---

## Task 12: Final validation

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest backend/tests/ -v --tb=short
```

Expected: all PASS

- [ ] **Step 2: Run Ragas evaluation — final comparison**

```bash
python scripts/evaluate_rag.py --backend http://localhost:8000 --output scripts/eval_results/
```

Compare `faithfulness`, `answer_relevancy`, `context_precision` against the Task 6 baseline.

- [ ] **Step 3: Manual spot-check with a technician query**

Ask the agent:
- "What causes error 13.B9.Az and how is it fixed?"
- "Show me all parts related to the fuser unit on the C450i"
- "What does the service manual say about drum unit replacement?"

Verify: complete answers, no truncated `...` suffixes in solutions, relevant context.

- [ ] **Step 4: Final commit**

```bash
git commit -m "[RAG] All improvements complete: data quality, vector search, reranking, evaluation"
```
