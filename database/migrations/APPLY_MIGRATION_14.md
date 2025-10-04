# 🚀 Migration 14 Anwenden (2 Teile)

## ⚡ **WICHTIG: In dieser Reihenfolge ausführen!**

Migration 14 wurde in **2 Teile** aufgeteilt für einfachere Fehlersuche:

---

## 📋 **TEIL 1: Drop & Create TABLE**

### **File:** `14a_drop_and_create_documents_table.sql`

**Was passiert:**
- ✅ Erkennt ob `krai_core.documents` eine TABLE oder VIEW ist
- ✅ Droppt das Objekt (CASCADE)
- ✅ Erstellt neue TABLE mit ALLEN Spalten:
  - `stage_status JSONB` ← **NEU!**
  - `processing_results JSONB` ← **NEU!**
  - `version VARCHAR(50)` ← **NEU!**
  - OHNE: `storage_url`, `product_id`, `manufacturer_id` ← **ENTFERNT!**

### **In Supabase SQL Editor ausführen:**

1. Öffne: https://supabase.com/dashboard/project/[PROJECT]/sql/new
2. Kopiere kompletten Inhalt von `14a_drop_and_create_documents_table.sql`
3. Klick "Run"
4. Prüfe Ausgabe: "Dropped TABLE..." oder "Dropped VIEW..."

### **Verification:**

```sql
-- Prüfe ob Tabelle existiert und stage_status vorhanden ist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'krai_core' 
  AND table_name = 'documents'
  AND column_name IN ('stage_status', 'processing_results', 'version')
ORDER BY column_name;

-- Sollte 3 Zeilen zurückgeben:
-- processing_results | jsonb
-- stage_status       | jsonb
-- version            | character varying
```

---

## 📋 **TEIL 2: Indexes, Comments & Views**

### **File:** `14b_add_indexes_and_views.sql`

**Was passiert:**
- ✅ Erstellt Performance-Indexes (inkl. GIN für JSONB)
- ✅ Fügt Kommentare hinzu (Dokumentation)
- ✅ Erstellt `public.documents` VIEW (für Supabase PostgREST)
- ✅ Erstellt INSERT/UPDATE/DELETE Rules (View funktioniert wie Tabelle)

### **In Supabase SQL Editor ausführen:**

1. **NACHDEM Teil 1 erfolgreich war!**
2. Kopiere kompletten Inhalt von `14b_add_indexes_and_views.sql`
3. Klick "Run"
4. Prüfe Ausgabe: sollten keine Fehler kommen

### **Verification:**

```sql
-- Prüfe ob public.documents VIEW existiert
SELECT * FROM public.documents LIMIT 1;

-- Prüfe Indexes
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'krai_core' 
  AND tablename = 'documents'
ORDER BY indexname;

-- Sollte mindestens 9 Indexes zeigen
```

---

## ⚠️ **WICHTIG: Daten-Backup!**

Falls die Tabelle bereits Daten enthält:

```sql
-- 1. BACKUP ERSTELLEN (vor Teil 1!)
CREATE TABLE krai_core.documents_backup_20241004 AS 
SELECT * FROM krai_core.documents;

-- 2. Teil 1 & 2 ausführen

-- 3. DATEN ZURÜCKSPIELEN
INSERT INTO krai_core.documents 
SELECT 
    id, filename, original_filename, file_size, file_hash, storage_path,
    document_type, language, version, publish_date, page_count, word_count,
    character_count, content_text, content_summary, extracted_metadata,
    processing_status, 
    NULL as processing_results,  -- Alte Daten haben das nicht
    NULL as processing_error,
    '{}'::jsonb as stage_status,  -- Default für alte Daten
    confidence_score, manual_review_required, manual_review_completed,
    manual_review_notes, ocr_confidence, manufacturer, series, models,
    created_at, updated_at
FROM krai_core.documents_backup_20241004;

-- 4. BACKUP LÖSCHEN
DROP TABLE krai_core.documents_backup_20241004;
```

---

## ✅ **Nach Migration: Script testen**

```bash
cd backend/processors_v2
python process_production.py
```

**Erwartete Ausgabe:**
```
✅ Created document record: [UUID]
✅ Stage completed: upload
```

**KEINE Fehler mehr:**
- ❌ ~~"column stage_status does not exist"~~
- ❌ ~~"column processing_results does not exist"~~
- ❌ ~~"cannot drop columns from view"~~
- ❌ ~~"table public.documents not found"~~

---

## 🎯 **Zusammenfassung**

| Migration | Was es macht | Reihenfolge |
|-----------|--------------|-------------|
| **14a** | Drop + Create TABLE | **1. ZUERST** |
| **14b** | Indexes + Views | **2. DANACH** |

**Beide Teile müssen ausgeführt werden!**

---

## 🐛 **Troubleshooting**

### **"column stage_status does not exist" NACH Migration**

```sql
-- Prüfe ob Spalte wirklich da ist:
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'krai_core' 
  AND table_name = 'documents' 
  AND column_name = 'stage_status';

-- Wenn leer: Teil 1 nochmal ausführen!
```

### **"table public.documents not found"**

```sql
-- Prüfe ob VIEW existiert:
SELECT viewname 
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname = 'documents';

-- Wenn leer: Teil 2 nochmal ausführen!
```

---

## 🚀 **Fertig?**

Nach erfolgreicher Migration sollte das Processing funktionieren ohne Fehler! 🎉
