-- Migration: Expand product_type allowed values
-- Date: 2025-10-08
-- Purpose: Add more specific product types instead of generic ones

-- Drop old constraint
ALTER TABLE krai_core.products 
DROP CONSTRAINT IF EXISTS product_type_check;

-- Add new constraint with expanded values
ALTER TABLE krai_core.products 
ADD CONSTRAINT product_type_check CHECK (
    product_type IN (
        -- Original values
        'printer',
        'scanner',
        'multifunction',
        'copier',
        'plotter',
        'accessory',
        'option',
        'consumable',
        'finisher',
        'feeder',
        
        -- Expanded printer types
        'laser_printer',
        'inkjet_printer',
        'production_printer',
        'solid_ink_printer',
        
        -- Expanded multifunction types
        'laser_multifunction',
        'inkjet_multifunction',
        
        -- Plotter types
        'inkjet_plotter',
        'latex_plotter'
    )
);

COMMENT ON CONSTRAINT product_type_check ON krai_core.products IS 
'Allowed product types including specific technology variants (laser, inkjet, production, etc.)';
