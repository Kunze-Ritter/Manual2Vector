# Supabase Deprecation Notice

## Status: Migration Complete ✅

The KRAI project completed its migration from Supabase to PostgreSQL in **November 2024 (KRAI-002)**.

### What Changed
- **Database**: Supabase → PostgreSQL with pgvector
- **Storage**: MinIO (S3-compatible) - See `docs/MIGRATION_R2_TO_MINIO.md` for migration details
- **Architecture**: Cloud-first → Local-first

### For New Users
- Use PostgreSQL-only configuration (see `DOCKER_SETUP.md`)
- All setup scripts generate PostgreSQL credentials
- No Supabase account needed

### For Existing Supabase Users
- See `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` for migration guide
- Supabase adapter is deprecated and will be removed in future versions
- Plan migration to PostgreSQL for continued support

### Documentation Status
- **Active**: PostgreSQL-only guides and examples
- **Reference**: Migration guides for legacy users
- **Deprecated**: n8n workflows (use Laravel Dashboard or FastAPI directly)

### Support Timeline
- **Current**: PostgreSQL-only (recommended)
- **Legacy**: Supabase adapter (deprecated, no new features)
- **Future**: Supabase adapter removal (TBD)

For questions, see the migration guide or contact support.
