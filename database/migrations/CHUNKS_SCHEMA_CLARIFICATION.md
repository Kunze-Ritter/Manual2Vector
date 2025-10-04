# 📦 Chunks Schema Clarification

## Problem: Two Chunks Tables! 😱

Es gibt **ZWEI** chunks Tabellen in der Datenbank, was zu Verwirrung führt:

### 1. `krai_intelligence.chunks` ✅ **AKTIV - WIRD VERWENDET**

```sql
CREATE TABLE krai_intelligence.chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    text_chunk TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    fingerprint VARCHAR(32) NOT NULL,
    embedding vector(768),              -- ✅ Für Semantic Search
    metadata JSONB DEFAULT '{}',        -- ✅ Enthält header_metadata!
    processing_status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Verwendung:**
- ✅ Von `embedding_processor.py` beschrieben
- ✅ Enthält alle Chunks mit Metadaten
- ✅ Enthält Embeddings für Semantic Search
- ✅ Metadata JSONB enthält:
  - `page_header` - Der entfernte Header-Text
  - `header_products` - Produkt-Modellnummern aus dem Header
  - `header_removed` - Boolean flag
  - `chunk_type` - procedure, troubleshooting, specification, etc.
  - `char_count`, `word_count`
  - `embedded_at` - Timestamp

### 2. `krai_content.chunks` ❌ **LEGACY - NICHT VERWENDET**

```sql
CREATE TABLE krai_content.chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    content TEXT NOT NULL,              -- Andere Spaltenname!
    chunk_type VARCHAR(50),
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    section_title VARCHAR(255),
    confidence_score DECIMAL(3,2),
    -- ❌ KEINE metadata Spalte!
    -- ❌ KEINE embedding Spalte!
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Status:**
- ❌ Wird von KEINEM v2 Code verwendet
- ❌ Ist leer (keine Daten)
- ❌ Hat keine `metadata` Spalte
- ❌ Legacy/ungenutzt

---

## Lösung: Migration 20

**Migration 20 (`20_cleanup_duplicate_chunks_table.sql`) macht:**

1. ✅ Verifiziert dass `krai_content.chunks` leer ist
2. ✅ Droppt `krai_content.chunks` Tabelle
3. ✅ Erstellt `public.chunks` View zu `krai_intelligence.chunks`

---

## Code Verwendung

### ✅ Richtig (wird verwendet):

```python
# embedding_processor.py
self.supabase.table('chunks').upsert({
    'id': chunk_id,
    'text_chunk': chunk_text,
    'metadata': {
        'page_header': 'AccurioPress C4080',
        'header_products': ['C4080'],
        'chunk_type': 'procedure'
    },
    'embedding': vector
}).execute()

# -> Schreibt in krai_intelligence.chunks ✅
```

### ❌ Falsch (existierte nicht):

```python
# Niemand tut das (zum Glück!)
self.supabase.schema('krai_content').table('chunks').insert()
```

---

## Nach Migration 20

```sql
-- Nur eine chunks Tabelle:
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_name = 'chunks';

Result:
| table_schema        | table_name |
|---------------------|------------|
| krai_intelligence   | chunks     |  ✅ EINZIGE chunks Tabelle
| public              | chunks     |  ✅ VIEW zu krai_intelligence.chunks
```

---

## Metadata Struktur

Nach dem Fix in `embedding_processor.py` enthält jeder Chunk:

```json
{
  "char_count": 1395,
  "word_count": 226,
  "chunk_type": "procedure",
  "embedded_at": "2025-10-04T22:49:14.611492",
  "page_header": "AccurioPress C4080 / C4070 / C84hc",
  "header_products": ["C4080", "C4070", "C84hc"],
  "header_removed": true
}
```

---

## Zusammenfassung

| Feature | krai_intelligence.chunks | krai_content.chunks (OLD) |
|---------|-------------------------|---------------------------|
| **Status** | ✅ AKTIV | ❌ DEPRECATED |
| **Von Code verwendet** | ✅ Ja | ❌ Nein |
| **Metadata JSONB** | ✅ Ja | ❌ Nein |
| **Embeddings** | ✅ Ja (vector) | ❌ Nein |
| **Header Metadata** | ✅ Ja | ❌ Nein |
| **Daten vorhanden** | ✅ Ja | ❌ Leer |

**Nach Migration 20:** Nur noch `krai_intelligence.chunks` existiert! 🎉
