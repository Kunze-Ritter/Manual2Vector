-- Migration 13: Cleanup documents table + Add document_products Many-to-Many

-- ============================================================================
-- PART 1: Remove unused columns from krai_core.documents
-- ============================================================================

-- Remove storage_url (no longer using R2 for PDFs) - CASCADE to drop dependent views
ALTER TABLE krai_core.documents
DROP COLUMN IF EXISTS storage_url CASCADE;

-- Remove product_id (can only reference 1 product - wrong for manuals with many products)
ALTER TABLE krai_core.documents
DROP COLUMN IF EXISTS product_id CASCADE;

-- Remove manufacturer_id (redundant - we have manufacturer VARCHAR)
ALTER TABLE krai_core.documents
DROP COLUMN IF EXISTS manufacturer_id CASCADE;

COMMENT ON COLUMN krai_core.documents.manufacturer IS 'Manufacturer name (text) - auto-detected during processing';
COMMENT ON COLUMN krai_core.documents.models IS 'Array of model numbers extracted from document';

-- ============================================================================
-- PART 2: Create document_products Many-to-Many relationship table
-- ============================================================================

CREATE TABLE IF NOT EXISTS krai_core.document_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    
    -- Relationship metadata
    is_primary_product BOOLEAN DEFAULT false,
    confidence_score DECIMAL(3,2) DEFAULT 0.80,
    extraction_method VARCHAR(50),  -- 'pattern', 'llm', 'vision', 'manual'
    page_numbers INTEGER[],  -- Pages where this product was mentioned
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint: one product per document (but many products per document allowed)
    UNIQUE(document_id, product_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_document_products_document_id 
ON krai_core.document_products(document_id);

CREATE INDEX IF NOT EXISTS idx_document_products_product_id 
ON krai_core.document_products(product_id);

CREATE INDEX IF NOT EXISTS idx_document_products_primary 
ON krai_core.document_products(document_id, is_primary_product) 
WHERE is_primary_product = true;

-- Comments
COMMENT ON TABLE krai_core.document_products IS 'Many-to-Many relationship between documents and products';
COMMENT ON COLUMN krai_core.document_products.is_primary_product IS 'True if this is the main product covered by the document';
COMMENT ON COLUMN krai_core.document_products.extraction_method IS 'How the product was extracted: pattern, llm, vision, or manual';
COMMENT ON COLUMN krai_core.document_products.confidence_score IS 'Confidence score (0-1) of the product extraction';

-- ============================================================================
-- PART 3: Grant permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON krai_core.document_products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_core.document_products TO service_role;

-- ============================================================================
-- PART 4: Helper function to get all products for a document
-- ============================================================================

CREATE OR REPLACE FUNCTION krai_core.get_document_products(doc_id UUID)
RETURNS TABLE (
    product_id UUID,
    model_number VARCHAR,
    manufacturer_name VARCHAR,
    is_primary BOOLEAN,
    confidence DECIMAL,
    extraction_method VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id as product_id,
        p.model_number,
        m.name as manufacturer_name,
        dp.is_primary_product as is_primary,
        dp.confidence_score as confidence,
        dp.extraction_method
    FROM krai_core.document_products dp
    JOIN krai_core.products p ON dp.product_id = p.id
    LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
    WHERE dp.document_id = doc_id
    ORDER BY dp.is_primary_product DESC, dp.confidence_score DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION krai_core.get_document_products IS 'Get all products associated with a document, ordered by primary first then confidence';

-- ============================================================================
-- Done!
-- ============================================================================
