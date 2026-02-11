# Migration Guide: R2 to MinIO-Only Storage

## Overview

As of this release, Cloudflare R2 support has been **completely removed** from KRAI-Engine. The system now exclusively uses MinIO (S3-compatible) object storage. This change simplifies the codebase and eliminates configuration ambiguity.

## Why This Change?

1. **Simplification**: MinIO is S3-compatible and provides all necessary features
2. **Consistency**: Single storage backend reduces configuration complexity
3. **Maintainability**: Fewer code paths and fallback logic to maintain
4. **Clarity**: No ambiguity about which storage system is "the truth"

## Breaking Changes

### Environment Variables Removed

All `R2_*` environment variables are **no longer supported** and will cause the application to fail at startup if detected.

### Variable Mapping

| Old R2 Variable | New OBJECT_STORAGE Variable | Notes |
|----------------|----------------------------|-------|
| `R2_ACCESS_KEY_ID` | `OBJECT_STORAGE_ACCESS_KEY` | MinIO access key |
| `R2_SECRET_ACCESS_KEY` | `OBJECT_STORAGE_SECRET_KEY` | MinIO secret key |
| `R2_ENDPOINT_URL` | `OBJECT_STORAGE_ENDPOINT` | MinIO endpoint (e.g., http://localhost:9000) |
| `R2_BUCKET_NAME_DOCUMENTS` | `OBJECT_STORAGE_BUCKET_DOCUMENTS` | Documents bucket name |
| `R2_BUCKET_NAME_ERROR` | `OBJECT_STORAGE_BUCKET_ERROR` | Error images bucket name |
| `R2_BUCKET_NAME_PARTS` | `OBJECT_STORAGE_BUCKET_PARTS` | Parts images bucket name |
| `R2_PUBLIC_URL_DOCUMENTS` | `OBJECT_STORAGE_PUBLIC_URL_DOCUMENTS` | Public URL for documents |
| `R2_PUBLIC_URL_ERROR` | `OBJECT_STORAGE_PUBLIC_URL_ERROR` | Public URL for error images |
| `R2_PUBLIC_URL_PARTS` | `OBJECT_STORAGE_PUBLIC_URL_PARTS` | Public URL for parts images |
| `UPLOAD_IMAGES_TO_R2` | `UPLOAD_IMAGES_TO_STORAGE` | Enable image uploads |
| `UPLOAD_DOCUMENTS_TO_R2` | `UPLOAD_DOCUMENTS_TO_STORAGE` | Enable document uploads |
| `R2_USE_SSL` | `OBJECT_STORAGE_USE_SSL` | Enable SSL for storage |
| `R2_REGION` | `OBJECT_STORAGE_REGION` | Storage region (default: auto) |

## Migration Steps

### Step 1: Update Environment Variables

1. Open your `.env` file
2. Replace all `R2_*` variables with their `OBJECT_STORAGE_*` equivalents
3. Remove any `R2_*` variables from your configuration

**Before:**
```bash
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
R2_BUCKET_NAME_DOCUMENTS=documents
UPLOAD_IMAGES_TO_R2=true
```

**After:**
```bash
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=minioadmin
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_BUCKET_DOCUMENTS=documents
UPLOAD_IMAGES_TO_STORAGE=true
```

### Step 2: Verify Configuration

Run the application startup validation:

```bash
python backend/main.py
```

If any R2 variables are detected, you'll see an error message:

```
❌ R2 variables detected: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
R2 support has been removed. Please use OBJECT_STORAGE_* variables instead.
See .env.example and docs/MIGRATION_R2_TO_MINIO.md for migration guide.
```

### Step 3: Data Migration (If Needed)

If you have existing data in R2 that needs to be migrated to MinIO:

1. **Export from R2**: Use `rclone` or AWS CLI to download objects
2. **Import to MinIO**: Use MinIO client (`mc`) to upload objects
3. **Update Database References**: Ensure storage URLs in database point to MinIO

**Example using rclone:**
```bash
# Configure R2 remote
rclone config

# Sync R2 to local
rclone sync r2:your-bucket ./local-backup

# Configure MinIO remote
rclone config

# Sync local to MinIO
rclone sync ./local-backup minio:documents
```

### Step 4: Test Storage Operations

Verify that storage operations work correctly:

```bash
# Test image upload
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.pdf"

# Check health endpoint
curl http://localhost:8000/health
```

## Troubleshooting

### Application Fails to Start

**Error:** `R2 variables detected`

**Solution:** Remove all `R2_*` variables from your `.env` file and replace with `OBJECT_STORAGE_*` equivalents.

### Storage Connection Failed

**Error:** `Failed to connect to object storage`

**Solution:** Verify MinIO is running and `OBJECT_STORAGE_ENDPOINT` is correct:

```bash
# Check MinIO is running
docker ps | grep minio

# Test MinIO endpoint
curl http://localhost:9000/minio/health/live
```

### Images Not Uploading

**Error:** `Storage not configured`

**Solution:** Ensure `UPLOAD_IMAGES_TO_STORAGE=true` is set in your `.env` file.

## Support

For questions or issues with migration:

1. Check `.env.example` for reference configuration
2. Review MinIO documentation: https://min.io/docs/
3. Verify Docker Compose configuration includes MinIO service

## Rollback (Not Recommended)

If you need to temporarily rollback to a version with R2 support, you must use a previous version of the codebase. However, this is **not recommended** as R2 support will not receive updates or bug fixes.
