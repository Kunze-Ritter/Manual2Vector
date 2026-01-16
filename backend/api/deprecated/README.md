# Deprecated Scripts

These scripts were used during Supabase migration and are no longer maintained.
They have been replaced by PostgreSQL versions using:

- DatabaseAdapter pattern (`backend/services/database_adapter.py`)
- Direct asyncpg queries via `get_pool()` (`backend/services/db_pool.py`)

## Deprecated Test Scripts

The following scripts used Supabase's PostgREST API and have been replaced:

- `test_error_C9402.py` → `test_error_C9402_postgresql.py`
- `test_semantic_C9402.py` → `test_semantic_C9402_postgresql.py`
- `test_part_41X5345.py` → `test_part_41X5345_postgresql.py`
- `check_error_code_in_db.py` → `check_error_code_in_db_postgresql.py`
- `test_tools_directly.py` → `test_tools_directly_postgresql.py`

## For Testing

Use pytest test suites in `tests/` directory instead of these ad-hoc scripts.

## Migration Notes

All new scripts should:

1. Use `get_pool()` from `services.db_pool` for database connections
2. Use raw SQL queries with asyncpg
3. Follow async/await pattern
4. Reference `DATABASE_SCHEMA.md` for table/column names
