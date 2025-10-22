-- Migration 107: Add new product types for improved categorization
-- Adds: finisher_accessory, controller_accessory, image_controller, and other specialized types
-- Note: product_type is VARCHAR(50) with CHECK constraint

-- Step 1: Drop existing CHECK constraint
ALTER TABLE krai_core.products DROP CONSTRAINT IF EXISTS product_type_check;

-- Step 2: Add new CHECK constraint with additional values
ALTER TABLE krai_core.products ADD CONSTRAINT product_type_check CHECK (
    product_type IN (
        -- Printers
        'laser_printer', 'inkjet_printer', 'laser_production_printer', 'inkjet_production_printer',
        'solid_ink_printer', 'dot_matrix_printer', 'thermal_printer', 'dye_sublimation_printer',
        
        -- Multifunction
        'laser_multifunction', 'inkjet_multifunction', 'laser_production_multifunction', 
        'inkjet_production_multifunction', 'solid_ink_multifunction',
        
        -- Plotters
        'inkjet_plotter', 'latex_plotter', 'pen_plotter',
        
        -- Scanners
        'scanner', 'document_scanner', 'photo_scanner', 'large_format_scanner',
        
        -- Copiers
        'copier',
        
        -- Finishers & Finisher Accessories (NEW CATEGORY)
        'finisher', 'stapler_finisher', 'booklet_finisher', 'punch_finisher',
        'saddle_finisher',  -- NEW: SD-* units
        'finisher_accessory',  -- NEW: RU, PK, SK, TR units
        'folder', 'trimmer', 'stacker',
        'post_inserter',  -- NEW: PI-* units
        'z_fold_unit',  -- NEW: ZU-* units
        'creaser',  -- NEW: CR-* units
        'folding_unit',  -- NEW: FD-* units
        
        -- Paper Handling
        'feeder', 'paper_feeder', 'envelope_feeder', 'large_capacity_feeder', 'document_feeder',
        
        -- Controllers & Accessories (NEW CATEGORY)
        'image_controller',  -- NEW: IC-*, MIC-* units
        'controller_accessory',  -- NEW: VI-* units
        'controller',  -- Legacy
        
        -- Accessories
        'accessory', 'cabinet', 'work_table', 'caster_base', 'bridge_unit',
        'interface_kit', 'media_sensor', 'memory_upgrade', 'hard_drive',
        'fax_kit', 'wireless_kit', 'keyboard', 'card_reader', 'coin_kit',
        'option', 'duplex_unit', 'output_tray', 'mailbox', 'mount_kit', 'job_separator',
        
        -- Consumables
        'consumable', 'toner_cartridge', 'ink_cartridge', 'drum_unit', 'developer_unit',
        'fuser_unit', 'transfer_belt', 'waste_toner_box', 'maintenance_kit',
        'staple_cartridge', 'punch_kit', 'print_head', 'ink_tank', 'paper',
        
        -- Software
        'software', 'license', 'firmware'
    )
);

-- Step 3: Update existing products with new types where appropriate

-- Update RU-* to finisher_accessory
UPDATE krai_core.products
SET product_type = 'finisher_accessory',
    updated_at = NOW()
WHERE model_number ~ '^RU-\d{3}$'
  AND product_type != 'finisher_accessory';

-- Update PK-* to finisher_accessory
UPDATE krai_core.products
SET product_type = 'finisher_accessory',
    updated_at = NOW()
WHERE model_number ~ '^PK-\d{3}$'
  AND product_type != 'finisher_accessory';

-- Update SK-* to finisher_accessory
UPDATE krai_core.products
SET product_type = 'finisher_accessory',
    updated_at = NOW()
WHERE model_number ~ '^SK-\d{3}$'
  AND product_type != 'finisher_accessory';

-- Update SD-* to saddle_finisher
UPDATE krai_core.products
SET product_type = 'saddle_finisher',
    updated_at = NOW()
WHERE model_number ~ '^SD-\d{3}$'
  AND product_type != 'saddle_finisher';

-- Update IC-* to image_controller
UPDATE krai_core.products
SET product_type = 'image_controller',
    updated_at = NOW()
WHERE model_number ~ '^IC-\d{3}[A-Z]?$'
  AND product_type != 'image_controller';

-- Update MIC-* to image_controller
UPDATE krai_core.products
SET product_type = 'image_controller',
    updated_at = NOW()
WHERE model_number ~ '^MIC-\d{4}$'
  AND product_type != 'image_controller';

-- Update VI-* to controller_accessory
UPDATE krai_core.products
SET product_type = 'controller_accessory',
    updated_at = NOW()
WHERE model_number ~ '^VI-\d{3}[A-Z]?$'
  AND product_type != 'controller_accessory';

-- Update MK-* to mount_kit
UPDATE krai_core.products
SET product_type = 'mount_kit',
    updated_at = NOW()
WHERE model_number ~ '^MK-\d{3}$'
  AND product_type NOT IN ('mount_kit', 'finisher_accessory');

-- Add comment on column
COMMENT ON COLUMN krai_core.products.product_type IS 'Product type (VARCHAR): includes specialized categories for finishers, controllers, and accessories';

-- Log migration
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO updated_count
    FROM krai_core.products
    WHERE updated_at > NOW() - INTERVAL '1 minute';
    
    RAISE NOTICE 'Migration 107 complete: Added new product types and updated % existing products', updated_count;
END $$;
