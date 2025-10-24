-- Check HP manufacturer entries in database
-- Run this in Supabase SQL Editor

-- 1. Find all HP-related manufacturers
SELECT 
    id,
    name,
    created_at,
    (SELECT COUNT(*) FROM krai_core.products WHERE manufacturer_id = m.id) as product_count
FROM krai_core.manufacturers m
WHERE LOWER(name) LIKE '%hp%' 
   OR LOWER(name) LIKE '%hewlett%' 
   OR LOWER(name) LIKE '%packard%'
ORDER BY created_at;

-- 2. Show products for each HP manufacturer
SELECT 
    m.name as manufacturer,
    m.id as manufacturer_id,
    COUNT(p.id) as product_count,
    STRING_AGG(p.model_number, ', ' ORDER BY p.model_number) as example_products
FROM krai_core.manufacturers m
LEFT JOIN krai_core.products p ON p.manufacturer_id = m.id
WHERE LOWER(m.name) LIKE '%hp%' 
   OR LOWER(m.name) LIKE '%hewlett%' 
   OR LOWER(m.name) LIKE '%packard%'
GROUP BY m.id, m.name
ORDER BY m.created_at;

-- 3. If multiple HP manufacturers exist, show merge script
-- (Run this only if you see duplicates above)
/*
-- Example merge script (adjust IDs based on results above):
-- Keep the OLDEST manufacturer ID, merge others into it

-- Step 1: Update products to use canonical manufacturer
UPDATE krai_core.products 
SET manufacturer_id = 'CANONICAL_ID_HERE'  -- Replace with oldest HP manufacturer ID
WHERE manufacturer_id IN (
    SELECT id FROM krai_core.manufacturers 
    WHERE LOWER(name) LIKE '%hp%' 
       OR LOWER(name) LIKE '%hewlett%' 
       OR LOWER(name) LIKE '%packard%'
);

-- Step 2: Rename canonical manufacturer to standard name
UPDATE krai_core.manufacturers
SET name = 'Hewlett Packard'
WHERE id = 'CANONICAL_ID_HERE';  -- Replace with canonical ID

-- Step 3: Delete duplicate manufacturers
DELETE FROM krai_core.manufacturers
WHERE (LOWER(name) LIKE '%hp%' OR LOWER(name) LIKE '%hewlett%' OR LOWER(name) LIKE '%packard%')
  AND id != 'CANONICAL_ID_HERE';  -- Keep only canonical ID
*/
