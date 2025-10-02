-- ============================================
-- Migration: Create n8n-compatible vector search function
-- Date: 2025-10-02
-- Purpose: n8n Supabase Vector Store expects match_documents function
-- ============================================

-- Create n8n-compatible vector search function in public schema
CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding vector(768),
    match_count integer DEFAULT 5,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.text_chunk as content,
        jsonb_build_object(
            'document_id', c.document_id::text,
            'chunk_index', c.chunk_index,
            'page_number', c.page_number,
            'source', d.filename,
            'manufacturer', m.name,
            'product', p.model
        ) as metadata,
        (1 - (e.embedding <=> query_embedding))::float as similarity
    FROM krai_content.chunks c
    JOIN krai_intelligence.embeddings e ON c.id = e.chunk_id
    LEFT JOIN krai_core.documents d ON c.document_id = d.id
    LEFT JOIN krai_core.manufacturers m ON d.manufacturer_id = m.id
    LEFT JOIN krai_core.products p ON d.product_id = p.id
    WHERE 
        c.processing_status = 'completed'
        AND e.embedding IS NOT NULL
        -- Filter by similarity threshold
        AND (1 - (e.embedding <=> query_embedding)) > 0.5
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant access to the function
GRANT EXECUTE ON FUNCTION public.match_documents(vector(768), integer, jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.match_documents(vector(768), integer, jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION public.match_documents(vector(768), integer, jsonb) TO anon;

-- Add comment
COMMENT ON FUNCTION public.match_documents IS 'n8n Vector Store: Search for similar documents using cosine similarity';

-- ============================================
-- ALTERNATIVE: If you want to use embeddings view
-- ============================================

-- Create version that works with vw_embeddings view
CREATE OR REPLACE FUNCTION public.match_embeddings(
    query_embedding vector(768),
    match_count integer DEFAULT 5,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.text_content as content,
        jsonb_build_object(
            'chunk_id', e.chunk_id::text,
            'document_id', e.document_id::text,
            'model_name', e.model_name,
            'created_at', e.created_at::text
        ) as metadata,
        (1 - (e.embedding <=> query_embedding))::float as similarity
    FROM krai_intelligence.embeddings e
    WHERE 
        e.embedding IS NOT NULL
        -- Filter by similarity threshold
        AND (1 - (e.embedding <=> query_embedding)) > 0.5
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant access
GRANT EXECUTE ON FUNCTION public.match_embeddings(vector(768), integer, jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.match_embeddings(vector(768), integer, jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION public.match_embeddings(vector(768), integer, jsonb) TO anon;

COMMENT ON FUNCTION public.match_embeddings IS 'n8n Vector Store: Alternative function using embeddings table directly';

-- ============================================
-- EXPLANATION
-- ============================================
-- n8n Supabase Vector Store expects a function with signature:
--   match_documents(query_embedding, match_count, filter)
--
-- Returns:
--   - id: UUID of the chunk/document
--   - content: Text content
--   - metadata: JSONB with additional info
--   - similarity: Float similarity score (0-1)
--
-- Two versions created:
--   1. match_documents - Uses chunks table with joins
--   2. match_embeddings - Uses embeddings table directly
--
-- Use match_documents for richer metadata
-- Use match_embeddings for faster queries
-- ============================================

-- VERIFICATION
-- ============================================
-- Test the function (replace with actual embedding):
-- SELECT * FROM public.match_documents(
--     '[0.1, 0.2, ...]'::vector(768),  -- Replace with real embedding
--     5,
--     '{}'::jsonb
-- );
--
-- Check function exists:
-- SELECT routine_name, routine_type 
-- FROM information_schema.routines 
-- WHERE routine_schema = 'public' 
-- AND routine_name LIKE 'match_%';
-- ============================================
