-- ======================================================================
-- Migration 36: Create N8N Vector Search Function
-- ======================================================================
-- Description: Create match_documents function for N8N Vector Store Node
-- Date: 2025-10-06
-- Reason: N8N Supabase Vector Store expects a vector similarity search function
-- ======================================================================

-- Background:
-- N8N Vector Store Node calls a PostgreSQL function for similarity search
-- The function must be named based on the "Query Name" parameter
-- Query Name: "embedding" → Function: "match_embedding" or "embedding"
--
-- N8N expects this signature:
-- function_name(query_embedding vector, match_count int, filter jsonb DEFAULT '{}')

-- Drop old function if exists
DROP FUNCTION IF EXISTS public.match_documents(vector, int, jsonb);
DROP FUNCTION IF EXISTS public.match_embeddings(vector, int, jsonb);
DROP FUNCTION IF EXISTS public.embedding(vector, int, jsonb);

-- Create the vector similarity search function
-- Name: match_documents (N8N default)
CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding vector(768),
    match_count int DEFAULT 5,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id uuid,
    chunk_id uuid,
    document_id uuid,
    content text,
    embedding vector(768),
    metadata jsonb,
    created_at timestamp with time zone,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        vw.id,
        vw.chunk_id,
        vw.document_id,
        vw.content,
        vw.embedding,
        vw.metadata,
        vw.created_at,
        1 - (vw.embedding <=> query_embedding) AS similarity
    FROM public.vw_embeddings vw
    WHERE 
        -- Apply filters if provided
        (filter = '{}'::jsonb OR vw.metadata @> filter)
    ORDER BY vw.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Also create function with "embedding" name (alternative for N8N)
CREATE OR REPLACE FUNCTION public.embedding(
    query_embedding vector(768),
    match_count int DEFAULT 5,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id uuid,
    chunk_id uuid,
    document_id uuid,
    content text,
    embedding vector(768),
    metadata jsonb,
    created_at timestamp with time zone,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM public.match_documents(query_embedding, match_count, filter);
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.match_documents(vector(768), int, jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.embedding(vector(768), int, jsonb) TO anon, authenticated, service_role;

-- Add comments
COMMENT ON FUNCTION public.match_documents IS 
'Vector similarity search function for N8N Vector Store. 
Searches vw_embeddings view using cosine similarity.
Returns top K most similar chunks with similarity score.';

COMMENT ON FUNCTION public.embedding IS 
'Alias for match_documents function. 
N8N Vector Store may call this based on Query Name parameter.';

-- ======================================================================
-- Verification
-- ======================================================================

-- Test the function with a random embedding
WITH random_embedding AS (
    SELECT embedding as query_vec
    FROM public.vw_embeddings
    ORDER BY random()
    LIMIT 1
)
SELECT 
    id,
    substring(content, 1, 50) as content_preview,
    round(similarity::numeric, 4) as similarity_score
FROM public.match_documents(
    (SELECT query_vec FROM random_embedding),
    5,
    '{}'::jsonb
)
ORDER BY similarity DESC;

-- Expected: 5 rows with similarity scores between 0 and 1

-- Test with filter
WITH random_embedding AS (
    SELECT embedding as query_vec
    FROM public.vw_embeddings
    ORDER BY random()
    LIMIT 1
)
SELECT 
    id,
    metadata->>'page_start' as page,
    round(similarity::numeric, 4) as similarity_score
FROM public.match_documents(
    (SELECT query_vec FROM random_embedding),
    3,
    '{"embedding_model": "embeddinggemma"}'::jsonb
)
ORDER BY similarity DESC;

-- Expected: 3 rows filtered by embedding_model

-- ======================================================================
-- N8N Configuration
-- ======================================================================
--
-- In N8N Supabase Vector Store Node:
--
-- Table Name: vw_embeddings
-- Query Name: embedding          ← This determines function name
-- Top K: 5
--
-- N8N will call: public.embedding(query_vector, 5, '{}')
-- Which internally calls: public.match_documents(...)
--
-- ======================================================================
