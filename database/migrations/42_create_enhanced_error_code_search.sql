-- Migration: Enhanced Error Code Search with Video Support
-- Date: 2025-01-07
-- Purpose: Search error codes across documents and videos with keyword matching

CREATE OR REPLACE FUNCTION search_error_code_multi_source(
  p_error_code TEXT,
  p_manufacturer_name TEXT DEFAULT NULL,
  p_product_name TEXT DEFAULT NULL
)
RETURNS TABLE (
  source_type TEXT,
  source_id UUID,
  source_title TEXT,
  error_code TEXT,
  error_description TEXT,
  solution_text TEXT,
  parts_list TEXT,
  page_number INT,
  video_url TEXT,
  video_duration INT,
  thumbnail_url TEXT,
  relevance_score FLOAT,
  metadata JSONB
)
AS $$
DECLARE
  v_manufacturer_id UUID;
  v_product_id UUID;
BEGIN
  -- Get manufacturer ID
  IF p_manufacturer_name IS NOT NULL THEN
    SELECT id INTO v_manufacturer_id 
    FROM krai_core.manufacturers 
    WHERE name ILIKE p_manufacturer_name 
    LIMIT 1;
  END IF;
  
  -- Get product ID
  IF p_product_name IS NOT NULL THEN
    SELECT id INTO v_product_id 
    FROM krai_core.products 
    WHERE model_number ILIKE p_product_name
    LIMIT 1;
  END IF;
  
  RETURN QUERY
  
  -- 1. Error codes from documents
  SELECT 
    'document'::TEXT as source_type,
    ec.document_id as source_id,
    d.filename as source_title,
    ec.error_code,
    ec.error_description,
    ec.solution_text,
    array_to_string(ec.parts_referenced, ', ')::TEXT as parts_list,
    ec.page_number,
    NULL::TEXT as video_url,
    NULL::INT as video_duration,
    NULL::TEXT as thumbnail_url,
    1.0::FLOAT as relevance_score,
    jsonb_build_object(
      'document_type', d.document_type,
      'confidence', ec.confidence,
      'chunk_id', ec.chunk_id
    ) as metadata
  FROM krai_intelligence.error_codes ec
  JOIN krai_core.documents d ON d.id = ec.document_id
  WHERE ec.error_code = p_error_code
    AND (v_manufacturer_id IS NULL OR ec.manufacturer_id = v_manufacturer_id)
    AND (v_product_id IS NULL OR ec.product_id = v_product_id)
    AND ec.document_id IS NOT NULL
  
  UNION ALL
  
  -- 2. Error codes from videos (direct match)
  SELECT 
    'video'::TEXT,
    ec.video_id,
    v.title,
    ec.error_code,
    ec.error_description,
    ec.solution_text,
    array_to_string(ec.parts_referenced, ', ')::TEXT,
    NULL::INT,
    v.video_url,
    v.duration,
    v.thumbnail_url,
    1.0::FLOAT,
    jsonb_build_object(
      'platform', v.platform,
      'channel_title', v.channel_title,
      'view_count', v.view_count,
      'confidence', ec.confidence
    )
  FROM krai_intelligence.error_codes ec
  JOIN krai_content.videos v ON v.id = ec.video_id
  WHERE ec.error_code = p_error_code
    AND (v_manufacturer_id IS NULL OR ec.manufacturer_id = v_manufacturer_id)
    AND (v_product_id IS NULL OR ec.product_id = v_product_id)
    AND ec.video_id IS NOT NULL
  
  UNION ALL
  
  -- 3. Related videos (keyword match - no direct error code link)
  SELECT 
    'related_video'::TEXT,
    v.id,
    v.title,
    p_error_code::TEXT,
    NULL::TEXT,
    v.description,
    NULL::TEXT,
    NULL::INT,
    v.video_url,
    v.duration,
    v.thumbnail_url,
    0.7::FLOAT,  -- Lower relevance
    jsonb_build_object(
      'platform', v.platform,
      'channel_title', v.channel_title,
      'view_count', v.view_count,
      'match_type', 'keyword'
    )
  FROM krai_content.videos v
  WHERE (v_manufacturer_id IS NULL OR v.manufacturer_id = v_manufacturer_id)
    AND (v_product_id IS NULL OR v.id IN (
      SELECT vp.video_id FROM krai_content.video_products vp 
      WHERE vp.product_id = v_product_id
    ))
    AND (
      v.description ILIKE '%' || p_error_code || '%' OR
      v.metadata::TEXT ILIKE '%' || p_error_code || '%'
    )
    AND v.id NOT IN (
      -- Exclude videos already in error_codes
      SELECT video_id FROM krai_intelligence.error_codes 
      WHERE error_code = p_error_code 
        AND video_id IS NOT NULL
    )
  
  ORDER BY relevance_score DESC, source_type;
END;
$$ LANGUAGE plpgsql;
-- Grant permissions
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO authenticated;
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO anon;
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO service_role;

-- Example usage:
-- SELECT * FROM search_error_code_multi_source('30.03.30', 'HP', 'X580');
