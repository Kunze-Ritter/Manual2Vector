-- ======================================================================
-- Migration 20a: Verify krai_content.chunks is Empty
-- ======================================================================
-- Description: Check if legacy chunks table can be safely dropped
-- Date: 2025-10-05
-- Purpose: Safety check before cleanup
-- ======================================================================

-- EXPLANATION:
-- There are TWO chunks tables which causes confusion:
-- 
-- 1. krai_intelligence.chunks (ACTIVE - USED BY CODE)
--    - Has: text_chunk, metadata JSONB, embedding vector(768)
--    - Contains: All document chunks with header metadata
--    - Purpose: Main chunks table for semantic search
--
-- 2. krai_content.chunks (LEGACY - UNUSED)
--    - Has: content, chunk_type, NO metadata column
--    - Contains: Nothing (never populated by v2 code)
--    - Purpose: Unknown/legacy, not referenced anywhere

-- ======================================================================
-- Verify krai_content.chunks is empty
-- ======================================================================

DO $$
DECLARE
    row_count INT;
BEGIN
    SELECT COUNT(*) INTO row_count FROM krai_content.chunks;
    
    IF row_count > 0 THEN
        RAISE NOTICE '⚠️  WARNING: krai_content.chunks contains % rows!', row_count;
        RAISE NOTICE '   Review data before dropping. Aborting migration.';
        RAISE EXCEPTION 'Table not empty - manual review required';
    ELSE
        RAISE NOTICE '✅ krai_content.chunks is empty - safe to proceed with 20b';
    END IF;
END $$;

-- ======================================================================
-- Show current state
-- ======================================================================

SELECT 
    table_schema,
    table_name,
    (SELECT COUNT(*) FROM krai_content.chunks) as row_count
FROM information_schema.tables
WHERE table_name = 'chunks'
ORDER BY table_schema;

-- Expected output:
-- | table_schema        | table_name | row_count |
-- |---------------------|------------|-----------|
-- | krai_content        | chunks     | 0         |
-- | krai_intelligence   | chunks     | 3968      |
