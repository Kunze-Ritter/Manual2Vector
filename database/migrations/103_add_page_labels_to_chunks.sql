-- Add page_label columns to chunks table
-- For proper page number display (i, ii, iii, 1, 2, 3 instead of just index)

-- Add columns
ALTER TABLE krai_intelligence.chunks 
ADD COLUMN IF NOT EXISTS page_label_start VARCHAR(20),
ADD COLUMN IF NOT EXISTS page_label_end VARCHAR(20);

-- Add indexes for searching by page label
CREATE INDEX IF NOT EXISTS idx_chunks_page_label_start 
ON krai_intelligence.chunks(page_label_start);

CREATE INDEX IF NOT EXISTS idx_chunks_page_label_end 
ON krai_intelligence.chunks(page_label_end);

-- Add comments
COMMENT ON COLUMN krai_intelligence.chunks.page_label_start IS 
'Document page label for start page (e.g., "i", "ii", "1", "2") - for user display';

COMMENT ON COLUMN krai_intelligence.chunks.page_label_end IS 
'Document page label for end page (e.g., "i", "ii", "1", "2") - for user display';

-- Note: page_start and page_end remain as PDF index (0-based)
-- page_label_start and page_label_end are the actual document page numbers

-- Success message
SELECT '✅ page_label columns added to chunks table!' as status;
