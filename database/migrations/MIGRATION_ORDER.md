# 🚀 Migrations Ausführen - KORREKTE REIHENFOLGE

## ⚠️ **WICHTIG: Reihenfolge beachten!**

Führe die Migrations in **dieser exakten Reihenfolge** aus:

---

## 📋 **SCHRITT-FÜR-SCHRITT ANLEITUNG**

### **1. Migration 12: Processing Fields**
**File:** `12_add_processing_fields_to_documents.sql`

**Was es macht:**
- Fügt `processing_results` (JSONB) zu documents hinzu
- Fügt `processing_error` (TEXT) hinzu
- Fügt `processing_status` (VARCHAR) hinzu

**Ausführen:**
```sql
-- Kopiere Inhalt von 12_add_processing_fields_to_documents.sql
-- Run in Supabase SQL Editor
```

---

### **2. Migration 13: Document-Products Table**
**File:** `13_create_document_products_table_only.sql`

**Was es macht:**
- Erstellt `krai_core.document_products` TABLE (Many-to-Many)
- Erstellt Indexes
- Erstellt Helper Function `get_document_products()`

**Ausführen:**
```sql
-- Kopiere Inhalt von 13_create_document_products_table_only.sql
-- Run in Supabase SQL Editor
```

**Verification:**
```sql
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'krai_core' AND tablename = 'document_products';

-- MUSS 1 Zeile zurückgeben!
```

---

### **3. Migration 14a: Documents Table (Part 1)**
**File:** `14a_drop_and_create_documents_table.sql`

**Was es macht:**
- Droppt alte `krai_core.documents` (TABLE oder VIEW)
- Erstellt neue `krai_core.documents` TABLE
- Mit allen Spalten inkl. `stage_status`, `version`, etc.
- OHNE: `storage_url`, `product_id`, `manufacturer_id`

**Ausführen:**
```sql
-- Kopiere Inhalt von 14a_drop_and_create_documents_table.sql
-- Run in Supabase SQL Editor
```

**Verification:**
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'krai_core' 
  AND table_name = 'documents'
  AND column_name = 'stage_status';

-- MUSS stage_status zurückgeben!
```

---

### **4. Migration 14b: Documents Indexes & Views (Part 2)**
**File:** `14b_add_indexes_and_views.sql`

**Was es macht:**
- Erstellt Indexes für Performance
- Erstellt `public.documents` VIEW
- Erstellt INSERT/UPDATE/DELETE Rules

**Ausführen:**
```sql
-- Kopiere Inhalt von 14b_add_indexes_and_views.sql
-- Run in Supabase SQL Editor
```

**Verification:**
```sql
SELECT * FROM public.documents LIMIT 1;

-- Sollte funktionieren (kein Fehler)
```

---

### **5. Migration 15a: Products View (Part 1)**
**File:** `15a_create_products_view.sql`

**Was es macht:**
- Erstellt `public.products` VIEW → `krai_core.products`
- Erstellt INSERT/UPDATE/DELETE Rules

**Ausführen:**
```sql
-- Kopiere Inhalt von 15a_create_products_view.sql
-- Run in Supabase SQL Editor
```

**Verification:**
```sql
SELECT * FROM public.products LIMIT 1;

-- Sollte funktionieren
```

---

### **6. Migration 15b: Document-Products & Manufacturers Views (Part 2)**
**File:** `15b_create_document_products_manufacturers_views.sql`

**Was es macht:**
- Erstellt `public.document_products` VIEW
- Erstellt `public.manufacturers` VIEW
- Erstellt INSERT/UPDATE/DELETE Rules

**⚠️ WICHTIG:** Kann erst NACH Migration 13 ausgeführt werden!

**Ausführen:**
```sql
-- Kopiere Inhalt von 15b_create_document_products_manufacturers_views.sql
-- Run in Supabase SQL Editor
```

**Verification:**
```sql
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname IN ('products', 'document_products', 'manufacturers')
ORDER BY viewname;

-- MUSS 3 Zeilen zurückgeben:
-- document_products
-- manufacturers
-- products
```

---

## ✅ **ZUSAMMENFASSUNG REIHENFOLGE:**

```
1. Migration 12  (processing fields)
2. Migration 13  (document_products TABLE)     ← MUSS VOR 15b!
3. Migration 14a (documents TABLE neu)
4. Migration 14b (documents indexes + views)
5. Migration 15a (products VIEW)
6. Migration 15b (document_products VIEW)      ← BRAUCHT 13!
```

---

## 🐛 **FEHLER: "relation krai_core.document_products does not exist"**

**Ursache:** Migration 15b wurde VOR Migration 13 ausgeführt!

**Lösung:** 
1. Migration 13 ausführen (erstellt die TABLE)
2. DANN Migration 15b ausführen (erstellt die VIEW)

---

## 🎯 **NACH ALLEN MIGRATIONS:**

### **Test Script:**
```bash
cd backend/processors_v2
python process_production.py
```

### **Erwartete Ausgabe:**
```
✅ Created document record
✅ Saved 1 products to DB
✅ Saved 1 document-product relationships
✅ Updated document metadata: Konica Minolta, 1 models, version: 2024/12/25
✅ PIPELINE COMPLETE!
```

---

## 📊 **FINALE VERIFICATION:**

```sql
-- Check alle wichtigen Tabellen:
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'krai_core' 
  AND tablename IN ('documents', 'products', 'document_products', 'manufacturers')
ORDER BY tablename;

-- Check alle wichtigen Views:
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname IN ('documents', 'products', 'document_products', 'manufacturers')
ORDER BY viewname;

-- Beide sollten jeweils 4 Zeilen zurückgeben
```

---

## 🎉 **FERTIG!**

Alle Migrations erfolgreich ausgeführt! Das Processing Script sollte jetzt funktionieren! 🚀
