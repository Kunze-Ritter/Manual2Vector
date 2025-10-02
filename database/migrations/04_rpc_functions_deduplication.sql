-- ======================================================================
-- RPC FUNCTIONS FOR CROSS-SCHEMA DEDUPLICATION
-- ======================================================================
-- These functions allow Supabase PostgREST to access tables in different schemas
-- Needed because PostgREST can't directly query krai_content.images.file_hash

-- Function to get image by file_hash (for deduplication)
CREATE OR REPLACE FUNCTION get_image_by_hash(p_file_hash VARCHAR)
RETURNS TABLE (
    id UUID,
    filename VARCHAR,
    file_hash VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE,
    document_id UUID,
    storage_url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.filename,
        i.file_hash,
        i.created_at,
        i.document_id,
        i.storage_url
    FROM krai_content.images i
    WHERE i.file_hash = p_file_hash
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to count images by document (for stage detection)
CREATE OR REPLACE FUNCTION count_images_by_document(p_document_id UUID)
RETURNS INTEGER AS $$
DECLARE
    image_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO image_count
    FROM krai_content.images
    WHERE document_id = p_document_id;
    
    RETURN image_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to count chunks by document (for stage detection)
CREATE OR REPLACE FUNCTION count_chunks_by_document(p_document_id UUID)
RETURNS INTEGER AS $$
DECLARE
    chunk_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO chunk_count
    FROM krai_intelligence.chunks
    WHERE document_id = p_document_id;
    
    RETURN chunk_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get chunk IDs for embeddings check
CREATE OR REPLACE FUNCTION get_chunk_ids_by_document(p_document_id UUID, p_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    chunk_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT id
    FROM krai_intelligence.chunks
    WHERE document_id = p_document_id
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if embeddings exist for chunks
CREATE OR REPLACE FUNCTION embeddings_exist_for_chunks(p_chunk_ids UUID[])
RETURNS BOOLEAN AS $$
DECLARE
    embedding_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO embedding_count
    FROM krai_intelligence.embeddings
    WHERE chunk_id = ANY(p_chunk_ids);
    
    RETURN embedding_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions to service role
GRANT EXECUTE ON FUNCTION get_image_by_hash(VARCHAR) TO service_role;
GRANT EXECUTE ON FUNCTION count_images_by_document(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION count_chunks_by_document(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION get_chunk_ids_by_document(UUID, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION embeddings_exist_for_chunks(UUID[]) TO service_role;

-- Grant execute permissions to authenticated users (if needed)
GRANT EXECUTE ON FUNCTION get_image_by_hash(VARCHAR) TO authenticated;
GRANT EXECUTE ON FUNCTION count_images_by_document(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION count_chunks_by_document(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_chunk_ids_by_document(UUID, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION embeddings_exist_for_chunks(UUID[]) TO authenticated;

-- Comments for documentation
COMMENT ON FUNCTION get_image_by_hash IS 'Get image by file_hash for deduplication - works across krai_content schema';
COMMENT ON FUNCTION count_images_by_document IS 'Count images for a document - used for stage detection';
COMMENT ON FUNCTION count_chunks_by_document IS 'Count chunks for a document - used for stage detection';
COMMENT ON FUNCTION get_chunk_ids_by_document IS 'Get chunk IDs for a document - used for embeddings check';
COMMENT ON FUNCTION embeddings_exist_for_chunks IS 'Check if embeddings exist for given chunk IDs';
