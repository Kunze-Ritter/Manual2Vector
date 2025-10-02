-- ============================================
-- Migration: Expand memory role constraint for flexible usage
-- Date: 2025-10-02
-- Purpose: Support n8n and custom role values (technician, engineer, etc.)
-- ============================================

-- Drop old constraint (only allowed: user, assistant, system, function, tool)
ALTER TABLE krai_agent.memory 
DROP CONSTRAINT IF EXISTS memory_role_check;

-- Add expanded constraint with all common role values
ALTER TABLE krai_agent.memory
ADD CONSTRAINT memory_role_check 
CHECK (role IN (
    -- Standard AI/LLM roles
    'user',         -- Standard user message
    'assistant',    -- Standard AI response
    'system',       -- System prompt
    'function',     -- Function call result
    'tool',         -- Tool call result
    
    -- n8n AI Agent roles
    'ai',           -- n8n AI Agent response
    'human',        -- n8n Human/User message
    'chatbot',      -- Alternative AI naming
    
    -- Custom business roles (KRAI specific)
    'technician',   -- Techniker/Service-Mitarbeiter
    'engineer',     -- Ingenieur
    'manager',      -- Manager/Vorgesetzter
    'supervisor',   -- Supervisor/Teamleiter
    'customer',     -- Kunde/Endnutzer
    'support',      -- Support-Team
    'expert'        -- Fachexperte
));

-- ============================================
-- ROLE DOCUMENTATION
-- ============================================
-- Standard AI Roles:
--   - user:      Human user input
--   - assistant: AI model response
--   - system:    System prompts/instructions
--   - function:  Function execution results
--   - tool:      Tool execution results
--
-- n8n Compatibility:
--   - ai:        n8n AI Agent (equivalent to 'assistant')
--   - human:     n8n User (equivalent to 'user')
--   - chatbot:   Alternative AI agent naming
--
-- Business Roles (KRAI):
--   - technician: Service technician/field engineer
--   - engineer:   Technical engineer/specialist
--   - manager:    Manager/supervisor
--   - supervisor: Team lead/supervisor
--   - customer:   End customer/user
--   - support:    Support team member
--   - expert:     Subject matter expert
--
-- Usage in n8n:
--   Set role field to appropriate value based on context
--   Example: 'technician' for service technician queries
-- ============================================

-- VERIFICATION TESTS
-- ============================================
-- Test standard roles:
-- INSERT INTO krai_agent.memory (session_id, role, content) 
-- VALUES ('test-session', 'user', 'Test user message');

-- Test n8n roles:
-- INSERT INTO krai_agent.memory (session_id, role, content) 
-- VALUES ('test-session', 'ai', 'Test AI response');

-- Test custom roles:
-- INSERT INTO krai_agent.memory (session_id, role, content) 
-- VALUES ('test-session', 'technician', 'Technician query');

-- Verify constraint works:
-- SELECT DISTINCT role FROM krai_agent.memory ORDER BY role;
-- ============================================
