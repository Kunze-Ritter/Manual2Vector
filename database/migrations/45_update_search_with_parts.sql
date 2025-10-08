-- Migration: Update search function to include parts
-- Date: 2025-10-08
-- Purpose: Add parts to error code search results

DROP FUNCTION IF EXISTS search_error_code_multi_source(TEXT, TEXT, TEXT);

CREATE OR REPLACE FUNCTION search_error_code_multi_source(
  p_error_code TEXT,
  p_manufacturer_name TEXT DEFAULT NULL,
  p_product_name TEXT DEFAULT NULL
)
RETURNS TABLE (
  source_type TEXT,
  source_id UUID,
  source_title TEXT,
  code TEXT,
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
LANGUAGE plpgsql
AS $$
DECLARE
  v_manufacturer_id UUID;
  v_product_id UUID;
BEGIN
  -- Get manufacturer ID
  IF p_manufacturer_name IS NOT NULL THEN
    SELECT id INTO v_manufacturer_id
    FROM krai_core.manufacturers
    WHERE LOWER(name) = LOWER(p_manufacturer_name)
    LIMIT 1;
  END IF;
  
  -- Get product ID
  IF p_product_name IS NOT NULL THEN
    SELECT id INTO v_product_id
    FROM krai_core.products
    WHERE LOWER(model_number) = LOWER(p_product_name)
       OR LOWER(model_name) = LOWER(p_product_name)
    LIMIT 1;
  END IF;
  
  RETURN QUERY
  
  -- 1. Error codes from documents WITH PARTS
  SELECT 
    'document'::TEXT as source_type,
    ec.document_id as source_id,
    d.filename::TEXT as source_title,
    ec.error_code::TEXT as code,
    ec.error_description::TEXT,
    ec.solution_text::TEXT,
    (
      SELECT string_agg(pc.part_number || ' (' || pc.part_name || ')', ', ')
      FROM krai_intelligence.error_code_parts ecp
      JOIN krai_parts.parts_catalog pc ON pc.id = ecp.part_id
      WHERE ecp.error_code_id = ec.id
    )::TEXT as parts_list,
    ec.page_number::INT,
    NULL::TEXT as video_url,
    NULL::INT as video_duration,
    NULL::TEXT as thumbnail_url,
    1.0::FLOAT as relevance_score,
    jsonb_build_object(
      'document_type', d.document_type,
      'confidence', ec.confidence_score,
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
    'video'::TEXT as source_type,
    ec.video_id as source_id,
    v.title::TEXT as source_title,
    ec.error_code::TEXT as code,
    ec.error_description::TEXT,
    ec.solution_text::TEXT,
    NULL::TEXT as parts_list,
    NULL::INT as page_number,
    v.video_url::TEXT,
    v.duration::INT as video_duration,
    v.thumbnail_url::TEXT,
    1.0::FLOAT as relevance_score,
    jsonb_build_object(
      'video_platform', v.platform,
      'confidence', ec.confidence_score
    ) as metadata
  FROM krai_intelligence.error_codes ec
  JOIN krai_content.videos v ON v.id = ec.video_id
  WHERE ec.error_code = p_error_code
    AND (v_manufacturer_id IS NULL OR ec.manufacturer_id = v_manufacturer_id)
    AND (v_product_id IS NULL OR ec.product_id = v_product_id)
    AND ec.video_id IS NOT NULL
  
  UNION ALL
  
  -- 3. Related videos (keyword matching)
  SELECT 
    'related_video'::TEXT as source_type,
    v.id as source_id,
    v.title::TEXT as source_title,
    p_error_code::TEXT as code,
    v.description::TEXT as error_description,
    NULL::TEXT as solution_text,
    NULL::TEXT as parts_list,
    NULL::INT as page_number,
    v.video_url::TEXT,
    v.duration::INT as video_duration,
    v.thumbnail_url::TEXT,
    0.7::FLOAT as relevance_score,
    jsonb_build_object(
      'video_platform', v.platform,
      'match_type', 'keyword'
    ) as metadata
  FROM krai_content.videos v
  WHERE (
    v.title ILIKE '%' || p_error_code || '%'
    OR v.description ILIKE '%' || p_error_code || '%'
    OR v.tags::TEXT ILIKE '%' || p_error_code || '%'
  )
  AND (v_manufacturer_id IS NULL OR v.manufacturer_id = v_manufacturer_id)
  AND NOT EXISTS (
    SELECT 1 FROM krai_intelligence.error_codes ec2
    WHERE ec2.video_id = v.id AND ec2.error_code = p_error_code
  )
  LIMIT 5;
  
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO authenticated;
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO anon;
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO service_role;

COMMENT ON FUNCTION search_error_code_multi_source IS 'Search error codes across documents and videos with parts information';
