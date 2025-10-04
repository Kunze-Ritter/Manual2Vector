# 🚀 Migration 15 Anwenden (2 Teile)

## ⚡ **WICHTIG: In dieser Reihenfolge ausführen!**

Migration 15 wurde in **2 Teile** aufgeteilt:

---

## 📋 **TEIL 1: Products View**

### **File:** `15a_create_products_view.sql`

**Was passiert:**
- ✅ Droppt `public.products` VIEW falls vorhanden (CASCADE)
- ✅ Erstellt `public.products` VIEW → `krai_core.products`
- ✅ Erstellt INSERT/UPDATE/DELETE Rules (View funktioniert wie Table)
- ✅ Grant Permissions (authenticated, service_role)

### **In Supabase SQL Editor ausführen:**

1. Öffne: https://supabase.com/dashboard/project/[PROJECT]/sql/new
2. Kopiere kompletten Inhalt von `15a_create_products_view.sql`
3. Klick "Run"
4. Prüfe: keine Fehler

### **Verification:**

```sql
-- Prüfe ob View existiert:
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public' AND viewname = 'products';

-- Test INSERT via View:
SELECT * FROM public.products LIMIT 1;
```

---

## 📋 **TEIL 2: Document-Products & Manufacturers Views**

### **File:** `15b_create_document_products_manufacturers_views.sql`

**Was passiert:**
- ✅ Erstellt `public.document_products` VIEW → `krai_core.document_products`
- ✅ Erstellt `public.manufacturers` VIEW → `krai_core.manufacturers`
- ✅ Erstellt INSERT/UPDATE/DELETE Rules für beide
- ✅ Grant Permissions

### **In Supabase SQL Editor ausführen:**

1. **NACHDEM Teil 1 erfolgreich war!**
2. Kopiere kompletten Inhalt von `15b_create_document_products_manufacturers_views.sql`
3. Klick "Run"
4. Prüfe: keine Fehler

### **Verification:**

```sql
-- Prüfe alle 3 Views:
SELECT schemaname, viewname 
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname IN ('products', 'document_products', 'manufacturers')
ORDER BY viewname;

-- Sollte 3 Zeilen zurückgeben:
-- document_products
-- manufacturers
-- products
```

---

## 🎯 **WARUM DIESE VIEWS?**

### **Problem:**
```python
# Code versucht:
self.supabase.table('products').insert(...)

# PostgREST sucht in:
public.products  ← MUSS existieren!
```

### **Lösung:**
```
PostgREST → public.products (VIEW) → krai_core.products (TABLE)
```

**Vorteile:**
- ✅ Code nutzt Standard PostgREST (public schema)
- ✅ Permissions via Views (nicht direkt auf krai_core)
- ✅ INSERT/UPDATE/DELETE funktioniert (via Rules)

---

## ⚠️ **FEHLER: "cannot drop columns from view"**

Falls dieser Fehler kommt:
```
ERROR: cannot drop columns from view
```

**Das bedeutet:** Du versuchst, Migration 13 auszuführen BEVOR public.products existiert!

**Reihenfolge:**
1. ✅ Migration 12 (documents: processing_results)
2. ✅ Migration 14a + 14b (documents: TABLE statt VIEW)
3. ✅ **Migration 15a + 15b** (public views) ← **ZUERST!**
4. ✅ Migration 13 (document_products table) ← **DANACH!**

---

## 📊 **NACH Migration 15:**

### **Code funktioniert:**
```python
# Products speichern:
self.supabase.table('products').insert(record).execute()
# → Nutzt public.products VIEW → krai_core.products TABLE ✅

# Document-Products speichern:
self.supabase.table('document_products').insert(relationship).execute()
# → Nutzt public.document_products VIEW → krai_core.document_products TABLE ✅
```

### **Keine Fehler mehr:**
- ❌ ~~"permission denied for schema krai_core"~~
- ❌ ~~"table public.products not found"~~
- ❌ ~~"cannot drop columns from view"~~

---

## 🚀 **DANN SCRIPT TESTEN:**

```bash
cd backend/processors_v2
python process_production.py
```

**Erwartete Ausgabe:**
```
✅ Saved 1 products to DB
✅ Saved 1 document-product relationships
✅ Updated document metadata: [Manufacturer], 1 models
```

---

## 🎉 **ZUSAMMENFASSUNG:**

| Migration | Was es macht | Reihenfolge |
|-----------|--------------|-------------|
| **15a** | public.products VIEW | **1. ZUERST** |
| **15b** | public.document_products + manufacturers VIEWs | **2. DANACH** |

**Beide Teile müssen ausgeführt werden!**
