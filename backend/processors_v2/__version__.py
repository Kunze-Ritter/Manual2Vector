"""
Version Information for KRAI Processing Pipeline
Auto-updated with each significant release
"""

__version__ = "2.0.41"
__commit__ = "TBD"
__date__ = "2025-10-05"

# Version History:
# 2.0.41 (TBD) - Fix: ULTIMATE - Use RPC Function to bypass PostgREST cache!
# 2.0.40 (ad934a4) - Fix: DROP + RECREATE columns to reset PostgREST cache!
# 2.0.39 (4445d62) - Fix: ONLY use BASE SCHEMA - PostgREST cache broken for Migration 09 columns
# 2.0.38 (803eec1) - Fix: Remove ai_extracted field (Supabase cache issue)
# 2.0.37 (c745775) - Feat: SMART image matching via Vision AI descriptions!
# 2.0.36 (1cc51e7) - Feat: Link error codes to chunks & images (N8N Agent integration!)
# 2.0.35 (71ca96e) - Feat: Re-add metadata + context_text + ai_extracted fields
# 2.0.34 (b2a4763) - Fix: Remove metadata field - column doesn't exist in schema
# 2.0.33 (53dcb99) - Fix: Schema mismatch - documents.manufacturer not manufacturer_id
# 2.0.32 (a1ec31f) - Feat: Save error codes IMMEDIATELY after extraction (no waiting!)
# 2.0.31 (96582f0) - Feat: Version tracking + banner
# 2.0.30 (ac6c400) - Fix: Error codes manufacturer_id + severity_level
# 2.0.29 (9ef0e2b) - Feat: Auto-link images to chunks after embedding
# 2.0.28 (b027d40) - Fix: Images chunk_id FK to krai_intelligence.chunks
# 2.0.27 (d4f5776) - Fix: CRITICAL - Preserve chunk metadata in embedding
# 2.0.26 (8ce7054) - Fix: Handle .pdfz files (uncompressed PDFs)
# 2.0.25 (524c066) - Fix: HP header detection + URL product extraction
