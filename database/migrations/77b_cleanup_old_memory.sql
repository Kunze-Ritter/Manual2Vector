-- ============================================================================
-- Migration 77b: Cleanup Old Memory Data
-- ============================================================================
-- Purpose: Fix existing memory entries with wrong/missing types
-- Date: 2025-10-11
-- ============================================================================

-- Option 1: Delete all old memory (clean slate)
-- Uncomment if you want to start fresh:
DELETE FROM krai_agent.memory;

-- Option 2: Fix existing entries (migrate data)
-- Update NULL or invalid roles to 'user'
UPDATE krai_agent.memory
SET role = 'user'
WHERE role IS NULL 
   OR role NOT IN ('user', 'assistant', 'system', 'tool', 'function');

-- Update empty content
UPDATE krai_agent.memory
SET content = '[Empty message]'
WHERE content IS NULL OR content = '';

-- Show what we have now
SELECT 
    session_id,
    role,
    LEFT(content, 50) as content_preview,
    created_at
FROM krai_agent.memory
ORDER BY created_at DESC
LIMIT 10;

-- Done!
SELECT 'Memory data cleaned!' as status;
