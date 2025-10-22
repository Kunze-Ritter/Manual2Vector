-- Cleanup unused columns from documents table
-- Remove content_text, content_summary, original_filename

-- Step 1: Drop view that depends on these columns
DROP VIEW IF EXISTS public.vw_documents CASCADE;

-- Step 2: Remove unused columns
ALTER TABLE krai_core.documents 
DROP COLUMN IF EXISTS content_text,
DROP COLUMN IF EXISTS content_summary,
DROP COLUMN IF EXISTS original_filename;

-- Step 3: Recreate view without the removed columns
CREATE OR REPLACE VIEW public.vw_documents AS
SELECT 
    id,
    filename,
    file_size,
    file_hash,
    storage_path,
    document_type,
    language,
    version,
    publish_date,
    page_count,
    word_count,
    character_count,
    extracted_metadata,
    processing_status,
    processing_results,
    processing_error,
    stage_status,
    confidence_score,
    ocr_confidence,
    manual_review_required,
    manual_review_completed,
    manual_review_notes,
    manufacturer,
    manufacturer_id,
    series,
    models,
    priority_level,
    created_at,
    updated_at
FROM krai_core.documents;

-- Grant permissions
GRANT SELECT ON public.vw_documents TO anon, authenticated;

-- Add comments
COMMENT ON VIEW public.vw_documents IS 
'Documents view - cleaned up (content_text, content_summary, original_filename removed)';

COMMENT ON TABLE krai_core.documents IS 
'Core documents table - cleaned up unused columns';

-- Success message
SELECT '✅ Cleaned up unused columns and recreated vw_documents!' as status;
