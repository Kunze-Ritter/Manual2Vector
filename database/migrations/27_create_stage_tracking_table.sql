-- ======================================================================
-- Migration 27: Create Stage Tracking Table
-- ======================================================================
-- Description: Create krai_system.stage_tracking table for pipeline monitoring
-- Date: 2025-10-05
-- Reason: Master pipeline uses stage_tracking but table was never created in migrations
-- ======================================================================

-- Ensure krai_system schema exists
CREATE SCHEMA IF NOT EXISTS krai_system;

-- Create stage_tracking table
CREATE TABLE IF NOT EXISTS krai_system.stage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_stage_tracking_document ON krai_system.stage_tracking(document_id);
CREATE INDEX IF NOT EXISTS idx_stage_tracking_stage ON krai_system.stage_tracking(stage_name);
CREATE INDEX IF NOT EXISTS idx_stage_tracking_status ON krai_system.stage_tracking(status);
CREATE INDEX IF NOT EXISTS idx_stage_tracking_created ON krai_system.stage_tracking(created_at DESC);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_system.stage_tracking TO service_role;

-- Add comment
COMMENT ON TABLE krai_system.stage_tracking IS 
'Tracks processing pipeline stages for monitoring and debugging';

-- ======================================================================
-- Verification
-- ======================================================================

-- Test insert
DO $$
DECLARE
    test_doc_id UUID;
    test_tracking_id UUID;
BEGIN
    -- Get a real document_id for testing
    SELECT id INTO test_doc_id FROM krai_core.documents LIMIT 1;
    
    IF test_doc_id IS NOT NULL THEN
        -- Test the table
        INSERT INTO krai_system.stage_tracking (
            document_id,
            stage_name,
            status,
            metadata
        ) VALUES (
            test_doc_id,
            'test_stage',
            'completed',
            '{"test": true}'::jsonb
        )
        RETURNING id INTO test_tracking_id;
        
        RAISE NOTICE '✅ stage_tracking table works! Test ID: %', test_tracking_id;
        
        -- Cleanup test data
        DELETE FROM krai_system.stage_tracking WHERE id = test_tracking_id;
        RAISE NOTICE '✅ Test data cleaned up';
    ELSE
        RAISE NOTICE '⚠️  No documents found for testing (table still created successfully)';
    END IF;
END $$;

-- Show table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'krai_system'
  AND table_name = 'stage_tracking'
ORDER BY ordinal_position;
