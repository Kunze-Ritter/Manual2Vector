# Project Cleanup Log

**Date:** 2025-10-28
**Initiated by:** Cascade AI Assistant

## Summary

A four-phase cleanup reorganized tests, utility scripts, documentation, and legacy processors to reduce clutter and make the active pipeline easier to maintain. No files were deleted—everything was either moved into structured directories or archived for reference.

## File Movements

### 1. Tests
- Moved root-level `test_*.py`, `test_*.ps1`, and `test_from_docker.sh` into `tests/`.
- Created `tests/processors/` and relocated all processor-specific tests from `backend/processors/`.

### 2. Utility & Maintenance Scripts
- Relocated `check_*.py`, migration runners, and helper utilities from the repository root to `scripts/`.
- Moved processor helper scripts (`auto_processor.py`, `pipeline_processor.py`) into `scripts/`.
- Added `examples/` and moved `example_pipeline_usage.py` there for discoverable reference code.

### 3. Documentation
- Created dedicated documentation subfolders:
  - `docs/processor/`
  - `docs/video_enrichment/`
  - `docs/database/`
  - `docs/features/`
  - `docs/releases/`
  - `docs/project_management/`
- Migrated existing Markdown files into the appropriate folders (TODO lists, release notes, schema docs, feature guides, setup instructions).

### 4. Archives
- Added `archive/` with subdirectories:
  - `archive/temp_files/` for transient logs, commit message drafts, and temporary exports.
  - `archive/old_env/` for legacy environment files (e.g., `.env.old`).
- Added `backend/processors/archive/` and moved deprecated processor implementations (e.g., `master_pipeline.py`, `image_storage_processor_old.py`).

## Directory Overview (Updated)

```
archive/
├── temp_files/        # Transient outputs, commit message drafts
└── old_env/           # Deprecated environment files
examples/              # Usage demonstrations (e.g., example_pipeline_usage.py)
backend/processors/archive/
                        # Legacy processor implementations retained for reference
scripts/               # Centralized maintenance utilities (checks, fixes, migrations)
tests/
├── processors/        # Processor-focused integration tests
└── ...                # Other repository tests
``` 

Documentation subfolders:
- `docs/processor/` – Processor design, checklists, and maintenance plans
- `docs/video_enrichment/` – Video enrichment status and linking documentation
- `docs/database/` – Schema references, migration guides, and view audits
- `docs/features/` – Feature-specific guides (chunk linking, parts linking, Foliant)
- `docs/releases/` – Release notes, performance summaries, and rollout guides
- `docs/project_management/` – TODO lists, QA reports, refactoring plans, project boards

## Archive Strategy
- **No deletions:** Every file is preserved to support quick rollback or historical reference.
- **Clear separation:** Active code remains in primary directories, while `archive/` and `backend/processors/archive/` hold legacy assets.
- **Temp isolation:** Short-lived artifacts now live under `archive/temp_files/` to keep the root clean without losing debugging context.

## Rollback Instructions
1. Identify the desired file in its new location (see sections above).
2. Move the file back to its previous path if legacy tooling depends on the old layout.
3. Update import paths or scripts if the new structure should remain permanently.
4. Commit the reversion or open a pull request documenting the rationale.

## Related Documentation Updates
- `backend/processors/README.md` now lists active processors, archives, tests, and utility script locations.
- `README.md` project structure updated to reflect new directories and references this cleanup log for details.

For further questions or adjustments, consult this log and the updated READMEs.
