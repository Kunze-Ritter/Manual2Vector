-- ======================================================================
-- Migration 26: Update vw_embeddings View to Point to chunks Table
-- ======================================================================
-- Description: Fix N8N Vector Search - embeddings are now in chunks.embedding column
-- Date: 2025-10-05
-- Reason: Migration 25 dropped old embeddings table, N8N needs updated view
-- ======================================================================

-- Background:
-- Old: vw_embeddings → krai_intelligence.embeddings (DROPPED in Migration 25)
-- New: vw_embeddings → krai_intelligence.chunks (embeddings stored here now)
--
-- N8N Vector Search Tool uses vw_embeddings view for similarity search
-- This migration ensures N8N continues to work after embeddings table removal

-- Drop old view (points to non-existent embeddings table)
DROP VIEW IF EXISTS public.vw_embeddings CASCADE;

-- Recreate view pointing to chunks table
CREATE OR REPLACE VIEW public.vw_embeddings AS
SELECT 
    id,
    id as chunk_id,                    -- For compatibility (chunks are embeddings now)
    'embeddinggemma' as embedding_model,  -- Current model
    embedding as embedding_vector,     -- Renamed column
    768 as embedding_dimensions,       -- embeddinggemma dimension
    created_at,
    document_id,                       -- Extra: helpful for filtering
    text_chunk,                        -- Extra: the actual text
    chunk_index,                       -- Extra: for ordering
    page_start,                        -- Extra: for context
    page_end                           -- Extra: for context
FROM krai_intelligence.chunks
WHERE embedding IS NOT NULL;          -- Only chunks with embeddings

-- Grant access
GRANT SELECT ON public.vw_embeddings TO anon, authenticated, service_role;

-- Update comment
COMMENT ON VIEW public.vw_embeddings IS 
'Read-only view of chunk embeddings for N8N Vector Search. Points to krai_intelligence.chunks.embedding column (new design).';

-- ======================================================================
-- Verification
-- ======================================================================

-- Test the view
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT embedding_model) as models_used,
    MIN(embedding_dimensions) as min_dims,
    MAX(embedding_dimensions) as max_dims,
    MIN(created_at) as oldest_embedding,
    MAX(created_at) as newest_embedding
FROM public.vw_embeddings;

-- Expected:
-- total_embeddings: 47061
-- models_used: 1 (embeddinggemma)
-- min_dims: 768
-- max_dims: 768

-- Test vector search capability (sample query)
-- This is what N8N does internally:
SELECT 
    id,
    chunk_id,
    text_chunk,
    page_start,
    document_id
FROM public.vw_embeddings
ORDER BY created_at DESC
LIMIT 5;

-- Expected: 5 rows with text_chunk and embedding data
