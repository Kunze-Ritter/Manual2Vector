# Tables/Views Used in Backend Code

## DIRECTLY USED TABLES (via .table()):

### Core Tables:
- ✅ `documents` - heavily used everywhere
- ✅ `chunks` - used in database_service.py
- ✅ `error_codes` - used in agent_api.py
- ✅ `images` - used in database_service_production.py
- ✅ `embeddings` - used in database_service_production.py

### Product Tables:
- ✅ `manufacturers` - used in manufacturer_utils.py, oem_sync.py
- ✅ `products` - used in manufacturer_utils.py, oem_sync.py
- ✅ `product_series` - used in manufacturer_utils.py
- ✅ `document_products` - used in document_processor.py

### Parts Tables:
- ✅ `parts_catalog` - used in document_processor.py
- ✅ `vw_parts` - used in agent_api.py (VIEW!)

### Link/Video Tables:
- ✅ `links` - used in link_extractor.py
- ✅ `videos` - used in link_extractor.py
- ✅ `video_products` - used in manufacturer_utils.py

### Other Tables:
- ✅ `oem_relationships` - used in oem_sync.py
- ✅ `processing_queue` - used in queue_processor.py
- ✅ `system_metrics` - used in database_service.py

## VIEWS USED:

### Agent API:
- ✅ `vw_parts` - agent_api.py line 194 (for parts search)

### N8N/Analytics:
- ❓ `vw_search_analytics` or `search_analytics` - need to check n8n workflows

## CONCLUSION:

**Code uses TABLE NAMES directly, NOT view names!**

Example:
- Code: `supabase.table('products')`
- Supabase PostgREST: Resolves to `public.products` VIEW
- View points to: `krai_core.products` TABLE

**This means:**
- ✅ We can delete duplicate VIEW migrations safely
- ✅ As long as ONE view exists per table, code will work
- ✅ Views are just for PostgREST access (public schema)

**SAFE TO DELETE:**
- Migration 15a (duplicate products view)
- Migration 15b (duplicate document_products/manufacturers views)
- Migration 17 (deprecated search_analytics)
- Migration 20 (deprecated chunks view)
- Migration 26 (superseded vw_embeddings)
