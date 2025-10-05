-- ======================================================================
-- Migration 21: Fix images.chunk_id Foreign Key
-- ======================================================================
-- Description: Update chunk_id FK to point to correct table
-- Date: 2025-10-05
-- Problem: chunk_id references krai_content.chunks (deleted in Migration 20)
--          Should reference krai_intelligence.chunks
-- ======================================================================

-- Drop old FK constraint (points to deleted table)
ALTER TABLE krai_content.images 
DROP CONSTRAINT IF EXISTS images_chunk_id_fkey;

-- Add new FK constraint to correct table
ALTER TABLE krai_content.images
ADD CONSTRAINT images_chunk_id_fkey 
FOREIGN KEY (chunk_id) 
REFERENCES krai_intelligence.chunks(id) 
ON DELETE SET NULL;

-- Add helpful comment
COMMENT ON COLUMN krai_content.images.chunk_id IS 
'Optional reference to chunk where this image appears. Links to krai_intelligence.chunks.';

-- Verify FK was updated
SELECT 
    tc.constraint_name,
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'krai_content'
    AND tc.table_name = 'images'
    AND kcu.column_name = 'chunk_id';

-- Expected output:
-- | constraint_name        | table_schema | table_name | column_name | foreign_table_schema | foreign_table_name | foreign_column_name |
-- |------------------------|--------------|------------|-------------|----------------------|--------------------|---------------------|
-- | images_chunk_id_fkey   | krai_content | images     | chunk_id    | krai_intelligence    | chunks             | id                  |
