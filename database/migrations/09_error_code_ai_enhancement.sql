-- ===========================================
-- ERROR CODE AI ENHANCEMENT
-- ===========================================
-- Enhances error_codes table with AI extraction capabilities
-- Adds screenshot support, context, and confidence scoring

-- Add AI extraction fields
ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS image_id UUID REFERENCES krai_content.images(id) ON DELETE SET NULL;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS context_text TEXT;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS ai_extracted BOOLEAN DEFAULT false;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT false;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255);

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_error_codes_manufacturer ON krai_intelligence.error_codes(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_error_codes_severity ON krai_intelligence.error_codes(severity_level);
CREATE INDEX IF NOT EXISTS idx_error_codes_confidence ON krai_intelligence.error_codes(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_error_codes_verified ON krai_intelligence.error_codes(verified, ai_extracted);
CREATE INDEX IF NOT EXISTS idx_error_codes_image ON krai_intelligence.error_codes(image_id) WHERE image_id IS NOT NULL;

-- Full-text search index on error_code and description
CREATE INDEX IF NOT EXISTS idx_error_codes_search ON krai_intelligence.error_codes 
USING gin(to_tsvector('english', error_code || ' ' || COALESCE(error_description, '') || ' ' || COALESCE(solution_text, '')));

-- Comments
COMMENT ON COLUMN krai_intelligence.error_codes.image_id IS 'Reference to screenshot/image where error code was found';
COMMENT ON COLUMN krai_intelligence.error_codes.context_text IS 'Surrounding text context where error code was found';
COMMENT ON COLUMN krai_intelligence.error_codes.metadata IS 'AI extraction metadata (GPT model, temperature, tokens used, etc.)';
COMMENT ON COLUMN krai_intelligence.error_codes.ai_extracted IS 'True if extracted by AI (GPT-4 Vision), false if pattern-matched';
COMMENT ON COLUMN krai_intelligence.error_codes.verified IS 'True if manually verified by human';

-- Helper function to search error codes
CREATE OR REPLACE FUNCTION krai_intelligence.search_error_codes(
    p_search_query TEXT,
    p_manufacturer_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    error_code VARCHAR,
    error_description TEXT,
    solution_text TEXT,
    severity_level VARCHAR,
    confidence_score DECIMAL,
    document_id UUID,
    manufacturer_id UUID,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ec.id,
        ec.error_code,
        ec.error_description,
        ec.solution_text,
        ec.severity_level,
        ec.confidence_score,
        ec.document_id,
        ec.manufacturer_id,
        ts_rank(
            to_tsvector('english', ec.error_code || ' ' || COALESCE(ec.error_description, '') || ' ' || COALESCE(ec.solution_text, '')),
            plainto_tsquery('english', p_search_query)
        ) as rank
    FROM krai_intelligence.error_codes ec
    WHERE 
        (p_manufacturer_id IS NULL OR ec.manufacturer_id = p_manufacturer_id)
        AND to_tsvector('english', ec.error_code || ' ' || COALESCE(ec.error_description, '') || ' ' || COALESCE(ec.solution_text, '')) 
            @@ plainto_tsquery('english', p_search_query)
    ORDER BY rank DESC, ec.confidence_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Helper function to get error code statistics
CREATE OR REPLACE FUNCTION krai_intelligence.get_error_code_statistics()
RETURNS TABLE (
    total_codes BIGINT,
    ai_extracted_codes BIGINT,
    pattern_matched_codes BIGINT,
    verified_codes BIGINT,
    with_solutions BIGINT,
    avg_confidence DECIMAL,
    by_severity JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_codes,
        COUNT(*) FILTER (WHERE ai_extracted = true)::BIGINT as ai_extracted_codes,
        COUNT(*) FILTER (WHERE ai_extracted = false)::BIGINT as pattern_matched_codes,
        COUNT(*) FILTER (WHERE verified = true)::BIGINT as verified_codes,
        COUNT(*) FILTER (WHERE solution_text IS NOT NULL AND LENGTH(solution_text) > 0)::BIGINT as with_solutions,
        AVG(confidence_score) as avg_confidence,
        jsonb_object_agg(
            severity_level, 
            count
        ) as by_severity
    FROM (
        SELECT severity_level, COUNT(*)::INTEGER as count
        FROM krai_intelligence.error_codes
        GROUP BY severity_level
    ) severity_counts;
END;
$$ LANGUAGE plpgsql;

-- Helper function to find duplicate error codes
CREATE OR REPLACE FUNCTION krai_intelligence.find_duplicate_error_codes()
RETURNS TABLE (
    error_code VARCHAR,
    manufacturer_id UUID,
    count BIGINT,
    document_ids UUID[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ec.error_code,
        ec.manufacturer_id,
        COUNT(*)::BIGINT as count,
        ARRAY_AGG(DISTINCT ec.document_id) as document_ids
    FROM krai_intelligence.error_codes ec
    GROUP BY ec.error_code, ec.manufacturer_id
    HAVING COUNT(*) > 1
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION krai_intelligence.search_error_codes TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION krai_intelligence.get_error_code_statistics TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION krai_intelligence.find_duplicate_error_codes TO service_role, authenticated;
