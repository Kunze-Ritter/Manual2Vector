# VIEW AUDIT - Duplicate Views in Migrations

## DUPLICATE VIEWS FOUND:

### 1. **public.products**
- ✅ Migration 15: CREATE OR REPLACE VIEW (with RULES)
- ❌ Migration 15a: CREATE VIEW (duplicate, no RULES)
- **ACTION:** Delete 15a

### 2. **public.document_products**
- ✅ Migration 15: CREATE OR REPLACE VIEW (with RULES)
- ❌ Migration 15b: CREATE VIEW (duplicate)
- **ACTION:** Delete 15b

### 3. **public.manufacturers**
- ✅ Migration 15: CREATE OR REPLACE VIEW (with RULES)
- ❌ Migration 15b: CREATE VIEW (duplicate)
- **ACTION:** Delete 15b

### 4. **public.links**
- ❌ Migration 16a: CREATE VIEW (with RULES) - ALREADY DELETED ✅
- ✅ Migration 31: CREATE OR REPLACE VIEW (with TRIGGERS)
- **ACTION:** Already cleaned up

### 5. **public.videos**
- ✅ Migration 31: CREATE OR REPLACE VIEW (with TRIGGERS)
- ❌ Migration 39: CREATE OR REPLACE VIEW (duplicate?)
- **ACTION:** Check if 39 is needed

### 6. **public.chunks**
- ❌ Migration 20: CREATE OR REPLACE VIEW (DEPRECATED)
- ✅ Migration 20c: CREATE VIEW (current)
- **ACTION:** Delete 20 (marked DEPRECATED)

### 7. **public.vw_embeddings**
- ❌ Migration 26: CREATE OR REPLACE VIEW
- ✅ Migration 35: CREATE OR REPLACE VIEW (fixed column names)
- **ACTION:** Delete 26 (superseded by 35)

### 8. **public.search_analytics / vw_search_analytics**
- Migration 16b: vw_search_analytics
- Migration 17: search_analytics (DEPRECATED)
- **ACTION:** Check which is used

## SUMMARY:

**Migrations to DELETE:**
- ✅ 16a (already deleted)
- ❌ 15a (duplicate of 15)
- ❌ 15b (duplicate of 15)
- ❌ 17 (marked DEPRECATED)
- ❌ 20 (marked DEPRECATED)
- ❌ 26 (superseded by 35)

**Migrations to CHECK:**
- 39 (videos view - might be duplicate of 31)
- 16b vs 17 (search_analytics naming)

## NEXT STEPS:

1. Check which views are actually used in code
2. Delete duplicate migrations
3. Create cleanup migration for database
