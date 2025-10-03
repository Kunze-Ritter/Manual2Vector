-- ======================================================================
-- 🔧 MIGRATION 09: Product Compatibility & Dependencies
-- ======================================================================
-- Purpose: Track dependencies, incompatibilities, and prerequisites
--          between products (especially options/accessories)
-- ======================================================================

BEGIN;

-- ======================================================================
-- STEP 1: Extend product_accessories with more relationship types
-- ======================================================================

-- Add new compatibility types
ALTER TABLE krai_core.product_accessories
DROP CONSTRAINT IF EXISTS product_accessories_compatibility_type_check;

ALTER TABLE krai_core.product_accessories
ADD CONSTRAINT product_accessories_compatibility_type_check 
CHECK (compatibility_type IN (
    'compatible',        -- Works together
    'required',          -- accessory_id is required for product_id
    'requires',          -- product_id requires accessory_id
    'conflicts',         -- Cannot be used together
    'recommended',       -- Recommended combination
    'alternative',       -- Alternative option
    'prerequisite'       -- Must be installed before
));

-- Add priority field for conflict resolution
ALTER TABLE krai_core.product_accessories
ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;

-- Add documentation/reason
ALTER TABLE krai_core.product_accessories
ADD COLUMN IF NOT EXISTS compatibility_notes TEXT;

-- ======================================================================
-- STEP 2: Create Product Configuration Validation Table
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_core.product_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    configuration_name VARCHAR(200),
    base_product_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    
    -- Configuration details
    accessories JSONB DEFAULT '[]',  -- Array of accessory IDs
    is_valid BOOLEAN DEFAULT true,
    validation_errors JSONB DEFAULT '[]',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    
    -- Indexing
    CONSTRAINT configuration_name_unique UNIQUE (configuration_name)
);

CREATE INDEX IF NOT EXISTS idx_configurations_base_product 
ON krai_core.product_configurations(base_product_id);

CREATE INDEX IF NOT EXISTS idx_configurations_accessories 
ON krai_core.product_configurations USING GIN (accessories);

-- ======================================================================
-- STEP 3: Helper Functions
-- ======================================================================

-- Function: Check if two products are compatible
CREATE OR REPLACE FUNCTION krai_core.check_compatibility(
    product_1_id UUID,
    product_2_id UUID
) RETURNS TABLE (
    compatible BOOLEAN,
    relationship VARCHAR,
    notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN pa.compatibility_type = 'conflicts' THEN false
            ELSE true
        END as compatible,
        pa.compatibility_type as relationship,
        pa.compatibility_notes as notes
    FROM krai_core.product_accessories pa
    WHERE (pa.product_id = product_1_id AND pa.accessory_id = product_2_id)
       OR (pa.product_id = product_2_id AND pa.accessory_id = product_1_id);
    
    -- If no relationship found, assume compatible
    IF NOT FOUND THEN
        RETURN QUERY SELECT true, 'unknown'::VARCHAR, 'No compatibility information found'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Get all required accessories for a product
CREATE OR REPLACE FUNCTION krai_core.get_required_accessories(
    p_product_id UUID
) RETURNS TABLE (
    accessory_id UUID,
    model_number VARCHAR,
    product_type VARCHAR,
    reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.model_number,
        p.product_type,
        pa.compatibility_notes
    FROM krai_core.product_accessories pa
    JOIN krai_core.products p ON p.id = pa.accessory_id
    WHERE pa.product_id = p_product_id
      AND pa.compatibility_type IN ('required', 'prerequisite');
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Get all incompatible products
CREATE OR REPLACE FUNCTION krai_core.get_incompatible_products(
    p_product_id UUID
) RETURNS TABLE (
    incompatible_id UUID,
    model_number VARCHAR,
    product_type VARCHAR,
    reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.model_number,
        p.product_type,
        pa.compatibility_notes
    FROM krai_core.product_accessories pa
    JOIN krai_core.products p ON p.id = pa.accessory_id
    WHERE pa.product_id = p_product_id
      AND pa.compatibility_type = 'conflicts';
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Validate a product configuration
CREATE OR REPLACE FUNCTION krai_core.validate_configuration(
    p_base_product_id UUID,
    p_accessory_ids UUID[]
) RETURNS TABLE (
    is_valid BOOLEAN,
    errors JSONB
) AS $$
DECLARE
    v_errors JSONB := '[]'::JSONB;
    v_is_valid BOOLEAN := true;
    v_accessory UUID;
    v_other_accessory UUID;
    v_required_accessories UUID[];
    v_compatibility RECORD;
BEGIN
    -- Check for required accessories
    SELECT ARRAY_AGG(accessory_id) INTO v_required_accessories
    FROM krai_core.product_accessories
    WHERE product_id = p_base_product_id
      AND compatibility_type IN ('required', 'prerequisite');
    
    -- Check if all required accessories are present
    IF v_required_accessories IS NOT NULL THEN
        FOREACH v_accessory IN ARRAY v_required_accessories
        LOOP
            IF NOT (v_accessory = ANY(p_accessory_ids)) THEN
                v_is_valid := false;
                v_errors := v_errors || jsonb_build_object(
                    'type', 'missing_required',
                    'accessory_id', v_accessory,
                    'message', 'Required accessory is missing'
                );
            END IF;
        END LOOP;
    END IF;
    
    -- Check for conflicts between accessories
    FOREACH v_accessory IN ARRAY p_accessory_ids
    LOOP
        FOREACH v_other_accessory IN ARRAY p_accessory_ids
        LOOP
            IF v_accessory != v_other_accessory THEN
                -- Check compatibility
                SELECT * INTO v_compatibility
                FROM krai_core.check_compatibility(v_accessory, v_other_accessory);
                
                IF v_compatibility.compatible = false THEN
                    v_is_valid := false;
                    v_errors := v_errors || jsonb_build_object(
                        'type', 'conflict',
                        'accessory_1', v_accessory,
                        'accessory_2', v_other_accessory,
                        'message', v_compatibility.notes
                    );
                END IF;
            END IF;
        END LOOP;
    END LOOP;
    
    RETURN QUERY SELECT v_is_valid, v_errors;
END;
$$ LANGUAGE plpgsql STABLE;

-- ======================================================================
-- STEP 4: Sample Compatibility Data (Examples)
-- ======================================================================

-- Note: These are examples. Real data should be extracted from documents.

COMMENT ON TABLE krai_core.product_accessories IS 
'Product relationships and compatibility matrix. 
Examples:
- MK-746 requires MK-730 (mounting bracket)
- SD-506 conflicts with SD-513 (both saddle finishers)
- PF-602m requires power supply unit';

COMMENT ON FUNCTION krai_core.validate_configuration IS
'Validates a product configuration by checking:
1. All required accessories are present
2. No conflicting accessories
3. Prerequisites are met';

COMMIT;
