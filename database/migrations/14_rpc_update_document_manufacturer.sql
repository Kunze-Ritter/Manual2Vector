-- =====================================================
-- RPC FUNCTION: UPDATE DOCUMENT MANUFACTURER
-- =====================================================
-- Bypasses PostgREST schema cache issues
-- Similar to insert_error_code RPC function
-- IMPORTANT: Must be in 'public' schema for PostgREST to find it!

CREATE OR REPLACE FUNCTION public.update_document_manufacturer(
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
GRANT EXECUTE ON FUNCTION public.update_document_manufacturer TO authenticated;
GRANT EXECUTE ON FUNCTION public.update_document_manufacturer TO service_role;
GRANT EXECUTE ON FUNCTION public.update_document_manufacturer TO anon;

-- Add comment
COMMENT ON FUNCTION public.update_document_manufacturer IS 
'Updates document manufacturer information. Bypasses PostgREST schema cache issues.';

-- =====================================================
-- RPC FUNCTION: UPSERT DOCUMENT
-- =====================================================
-- Bypasses PostgREST schema cache for document insert/update
-- Handles manufacturer_id field that PostgREST can't see

CREATE OR REPLACE FUNCTION public.upsert_document(
    p_document_id UUID,
    p_filename TEXT,
    p_original_filename TEXT,
    p_file_size BIGINT,
    p_storage_path TEXT,
    p_document_type TEXT,
    p_language TEXT,
    p_page_count INTEGER,
    p_word_count INTEGER,
    p_character_count INTEGER,
    p_processing_status TEXT,
    p_processing_results JSONB,
    p_manufacturer TEXT,
    p_manufacturer_id UUID
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Insert or update document
    INSERT INTO krai_core.documents (
        id,
        filename,
        original_filename,
        file_size,
        storage_path,
        document_type,
        language,
        page_count,
        word_count,
        character_count,
        processing_status,
        processing_results,
        manufacturer,
        manufacturer_id,
        created_at,
        updated_at
    ) VALUES (
        p_document_id,
        p_filename,
        p_original_filename,
        p_file_size,
        p_storage_path,
        p_document_type,
        p_language,
        p_page_count,
        p_word_count,
        p_character_count,
        p_processing_status,
        p_processing_results,
        p_manufacturer,
        p_manufacturer_id,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        filename = EXCLUDED.filename,
        original_filename = EXCLUDED.original_filename,
        file_size = EXCLUDED.file_size,
        storage_path = EXCLUDED.storage_path,
        document_type = EXCLUDED.document_type,
        language = EXCLUDED.language,
        page_count = EXCLUDED.page_count,
        word_count = EXCLUDED.word_count,
        character_count = EXCLUDED.character_count,
        processing_status = EXCLUDED.processing_status,
        processing_results = EXCLUDED.processing_results,
        manufacturer = EXCLUDED.manufacturer,
        manufacturer_id = EXCLUDED.manufacturer_id,
        updated_at = NOW();
    
    RETURN p_document_id;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.upsert_document TO authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_document TO service_role;
GRANT EXECUTE ON FUNCTION public.upsert_document TO anon;

-- Add comment
COMMENT ON FUNCTION public.upsert_document IS 
'Inserts or updates a document. Bypasses PostgREST schema cache issues with manufacturer_id.';
