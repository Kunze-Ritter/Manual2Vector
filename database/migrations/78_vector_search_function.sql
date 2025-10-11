-- ============================================================================
-- Migration 78: Vector Search Function for n8n
-- ============================================================================
-- Purpose: Create function for semantic search in chunks table
-- Date: 2025-10-11
-- ============================================================================

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION krai.match_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
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
        c.content,
        c.metadata,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM krai.chunks c
    WHERE c.embedding IS NOT NULL
      AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION krai.match_chunks IS 
'Semantic search function for n8n Vector Store. Returns chunks similar to query embedding.';

-- Grant execute permission
GRANT EXECUTE ON FUNCTION krai.match_chunks TO authenticated;
GRANT EXECUTE ON FUNCTION krai.match_chunks TO anon;

-- Test the function (after embeddings are created)
/*
-- Example usage:
SELECT * FROM krai.match_chunks(
    (SELECT embedding FROM krai.chunks LIMIT 1),  -- Test with existing embedding
    0.7,  -- Similarity threshold
    5     -- Number of results
);
*/

SELECT 'Vector search function created!' as status;
