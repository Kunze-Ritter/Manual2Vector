-- ============================================================================
-- Migration 75: Add Specifications JSONB Column to Products Table
-- ============================================================================
-- Purpose: Store flexible product specifications in JSONB format
-- Date: 2025-10-10
-- Author: KRAI Development Team
--
-- This enables:
-- - Flexible storage of any product specification
-- - No schema changes needed for new spec types
-- - Fast queries with GIN indexes
-- - Integration with Product Research System
-- ============================================================================

-- Add specifications column to products table
ALTER TABLE krai_core.products 
ADD COLUMN IF NOT EXISTS specifications JSONB DEFAULT '{}'::jsonb;

-- Create GIN index for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_products_specifications 
    ON krai_core.products USING GIN(specifications);

-- Add comment
COMMENT ON COLUMN krai_core.products.specifications IS 
    'JSONB with flexible product specifications (speed, resolution, memory, connectivity, etc.)';

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
--   "monthly_duty": 300000,
--   "physical": {
--     "dimensions": {"width": 615, "depth": 685, "height": 1193, "unit": "mm"},
--     "weight": 145.5,
--     "weight_unit": "kg",
--     "power_consumption": 1500,
--     "power_unit": "W"
--   }
-- }

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 75 completed successfully!';
    RAISE NOTICE '   - Added specifications JSONB column to products';
    RAISE NOTICE '   - Created GIN index for performance';
    RAISE NOTICE '   - Ready for Product Research System integration';
END $$;
