# Master Stash Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the product-worthy changes from `stash@{0}` onto `master` in small, verified slices while keeping workstation-only noise out of git.

**Architecture:** Restore each slice from `stash@{0}` test-first: pull in the targeted tests, verify the current `master` behavior is missing or broken for that slice, then restore only the matching implementation files and rerun the focused test suite. Keep backend FastAPI work and Laravel admin work in separate commits so each slice is revertible and independently shippable.

**Tech Stack:** Git stash restore, FastAPI, pytest, Laravel 12, Filament 5, PHPUnit 11, Laravel Pint

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `backend/processors/upload_processor.py` | **Modify** | Store uploaded PDFs in object storage and persist returned storage metadata |
| `backend/services/object_storage_service.py` | **Modify** | Add `documents` bucket support, public-read policy wiring, and generic file upload helper |
| `backend/services/postgresql_adapter.py` | **Modify** | Persist `storage_path` and `storage_url` for documents |
| `backend/tests/test_object_storage_service.py` | **Create** | Verify public-read bucket policy is applied for document bucket |
| `backend/tests/test_upload_processor_storage.py` | **Create** | Verify upload processor pushes PDFs to object storage and stores returned metadata |
| `.env.example` | **Modify** | Add `OBJECT_STORAGE_AUTO_PUBLIC_READ` and OpenRouter/OpenWebUI related env hints |
| `docker-compose.yml` | **Modify** | Fix `laravel-admin` env wiring and preserve service auth variables in `environment:` |
| `backend/api/agent_scope.py` | **Create** | Shared scope normalization and SQL helper logic for OpenWebUI/OpenAI-compatible payloads |
| `backend/api/routes/openai_compat.py` | **Modify** | Scope-aware fast paths, OpenRouter model reporting, related docs/videos context, OpenWebUI metadata handling |
| `backend/api/middleware/request_validation_middleware.py` | **Modify** | Stop consuming multipart upload streams before upload processing |
| `backend/tests/test_agent_scope.py` | **Create** | Unit coverage for scope extraction and SQL placeholder generation |
| `backend/tests/test_openwebui_compat.py` | **Create** | Focused integration coverage for OpenAI-compatible routing behavior |
| `laravel-admin/app/Services/BackendApiService.php` | **Modify** | Use canonical document-stage retry endpoint and flatten backend error payloads |
| `laravel-admin/app/Services/MonitoringService.php` | **Modify** | Return per-endpoint error payloads when batch lock acquisition fails |
| `laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource.php` | **Modify** | Load document `stage_status` so admin actions can gate retry availability |
| `laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Pages/ViewPipelineError.php` | **Modify** | Wire retry / resolve actions to backend and show meaningful disabled reasons |
| `laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Tables/PipelineErrorsTable.php` | **Modify** | Gate retry actions per stage status and improve failure messaging |
| `laravel-admin/app/Filament/Resources/Monitoring/AlertConfigurationResource/Tables/AlertConfigurationsTable.php` | **Modify** | Use Filament 5 action APIs consistently |
| `laravel-admin/tests/Feature/BackendApiServiceTest.php` | **Create** | Retry endpoint and nested backend error flattening coverage |
| `laravel-admin/tests/Feature/MonitoringServiceTest.php` | **Modify** | Cover lock-timeout batch response shape and safer cache cleanup |
| `laravel-admin/config/logging.php` | **Modify** | Add dedicated `krai-engine` and `krai-images` log channels |
| `laravel-admin/app/Filament/Resources/Settings/Pages/ManageSettings.php` | **Modify** | Remove hard dependency on `OllamaResource`, move to schema-driven content API, and fetch Ollama data directly |
| `laravel-admin/app/Filament/Resources/Settings/Schemas/SettingsFormSchema.php` | **Modify** | Switch to Filament `Schemas` layout components and keep view fields passive |
| `laravel-admin/resources/views/filament/forms/components/ollama-status-display.blade.php` | **Modify** | Read page state directly after schema refactor |
| `laravel-admin/resources/views/filament/forms/components/ollama-models-table.blade.php` | **Modify** | Read page state directly after schema refactor |
| `laravel-admin/resources/views/filament/resources/settings/pages/manage-settings.blade.php` | **Delete** | Remove obsolete custom page view after schema-driven page migration |
| `laravel-admin/tests/Feature/ManageSettingsTest.php` | **Create** | Cover schema API migration and direct Ollama HTTP helpers |
| `laravel-admin/public/css/filament/filament/app.css` | **Triage Later** | Only restore if source-level changes require refreshed published assets |
| `laravel-admin/public/js/filament/...` | **Triage Later** | Only restore if source-level changes require refreshed published assets |
| `.env.auth` | **Do Not Commit** | Local credential file, keep out of `master` |
| `.claude/settings.json` | **Do Not Commit** | Local tool config, keep out of `master` |
| `.windsurf/rules/project-rules.md` | **Do Not Commit** | Deleted tool-local file, not product work |

