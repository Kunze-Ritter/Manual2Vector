-- Migration 109: Update upsert_document RPC function - Remove p_original_filename parameter
-- Date: 2025-10-22
-- Reason: original_filename column was removed in migration 105, but RPC function still expects it

-- Drop ALL versions of the function (there might be multiple)
DROP FUNCTION IF EXISTS public.upsert_document CASCADE;

-- Create new function WITHOUT p_original_filename
CREATE OR REPLACE FUNCTION public.upsert_document(
    p_document_id UUID,
    p_filename TEXT,
    p_file_size BIGINT,
    p_storage_path TEXT,
    p_document_type VARCHAR(50),
    p_language VARCHAR(10),
    p_page_count INTEGER,
    p_word_count INTEGER,
    p_character_count INTEGER,
    p_processing_status VARCHAR(50),
    p_processing_results JSONB,
    p_manufacturer VARCHAR(100),
    p_manufacturer_id UUID
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- Upsert document
    INSERT INTO krai_core.documents (
        id,
        filename,
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
        manufacturer_id
    ) VALUES (
        p_document_id,
        p_filename,
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
        p_manufacturer_id
    )
    ON CONFLICT (id) DO UPDATE SET
        filename = EXCLUDED.filename,
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
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.upsert_document TO anon, authenticated, service_role;

COMMENT ON FUNCTION public.upsert_document IS 'Upsert document without original_filename (removed in migration 105)';
