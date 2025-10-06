-- Migration: Create error_code_images junction table for many-to-many relationship
-- This allows multiple images per error code

-- Create junction table
CREATE TABLE IF NOT EXISTS krai_intelligence.error_code_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_code_id UUID NOT NULL REFERENCES krai_intelligence.error_codes(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES krai_content.images(id) ON DELETE CASCADE,
    match_method TEXT, -- 'smart_vision_ai', 'page_match', 'manual'
    match_confidence FLOAT DEFAULT 0.5,
    display_order INTEGER DEFAULT 0, -- For sorting images by relevance
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(error_code_id, image_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_error_code_images_error_code 
    ON krai_intelligence.error_code_images(error_code_id);
    
CREATE INDEX IF NOT EXISTS idx_error_code_images_image 
    ON krai_intelligence.error_code_images(image_id);

-- Add RLS policies
ALTER TABLE krai_intelligence.error_code_images ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow read access to error_code_images"
    ON krai_intelligence.error_code_images
    FOR SELECT
    USING (true);

CREATE POLICY "Allow insert for service role"
    ON krai_intelligence.error_code_images
    FOR INSERT
    WITH CHECK (true);

-- Comment
COMMENT ON TABLE krai_intelligence.error_code_images IS 
'Junction table linking error codes to multiple images (many-to-many relationship)';

COMMENT ON COLUMN krai_intelligence.error_code_images.match_method IS 
'How the image was matched: smart_vision_ai (AI detected error code), page_match (same page), manual';

COMMENT ON COLUMN krai_intelligence.error_code_images.display_order IS 
'Order for displaying images (0 = most relevant)';
