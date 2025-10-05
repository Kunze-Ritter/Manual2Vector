-- ======================================================================
-- Migration 28: Denormalize Links/Videos for Unified Search
-- ======================================================================
-- Description: Add manufacturer_id, series_id to links/videos for fast filtering
--              Add priority_level to documents for result ranking
--              Add related_error_codes array for direct error code linking
-- Date: 2025-10-05
-- Reason: Enable unified multi-resource search for technicians
-- ======================================================================

-- GOAL: Technician searches "Error C-2801" and gets:
--   1. Service Manual entries (priority 2)
--   2. Service Bulletins (priority 1 - newest info!)
--   3. Video Tutorials (priority 3)
--   4. External Links (priority 4)
--   5. Related Parts (priority 5)

-- ======================================================================
-- PART 1: Extend Links Table
-- ======================================================================

-- Add manufacturer and series for fast filtering
ALTER TABLE krai_content.links
ADD COLUMN IF NOT EXISTS manufacturer_id UUID REFERENCES krai_core.manufacturers(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS series_id UUID REFERENCES krai_core.product_series(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS related_error_codes TEXT[];  -- Array of error codes mentioned in link

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_links_manufacturer ON krai_content.links(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_links_series ON krai_content.links(series_id);
CREATE INDEX IF NOT EXISTS idx_links_error_codes ON krai_content.links USING GIN(related_error_codes);

-- Update comments
COMMENT ON COLUMN krai_content.links.manufacturer_id IS 
'Manufacturer this link is related to (for fast filtering)';
COMMENT ON COLUMN krai_content.links.series_id IS 
'Product series this link is related to (for fast filtering)';
COMMENT ON COLUMN krai_content.links.related_error_codes IS 
'Array of error codes mentioned in link (e.g., ["C-2801", "C-2802"])';

-- ======================================================================
-- PART 2: Extend Videos Table (if exists)
-- ======================================================================

-- Check if videos table exists, if yes extend it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'krai_content' AND table_name = 'videos'
    ) THEN
        -- Add columns if they don't exist
        ALTER TABLE krai_content.videos
        ADD COLUMN IF NOT EXISTS manufacturer_id UUID REFERENCES krai_core.manufacturers(id) ON DELETE SET NULL,
        ADD COLUMN IF NOT EXISTS series_id UUID REFERENCES krai_core.product_series(id) ON DELETE SET NULL,
        ADD COLUMN IF NOT EXISTS related_error_codes TEXT[];
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_videos_manufacturer ON krai_content.videos(manufacturer_id);
        CREATE INDEX IF NOT EXISTS idx_videos_series ON krai_content.videos(series_id);
        CREATE INDEX IF NOT EXISTS idx_videos_error_codes ON krai_content.videos USING GIN(related_error_codes);
        
        RAISE NOTICE '✅ Extended videos table';
    ELSE
        RAISE NOTICE '⚠️  Videos table does not exist (will be created later)';
    END IF;
END $$;

-- ======================================================================
-- PART 3: Add Priority Level to Documents
-- ======================================================================

-- Priority determines result ranking (1=highest, 10=lowest)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS priority_level INTEGER DEFAULT 5;

-- Set priority based on document type
UPDATE krai_core.documents 
SET priority_level = CASE document_type
    WHEN 'service_bulletin' THEN 1      -- Most important - latest fixes!
    WHEN 'technical_bulletin' THEN 1    -- Also critical updates
    WHEN 'service_manual' THEN 2        -- Primary technical resource
    WHEN 'parts_catalog' THEN 3         -- For parts lookup
    WHEN 'user_manual' THEN 4           -- Basic info
    WHEN 'quick_reference' THEN 4       -- Quick guides
    WHEN 'specification' THEN 5         -- Detailed specs
    WHEN 'other' THEN 6                 -- Everything else
    ELSE 5
END
WHERE priority_level IS NULL OR priority_level = 5;  -- Only update defaults

-- Create index for sorting
CREATE INDEX IF NOT EXISTS idx_documents_priority ON krai_core.documents(priority_level);

-- Update comment
COMMENT ON COLUMN krai_core.documents.priority_level IS 
'Search result priority (1=highest/bulletins, 2=service_manual, 3=parts, etc.)';

-- ======================================================================
-- PART 4: Helper Function - Auto-populate manufacturer/series from document
-- ======================================================================

-- This function will be called by the pipeline to auto-link resources
CREATE OR REPLACE FUNCTION auto_link_resource_to_document(
    p_resource_table TEXT,
    p_resource_id UUID,
    p_document_id UUID
)
RETURNS VOID AS $$
DECLARE
    v_manufacturer_id UUID;
    v_series_id UUID;
    v_sql TEXT;
BEGIN
    -- Get manufacturer and main series from document via document_products
    SELECT 
        p.manufacturer_id,
        p.series_id
    INTO v_manufacturer_id, v_series_id
    FROM krai_core.document_products dp
    JOIN krai_core.products p ON dp.product_id = p.id
    WHERE dp.document_id = p_document_id
    AND p.manufacturer_id IS NOT NULL
    LIMIT 1;
    
    -- Update the resource table
    IF v_manufacturer_id IS NOT NULL THEN
        v_sql := format(
            'UPDATE %I SET manufacturer_id = $1, series_id = $2 WHERE id = $3',
            p_resource_table
        );
        
        EXECUTE v_sql USING v_manufacturer_id, v_series_id, p_resource_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION auto_link_resource_to_document IS 
'Helper function to auto-populate manufacturer/series for links/videos from their document';

-- ======================================================================
-- PART 5: Backfill existing data
-- ======================================================================

-- Backfill manufacturer_id for existing links (via document_products)
UPDATE krai_content.links l
SET manufacturer_id = (
    SELECT p.manufacturer_id
    FROM krai_core.document_products dp
    JOIN krai_core.products p ON dp.product_id = p.id
    WHERE dp.document_id = l.document_id
    AND p.manufacturer_id IS NOT NULL
    LIMIT 1
)
WHERE l.manufacturer_id IS NULL
AND l.document_id IS NOT NULL;

-- Backfill series_id for existing links (take first product's series)
UPDATE krai_content.links l
SET series_id = (
    SELECT p.series_id
    FROM krai_core.document_products dp
    JOIN krai_core.products p ON dp.product_id = p.id
    WHERE dp.document_id = l.document_id
    AND p.series_id IS NOT NULL
    LIMIT 1
)
WHERE l.series_id IS NULL
AND l.document_id IS NOT NULL;

-- Backfill videos if table exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'krai_content' AND table_name = 'videos'
    ) THEN
        -- Backfill manufacturer_id (via document_products)
        UPDATE krai_content.videos v
        SET manufacturer_id = (
            SELECT p.manufacturer_id
            FROM krai_core.document_products dp
            JOIN krai_core.products p ON dp.product_id = p.id
            WHERE dp.document_id = v.document_id
            AND p.manufacturer_id IS NOT NULL
            LIMIT 1
        )
        WHERE v.manufacturer_id IS NULL
        AND v.document_id IS NOT NULL;
        
        -- Backfill series_id
        UPDATE krai_content.videos v
        SET series_id = (
            SELECT p.series_id
            FROM krai_core.document_products dp
            JOIN krai_core.products p ON dp.product_id = p.id
            WHERE dp.document_id = v.document_id
            AND p.series_id IS NOT NULL
            LIMIT 1
        )
        WHERE v.series_id IS NULL
        AND v.document_id IS NOT NULL;
        
        RAISE NOTICE '✅ Backfilled videos';
    END IF;
END $$;

-- ======================================================================
-- Verification
-- ======================================================================

-- Show updated link structure
SELECT 
    COUNT(*) as total_links,
    COUNT(manufacturer_id) as links_with_manufacturer,
    COUNT(series_id) as links_with_series,
    ROUND(100.0 * COUNT(manufacturer_id) / NULLIF(COUNT(*), 0), 2) as manufacturer_pct,
    ROUND(100.0 * COUNT(series_id) / NULLIF(COUNT(*), 0), 2) as series_pct
FROM krai_content.links;

-- Show document priorities
SELECT 
    document_type,
    priority_level,
    COUNT(*) as doc_count
FROM krai_core.documents
GROUP BY document_type, priority_level
ORDER BY priority_level, document_type;

-- Expected:
-- service_bulletin: priority 1
-- service_manual: priority 2
-- Most links now have manufacturer_id
