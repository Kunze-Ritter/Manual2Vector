-- ======================================================================
-- 🔧 MIGRATION 10: Per-Stage Status Tracking
-- ======================================================================
-- Purpose: Track status, progress, and errors for each processing stage
--          individually to enable parallel processing and better monitoring
-- ======================================================================

BEGIN;

-- ======================================================================
-- STEP 1: Add stage_status JSONB column to documents table
-- ======================================================================

ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS stage_status JSONB DEFAULT '{
  "upload": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "text_extraction": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "image_processing": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "classification": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "metadata_extraction": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "storage": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "embedding": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  },
  "search_indexing": {
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "duration_seconds": null,
    "progress": 0,
    "error": null,
    "metadata": {}
  }
}'::JSONB;

-- Create index for faster JSONB queries
CREATE INDEX IF NOT EXISTS idx_documents_stage_status 
ON krai_core.documents USING GIN (stage_status);

-- ======================================================================
-- STEP 2: Helper Functions for Stage Status Management
-- ======================================================================

-- Function: Start a stage
CREATE OR REPLACE FUNCTION krai_core.start_stage(
    p_document_id UUID,
    p_stage_name TEXT
) RETURNS VOID AS $$
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
CREATE OR REPLACE FUNCTION krai_core.update_stage_progress(
    p_document_id UUID,
    p_stage_name TEXT,
    p_progress NUMERIC,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS VOID AS $$
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
CREATE OR REPLACE FUNCTION krai_core.complete_stage(
    p_document_id UUID,
    p_stage_name TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS VOID AS $$
DECLARE
    v_started_at TIMESTAMP;
    v_duration NUMERIC;
BEGIN
    -- Get started_at timestamp
    SELECT (stage_status->p_stage_name->>'started_at')::TIMESTAMP
    INTO v_started_at
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    -- Calculate duration
    IF v_started_at IS NOT NULL THEN
        v_duration := EXTRACT(EPOCH FROM (NOW() - v_started_at));
    ELSE
        v_duration := 0;
    END IF;
    
    -- Update status
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
CREATE OR REPLACE FUNCTION krai_core.fail_stage(
    p_document_id UUID,
    p_stage_name TEXT,
    p_error TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS VOID AS $$
DECLARE
    v_started_at TIMESTAMP;
    v_duration NUMERIC;
BEGIN
    -- Get started_at timestamp
    SELECT (stage_status->p_stage_name->>'started_at')::TIMESTAMP
    INTO v_started_at
    FROM krai_core.documents
    WHERE id = p_document_id;
    
    -- Calculate duration
    IF v_started_at IS NOT NULL THEN
        v_duration := EXTRACT(EPOCH FROM (NOW() - v_started_at));
    ELSE
        v_duration := 0;
    END IF;
    
    -- Update status
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
CREATE OR REPLACE FUNCTION krai_core.skip_stage(
    p_document_id UUID,
    p_stage_name TEXT,
    p_reason TEXT DEFAULT 'Not applicable'
) RETURNS VOID AS $$
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

-- Function: Get overall progress (percentage of completed stages)
CREATE OR REPLACE FUNCTION krai_core.get_document_progress(
    p_document_id UUID
) RETURNS NUMERIC AS $$
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
    
    -- Count completed stages
    SELECT COUNT(*) INTO v_completed_stages
    FROM jsonb_each(v_stage_status) AS stages
    WHERE stages.value->>'status' = 'completed';
    
    RETURN (v_completed_stages::NUMERIC / v_total_stages::NUMERIC * 100)::NUMERIC(5,2);
END;
$$ LANGUAGE plpgsql;

-- Function: Get current stage (first non-completed stage)
CREATE OR REPLACE FUNCTION krai_core.get_current_stage(
    p_document_id UUID
) RETURNS TEXT AS $$
DECLARE
    v_stage_status JSONB;
    v_stage_order TEXT[] := ARRAY[
        'upload', 
        'text_extraction', 
        'image_processing', 
        'classification', 
        'metadata_extraction', 
        'storage', 
        'embedding', 
        'search_indexing'
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
    
    -- Find first non-completed stage
    FOREACH v_stage IN ARRAY v_stage_order
    LOOP
        v_status := v_stage_status->v_stage->>'status';
        
        IF v_status IN ('pending', 'processing', 'failed') THEN
            RETURN v_stage;
        END IF;
    END LOOP;
    
    -- All stages completed
    RETURN 'completed';
END;
$$ LANGUAGE plpgsql;

-- Function: Check if document can start a stage (all prerequisites completed)
CREATE OR REPLACE FUNCTION krai_core.can_start_stage(
    p_document_id UUID,
    p_stage_name TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_stage_status JSONB;
    v_stage_order TEXT[] := ARRAY[
        'upload', 
        'text_extraction', 
        'image_processing', 
        'classification', 
        'metadata_extraction', 
        'storage', 
        'embedding', 
        'search_indexing'
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
    
    -- Find stage index
    v_stage_index := array_position(v_stage_order, p_stage_name);
    
    IF v_stage_index IS NULL OR v_stage_index = 1 THEN
        RETURN TRUE; -- Upload can always start
    END IF;
    
    -- Check if previous stage is completed or skipped
    v_prev_stage := v_stage_order[v_stage_index - 1];
    v_prev_status := v_stage_status->v_prev_stage->>'status';
    
    RETURN v_prev_status IN ('completed', 'skipped');
END;
$$ LANGUAGE plpgsql;

-- ======================================================================
-- STEP 3: Views for Monitoring
-- ======================================================================

-- View: Documents by stage status
CREATE OR REPLACE VIEW krai_core.vw_documents_by_stage AS
SELECT 
    d.id,
    d.filename,
    d.processing_status,
    krai_core.get_current_stage(d.id) as current_stage,
    krai_core.get_document_progress(d.id) as progress_percentage,
    d.stage_status->>'upload' as upload_status,
    d.stage_status->>'text_extraction' as text_extraction_status,
    d.stage_status->>'image_processing' as image_processing_status,
    d.stage_status->>'classification' as classification_status,
    d.stage_status->>'metadata_extraction' as metadata_extraction_status,
    d.stage_status->>'storage' as storage_status,
    d.stage_status->>'embedding' as embedding_status,
    d.stage_status->>'search_indexing' as search_indexing_status,
    d.created_at,
    d.updated_at
FROM krai_core.documents d;

-- View: Stage statistics
CREATE OR REPLACE VIEW krai_core.vw_stage_statistics AS
SELECT 
    stage_name,
    COUNT(*) FILTER (WHERE stage_data->>'status' = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE stage_data->>'status' = 'processing') as processing_count,
    COUNT(*) FILTER (WHERE stage_data->>'status' = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE stage_data->>'status' = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE stage_data->>'status' = 'skipped') as skipped_count,
    AVG((stage_data->>'duration_seconds')::NUMERIC) FILTER (WHERE stage_data->>'status' = 'completed') as avg_duration_seconds
FROM (
    SELECT 
        stages.key as stage_name,
        stages.value as stage_data
    FROM 
        krai_core.documents,
        jsonb_each(stage_status) as stages
) subquery
GROUP BY stage_name;

COMMIT;

-- ======================================================================
-- Example Usage:
-- ======================================================================
-- 
-- Start a stage:
--   SELECT krai_core.start_stage('document-uuid', 'text_extraction');
--
-- Update progress:
--   SELECT krai_core.update_stage_progress(
--     'document-uuid', 
--     'text_extraction', 
--     45.5, 
--     '{"pages_processed": 2000}'::JSONB
--   );
--
-- Complete a stage:
--   SELECT krai_core.complete_stage(
--     'document-uuid', 
--     'text_extraction',
--     '{"total_pages": 4386}'::JSONB
--   );
--
-- Fail a stage:
--   SELECT krai_core.fail_stage(
--     'document-uuid', 
--     'text_extraction',
--     'OCR engine timeout'
--   );
--
-- Get current progress:
--   SELECT krai_core.get_document_progress('document-uuid');
--
-- Get current stage:
--   SELECT krai_core.get_current_stage('document-uuid');
--
-- Check if can start stage:
--   SELECT krai_core.can_start_stage('document-uuid', 'embedding');
--
-- View all documents with stage status:
--   SELECT * FROM krai_core.vw_documents_by_stage;
--
-- View stage statistics:
--   SELECT * FROM krai_core.vw_stage_statistics;
-- ======================================================================
