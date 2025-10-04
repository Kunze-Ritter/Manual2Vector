-- ======================================================================
-- Migration 20c: Create Public Chunks View
-- ======================================================================
-- Description: Create view pointing to krai_intelligence.chunks
-- Date: 2025-10-05
-- Purpose: Provide PostgREST access to chunks table
-- Prerequisite: Run 20a and 20b first
-- ======================================================================

-- Create view pointing to krai_intelligence.chunks
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

-- Grant access to all roles
GRANT SELECT ON public.chunks TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chunks TO service_role;

-- Add helpful comment
COMMENT ON VIEW public.chunks IS 
'Main chunks table - contains document text chunks with metadata (including header info) and embeddings for semantic search. Points to krai_intelligence.chunks.';

-- ======================================================================
-- Verification
-- ======================================================================

-- Check view was created:
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name = 'chunks'
ORDER BY table_schema;

-- Expected output:
-- | table_schema        | table_name | table_type  |
-- |---------------------|------------|-------------|
-- | krai_intelligence   | chunks     | BASE TABLE  |
-- | public              | chunks     | VIEW        |

-- Check view works and shows metadata:
SELECT 
    COUNT(*) as total_chunks,
    COUNT(embedding) as chunks_with_embeddings,
    COUNT(metadata->'page_header') as chunks_with_header_metadata,
    COUNT(metadata->'header_products') as chunks_with_products
FROM public.chunks;

-- Expected: All counts should match krai_intelligence.chunks
