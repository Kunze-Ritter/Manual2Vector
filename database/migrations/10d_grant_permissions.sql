-- ======================================================================
-- 🔧 MIGRATION 10d: Grant Permissions & Add SECURITY DEFINER
-- ======================================================================
-- Fix: Add SECURITY DEFINER to functions so they run with owner privileges
-- ======================================================================

BEGIN;

-- Drop existing functions
DROP FUNCTION IF EXISTS public.start_stage(UUID, TEXT);
DROP FUNCTION IF EXISTS public.update_stage_progress(UUID, TEXT, NUMERIC, JSONB);
DROP FUNCTION IF EXISTS public.complete_stage(UUID, TEXT, JSONB);
DROP FUNCTION IF EXISTS public.fail_stage(UUID, TEXT, TEXT, JSONB);
DROP FUNCTION IF EXISTS public.skip_stage(UUID, TEXT, TEXT);
DROP FUNCTION IF EXISTS public.get_document_progress(UUID);
DROP FUNCTION IF EXISTS public.get_current_stage(UUID);
DROP FUNCTION IF EXISTS public.can_start_stage(UUID, TEXT);

-- Recreate with SECURITY DEFINER

-- Function: Start a stage
CREATE OR REPLACE FUNCTION public.start_stage(
    p_document_id UUID,
    p_stage_name TEXT
) RETURNS VOID 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
BEGIN
    UPDATE krai_core.documents
    SET 
        stage_status = jsonb_set(
            jsonb_set(
                stage_status,
                ARRAY[p_stage_name, 'status'],
                '"processing"'
            ),
            ARRAY[p_stage_name, 'started_at'],
            to_jsonb(NOW()::TEXT)
        ),
        updated_at = NOW()
    WHERE id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Update stage progress
