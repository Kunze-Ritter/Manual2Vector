-- Migration 11: pgvector for Embeddings
-- 
-- Adds vector embeddings support to enable semantic search
-- Uses pgvector extension for efficient similarity search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to krai_intelligence.chunks table (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'krai_intelligence' 
        AND table_name = 'chunks' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE krai_intelligence.chunks 
        ADD COLUMN embedding vector(768);  -- embeddinggemma uses 768 dimensions
    END IF;
END $$;

-- Create index for fast vector similarity search
-- Using HNSW (Hierarchical Navigable Small World) for best performance
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx 
ON krai_intelligence.chunks 
USING hnsw (embedding vector_cosine_ops);

-- Alternative: IVFFlat index (faster build, slower search)
-- CREATE INDEX IF NOT EXISTS chunks_embedding_ivf_idx 
-- ON krai_core.chunks 
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- Function: Match similar chunks using cosine similarity
CREATE OR REPLACE FUNCTION public.match_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10,
    filter_document_id uuid DEFAULT NULL
)
RETURNS TABLE (
    chunk_id uuid,
    document_id uuid,
    chunk_index int,
    text_chunk text,
    page_start int,
    page_end int,
    similarity float,
    metadata jsonb
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = krai_intelligence, public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS chunk_id,
        c.document_id,
        c.chunk_index,
        c.text_chunk,
        c.page_start,
        c.page_end,
        1 - (c.embedding <=> query_embedding) AS similarity,  -- Cosine similarity
        c.metadata
    FROM krai_intelligence.chunks c
    WHERE 
        c.embedding IS NOT NULL
        AND (filter_document_id IS NULL OR c.document_id = filter_document_id)
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding  -- Sort by distance (lower = more similar)
    LIMIT match_count;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.match_chunks TO anon, authenticated, service_role;

-- Function: Get embedding statistics
CREATE OR REPLACE FUNCTION public.get_embedding_stats()
RETURNS TABLE (
    total_chunks bigint,
    chunks_with_embeddings bigint,
    embedding_coverage float,
    avg_chunk_length float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = krai_core, public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::bigint AS total_chunks,
        COUNT(embedding)::bigint AS chunks_with_embeddings,
        (COUNT(embedding)::float / NULLIF(COUNT(*), 0) * 100)::float AS embedding_coverage,
        AVG(LENGTH(text_chunk))::float AS avg_chunk_length
    FROM krai_intelligence.chunks;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.get_embedding_stats TO anon, authenticated, service_role;

-- Function: Find documents with similar content
CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.6,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    document_id uuid,
    avg_similarity float,
    matching_chunks int,
    document_filename text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = krai_core, public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.document_id,
        AVG(1 - (c.embedding <=> query_embedding))::float AS avg_similarity,
        COUNT(*)::int AS matching_chunks,
        d.filename
    FROM krai_intelligence.chunks c
    JOIN krai_core.documents d ON d.id = c.document_id
    WHERE 
        c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    GROUP BY c.document_id, d.filename
    ORDER BY avg_similarity DESC
    LIMIT match_count;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.match_documents TO anon, authenticated, service_role;

-- Add comment
COMMENT ON COLUMN krai_core.chunks.embedding IS 'Vector embedding (768-dim) for semantic search using embeddinggemma';
COMMENT ON FUNCTION public.match_chunks IS 'Find similar chunks using cosine similarity search';
COMMENT ON FUNCTION public.get_embedding_stats IS 'Get statistics about embedding coverage';
COMMENT ON FUNCTION public.match_documents IS 'Find documents with similar content based on chunk embeddings';
