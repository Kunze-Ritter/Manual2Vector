-- Migration 12: Add processing_results column to documents table
-- This column stores the complete processing results from the pipeline
-- including extracted entities, statistics, and metadata

-- Add processing_results column (JSONB for flexible storage)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_results JSONB DEFAULT NULL;

-- Add processing_error column (for error messages)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_error TEXT DEFAULT NULL;

-- Add processing_status column (for status tracking)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'pending';

-- Create index on processing_status for filtering
CREATE INDEX IF NOT EXISTS idx_documents_processing_status
ON krai_core.documents(processing_status);

-- Create GIN index on processing_results for JSON queries
CREATE INDEX IF NOT EXISTS idx_documents_processing_results
ON krai_core.documents USING GIN (processing_results);

-- Add comments
COMMENT ON COLUMN krai_core.documents.processing_results IS 'Complete processing results from the pipeline (JSONB)';
COMMENT ON COLUMN krai_core.documents.processing_error IS 'Error message if processing failed';
COMMENT ON COLUMN krai_core.documents.processing_status IS 'Processing status: pending, processing, completed, failed';

-- Grant permissions
GRANT SELECT, UPDATE ON krai_core.documents TO authenticated;
GRANT SELECT, UPDATE ON krai_core.documents TO service_role;
