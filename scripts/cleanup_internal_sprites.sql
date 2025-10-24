-- Cleanup internal sprite codes from database
-- Run this in Supabase SQL Editor

-- Delete product_accessories links first
DELETE FROM krai_core.product_accessories 
WHERE product_id IN (
  SELECT id FROM krai_core.products 
  WHERE model_number LIKE 'APCM_%' 
     OR model_number LIKE 'IM_%'
     OR model_number LIKE 'Controller_%'
     OR model_number LIKE 'VI-515_%'
     OR model_number LIKE 'IC-320S%'
)
OR accessory_id IN (
  SELECT id FROM krai_core.products 
  WHERE model_number LIKE 'APCM_%' 
     OR model_number LIKE 'IM_%'
     OR model_number LIKE 'Controller_%'
     OR model_number LIKE 'VI-515_%'
     OR model_number LIKE 'IC-320S%'
);

-- Delete the products
DELETE FROM krai_core.products 
WHERE model_number LIKE 'APCM_%' 
   OR model_number LIKE 'IM_%'
   OR model_number LIKE 'Controller_%'
   OR model_number LIKE 'VI-515_%'
   OR model_number LIKE 'IC-320S%';

-- Show remaining products
SELECT model_number, product_type, manufacturer_id
FROM krai_core.products
WHERE manufacturer_id = 'a62168e3-8b74-47b6-824c-5a1772e6b06f'  -- Konica Minolta
  AND product_type = 'laser_multifunction'
ORDER BY model_number;
