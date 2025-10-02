-- ============================================
-- Migration: Fix memory role default for n8n
-- Date: 2025-10-02
-- Purpose: n8n sometimes doesn't set role, causing NOT NULL violation
-- ============================================

-- Update trigger to set default role if missing
CREATE OR REPLACE FUNCTION krai_agent.sync_message_content()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure metadata is never NULL
    IF NEW.metadata IS NULL THEN
        NEW.metadata := '{}'::jsonb;
    END IF;
    
    -- Ensure tokens_used is never NULL
    IF NEW.tokens_used IS NULL THEN
        NEW.tokens_used := 0;
    END IF;
    
    -- Ensure role is never NULL (n8n compatibility)
    -- Map n8n's 'human' to 'technician' for service chat
    IF NEW.role IS NULL OR NEW.role = '' THEN
        NEW.role := 'technician';  -- Default for service chat
    ELSIF NEW.role = 'human' THEN
        NEW.role := 'technician';  -- Convert n8n's 'human' to 'technician'
    -- Keep 'ai', 'assistant', etc. as is
    END IF;
    
    -- Sync message and content
    IF NEW.message IS NOT NULL AND NEW.message != '' THEN
        NEW.content := NEW.message;
    ELSIF NEW.content IS NOT NULL AND NEW.content != '' THEN
        NEW.message := NEW.content;
    END IF;
    
    -- Fail if both message and content are empty
    IF (NEW.message IS NULL OR NEW.message = '') AND (NEW.content IS NULL OR NEW.content = '') THEN
        RAISE EXCEPTION 'Either message or content must be provided';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Alternative: Add default value to column
ALTER TABLE krai_agent.memory 
ALTER COLUMN role SET DEFAULT 'technician';

-- ============================================
-- EXPLANATION
-- ============================================
-- n8n Postgres Memory sometimes fails to set role value
-- This causes "null value in column role violates not-null constraint"
--
-- SOLUTION: Automatic role mapping for service technician chat
-- 1. Trigger converts NULL → 'technician'
-- 2. Trigger converts 'human' → 'technician' (n8n default)
-- 3. Column default = 'technician' as fallback
--
-- n8n normally sets:
--   - 'human' → converted to 'technician' (user is a technician)
--   - 'ai' → stays 'ai' (assistant response)
--
-- This way you can track that messages come from service technicians!
-- ============================================

-- VERIFICATION
-- ============================================
-- Test insert without role (should set to 'technician'):
-- INSERT INTO krai_agent.memory (session_id, message) 
-- VALUES ('test-session', 'Test message without role');
-- 
-- Should auto-set role = 'technician':
-- SELECT id, session_id, role, message FROM krai_agent.memory 
-- WHERE session_id = 'test-session';
--
-- Test n8n behavior (should convert 'human' to 'technician'):
-- When n8n inserts with role='human', it gets converted to 'technician'
-- ============================================
