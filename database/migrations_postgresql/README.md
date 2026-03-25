# KRAI PostgreSQL Migrations

**Last Updated:** 2026-03-25
**Status:** Active SQL migration directory for the current repository state

## Important

- This folder is the active PostgreSQL migration set used by the repo.
- It is no longer a 3-file or 4-file "consolidated" migration bundle.
- The current repo contains migration files from `001` through `029`.
- Some numeric prefixes appear more than once, for example `004`, `005`, and `009`.
  These are historical variants or follow-up migrations. Check the full filename and
  the target schema state before applying them to a live database.
- Do not assume every file in this folder should be executed blindly on every environment.

## Practical Use

For a fresh PostgreSQL bootstrap, start with:

1. `001_core_schema.sql`
2. `002_views.sql`
3. `003_functions.sql`

After that, review the later files in this directory and apply the migrations that
match your deployment path and current schema state.

Examples of additive topics covered here:

- stage tracking
- manufacturer verification cache
- firecrawl queue tables and fixes
- product discovery columns
- pipeline resilience
- stage metrics
- video enrichment columns
- error code hierarchy
- processing queue extensions
- vector indexes
- match-function fixes

## Current Repo Range

- Base bootstrap: `001` to `003`
- Additional migrations currently present up to `029_fix_match_functions.sql`
- Canonical table/column reference: `../../DATABASE_SCHEMA.md`

## Verification

Use the database migration table and schema inspection queries before and after changes:

```sql
SELECT * FROM krai_system.migrations ORDER BY applied_at;

SELECT nspname
FROM pg_namespace
WHERE nspname LIKE 'krai_%'
ORDER BY nspname;

SELECT viewname
FROM pg_views
WHERE schemaname = 'public' AND viewname LIKE 'vw_%'
ORDER BY viewname;
```

## Related Docs

- `../README.md`
- `../migrations/README.md`
- `../../DATABASE_SCHEMA.md`
