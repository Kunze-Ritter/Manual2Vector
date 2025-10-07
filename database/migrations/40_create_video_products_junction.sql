-- Migration: Create video_products junction table
-- Date: 2025-01-07
-- Purpose: Many-to-many relationship between videos and products

-- Create junction table
CREATE TABLE IF NOT EXISTS krai_content.video_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES krai_content.videos(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique video-product pairs
    UNIQUE(video_id, product_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_video_products_video_id ON krai_content.video_products(video_id);
CREATE INDEX IF NOT EXISTS idx_video_products_product_id ON krai_content.video_products(product_id);

-- Comments
COMMENT ON TABLE krai_content.video_products IS 'Many-to-many relationship between videos and products';
COMMENT ON COLUMN krai_content.video_products.video_id IS 'Reference to video';
COMMENT ON COLUMN krai_content.video_products.product_id IS 'Reference to product model';

-- Create view in public schema
CREATE OR REPLACE VIEW public.video_products AS
SELECT * FROM krai_content.video_products;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.video_products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.video_products TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.video_products TO service_role;
