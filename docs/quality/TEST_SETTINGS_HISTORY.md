# Test Settings History and Baseline

## Current Baseline (2026-02-13)

### Test Identity
- Test run: `test_20260213_072532`
- Report file: `file:test_results/production_test_20260213_172656.json`
- Date: `2026-02-13`
- Result: `FAIL`

### Input Set
- `C:\Firmwares\HP\HP_E877_CPMD.pdf`
- `C:\Firmwares\HP\HP_E877_SM.pdf`

### Target Document IDs
- `becd5a67-3008-4d60-82ee-aa24f666b8c9`
- `b557ec67-52db-4863-9e3a-b0d48e330b2e`

### Runtime Baseline
- Total duration: `36,084.05s` (`10.02h`)
- Stages expected/completed: `30/30`
- Success rate (stage completion): `1.0`

## Quality Threshold Configuration
Source: `file:config/production_test_thresholds.json`

```json
{
  "min_chunks": 100,
  "min_images": 10,
  "min_error_codes": 5,
  "min_embedding_coverage": 0.95,
  "min_products": 1,
  "min_parts": 0
}
```

## Measured Outcome vs Threshold

| Metric | Value | Threshold | Status |
|---|---:|---:|---|
| chunks | 5159 | 100 | PASS |
| images | 2062 | 10 | PASS |
| error_codes | 0 | 5 | FAIL |
| parts | 0 | 0 | PASS |
| products_count | 0 | 1 | FAIL |
| embedding_coverage | 1.0 | 0.95 | PASS |
| linked_products | 0 | >=1 | FAIL |

## Per-Document Performance Baseline

| Document | Chunks | Images | Error Codes | Products | Embedding Coverage |
|---|---:|---:|---:|---:|---:|
| `HP_E877_CPMD.pdf` | 1189 | 1708 | 0 | 0 | 1.0 |
| `HP_E877_SM.pdf` | 3970 | 354 | 0 | 0 | 1.0 |

## Configuration and Schema Notes

### Manufacturer Configuration
- `krai_core.manufacturers` contains HP row:
  - `id = e7680b1c-d4f8-45fb-934a-3be603c29cac`
  - `name = HP Inc.`
  - `short_name = HP`
- Documents are not linked (`documents.manufacturer_id = NULL`) despite `documents.manufacturer = 'HP Inc.'`.

### Stage Configuration
- All standard 15 stages present and completed for both documents.
- No explicit stage-level extraction failure marker when outputs are zero.

### Parts Schema Behavior
- `krai_parts.parts_catalog` currently links by `product_id` and `manufacturer_id`.
- No `document_id` column in `parts_catalog`.
- Parts-by-document reporting requires `document_products` join path.

## Diagnostic Query Compatibility History

The original 8-query diagnostic packet required schema adjustments:

1. `document_products.confidence_score` -> use `relevance_score`
2. `error_codes.manufacturer_name/description/solution/confidence/severity/context` ->
   use `manufacturer_id` join + `error_description`, `solution_text`, `confidence_score`, `severity_level`
3. `parts_catalog.document_id/manufacturer_name/confidence/page_number` not present ->
   resolve parts through `product_id` join to `document_products`

Canonical diagnostic output:
- `file:docs/quality/sql_diagnostics_20260213.json`

## Pattern Presence Baseline

Chunk probe confirms expected semantic signals exist in corpus:

| Document ID | chunks_with_e877 | chunks_with_hp_error_pattern |
|---|---:|---:|
| `b557ec67-52db-4863-9e3a-b0d48e330b2e` | 30 | 11 |
| `becd5a67-3008-4d60-82ee-aa24f666b8c9` | 15 | 250 |

Interpretation:
- Source content contains extractable patterns.
- Failure is not caused by missing textual signal.

## Image Processing Baseline

| Document ID | image_count | images_with_ocr | images_with_ai_desc | images_with_context_embedding |
|---|---:|---:|---:|---:|
| `b557ec67-52db-4863-9e3a-b0d48e330b2e` | 354 | 56 | 13 | 0 |
| `becd5a67-3008-4d60-82ee-aa24f666b8c9` | 1708 | 67 | 43 | 0 |

## Change Log

### 2026-02-13
- Established baseline for HP E877 production test.
- Logged full SQL diagnostics under `file:docs/quality/sql_diagnostics_20260213.json`.
- Identified primary quality gap: manufacturer FK linkage and downstream extraction emptiness.

### 2026-02-13 (Traycer Artifacts Update - Link/Video Fixes)
- Applied and validated targeted fixes for Stage 7 link/video extraction:
  - PDF annotation decoding hardening for malformed bytes.
  - Context logging format fix for nullable page values.
  - Link deduplication now preserves `page_number` and rich context fields.
  - Video persistence now stores `video_url` and updates rows via URL/YouTube upsert.
  - Stage-check reset mapping corrected for link extraction processor markers.
- Data cleanup applied for stale orphan video rows from earlier failed runs.
- Verified after rerun:
  - Document `becd5a67-3008-4d60-82ee-aa24f666b8c9`: `links=29`, `videos=1`, `videos_null_page=0`.
  - Document `b557ec67-52db-4863-9e3a-b0d48e330b2e`: `links=192`, `videos=159`, `videos_null_page=0`.

#### Open Note: Brightcove Enrichment
- Brightcove links/videos are extracted and persisted, but metadata enrichment remains partial.
- Current state:
  - Many Brightcove rows still have `metadata.needs_enrichment=true`.
  - `context_description` for videos is largely empty.
  - Full Brightcove API enrichment still requires provider/account-specific integration.
- Status: **Open follow-up item** (not a blocker for extraction correctness).

### 2026-02-14 (Traycer Artifacts Update - Multi-Manufacturer Test)
- New input set:
  - `C:\Firmwares\Konica Minolta\KM_C658_C558_C458_C368_C308_C258_SM_EN.pdf`
  - `C:\Firmwares\Lexmark\7566-69x_sm.pdf`
- New document IDs:
  - `9e7e4f7f-02c9-41e3-9a77-32bfd1647c1a`
  - `d5849a18-cc45-44aa-81e0-e278a3e61022`
- Quality artifact generated:
  - `file:test_results/quality_check_multivendor_20260214_013146.json`
  - Summary artifact: `file:docs/quality/TRAYCER_ARTIFACTS_20260214_MULTIVENDOR.md`
- Validator update applied for mixed manufacturers:
  - Removed HP/E877 hardcoded correctness checks from `file:scripts/quality_validator.py`.
  - Correctness now validates generic product/model/manufacturer presence.
- Quality result: `FAIL` (primary reasons: images not processed in targeted run and incomplete stage marker coverage).

## Next Baseline Update Rules
- Create a new dated baseline file after each production test affecting extraction behavior.
- Preserve threshold deltas and SQL compatibility changes.
- Include absolute run timestamps and document IDs for reproducibility.
