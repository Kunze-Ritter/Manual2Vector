-- ======================================================================
-- 🔧 RESTRUCTURE: Products & Options mit JSONB
-- ======================================================================
-- Ziel: Flexible, einheitliche Struktur für alle Specs
-- Hierarchie: Manufacturer → Series → Products → Options/Accessories
-- ======================================================================

BEGIN;

-- ======================================================================
-- STEP 1: Optimierte Products Table (nur Core + JSONB)
-- ======================================================================

-- Backup existing data
CREATE TABLE IF NOT EXISTS krai_core.products_backup AS 
SELECT * FROM krai_core.products;

-- Drop old columns (werden in JSONB migriert)
ALTER TABLE krai_core.products
DROP COLUMN IF EXISTS print_technology,
DROP COLUMN IF EXISTS max_print_speed_ppm,
DROP COLUMN IF EXISTS max_resolution_dpi,
DROP COLUMN IF EXISTS max_paper_size,
DROP COLUMN IF EXISTS duplex_capable,
DROP COLUMN IF EXISTS network_capable,
DROP COLUMN IF EXISTS mobile_print_support,
DROP COLUMN IF EXISTS supported_languages,
DROP COLUMN IF EXISTS energy_star_certified,
DROP COLUMN IF EXISTS warranty_months,
DROP COLUMN IF EXISTS weight_kg,
DROP COLUMN IF EXISTS dimensions_mm,
DROP COLUMN IF EXISTS color_options,
DROP COLUMN IF EXISTS connectivity_options,
DROP COLUMN IF EXISTS option_dependencies,
DROP COLUMN IF EXISTS replacement_parts,
DROP COLUMN IF EXISTS common_issues;

-- Clean products table structure
-- krai_core.products
-- ├── id (UUID)
-- ├── manufacturer_id (FK)
-- ├── series_id (FK)
-- ├── parent_id (FK) - für Accessories/Options!
-- ├── model_number
-- ├── model_name
-- ├── product_type (printer|accessory|option|consumable)
-- ├── specifications (JSONB) - ALLE Specs hier!
-- ├── pricing (JSONB) - Preise & Kosten
-- ├── lifecycle (JSONB) - Launch, EOL dates
-- ├── urls (JSONB) - Manuals, Drivers, etc.
-- └── metadata (JSONB) - Sonstiges

ALTER TABLE krai_core.products
ADD COLUMN IF NOT EXISTS specifications JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS pricing JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS lifecycle JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS urls JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Update product_type ENUM
ALTER TABLE krai_core.products
ALTER COLUMN product_type TYPE VARCHAR(50);

-- Add check constraint
ALTER TABLE krai_core.products
ADD CONSTRAINT product_type_check 
CHECK (product_type IN ('printer', 'scanner', 'multifunction', 'copier', 'plotter', 
                        'accessory', 'option', 'consumable', 'finisher', 'feeder'));

COMMENT ON COLUMN krai_core.products.parent_id IS 
'Parent product ID. Used for accessories/options that belong to a main product. NULL for main products.';

COMMENT ON COLUMN krai_core.products.specifications IS 
'All product specifications in JSONB format. Example:
{
  "max_print_speed_ppm": 80,
  "max_resolution_dpi": 1200,
  "max_paper_size": "SRA3",
  "duplex_capable": true,
  "dimensions": {"width": 750, "depth": 850, "height": 1200},
  "connectivity": ["USB", "Ethernet", "WiFi"],
  "paper_capacity": {"standard": 3000, "maximum": 6000},
  "monthly_duty_cycle": 300000,
  "energy_star": 8.0
}';

COMMENT ON COLUMN krai_core.products.pricing IS 
'Pricing information in JSONB format. Example:
{
  "msrp_usd": 25000,
  "msrp_eur": 23000,
  "discount_tiers": [{"qty": 5, "discount_percent": 10}],
  "rental_monthly": 500,
  "service_contract_monthly": 200
}';

