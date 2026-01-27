# Deprecated Environment Variables

## 📋 Purpose

This document tracks all deprecated environment variables in the KRAI project. Use this as a quick reference when encountering old variables in documentation or scripts.

## ⏱️ Migration Timeline

- **Deprecation Date:** Q4 2024
- **Removal Date:** TBD (variables remain commented in `.env` files for reference)
- **Migration Guide:** See `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md`

---

## 🗄️ Deprecated Database Variables

| Variable Name | Deprecated Since | Replaced By | Migration Notes |
|---------------|------------------|-------------|-----------------|
| `SUPABASE_URL` | 2024-Q4 | `DATABASE_CONNECTION_URL` | Use PostgreSQL connection string |
| `SUPABASE_ANON_KEY` | 2024-Q4 | *(not needed)* | PostgreSQL uses password authentication |
| `SUPABASE_SERVICE_ROLE_KEY` | 2024-Q4 | *(not needed)* | PostgreSQL uses password authentication |
| `SUPABASE_STORAGE_URL` | 2024-Q4 | `OBJECT_STORAGE_ENDPOINT` | Use MinIO endpoint |
| `SUPABASE_DB_PASSWORD` | 2024-Q4 | `DATABASE_PASSWORD` | Direct PostgreSQL password |
| `DATABASE_URL` | 2024-Q4 | `DATABASE_CONNECTION_URL` | Renamed for clarity |

### Migration Example

**Old (Supabase):**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

**New (PostgreSQL):**
```bash
DATABASE_TYPE=postgresql
DATABASE_HOST=krai-postgres
DATABASE_PORT=5432
DATABASE_NAME=krai
DATABASE_USER=krai_user
DATABASE_PASSWORD=<secure-password>
DATABASE_CONNECTION_URL=postgresql://krai_user:<password>@krai-postgres:5432/krai
```

---

## 📦 Deprecated Storage Variables

| Variable Name | Deprecated Since | Replaced By | Migration Notes |
|---------------|------------------|-------------|-----------------|
| `R2_ACCESS_KEY_ID` | 2024-Q4 | `OBJECT_STORAGE_ACCESS_KEY` | MinIO access key |
| `R2_SECRET_ACCESS_KEY` | 2024-Q4 | `OBJECT_STORAGE_SECRET_KEY` | MinIO secret key |
| `R2_ENDPOINT_URL` | 2024-Q4 | `OBJECT_STORAGE_ENDPOINT` | MinIO S3-compatible endpoint |
| `R2_BUCKET_NAME_DOCUMENTS` | 2024-Q4 | *(managed by MinIO)* | Buckets created automatically |
| `R2_REGION` | 2024-Q4 | `OBJECT_STORAGE_REGION` | AWS region identifier |
| `R2_PUBLIC_URL_DOCUMENTS` | 2024-Q4 | `OBJECT_STORAGE_PUBLIC_URL` | Single public URL for all buckets |
| `R2_PUBLIC_URL_ERROR` | 2024-Q4 | `OBJECT_STORAGE_PUBLIC_URL` | Single public URL for all buckets |
| `R2_PUBLIC_URL_PARTS` | 2024-Q4 | `OBJECT_STORAGE_PUBLIC_URL` | Single public URL for all buckets |
| `UPLOAD_IMAGES_TO_R2` | 2024-Q4 | *(not needed)* | MinIO is default storage |
| `UPLOAD_DOCUMENTS_TO_R2` | 2024-Q4 | *(not needed)* | MinIO is default storage |
| `MINIO_ENDPOINT` | 2024-Q4 | `OBJECT_STORAGE_ENDPOINT` | Renamed for consistency |
| `MINIO_ACCESS_KEY` | 2024-Q4 | `OBJECT_STORAGE_ACCESS_KEY` | Renamed for consistency |
| `MINIO_SECRET_KEY` | 2024-Q4 | `OBJECT_STORAGE_SECRET_KEY` | Renamed for consistency |

### Migration Example

**Old (Cloudflare R2):**
```bash
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_ENDPOINT_URL=https://your-account-id.eu.r2.cloudflarestorage.com
R2_BUCKET_NAME_DOCUMENTS=your-bucket-name
R2_PUBLIC_URL_DOCUMENTS=https://pub-your-documents-bucket.r2.dev
R2_PUBLIC_URL_ERROR=https://pub-your-error-bucket.r2.dev
R2_PUBLIC_URL_PARTS=https://pub-your-parts-bucket.r2.dev
```

**New (MinIO):**
```bash
OBJECT_STORAGE_TYPE=s3
OBJECT_STORAGE_ENDPOINT=http://krai-minio:9000
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=<secure-password>
OBJECT_STORAGE_REGION=us-east-1
OBJECT_STORAGE_USE_SSL=false
OBJECT_STORAGE_PUBLIC_URL=http://localhost:9000
```

---

## 🤖 Deprecated AI Service Variables

| Variable Name | Deprecated Since | Replaced By | Migration Notes |
|---------------|------------------|-------------|-----------------|
| `OLLAMA_BASE_URL` | 2024-Q4 | `OLLAMA_URL` | Simplified naming convention |
| `AI_SERVICE_URL` | 2024-Q4 | `OLLAMA_URL` | Consolidated into single variable |

### Migration Example

**Old:**
```bash
OLLAMA_BASE_URL=http://krai-ollama:11434
AI_SERVICE_URL=http://krai-ollama:11434
```

