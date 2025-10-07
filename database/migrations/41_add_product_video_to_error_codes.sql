-- Migration: Add product_id and video_id to error_codes
-- Date: 2025-01-07
-- Purpose: Support product-specific and video-linked error codes

-- Add columns
ALTER TABLE krai_core.error_codes 
ADD COLUMN IF NOT EXISTS product_id UUID REFERENCES krai_core.products(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS video_id UUID REFERENCES krai_content.videos(id) ON DELETE SET NULL;

-- Drop old unique constraint (if exists)
ALTER TABLE krai_core.error_codes 
DROP CONSTRAINT IF EXISTS error_codes_error_code_manufacturer_id_key;

-- Create new unique constraint
-- Allows same error code for different products/documents/videos
CREATE UNIQUE INDEX IF NOT EXISTS idx_error_codes_unique_source
ON krai_core.error_codes(
  error_code, 
  manufacturer_id, 
  COALESCE(product_id, '00000000-0000-0000-0000-000000000000'::uuid),
  COALESCE(document_id, '00000000-0000-0000-0000-000000000000'::uuid),
  COALESCE(video_id, '00000000-0000-0000-0000-000000000000'::uuid)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_error_codes_product_id 
ON krai_core.error_codes(product_id) WHERE product_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_error_codes_video_id 
ON krai_core.error_codes(video_id) WHERE video_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_error_codes_document_id 
ON krai_core.error_codes(document_id) WHERE document_id IS NOT NULL;

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_error_codes_lookup
ON krai_core.error_codes(error_code, manufacturer_id, product_id);

-- Comments
COMMENT ON COLUMN krai_core.error_codes.product_id IS 'Product/model this error code applies to (allows same code for different models)';
COMMENT ON COLUMN krai_core.error_codes.video_id IS 'Video demonstrating solution for this error code';

-- Update view
CREATE OR REPLACE VIEW public.error_codes AS
SELECT * FROM krai_core.error_codes;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.error_codes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.error_codes TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.error_codes TO service_role;
