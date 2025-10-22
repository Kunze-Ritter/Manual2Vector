# Processor Fix Plan - chunk_id Verknüpfung

## Problem:
Error codes werden OHNE `chunk_id` gespeichert → Keine Bilder-Verknüpfung!

## Lösung:

### 1. Füge `chunk_id` zum ExtractedErrorCode Model hinzu

**Datei:** `backend/processors/models.py`

```python
@dataclass
class ExtractedErrorCode:
    error_code: str
    error_description: str
    solution_text: Optional[str] = None
    context_text: Optional[str] = None
    confidence: float = 0.0
    page_number: Optional[int] = None
    extraction_method: str = "regex"
    severity_level: str = "medium"
    requires_technician: bool = False
    requires_parts: bool = False
    chunk_id: Optional[str] = None  # ← NEU!
```

### 2. Setze `chunk_id` beim Enrichment

**Datei:** `backend/processors/error_code_extractor.py`

Nach dem Enrichment, finde den passenden chunk:

```python
def _find_chunk_for_error_code(
    self, 
    error_code: str, 
    page_number: int,
    chunks: List[Dict]
) -> Optional[str]:
    """Find the chunk that contains this error code"""
    
    # Search for chunk on same page that contains the error code
    for chunk in chunks:
        chunk_page = chunk.get('page_start') or chunk.get('page_number')
        chunk_text = chunk.get('text_chunk', '')
        
        # Match: Same page + contains error code
        if chunk_page == page_number and error_code in chunk_text:
            return chunk.get('id')
    
    # Fallback: Any chunk that contains the error code
    for chunk in chunks:
        if error_code in chunk.get('text_chunk', ''):
            return chunk.get('id')
    
    return None
```

Dann im Enrichment:

```python
# Nach dem Enrichment, setze chunk_id
if chunk_results.data:
    chunk_id = self._find_chunk_for_error_code(
        error_code=code,
        page_number=error_code.page_number,
        chunks=chunk_results.data
    )
    if chunk_id:
        error_code.chunk_id = chunk_id
```

### 3. Übergebe `chunk_id` an RPC

**Datei:** `backend/processors/master_pipeline.py`

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

### 4. Update RPC Function in Supabase

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

## Test nach Implementation:

```python
# 1. Verarbeite ein Dokument
python -m backend.pipeline.master_pipeline --file test.pdf

# 2. Prüfe ob chunk_id gesetzt wurde
python check_enrichment_quality.py

# 3. Erwartung: 80%+ der error_codes haben chunk_id
```

## Erwartetes Ergebnis:

```sql
SELECT 
    COUNT(*) FILTER (WHERE chunk_id IS NOT NULL) as with_chunk,
    COUNT(*) FILTER (WHERE chunk_id IS NULL) as without_chunk,
    COUNT(*) as total
FROM krai_intelligence.error_codes;

-- Erwartung:
-- with_chunk: 80%+
-- without_chunk: 20%-
```
