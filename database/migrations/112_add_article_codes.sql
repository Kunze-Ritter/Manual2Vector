-- Migration 112: Add article_code to products table
-- Stores manufacturer article/part numbers (e.g., AAJ4WY2961 for DK-518)
-- Date: 2025-10-22

-- Add article_code column to products
ALTER TABLE krai_core.products 
ADD COLUMN IF NOT EXISTS article_code VARCHAR(50);

-- Add index for faster lookups by article code
CREATE INDEX IF NOT EXISTS idx_products_article_code 
ON krai_core.products(article_code);

-- Add comment
COMMENT ON COLUMN krai_core.products.article_code IS 
'Manufacturer article/part number (e.g., AAJ4WY2961). Used for ordering and identification.';

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 112 complete: Added article_code to products table';
END $$;
