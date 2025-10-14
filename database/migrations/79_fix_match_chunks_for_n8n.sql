-- Migration 79: Fix match_chunks function for n8n compatibility
-- n8n expects: match_chunks(filter, match_count, query_embedding)
-- Current function has: match_chunks(query_embedding, match_threshold, match_count, filter_document_id)

-- Create n8n-compatible wrapper function
CREATE OR REPLACE FUNCTION public.match_chunks(
    filter jsonb DEFAULT '{}'::jsonb,
    match_count integer DEFAULT 10,
    query_embedding vector DEFAULT NULL
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
    -- Call the original function with correct parameter order
    RETURN QUERY
    SELECT 
        c.id,
        c.text_chunk as content,
        c.metadata,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM krai_intelligence.chunks c
    WHERE 
        -- Apply filters if provided
        CASE 
            WHEN filter ? 'document_id' THEN 
                c.document_id = (filter->>'document_id')::uuid
            ELSE true
        END
        -- Only return results with embeddings
        AND c.embedding IS NOT NULL
        -- Similarity threshold
        AND 1 - (c.embedding <=> query_embedding) > 0.5
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.match_chunks(jsonb, integer, vector) TO authenticated;
GRANT EXECUTE ON FUNCTION public.match_chunks(jsonb, integer, vector) TO anon;
GRANT EXECUTE ON FUNCTION public.match_chunks(jsonb, integer, vector) TO service_role;

-- Add comment
COMMENT ON FUNCTION public.match_chunks(jsonb, integer, vector) IS 
'n8n-compatible vector similarity search function. Searches chunks by embedding similarity with optional filters.';
