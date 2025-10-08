-- Migration: Ensure documents.manufacturer_id column exists
-- Date: 2025-10-08
-- Purpose: Add manufacturer_id to documents if missing

-- Add manufacturer_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'krai_core' 
        AND table_name = 'documents' 
        AND column_name = 'manufacturer_id'
    ) THEN
        ALTER TABLE krai_core.documents 
        ADD COLUMN manufacturer_id UUID REFERENCES krai_core.manufacturers(id);
        
        RAISE NOTICE 'Added manufacturer_id column to documents table';
    ELSE
        RAISE NOTICE 'manufacturer_id column already exists';
    END IF;
END $$;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_documents_manufacturer_id 
ON krai_core.documents(manufacturer_id);

COMMENT ON COLUMN krai_core.documents.manufacturer_id IS 'Reference to manufacturer (normalized from manufacturer name)';
