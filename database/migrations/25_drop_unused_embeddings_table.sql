-- ======================================================================
-- Migration 25: Drop Unused Embeddings Table
-- ======================================================================
-- Description: Remove old embeddings table (embeddings are now stored in chunks.embedding column)
-- Date: 2025-10-05
-- Reason: Avoid confusion - embeddings are stored in chunks table, not separate embeddings table
-- ======================================================================

-- Background:
-- Old design (Migration 01): Separate krai_intelligence.embeddings table with FK to chunks
-- New design (Current):      Embeddings stored directly in krai_intelligence.chunks.embedding column
-- 
-- Advantages of new design:
-- - Single table lookup (faster queries)
-- - Atomic updates (chunk + embedding together)
-- - Simpler schema (less joins)
-- - pgvector indexes on chunks table directly

-- Drop the unused embeddings table
DROP TABLE IF EXISTS krai_intelligence.embeddings CASCADE;

-- Verify it's gone
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'krai_intelligence' 
        AND table_name = 'embeddings'
    ) THEN
        RAISE NOTICE '✅ embeddings table successfully dropped';
    ELSE
        RAISE NOTICE '⚠️  embeddings table still exists';
    END IF;
END $$;

-- ======================================================================
-- Verification
-- ======================================================================

-- Confirm embeddings are in chunks table
SELECT 
    'krai_intelligence.chunks' as table_name,
    COUNT(*) as total_chunks,
    COUNT(embedding) as chunks_with_embeddings,
    ROUND(100.0 * COUNT(embedding) / NULLIF(COUNT(*), 0), 2) as embedded_percentage
FROM krai_intelligence.chunks;

-- Expected: 100% of chunks have embeddings
