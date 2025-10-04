# 📋 Database Migrations - Execution Order


---

## ✅ **CORE MIGRATIONS (Already Applied)**

The# Database Migrations Execution Order

This document provides the correct order to execute database migrations.

## Important Notes

- Always execute migrations in order
- Some migrations depend on previous ones
- Test in development environment first
- Some migrations may have been renamed to avoid conflicts
- Multi-part migrations (e.g., 20a, 20b, 20c) must be run in sequence

## Execution Order

Execute these migrations in Supabase SQL Editor in this exact order:

### **Migration 14b: Indexes & Chunks View**
📄 `14b_add_indexes_and_views.sql`
- Creates `public.chunks` VIEW with COALESCE fix
- **Status:** ✅ Ready to execute

### **Migration 15a: Products View**
📄 `15a_create_products_view.sql`
- Creates `public.products` VIEW
- COALESCE fix for `id` and `created_at`
- **Status:** ✅ Ready to execute

### **Migration 15b: Document Products & Manufacturers Views**
📄 `15b_create_document_products_manufacturers_views.sql`
- Creates `public.document_products` VIEW
- Creates `public.manufacturers` VIEW
- COALESCE fixes for both
- **Status:** ✅ Ready to execute

### **Migration 16a: Links View**
📄 `16a_create_public_links_videos_views.sql`
- Creates `public.links` VIEW
- COALESCE fix for `id`, `created_at`, `updated_at`
- INSERT/UPDATE/DELETE rules
- **Status:** ✅ Ready to execute

### **Migration 16b: Search Analytics View**
📄 `16b_create_search_analytics_view.sql`
- Creates `public.vw_search_analytics` VIEW for n8n
- INSERT trigger for analytics logging
- **Status:** ✅ Ready to execute

### **Migration 17: Make Manufacturer ID Nullable**
📄 `17_make_manufacturer_id_nullable.sql`
- Makes `manufacturer_id` in `krai_core.products` NULLABLE
- Important for products without manufacturer
- **Status:** ✅ Ready to execute

### **Migration 18: Parts Catalog View**
📄 `18_create_public_parts_catalog_view.sql`
- Creates `public.parts_catalog` VIEW
- Enables Parts Extraction feature
- COALESCE fix for `id`, `created_at`
- INSERT/UPDATE/DELETE rules
- **Status:** ✅ Ready to execute

### **Migration 19: Video Thumbnail Analysis**
📄 `19_add_video_thumbnail_analysis.sql`
- Adds `thumbnail_ocr_text` column
- Adds `thumbnail_ai_description` column
- Adds `thumbnail_analysis_date` column
- Enables Vision AI for video thumbnails
- **Status:** ✅ Ready to execute

### **Migration 20a: Verify Legacy Chunks Table**
📄 `20a_verify_chunks_table_empty.sql`
- Verifies `krai_content.chunks` is empty
- Safety check before cleanup
- **Status:** ✅ Ready to execute
- **⚠️  MUST run before 20b!**

### **Migration 20b: Drop Legacy Chunks Table**
📄 `20b_drop_legacy_chunks_table.sql`
- Drops unused `krai_content.chunks` table
- Removes duplicate chunks table
- **Status:** ✅ Ready to execute
- **⚠️  MUST run 20a first!**

### **Migration 20c: Create Chunks View**
📄 `20c_create_chunks_view.sql`
- Creates `public.chunks` VIEW → `krai_intelligence.chunks`
- Grants proper permissions
- **Status:** ✅ Ready to execute
- **⚠️  MUST run 20b first!**

---

## ⚠️ **DEPRECATED MIGRATIONS (DO NOT USE)**

These files are kept for reference only. **DO NOT EXECUTE:**

### **❌ 17_consolidated_features_DEPRECATED.sql**
- Attempted to consolidate migrations 06-16
- **Reason for deprecation:** Redundant with existing migrations, would cause conflicts
- **Use instead:** Individual migrations 14b-18

### **❌ 20_cleanup_duplicate_chunks_table.sql (DEPRECATED)**
- Attempted to do all cleanup in one migration
- **Reason for deprecation:** Too complex, causes execution errors
- **Use instead:** Migrations 20a → 20b → 20c (split into parts)

---

## 📝 **Execution Checklist**

```sql
-- Copy and paste each migration in this order into Supabase SQL Editor:

-- ✅ 1. Migration 14b
-- File: database/migrations/14b_add_indexes_and_views.sql

-- ✅ 2. Migration 15a
-- File: database/migrations/15a_create_products_view.sql

-- ✅ 3. Migration 15b
-- File: database/migrations/15b_create_document_products_manufacturers_views.sql

-- ✅ 4. Migration 16a
-- File: database/migrations/16a_create_public_links_videos_views.sql

-- ✅ 5. Migration 16b
-- File: database/migrations/16b_create_search_analytics_view.sql

-- ✅ 6. Migration 17
-- File: database/migrations/17_make_manufacturer_id_nullable.sql

-- ✅ 7. Migration 18
-- File: database/migrations/18_create_public_parts_catalog_view.sql

-- ✅ 8. Migration 19
-- File: database/migrations/19_add_video_thumbnail_analysis.sql

-- ✅ 9. Migration 20a (VERIFY FIRST!)
-- File: database/migrations/20a_verify_chunks_table_empty.sql

-- ✅ 10. Migration 20b (ONLY IF 20a succeeds!)
-- File: database/migrations/20b_drop_legacy_chunks_table.sql

-- ✅ 11. Migration 20c (FINAL STEP)
-- File: database/migrations/20c_create_chunks_view.sql
```

---

## 🔍 **Verification Queries**

After running all migrations, verify they were applied correctly:

```sql
-- Check that all views exist
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname IN ('chunks', 'products', 'document_products', 'manufacturers', 'links', 'parts_catalog', 'vw_search_analytics')
ORDER BY viewname;
-- Should return 7 rows

-- Check manufacturer_id is nullable
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'krai_core' 
  AND table_name = 'products' 
  AND column_name = 'manufacturer_id';
-- Should show: is_nullable = YES
```

---

## 📌 **Notes**

- All migrations include `CREATE OR REPLACE` or `IF NOT EXISTS` clauses
- Safe to re-run if needed (idempotent)
- COALESCE fixes ensure UUIDs and timestamps are handled correctly
- Each migration includes verification queries in comments
