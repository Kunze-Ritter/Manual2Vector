-- ============================================
-- Migration: Add 'message' column to krai_agent.memory
-- Date: 2025-10-02
-- Purpose: n8n writes to 'message', synced with 'content'
-- ============================================

-- Add message column (same as content)
ALTER TABLE krai_agent.memory 
ADD COLUMN IF NOT EXISTS message TEXT;

-- Copy existing content to message
UPDATE krai_agent.memory 
SET message = content 
WHERE message IS NULL;

-- Create trigger to keep message and content in sync
-- When inserting/updating message, sync to content
CREATE OR REPLACE FUNCTION krai_agent.sync_message_content()
RETURNS TRIGGER AS $$
BEGIN
    -- If message is provided but not content, copy message to content
    IF NEW.message IS NOT NULL AND (NEW.content IS NULL OR NEW.content = '') THEN
        NEW.content := NEW.message;
    END IF;
    
    -- If content is provided but not message, copy content to message
    IF NEW.content IS NOT NULL AND (NEW.message IS NULL OR NEW.message = '') THEN
        NEW.message := NEW.content;
    END IF;
    
    -- If both provided, prefer message (n8n writes to message)
    IF NEW.message IS NOT NULL AND NEW.content IS NOT NULL THEN
        NEW.content := NEW.message;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to INSERT and UPDATE
DROP TRIGGER IF EXISTS sync_message_content_trigger ON krai_agent.memory;

CREATE TRIGGER sync_message_content_trigger
BEFORE INSERT OR UPDATE ON krai_agent.memory
FOR EACH ROW
EXECUTE FUNCTION krai_agent.sync_message_content();

-- Update view to use message column directly
DROP VIEW IF EXISTS public.vw_agent_memory CASCADE;

CREATE OR REPLACE VIEW public.vw_agent_memory AS
SELECT 
    id, 
    session_id, 
    role, 
    message,    -- Now a real column, not alias
    content,    -- Still available for compatibility
    metadata, 
    tokens_used, 
    created_at, 
    updated_at
FROM krai_agent.memory;

-- Grant access
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_agent_memory TO service_role;
GRANT SELECT ON public.vw_agent_memory TO authenticated, anon;

COMMENT ON COLUMN krai_agent.memory.message IS 'Chat message content (synced with content column)';
COMMENT ON VIEW public.vw_agent_memory IS 'Agent Memory: message and content columns stay in sync';

-- ============================================
-- EXPLANATION
-- ============================================
-- Table now has BOTH 'message' and 'content' columns
-- Trigger keeps them in sync automatically:
--   - Write to 'message' → copies to 'content'
--   - Write to 'content' → copies to 'message'
--   - n8n can write to 'message' field
--   - Other code can use 'content' field
--   - Both always have the same value
-- ============================================

-- VERIFICATION
-- ============================================
-- Test insert with message:
-- INSERT INTO krai_agent.memory (session_id, role, message) 
-- VALUES ('test-session', 'user', 'Test via message column');
-- 
-- Check both columns are synced:
-- SELECT id, message, content FROM krai_agent.memory WHERE session_id = 'test-session';
-- Both should show 'Test via message column'
--
-- Test insert with content:
-- INSERT INTO krai_agent.memory (session_id, role, content) 
-- VALUES ('test-session', 'assistant', 'Test via content column');
-- 
-- Check sync:
-- SELECT id, message, content FROM krai_agent.memory WHERE session_id = 'test-session';
-- Both should show 'Test via content column'
-- ============================================
