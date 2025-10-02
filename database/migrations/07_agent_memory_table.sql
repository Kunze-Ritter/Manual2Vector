-- ===========================================
-- AGENT MEMORY TABLE FOR N8N
-- ===========================================
-- Compatible with n8n Postgres Memory Module

-- Create krai_agent schema if not exists
CREATE SCHEMA IF NOT EXISTS krai_agent;

-- Drop existing memory table if any
DROP TABLE IF EXISTS krai_agent.memory CASCADE;

-- Agent Memory Table (n8n compatible)
CREATE TABLE krai_agent.memory (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'function', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for fast lookups
CREATE INDEX idx_memory_session_id ON krai_agent.memory(session_id);
CREATE INDEX idx_memory_created_at ON krai_agent.memory(created_at DESC);
CREATE INDEX idx_memory_session_created ON krai_agent.memory(session_id, created_at DESC);

-- Enable RLS
ALTER TABLE krai_agent.memory ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all for service_role, read-only for others)
CREATE POLICY "Allow service_role full access" ON krai_agent.memory
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow authenticated read" ON krai_agent.memory
    FOR SELECT
    TO authenticated
    USING (true);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION krai_agent.update_memory_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER memory_updated_at
    BEFORE UPDATE ON krai_agent.memory
    FOR EACH ROW
    EXECUTE FUNCTION krai_agent.update_memory_timestamp();

-- Helper function to get recent memory for a session
CREATE OR REPLACE FUNCTION krai_agent.get_session_memory(
    p_session_id VARCHAR,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    role VARCHAR,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.role,
        m.content,
        m.metadata,
        m.created_at
    FROM krai_agent.memory m
    WHERE m.session_id = p_session_id
    ORDER BY m.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Helper function to clear old memory
CREATE OR REPLACE FUNCTION krai_agent.clear_old_memory(
    p_days_to_keep INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM krai_agent.memory
    WHERE created_at < now() - (p_days_to_keep || ' days')::interval;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create public view for PostgREST access
DROP VIEW IF EXISTS public.vw_agent_memory CASCADE;

CREATE OR REPLACE VIEW public.vw_agent_memory AS
SELECT 
    id, session_id, role, content, metadata, tokens_used, created_at, updated_at
FROM krai_agent.memory;

-- Grant access
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_agent_memory TO service_role;
GRANT SELECT ON public.vw_agent_memory TO authenticated, anon;

COMMENT ON TABLE krai_agent.memory IS 'Agent conversation memory for n8n Postgres Memory Module';
COMMENT ON VIEW public.vw_agent_memory IS 'Agent Memory: Conversation history for n8n AI Agent (PostgREST accessible)';

-- Insert example memory for testing
INSERT INTO krai_agent.memory (session_id, role, content, metadata) VALUES
    ('demo-session-001', 'system', 'You are a helpful AI assistant for KRAI documentation.', '{"model": "gpt-4", "temperature": 0.7}'),
    ('demo-session-001', 'user', 'What is error code E001?', '{"source": "web_ui"}'),
    ('demo-session-001', 'assistant', 'Error E001 typically indicates a paper jam. Please check the paper tray.', '{"confidence": 0.95}');
