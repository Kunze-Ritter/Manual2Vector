-- ============================================================================
-- Migration 73: Add OEM Columns to Products Table
-- ============================================================================
-- Purpose: Store OEM manufacturer info directly on products for fast lookup
-- Date: 2025-10-10
-- Author: KRAI Development Team
--
-- This enables:
-- - Fast OEM lookup without regex matching
-- - Direct product-to-OEM relationships
-- - Better search performance
-- ============================================================================

-- Add OEM columns to products table
ALTER TABLE krai_core.products 
ADD COLUMN IF NOT EXISTS oem_manufacturer VARCHAR(100),
ADD COLUMN IF NOT EXISTS oem_relationship_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS oem_notes TEXT;

-- Create index for fast OEM lookups
CREATE INDEX IF NOT EXISTS idx_products_oem_manufacturer 
    ON krai_core.products(oem_manufacturer);

CREATE INDEX IF NOT EXISTS idx_products_oem_relationship_type 
    ON krai_core.products(oem_relationship_type);

-- Add comments
COMMENT ON COLUMN krai_core.products.oem_manufacturer IS 
    'The OEM manufacturer if this is a rebrand (e.g., "Brother" for Konica Minolta 5000i)';

COMMENT ON COLUMN krai_core.products.oem_relationship_type IS 
    'Type of OEM relationship: engine, rebrand, platform, partnership';

COMMENT ON COLUMN krai_core.products.oem_notes IS 
    'Additional notes about the OEM relationship';