CREATE OR REPLACE FUNCTION public.update_stage_progress(
    p_document_id UUID,
    p_stage_name TEXT,
    p_progress NUMERIC,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS VOID 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
BEGIN
    UPDATE krai_core.documents
    SET 
        stage_status = jsonb_set(
            jsonb_set(
                stage_status,
                ARRAY[p_stage_name, 'progress'],
                to_jsonb(p_progress)
            ),
            ARRAY[p_stage_name, 'metadata'],
            p_metadata
        ),
        updated_at = NOW()
    WHERE id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Complete a stage
CREATE OR REPLACE FUNCTION public.complete_stage(
    p_document_id UUID,
    p_stage_name TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS VOID 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
DECLARE
    v_started_at TIMESTAMP;
    v_duration NUMERIC;
BEGIN
    SELECT (stage_status->p_stage_name->>'started_at')::TIMESTAMP
    INTO v_started_at
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    IF v_started_at IS NOT NULL THEN
        v_duration := EXTRACT(EPOCH FROM (NOW() - v_started_at));
    ELSE
        v_duration := 0;
    END IF;
    
    UPDATE krai_core.documents
    SET 
        stage_status = jsonb_set(
            jsonb_set(
                jsonb_set(
                    jsonb_set(
                        jsonb_set(
                            stage_status,
                            ARRAY[p_stage_name, 'status'],
                            '"completed"'
                        ),
                        ARRAY[p_stage_name, 'completed_at'],
                        to_jsonb(NOW()::TEXT)
                    ),
                    ARRAY[p_stage_name, 'duration_seconds'],
                    to_jsonb(v_duration)
                ),
                ARRAY[p_stage_name, 'progress'],
                '100'
            ),
            ARRAY[p_stage_name, 'metadata'],
            p_metadata
        ),
        updated_at = NOW()
    WHERE id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Fail a stage
CREATE OR REPLACE FUNCTION public.fail_stage(
    p_document_id UUID,
    p_stage_name TEXT,
    p_error TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS VOID 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
DECLARE
    v_started_at TIMESTAMP;
    v_duration NUMERIC;
BEGIN
    SELECT (stage_status->p_stage_name->>'started_at')::TIMESTAMP
    INTO v_started_at
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    IF v_started_at IS NOT NULL THEN
        v_duration := EXTRACT(EPOCH FROM (NOW() - v_started_at));
    ELSE
        v_duration := 0;
    END IF;
    
    UPDATE krai_core.documents
    SET 
        stage_status = jsonb_set(
            jsonb_set(
                jsonb_set(
                    jsonb_set(
                        jsonb_set(
                            stage_status,
                            ARRAY[p_stage_name, 'status'],
                            '"failed"'
                        ),
                        ARRAY[p_stage_name, 'completed_at'],
                        to_jsonb(NOW()::TEXT)
                    ),
                    ARRAY[p_stage_name, 'duration_seconds'],
                    to_jsonb(v_duration)
                ),
                ARRAY[p_stage_name, 'error'],
                to_jsonb(p_error)
            ),
            ARRAY[p_stage_name, 'metadata'],
            p_metadata
        ),
        processing_status = 'failed',
        updated_at = NOW()
    WHERE id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Skip a stage
CREATE OR REPLACE FUNCTION public.skip_stage(
    p_document_id UUID,
    p_stage_name TEXT,
    p_reason TEXT DEFAULT 'Not applicable'
) RETURNS VOID 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
BEGIN
    UPDATE krai_core.documents
    SET 
        stage_status = jsonb_set(
            jsonb_set(
                jsonb_set(
                    stage_status,
                    ARRAY[p_stage_name, 'status'],
                    '"skipped"'
                ),
                ARRAY[p_stage_name, 'completed_at'],
                to_jsonb(NOW()::TEXT)
            ),
            ARRAY[p_stage_name, 'metadata'],
            jsonb_build_object('reason', p_reason)
        ),
        updated_at = NOW()
    WHERE id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get overall progress
CREATE OR REPLACE FUNCTION public.get_document_progress(
    p_document_id UUID
) RETURNS NUMERIC 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
DECLARE
    v_stage_status JSONB;
    v_total_stages INTEGER := 8;
    v_completed_stages INTEGER := 0;
BEGIN
    SELECT stage_status INTO v_stage_status
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    IF v_stage_status IS NULL THEN
        RETURN 0;
    END IF;
    
    SELECT COUNT(*) INTO v_completed_stages
    FROM jsonb_each(v_stage_status) AS stages
    WHERE stages.value->>'status' = 'completed';
    
    RETURN (v_completed_stages::NUMERIC / v_total_stages::NUMERIC * 100)::NUMERIC(5,2);
END;
$$ LANGUAGE plpgsql;

-- Function: Get current stage
CREATE OR REPLACE FUNCTION public.get_current_stage(
    p_document_id UUID
) RETURNS TEXT 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
DECLARE
    v_stage_status JSONB;
    v_stage_order TEXT[] := ARRAY[
        'upload', 'text_extraction', 'image_processing', 'classification',
        'metadata_extraction', 'storage', 'embedding', 'search_indexing'
    ];
    v_stage TEXT;
    v_status TEXT;
BEGIN
    SELECT stage_status INTO v_stage_status
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    IF v_stage_status IS NULL THEN
        RETURN 'upload';
    END IF;
    
    FOREACH v_stage IN ARRAY v_stage_order
    LOOP
        v_status := v_stage_status->v_stage->>'status';
        
        IF v_status IN ('pending', 'processing', 'failed') THEN
            RETURN v_stage;
        END IF;
    END LOOP;
    
    RETURN 'completed';
END;
$$ LANGUAGE plpgsql;

-- Function: Check if document can start a stage
CREATE OR REPLACE FUNCTION public.can_start_stage(
    p_document_id UUID,
    p_stage_name TEXT
) RETURNS BOOLEAN 
SECURITY DEFINER
SET search_path = public, krai_core
AS $$
DECLARE
    v_stage_status JSONB;
    v_stage_order TEXT[] := ARRAY[
        'upload', 'text_extraction', 'image_processing', 'classification',
        'metadata_extraction', 'storage', 'embedding', 'search_indexing'
    ];
    v_stage_index INTEGER;
    v_prev_stage TEXT;
    v_prev_status TEXT;
BEGIN
    SELECT stage_status INTO v_stage_status
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    IF v_stage_status IS NULL THEN
        RETURN FALSE;
    END IF;
    
    v_stage_index := array_position(v_stage_order, p_stage_name);
    
    IF v_stage_index IS NULL OR v_stage_index = 1 THEN
        RETURN TRUE;
    END IF;
    
    v_prev_stage := v_stage_order[v_stage_index - 1];
    v_prev_status := v_stage_status->v_prev_stage->>'status';
    
    RETURN v_prev_status IN ('completed', 'skipped');
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION public.start_stage(UUID, TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.update_stage_progress(UUID, TEXT, NUMERIC, JSONB) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.complete_stage(UUID, TEXT, JSONB) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.fail_stage(UUID, TEXT, TEXT, JSONB) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.skip_stage(UUID, TEXT, TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.get_document_progress(UUID) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.get_current_stage(UUID) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.can_start_stage(UUID, TEXT) TO authenticated, anon;

COMMIT;