---

### Task 1: Backend document-storage upload slice

**Files:**
- Modify: `backend/processors/upload_processor.py`
- Modify: `backend/services/object_storage_service.py`
- Modify: `backend/services/postgresql_adapter.py`
- Modify: `.env.example`
- Test: `backend/tests/test_object_storage_service.py`
- Test: `backend/tests/test_upload_processor_storage.py`

- [ ] **Step 1: Restore the storage-focused pytest files from `stash@{0}`**

```bash
git restore --source='stash@{0}^3' --worktree --staged \
  backend/tests/test_object_storage_service.py \
  backend/tests/test_upload_processor_storage.py
```

- [ ] **Step 2: Run the focused backend tests and confirm current `master` is missing the slice**

```bash
cd backend && python -m pytest tests/test_object_storage_service.py tests/test_upload_processor_storage.py -v
```

Expected: FAIL because `ObjectStorageService` has no generic document upload/public-read behavior and `UploadProcessor` does not accept `storage_service` / `upload_documents_to_storage`.

- [ ] **Step 3: Restore the matching implementation files from `stash@{0}`**

```bash
git restore --source='stash@{0}' --worktree --staged \
  backend/processors/upload_processor.py \
  backend/services/object_storage_service.py \
  backend/services/postgresql_adapter.py \
  .env.example
```

Key behaviors to preserve while reviewing the restored diff:
- `UploadProcessor` accepts optional `storage_service` and `upload_documents_to_storage`
- PDF uploads can call `upload_file(..., bucket_type='documents')`
- document create/update payloads persist both `storage_path` and `storage_url`
- `OBJECT_STORAGE_AUTO_PUBLIC_READ=true` is documented in `.env.example`

- [ ] **Step 4: Re-run the focused backend tests**

```bash
cd backend && python -m pytest tests/test_object_storage_service.py tests/test_upload_processor_storage.py -v
```

Expected: PASS

- [ ] **Step 5: Run the existing upload-route regression suite**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -v
```

Expected: PASS

- [ ] **Step 6: Commit the slice**

```bash
git add .env.example \
  backend/processors/upload_processor.py \
  backend/services/object_storage_service.py \
  backend/services/postgresql_adapter.py \
  backend/tests/test_object_storage_service.py \
  backend/tests/test_upload_processor_storage.py
git commit -m "[Stash] Restore backend document storage upload flow"
```

---

### Task 2: Backend OpenWebUI/OpenAI-compatible scope slice

**Files:**
- Create: `backend/api/agent_scope.py`
- Modify: `backend/api/routes/openai_compat.py`
- Modify: `backend/api/middleware/request_validation_middleware.py`
- Modify: `.env.example`
- Test: `backend/tests/test_agent_scope.py`
- Test: `backend/tests/test_openwebui_compat.py`

- [ ] **Step 1: Restore the scope-focused backend tests**

```bash
git restore --source='stash@{0}^3' --worktree --staged \
  backend/api/agent_scope.py \
  backend/tests/test_agent_scope.py \
  backend/tests/test_openwebui_compat.py
```

- [ ] **Step 2: Run the focused backend tests to surface the missing behavior on `master`**

```bash
cd backend && python -m pytest tests/test_agent_scope.py tests/test_openwebui_compat.py -v
```

Expected: FAIL because `openai_compat.py` does not yet understand `scope`, `metadata`, `OpenRouter`, or the related context payloads covered by these tests.

- [ ] **Step 3: Restore the matching FastAPI implementation**

```bash
git restore --source='stash@{0}' --worktree --staged \
  backend/api/routes/openai_compat.py \
  backend/api/middleware/request_validation_middleware.py \
  .env.example
```

Review points before keeping the diff:
- multipart requests must bypass body parsing in `RequestValidationMiddleware`
- `openai_compat.py` must use the shared `agent_scope` helpers rather than ad-hoc parsing
- OpenRouter model reporting and env docs belong in this slice
- fast-path responses may include `krai_context` but must preserve existing OpenAI-compatible response shape

- [ ] **Step 4: Re-run the focused backend tests**

```bash
cd backend && python -m pytest tests/test_agent_scope.py tests/test_openwebui_compat.py -v
```

Expected: PASS

- [ ] **Step 5: Run the existing upload-route regression suite again**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py -v
```

Expected: PASS

- [ ] **Step 6: Commit the slice**

