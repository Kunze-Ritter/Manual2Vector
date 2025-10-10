-- ============================================================================
-- Migration 74: Create Product Research Cache Table
-- ============================================================================
-- Purpose: Store AI-powered online research results for products
-- Date: 2025-10-10
-- Author: KRAI Development Team
--
-- This enables:
-- - Automatic product specs extraction from manufacturer websites
-- - OEM relationship discovery
-- - Series name verification
-- - Self-learning system (reduces manual pattern maintenance)
-- ============================================================================

-- Create product_research_cache table
CREATE TABLE IF NOT EXISTS krai_intelligence.product_research_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Product identification
    manufacturer VARCHAR(100) NOT NULL,
    model_number VARCHAR(100) NOT NULL,
    
    -- Series information
    series_name VARCHAR(200),
    series_description TEXT,
    
    -- Product specifications (JSONB for flexibility)
    specifications JSONB DEFAULT '{}'::jsonb,
    -- Example structure:
    -- {
    --   "speed_mono": 75,
    --   "speed_color": 75,
    --   "resolution": "1200x1200 dpi",
    --   "paper_sizes": ["A4", "A3", "Letter", "Legal"],
    --   "duplex": "automatic",
    --   "memory": "8192 MB",
    --   "storage": "256 GB SSD",
    --   "connectivity": ["USB 2.0", "Ethernet", "WiFi"],
    --   "scan_speed": "240 ipm",
    --   "monthly_duty": 300000
    -- }
    
    -- Physical specifications
    physical_specs JSONB DEFAULT '{}'::jsonb,
    -- Example:
    -- {
    --   "dimensions": {"width": 615, "depth": 685, "height": 1193, "unit": "mm"},
    --   "weight": 145.5,
    --   "weight_unit": "kg",
    --   "power_consumption": 1500,
    --   "power_unit": "W"
    -- }
    
    -- OEM information
    oem_manufacturer VARCHAR(100),
    oem_relationship_type VARCHAR(50),
    oem_notes TEXT,
    
    -- Lifecycle information
    launch_date DATE,
    eol_date DATE,
    
    -- Pricing (optional)
    pricing JSONB DEFAULT '{}'::jsonb,
    -- Example:
    -- {
    --   "msrp": 15000,
    --   "currency": "USD",
    --   "region": "US"
    -- }
    
    -- Product type
    product_type VARCHAR(100),
    
    -- Research metadata
    confidence FLOAT DEFAULT 0.0,
    source_urls TEXT[],
    research_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cache_valid_until TIMESTAMP WITH TIME ZONE,
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Research notes
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT unique_manufacturer_model UNIQUE (manufacturer, model_number)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_research_cache_manufacturer 
    ON krai_intelligence.product_research_cache(manufacturer);

CREATE INDEX IF NOT EXISTS idx_research_cache_model 
    ON krai_intelligence.product_research_cache(model_number);

CREATE INDEX IF NOT EXISTS idx_research_cache_series 
    ON krai_intelligence.product_research_cache(series_name);

CREATE INDEX IF NOT EXISTS idx_research_cache_confidence 
    ON krai_intelligence.product_research_cache(confidence);

CREATE INDEX IF NOT EXISTS idx_research_cache_verified 
    ON krai_intelligence.product_research_cache(verified);

CREATE INDEX IF NOT EXISTS idx_research_cache_valid_until 
    ON krai_intelligence.product_research_cache(cache_valid_until);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_research_cache_specifications 
    ON krai_intelligence.product_research_cache USING GIN(specifications);

CREATE INDEX IF NOT EXISTS idx_research_cache_physical_specs 
    ON krai_intelligence.product_research_cache USING GIN(physical_specs);

-- Add RLS (Row Level Security)
ALTER TABLE krai_intelligence.product_research_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Allow read access to all authenticated users
CREATE POLICY research_cache_select_policy ON krai_intelligence.product_research_cache
    FOR SELECT
    USING (true);

