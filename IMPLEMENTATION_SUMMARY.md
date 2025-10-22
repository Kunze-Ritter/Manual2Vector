# Implementation Summary - chunk_id Verknüpfung

## ✅ Was wurde implementiert:

### 1. Model Update ✅
**Datei:** `backend/processors/models.py`
- `chunk_id: Optional[str] = None` zu `ExtractedErrorCode` hinzugefügt

### 2. Chunk-Finder Funktion ✅
**Datei:** `backend/processors/error_code_extractor.py`
- `find_chunk_for_error_code()` Funktion hinzugefügt
- Strategie: Sucht Chunk auf gleicher Seite, dann beliebiger Chunk

### 3. Was noch fehlt:

#### A. Enrichment Update
**Datei:** `backend/processors/error_code_extractor.py`

In `enrich_error_codes_from_document()` nach dem Enrichment:

```python
# Nach Zeile ~270 (nach chunk_results query):
from backend.processors.error_code_extractor import find_chunk_for_error_code

# Für jeden enriched error code:
for error_code in codes_needing_enrichment:
    if chunk_results.data:
        chunk_id = find_chunk_for_error_code(
            error_code=error_code.error_code,
            page_number=error_code.page_number,
            chunks=chunk_results.data,
            logger=self.logger
        )
        if chunk_id:
            error_code.chunk_id = chunk_id
            self.logger.debug(f"Linked {error_code.error_code} to chunk {chunk_id}")
```

#### B. Master Pipeline Update
**Datei:** `backend/processors/master_pipeline.py`

In `_save_error_codes()` Zeile ~466:

```python
ec_data = error_code if isinstance(error_code, dict) else {
    'error_code': getattr(error_code, 'error_code', ''),
    'error_description': getattr(error_code, 'error_description', ''),
    'solution_text': getattr(error_code, 'solution_text', None),
    'confidence': getattr(error_code, 'confidence', 0.0),
    'page_number': getattr(error_code, 'page_number', None),
    'context_text': getattr(error_code, 'context_text', None),
    'severity_level': getattr(error_code, 'severity_level', 'medium'),
    'requires_technician': getattr(error_code, 'requires_technician', False),
    'requires_parts': getattr(error_code, 'requires_parts', False),
    'chunk_id': getattr(error_code, 'chunk_id', None),  # ← NEU!
}
```

Und in RPC call Zeile ~478:

```python
result = self.supabase.rpc('insert_error_code', {
    'p_document_id': str(document_id),
    'p_manufacturer_id': manufacturer_id,
    'p_error_code': ec_data.get('error_code'),
    'p_error_description': ec_data.get('error_description'),
    'p_solution_text': ec_data.get('solution_text'),
    'p_confidence_score': ec_data.get('confidence', 0.8),
    'p_page_number': ec_data.get('page_number'),
    'p_severity_level': ec_data.get('severity_level', 'medium'),
    'p_extraction_method': ec_data.get('extraction_method', 'regex_pattern'),
    'p_requires_technician': ec_data.get('requires_technician', False),
    'p_requires_parts': ec_data.get('requires_parts', False),
    'p_context_text': ec_data.get('context_text'),
    'p_chunk_id': ec_data.get('chunk_id'),  # ← NEU!
    'p_metadata': metadata
}).execute()
```

#### C. Supabase RPC Function Update
**In Supabase SQL Editor:**

```sql
CREATE OR REPLACE FUNCTION insert_error_code(
    p_document_id UUID,
    p_manufacturer_id UUID,
    p_error_code TEXT,
    p_error_description TEXT,
    p_solution_text TEXT DEFAULT NULL,
    p_confidence_score NUMERIC DEFAULT 0.8,
    p_page_number INTEGER DEFAULT NULL,
    p_severity_level TEXT DEFAULT 'medium',
    p_extraction_method TEXT DEFAULT 'regex_pattern',
    p_requires_technician BOOLEAN DEFAULT FALSE,
    p_requires_parts BOOLEAN DEFAULT FALSE,
    p_context_text TEXT DEFAULT NULL,
    p_chunk_id UUID DEFAULT NULL,  -- ← NEU!
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_error_id UUID;
BEGIN
    INSERT INTO krai_intelligence.error_codes (
        document_id,
        manufacturer_id,
        error_code,
        error_description,
        solution_text,
        confidence_score,
        page_number,
        severity_level,
        extraction_method,
        requires_technician,
        requires_parts,
        context_text,
        chunk_id,  -- ← NEU!
        metadata
    ) VALUES (
        p_document_id,
        p_manufacturer_id,
        p_error_code,
        p_error_description,
        p_solution_text,
        p_confidence_score,
        p_page_number,
        p_severity_level,
        p_extraction_method,
        p_requires_technician,
        p_requires_parts,
        p_context_text,
        p_chunk_id,  -- ← NEU!
        p_metadata
    )
    RETURNING id INTO v_error_id;
    
    RETURN v_error_id;
END;
$$;
```

## 🚀 Nächste Schritte:

1. ✅ Model Update - **DONE**
2. ✅ Chunk-Finder Funktion - **DONE**
3. ⏳ Enrichment Update - **TODO** (siehe oben)
4. ⏳ Master Pipeline Update - **TODO** (siehe oben)
5. ⏳ Supabase RPC Update - **TODO** (siehe oben)

## 📝 Test nach Implementation:

```bash
# 1. Verarbeite ein Test-Dokument
python -m backend.pipeline.master_pipeline --file test.pdf

# 2. Prüfe chunk_id Verknüpfung
python check_enrichment_quality.py

# 3. Erwartung: 80%+ haben chunk_id
```

Möchtest du dass ich die restlichen 3 Schritte auch implementiere? 🚀
