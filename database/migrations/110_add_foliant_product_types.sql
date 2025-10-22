-- Migration 110: Add product types from Foliant PDF imports
-- Adds: authentication_unit, controller_unit, punch_unit, stapler, relay_unit, fold_unit, large_capacity_unit
-- Date: 2025-10-22

-- Step 1: Drop existing CHECK constraint
ALTER TABLE krai_core.products DROP CONSTRAINT IF EXISTS product_type_check;

-- Step 2: Add new CHECK constraint with Foliant types
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
        
        -- Finishers & Finisher Accessories
        'finisher', 'stapler_finisher', 'booklet_finisher', 'punch_finisher',
        'saddle_finisher', 'finisher_accessory', 'folder', 'trimmer', 'stacker',
        'post_inserter', 'z_fold_unit', 'creaser', 'folding_unit',
        'stapler',  -- NEW: SD-*, JS-* standalone staplers
        'punch_unit',  -- NEW: HT-* hole punch units
        'fold_unit',  -- NEW: CR-*, FD-* folding/creasing units
        
        -- Paper Handling
        'feeder', 'paper_feeder', 'envelope_feeder', 'large_capacity_feeder', 'document_feeder',
        'large_capacity_unit',  -- NEW: LU-*, LK-* large capacity units
        'relay_unit',  -- NEW: RU-* relay units
        
        -- Controllers & Accessories
        'image_controller', 'controller_accessory', 'controller',
        'controller_unit',  -- NEW: CU-*, EK-*, IQ-* controller units
        'authentication_unit',  -- NEW: AU-*, IC-*, UK-* authentication/card readers
        
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

-- Step 3: Add comment
COMMENT ON CONSTRAINT product_type_check ON krai_core.products IS 
'Product types including Foliant-specific categories: authentication_unit, controller_unit, punch_unit, stapler, relay_unit, fold_unit, large_capacity_unit';

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 110 complete: Added Foliant product types (authentication_unit, controller_unit, punch_unit, stapler, relay_unit, fold_unit, large_capacity_unit)';
END $$;
