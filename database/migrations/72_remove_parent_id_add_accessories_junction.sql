-- Migration 72: Remove parent_id and add product_accessories junction table
-- 
-- Purpose:
-- 1. Remove unused parent_id column from products (was for series/options, now obsolete)
-- 2. Add proper M:N junction table for product accessories
--    (One accessory can fit multiple products, one product can have multiple accessories)
--
-- Rationale:
-- - parent_id was 1:N (one parent) but accessories need M:N (many products)
-- - manufacturer_id and series_id already handle product hierarchy
-- - Junction table is the correct pattern for accessories/options

BEGIN;

-- ============================================================================
-- PART 1: Remove parent_id from products
-- ============================================================================

-- Check if column exists before dropping (idempotent)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'krai_core' 
        AND table_name = 'products' 
        AND column_name = 'parent_id'
    ) THEN
        ALTER TABLE krai_core.products DROP COLUMN parent_id;
        RAISE NOTICE 'Dropped parent_id column from products';
    ELSE
        RAISE NOTICE 'parent_id column does not exist, skipping';
    END IF;
END $$;

-- ============================================================================
-- PART 2: Create product_accessories junction table
-- ============================================================================

-- Junction table for M:N relationship between products and accessories
-- Example: Finisher FS-533 can be used with bizhub C558, C658, C758
CREATE TABLE IF NOT EXISTS krai_core.product_accessories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- The main product (e.g., bizhub C558)
    product_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    
    -- The accessory/option (e.g., Finisher FS-533)
    accessory_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    
    -- Optional: Compatibility notes
    compatibility_notes TEXT,
    
    -- Optional: Is this accessory standard or optional?
    is_standard BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate links
    UNIQUE(product_id, accessory_id),
    
    -- Prevent self-reference (product can't be its own accessory)
    CHECK (product_id != accessory_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_product_accessories_product 
    ON krai_core.product_accessories(product_id);
CREATE INDEX IF NOT EXISTS idx_product_accessories_accessory 
    ON krai_core.product_accessories(accessory_id);

-- ============================================================================
-- PART 3: Add helpful comments
-- ============================================================================

COMMENT ON TABLE krai_core.product_accessories IS 
    'M:N junction table linking products to their compatible accessories/options. One accessory can fit multiple products.';

COMMENT ON COLUMN krai_core.product_accessories.product_id IS 
    'The main product (e.g., bizhub C558)';

COMMENT ON COLUMN krai_core.product_accessories.accessory_id IS 
    'The accessory/option (e.g., Finisher FS-533, Paper Tray PF-707)';

COMMENT ON COLUMN krai_core.product_accessories.is_standard IS 
    'True if this accessory comes standard with the product, false if optional';

COMMIT;
