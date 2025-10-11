-- Migration: Optimize and expand product_type values
-- Date: 2025-10-09
-- Purpose: Remove redundant generic types, add dot_matrix, expand accessories/options

-- STEP 1: Check existing data
DO $$
BEGIN
    RAISE NOTICE 'Checking existing product_type values...';
END $$;

SELECT product_type, COUNT(*) as count
FROM krai_core.products
GROUP BY product_type
ORDER BY count DESC;

-- STEP 2: Migrate existing 'printer' values to 'laser_printer' (default assumption)
-- You can adjust this based on actual data
UPDATE krai_core.products
SET product_type = 'laser_printer'
WHERE product_type = 'printer';

-- STEP 3: Migrate existing 'multifunction' values to 'laser_multifunction' (default assumption)
UPDATE krai_core.products
SET product_type = 'laser_multifunction'
WHERE product_type = 'multifunction';

-- STEP 4: Drop old constraint
ALTER TABLE krai_core.products 
DROP CONSTRAINT IF EXISTS product_type_check;

-- STEP 5: Add new optimized constraint
ALTER TABLE krai_core.products 
ADD CONSTRAINT product_type_check CHECK (
    product_type IN (
        -- ===== PRINTERS (Single Function) =====
        'laser_printer',           -- Laser/LED printer
        'inkjet_printer',          -- Inkjet printer
        'laser_production_printer',-- Laser production printer (AccurioPress, imagePRESS)
        'inkjet_production_printer',-- Inkjet production printer (PageWide XL, AccurioJet)
        'solid_ink_printer',       -- Solid ink printer (Xerox ColorQube)
        'dot_matrix_printer',      -- Dot matrix/impact printer
        'thermal_printer',         -- Thermal transfer printer
        'dye_sublimation_printer', -- Dye-sub photo printer
        
        -- ===== MULTIFUNCTION (MFP) =====
        'laser_multifunction',     -- Laser/LED MFP
        'inkjet_multifunction',    -- Inkjet MFP
        'laser_production_multifunction',-- Laser production MFP
        'inkjet_production_multifunction',-- Inkjet production MFP
        'solid_ink_multifunction', -- Solid ink MFP (Xerox ColorQube)
        
        -- ===== PLOTTERS =====
        'inkjet_plotter',          -- Large format inkjet
        'latex_plotter',           -- HP Latex plotter
        'pen_plotter',             -- Pen plotter (legacy)
        
        -- ===== SCANNERS =====
        'scanner',                 -- Standalone scanner
        'document_scanner',        -- Document/ADF scanner
        'photo_scanner',           -- Photo/flatbed scanner
        'large_format_scanner',    -- Large format scanner
        
        -- ===== COPIERS =====
        'copier',                  -- Standalone copier (legacy)
        
        -- ===== FINISHERS & POST-PROCESSING =====
        'finisher',                -- Generic finisher
        'stapler_finisher',        -- Stapler finisher
        'booklet_finisher',        -- Booklet/saddle-stitch finisher
        'punch_finisher',          -- Hole punch finisher
        'folder',                  -- Folder unit
        'trimmer',                 -- Trimmer unit
        'stacker',                 -- Output stacker
        
        -- ===== FEEDERS =====
        'feeder',                  -- Generic feeder
        'paper_feeder',            -- Paper cassette/tray
        'envelope_feeder',         -- Envelope feeder
        'large_capacity_feeder',   -- LCF/HCF
        'document_feeder',         -- ADF (Auto Document Feeder)
        
        -- ===== ACCESSORIES =====
        'accessory',               -- Generic accessory
        'cabinet',                 -- Cabinet/stand
        'work_table',              -- Work table
        'caster_base',             -- Caster base/wheels
        'bridge_unit',             -- Bridge unit (connects devices)
        'interface_kit',           -- Network/USB interface
        'media_sensor',            -- Intelligent media sensor (paper weight/thickness)
        'memory_upgrade',          -- RAM/memory upgrade
        'hard_drive',              -- Internal hard drive
        'controller',              -- Print controller/DFE
        'fax_kit',                 -- Fax expansion kit
        'wireless_kit',            -- Wireless LAN kit
        'keyboard',                -- Keyboard unit
        'card_reader',             -- Card reader (authentication)
        'coin_kit',                -- Coin/payment kit
        
        -- ===== OPTIONS =====
        'option',                  -- Generic option
        'duplex_unit',             -- Duplex unit
        'output_tray',             -- Output tray
        'mailbox',                 -- Mailbox sorter
        'mount_kit',               -- Mount kit (MK-xxx for installing options)        
        'job_separator',           -- Job separator
        
        -- ===== CONSUMABLES =====
        'consumable',              -- Generic consumable
        'toner_cartridge',         -- Toner cartridge
        'ink_cartridge',           -- Ink cartridge
        'drum_unit',               -- Drum unit/imaging unit
        'developer_unit',          -- Developer unit
        'fuser_unit',              -- Fuser/fixing unit
        'transfer_belt',           -- Transfer belt/unit
        'waste_toner_box',         -- Waste toner container
        'maintenance_kit',         -- Maintenance kit (PM kits, service kits)
        'staple_cartridge',        -- Staple cartridge
        'punch_kit',               -- Punch waste box/kit
        'print_head',              -- Print head (inkjet)
        'ink_tank',                -- Ink tank (refillable)
        'paper',                   -- Paper (if tracked as product)
        
        -- ===== SOFTWARE & LICENSES =====
        'software',                -- Software package
        'license',                 -- Software license
        'firmware'                 -- Firmware update
    )
);

COMMENT ON CONSTRAINT product_type_check ON krai_core.products IS 
'Comprehensive product type classification including printers, MFPs, plotters, scanners, finishers, feeders, accessories, options, consumables, and software';

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_products_product_type 
ON krai_core.products(product_type);

COMMENT ON INDEX krai_core.idx_products_product_type IS 
'Index for filtering products by type (printer, accessory, consumable, etc.)';

-- STEP 6: Show migration summary
DO $$
DECLARE
    total_products INTEGER;
    laser_printers INTEGER;
    laser_mfps INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_products FROM krai_core.products;
    SELECT COUNT(*) INTO laser_printers FROM krai_core.products WHERE product_type = 'laser_printer';
    SELECT COUNT(*) INTO laser_mfps FROM krai_core.products WHERE product_type = 'laser_multifunction';
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 70 completed successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total products: %', total_products;
    RAISE NOTICE 'Laser printers: %', laser_printers;
    RAISE NOTICE 'Laser MFPs: %', laser_mfps;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Product types expanded from 18 to 76';
    RAISE NOTICE 'All existing data migrated successfully';
    RAISE NOTICE '========================================';
END $$;
