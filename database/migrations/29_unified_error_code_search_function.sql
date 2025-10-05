-- ======================================================================
-- Migration 29: Unified Error Code Search Function
-- ======================================================================
-- Description: Multi-resource search function for error codes
--              Returns: Service Manuals, Bulletins, Videos, Links, Parts
-- Date: 2025-10-05
-- Reason: Enable technicians to find ALL resources for an error code in one query
-- ======================================================================

-- This is the CORE function for the N8N "Search Error Code" tool
-- It aggregates results from multiple tables and ranks them by priority

CREATE OR REPLACE FUNCTION search_error_code_resources(
    p_error_code VARCHAR(20),
    p_manufacturer_id UUID DEFAULT NULL,
    p_series_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    resource_type TEXT,
    resource_id UUID,
    title TEXT,
    description TEXT,
    url TEXT,
    page_number INTEGER,
    priority INTEGER,
    relevance_score NUMERIC,
    document_type TEXT,
    document_title TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    
    -- ====================================================================
    -- SOURCE 1: Error Code Entries from Service Manuals/Bulletins
    -- Priority: 1 (bulletins), 2 (service_manual)
    -- ====================================================================
    SELECT 
        'error_code'::TEXT as resource_type,
        ec.id as resource_id,
        (ec.error_code || ': ' || COALESCE(ec.error_description, 'No description'))::TEXT as title,
        COALESCE(ec.solution_text, 'No solution available')::TEXT as description,
        NULL::TEXT as url,
        ec.page_number,
        d.priority_level as priority,
        ec.confidence_score::NUMERIC as relevance_score,
        d.document_type::TEXT,
        d.filename::TEXT as document_title,
        jsonb_build_object(
            'document_id', ec.document_id,
            'document_type', d.document_type,
            'has_image', ec.image_id IS NOT NULL,
            'has_chunk', ec.chunk_id IS NOT NULL,
            'extraction_method', ec.extraction_method,
            'severity', ec.severity_level,
            'requires_technician', ec.requires_technician,
            'requires_parts', ec.requires_parts,
            'context_text', LEFT(ec.context_text, 200)
        ) as metadata
    FROM krai_intelligence.error_codes ec
    JOIN krai_core.documents d ON ec.document_id = d.id
    WHERE ec.error_code = p_error_code
    AND (p_manufacturer_id IS NULL OR ec.manufacturer_id = p_manufacturer_id)
    
    UNION ALL
    
    -- ====================================================================
    -- SOURCE 2: Chunks with Error Code mentions (fallback)
    -- Priority: 3 (manual context)
    -- ====================================================================
    SELECT * FROM (
        SELECT 
            'chunk'::TEXT as resource_type,
            c.id as resource_id,
            ('Context: ' || LEFT(c.text_chunk, 100) || '...')::TEXT as title,
            LEFT(c.text_chunk, 300)::TEXT as description,
            NULL::TEXT as url,
            c.page_start as page_number,
            d.priority_level + 1 as priority,
            0.7::NUMERIC as relevance_score,
            d.document_type::TEXT,
            d.filename::TEXT as document_title,
            jsonb_build_object(
                'document_id', c.document_id,
                'chunk_type', c.metadata->>'chunk_type',
                'page_start', c.page_start,
                'page_end', c.page_end,
                'chunk_index', c.chunk_index
            ) as metadata
        FROM krai_intelligence.chunks c
        JOIN krai_core.documents d ON c.document_id = d.id
        WHERE c.text_chunk ILIKE '%' || p_error_code || '%'
        AND (c.metadata->>'chunk_type' IN ('error_code_section', 'troubleshooting') OR c.metadata->>'chunk_type' IS NULL)
        LIMIT 5
    ) chunks
    
    UNION ALL
    
    -- ====================================================================
    -- SOURCE 3A: Video Links (from links table with video type)
    -- Priority: 3 (video tutorials)
    -- NOTE: Videos table might be empty, so we search links with video type
    -- ====================================================================
    SELECT 
        'video'::TEXT as resource_type,
        l.id as resource_id,
        COALESCE(l.description, 'Video Tutorial')::TEXT as title,
        COALESCE(l.description, 'No description')::TEXT as description,
        l.url::TEXT as url,
        l.page_number,
        3 as priority,
        0.85::NUMERIC as relevance_score,
        'video'::TEXT as document_type,
        d.filename::TEXT as document_title,
        jsonb_build_object(
            'link_id', l.id,
            'link_type', l.link_type,
            'video_id', l.video_id,
            'related_error_codes', l.related_error_codes
        ) as metadata
    FROM krai_content.links l
    LEFT JOIN krai_core.documents d ON l.document_id = d.id
    WHERE l.link_type IN ('video', 'youtube', 'vimeo')
    AND l.is_active = true
    AND (
        -- Direct error code match
        p_error_code = ANY(l.related_error_codes)
        -- Or mentioned in description/url
        OR l.description ILIKE '%' || p_error_code || '%'
        OR l.url ILIKE '%' || p_error_code || '%'
    )
    AND (p_manufacturer_id IS NULL OR l.manufacturer_id = p_manufacturer_id)
    AND (p_series_id IS NULL OR l.series_id = p_series_id)
    
    UNION ALL
    
    -- ====================================================================
    -- SOURCE 3B: Video Metadata (from videos table if populated)
    -- Priority: 3 (video tutorials with full metadata)
    -- ====================================================================
    SELECT 
        'video'::TEXT as resource_type,
        v.id as resource_id,
        COALESCE(v.title, 'Video Tutorial')::TEXT as title,
        COALESCE(v.description, 'No description')::TEXT as description,
        COALESCE(l.url, v.title)::TEXT as url,
        NULL::INTEGER as page_number,
        3 as priority,
        0.9::NUMERIC as relevance_score,
        'video'::TEXT as document_type,
        d.filename::TEXT as document_title,
        jsonb_build_object(
            'link_id', v.link_id,
            'duration', v.duration,
            'channel_title', v.channel_title,
            'thumbnail_url', v.thumbnail_url,
            'related_error_codes', v.related_error_codes
        ) as metadata
    FROM krai_content.videos v
    LEFT JOIN krai_content.links l ON v.link_id = l.id
    LEFT JOIN krai_core.documents d ON l.document_id = d.id
    WHERE (
        -- Direct error code match
        p_error_code = ANY(v.related_error_codes)
        -- Or mentioned in title/description
        OR v.title ILIKE '%' || p_error_code || '%'
        OR v.description ILIKE '%' || p_error_code || '%'
    )
    AND (p_manufacturer_id IS NULL OR v.manufacturer_id = p_manufacturer_id)
    AND (p_series_id IS NULL OR v.series_id = p_series_id)
    
    UNION ALL
    
    -- ====================================================================
    -- SOURCE 4: External Links (tutorials, support pages)
    -- Priority: 4 (external resources)
    -- ====================================================================
    SELECT 
        'link'::TEXT as resource_type,
        l.id as resource_id,
        COALESCE(l.description, 'External Resource')::TEXT as title,
        COALESCE(l.description, 'No description')::TEXT as description,
        l.url::TEXT as url,
        l.page_number,
        4 as priority,
        0.7::NUMERIC as relevance_score,
        l.link_type::TEXT as document_type,
        d.filename::TEXT as document_title,
        jsonb_build_object(
            'document_id', l.document_id,
            'link_type', l.link_type,
            'is_active', l.is_active,
            'related_error_codes', l.related_error_codes
        ) as metadata
    FROM krai_content.links l
    LEFT JOIN krai_core.documents d ON l.document_id = d.id
    WHERE (
        -- Direct error code match
        p_error_code = ANY(l.related_error_codes)
        -- Or mentioned in description/url
        OR l.description ILIKE '%' || p_error_code || '%'
        OR l.url ILIKE '%' || p_error_code || '%'
    )
    AND (p_manufacturer_id IS NULL OR l.manufacturer_id = p_manufacturer_id)
    AND (p_series_id IS NULL OR l.series_id = p_series_id)
    AND l.is_active = true
    
    
    -- ====================================================================
    -- SOURCE 5: Related Spare Parts (if mentioned in error context)
    -- Priority: 5 (parts for replacement)
    -- NOTE: Skipped for now as krai_parts.spare_parts table doesn't exist yet
    -- ====================================================================
    -- Will be enabled once spare parts table is created
    
    -- ====================================================================
    -- ORDER BY: Priority (bulletins first), then relevance score
    -- ====================================================================
    ORDER BY priority ASC, relevance_score DESC, title
    LIMIT p_limit;
    
END;
$$ LANGUAGE plpgsql STABLE;

-- Grant access
GRANT EXECUTE ON FUNCTION search_error_code_resources TO service_role, authenticated;

-- Add comprehensive comment
COMMENT ON FUNCTION search_error_code_resources IS 
'Unified multi-resource search for error codes. Returns error code entries, chunks, videos, links, and parts ranked by priority. Used by N8N Search Error Code tool.';

-- ======================================================================
-- Simplified Version: Search by Error Code only (no filters)
-- ======================================================================

CREATE OR REPLACE FUNCTION search_error_code(
    p_error_code VARCHAR(20)
)
RETURNS TABLE (
    resource_type TEXT,
    title TEXT,
    description TEXT,
    url TEXT,
    page_number INTEGER,
    priority INTEGER,
    document_type TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.resource_type,
        r.title,
        r.description,
        r.url,
        r.page_number,
        r.priority,
        r.document_type,
        r.metadata
    FROM search_error_code_resources(p_error_code, NULL, NULL, 20) r;
END;
$$ LANGUAGE plpgsql STABLE;

GRANT EXECUTE ON FUNCTION search_error_code TO service_role, authenticated;

COMMENT ON FUNCTION search_error_code IS 
'Simplified version of search_error_code_resources - just provide error code';

-- ======================================================================
-- Helper Function: Get Error Code Summary
-- ======================================================================

CREATE OR REPLACE FUNCTION get_error_code_summary(
    p_error_code VARCHAR(20),
    p_manufacturer_id UUID DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'error_code', p_error_code,
        'total_resources', COUNT(*),
        'by_type', jsonb_object_agg(
            resource_type,
            count
        ),
        'highest_priority', MIN(priority),
        'has_bulletin', BOOL_OR(document_type = 'service_bulletin')
    ) INTO v_result
    FROM (
        SELECT 
            resource_type,
            document_type,
            priority,
            COUNT(*) as count
        FROM search_error_code_resources(p_error_code, p_manufacturer_id, NULL, 100)
        GROUP BY resource_type, document_type, priority
    ) subq;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql STABLE;

GRANT EXECUTE ON FUNCTION get_error_code_summary TO service_role, authenticated;

COMMENT ON FUNCTION get_error_code_summary IS 
'Get summary statistics for error code resources';

-- ======================================================================
-- Verification
-- ======================================================================

-- Test the function with a known error code
DO $$
DECLARE
    test_error_code VARCHAR(20);
    result_count INTEGER;
    i RECORD;
BEGIN
    -- Try to find a real error code from the database
    SELECT error_code INTO test_error_code 
    FROM krai_intelligence.error_codes 
    LIMIT 1;
    
    IF test_error_code IS NOT NULL THEN
        -- Count results
        SELECT COUNT(*) INTO result_count
        FROM search_error_code(test_error_code);
        
        RAISE NOTICE '✅ Unified search function works!';
        RAISE NOTICE '   Test error code: %', test_error_code;
        RAISE NOTICE '   Results found: %', result_count;
        
        -- Show sample results
        RAISE NOTICE '';
        RAISE NOTICE '📋 Sample results:';
        
        FOR i IN (
            SELECT 
                resource_type,
                title,
                priority,
                document_type
            FROM search_error_code(test_error_code)
            LIMIT 5
        ) LOOP
            RAISE NOTICE '   [Priority %] % - % (Type: %)', 
                i.priority, i.resource_type, LEFT(i.title, 60), i.document_type;
        END LOOP;
    ELSE
        RAISE NOTICE '⚠️  No error codes in database yet (function still created successfully)';
    END IF;
END $$;