```bash
git add .env.example \
  backend/api/agent_scope.py \
  backend/api/middleware/request_validation_middleware.py \
  backend/api/routes/openai_compat.py \
  backend/tests/test_agent_scope.py \
  backend/tests/test_openwebui_compat.py
git commit -m "[Stash] Restore scope-aware OpenAI compatibility improvements"
```

---

### Task 3: Laravel monitoring and retry-admin slice

**Files:**
- Modify: `laravel-admin/app/Services/BackendApiService.php`
- Modify: `laravel-admin/app/Services/MonitoringService.php`
- Modify: `laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource.php`
- Modify: `laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Pages/ViewPipelineError.php`
- Modify: `laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Tables/PipelineErrorsTable.php`
- Modify: `laravel-admin/app/Filament/Resources/Monitoring/AlertConfigurationResource/Tables/AlertConfigurationsTable.php`
- Modify: `laravel-admin/config/logging.php`
- Test: `laravel-admin/tests/Feature/BackendApiServiceTest.php`
- Test: `laravel-admin/tests/Feature/MonitoringServiceTest.php`

- [ ] **Step 1: Restore the retry/admin PHPUnit coverage**

```bash
git restore --source='stash@{0}^3' --worktree --staged \
  laravel-admin/tests/Feature/BackendApiServiceTest.php
git restore --source='stash@{0}' --worktree --staged \
  laravel-admin/tests/Feature/MonitoringServiceTest.php
```

- [ ] **Step 2: Run the focused Laravel tests and confirm missing behavior**

```bash
cd laravel-admin && php artisan test --compact \
  tests/Feature/BackendApiServiceTest.php \
  tests/Feature/MonitoringServiceTest.php
```

Expected: FAIL because retry still targets `/api/v1/pipeline/retry-stage`, nested error payloads are not flattened, and batch lock failures do not return per-endpoint error payloads.

- [ ] **Step 3: Restore the matching Laravel monitoring/admin files**

```bash
git restore --source='stash@{0}' --worktree --staged \
  laravel-admin/app/Services/BackendApiService.php \
  laravel-admin/app/Services/MonitoringService.php \
  laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource.php \
  laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Pages/ViewPipelineError.php \
  laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Tables/PipelineErrorsTable.php \
  laravel-admin/app/Filament/Resources/Monitoring/AlertConfigurationResource/Tables/AlertConfigurationsTable.php \
  laravel-admin/config/logging.php
```

Review points before keeping the diff:
- retry normalization must only allow explicitly supported admin stages
- retry buttons must be disabled when backend config is missing or stage status is not `failed`
- resolve actions should still mark the local record even if backend sync fails
- lock timeout handling must return a keyed error payload for every requested monitoring endpoint

- [ ] **Step 4: Re-run the focused Laravel tests**

```bash
cd laravel-admin && php artisan test --compact \
  tests/Feature/BackendApiServiceTest.php \
  tests/Feature/MonitoringServiceTest.php
```

Expected: PASS

- [ ] **Step 5: Run formatting on touched PHP files**

```bash
cd laravel-admin && vendor/bin/pint --dirty
```

Expected: PASS with no remaining formatting changes

- [ ] **Step 6: Commit the slice**

```bash
git add laravel-admin/app/Services/BackendApiService.php \
  laravel-admin/app/Services/MonitoringService.php \
  laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource.php \
  laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Pages/ViewPipelineError.php \
  laravel-admin/app/Filament/Resources/Monitoring/PipelineErrorResource/Tables/PipelineErrorsTable.php \
  laravel-admin/app/Filament/Resources/Monitoring/AlertConfigurationResource/Tables/AlertConfigurationsTable.php \
  laravel-admin/config/logging.php \
  laravel-admin/tests/Feature/BackendApiServiceTest.php \
  laravel-admin/tests/Feature/MonitoringServiceTest.php
git commit -m "[Stash] Restore Laravel monitoring retry and lock handling"
```

---

### Task 4: Laravel settings/Ollama page refactor slice

**Files:**
- Modify: `laravel-admin/app/Filament/Resources/Settings/Pages/ManageSettings.php`
- Modify: `laravel-admin/app/Filament/Resources/Settings/Schemas/SettingsFormSchema.php`
- Modify: `laravel-admin/resources/views/filament/forms/components/ollama-status-display.blade.php`
- Modify: `laravel-admin/resources/views/filament/forms/components/ollama-models-table.blade.php`
- Delete: `laravel-admin/resources/views/filament/resources/settings/pages/manage-settings.blade.php`
- Test: `laravel-admin/tests/Feature/ManageSettingsTest.php`
- Triage Later: `laravel-admin/public/css/filament/filament/app.css`
- Triage Later: `laravel-admin/public/js/filament/...`

