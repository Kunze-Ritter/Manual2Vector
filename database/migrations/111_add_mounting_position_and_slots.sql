-- Migration 111: Add mounting position and slot support for accessories
-- Adds: mounting_position, slot_number, max_quantity to product_accessories
-- Date: 2025-10-22

-- Add new columns to product_accessories
ALTER TABLE krai_core.product_accessories 
ADD COLUMN IF NOT EXISTS mounting_position VARCHAR(20),
ADD COLUMN IF NOT EXISTS slot_number INTEGER,
ADD COLUMN IF NOT EXISTS max_quantity INTEGER DEFAULT 1;

-- Add check constraint for mounting_position
ALTER TABLE krai_core.product_accessories 
DROP CONSTRAINT IF EXISTS mounting_position_check;

ALTER TABLE krai_core.product_accessories 
ADD CONSTRAINT mounting_position_check CHECK (
    mounting_position IN (
        'top',          -- Document feeders mounted on top
        'side',         -- Finishers, large capacity units on side
        'bottom',       -- Cabinets, desks under the device
        'internal',     -- Controllers, authentication inside/back
        'accessory',    -- Mount kits, punch kits, etc.
        NULL            -- Not specified
    )
);

-- Add comments
COMMENT ON COLUMN krai_core.product_accessories.mounting_position IS 
'Physical mounting position: top (document feeders), side (finishers), bottom (cabinets), internal (controllers), accessory (kits)';

COMMENT ON COLUMN krai_core.product_accessories.slot_number IS 
'Slot number if accessory can be installed in multiple positions (e.g., FK-513 in slot 1 or 2)';

COMMENT ON COLUMN krai_core.product_accessories.max_quantity IS 
'Maximum quantity of this accessory that can be installed (default: 1)';

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_product_accessories_mounting_position 
ON krai_core.product_accessories(mounting_position);

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 111 complete: Added mounting_position, slot_number, and max_quantity to product_accessories';
END $$;
