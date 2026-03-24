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

Returns document processing status. Reads from `krai_core.documents`: `processing_status`, `stage_status` (JSONB), `language`, `document_type`. Derive `current_stage` and `progress` from `stage_status` JSONB (the authoritative pipeline state) — do **not** read from `krai_system.stage_tracking`. Uses a new `DocumentProcessingStatusResponse` Pydantic model (add to `backend/api/routes/response_models.py`; distinct from the existing `DocumentStatusResponse` which has field `document_status`).

**Note:** An existing `GET /status/{document_id}` endpoint lives at the app root (not under `/api/v1/`). The new endpoint is distinct and follows the `/api/v1/documents/` prefix convention. The old root-level endpoint is left unchanged.

All new endpoints in `document_processing.py` wrap their payload in `SuccessResponse` (consistent with `documents.py`). Laravel reads fields from `$data['data'][...]`.

Response wrapped in `SuccessResponse`:
```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "status": "pending|processing|completed|failed",
    "current_stage": "embedding",
    "progress": 0.75,
    "queue_position": 0,
    "total_queue_items": 0
  }
}
```

Laravel reads: `$data['data']['status']`, `$data['data']['current_stage']`, etc.

#### `POST /api/v1/documents/{document_id}/reprocess`
Permission: `documents:write`

Resets document to allow full pipeline reprocessing. The pipeline uses `krai_core.documents.stage_status` (JSONB) as the authoritative stage state — not `stage_tracking` rows. Steps:
1. UPDATE `krai_core.documents` SET `processing_status = 'pending'`, `stage_status = '{}'::jsonb` WHERE `id = $1`
2. DELETE from `krai_system.stage_tracking` WHERE `document_id = $1` (cleanup, guarded — table may not exist in all environments)
3. DELETE from `krai_system.completion_markers` WHERE `document_id = $1` (guarded with IF EXISTS / try-except)
4. Start `_process_document_background(document_id, context)` as FastAPI `BackgroundTask`

Response wrapped in `SuccessResponse`:
```json
{ "success": true, "data": { "message": "Reprocessing queued", "document_id": "uuid", "status": "pending" } }
```

#### `POST /api/v1/documents/{document_id}/process/stage/{stage_name}`
Permission: `documents:write`

Runs a single pipeline stage for the document. Validates `stage_name` against `CANONICAL_STAGES`. Starts as a `BackgroundTask`.

Response wrapped in `SuccessResponse`:
```json
{ "success": true, "data": { "stage": "embedding", "status": "queued", "document_id": "uuid" } }
```

#### `POST /api/v1/documents/{document_id}/process/stages`
Permission: `documents:write`

Request body:
```json
{ "stages": ["text_extraction", "embedding"], "stop_on_error": true }
```

Runs stages sequentially (synchronous — caller receives per-stage results). Reuses the existing `StageProcessingResponse` model from `backend/api/routes/response_models.py`. Note: `StageProcessingResponse` has a `success: bool` field that will be redundant when nested inside `SuccessResponse.data` — this is acceptable; implementer should use `SuccessResponse[StageProcessingResponse]` as `response_model`.

See Area 3 Fix 7 for the `$uploadTimeout` constructor change that enables this.

Response wrapped in `SuccessResponse` using `StageProcessingResponse`:
```json
{
  "success": true,
  "data": {
    "total_stages": 2,
    "successful": 2,
    "failed": 0,
    "success_rate": 1.0,
    "stage_results": [
      { "stage": "text_extraction", "success": true, "processing_time": 1.2, "data": {} },
      { "stage": "embedding", "success": true, "processing_time": 3.4, "data": {} }
    ]
  }
}
```

#### `GET /api/v1/documents/{document_id}/stages`
Permission: `documents:read`

Returns per-stage completion status for a specific document. Reads `stage_status` from `krai_core.documents.stage_status` (JSONB). Uses existing `StageStatusResponse` model from `backend/api/routes/response_models.py` (fields: `document_id`, `stage_status: Dict[str, str]`). The existing `StageStatusResponse` model already has `found: bool` (no change needed to the model). Include `found` in the response body.

Response wrapped in `SuccessResponse`:
```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "stage_status": { "text_extraction": "completed", "embedding": "pending" },
    "found": true
  }
}
```

On 404 (document not found): return `SuccessResponse` with `found: false` and empty `stage_status: {}`.

Laravel reads: `$data['data']['stage_status']` → associative array, `$data['data']['found']` → bool, `$data['data']['document_id']`.

#### `GET /api/v1/stages/names`
Permission: `documents:read`

Returns the global list of canonical stage names available for processing. `CANONICAL_STAGES` is application-level and identical for all documents, so this endpoint is **not** document-scoped. Used by `getAvailableStages` in Laravel to populate stage selection UI. Uses existing `StageListResponse` model from `backend/api/routes/response_models.py` (fields: `stages: List[str]`, `total: int`).

