# Traycer Artifacts Update - Multi-Manufacturer Run (2026-02-14)

## Scope
- Konica Minolta:
  - `C:\Firmwares\Konica Minolta\KM_C658_C558_C458_C368_C308_C258_SM_EN.pdf`
  - Document ID: `9e7e4f7f-02c9-41e3-9a77-32bfd1647c1a`
- Lexmark:
  - `C:\Firmwares\Lexmark\7566-69x_sm.pdf`
  - Document ID: `d5849a18-cc45-44aa-81e0-e278a3e61022`

## Implemented Changes Included in This Artifact
- Stage 7 link/video robustness fixes (decode safety, nullable page handling, video URL persistence, dedupe preservation).
- Stage-check marker mapping fix for link extraction in `scripts/run_stage_checks.py`.
- Quality validator generalized for mixed manufacturers in `scripts/quality_validator.py`:
  - Removed HP/E877 hardcoded correctness logic.
  - Correctness now checks generic model/manufacturer presence plus minimum product count.
- Brightcove note added to historical artifact (`docs/quality/TEST_SETTINGS_HISTORY.md`).

## Run Status
- Stage processing executed in targeted mode for both documents.
- Stable completed markers:
  - `text_processor`, `TableProcessor`, `link_extraction_processor`,
  - `chunk_preprocessor`, `classification_processor`, `metadata_processor_ai`,
  - `parts_processor`, `series_processor`, `storage_processor`.
- Missing markers remain for:
  - `upload_processor`, `svg_processor`, `image_processor`, `visual_embedding_processor`,
  - `embedding_processor`, `search_processor`.

## Quality Check Output
- Initial result file: `test_results/quality_check_multivendor_20260214_013146.json`
- Latest result file: `test_results/quality_check_multivendor_20260214_123316.json`
- Overall result: `FAIL`

### Key Metrics
- Completeness:
  - Chunks: `5435` (`PASS`)
  - Images: `0` (`FAIL`, threshold `10`)
  - Error codes: `207` (`PASS`)
  - Parts: `20` (`PASS`)
- Correctness: `PASS`
- Embeddings coverage: `1.0` (`PASS`)
- Relationships: `PASS`
- Stage status: `FAIL` (incomplete marker coverage for expected 15-stage baseline)

## Manufacturer and Model Detection (Requested)
- Konica Minolta document (`9e7e4f7f-02c9-41e3-9a77-32bfd1647c1a`):
  - Document manufacturer: `Konica Minolta`
  - Linked products/models:
    - `C308`
    - `C368`
    - `C458`
    - `C558`
    - `C658`
- Lexmark document (`d5849a18-cc45-44aa-81e0-e278a3e61022`):
  - Document manufacturer: `Unknown`
  - Linked products/models: none (`0`)

## Open Note: Brightcove (Follow-up)
- Brightcove extraction and persistence are functional.
- Enrichment remains partial for many Brightcove rows (`needs_enrichment=true` and sparse context).
- Full metadata enrichment still needs provider/account-specific Brightcove integration.

## Runtime Note on Missing Image Stages
- For both new documents, stage `svg_processing` is currently left in `running` state and did not complete within long rerun windows.
- Consequence:
  - `image_processing` and `visual_embedding` are not completed.
  - Image count stays at `0`, so completeness fails on images.
