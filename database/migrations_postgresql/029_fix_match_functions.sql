-- database/migrations_postgresql/029_fix_match_functions.sql
-- Fix: match_chunks and match_multimodal referenced c.chunk_text (wrong column).
-- Correct column name is c.text_chunk per krai_intelligence.chunks schema.
-- See CLAUDE.md known column name traps.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'krai_intelligence'
      AND table_name = 'chunks'
      AND column_name = 'text_chunk'
  ) THEN
    RAISE EXCEPTION 'Column krai_intelligence.chunks.text_chunk does not exist — check schema';
  END IF;
END $$;

-- Fix match_chunks
CREATE OR REPLACE FUNCTION krai_intelligence.match_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
) RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_text text,
    page_number int,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.document_id,
        c.text_chunk,          -- FIXED: was c.chunk_text
        c.page_number,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM krai_intelligence.chunks c
    WHERE c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Fix match_multimodal
CREATE OR REPLACE FUNCTION krai_intelligence.match_multimodal(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
) RETURNS TABLE (
    source_id uuid,
    source_type text,
    content text,
    document_id uuid,
    page_number int,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    WITH all_matches AS (
        -- Text chunks
        SELECT
            c.id as source_id,
            'chunk'::text as source_type,
            c.text_chunk as content,   -- FIXED: was c.chunk_text
            c.document_id,
            c.page_number,
            1 - (c.embedding <=> query_embedding) as similarity
        FROM krai_intelligence.chunks c
        WHERE c.embedding IS NOT NULL
            AND 1 - (c.embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Images
        SELECT
            i.id as source_id,
            'image'::text as source_type,
            COALESCE(i.ai_description, i.figure_context, '') as content,
            i.document_id,
            i.page_number,
            1 - (i.context_embedding <=> query_embedding) as similarity
        FROM krai_content.images i
        WHERE i.context_embedding IS NOT NULL
            AND 1 - (i.context_embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Videos
        SELECT
            v.id as source_id,
            'video'::text as source_type,
            COALESCE(v.description, v.title, '') as content,
            v.document_id,
            v.page_number,
            1 - (v.context_embedding <=> query_embedding) as similarity
        FROM krai_content.videos v
        WHERE v.context_embedding IS NOT NULL
            AND 1 - (v.context_embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Links
        SELECT
            l.id as source_id,
            'link'::text as source_type,
            COALESCE(l.description, l.url, '') as content,
            l.document_id,
            l.page_number,
            1 - (l.context_embedding <=> query_embedding) as similarity
        FROM krai_content.links l
        WHERE l.context_embedding IS NOT NULL
            AND 1 - (l.context_embedding <=> query_embedding) > match_threshold

        UNION ALL

        -- Structured tables
        SELECT
            t.id as source_id,
            'table'::text as source_type,
            COALESCE(t.table_markdown, '') as content,
            t.document_id,
            t.page_number,
            1 - (t.table_embedding <=> query_embedding) as similarity
        FROM krai_intelligence.structured_tables t
        WHERE t.table_embedding IS NOT NULL
            AND 1 - (t.table_embedding <=> query_embedding) > match_threshold
    )
    SELECT * FROM all_matches
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Record migration
INSERT INTO krai_system.migrations (migration_name, applied_at, description)
VALUES ('029_fix_match_functions', NOW(), 'Fix match_chunks and match_multimodal: use c.text_chunk instead of c.chunk_text')
ON CONFLICT (migration_name) DO NOTHING;
