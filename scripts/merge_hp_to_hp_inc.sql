-- Merge HP manufacturers to "HP Inc." as canonical name
-- Run this in Supabase SQL Editor

-- Step 1: Delete "Hewlett Packard" (both have 0 products anyway)
DELETE FROM krai_core.manufacturers 
WHERE id = '6b265278-8085-4705-bb0c-f50e542c0b30';  -- Hewlett Packard

-- Step 2: Verify only HP Inc. remains
SELECT id, name, created_at
FROM krai_core.manufacturers
WHERE LOWER(name) LIKE '%hp%' 
   OR LOWER(name) LIKE '%hewlett%' 
   OR LOWER(name) LIKE '%packard%';

-- Expected result: Only "HP Inc." (28a8e546-e400-47ad-9622-96d841810c1c)
