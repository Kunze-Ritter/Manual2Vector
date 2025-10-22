-- Fix: Update links with manufacturer_id from their documents
-- Run this in Supabase SQL Editor

-- Update links that have document_id but no manufacturer_id
UPDATE krai_content.links l
SET manufacturer_id = d.manufacturer_id
FROM krai_core.documents d
WHERE l.document_id = d.id
AND l.manufacturer_id IS NULL
AND d.manufacturer_id IS NOT NULL;

-- Check results
SELECT 
    COUNT(*) FILTER (WHERE manufacturer_id IS NOT NULL) as with_manufacturer,
    COUNT(*) FILTER (WHERE manufacturer_id IS NULL) as without_manufacturer,
    COUNT(*) as total
FROM krai_content.links;
