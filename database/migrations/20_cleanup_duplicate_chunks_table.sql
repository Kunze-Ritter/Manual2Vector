-- ======================================================================
-- Migration 20: Cleanup Duplicate Chunks Table
-- ======================================================================
-- Description: Remove unused krai_content.chunks table (duplicate/legacy)
-- Date: 2025-10-05
-- Purpose: Clean up schema confusion - only krai_intelligence.chunks is used
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
--
-- DECISION: DROP krai_content.chunks as it's not used

-- ======================================================================
-- Step 1: Verify krai_content.chunks is empty
-- ======================================================================

DO $$
DECLARE
    row_count INT;
BEGIN
    SELECT COUNT(*) INTO row_count FROM krai_content.chunks;
    
    IF row_count > 0 THEN
        RAISE NOTICE 'WARNING: krai_content.chunks contains % rows!', row_count;
        RAISE NOTICE 'Review data before dropping. Aborting migration.';
        RAISE EXCEPTION 'Table not empty - manual review required';
    ELSE
        RAISE NOTICE 'krai_content.chunks is empty - safe to drop';
    END IF;
END $$;

-- ======================================================================
-- Step 2: Drop unused table
-- ======================================================================

-- Drop dependent view first
DROP VIEW IF EXISTS public.vw_chunks CASCADE;

-- Drop the unused chunks table
DROP TABLE IF EXISTS krai_content.chunks CASCADE;

-- ======================================================================
-- Step 3: Create correct view pointing to krai_intelligence.chunks
-- ======================================================================

CREATE OR REPLACE VIEW public.chunks AS
SELECT 
    id,
    document_id,
    text_chunk,
    chunk_index,
    page_start,
    page_end,
    embedding,
    metadata,
    fingerprint,
    processing_status,
    created_at,
    updated_at
FROM krai_intelligence.chunks;

-- Grant access
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chunks TO anon, authenticated, service_role;

-- Add comment
COMMENT ON VIEW public.chunks IS 
'Main chunks table - contains document text chunks with metadata (including header info) and embeddings for semantic search';

-- ======================================================================
-- Verification
-- ======================================================================

-- Check table was dropped:
-- SELECT table_schema, table_name 
-- FROM information_schema.tables 
-- WHERE table_name = 'chunks';
-- 
-- Expected: Only krai_intelligence.chunks should exist

-- Check view works:
-- SELECT 
--     COUNT(*) as total_chunks,
--     COUNT(embedding) as chunks_with_embeddings,
--     COUNT(metadata->'page_header') as chunks_with_header_metadata
-- FROM public.chunks;
