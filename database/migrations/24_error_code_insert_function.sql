-- ======================================================================
-- Migration 24: Error Code INSERT Function (Bypass PostgREST Cache!)
-- ======================================================================
-- Description: Create PostgreSQL function to insert error codes
-- Date: 2025-10-05
-- Reason: PostgREST schema cache is BROKEN - RPC functions bypass it!
-- ======================================================================

-- Function to insert a single error code
CREATE OR REPLACE FUNCTION insert_error_code(
    p_document_id UUID,
    p_manufacturer_id UUID,
    p_error_code VARCHAR(20),
    p_error_description TEXT DEFAULT NULL,
    p_solution_text TEXT DEFAULT NULL,
    p_confidence_score DECIMAL DEFAULT 0.8,
    p_page_number INTEGER DEFAULT NULL,
    p_severity_level VARCHAR(20) DEFAULT 'medium',
    p_extraction_method VARCHAR(50) DEFAULT 'regex_pattern',
    p_requires_technician BOOLEAN DEFAULT FALSE,
    p_requires_parts BOOLEAN DEFAULT FALSE,
    p_context_text TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO krai_intelligence.error_codes (
        document_id,
        manufacturer_id,
        error_code,
        error_description,
        solution_text,
        confidence_score,
        page_number,
        severity_level,
        extraction_method,
        requires_technician,
        requires_parts,
        context_text,
        metadata
    ) VALUES (
        p_document_id,
        p_manufacturer_id,
        p_error_code,
        p_error_description,
        p_solution_text,
        p_confidence_score,
        p_page_number,
        p_severity_level,
        p_extraction_method,
        p_requires_technician,
        p_requires_parts,
        p_context_text,
        p_metadata
    )
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION insert_error_code TO service_role;

-- Add helpful comment
COMMENT ON FUNCTION insert_error_code IS 
'Insert error code bypassing PostgREST schema cache. Use this instead of direct INSERT via PostgREST API.';

-- ======================================================================
-- Test the function
-- ======================================================================

-- Test insert (will rollback)
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- Get a real document_id for testing
    SELECT id INTO test_id FROM krai_core.documents LIMIT 1;
    
    IF test_id IS NOT NULL THEN
        -- Test the function
        SELECT insert_error_code(
            p_document_id := test_id,
            p_manufacturer_id := NULL,
            p_error_code := 'TEST-001',
            p_error_description := 'Test error code',
            p_context_text := 'Test context',
            p_metadata := '{"test": true}'::jsonb
        ) INTO test_id;
        
        RAISE NOTICE '✅ Function works! Test error code ID: %', test_id;
        
        -- Rollback test data
        DELETE FROM krai_intelligence.error_codes WHERE id = test_id;
        RAISE NOTICE '✅ Test data cleaned up';
    ELSE
        RAISE NOTICE '⚠️  No documents found for testing';
    END IF;
END $$;