Response wrapped in `SuccessResponse`:
```json
{
  "success": true,
  "data": {
    "stages": ["text_extraction", "table_extraction", "embedding", "search_indexing"],
    "total": 16
  }
}
```

Laravel reads: `$data['data']['stages']` → plain `array` of stage name strings, `$data['data']['total']` → count.

#### `POST /api/v1/documents/{document_id}/process/video`
Permission: `documents:write`

Request body:
```json
{ "video_url": "https://...", "manufacturer_id": "uuid-or-null" }
```

Triggers `VideoEnrichmentProcessor` for the document. Returns enriched video metadata wrapped in `SuccessResponse`.

Response wrapped in `SuccessResponse`:
```json
{
  "success": true,
  "data": {
    "video_id": "uuid",
    "title": "...",
    "platform": "youtube",
    "thumbnail_url": "...",
    "duration": 342,
    "channel_title": "..."
  }
}
```

#### `POST /api/v1/documents/{document_id}/process/thumbnail`
Permission: `documents:write`

Request body:
```json
{ "page": 0, "size": [800, 600] }
```

The `page` field is **0-indexed** (consistent with the existing `ThumbnailGenerationRequest` model in `backend/api/routes/response_models.py`). Page `0` = first page.

Renders the specified page of the document PDF via PyMuPDF, saves the image to MinIO under `documents/{document_id}/thumbnail.png`, and returns the URL wrapped in `SuccessResponse`.

Response wrapped in `SuccessResponse`:
```json
{
  "success": true,
  "data": { "thumbnail_url": "https://...", "size": [800, 600], "file_size": 42318 }
}
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

`createHttpClient()` must not set `Content-Type`. File uploads use `->attach()` which sets `multipart/form-data` automatically.

After removing `Content-Type: application/json` from the base client, Laravel's HTTP client will default to `application/x-www-form-urlencoded` for positional array payloads. Add `->asJson()` explicitly to every non-upload call that sends a request body:

| Method | Change |
|--------|--------|
| `processMultipleStages` | Add `->asJson()` before `->post(...)` |
| `processVideo` | Add `->asJson()` before `->post(...)` |
| `generateThumbnail` | Add `->asJson()` before `->post(...)` |

Methods with no body (`reprocessDocument`, `processStage`) and GET requests need no `->asJson()`.

### Fix 2 — Upload URL

```php
// BEFORE
$endpoint = '/documents/upload';

// AFTER
$endpoint = '/upload';
```

The Content-Type conflict is already resolved by Fix 1 (removing it from `createHttpClient()`). No additional change needed on the upload call itself — `->attach()` will set `multipart/form-data` automatically once the base client no longer overrides it.

### Fix 3 — `getDocumentStatus`

```php
// BEFORE
$endpoint = "/documents/{$documentId}/status";
return [
    'success' => true,
    'document_status' => $data['document_status'] ?? 'unknown',
    ...
];

// AFTER
$endpoint = "/api/v1/documents/{$documentId}/status";
return [
    'success' => true,
    'status' => $data['data']['status'] ?? 'unknown',
    'current_stage' => $data['data']['current_stage'] ?? null,
    'progress' => $data['data']['progress'] ?? 0,
    'queue_position' => $data['data']['queue_position'] ?? 0,
    'total_queue_items' => $data['data']['total_queue_items'] ?? 0,
];
```

**Note:** The PHP return array key changes from `'document_status'` to `'status'`. Known callers that must be updated:
- `laravel-admin/app/Filament/Resources/Documents/Pages/EditDocument.php:101` — reads `$result['document_status']` → change to `$result['status']`

Run `grep -r "document_status\|getDocumentStatus" laravel-admin/` to confirm no other callers are missed before completing this fix.

### Fix 4 — `getStageStatus`

```php
// BEFORE
$endpoint = "/documents/{$documentId}/stages/status";
// reads: $data['document_id'], $data['stage_status']

// AFTER
$endpoint = "/api/v1/documents/{$documentId}/stages";
// on success:
return [
    'success' => true,
    'document_id' => $data['data']['document_id'] ?? $documentId,
    'stage_status' => $data['data']['stage_status'] ?? [],
    'found' => $data['data']['found'] ?? false,
];
// on failure: keep existing error return unchanged
```

**Dead branch removal:** The existing `elseif ($response->status() === 404)` branch returns `found: false`. The new Python endpoint no longer returns HTTP 404 for missing documents — it returns HTTP 200 with `found: false` in the body instead. Remove the `elseif (404)` branch; it will never be reached.

### Fix 5 — `getAvailableStages`

Call the new global `GET /api/v1/stages/names` endpoint (stage list is application-level, not document-specific). Remove the `$documentId` parameter from the method signature. A project-wide search (`grep -r "getAvailableStages"`) confirms there are no call sites outside `KraiEngineService.php` itself, so no external callers need updating.

```php
// BEFORE
public function getAvailableStages(string $documentId): array
    $endpoint = "/documents/{$documentId}/stages";
    // success return:
    return [
        'success' => true,
        'stages' => $data['stages'] ?? [],
        'total' => $data['total'] ?? 0,
    ];

