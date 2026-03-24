# Laravel ↔ Python Upload Flow Fix Design
**Date:** 2026-03-24
**Status:** Approved
**Scope:** Backend (Python FastAPI) + Laravel Admin (KraiEngineService + docker-compose + env)

## Background

A thorough audit of the Laravel ↔ Python document upload flow revealed 15 issues ranging from critical (upload never reaching Python) to warnings (missing env vars). The upload endpoint URL is wrong, the multipart Content-Type header conflicts with the file upload, several Python endpoints are completely missing, and response field names don't match. This spec covers all fixes.

---

## Audit Summary

### Critical (breaks upload entirely)
- **C1** — Laravel calls `POST /documents/upload`; Python serves `POST /upload`
- **C2** — `createHttpClient()` sets `Content-Type: application/json` which conflicts with `attach()` multipart
- **C3** — `language` field sent by Laravel is hardcoded to `"en"` in Python's upload route; user value ignored
- **C4** — All stage/reprocess/status/video/thumbnail endpoints in `KraiEngineService` do not exist on Python

### Bugs (incorrect behaviour, may not block basic flow)
- **B1** — `getDocumentStatus`: wrong URL (`/documents/{id}/status`) + wrong field (`document_status` vs `status`)
- **B2** — `getAvailableStages`: response is wrapped in `SuccessResponse.data`; Laravel reads top level
- **B3** — `getStageStatus`: wrong path (`/stages/status` doesn't exist) + wrong field (`stage_status` vs `data.stages`)
- **B4** — `KRAI_SERVICE_JWT` not passed to `laravel-admin` container in `docker-compose.yml`

### Warnings
- **W1** — `KRAI_ENGINE_ADMIN_USERNAME` / `KRAI_ENGINE_ADMIN_PASSWORD` undocumented in `.env.example`
- **W2** — Auth router is commented out in `app.py` — `TokenService` fallback login always 404s

---

## Approach: Fix Both Sides (Option A)

Fix Laravel to call the correct existing Python URLs. Add the missing Python endpoints in a new dedicated router file. Normalise all API surface to `/api/v1/documents/{id}/...`.

---

## Area 1: New Python Endpoints

### New file: `backend/api/routes/document_processing.py`

Mounted in `app.py` under prefix `/api/v1`. All endpoints require Bearer JWT.

#### `GET /api/v1/documents/{document_id}/status`
Permission: `documents:read`

Returns document processing status. Reads from `krai_core.documents` (status, language, document_type) and `krai_system.stage_tracking` (current stage, progress).

Response:
```json
{
  "document_id": "uuid",
  "status": "pending|processing|completed|failed",
  "current_stage": "embedding",
  "progress": 0.75,
  "queue_position": 0,
  "total_queue_items": 0
}
```

#### `POST /api/v1/documents/{document_id}/reprocess`
Permission: `documents:write`

Resets document to allow full pipeline reprocessing:
1. DELETE from `krai_system.stage_tracking` WHERE `document_id = $1`
2. DELETE from `krai_system.completion_markers` WHERE `document_id = $1`
3. UPDATE `krai_core.documents` SET `processing_status = 'pending'` WHERE `id = $1`
4. Start `_process_document_background(document_id, context)` as FastAPI `BackgroundTask`

Response:
```json
{ "message": "Reprocessing queued", "document_id": "uuid", "status": "pending" }
```

#### `POST /api/v1/documents/{document_id}/process/stage/{stage_name}`
Permission: `documents:write`

Runs a single pipeline stage for the document. Validates `stage_name` against `CANONICAL_STAGES`. Starts the stage as a `BackgroundTask`.

Response:
```json
{ "stage": "embedding", "status": "queued", "document_id": "uuid" }
```

#### `POST /api/v1/documents/{document_id}/process/stages`
Permission: `documents:write`

Request body:
```json
{ "stages": ["text_extraction", "embedding"], "stop_on_error": true }
```

Runs stages sequentially (not as BackgroundTask — synchronous so caller gets results). Returns per-stage results.

Response:
```json
{
  "total_stages": 2,
  "successful": 2,
  "failed": 0,
  "success_rate": 1.0,
  "stage_results": [
    { "stage": "text_extraction", "success": true, "processing_time": 1.2, "data": {} },
    { "stage": "embedding", "success": true, "processing_time": 3.4, "data": {} }
  ]
}
```

#### `POST /api/v1/documents/{document_id}/process/video`
Permission: `documents:write`

Request body:
```json
{ "video_url": "https://...", "manufacturer_id": "uuid-or-null" }
```

Triggers `VideoEnrichmentProcessor` for the document. Returns enriched video metadata.

Response:
```json
{
  "video_id": "uuid",
  "title": "...",
  "platform": "youtube",
  "thumbnail_url": "...",
  "duration": 342,
  "channel_title": "..."
}
```

#### `POST /api/v1/documents/{document_id}/process/thumbnail`
Permission: `documents:write`

Request body:
```json
{ "page": 1, "size": [800, 600] }
```

Renders the specified page of the document PDF via PyMuPDF, saves the image to MinIO under `documents/{document_id}/thumbnail.png`, and returns the URL.

Response:
```json
{ "thumbnail_url": "https://...", "size": [800, 600], "file_size": 42318 }
```

---

## Area 2: Python Upload Route Fix

### Fix in `backend/api/app.py` — `POST /upload`

Read `language` from the multipart form field instead of hardcoding `"en"`:

```python
# BEFORE
context = ProcessingContext(..., language="en")

# AFTER
context = ProcessingContext(..., language=language or "en")
```

Add `language: str = Form("en")` to the endpoint signature.

---

## Area 3: Laravel `KraiEngineService` Fixes

### Fix 1 — Remove `Content-Type: application/json` from base client

`createHttpClient()` must not set `Content-Type`. File uploads use `->attach()` which sets `multipart/form-data` automatically. JSON requests use `->asJson()` explicitly on the call.

### Fix 2 — Upload URL

```php
// BEFORE
$endpoint = '/documents/upload';

// AFTER
$endpoint = '/upload';
```

Also add `->asMultipart()` (or rely on `->attach()`) and remove any Content-Type override on the upload call.

### Fix 3 — `getDocumentStatus`

```php
// BEFORE
$endpoint = "/documents/{$documentId}/status";
return $data['document_status'];

// AFTER
$endpoint = "/api/v1/documents/{$documentId}/status";
return $data['status'];
```

Also map `queue_position` and `total_queue_items` from response (these now exist in the new endpoint).

### Fix 4 — `getStageStatus`

```php
// BEFORE
$endpoint = "/documents/{$documentId}/stages/status";
$stageStatus = $data['stage_status'];

// AFTER
$endpoint = "/api/v1/documents/{$documentId}/stages";
$stageStatus = $data['data']['stages'] ?? [];
```

### Fix 5 — `getAvailableStages`

```php
// BEFORE
return $data['stages'];

// AFTER
return $data['data']['stages'] ?? [];
// Also: $data['data'] may have 'overall_progress', 'current_stage' etc — pass those through
```

### Fix 6 — All other endpoint URLs

Update to use the new `/api/v1/documents/{id}/...` paths:

| Method | Old URL | New URL |
|--------|---------|---------|
| `reprocessDocument` | `/documents/{id}/reprocess` | `/api/v1/documents/{id}/reprocess` |
| `processStage` | `/documents/{id}/process/stage/{name}` | `/api/v1/documents/{id}/process/stage/{name}` |
| `processMultipleStages` | `/documents/{id}/process/stages` | `/api/v1/documents/{id}/process/stages` |
| `processVideo` | `/documents/{id}/process/video` | `/api/v1/documents/{id}/process/video` |
| `generateThumbnail` | `/documents/{id}/process/thumbnail` | `/api/v1/documents/{id}/process/thumbnail` |

---

## Area 4: Docker + Environment

### `docker-compose.yml`

Add `KRAI_SERVICE_JWT` to the `laravel-admin` environment block:

```yaml
laravel-admin:
  environment:
    # ... existing vars ...
    KRAI_SERVICE_JWT: ${KRAI_SERVICE_JWT:-}
```

### `laravel-admin/.env.example`

Document `KRAI_ENGINE_ADMIN_USERNAME` and `KRAI_ENGINE_ADMIN_PASSWORD` (used by `TokenService` for auto-refresh login):

```
KRAI_ENGINE_ADMIN_USERNAME=admin
KRAI_ENGINE_ADMIN_PASSWORD=changeme
```

### Root `.env.example`

Add `KRAI_SERVICE_JWT` with generation hint:
```
# Service-to-service JWT for Laravel → Python API calls
# Generate with: python scripts/generate_service_token.py
KRAI_SERVICE_JWT=
```

---

## Out of Scope

- Auth router re-enabling (`app.py` comment-out) — tracked separately
- `TokenService` auto-refresh in `KraiEngineService` (static JWT only for now)
- Filament UI changes for the new endpoints (existing UI already calls the correct methods)
- Pipeline stage name normalisation (chunk_prep vs CHUNK_PREPROCESSING)
