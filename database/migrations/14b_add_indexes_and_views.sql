-- Migration 14b: Add Indexes, Comments and Views
-- PART 2 of 2: Optimize and expose documents table
-- NOTE: Run this AFTER 14a_drop_and_create_documents_table.sql

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_documents_file_hash 
ON krai_core.documents(file_hash);

CREATE INDEX IF NOT EXISTS idx_documents_manufacturer 
ON krai_core.documents(manufacturer);

CREATE INDEX IF NOT EXISTS idx_documents_document_type 
ON krai_core.documents(document_type);

CREATE INDEX IF NOT EXISTS idx_documents_processing_status 
ON krai_core.documents(processing_status);

CREATE INDEX IF NOT EXISTS idx_documents_created_at 
ON krai_core.documents(created_at);

-- GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_documents_extracted_metadata 
ON krai_core.documents USING GIN (extracted_metadata);

CREATE INDEX IF NOT EXISTS idx_documents_processing_results 
ON krai_core.documents USING GIN (processing_results);

CREATE INDEX IF NOT EXISTS idx_documents_stage_status 
ON krai_core.documents USING GIN (stage_status);

-- GIN index for models array
CREATE INDEX IF NOT EXISTS idx_documents_models 
ON krai_core.documents USING GIN (models);

-- ============================================================================
-- Add Comments for Documentation
-- ============================================================================

COMMENT ON TABLE krai_core.documents 
IS 'Documents table - contains all uploaded documents with processing status';

COMMENT ON COLUMN krai_core.documents.manufacturer 
IS 'Manufacturer name (text) - auto-detected during processing';

COMMENT ON COLUMN krai_core.documents.models 
IS 'Array of model numbers extracted from document';

COMMENT ON COLUMN krai_core.documents.processing_results 
IS 'Complete processing results from pipeline (JSONB)';

COMMENT ON COLUMN krai_core.documents.processing_error 
IS 'Error message if processing failed';

COMMENT ON COLUMN krai_core.documents.processing_status 
IS 'Processing status: pending, processing, completed, failed';

COMMENT ON COLUMN krai_core.documents.stage_status 
IS 'Per-stage processing status tracking (JSONB)';

COMMENT ON COLUMN krai_core.documents.version 
IS 'Document version extracted from content';

-- ============================================================================
-- Create public.documents VIEW (for Supabase PostgREST compatibility)
-- ============================================================================

CREATE OR REPLACE VIEW public.documents AS
SELECT * FROM krai_core.documents;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO service_role;

-- ============================================================================
-- Enable INSERT/UPDATE/DELETE on public.documents view
-- ============================================================================

CREATE OR REPLACE RULE documents_insert AS
ON INSERT TO public.documents DO INSTEAD
INSERT INTO krai_core.documents (
    id, filename, original_filename, file_size, file_hash, storage_path,
    document_type, language, version, publish_date, page_count, word_count,
    character_count, content_text, content_summary, extracted_metadata,
    processing_status, processing_results, processing_error, stage_status,
    confidence_score, manual_review_required, manual_review_completed, 
    manual_review_notes, ocr_confidence, manufacturer, series, models, 
    created_at, updated_at
) VALUES (
    COALESCE(NEW.id, uuid_generate_v4()),
    NEW.filename, NEW.original_filename, NEW.file_size, NEW.file_hash, NEW.storage_path,
    NEW.document_type, NEW.language, NEW.version, NEW.publish_date, NEW.page_count, NEW.word_count,
    NEW.character_count, NEW.content_text, NEW.content_summary, NEW.extracted_metadata,
    NEW.processing_status, NEW.processing_results, NEW.processing_error, NEW.stage_status,
    NEW.confidence_score, NEW.manual_review_required, NEW.manual_review_completed,
    NEW.manual_review_notes, NEW.ocr_confidence, NEW.manufacturer, NEW.series, NEW.models,
    COALESCE(NEW.created_at, NOW()), COALESCE(NEW.updated_at, NOW())
) RETURNING *;

CREATE OR REPLACE RULE documents_update AS
ON UPDATE TO public.documents DO INSTEAD
UPDATE krai_core.documents SET 
    filename = NEW.filename,
    file_size = NEW.file_size,
    file_hash = NEW.file_hash,
    storage_path = NEW.storage_path,
    document_type = NEW.document_type,
    version = NEW.version,
    manufacturer = NEW.manufacturer,
    models = NEW.models,
    series = NEW.series,
    page_count = NEW.page_count,
    processing_status = NEW.processing_status,
    processing_results = NEW.processing_results,
    processing_error = NEW.processing_error,
    stage_status = NEW.stage_status,
    extracted_metadata = NEW.extracted_metadata,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE documents_delete AS
ON DELETE TO public.documents DO INSTEAD
DELETE FROM krai_core.documents WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Done! Verification queries:
-- ============================================================================

-- Check all columns exist:
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns 
-- WHERE table_schema = 'krai_core' 
--   AND table_name = 'documents'
-- ORDER BY ordinal_position;

-- Check if stage_status column exists:
-- SELECT column_name, data_type
-- FROM information_schema.columns 
-- WHERE table_schema = 'krai_core' 
--   AND table_name = 'documents'
--   AND column_name = 'stage_status';

-- Check public view:
-- SELECT * FROM public.documents LIMIT 1;
