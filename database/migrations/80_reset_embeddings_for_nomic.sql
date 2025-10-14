-- Migration 80: Reset all embeddings for re-processing with nomic-embed-text
-- This will trigger ChunkProcessor to create new embeddings with the new model
-- NOTE: This is done in batches to avoid timeout

-- Create a function to reset embeddings in batches
CREATE OR REPLACE FUNCTION reset_embeddings_batch()
RETURNS void AS $$
DECLARE
    batch_size INTEGER := 5000;
    updated_count INTEGER;
    total_updated INTEGER := 0;
BEGIN
    LOOP
        -- Update in batches
        UPDATE krai_intelligence.chunks
        SET 
            embedding = NULL,
            processing_status = 'pending',
            updated_at = NOW()
        WHERE id IN (
            SELECT id 
            FROM krai_intelligence.chunks 
            WHERE embedding IS NOT NULL 
            LIMIT batch_size
        );
        
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        total_updated := total_updated + updated_count;
        
        -- Exit if no more rows to update
        EXIT WHEN updated_count = 0;
        
        -- Commit this batch
        COMMIT;
        
        RAISE NOTICE 'Reset % chunks (total: %)', updated_count, total_updated;
    END LOOP;
    
    RAISE NOTICE 'Finished! Total chunks reset: %', total_updated;
END;
$$ LANGUAGE plpgsql;

-- Execute the batch reset
SELECT reset_embeddings_batch();

-- Drop the temporary function
DROP FUNCTION reset_embeddings_batch();
