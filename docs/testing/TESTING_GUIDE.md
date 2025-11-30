# Post-Migration Testing Guide

## Pre-Migration (Backup)

- Export Supabase data: `pg_dump ... > backup.sql`

## Database Connectivity

- [ ] `scripts/test_postgresql_connection_simple.py` → ✅ Connected
- [ ] `DATABASE_TYPE=postgresql` in `.env`
- [ ] Adapter: `python -c "from backend.services.database_factory import create_database_adapter; print('✅')"`

## API Endpoints

- [ ] Health: `curl localhost:8000/health` → `status: healthy`
- [ ] Documents: `curl /api/v1/documents` → JSON list
- [ ] CRUD: Create/update/delete document → 200 OK
- [ ] Error codes/images/videos/products → No 500s
- [ ] Batch: `curl /api/v1/batch/delete` → Task queued

## Pipeline

- [ ] `scripts/pipeline_processor.py <doc_id>` → Parts/series extracted
- [ ] Parts: `backend/processors/parts_processor.py <doc_id>` → Stats printed
- [ ] Series: Verify `krai_core.product_series` populated

## Monitoring

- [ ] `scripts/test_monitoring.py` → All tests ✅
- [ ] Metrics: `curl /api/v1/monitoring/metrics` → JSON
- [ ] Alerts: Background loop starts

## Storage

- [ ] Upload document → File in MinIO `documents/` bucket
- [ ] Images extracted → `images/` bucket populated

## Rollback

- [ ] `git checkout HEAD~1 -- .env.example` → Supabase restored

## Performance

- Query time <500ms; compare before/after benchmarks

---

**Migration Status**: ✅ **COMPLETED**
**Date**: 2025-01-09
**Next Steps**: Monitor production performance and optimize queries as needed
