-- ===========================================
-- PUBLIC VIEWS FOR POSTGREST ACCESS
-- ===========================================
-- PostgREST kann nur auf 'public' Schema zugreifen
-- Diese Views machen krai_content/krai_intelligence im public Schema verfügbar

-- Drop existing views if any
DROP VIEW IF EXISTS public.vw_images CASCADE;
DROP VIEW IF EXISTS public.vw_chunks CASCADE;
DROP VIEW IF EXISTS public.vw_embeddings CASCADE;

-- View for krai_content.images
CREATE OR REPLACE VIEW public.vw_images AS
SELECT 
    id,
    document_id,
    chunk_id,
    filename,
    original_filename,
    storage_path,
    storage_url,
    file_size,
    image_format,
    width_px,
    height_px,
    page_number,
    image_index,
    image_type,
    ai_description,
    ai_confidence,
    contains_text,
    ocr_text,
    ocr_confidence,
    manual_description,
    tags,
    file_hash,
    created_at,
    updated_at,
    figure_number,
    figure_context
FROM krai_content.images;

-- View for krai_content.chunks
CREATE OR REPLACE VIEW public.vw_chunks AS
SELECT 
    id,
    document_id,
    chunk_text,
    chunk_index,
    page_number,
    chunk_metadata,
    created_at,
    updated_at
FROM krai_content.chunks;

-- View for krai_intelligence.embeddings
CREATE OR REPLACE VIEW public.vw_embeddings AS
SELECT 
    id,
    chunk_id,
    embedding_model,
    embedding_vector,
    embedding_dimensions,
    created_at
FROM krai_intelligence.embeddings;

-- Grant access to anon and authenticated users
GRANT SELECT ON public.vw_images TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_chunks TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_embeddings TO anon, authenticated, service_role;

-- Comments for documentation
COMMENT ON VIEW public.vw_images IS 'Read-only view of krai_content.images for PostgREST access (IPv4 compatible)';
COMMENT ON VIEW public.vw_chunks IS 'Read-only view of krai_content.chunks for PostgREST access (IPv4 compatible)';
COMMENT ON VIEW public.vw_embeddings IS 'Read-only view of krai_intelligence.embeddings for PostgREST access (IPv4 compatible)';
