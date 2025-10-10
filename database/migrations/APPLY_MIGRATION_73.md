# Migration 73: Add Missing document_id Foreign Key

## Problem
The `error_codes` table is missing the foreign key constraint for `document_id`, even though it's defined in the original schema (01_schema_and_tables.sql line 218).

**Current state:**
```sql
-- Foreign keys that exist:
✅ error_codes_chunk_id_fkey
✅ error_codes_image_id_fkey
✅ error_codes_manufacturer_id_fkey
✅ error_codes_product_id_fkey
✅ error_codes_video_id_fkey

-- Missing:
❌ error_codes_document_id_fkey
```

**Impact:**
- `document_id` appears as plain UUID in Supabase UI (no relation link)
- `manufacturer_id` appears as linked record (has foreign key)
- Data integrity not enforced at database level

## Solution
Add the missing foreign key constraint:

```sql
ALTER TABLE krai_intelligence.error_codes
ADD CONSTRAINT error_codes_document_id_fkey
FOREIGN KEY (document_id)
REFERENCES krai_core.documents(id)
ON DELETE CASCADE;
```

## How to Apply

### Option 1: Supabase SQL Editor (Recommended)
1. Open Supabase Dashboard → SQL Editor
2. Copy contents of `73_add_error_codes_document_fkey.sql`
3. Execute
4. Verify success message: ✅ Foreign key constraint created

### Option 2: psql Command Line
```bash
psql $DATABASE_URL -f database/migrations/73_add_error_codes_document_fkey.sql
```

### Option 3: Python Script
```bash
cd scripts
python apply_migration.py 73
```

## Verification

After applying, run this query to verify:

```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_schema = 'krai_intelligence'
  AND tc.table_name = 'error_codes'
  AND tc.constraint_type = 'FOREIGN KEY'
  AND kcu.column_name = 'document_id';
```

**Expected result:**
```json
{
  "constraint_name": "error_codes_document_id_fkey",
  "table_name": "error_codes",
  "column_name": "document_id",
  "foreign_table_name": "documents"
}
```

## Expected Changes

### Before:
- `document_id` column: Plain UUID field
- Supabase UI: Shows UUID string only
- No referential integrity

### After:
- `document_id` column: Foreign key to documents table
- Supabase UI: Shows linked record with document details
- Referential integrity enforced (CASCADE on delete)

## Rollback

If needed, remove the constraint:

```sql
ALTER TABLE krai_intelligence.error_codes
DROP CONSTRAINT IF EXISTS error_codes_document_id_fkey;
```

## Notes

- **Safe to apply:** This migration only adds a constraint, doesn't modify data
- **No downtime:** Can be applied on live database
- **Idempotent:** Safe to run multiple times (uses IF NOT EXISTS)
- **Performance:** Creates index for better query performance

## Related Files
- Original schema: `01_schema_and_tables.sql` (line 218)
- Error code processor: `backend/processors/document_processor.py` (line 1504)
