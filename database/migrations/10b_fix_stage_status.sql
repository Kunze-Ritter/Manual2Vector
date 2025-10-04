-- ======================================================================
-- 🔧 MIGRATION 10b: Fix Stage Status (Add to correct schema)
-- ======================================================================
-- Fix: Add stage_status column to documents table in correct schema
-- ======================================================================

BEGIN;

-- First, let's check and add to public.documents if it exists there
ALTER TABLE public.documents
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

-- Create index on public.documents
CREATE INDEX IF NOT EXISTS idx_documents_stage_status 
ON public.documents USING GIN (stage_status);

-- Update helper functions to use public schema if krai_core doesn't exist
-- Or create wrapper functions

COMMIT;

-- Note: If your documents table is in a different schema,
-- replace 'public' with your schema name above.
