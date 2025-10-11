-- ============================================================================
-- Migration 75: Agent Tool Functions for n8n Technician Agent V2.1
-- ============================================================================
-- Purpose: SQL Functions that the n8n agent can call via Supabase
-- Date: 2025-10-11
-- Author: KRAI Development Team
-- ============================================================================

-- ============================================================================
-- Tool 1: Error Code Search
-- ============================================================================

-- Drop existing function if it exists (with all overloads)
DROP FUNCTION IF EXISTS krai_intelligence.search_error_codes(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS krai_intelligence.search_error_codes(TEXT);
DROP FUNCTION IF EXISTS krai_intelligence.search_error_codes;

CREATE OR REPLACE FUNCTION krai_intelligence.search_error_codes(
    p_error_code TEXT,
    p_manufacturer TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL
)
RETURNS TABLE (
    error_code TEXT,
    description TEXT,
    cause TEXT,
    solution TEXT,
    page_number INTEGER,
    model_number TEXT,
    manufacturer TEXT,
    source_document TEXT,
    document_id UUID
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ec.error_code::TEXT,
        ec.description::TEXT,
        ec.cause::TEXT,
        ec.solution::TEXT,
        ec.page_number,
        p.model_number::TEXT,
        m.name::TEXT as manufacturer,
        d.filename::TEXT as source_document,
        d.id as document_id
    FROM krai_intelligence.error_codes ec
    LEFT JOIN krai_core.products p ON ec.product_id = p.id
    LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
    LEFT JOIN krai_core.documents d ON ec.document_id = d.id
    WHERE ec.error_code ILIKE '%' || p_error_code || '%'
        AND (p_manufacturer IS NULL OR m.name ILIKE '%' || p_manufacturer || '%')
        AND (p_model IS NULL OR p.model_number ILIKE '%' || p_model || '%')
    ORDER BY 
        -- Exact match first
        CASE WHEN ec.error_code = p_error_code THEN 0 ELSE 1 END,
        -- Then by similarity
        similarity(ec.error_code, p_error_code) DESC
    LIMIT 5;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.search_error_codes IS 
'Search for error codes with optional manufacturer and model filters. Returns up to 5 best matches.';

-- ============================================================================
-- Tool 2: Parts Search
-- ============================================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS krai_intelligence.search_parts(TEXT, TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS krai_intelligence.search_parts;

CREATE OR REPLACE FUNCTION krai_intelligence.search_parts(
    p_search_term TEXT,
    p_part_number TEXT DEFAULT NULL,
    p_manufacturer TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL
)
RETURNS TABLE (
    part_number TEXT,
    part_name TEXT,
    description TEXT,
    page_number INTEGER,
    model_number TEXT,
    manufacturer TEXT,
    source_document TEXT,
    document_id UUID
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pt.part_number::TEXT,
        pt.part_name::TEXT,
        pt.description::TEXT,
        pt.page_number,
        p.model_number::TEXT,
        m.name::TEXT as manufacturer,
        d.filename::TEXT as source_document,
        d.id as document_id
    FROM krai_parts.parts_catalog pt
    LEFT JOIN krai_core.manufacturers m ON pt.manufacturer_id = m.id
    LEFT JOIN krai_core.documents d ON pt.document_id = d.id
    LEFT JOIN krai_core.document_products dp ON d.id = dp.document_id
    LEFT JOIN krai_core.products p ON dp.product_id = p.id
    WHERE (
        pt.part_name ILIKE '%' || p_search_term || '%' 
        OR pt.description ILIKE '%' || p_search_term || '%'
        OR (p_part_number IS NOT NULL AND pt.part_number ILIKE '%' || p_part_number || '%')
    )
    AND (p_manufacturer IS NULL OR m.name ILIKE '%' || p_manufacturer || '%')
    AND (p_model IS NULL OR p.model_number ILIKE '%' || p_model || '%')
    ORDER BY 
        -- Exact part number match first
        CASE WHEN pt.part_number = p_part_number THEN 0 ELSE 1 END,
        -- Then by name similarity
        similarity(pt.part_name, p_search_term) DESC
    LIMIT 10;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.search_parts IS 
'Search for parts by name, description or part number. Returns up to 10 best matches.';

-- ============================================================================
-- Tool 3: Product Info
-- ============================================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS krai_intelligence.get_product_info(TEXT, TEXT);
DROP FUNCTION IF EXISTS krai_intelligence.get_product_info;

CREATE OR REPLACE FUNCTION krai_intelligence.get_product_info(
    p_model_number TEXT,
    p_manufacturer TEXT DEFAULT NULL
)
RETURNS TABLE (
    product_id UUID,
    model_number TEXT,
    manufacturer TEXT,
    manufacturer_id UUID,
    series_name TEXT,
    product_type TEXT,
    oem_manufacturer TEXT,
    oem_relationship_type TEXT,
    document_count BIGINT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id as product_id,
        p.model_number::TEXT,
        m.name::TEXT as manufacturer,
        m.id as manufacturer_id,
        ps.series_name::TEXT,
        p.product_type::TEXT,
        p.oem_manufacturer::TEXT,
        p.oem_relationship_type::TEXT,
        COUNT(DISTINCT dp.document_id) as document_count
    FROM krai_core.products p
    LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
    LEFT JOIN krai_core.product_series ps ON p.series_id = ps.id
    LEFT JOIN krai_core.document_products dp ON p.id = dp.product_id
    WHERE p.model_number ILIKE '%' || p_model_number || '%'
        AND (p_manufacturer IS NULL OR m.name ILIKE '%' || p_manufacturer || '%')
    GROUP BY p.id, m.id, m.name, ps.series_name
    ORDER BY 
        -- Exact match first
        CASE WHEN p.model_number = p_model_number THEN 0 ELSE 1 END,
        similarity(p.model_number, p_model_number) DESC
    LIMIT 5;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.get_product_info IS 
'Get detailed product information including series, OEM info and document count.';

-- ============================================================================
-- Tool 4: Video Search
-- ============================================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS krai_intelligence.search_videos(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS krai_intelligence.search_videos;

CREATE OR REPLACE FUNCTION krai_intelligence.search_videos(
    p_search_term TEXT,
    p_manufacturer TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL
)
RETURNS TABLE (
    video_id UUID,
    youtube_id TEXT,
    title TEXT,
    description TEXT,
    channel_name TEXT,
    view_count INTEGER,
    thumbnail_url TEXT,
    video_url TEXT,
    manufacturer TEXT,
    model_number TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id as video_id,
        v.youtube_id::TEXT,
        v.title::TEXT,
        v.description::TEXT,
        v.channel_name::TEXT,
        v.view_count,
        v.thumbnail_url::TEXT,
        'https://www.youtube.com/watch?v=' || v.youtube_id as video_url,
        m.name::TEXT as manufacturer,
        p.model_number::TEXT
    FROM krai_content.videos v
    LEFT JOIN krai_core.documents d ON v.document_id = d.id
    LEFT JOIN krai_core.manufacturers m ON d.manufacturer_id = m.id
    LEFT JOIN krai_core.document_products dp ON d.id = dp.document_id
    LEFT JOIN krai_core.products p ON dp.product_id = p.id
    WHERE (
        v.title ILIKE '%' || p_search_term || '%'
        OR v.description ILIKE '%' || p_search_term || '%'
    )
    AND (p_manufacturer IS NULL OR m.name ILIKE '%' || p_manufacturer || '%')
    AND (p_model IS NULL OR p.model_number ILIKE '%' || p_model || '%')
    ORDER BY 
        -- Prioritize by view count and relevance
        v.view_count DESC NULLS LAST,
        similarity(v.title, p_search_term) DESC
    LIMIT 5;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.search_videos IS 
'Search for YouTube videos related to repairs, maintenance or tutorials.';

-- ============================================================================
-- Tool 5: Context-Aware Document Search
-- ============================================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS krai_intelligence.search_documentation_context(TEXT, TEXT, TEXT, TEXT, INTEGER);
DROP FUNCTION IF EXISTS krai_intelligence.search_documentation_context;

CREATE OR REPLACE FUNCTION krai_intelligence.search_documentation_context(
    p_query TEXT,
    p_manufacturer TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL,
    p_document_type TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    chunk_id UUID,
    text_chunk TEXT,
    page_number INTEGER,
    filename TEXT,
    document_type TEXT,
    manufacturer TEXT,
    model_number TEXT,
    relevance_score FLOAT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id as chunk_id,
        c.text_chunk::TEXT,
        c.page_number,
        d.filename::TEXT,
        d.document_type::TEXT,
        d.manufacturer::TEXT,
        p.model_number::TEXT,
        -- Simple text relevance score (can be enhanced with embeddings)
        (
            similarity(c.text_chunk, p_query) * 0.7 +
            CASE WHEN c.text_chunk ILIKE '%' || p_query || '%' THEN 0.3 ELSE 0 END
        ) as relevance_score
    FROM krai_intelligence.chunks c
    LEFT JOIN krai_core.documents d ON c.document_id = d.id
    LEFT JOIN krai_core.document_products dp ON d.id = dp.document_id
    LEFT JOIN krai_core.products p ON dp.product_id = p.id
    WHERE c.text_chunk ILIKE '%' || p_query || '%'
        AND (p_manufacturer IS NULL OR d.manufacturer ILIKE '%' || p_manufacturer || '%')
        AND (p_model IS NULL OR p.model_number ILIKE '%' || p_model || '%')
        AND (p_document_type IS NULL OR d.document_type = p_document_type)
    ORDER BY relevance_score DESC
    LIMIT p_limit;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.search_documentation_context IS 
'Context-aware search in documentation chunks with manufacturer and model filters.';

-- ============================================================================
-- Grant permissions to authenticated users
-- ============================================================================
GRANT EXECUTE ON FUNCTION krai_intelligence.search_error_codes TO authenticated;
GRANT EXECUTE ON FUNCTION krai_intelligence.search_parts TO authenticated;
GRANT EXECUTE ON FUNCTION krai_intelligence.get_product_info TO authenticated;
GRANT EXECUTE ON FUNCTION krai_intelligence.search_videos TO authenticated;
GRANT EXECUTE ON FUNCTION krai_intelligence.search_documentation_context TO authenticated;

-- Grant to anon for public API access (if needed)
GRANT EXECUTE ON FUNCTION krai_intelligence.search_error_codes TO anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.search_parts TO anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.get_product_info TO anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.search_videos TO anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.search_documentation_context TO anon;

-- ============================================================================
-- Enable pg_trgm extension for similarity search (if not already enabled)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- Create indexes for better performance
-- ============================================================================

-- Error codes
CREATE INDEX IF NOT EXISTS idx_error_codes_code_trgm 
ON krai_core.error_codes USING gin (error_code gin_trgm_ops);

-- Parts
CREATE INDEX IF NOT EXISTS idx_parts_name_trgm 
ON krai_core.parts USING gin (part_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_parts_number_trgm 
ON krai_core.parts USING gin (part_number gin_trgm_ops);

-- Products
CREATE INDEX IF NOT EXISTS idx_products_model_trgm 
ON krai_core.products USING gin (model_number gin_trgm_ops);

-- Videos
CREATE INDEX IF NOT EXISTS idx_videos_title_trgm 
ON krai_content.videos USING gin (title gin_trgm_ops);

-- Chunks
CREATE INDEX IF NOT EXISTS idx_chunks_text_trgm 
ON krai_intelligence.chunks USING gin (text_chunk gin_trgm_ops);

-- ============================================================================
-- Test queries (comment out after testing)
-- ============================================================================

-- Test error code search
-- SELECT * FROM krai_intelligence.search_error_codes('C-9402', 'Lexmark', 'CX963');

-- Test parts search
-- SELECT * FROM krai_intelligence.search_parts('Fuser', NULL, 'Lexmark', 'CX963');

-- Test product info
-- SELECT * FROM krai_intelligence.get_product_info('CX963', 'Lexmark');

-- Test video search
-- SELECT * FROM krai_intelligence.search_videos('Fuser replacement', 'Lexmark', NULL);

-- Test documentation search
-- SELECT * FROM krai_intelligence.search_documentation_context('How to replace fuser unit', 'Lexmark', 'CX963', 'service_manual', 3);
