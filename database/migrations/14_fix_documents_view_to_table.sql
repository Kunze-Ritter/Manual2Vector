-- Migration 14: Convert krai_core.documents from VIEW to TABLE
-- Problem: krai_core.documents ist eine VIEW, daher kann man keine Spalten droppen
-- Solution: View löschen und als echte Tabelle neu erstellen

-- ============================================================================
-- PART 1: Drop existing VIEW
-- ============================================================================

DROP VIEW IF EXISTS krai_core.documents CASCADE;

-- ============================================================================
-- PART 2: Create documents as TABLE (not VIEW)
-- ============================================================================

CREATE TABLE IF NOT EXISTS krai_core.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size BIGINT,
    file_hash VARCHAR(64),
    storage_path TEXT,
    -- storage_url TEXT,  -- REMOVED
    document_type VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    version VARCHAR(50),
    publish_date DATE,
    page_count INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    content_text TEXT,
    content_summary TEXT,
    extracted_metadata JSONB DEFAULT '{}',
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_results JSONB DEFAULT NULL,
    processing_error TEXT DEFAULT NULL,
    confidence_score DECIMAL(3,2),
    manual_review_required BOOLEAN DEFAULT false,
    manual_review_completed BOOLEAN DEFAULT false,
    manual_review_notes TEXT,
    ocr_confidence DECIMAL(3,2),
    manufacturer VARCHAR(100),
    -- manufacturer_id UUID,  -- REMOVED
    -- product_id UUID,       -- REMOVED
    series VARCHAR(100),
    models TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PART 3: Create indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON krai_core.documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_manufacturer ON krai_core.documents(manufacturer);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON krai_core.documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON krai_core.documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON krai_core.documents(created_at);

-- GIN index for JSONB fields
CREATE INDEX IF NOT EXISTS idx_documents_extracted_metadata ON krai_core.documents USING GIN (extracted_metadata);
CREATE INDEX IF NOT EXISTS idx_documents_processing_results ON krai_core.documents USING GIN (processing_results);

-- GIN index for models array
CREATE INDEX IF NOT EXISTS idx_documents_models ON krai_core.documents USING GIN (models);

-- ============================================================================
-- PART 4: Add comments
-- ============================================================================

COMMENT ON TABLE krai_core.documents IS 'Documents table (converted from view) - contains all uploaded documents';
COMMENT ON COLUMN krai_core.documents.manufacturer IS 'Manufacturer name (text) - auto-detected during processing';
COMMENT ON COLUMN krai_core.documents.models IS 'Array of model numbers extracted from document';
COMMENT ON COLUMN krai_core.documents.processing_results IS 'Complete processing results from pipeline (JSONB)';
COMMENT ON COLUMN krai_core.documents.processing_error IS 'Error message if processing failed';
COMMENT ON COLUMN krai_core.documents.processing_status IS 'Processing status: pending, processing, completed, failed';

-- ============================================================================
-- PART 5: Grant permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON krai_core.documents TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_core.documents TO service_role;

-- ============================================================================
-- PART 6: Create public.documents VIEW (for backwards compatibility)
-- ============================================================================

CREATE OR REPLACE VIEW public.documents AS
SELECT * FROM krai_core.documents;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE documents_insert AS
ON INSERT TO public.documents DO INSTEAD
INSERT INTO krai_core.documents (
    id, filename, original_filename, file_size, file_hash, storage_path,
    document_type, language, version, publish_date, page_count, word_count,
    character_count, content_text, content_summary, extracted_metadata,
    processing_status, processing_results, processing_error, confidence_score,
    manual_review_required, manual_review_completed, manual_review_notes,
    ocr_confidence, manufacturer, series, models, created_at, updated_at
) VALUES (
    NEW.id, NEW.filename, NEW.original_filename, NEW.file_size, NEW.file_hash, NEW.storage_path,
    NEW.document_type, NEW.language, NEW.version, NEW.publish_date, NEW.page_count, NEW.word_count,
    NEW.character_count, NEW.content_text, NEW.content_summary, NEW.extracted_metadata,
    NEW.processing_status, NEW.processing_results, NEW.processing_error, NEW.confidence_score,
    NEW.manual_review_required, NEW.manual_review_completed, NEW.manual_review_notes,
    NEW.ocr_confidence, NEW.manufacturer, NEW.series, NEW.models, NEW.created_at, NEW.updated_at
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
    extracted_metadata = NEW.extracted_metadata,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE documents_delete AS
ON DELETE TO public.documents DO INSTEAD
DELETE FROM krai_core.documents WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Done!
-- ============================================================================
