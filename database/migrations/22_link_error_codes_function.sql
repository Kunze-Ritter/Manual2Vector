-- ======================================================================
-- Migration 22: Link Error Codes to Chunks & Images
-- ======================================================================
-- Description: Create function to link error codes to their chunks and images
-- Date: 2025-10-05
-- Purpose: Enable N8N Agent to show images + context when user asks about error codes
-- ======================================================================

-- Function to link error codes for a document
CREATE OR REPLACE FUNCTION link_error_codes_to_chunks_and_images(p_document_id UUID)
RETURNS TABLE(
    linked_to_chunks INTEGER,
    linked_to_images INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    chunk_count INTEGER;
    image_count INTEGER;
BEGIN
    -- Update chunk_id for error codes
    -- Links error code to chunk where page_number falls within chunk's page range
    UPDATE krai_intelligence.error_codes ec
    SET chunk_id = (
        SELECT c.id 
        FROM krai_intelligence.chunks c
        WHERE c.document_id = ec.document_id
          AND c.page_start <= ec.page_number 
          AND c.page_end >= ec.page_number
        LIMIT 1
    )
    WHERE ec.chunk_id IS NULL 
      AND ec.document_id = p_document_id
      AND ec.page_number IS NOT NULL;
    
    GET DIAGNOSTICS chunk_count = ROW_COUNT;
    
    -- Update image_id for error codes
    -- Links error code to first image on same page (error screenshot/diagram)
    UPDATE krai_intelligence.error_codes ec
    SET image_id = (
        SELECT i.id 
        FROM krai_content.images i
        WHERE i.document_id = ec.document_id
          AND i.page_number = ec.page_number
        ORDER BY i.image_index
        LIMIT 1
    )
    WHERE ec.image_id IS NULL 
      AND ec.document_id = p_document_id
      AND ec.page_number IS NOT NULL;
    
    GET DIAGNOSTICS image_count = ROW_COUNT;
    
    RETURN QUERY SELECT chunk_count, image_count;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION link_error_codes_to_chunks_and_images TO service_role;

-- Add helpful comments
COMMENT ON FUNCTION link_error_codes_to_chunks_and_images IS 
'Links error codes to their chunks (for text context) and images (for screenshots/diagrams). Used by N8N Agent to show complete error code information with visual aids.';

-- ======================================================================
-- Batch Update: Link ALL existing error codes
-- ======================================================================

-- Link all existing error codes (one-time batch operation)
DO $$
DECLARE
    doc_record RECORD;
    total_chunks INTEGER := 0;
    total_images INTEGER := 0;
    result_record RECORD;
BEGIN
    -- Loop through all documents that have error codes
    FOR doc_record IN 
        SELECT DISTINCT document_id 
        FROM krai_intelligence.error_codes
        WHERE (chunk_id IS NULL OR image_id IS NULL)
          AND page_number IS NOT NULL
    LOOP
        -- Link error codes for this document
        SELECT * INTO result_record
        FROM link_error_codes_to_chunks_and_images(doc_record.document_id);
        
        total_chunks := total_chunks + result_record.linked_to_chunks;
        total_images := total_images + result_record.linked_to_images;
    END LOOP;
    
    RAISE NOTICE '✅ Linked % error codes to chunks', total_chunks;
    RAISE NOTICE '✅ Linked % error codes to images', total_images;
END $$;

-- ======================================================================
-- Verification
-- ======================================================================

-- Show linking statistics
SELECT 
    COUNT(*) as total_error_codes,
    COUNT(chunk_id) as linked_to_chunks,
    COUNT(image_id) as linked_to_images,
    ROUND(100.0 * COUNT(chunk_id) / COUNT(*), 2) as chunk_link_percentage,
    ROUND(100.0 * COUNT(image_id) / COUNT(*), 2) as image_link_percentage
FROM krai_intelligence.error_codes;

-- Expected output:
-- | total | linked_chunks | linked_images | chunk_% | image_% |
-- |-------|---------------|---------------|---------|---------|
-- | 39    | 39            | ~30           | 100%    | ~80%    |
