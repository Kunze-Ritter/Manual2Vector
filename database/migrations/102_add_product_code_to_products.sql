-- Add product_code column to products table
-- For Konica Minolta: First 4 digits of serial number (e.g., A93E, AAJN)

-- Add column
ALTER TABLE krai_core.products 
ADD COLUMN IF NOT EXISTS product_code VARCHAR(10);

-- Add index for fast lookups
CREATE INDEX IF NOT EXISTS idx_products_product_code 
ON krai_core.products(product_code);

-- Add comment
COMMENT ON COLUMN krai_core.products.product_code IS 
'Product code (e.g., first 4 chars of serial number for Konica Minolta: A93E, AAJN)';

-- Update existing products with product_code from model_number
-- For Konica Minolta: Extract first 4 characters
UPDATE krai_core.products p
SET product_code = LEFT(model_number, 4)
FROM krai_core.manufacturers m
WHERE p.manufacturer_id = m.id
AND m.name ILIKE '%konica%'
AND product_code IS NULL
AND LENGTH(model_number) >= 4;

-- Verify
SELECT 
    COUNT(*) FILTER (WHERE product_code IS NOT NULL) as with_code,
    COUNT(*) FILTER (WHERE product_code IS NULL) as without_code,
    COUNT(*) as total
FROM krai_core.products;

-- Success message
SELECT '✅ product_code column added to products table!' as status;
