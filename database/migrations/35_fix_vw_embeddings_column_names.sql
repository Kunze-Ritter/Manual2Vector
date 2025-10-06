-- ======================================================================
-- Migration 35: Fix vw_embeddings Column Names for N8N
-- ======================================================================
-- Description: Fix column names in vw_embeddings view for N8N Vector Store compatibility
-- Date: 2025-10-06
-- Reason: N8N Vector Store expects 'embedding' column, not 'embedding_vector'
-- ======================================================================

-- Background:
-- N8N Vector Store Node expects specific column names:
-- - embedding (for the vector)
-- - metadata (for additional data)
--
-- Migration 26 used 'embedding_vector' which breaks N8N compatibility

-- Drop old view
DROP VIEW IF EXISTS public.vw_embeddings CASCADE;

-- Recreate view with N8N-compatible column names
CREATE OR REPLACE VIEW public.vw_embeddings AS
SELECT 
    id,
    id as chunk_id,
    document_id,
    text_chunk as content,              -- N8N uses 'content' for text
    embedding as embedding,              -- ✅ N8N expects 'embedding' NOT 'embedding_vector'
    jsonb_build_object(
        'chunk_index', chunk_index,
        'page_start', page_start,
        'page_end', page_end,
        'document_id', document_id,
        'embedding_model', 'embeddinggemma',
        'dimensions', 768
    ) as metadata,                       -- N8N stores extra data in 'metadata'
    created_at
FROM krai_intelligence.chunks
WHERE embedding IS NOT NULL;

-- Grant access
GRANT SELECT ON public.vw_embeddings TO anon, authenticated, service_role;

-- Update comment
COMMENT ON VIEW public.vw_embeddings IS 
'N8N-compatible view of chunk embeddings for Vector Search. 
Columns optimized for N8N Vector Store Node:
- embedding: The pgvector embedding
- content: The text content
- metadata: Additional chunk information';

-- ======================================================================
-- Verification
-- ======================================================================

-- Test the view structure
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'vw_embeddings'
ORDER BY ordinal_position;

-- Expected columns:
-- id              | uuid
-- chunk_id        | uuid
-- document_id     | uuid
-- content         | text
-- embedding       | vector(768)
-- metadata        | jsonb
-- created_at      | timestamp

-- Test vector search capability
SELECT 
    id,
    chunk_id,
    substring(content, 1, 100) as content_preview,
    metadata->>'chunk_index' as chunk_index,
    metadata->>'page_start' as page_start,
    created_at
FROM public.vw_embeddings
ORDER BY created_at DESC
LIMIT 5;

-- Test embedding column exists
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(embedding) as embeddings_present,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as percentage
FROM public.vw_embeddings;

-- Expected: 100% embeddings present

-- ======================================================================
-- N8N Vector Store Node Configuration
-- ======================================================================
--
-- In N8N Vector Store Node, use these settings:
--
-- Table Name: vw_embeddings
-- Query Name: embedding      ← This is the embedding column
-- Content Column: content    ← This is the text column  
-- Metadata Column: metadata  ← This contains extra data
-- Top K: 5                   ← Number of results
--
-- ======================================================================
