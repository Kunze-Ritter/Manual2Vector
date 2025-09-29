-- Add Links table for video/tutorial links extraction
CREATE TABLE IF NOT EXISTS krai_content.links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    link_type VARCHAR(50) NOT NULL DEFAULT 'external', -- 'video', 'external', 'tutorial'
    page_number INTEGER NOT NULL,
    description TEXT,
    position_data JSONB, -- Store link position/rect data
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add figure reference columns to images table
ALTER TABLE krai_content.images 
ADD COLUMN IF NOT EXISTS figure_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS figure_context TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_links_document_id ON krai_content.links(document_id);
CREATE INDEX IF NOT EXISTS idx_links_type ON krai_content.links(link_type);
CREATE INDEX IF NOT EXISTS idx_links_page ON krai_content.links(page_number);
CREATE INDEX IF NOT EXISTS idx_images_figure_number ON krai_content.images(figure_number) WHERE figure_number IS NOT NULL;

-- Add comments for documentation
COMMENT ON TABLE krai_content.links IS 'External links extracted from PDFs (videos, tutorials, etc.)';
COMMENT ON COLUMN krai_content.links.link_type IS 'Type: video, external, tutorial';
COMMENT ON COLUMN krai_content.links.position_data IS 'JSON data with link position/rect information';
COMMENT ON COLUMN krai_content.images.figure_number IS 'Figure reference number (e.g., "1", "2.1")';
COMMENT ON COLUMN krai_content.images.figure_context IS 'Context text around figure reference';

-- Create view for agent context queries
CREATE OR REPLACE VIEW krai_content.document_media_context AS
SELECT 
    d.id as document_id,
    d.filename,
    d.manufacturer,
    d.document_type,
    -- Images with figure references
    i.id as image_id,
    i.filename as image_filename,
    i.figure_number,
    i.figure_context,
    i.page_number as image_page,
    i.storage_url as image_url,
    -- Links (videos, tutorials)
    l.id as link_id,
    l.url as link_url,
    l.link_type,
    l.page_number as link_page,
    l.description as link_description
FROM krai_core.documents d
LEFT JOIN krai_content.images i ON d.id = i.document_id
LEFT JOIN krai_content.links l ON d.id = l.document_id
WHERE (i.id IS NOT NULL OR l.id IS NOT NULL);

COMMENT ON VIEW krai_content.document_media_context IS 'Unified view for agent context: documents with images, figures, and links';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.links TO authenticated;
GRANT SELECT ON krai_content.document_media_context TO authenticated;

SELECT 'Links and Figure References schema added successfully' as status;
