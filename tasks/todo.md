# KRAI-minimal Optimization & Cleanup Plan (March 2026) - COMPLETED

## Objective
Audit the codebase for dead code, remove unused services (especially AI/Chat remnants), and optimize the system for its new role with OpenWebUI.

## Accomplished Tasks

### 1. Laravel / Filament Audit & AI Removal
- [x] **Removed AI Resources:** Deleted `PromptTemplateResource` and `OllamaResource`.
- [x] **Removed AI Pages:** Deleted `AiChatPage`, `VectorSearchPage`, and `FirecrawlTestPage`.
- [x] **Cleaned Models & Services:** Removed `ChatMessage`, `ChatSession`, `PromptTemplate` models and `AiAgentService`.
- [x] **Fixed Filament Errors:** Migrated `ViewPipelineError` to use `Filament Schemas` bridge, fixing "Class not found" errors.
- [x] **Consolidated Settings:** Removed OpenAI and Chat-specific settings; now focused purely on backend-relevant Ollama parameters.

### 2. Backend Dead Code Removal
- [x] **Cleaned Deprecated Code:** Deleted `backend/processors/deprecated/` and `backend/api/deprecated/`.
- [x] **Removed Redundant Adapters:** Deleted `backend/services/docker_postgresql_adapter.py`.
- [x] **Supabase Cleanup:** Surgically removed legacy Supabase fallback logic from `ChunkPreprocessor` and `ClassificationProcessor`.
- [x] **API Route Optimization:** Cleaned up legacy `TODO`s in `backend/api/app.py` and consolidated database access patterns.

### 3. General Project Hygiene
- [x] **Removed Root Junk:** Deleted `run_migration_006.py` and several test scripts from the project root.
- [x] **Migration Audit:** Identified migration 023 as containing Chat tables; they remain in the DB for now but are no longer used by any code.
- [x] **Code Formatting:** Ran `Laravel Pint` on all modified PHP files to ensure consistency.

## Benefits
- **Reduced Attack Surface:** Removal of unused API endpoints and models.
- **Improved Performance:** Cleaner code paths in processors (no unnecessary attribute checks for dead clients).
- **Maintenance:** Significantly reduced codebase size and complexity.
- **Stability:** Fixed recurring Filament dashboard errors by modernizing the components.

---
## Review Section
*Project is now lean, clean, and fully focused on its core 16-stage pipeline and OpenWebUI integration.*