COMMENT ON COLUMN krai_core.products.lifecycle IS 
'Product lifecycle dates in JSONB format. Example:
{
  "launch_date": "2024-01-15",
  "end_of_sale_date": "2029-12-31",
  "end_of_life_date": "2034-12-31",
  "warranty_months": 12,
  "extended_warranty_available": true
}';

COMMENT ON COLUMN krai_core.products.urls IS 
'Product URLs in JSONB format. Example:
{
  "service_manual": "https://...",
  "parts_catalog": "https://...",
  "driver_download": "https://...",
  "product_page": "https://...",
  "support_page": "https://..."
}';

-- ======================================================================
-- STEP 2: Product Compatibility Table (simplified)
-- ======================================================================

-- Neue, einfachere Compatibility Table
CREATE TABLE IF NOT EXISTS krai_core.product_accessories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    accessory_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    compatibility_type VARCHAR(50) NOT NULL, -- 'required', 'optional', 'recommended'
    installation_required BOOLEAN DEFAULT false,
    quantity_min INTEGER DEFAULT 1,
    quantity_max INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, accessory_id)
);

COMMENT ON TABLE krai_core.product_accessories IS 
'Defines which accessories/options are compatible with which products.
Example: C4080 → compatible with → MK-746 Finisher';

-- ======================================================================
-- STEP 3: GIN Indexes für schnelle JSONB Queries
-- ======================================================================

CREATE INDEX IF NOT EXISTS idx_products_specifications 
ON krai_core.products USING GIN (specifications);

CREATE INDEX IF NOT EXISTS idx_products_pricing 
ON krai_core.products USING GIN (pricing);

CREATE INDEX IF NOT EXISTS idx_products_lifecycle 
ON krai_core.products USING GIN (lifecycle);

CREATE INDEX IF NOT EXISTS idx_products_metadata 
ON krai_core.products USING GIN (metadata);

-- Index für parent_id (Accessories finden)
CREATE INDEX IF NOT EXISTS idx_products_parent_id 
ON krai_core.products(parent_id) WHERE parent_id IS NOT NULL;

-- Index für product_type
CREATE INDEX IF NOT EXISTS idx_products_type 
ON krai_core.products(product_type);

-- ======================================================================
-- STEP 4: Helper Functions
-- ======================================================================

