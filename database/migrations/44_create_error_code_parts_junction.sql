-- Migration: Create error_code_parts junction table
-- Date: 2025-10-08
-- Purpose: Link parts to error codes for better search and display

-- Junction table: Error Codes ↔ Parts
CREATE TABLE IF NOT EXISTS krai_intelligence.error_code_parts (
    error_code_id UUID NOT NULL REFERENCES krai_intelligence.error_codes(id) ON DELETE CASCADE,
    part_id UUID NOT NULL REFERENCES krai_parts.parts_catalog(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 1.0,
    extraction_source TEXT, -- 'solution_text', 'description', 'chunk'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (error_code_id, part_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_error_code_parts_error_id 
ON krai_intelligence.error_code_parts(error_code_id);

CREATE INDEX IF NOT EXISTS idx_error_code_parts_part_id 
ON krai_intelligence.error_code_parts(part_id);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_intelligence.error_code_parts TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_intelligence.error_code_parts TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_intelligence.error_code_parts TO service_role;

COMMENT ON TABLE krai_intelligence.error_code_parts IS 'Junction table linking error codes to parts';
COMMENT ON COLUMN krai_intelligence.error_code_parts.relevance_score IS 'How relevant is this part to the error (0.0-1.0)';
COMMENT ON COLUMN krai_intelligence.error_code_parts.extraction_source IS 'Where the part was found (solution_text, description, etc.)';
