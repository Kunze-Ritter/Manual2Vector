-- Merge HP manufacturers to "HP Inc." as canonical name
-- Run this in Supabase SQL Editor

-- Step 0: Check what references exist
SELECT 
    'documents' as table_name,
    COUNT(*) as count
FROM krai_core.documents 
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30'
UNION ALL
SELECT 
    'products' as table_name,
    COUNT(*) as count
FROM krai_core.products 
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30'
UNION ALL
SELECT 
    'error_codes' as table_name,
    COUNT(*) as count
FROM krai_intelligence.error_codes 
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30'
UNION ALL
SELECT 
    'parts_catalog' as table_name,
    COUNT(*) as count
FROM krai_parts.parts_catalog 
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30';

-- Step 1: Update documents to use HP Inc.
UPDATE krai_core.documents 
SET manufacturer_id = '28a8e546-e400-47ad-9622-96d841810c1c'  -- HP Inc.
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30';  -- Hewlett Packard

-- Step 2: Update products to use HP Inc.
UPDATE krai_core.products 
SET manufacturer_id = '28a8e546-e400-47ad-9622-96d841810c1c'  -- HP Inc.
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30';  -- Hewlett Packard

-- Step 3: Update error_codes to use HP Inc.
UPDATE krai_intelligence.error_codes 
SET manufacturer_id = '28a8e546-e400-47ad-9622-96d841810c1c'  -- HP Inc.
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30';  -- Hewlett Packard

-- Step 4: Update parts_catalog to use HP Inc.
UPDATE krai_parts.parts_catalog 
SET manufacturer_id = '28a8e546-e400-47ad-9622-96d841810c1c'  -- HP Inc.
WHERE manufacturer_id = '6b265278-8085-4705-bb0c-f50e542c0b30';  -- Hewlett Packard

-- Step 5: Now delete "Hewlett Packard"
DELETE FROM krai_core.manufacturers 
WHERE id = '6b265278-8085-4705-bb0c-f50e542c0b30';  -- Hewlett Packard

-- Step 6: Verify only HP Inc. remains
SELECT id, name, created_at,
    (SELECT COUNT(*) FROM krai_core.documents WHERE manufacturer_id = m.id) as documents,
    (SELECT COUNT(*) FROM krai_core.products WHERE manufacturer_id = m.id) as products,
    (SELECT COUNT(*) FROM krai_intelligence.error_codes WHERE manufacturer_id = m.id) as error_codes,
    (SELECT COUNT(*) FROM krai_parts.parts_catalog WHERE manufacturer_id = m.id) as parts
FROM krai_core.manufacturers m
WHERE LOWER(name) LIKE '%hp%' 
   OR LOWER(name) LIKE '%hewlett%' 
   OR LOWER(name) LIKE '%packard%';

-- Expected result: Only "HP Inc." (28a8e546-e400-47ad-9622-96d841810c1c) with all documents/products/error_codes/parts
