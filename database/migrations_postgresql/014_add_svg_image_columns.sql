-- Migration 014: Add SVG-related image columns
-- Description: Adds vector-image storage metadata fields used by SVG processing

ALTER TABLE krai_content.images
    ADD COLUMN IF NOT EXISTS svg_storage_url TEXT,
    ADD COLUMN IF NOT EXISTS original_svg_content TEXT,
    ADD COLUMN IF NOT EXISTS is_vector_graphic BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS has_png_derivative BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_images_is_vector_graphic
    ON krai_content.images(is_vector_graphic)
    WHERE is_vector_graphic = true;
