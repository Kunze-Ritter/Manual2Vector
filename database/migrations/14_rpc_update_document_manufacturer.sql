-- =====================================================
-- RPC FUNCTION: UPDATE DOCUMENT MANUFACTURER
-- =====================================================
-- Bypasses PostgREST schema cache issues
-- Similar to insert_error_code RPC function

CREATE OR REPLACE FUNCTION krai_core.update_document_manufacturer(
    p_document_id UUID,
    p_manufacturer TEXT,
    p_manufacturer_id UUID
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Update document with manufacturer info
    UPDATE krai_core.documents
    SET 
        manufacturer = p_manufacturer,
        manufacturer_id = p_manufacturer_id,
        updated_at = NOW()
    WHERE id = p_document_id;
    
    -- Log if no rows were updated (document doesn't exist)
    IF NOT FOUND THEN
        RAISE NOTICE 'Document % not found', p_document_id;
    END IF;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION krai_core.update_document_manufacturer TO authenticated;
GRANT EXECUTE ON FUNCTION krai_core.update_document_manufacturer TO service_role;

-- Add comment
COMMENT ON FUNCTION krai_core.update_document_manufacturer IS 
'Updates document manufacturer information. Bypasses PostgREST schema cache issues.';
