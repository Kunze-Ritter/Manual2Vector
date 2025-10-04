# 📋 Database Migrations - Execution Order

This document lists all database migrations in the correct order for execution.

---

## ✅ **CORE MIGRATIONS (Already Applied)**

These migrations should already be applied to your Supabase database:

- **01** - 05: Initial schema setup (documents, products, error_codes, etc.)
- **06-13**: Agent features, views, analytics, etc.

---

## 🔧 **PENDING MIGRATIONS (Execute in Order)**

Execute these migrations in Supabase SQL Editor in this exact order:

### **Migration 14b: Indexes & Chunks View**
📄 `14b_add_indexes_and_views.sql`
- Adds performance indexes
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

---

## ⚠️ **DEPRECATED MIGRATIONS (DO NOT USE)**

These files are kept for reference only. **DO NOT EXECUTE:**

### **❌ 17_consolidated_features_DEPRECATED.sql**
- Attempted to consolidate migrations 06-16
- **Reason for deprecation:** Redundant with existing migrations, would cause conflicts
- **Use instead:** Individual migrations 14b-18

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
