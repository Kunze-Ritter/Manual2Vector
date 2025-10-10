-- ============================================================================
-- Migration 72: Create OEM Relationships Table
-- ============================================================================
-- Purpose: Store OEM/rebrand relationships for cross-manufacturer search
-- Date: 2025-10-10
-- Author: KRAI Development Team
--
-- This enables:
-- - Cross-OEM search (e.g., search "Konica 5000i" finds Brother docs)
-- - Automatic OEM detection during processing
-- - RAG query expansion for better search results
-- ============================================================================

-- Create oem_relationships table
CREATE TABLE IF NOT EXISTS krai_core.oem_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Brand Information
    brand_manufacturer VARCHAR(100) NOT NULL,
    brand_series_pattern VARCHAR(200) NOT NULL,
    
    -- OEM Information
    oem_manufacturer VARCHAR(100) NOT NULL,
    
    -- Relationship Details
    relationship_type VARCHAR(50) DEFAULT 'engine', -- 'engine', 'rebrand', 'platform', 'partnership'
    applies_to TEXT[] DEFAULT ARRAY['error_codes', 'parts'], -- What this OEM relationship affects
    
    -- Metadata
    notes TEXT,
    confidence FLOAT DEFAULT 1.0, -- 0.0 - 1.0 (how confident we are in this mapping)
    
    -- Source tracking
    source VARCHAR(100) DEFAULT 'manual', -- 'manual', 'industry_report', 'service_manual', etc.
    verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT unique_brand_oem UNIQUE (brand_manufacturer, brand_series_pattern, oem_manufacturer)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_oem_relationships_brand 
    ON krai_core.oem_relationships(brand_manufacturer);

CREATE INDEX IF NOT EXISTS idx_oem_relationships_oem 
    ON krai_core.oem_relationships(oem_manufacturer);

CREATE INDEX IF NOT EXISTS idx_oem_relationships_series 
    ON krai_core.oem_relationships(brand_series_pattern);

CREATE INDEX IF NOT EXISTS idx_oem_relationships_type 
    ON krai_core.oem_relationships(relationship_type);

-- Create GIN index for applies_to array
CREATE INDEX IF NOT EXISTS idx_oem_relationships_applies_to 
    ON krai_core.oem_relationships USING GIN(applies_to);

-- Add RLS (Row Level Security)
ALTER TABLE krai_core.oem_relationships ENABLE ROW LEVEL SECURITY;

-- Policy: Allow read access to all authenticated users
CREATE POLICY oem_relationships_select_policy ON krai_core.oem_relationships
    FOR SELECT
    USING (true);

-- Policy: Allow insert/update/delete for service role only
CREATE POLICY oem_relationships_modify_policy ON krai_core.oem_relationships
    FOR ALL
    USING (auth.role() = 'service_role');

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION krai_core.update_oem_relationships_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER oem_relationships_updated_at
    BEFORE UPDATE ON krai_core.oem_relationships
    FOR EACH ROW
    EXECUTE FUNCTION krai_core.update_oem_relationships_updated_at();

-- Add comments
COMMENT ON TABLE krai_core.oem_relationships IS 
    'Stores OEM/rebrand relationships between manufacturers for cross-manufacturer search and error code detection';

COMMENT ON COLUMN krai_core.oem_relationships.brand_manufacturer IS 
    'The brand name shown on the product (e.g., "Konica Minolta", "Xerox")';

COMMENT ON COLUMN krai_core.oem_relationships.brand_series_pattern IS 
    'Regex pattern to match product series (e.g., "[45]000i" for 4000i/5000i)';

COMMENT ON COLUMN krai_core.oem_relationships.oem_manufacturer IS 
    'The actual manufacturer of the engine/platform (e.g., "Brother", "Fujifilm")';

COMMENT ON COLUMN krai_core.oem_relationships.applies_to IS 
    'Array of what this OEM relationship affects: error_codes, parts, supplies, accessories';

COMMENT ON COLUMN krai_core.oem_relationships.confidence IS 
    'Confidence level in this mapping (0.0 = uncertain, 1.0 = verified)';

-- Grant permissions
GRANT SELECT ON krai_core.oem_relationships TO anon, authenticated;
GRANT ALL ON krai_core.oem_relationships TO service_role;
