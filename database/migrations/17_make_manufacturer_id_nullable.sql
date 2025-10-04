-- Migration 17: Make manufacturer_id nullable in products table
-- Reason: Products are extracted with manufacturer_name (text), not manufacturer_id (UUID)

-- ============================================================================
-- Make manufacturer_id NULLABLE
-- ============================================================================

ALTER TABLE krai_core.products 
ALTER COLUMN manufacturer_id DROP NOT NULL;

-- ============================================================================
-- Add comment
-- ============================================================================

COMMENT ON COLUMN krai_core.products.manufacturer_id IS 
'Optional FK to manufacturers table. Can be NULL if only manufacturer name is known. Use manufacturer_name (in metadata) for text-based manufacturer info.';

-- ============================================================================
-- Verification
-- ============================================================================

-- Check constraint was removed:
-- SELECT column_name, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_schema = 'krai_core' 
--   AND table_name = 'products' 
--   AND column_name = 'manufacturer_id';

-- Should show: is_nullable = YES