// AFTER
public function getAvailableStages(): array   // $documentId removed
    $endpoint = "/api/v1/stages/names";
    // success return:
    return [
        'success' => true,
        'stages' => $data['data']['stages'] ?? [],
        'total' => $data['data']['total'] ?? 0,
    ];
```

### Fix 6 — All other endpoint URLs + response field paths

All new Python endpoints wrap their payload in `SuccessResponse`, so every method that previously read `$data['field']` must now read `$data['data']['field']`. Update both the URL and the field reads together.

#### `reprocessDocument`
```php
// URL: /documents/{id}/reprocess → /api/v1/documents/{id}/reprocess
// Field reads:
'message'     => $data['data']['message']     ?? 'Document reprocessing started',
'document_id' => $data['data']['document_id'] ?? $documentId,
'status'      => $data['data']['status']      ?? 'started',
```

#### `processStage`
```php
// URL: /documents/{id}/process/stage/{name} → /api/v1/documents/{id}/process/stage/{name}
// Field reads (response is { stage, status, document_id } — background task, no processing_time):
'stage'       => $data['data']['stage']       ?? $stageName,
'status'      => $data['data']['status']      ?? 'queued',
'document_id' => $data['data']['document_id'] ?? $documentId,
// Remove: 'data' => $data and 'processing_time' => $data['processing_time']
```

**Caller update required:** `EditDocument.php:153` references `$result['processing_time']` in a `sprintf` notification body. Remove that field reference — replace with a message like `'Stage "%s" wurde zur Verarbeitung eingereiht'` (no timing available since the stage runs in background).

#### `processMultipleStages`
```php
// URL: /documents/{id}/process/stages → /api/v1/documents/{id}/process/stages
// Field reads:
'total_stages'  => $data['data']['total_stages']  ?? count($stages),
'successful'    => $data['data']['successful']    ?? 0,
'failed'        => $data['data']['failed']        ?? 0,
'stage_results' => $data['data']['stage_results'] ?? [],
'success_rate'  => $data['data']['success_rate']  ?? 0,
```

#### `processVideo`
```php
// URL: /documents/{id}/process/video → /api/v1/documents/{id}/process/video
// Field reads:
'video_id'      => $data['data']['video_id']      ?? null,
'title'         => $data['data']['title']         ?? null,
'platform'      => $data['data']['platform']      ?? null,
'thumbnail_url' => $data['data']['thumbnail_url'] ?? null,
'duration'      => $data['data']['duration']      ?? null,
'channel_title' => $data['data']['channel_title'] ?? null,
```

#### `generateThumbnail`
```php
// URL: /documents/{id}/process/thumbnail → /api/v1/documents/{id}/process/thumbnail
// Field reads:
'thumbnail_url' => $data['data']['thumbnail_url'] ?? null,
'size'          => $data['data']['size']          ?? $size,
'file_size'     => $data['data']['file_size']     ?? null,
```

### Fix 7 — Add `$uploadTimeout` to `KraiEngineService`

`$defaultTimeout = 120` is too short for multi-stage pipeline processing. Add to constructor:

```php
public function __construct(
    string $baseUrl,
    string $serviceToken,
    int $defaultTimeout = 120,
    int $queryTimeout = 60,
    int $uploadTimeout = 600  // NEW
)
```

Use `$this->uploadTimeout` for `processMultipleStages` (passes to `createHttpClient($this->uploadTimeout)`).

---

## Area 4: Docker + Environment

### `docker-compose.yml`

Add `KRAI_SERVICE_JWT`, `KRAI_ENGINE_ADMIN_USERNAME`, and `KRAI_ENGINE_ADMIN_PASSWORD` to the `laravel-admin` environment block (all three are consumed at runtime via `env()` in `KraiEngineService` and `TokenService`). Match the existing list-style format in the file (`- KEY=${VAR:-}`):

```yaml
laravel-admin:
  environment:
    # ... existing entries ...
    - KRAI_SERVICE_JWT=${KRAI_SERVICE_JWT:-}
    - KRAI_ENGINE_ADMIN_USERNAME=${KRAI_ENGINE_ADMIN_USERNAME:-}
    - KRAI_ENGINE_ADMIN_PASSWORD=${KRAI_ENGINE_ADMIN_PASSWORD:-}
```

### `laravel-admin/.env.example`

Document `KRAI_ENGINE_ADMIN_USERNAME` and `KRAI_ENGINE_ADMIN_PASSWORD` (used by `TokenService` for auto-refresh login):

```
KRAI_ENGINE_ADMIN_USERNAME=admin
KRAI_ENGINE_ADMIN_PASSWORD=changeme
```

### Root `.env.example`

`KRAI_SERVICE_JWT=` is already present in `.env.example`. Add a generation hint comment above it:
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
