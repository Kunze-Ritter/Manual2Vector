-- Migration 14a: Drop and Create documents TABLE
-- PART 1 of 2: Drop existing object and create fresh table

-- ============================================================================
-- Drop existing TABLE or VIEW (dynamic detection)
-- ============================================================================

DO $$ 
DECLARE
    obj_type text;
BEGIN
    -- Check what type of object it is
    SELECT CASE 
        WHEN EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'krai_core' AND tablename = 'documents') THEN 'table'
        WHEN EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'krai_core' AND viewname = 'documents') THEN 'view'
        ELSE 'none'
    END INTO obj_type;
    
    -- Drop based on type
    IF obj_type = 'table' THEN
        EXECUTE 'DROP TABLE krai_core.documents CASCADE';
        RAISE NOTICE 'Dropped TABLE krai_core.documents';
    ELSIF obj_type = 'view' THEN
        EXECUTE 'DROP VIEW krai_core.documents CASCADE';
        RAISE NOTICE 'Dropped VIEW krai_core.documents';
    ELSE
        RAISE NOTICE 'krai_core.documents does not exist';
    END IF;
END $$;

-- ============================================================================
-- Create documents as TABLE (with ALL required columns)
-- ============================================================================

CREATE TABLE krai_core.documents (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- File Information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size BIGINT,
    file_hash VARCHAR(64),
    storage_path TEXT,
    
    -- Document Classification
    document_type VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    
    -- Version & Publishing
    version VARCHAR(50),
    publish_date DATE,
    
    -- Content Statistics
    page_count INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    
    -- Content Storage
    content_text TEXT,
    content_summary TEXT,
    
    -- Metadata (JSONB)
    extracted_metadata JSONB DEFAULT '{}',
    
    -- Processing Status
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_results JSONB DEFAULT NULL,
    processing_error TEXT DEFAULT NULL,
    stage_status JSONB DEFAULT '{}',
    
    -- Quality Scores
    confidence_score DECIMAL(3,2),
    ocr_confidence DECIMAL(3,2),
    
    -- Manual Review
    manual_review_required BOOLEAN DEFAULT false,
    manual_review_completed BOOLEAN DEFAULT false,
    manual_review_notes TEXT,
    
    -- Extracted Information
    manufacturer VARCHAR(100),
    series VARCHAR(100),
    models TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Grant basic permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON krai_core.documents TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_core.documents TO service_role;

-- ============================================================================
-- Verification Query (run this to check)
-- ============================================================================

-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_schema = 'krai_core' 
--   AND table_name = 'documents'
-- ORDER BY ordinal_position;