-- Function: Check if product meets requirements
CREATE OR REPLACE FUNCTION krai_core.meets_requirements(
    product_specs JSONB,
    requirements JSONB
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN product_specs @> requirements;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION krai_core.meets_requirements IS 
'Check if product specifications meet tender requirements.
Example: WHERE meets_requirements(specifications, ''{"max_print_speed_ppm": 80}''::jsonb)';

-- Function: Get all accessories for a product
CREATE OR REPLACE FUNCTION krai_core.get_product_accessories(
    p_product_id UUID
) RETURNS TABLE (
    accessory_id UUID,
    model_number VARCHAR,
    product_type VARCHAR,
    compatibility_type VARCHAR,
    specifications JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.model_number,
        p.product_type,
        pa.compatibility_type,
        p.specifications
    FROM krai_core.product_accessories pa
    JOIN krai_core.products p ON p.id = pa.accessory_id
    WHERE pa.product_id = p_product_id;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION krai_core.get_product_accessories IS 
'Get all compatible accessories for a product.
Example: SELECT * FROM get_product_accessories(''product-uuid'')';

-- Function: Compare two products
CREATE OR REPLACE FUNCTION krai_core.compare_products(
    product_id_1 UUID,
    product_id_2 UUID
) RETURNS TABLE (
    spec_key TEXT,
    product_1_value TEXT,
    product_2_value TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH specs AS (
        SELECT 
            p1.model_number as model_1,
            p1.specifications as specs_1,
            p2.model_number as model_2,
            p2.specifications as specs_2
        FROM krai_core.products p1
        CROSS JOIN krai_core.products p2
        WHERE p1.id = product_id_1 AND p2.id = product_id_2
    )
    SELECT 
        keys.key::TEXT,
        (specs_1 -> keys.key)::TEXT,
        (specs_2 -> keys.key)::TEXT
    FROM specs,
    LATERAL jsonb_object_keys(specs_1) AS keys(key);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION krai_core.compare_products IS 
'Compare specifications of two products side-by-side.
Example: SELECT * FROM compare_products(''uuid1'', ''uuid2'')';

-- ======================================================================
-- STEP 5: Migrate old data to JSONB
-- ======================================================================

-- Migrate existing products to new JSONB structure
UPDATE krai_core.products p
SET specifications = (
    SELECT jsonb_build_object(
        'max_print_speed_ppm', pb.max_print_speed_ppm,
        'max_resolution_dpi', pb.max_resolution_dpi,
        'max_paper_size', pb.max_paper_size,
        'duplex_capable', pb.duplex_capable,
        'network_capable', pb.network_capable,
        'mobile_print_support', pb.mobile_print_support,
        'supported_languages', pb.supported_languages,
        'energy_star_certified', pb.energy_star_certified,
        'dimensions', pb.dimensions_mm,
        'connectivity_options', pb.connectivity_options,
        'print_technology', pb.print_technology,
        'weight_kg', pb.weight_kg
    )
    FROM krai_core.products_backup pb
    WHERE pb.id = p.id
)
WHERE specifications = '{}';

UPDATE krai_core.products p
SET pricing = (
    SELECT jsonb_build_object(
        'msrp_usd', pb.msrp_usd
    )
    FROM krai_core.products_backup pb
    WHERE pb.id = p.id AND pb.msrp_usd IS NOT NULL
)
WHERE pricing = '{}';

UPDATE krai_core.products p
SET lifecycle = (
    SELECT jsonb_build_object(
        'launch_date', pb.launch_date,
        'end_of_life_date', pb.end_of_life_date,
        'warranty_months', pb.warranty_months
    )
    FROM krai_core.products_backup pb
    WHERE pb.id = p.id
)
WHERE lifecycle = '{}';

UPDATE krai_core.products p
SET urls = (
    SELECT jsonb_build_object(
        'service_manual', pb.service_manual_url,
        'parts_catalog', pb.parts_catalog_url,
        'driver_download', pb.driver_download_url
    )
    FROM krai_core.products_backup pb
    WHERE pb.id = p.id
)
WHERE urls = '{}';

COMMIT;

-- ======================================================================
-- EXAMPLES: How to use new structure
-- ======================================================================

-- Example 1: Insert main product with specs
/*
INSERT INTO krai_core.products (
    manufacturer_id, series_id, model_number, product_type, specifications
) VALUES (
    'manufacturer-uuid', 'series-uuid', 'C4080', 'printer',
    '{
        "max_print_speed_ppm": 80,
        "max_resolution_dpi": 1200,
        "duplex_capable": true,
        "paper_capacity": {"standard": 3000, "max": 6000}
    }'::jsonb
);
*/

-- Example 2: Insert accessory
/*
INSERT INTO krai_core.products (
    manufacturer_id, series_id, parent_id, model_number, product_type, specifications
) VALUES (
    'manufacturer-uuid', NULL, 'c4080-uuid', 'MK-746', 'finisher',
    '{
        "type": "booklet_finisher",
        "staple_capacity": 100,
        "fold_types": ["half", "tri"]
    }'::jsonb
);
*/

-- Example 3: Link accessory to product
/*
INSERT INTO krai_core.product_accessories (product_id, accessory_id, compatibility_type)
VALUES ('c4080-uuid', 'mk746-uuid', 'optional');
*/

-- Example 4: Query - Find products matching requirements
/*
SELECT model_number, specifications 
FROM krai_core.products
WHERE meets_requirements(specifications, '{"max_print_speed_ppm": 80, "duplex_capable": true}'::jsonb);
*/

-- Example 5: Get all accessories for a product
/*
SELECT * FROM krai_core.get_product_accessories('c4080-uuid');
*/

-- Example 6: Compare two products
/*
SELECT * FROM krai_core.compare_products('c4080-uuid', 'c4070-uuid');
*/