-- Policy: Allow insert/update/delete for service role only
CREATE POLICY research_cache_modify_policy ON krai_intelligence.product_research_cache
    FOR ALL
    USING (auth.role() = 'service_role');

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION krai_intelligence.update_research_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER research_cache_updated_at
    BEFORE UPDATE ON krai_intelligence.product_research_cache
    FOR EACH ROW
    EXECUTE FUNCTION krai_intelligence.update_research_cache_updated_at();

-- Add comments
COMMENT ON TABLE krai_intelligence.product_research_cache IS 
    'Stores AI-powered online research results for products (specs, OEM, series)';

COMMENT ON COLUMN krai_intelligence.product_research_cache.manufacturer IS 
    'Manufacturer name (e.g., "Konica Minolta", "HP")';

COMMENT ON COLUMN krai_intelligence.product_research_cache.model_number IS 
    'Product model number (e.g., "C750i", "LaserJet Pro M454dw")';

COMMENT ON COLUMN krai_intelligence.product_research_cache.specifications IS 
    'JSONB with product specifications (speed, resolution, memory, etc.)';

COMMENT ON COLUMN krai_intelligence.product_research_cache.physical_specs IS 
    'JSONB with physical specifications (dimensions, weight, power)';

COMMENT ON COLUMN krai_intelligence.product_research_cache.confidence IS 
    'Confidence level in research results (0.0 = uncertain, 1.0 = verified)';

COMMENT ON COLUMN krai_intelligence.product_research_cache.source_urls IS 
    'Array of URLs used for research (manufacturer website, datasheets, etc.)';

COMMENT ON COLUMN krai_intelligence.product_research_cache.cache_valid_until IS 
    'Cache expiration date (research should be refreshed after this date)';

COMMENT ON COLUMN krai_intelligence.product_research_cache.verified IS 
    'Whether research results have been manually verified';

-- Grant permissions
GRANT SELECT ON krai_intelligence.product_research_cache TO anon, authenticated;
GRANT ALL ON krai_intelligence.product_research_cache TO service_role;

-- Create helper function to check if cache is valid
CREATE OR REPLACE FUNCTION krai_intelligence.is_research_cache_valid(
    p_manufacturer VARCHAR,
    p_model_number VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_valid_until TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT cache_valid_until INTO v_valid_until
    FROM krai_intelligence.product_research_cache
    WHERE manufacturer = p_manufacturer
      AND model_number = p_model_number;
    
    IF v_valid_until IS NULL THEN
        RETURN false;
    END IF;
    
    RETURN v_valid_until > NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION krai_intelligence.is_research_cache_valid IS 
    'Check if research cache is still valid for a product';

-- Create helper function to get cached research
CREATE OR REPLACE FUNCTION krai_intelligence.get_cached_research(
    p_manufacturer VARCHAR,
    p_model_number VARCHAR
) RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'series_name', series_name,
        'series_description', series_description,
        'specifications', specifications,
        'physical_specs', physical_specs,
        'oem_manufacturer', oem_manufacturer,
        'oem_relationship_type', oem_relationship_type,
        'oem_notes', oem_notes,
        'product_type', product_type,
        'confidence', confidence,
        'verified', verified,
        'source_urls', source_urls
    ) INTO v_result
    FROM krai_intelligence.product_research_cache
    WHERE manufacturer = p_manufacturer
      AND model_number = p_model_number
      AND (cache_valid_until IS NULL OR cache_valid_until > NOW());
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION krai_intelligence.get_cached_research IS 
    'Get cached research results for a product (returns NULL if expired)';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 74 completed successfully!';
    RAISE NOTICE '   - Created product_research_cache table';
    RAISE NOTICE '   - Added indexes for performance';
    RAISE NOTICE '   - Created helper functions';
    RAISE NOTICE '   - Enabled RLS for security';
END $$;
