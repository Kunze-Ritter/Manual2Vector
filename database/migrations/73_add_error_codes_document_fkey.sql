-- Migration 73: Add missing document_id foreign key to error_codes
-- Issue: Foreign key constraint for document_id was missing
-- This enables proper relation display in Supabase UI

-- Add foreign key constraint for document_id
ALTER TABLE krai_intelligence.error_codes
ADD CONSTRAINT error_codes_document_id_fkey
FOREIGN KEY (document_id)
REFERENCES krai_core.documents(id)
ON DELETE CASCADE;

-- Create index for performance (if not exists)
CREATE INDEX IF NOT EXISTS idx_error_codes_document_id
ON krai_intelligence.error_codes(document_id)
WHERE document_id IS NOT NULL;

-- Verify constraint was created
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'error_codes_document_id_fkey'
        AND table_schema = 'krai_intelligence'
        AND table_name = 'error_codes'
    ) THEN
        RAISE NOTICE '✅ Foreign key constraint error_codes_document_id_fkey created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create foreign key constraint';
    END IF;
END $$;
