# 🗄️ KRAI Database Migrations - Clean Structure

**Last Updated:** 2025-10-04  
**Status:** ✅ Production Ready

---

## 📋 **Migration Order (Apply in this sequence)**

### **Core Schema (REQUIRED)**

| # | File | Description | Status |
|---|------|-------------|--------|
| 01 | `01_schema_and_tables.sql` | **All schemas & tables** (manufacturers, products, documents, chunks, error_codes, etc.) | ✅ Applied |
| 02 | `02_security_rls_triggers.sql` | **RLS policies, triggers, functions** for security | ✅ Applied |
| 03 | `03_indexes_performance.sql` | **Performance indexes** on all tables | ✅ Applied |
| 04 | `04_rpc_functions_deduplication.sql` | **RPC functions** for deduplication & utilities | ✅ Applied |
| 05 | `05_public_views_for_postgrest.sql` | **Public views** for PostgREST API access | ✅ Applied |

### **Features & Enhancements**

| # | File | Description | Status |
|---|------|-------------|--------|
| 06 | `06_agent_views_complete.sql` | **Agent views** for N8N integration | ✅ Applied |
| 07 | `07_agent_memory_table.sql` | **Agent memory** table for conversation context | ✅ Applied |
| 08 | `08_link_video_enhancement.sql` | **Links & videos** tables | ✅ Applied |
| 09 | `09_error_code_ai_enhancement.sql` | **AI enhancements** for error codes | ✅ Applied |
| 10 | `10_stage_status_tracking.sql` | **Stage tracking** for processing pipeline | ✅ Applied |
| 11 | `11_pgvector_embeddings.sql` | **pgvector** for semantic search (**FIXED**) | ✅ Applied |
| 12 | `12_add_processing_results.sql` | **Processing results** column for documents | ⏳ Pending |
| 14 | `14_create_n8n_vector_search_function.sql` | **N8N vector search** function | ✅ Applied |
| 16 | `16_create_search_analytics_view.sql` | **Search analytics** view | ✅ Applied |
| 17 | `17_consolidated_features.sql` | **Consolidated** all features 06-16 | ✅ New |

---

## 🗂️ **Database Schema Structure**

### **Schemas:**

```
krai_core           - Core entities (manufacturers, products, documents)
krai_intelligence   - AI/ML (chunks, embeddings, error_codes, analytics)
krai_content        - Media (images, videos, links, chunks)
krai_config         - Configuration (features, compatibility)
krai_system         - System (audit, queue, health)
krai_agent          - Agent (memory, messages)
krai_ml             - ML models
krai_parts          - Parts catalog
krai_service        - Service management
krai_users          - User management
krai_integrations   - External APIs
```

### **Key Tables:**

```sql
-- Core
krai_core.manufacturers
krai_core.products
krai_core.documents
krai_core.product_series

-- Intelligence (AI/ML)
krai_intelligence.chunks          ← TEXT CHUNKS mit embeddings!
krai_intelligence.error_codes     ← ERROR CODES
krai_intelligence.embeddings      ← LEGACY (nicht genutzt)

-- Content
krai_content.images
krai_content.videos
krai_content.links

-- Agent
krai_agent.memory
krai_agent.message
```

---

## ⚠️ **WICHTIG: Migration 11 wurde gefixt!**

### **Problem:**
Migration 11 versuchte `krai_core.chunks` zu ändern, aber die Tabelle ist in `krai_intelligence.chunks`!

### **Fix:**
```sql
-- VORHER (falsch):
ALTER TABLE krai_core.chunks ADD COLUMN embedding vector(768);

-- NACHHER (korrekt):
ALTER TABLE krai_intelligence.chunks ADD COLUMN embedding vector(768);
```

**Status:** ✅ Gefixt und angewendet

---

## 🗑️ **Gelöschte Migrations (Konsolidiert in 17)**

Diese Migrations wurden gelöscht, da ihre Features in `17_consolidated_features.sql` zusammengefasst sind:

- ~~`06_jsonb_specifications.sql`~~ → In 17
- ~~`07_restructure_products_jsonb.sql`~~ → In 17
- ~~`09_product_compatibility.sql`~~ → In 17
- ~~`10_agent_memory_content_to_message.sql`~~ → In 17
- ~~`10b_fix_stage_status.sql`~~ → In 10
- ~~`10c_fix_functions_public.sql`~~ → In 04/05
- ~~`10d_grant_permissions.sql`~~ → In 02/17
- ~~`11_expand_memory_role_constraint.sql`~~ → In 17
- ~~`12_add_message_column_with_sync.sql`~~ → In 17
- ~~`15_fix_memory_role_default.sql`~~ → In 17

**Alle Test-Scripts gelöscht.**

---

## 🚀 **Nächste Schritte**

### **Für neue Installationen:**

```sql
-- 1. Apply Core Migrations (01-05)
psql -f 01_schema_and_tables.sql
psql -f 02_security_rls_triggers.sql
psql -f 03_indexes_performance.sql
psql -f 04_rpc_functions_deduplication.sql
psql -f 05_public_views_for_postgrest.sql

-- 2. Apply Features (06-17)
psql -f 06_agent_views_complete.sql
psql -f 07_agent_memory_table.sql
psql -f 08_link_video_enhancement.sql
psql -f 09_error_code_ai_enhancement.sql
psql -f 10_stage_status_tracking.sql
psql -f 11_pgvector_embeddings.sql
psql -f 12_add_processing_results.sql
psql -f 14_create_n8n_vector_search_function.sql
psql -f 16_create_search_analytics_view.sql
psql -f 17_consolidated_features.sql
```

### **Für bestehende DB (nur Update):**

```sql
-- Apply nur die fehlenden:
psql -f 12_add_processing_results.sql
psql -f 17_consolidated_features.sql
```

---

## 📊 **Schema Prüfen**

```sql
-- Check all tables
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname LIKE 'krai_%'
ORDER BY schemaname, tablename;

-- Check chunks table
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_schema = 'krai_intelligence' 
  AND table_name = 'chunks';

-- Check embeddings
SELECT COUNT(*) as total_chunks, 
       COUNT(embedding) as with_embeddings
FROM krai_intelligence.chunks;
```

---

## 🧹 **Aufräumen abgeschlossen!**

✅ Duplikate entfernt  
✅ Migrations konsolidiert  
✅ Migration 11 gefixt (krai_intelligence.chunks)  
✅ Test-Files gelöscht  
✅ Saubere Struktur

**Alle Migrations sind jetzt korrekt und zeigen auf die richtigen Tabellen!**
