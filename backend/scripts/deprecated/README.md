# Deprecated Scripts

This directory contains scripts that have been deprecated and are no longer actively maintained.

## Deprecation Policy

Scripts are moved here when:
1. They have been replaced by newer implementations
2. They are no longer compatible with the current system architecture
3. They use deprecated dependencies (e.g., Supabase client instead of PostgreSQL)

## Scripts Previously Deprecated

The following scripts were mentioned for deprecation but were not found in the codebase:
- `check_images.py` - Not found (may have been removed earlier)
- `check_links_in_db.py` - Replaced by `scripts/check_and_fix_links.py`
- `cleanup_duplicate_error_codes.py` - Not found (may have been removed earlier)
- `duplicate_cleanup.py` - Not found (may have been removed earlier)
- `image_duplicate_cleanup.py` - Not found (may have been removed earlier)

## Archived Scripts

### verify_deduplication_supabase.py
**Archived:** 2025-01-15  
**Reason:** Uses deprecated Supabase client (`DatabaseService`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`)  
**Replacement:** Use `backend/scripts/verify_deduplication_postgresql.py` which uses PostgreSQL adapter with `get_pool()`  
**Migration:** Full PostgreSQL migration completed - all Supabase references removed from active codebase

## Migration to PostgreSQL (2025-01-15)

All scripts in `backend/scripts/` have been migrated from Supabase to PostgreSQL using `asyncpg` and `get_pool()`:
- `check_chunk_ids.py` ✅
- `link_error_codes_to_images.py` ✅
- `link_existing_error_codes_to_chunks.py` ✅
- `update_document_series.py` ✅
- `verify_error_code_images.py` ✅
- `verify_deduplication.py` → `verify_deduplication_postgresql.py` ✅ (original archived as `verify_deduplication_supabase.py`)
- `run_migration_error_code_images.py` ✅ (refactored to use asyncpg)

CLI scripts in `scripts/` have also been migrated:
- `research_product.py` ✅
- `sync_oem_to_database.py` ✅
- `check_and_fix_links.py` ✅

## Notes

- If you need to reference old Supabase-based code, check git history before 2025-01-15
- All new scripts should use `asyncpg` with `get_pool()` from `services.db_pool`
- Follow the migration patterns documented in the project rules