- [ ] **Step 1: Restore the settings PHPUnit coverage**

```bash
git restore --source='stash@{0}^3' --worktree --staged \
  laravel-admin/tests/Feature/ManageSettingsTest.php
```

- [ ] **Step 2: Run the focused settings test and confirm current `master` behavior is stale**

```bash
cd laravel-admin && php artisan test --compact tests/Feature/ManageSettingsTest.php
```

Expected: FAIL because `ManageSettings` still depends on `OllamaResource`, still uses the older custom page view, and the schema still uses forms-layout components/state closures.

- [ ] **Step 3: Restore the matching settings source files**

```bash
git restore --source='stash@{0}' --worktree --staged \
  laravel-admin/app/Filament/Resources/Settings/Pages/ManageSettings.php \
  laravel-admin/app/Filament/Resources/Settings/Schemas/SettingsFormSchema.php \
  laravel-admin/resources/views/filament/forms/components/ollama-status-display.blade.php \
  laravel-admin/resources/views/filament/forms/components/ollama-models-table.blade.php \
  laravel-admin/resources/views/filament/resources/settings/pages/manage-settings.blade.php
```

Review points before keeping the diff:
- `ManageSettings` must switch to schema-driven page content and direct `Http`-based Ollama helpers
- `SettingsFormSchema` must use `Filament\\Schemas\\Components\\...`
- the obsolete custom page view should be removed from git after the page no longer references it

- [ ] **Step 4: Re-run the focused settings test**

```bash
cd laravel-admin && php artisan test --compact tests/Feature/ManageSettingsTest.php
```

Expected: PASS

- [ ] **Step 5: Decide whether published Filament assets are actually required**

Run only if the source-level tests pass but the page is still broken in a manual smoke check or if `git diff --stat 'stash@{0}' -- laravel-admin/public` shows assets tied directly to this refactor.

```bash
git diff --stat 'stash@{0}^1' 'stash@{0}' -- laravel-admin/public
```

Expected: treat `laravel-admin/public/...` as generated/vendor-published output unless there is concrete evidence the source changes require those exact files in git.

- [ ] **Step 6: Format and commit the slice**

```bash
cd laravel-admin && vendor/bin/pint --dirty
git add laravel-admin/app/Filament/Resources/Settings/Pages/ManageSettings.php \
  laravel-admin/app/Filament/Resources/Settings/Schemas/SettingsFormSchema.php \
  laravel-admin/resources/views/filament/forms/components/ollama-status-display.blade.php \
  laravel-admin/resources/views/filament/forms/components/ollama-models-table.blade.php \
  laravel-admin/resources/views/filament/resources/settings/pages/manage-settings.blade.php \
  laravel-admin/tests/Feature/ManageSettingsTest.php
git commit -m "[Stash] Restore Laravel settings Ollama page refactor"
```

---

### Task 5: Final stash triage and cleanup

**Files:**
- Triage: `.env.auth`
- Triage: `.claude/settings.json`
- Triage: `.windsurf/rules/project-rules.md`
- Triage: `docker-compose.yml`
- Triage: `laravel-admin/public/css/filament/filament/app.css`
- Triage: `laravel-admin/public/js/filament/...`

- [ ] **Step 1: List what remains unmatched after Tasks 1-4**

```bash
git diff --name-only 'stash@{0}^1' 'stash@{0}'
git diff --name-only
```

Expected: only intentionally deferred files remain

- [ ] **Step 2: Restore `docker-compose.yml` only if its env fixes are still missing on `master`**

```bash
git diff 'stash@{0}^1' 'stash@{0}' -- docker-compose.yml
```

Keep only the valid `environment:` block changes; do not reintroduce env keys under `volumes:`.

- [ ] **Step 3: Explicitly exclude local/tool files from commits**

Do not stage:
- `.env.auth`
- `.claude/settings.json`
- `.windsurf/rules/project-rules.md`

- [ ] **Step 4: Run final verification**

```bash
cd backend && python -m pytest tests/test_document_processing_routes.py tests/test_object_storage_service.py tests/test_upload_processor_storage.py tests/test_agent_scope.py tests/test_openwebui_compat.py -v
cd laravel-admin && php artisan test --compact tests/Feature/BackendApiServiceTest.php tests/Feature/MonitoringServiceTest.php tests/Feature/ManageSettingsTest.php
cd laravel-admin && vendor/bin/pint --dirty
```

Expected: PASS

- [ ] **Step 5: Commit any last intentional file(s) and drop the stash only after confirming nothing valuable remains**

```bash
git status --short
git stash drop 'stash@{0}'
```

Only drop the stash when the remaining diff has been audited and intentionally either committed or discarded.
