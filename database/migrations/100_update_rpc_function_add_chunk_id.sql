-- Update insert_error_code RPC Function to support chunk_id
-- Run this in Supabase SQL Editor

-- Drop ALL old versions of insert_error_code function
-- (There might be multiple versions with different signatures)
DROP FUNCTION IF EXISTS insert_error_code CASCADE;

-- Create new function with chunk_id parameter
CREATE OR REPLACE FUNCTION insert_error_code(
    p_document_id UUID,
    p_manufacturer_id UUID,
    p_error_code TEXT,
    p_error_description TEXT,
    p_solution_text TEXT DEFAULT NULL,
    p_confidence_score NUMERIC DEFAULT 0.8,
    p_page_number INTEGER DEFAULT NULL,
    p_severity_level TEXT DEFAULT 'medium',
    p_extraction_method TEXT DEFAULT 'regex_pattern',
    p_requires_technician BOOLEAN DEFAULT FALSE,
    p_requires_parts BOOLEAN DEFAULT FALSE,
    p_context_text TEXT DEFAULT NULL,
    p_chunk_id UUID DEFAULT NULL,  -- ← NEU! For image linking
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_error_id UUID;
BEGIN
    -- Check if error code already exists
    SELECT id INTO v_error_id
    FROM krai_intelligence.error_codes
    WHERE document_id = p_document_id
    AND error_code = p_error_code;
    
    IF v_error_id IS NOT NULL THEN
        -- Update existing error code
        UPDATE krai_intelligence.error_codes
        SET
            error_description = p_error_description,
            solution_text = p_solution_text,
            confidence_score = p_confidence_score,
            page_number = p_page_number,
            severity_level = p_severity_level,
            extraction_method = p_extraction_method,
            requires_technician = p_requires_technician,
            requires_parts = p_requires_parts,
            context_text = p_context_text,
            chunk_id = p_chunk_id,  -- ← NEU!
            metadata = p_metadata
        WHERE id = v_error_id;
    ELSE
        -- Insert new error code with chunk_id
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
            chunk_id,  -- ← NEU!
            metadata,
            created_at
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
            p_chunk_id,  -- ← NEU!
            p_metadata,
            NOW()
        )
        RETURNING id INTO v_error_id;
    END IF;
    
    RETURN v_error_id;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION insert_error_code TO authenticated;
GRANT EXECUTE ON FUNCTION insert_error_code TO service_role;

-- Test the function with real manufacturer and document
DO $$
DECLARE
    v_test_mfr_id UUID;
    v_test_doc_id UUID;
    v_test_error_id UUID;
BEGIN
    -- Get a real manufacturer
    SELECT id INTO v_test_mfr_id 
    FROM krai_core.manufacturers 
    LIMIT 1;
    
    -- Get a real document
    SELECT id INTO v_test_doc_id 
    FROM krai_core.documents 
    LIMIT 1;
    
    -- Test the function
    IF v_test_mfr_id IS NOT NULL AND v_test_doc_id IS NOT NULL THEN
        v_test_error_id := insert_error_code(
            p_document_id := v_test_doc_id,
            p_manufacturer_id := v_test_mfr_id,
            p_error_code := 'TEST.MIGRATION.100',
            p_error_description := 'Test error code - function accepts chunk_id parameter',
            p_chunk_id := NULL  -- NULL is valid, will be set during real processing
        );
        
        RAISE NOTICE '✅ Function test successful! Error ID: %', v_test_error_id;
        
        -- Clean up test
        DELETE FROM krai_intelligence.error_codes WHERE id = v_test_error_id;
        
        RAISE NOTICE '✅ Test cleaned up successfully';
    ELSE
        RAISE NOTICE '⚠️ No manufacturers or documents found for testing, but function was created successfully';
    END IF;
END $$;

-- Success message
SELECT '✅ RPC Function updated successfully! chunk_id parameter added.' as status;
