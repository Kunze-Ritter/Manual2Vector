# View Cleanup Plan

## Analysis: Which views are duplicates?

### DUPLICATE VIEWS (both exist, point to same table):

1. **links**
   - `public.links` → `krai_content.links`
   - `public.vw_links` → `krai_content.links`
   - **ACTION:** Keep `public.links`, DROP `public.vw_links`

2. **products**
   - `public.products` → `krai_core.products`
   - `public.vw_products` → `krai_core.products_with_names`
   - **ACTION:** Keep BOTH (different sources!)

3. **manufacturers**
   - `public.manufacturers` → `krai_core.manufacturers`
   - `public.vw_manufacturers` → `krai_core.manufacturers`
   - **ACTION:** Keep `public.manufacturers`, DROP `public.vw_manufacturers`

4. **documents**
   - `public.documents` → `krai_core.documents`
   - `public.vw_documents` → `krai_core.documents`
   - **ACTION:** Keep `public.documents`, DROP `public.vw_documents`

5. **error_codes**
   - `public.error_codes` → `krai_core.error_codes` (if exists)
   - `public.vw_error_codes` → `krai_core.error_codes`
   - **ACTION:** Need to check if public.error_codes exists

6. **chunks**
   - `public.chunks` → `krai_intelligence.chunks`
   - `public.vw_chunks` → `krai_content.chunks` (DIFFERENT!)
   - **ACTION:** Keep BOTH (different sources!)

7. **embeddings**
   - `public.embeddings` → ? (need to check)
   - `public.vw_embeddings` → `krai_intelligence.embeddings`
   - **ACTION:** Keep `public.vw_embeddings` (only one)

8. **images**
   - `public.images` → `krai_content.images` (if exists)
   - `public.vw_images` → `krai_content.images`
   - **ACTION:** Need to check if public.images exists

### UNIQUE VIEWS (no duplicates):

- ✅ `public.vw_agent_memory` (unique)
- ✅ `public.vw_audit_log` (unique)
- ✅ `public.vw_processing_queue` (unique)
- ✅ `public.vw_webhook_logs` (unique)
- ✅ `public.vw_search_analytics` (unique)
- ✅ `public.vw_parts` (unique, special join)

## DECISION:

**Keep simple names for API access:**
- `public.links`, `public.products`, `public.manufacturers`, `public.documents`

**Keep `vw_` prefix for:**
- Special views with joins/transformations
- Views that don't have a simple equivalent
- Agent-specific views

## MIGRATION 83: Drop duplicate vw_ views

```sql
-- Drop duplicate vw_ views (where simple view exists)
DROP VIEW IF EXISTS public.vw_links CASCADE;
DROP VIEW IF EXISTS public.vw_manufacturers CASCADE;
DROP VIEW IF EXISTS public.vw_documents CASCADE;

-- Check if these are duplicates first:
-- DROP VIEW IF EXISTS public.vw_images CASCADE;
-- DROP VIEW IF EXISTS public.vw_error_codes CASCADE;
```