**New:**
```bash
OLLAMA_URL=http://krai-ollama:11434
```

---

## 🔧 Migration Instructions

### Step 1: Identify Deprecated Variables

Search your `.env` file for deprecated variables:

```bash
# Linux/macOS
grep -E "SUPABASE_|R2_|OLLAMA_BASE_URL|AI_SERVICE_URL|MINIO_ENDPOINT" .env

# Windows (PowerShell)
Select-String -Path .env -Pattern "SUPABASE_|R2_|OLLAMA_BASE_URL|AI_SERVICE_URL|MINIO_ENDPOINT"
```

### Step 2: Update Configuration

Use the mapping tables above to replace deprecated variables with their modern equivalents.

### Step 3: Validate Configuration

Run the validation script to ensure all required variables are set:

```bash
python scripts/validate_env.py --verbose
```

### Step 4: Test Services

Verify that all services start correctly with the new configuration:

```bash
docker-compose up -d
docker-compose ps
curl http://localhost:8000/health
```

---

## 📊 Impact Assessment

### Components Affected by Deprecation

**Database Variables:**
- Backend API (`backend/api/`)
- Database adapters (`backend/services/database_factory.py`)
- Migration scripts (`database/migrations/`)
- Test suites (`tests/`)
- Utility scripts (`scripts/`)

**Storage Variables:**
- Storage adapters (`backend/services/storage/`)
- Upload endpoints (`backend/api/routes/upload.py`)
- Document processing (`backend/processors/`)
- Laravel dashboard image loading (`laravel-admin/resources/`)

**AI Service Variables:**
- AI service clients (`backend/services/ai/`)
- Ollama integration (`backend/services/ollama_service.py`)
- Processing pipelines (`backend/processors/`)

### Scripts Requiring Updates

Most scripts have been updated to use the adapter pattern. Legacy scripts that may still reference deprecated variables:

- Check `scripts/README_MIGRATION.md` for migration status
- Run `grep -r "SUPABASE_URL" scripts/` to find remaining references
- Update scripts to use `create_database_adapter()` from `backend/services/database_factory.py`

### Documentation Files Requiring Updates

The following documentation files have been updated to reflect the new variable names:

- ✅ `.env` - Deprecated variables commented out
- ✅ `.env.example` - Deprecated variables commented out
- ✅ `DEPLOYMENT.md` - Updated examples
- ✅ `README.md` - Updated configuration section
- ✅ `DOCKER_SETUP.md` - Updated variable lists
- ✅ `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` - Comprehensive migration guide
- ✅ `docs/setup/DEPRECATED_VARIABLES.md` - This document

---

## ⏰ Deprecation Timeline

### Current Status (2024-Q4)

- **Status:** Deprecated but supported
- **Action:** Variables are commented out in `.env` files
- **Support:** Can be uncommented for legacy deployments
- **Recommendation:** Migrate to PostgreSQL + MinIO

### Future Plans

- **Q1 2025:** Warning messages when deprecated variables are detected
- **Q2 2025:** Deprecation notices in logs
- **Q3 2025:** Potential removal of Supabase adapter (TBD based on usage)
- **Q4 2025:** Complete removal of deprecated variable support (TBD)

**Note:** Timeline is subject to change based on community feedback and usage patterns.

---

## ❓ FAQ

### Why were these variables deprecated?

The project migrated from cloud-based Supabase and Cloudflare R2 to local-first PostgreSQL and MinIO for better data sovereignty, reduced costs, and improved performance.

### Can I still use Supabase/R2?

Yes, but it's not recommended. Uncomment the deprecated variables in your `.env` file and set `DATABASE_TYPE=supabase`. However, support may be removed in future versions.

### What if I have existing deployments using these variables?

Existing deployments will continue to work. However, we recommend migrating to PostgreSQL + MinIO for better long-term support. See `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` for migration instructions.

### How do I report issues with the migration?

- Check the migration guide: `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md`
- Run diagnostics: `python scripts/validate_env.py --verbose`
- Check Docker logs: `docker-compose logs`
- Review this document for variable mappings

### Will deprecated variables be removed?

Potentially, but not immediately. We will provide ample warning and migration time. The current plan is to keep them commented in `.env` files indefinitely for reference.

### What about scripts that use deprecated variables?

Most scripts have been updated to use the adapter pattern. For scripts that still use deprecated variables:
1. Check `scripts/README_MIGRATION.md` for migration examples
2. Update to use `create_database_adapter()` from `backend/services/database_factory.py`
3. Replace direct Supabase/R2 calls with adapter methods

---

## 📚 Related Documentation

- [Supabase to PostgreSQL Migration Guide](../SUPABASE_TO_POSTGRESQL_MIGRATION.md)
- [Environment Variables Reference](../ENVIRONMENT_VARIABLES_REFERENCE.md)
- [Database Schema Documentation](../../DATABASE_SCHEMA.md)
- [Adapter Migration Guide](../database/ADAPTER_MIGRATION.md)
- [Script Migration README](../../scripts/README_MIGRATION.md)
- [Deployment Guide](../../DEPLOYMENT.md)
- [Docker Setup Guide](../../DOCKER_SETUP.md)

---

**Last Updated:** 2024-11-18  
**Deprecation Status:** Active (variables commented out in `.env` files)  
**Support Status:** PostgreSQL + MinIO (Production), Supabase + R2 (Deprecated)
