-- ======================================================================
-- ⚠️ DEPRECATED - DO NOT USE THIS MIGRATION! ⚠️
-- ======================================================================
-- Migration 17: Consolidated Features & Enhancements [DEPRECATED]
-- ======================================================================
-- Description: Consolidates all feature additions from migrations 06-16
-- Date: 2025-10-04
-- Status: DEPRECATED - Redundant with migrations 06-16
-- Reason: Tables already exist from earlier migrations (06, 07, 08, etc.)
--         Using this would cause conflicts with existing schema.
--         Use individual migrations 14b, 15a, 15b, 16a, 16b, 17 instead.
-- ======================================================================
-- ⚠️ THIS FILE IS KEPT FOR REFERENCE ONLY - DO NOT EXECUTE! ⚠️
-- ======================================================================

-- ======================================================================
-- AGENT FEATURES (from 06, 07, 10, 11, 12, 15)
-- ======================================================================

-- Agent Memory Table
CREATE TABLE IF NOT EXISTS krai_agent.memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_user_id ON krai_agent.memory(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_role ON krai_agent.memory(role);
CREATE INDEX IF NOT EXISTS idx_agent_memory_created_at ON krai_agent.memory(created_at DESC);

-- Agent Message Table (separate from memory for conversations)
CREATE TABLE IF NOT EXISTS krai_agent.message (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_message_user_id ON krai_agent.message(user_id);


-- ======================================================================
-- CONTENT ENHANCEMENTS (from 08, 09)
-- ======================================================================

-- Links & Videos (if not exists)
CREATE TABLE IF NOT EXISTS krai_content.links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    link_type TEXT CHECK (link_type IN ('external', 'internal', 'download', 'video')),
    title TEXT,
    description TEXT,
    page_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Enhancement for Error Codes
ALTER TABLE krai_intelligence.error_codes 
ADD COLUMN IF NOT EXISTS ai_solution TEXT,
ADD COLUMN IF NOT EXISTS ai_confidence FLOAT,
ADD COLUMN IF NOT EXISTS troubleshooting_steps JSONB DEFAULT '[]';


-- ======================================================================
-- PRODUCT COMPATIBILITY (from 09)
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_config.product_compatibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES krai_core.products(id) ON DELETE CASCADE,
    compatible_with_id UUID REFERENCES krai_core.products(id) ON DELETE CASCADE,
    compatibility_type TEXT CHECK (compatibility_type IN ('accessory', 'consumable', 'upgrade', 'replacement')),
    notes TEXT,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, compatible_with_id)
);


-- ======================================================================
-- N8N INTEGRATION FUNCTIONS (from 14, 16)
-- ======================================================================

-- Vector Search Function for N8N
CREATE OR REPLACE FUNCTION public.n8n_vector_search(
    query_text TEXT,
    match_count INT DEFAULT 5,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    text_chunk TEXT,
    similarity FLOAT,
    page_start INT,
    page_end INT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    query_embedding vector(768);
BEGIN
    -- This would need Ollama integration to generate embedding
    -- For now, return empty result
    RETURN QUERY
    SELECT 
        c.id,
        c.document_id,
        c.text_chunk,
        0.0::FLOAT as similarity,
        c.page_start,
        c.page_end
    FROM krai_intelligence.chunks c
    WHERE c.text_chunk ILIKE '%' || query_text || '%'
    LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.n8n_vector_search TO authenticated, service_role;


-- Search Analytics View (from 16)
CREATE OR REPLACE VIEW public.search_analytics AS
SELECT 
    date_trunc('day', sa.created_at) as date,
    COUNT(*) as total_searches,
    COUNT(DISTINCT sa.user_id) as unique_users,
    AVG(sa.results_count) as avg_results,
    COUNT(*) FILTER (WHERE sa.results_count = 0) as zero_results
FROM krai_intelligence.search_analytics sa
GROUP BY date_trunc('day', sa.created_at)
ORDER BY date DESC;

GRANT SELECT ON public.search_analytics TO authenticated, service_role;


-- ======================================================================
-- PROCESSING RESULTS (from 12)
-- ======================================================================

ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_results JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS processing_error TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'pending';

CREATE INDEX IF NOT EXISTS idx_documents_processing_status
ON krai_core.documents(processing_status);

CREATE INDEX IF NOT EXISTS idx_documents_processing_results
ON krai_core.documents USING GIN (processing_results);


-- ======================================================================
-- ENABLE RLS ON NEW TABLES
-- ======================================================================

ALTER TABLE krai_agent.memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_agent.message ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_content.links ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_config.product_compatibility ENABLE ROW LEVEL SECURITY;

-- RLS Policies (service_role full access)
CREATE POLICY IF NOT EXISTS agent_memory_service ON krai_agent.memory FOR ALL TO service_role USING (true);
CREATE POLICY IF NOT EXISTS agent_message_service ON krai_agent.message FOR ALL TO service_role USING (true);
CREATE POLICY IF NOT EXISTS links_service ON krai_content.links FOR ALL TO service_role USING (true);
CREATE POLICY IF NOT EXISTS compatibility_service ON krai_config.product_compatibility FOR ALL TO service_role USING (true);


-- ======================================================================
-- GRANT PERMISSIONS
-- ======================================================================

GRANT ALL ON krai_agent.memory TO service_role;
GRANT ALL ON krai_agent.message TO service_role;
GRANT ALL ON krai_content.links TO service_role;
GRANT ALL ON krai_config.product_compatibility TO service_role;

GRANT SELECT ON krai_agent.memory TO authenticated;
GRANT SELECT ON krai_agent.message TO authenticated;
GRANT SELECT ON krai_content.links TO authenticated;
GRANT SELECT ON krai_config.product_compatibility TO authenticated;


-- ======================================================================
-- COMMENTS
-- ======================================================================

COMMENT ON TABLE krai_agent.memory IS 'Agent conversation memory for context retention';
COMMENT ON TABLE krai_agent.message IS 'Agent messages separate from memory';
COMMENT ON TABLE krai_content.links IS 'External and internal links from documents';
COMMENT ON TABLE krai_config.product_compatibility IS 'Product compatibility mappings';
