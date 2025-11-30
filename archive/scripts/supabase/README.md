# Archived Supabase Scripts

This directory contains Supabase-specific scripts that have been archived as part of the migration to PostgreSQL-only architecture.

## Archived Scripts

- `export_supabase_schema.py` - Exported Supabase schema for documentation
- `export_supabase_schema_python.py` - Python script to export Supabase schema
- `export_supabase_via_api.py` - Export Supabase data via API
- `reload_postgrest_via_supabase.py` - Reload PostgREST through Supabase
- `test_supabase_connection.py` - Test Supabase connection
- `generate_db_doc_from_supabase.py` - Generate database documentation from Supabase

## Migration Notes

These scripts were archived on 2025-11-28 as part of the complete migration from Supabase to native PostgreSQL. The system now uses:

- `PostgreSQLAdapter` instead of `SupabaseAdapter`
- Native PostgreSQL connection via asyncpg
- Raw SQL queries instead of Supabase client operations
- PostgreSQL-specific functions and features

## Alternatives

For similar functionality with PostgreSQL:

- Use `scripts/export_db_schema_csv.py` for schema export
- Use `scripts/test_postgresql_connection_simple.py` for connection testing
- Use `scripts/generate_db_doc_from_csv.py` for documentation generation

## Retention Policy

These scripts are kept for historical reference and can be safely deleted after 6 months (2026-05-28) if no longer needed.
