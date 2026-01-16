# 🚀 Migration 12 Anwenden - processing_results Spalte

## ⚡ **SCHNELL-ANLEITUNG (2 Minuten):**

### **1. PostgreSQL SQL Editor öffnen:**

**Option A - pgAdmin:**
- Öffne pgAdmin und verbinde mit `krai-postgres`
- Rechtsklick auf Database → Query Tool

**Option B - psql:**
```bash
psql -h localhost -U krai_user -d krai
```

### **2. Diesen SQL Code kopieren & ausführen:**

```sql
-- Migration 12: Add processing_results column to documents table

-- Add processing_results column (JSONB for flexible storage)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_results JSONB DEFAULT NULL;

-- Add processing_error column (for error messages)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_error TEXT DEFAULT NULL;

-- Add processing_status column (for status tracking)
ALTER TABLE krai_core.documents
ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'pending';

-- Create index on processing_status for filtering
CREATE INDEX IF NOT EXISTS idx_documents_processing_status
ON krai_core.documents(processing_status);

-- Create GIN index on processing_results for JSON queries
CREATE INDEX IF NOT EXISTS idx_documents_processing_results
ON krai_core.documents USING GIN (processing_results);

-- Add comments
COMMENT ON COLUMN krai_core.documents.processing_results IS 'Complete processing results from the pipeline (JSONB)';
COMMENT ON COLUMN krai_core.documents.processing_error IS 'Error message if processing failed';
COMMENT ON COLUMN krai_core.documents.processing_status IS 'Processing status: pending, processing, completed, failed';

-- Grant permissions
GRANT SELECT, UPDATE ON krai_core.documents TO authenticated;
GRANT SELECT, UPDATE ON krai_core.documents TO service_role;
```

### **3. "Run" klicken!**

### **4. Fertig! ✅**

---

## 📊 **Was wird hinzugefügt:**

| Spalte | Typ | Zweck |
|--------|-----|-------|
| **processing_results** | JSONB | Alle Ergebnisse (Products, Error Codes, Links, Videos, Chunks, etc.) |
| **processing_error** | TEXT | Fehler-Meldung falls gescheitert |
| **processing_status** | TEXT | Status: `pending`, `processing`, `completed`, `failed` |

**Plus:**
- Index auf `processing_status` (schnelles Filtern)
- GIN Index auf `processing_results` (schnelle JSON-Queries)

---

## 🎯 **Warum wichtig:**

### **OHNE processing_results:**
```
❌ Daten landen nur in metadata (gemischt mit anderen Daten)
❌ Schwer zu querien
❌ Keine strukturierte Speicherung
```

### **MIT processing_results:**
```
✅ Eigene dedizierte Spalte
✅ GIN Index für schnelle Queries
✅ Saubere Trennung von Metadaten
✅ Alle Ergebnisse strukturiert an einem Ort:
   - Products
   - Error Codes  
   - Versions
   - Links
   - Videos
   - Images
   - Chunks
   - Statistics
```

---

## 🔍 **Beispiel Query NACH Migration:**

```sql
-- Finde alle Dokumente mit mehr als 10 Products:
SELECT id, file_name, 
       jsonb_array_length(processing_results->'products') as product_count
FROM krai_core.documents
WHERE processing_results->'products' IS NOT NULL
  AND jsonb_array_length(processing_results->'products') > 10;

-- Finde alle Dokumente mit Videos:
SELECT id, file_name,
       processing_results->'videos' as videos
FROM krai_core.documents  
WHERE processing_results->'videos' IS NOT NULL
  AND jsonb_array_length(processing_results->'videos') > 0;

-- Finde fehlgeschlagene Verarbeitungen:
SELECT id, file_name, processing_error
FROM krai_core.documents
WHERE processing_status = 'failed';
```

---

## ✅ **NACH der Migration:**

### **Pipeline speichert dann:**
```json
{
  "metadata": {...},
  "statistics": {
    "pages": 1234,
    "chunks": 567,
    "products": 22
  },
  "products": [
    {
      "model_number": "C4080",
      "manufacturer": "Konica Minolta",
      "confidence": 0.95
    }
  ],
  "error_codes": [...],
  "versions": [...],
  "links": [...],
  "videos": [...]
}
```

**→ Alles strukturiert in `processing_results` JSONB!** ✅

---

## 🚀 **NOCHMAL KURZ:**

1. **Öffne:** pgAdmin oder psql (siehe oben)
2. **Kopiere:** SQL Code von oben
3. **Run:** Execute/Ausführen
4. **Done:** ✅

**Dann Script neu starten - alles wird korrekt gespeichert!** 🎉
