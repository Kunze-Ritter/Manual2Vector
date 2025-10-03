-- Migration: Convert to JSONB specifications
-- Reason: Flexible spec storage for requirements matching & comparison

BEGIN;

-- Add JSONB columns to products table
ALTER TABLE krai_core.products 
ADD COLUMN IF NOT EXISTS specifications JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS technical_specs JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS feature_flags JSONB DEFAULT '{}';

-- Migrate existing data to JSONB (if columns exist)
UPDATE krai_core.products
SET specifications = jsonb_build_object(
    'max_print_speed_ppm', max_print_speed_ppm,
    'max_resolution_dpi', max_resolution_dpi,
    'max_paper_size', max_paper_size,
    'duplex_capable', duplex_capable,
    'network_capable', network_capable,
    'mobile_print_support', mobile_print_support,
    'dimensions_mm', dimensions_mm,
    'connectivity_options', connectivity_options,
    'print_technology', print_technology
)
WHERE specifications = '{}';

-- Create GIN indexes for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_products_specifications 
ON krai_core.products USING GIN (specifications);

CREATE INDEX IF NOT EXISTS idx_products_technical_specs 
ON krai_core.products USING GIN (technical_specs);

CREATE INDEX IF NOT EXISTS idx_products_feature_flags 
ON krai_core.products USING GIN (feature_flags);

-- Add comments for documentation
COMMENT ON COLUMN krai_core.products.specifications IS 
'Flexible product specifications in JSONB format. Used for requirements matching and product comparison.';

COMMENT ON COLUMN krai_core.products.technical_specs IS 
'Technical specifications (dimensions, power, environment) in JSONB format.';

COMMENT ON COLUMN krai_core.products.feature_flags IS 
'Feature flags and capabilities in JSONB format.';

-- Example query functions

-- Function: Check if product meets requirements
CREATE OR REPLACE FUNCTION krai_core.meets_requirements(
    product_specs JSONB,
    requirements JSONB
) RETURNS BOOLEAN AS $$
BEGIN
    -- Check if product specs contain all required specs
    RETURN product_specs @> requirements;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION krai_core.meets_requirements IS 
'Check if product specifications meet given requirements. Usage: meets_requirements(specifications, ''{"speed": 80}''::jsonb)';

-- Example: Find products matching tender requirements
-- SELECT * FROM products 
-- WHERE meets_requirements(specifications, '{"max_print_speed_ppm": 80, "duplex_capable": true}'::jsonb);

COMMIT;

-- ROLLBACK PLAN (if needed):
-- BEGIN;
-- DROP INDEX IF EXISTS idx_products_specifications;
-- DROP INDEX IF EXISTS idx_products_technical_specs;
-- DROP INDEX IF EXISTS idx_products_feature_flags;
-- DROP FUNCTION IF EXISTS krai_core.meets_requirements;
-- ALTER TABLE krai_core.products DROP COLUMN IF EXISTS specifications;
-- ALTER TABLE krai_core.products DROP COLUMN IF EXISTS technical_specs;
-- ALTER TABLE krai_core.products DROP COLUMN IF EXISTS feature_flags;
-- COMMIT;
