-- ============================================================================
-- Migration 76: Agent Enhancements - Analytics & Context
-- ============================================================================
-- Purpose: Add analytics, session management, and enhanced context features
-- Date: 2025-10-11
-- Author: KRAI Development Team
-- ============================================================================

-- ============================================================================
-- 1. Tool Usage Analytics
-- ============================================================================
CREATE TABLE IF NOT EXISTS krai_analytics.tool_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    query_params JSONB,
    results_count INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON krai_analytics.tool_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_tool ON krai_analytics.tool_usage(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_usage_created ON krai_analytics.tool_usage(created_at DESC);

COMMENT ON TABLE krai_analytics.tool_usage IS 
'Tracks which tools are used, how often, and their performance';

-- ============================================================================
-- 2. User Feedback
-- ============================================================================
CREATE TABLE IF NOT EXISTS krai_analytics.feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    message_id TEXT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_type TEXT CHECK (feedback_type IN ('helpful', 'not_helpful', 'incorrect', 'incomplete')),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_session ON krai_analytics.feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON krai_analytics.feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON krai_analytics.feedback(created_at DESC);

COMMENT ON TABLE krai_analytics.feedback IS 
'User feedback on agent responses for continuous improvement';

-- ============================================================================
-- 3. Session Context (Enhanced Memory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS krai_intelligence.session_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    context_type TEXT NOT NULL, -- 'manufacturer', 'model', 'error_code', 'part_number'
    context_value TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    first_mentioned_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    use_count INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_session_context_session ON krai_intelligence.session_context(session_id);
CREATE INDEX IF NOT EXISTS idx_session_context_type ON krai_intelligence.session_context(context_type);

COMMENT ON TABLE krai_intelligence.session_context IS 
'Stores extracted context (manufacturer, model, etc.) from conversations for better follow-up responses';

-- ============================================================================
-- 4. Function: Get Session Context
-- ============================================================================
CREATE OR REPLACE FUNCTION krai_intelligence.get_session_context(
    p_session_id TEXT
)
RETURNS TABLE (
    context_type TEXT,
    context_value TEXT,
    confidence FLOAT,
    use_count INTEGER,
    last_used_at TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sc.context_type,
        sc.context_value,
        sc.confidence,
        sc.use_count,
        sc.last_used_at
    FROM krai_intelligence.session_context sc
    WHERE sc.session_id = p_session_id
        AND sc.last_used_at > NOW() - INTERVAL '1 hour' -- Only recent context
    ORDER BY sc.use_count DESC, sc.last_used_at DESC;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.get_session_context IS 
'Retrieve current session context (manufacturer, model, etc.) for context-aware responses';

-- ============================================================================
-- 5. Function: Update Session Context
-- ============================================================================
CREATE OR REPLACE FUNCTION krai_intelligence.update_session_context(
    p_session_id TEXT,
    p_context_type TEXT,
    p_context_value TEXT,
    p_confidence FLOAT DEFAULT 1.0
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Insert or update context
    INSERT INTO krai_intelligence.session_context (
        session_id,
        context_type,
        context_value,
        confidence,
        first_mentioned_at,
        last_used_at,
        use_count
    )
    VALUES (
        p_session_id,
        p_context_type,
        p_context_value,
        p_confidence,
        NOW(),
        NOW(),
        1
    )
    ON CONFLICT (session_id, context_type, context_value) 
    DO UPDATE SET
        last_used_at = NOW(),
        use_count = krai_intelligence.session_context.use_count + 1,
        confidence = GREATEST(krai_intelligence.session_context.confidence, p_confidence);
END;
$$;

-- Add unique constraint for upsert
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_context_unique 
ON krai_intelligence.session_context(session_id, context_type, context_value);

COMMENT ON FUNCTION krai_intelligence.update_session_context IS 
'Update or insert session context (called when agent extracts manufacturer, model, etc.)';

-- ============================================================================
-- 6. Function: Get Popular Error Codes
-- ============================================================================
CREATE OR REPLACE FUNCTION krai_intelligence.get_popular_error_codes(
    p_manufacturer TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    error_code TEXT,
    description TEXT,
    occurrence_count BIGINT,
    affected_models TEXT[]
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ec.error_code::TEXT,
        ec.description::TEXT,
        COUNT(DISTINCT ec.id) as occurrence_count,
        ARRAY_AGG(DISTINCT p.model_number) as affected_models
    FROM krai_intelligence.error_codes ec
    LEFT JOIN krai_core.products p ON ec.product_id = p.id
    LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
    WHERE (p_manufacturer IS NULL OR m.name ILIKE '%' || p_manufacturer || '%')
    GROUP BY ec.error_code, ec.description
    ORDER BY occurrence_count DESC
    LIMIT p_limit;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.get_popular_error_codes IS 
'Get most common error codes for a manufacturer (useful for proactive support)';

-- ============================================================================
-- 7. Function: Get Frequently Replaced Parts
-- ============================================================================
CREATE OR REPLACE FUNCTION krai_intelligence.get_frequent_parts(
    p_manufacturer TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    part_number TEXT,
    part_name TEXT,
    occurrence_count BIGINT,
    compatible_models TEXT[]
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pt.part_number::TEXT,
        pt.part_name::TEXT,
        COUNT(DISTINCT pt.id) as occurrence_count,
        ARRAY_AGG(DISTINCT p.model_number) as compatible_models
    FROM krai_parts.parts_catalog pt
    LEFT JOIN krai_core.manufacturers m ON pt.manufacturer_id = m.id
    LEFT JOIN krai_core.documents d ON pt.document_id = d.id
    LEFT JOIN krai_core.document_products dp ON d.id = dp.document_id
    LEFT JOIN krai_core.products p ON dp.product_id = p.id
    WHERE (p_manufacturer IS NULL OR m.name ILIKE '%' || p_manufacturer || '%')
        AND (p_model IS NULL OR p.model_number ILIKE '%' || p_model || '%')
    GROUP BY pt.part_number, pt.part_name
    ORDER BY occurrence_count DESC
    LIMIT p_limit;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.get_frequent_parts IS 
'Get most frequently mentioned parts (useful for inventory management)';

-- ============================================================================
-- 8. Function: Smart Search (combines multiple sources)
-- ============================================================================
CREATE OR REPLACE FUNCTION krai_intelligence.smart_search(
    p_query TEXT,
    p_session_id TEXT DEFAULT NULL
)
RETURNS TABLE (
    result_type TEXT, -- 'error_code', 'part', 'product', 'video', 'documentation'
    result_data JSONB,
    relevance_score FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_manufacturer TEXT;
    v_model TEXT;
BEGIN
    -- Get context from session if available
    IF p_session_id IS NOT NULL THEN
        SELECT context_value INTO v_manufacturer
        FROM krai_intelligence.session_context
        WHERE session_id = p_session_id AND context_type = 'manufacturer'
        ORDER BY last_used_at DESC LIMIT 1;
        
        SELECT context_value INTO v_model
        FROM krai_intelligence.session_context
        WHERE session_id = p_session_id AND context_type = 'model'
        ORDER BY last_used_at DESC LIMIT 1;
    END IF;
    
    -- Search error codes
    RETURN QUERY
    SELECT 
        'error_code'::TEXT,
        jsonb_build_object(
            'error_code', ec.error_code,
            'description', ec.description,
            'cause', ec.cause,
            'solution', ec.solution,
            'page_number', ec.page_number,
            'model', p.model_number,
            'manufacturer', m.name
        ),
        0.9::FLOAT as relevance_score
    FROM krai_intelligence.error_codes ec
    LEFT JOIN krai_core.products p ON ec.product_id = p.id
    LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
    WHERE ec.error_code ILIKE '%' || p_query || '%'
        OR ec.description ILIKE '%' || p_query || '%'
    LIMIT 3;
    
    -- Search parts
    RETURN QUERY
    SELECT 
        'part'::TEXT,
        jsonb_build_object(
            'part_number', pt.part_number,
            'part_name', pt.part_name,
            'description', pt.description,
            'page_number', pt.page_number,
            'model', p.model_number,
            'manufacturer', m.name
        ),
        0.8::FLOAT as relevance_score
    FROM krai_parts.parts_catalog pt
    LEFT JOIN krai_core.manufacturers m ON pt.manufacturer_id = m.id
    LEFT JOIN krai_core.documents d ON pt.document_id = d.id
    LEFT JOIN krai_core.document_products dp ON d.id = dp.document_id
    LEFT JOIN krai_core.products p ON dp.product_id = p.id
    WHERE pt.part_name ILIKE '%' || p_query || '%'
        OR pt.part_number ILIKE '%' || p_query || '%'
    LIMIT 3;
    
    -- Search products
    RETURN QUERY
    SELECT 
        'product'::TEXT,
        jsonb_build_object(
            'model_number', p.model_number,
            'manufacturer', m.name,
            'series', ps.series_name,
            'product_type', p.product_type
        ),
        0.7::FLOAT as relevance_score
    FROM krai_core.products p
    LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
    LEFT JOIN krai_core.product_series ps ON p.series_id = ps.id
    WHERE p.model_number ILIKE '%' || p_query || '%'
    LIMIT 3;
END;
$$;

COMMENT ON FUNCTION krai_intelligence.smart_search IS 
'Smart search that combines multiple sources and uses session context';

-- ============================================================================
-- 9. View: Agent Performance Dashboard
-- ============================================================================
CREATE OR REPLACE VIEW krai_analytics.agent_performance AS
SELECT 
    DATE(tu.created_at) as date,
    tu.tool_name,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE tu.success = true) as successful_calls,
    COUNT(*) FILTER (WHERE tu.success = false) as failed_calls,
    AVG(tu.response_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY tu.response_time_ms) as p95_response_time_ms,
    AVG(tu.results_count) as avg_results_count
FROM krai_analytics.tool_usage tu
GROUP BY DATE(tu.created_at), tu.tool_name
ORDER BY date DESC, total_calls DESC;

COMMENT ON VIEW krai_analytics.agent_performance IS 
'Daily performance metrics for agent tools';

-- ============================================================================
-- 10. View: User Satisfaction
-- ============================================================================
CREATE OR REPLACE VIEW krai_analytics.user_satisfaction AS
SELECT 
    DATE(f.created_at) as date,
    COUNT(*) as total_feedback,
    AVG(f.rating) as avg_rating,
    COUNT(*) FILTER (WHERE f.rating >= 4) as positive_feedback,
    COUNT(*) FILTER (WHERE f.rating <= 2) as negative_feedback,
    COUNT(*) FILTER (WHERE f.feedback_type = 'helpful') as helpful_count,
    COUNT(*) FILTER (WHERE f.feedback_type = 'not_helpful') as not_helpful_count,
    COUNT(*) FILTER (WHERE f.feedback_type = 'incorrect') as incorrect_count
FROM krai_analytics.feedback f
GROUP BY DATE(f.created_at)
ORDER BY date DESC;

COMMENT ON VIEW krai_analytics.user_satisfaction IS 
'Daily user satisfaction metrics';

-- ============================================================================
-- Grant permissions
-- ============================================================================
GRANT EXECUTE ON FUNCTION krai_intelligence.get_session_context TO authenticated, anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.update_session_context TO authenticated, anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.get_popular_error_codes TO authenticated, anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.get_frequent_parts TO authenticated, anon;
GRANT EXECUTE ON FUNCTION krai_intelligence.smart_search TO authenticated, anon;

GRANT SELECT ON krai_analytics.agent_performance TO authenticated;
GRANT SELECT ON krai_analytics.user_satisfaction TO authenticated;

GRANT INSERT ON krai_analytics.tool_usage TO authenticated, anon;
GRANT INSERT ON krai_analytics.feedback TO authenticated, anon;

-- ============================================================================
-- Test queries (comment out after testing)
-- ============================================================================

-- Test session context
-- SELECT * FROM krai_intelligence.get_session_context('test-session-123');

-- Test popular error codes
-- SELECT * FROM krai_intelligence.get_popular_error_codes('Lexmark', 5);

-- Test frequent parts
-- SELECT * FROM krai_intelligence.get_frequent_parts('Lexmark', 'CX963', 5);

-- Test smart search
-- SELECT * FROM krai_intelligence.smart_search('Fuser Unit', 'test-session-123');

-- Test performance dashboard
-- SELECT * FROM krai_analytics.agent_performance WHERE date >= CURRENT_DATE - INTERVAL '7 days';

-- Test user satisfaction
-- SELECT * FROM krai_analytics.user_satisfaction WHERE date >= CURRENT_DATE - INTERVAL '7 days';
