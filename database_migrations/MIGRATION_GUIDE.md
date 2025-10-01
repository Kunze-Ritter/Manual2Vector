## 🎯 KRAI Database - Clean Migration Guide

**Version:** 2.0 Consolidated  
**Letzte Aktualisierung:** Oktober 2025

---

## 📋 Übersicht

Die Datenbank-Migrationen wurden **neu strukturiert** und in **3 logische, fehlerfreie Dateien** aufgeteilt:

```
01_schema_and_tables.sql          → Schemas, Tabellen, Foreign Keys, Views
02_security_rls_triggers.sql      → RLS, Policies, Roles, Triggers  
03_indexes_performance.sql        → Indexes, Functions, Materialized Views
```

**Vorteile:**
- ✅ **Logisch getrennt** - keine Import-Fehler mehr
- ✅ **Idempotent** - kann mehrfach ausgeführt werden
- ✅ **Getestet** - alle Abhängigkeiten korrekt aufgelöst
- ✅ **Vollständig** - enthält alle Updates bis Oktober 2025

---

## 🚀 Schnellstart

### Methode 1: Supabase SQL Editor (Empfohlen)

1. Öffne Supabase Dashboard → SQL Editor
2. Führe die Dateien **in dieser Reihenfolge** aus:

```sql
-- 1. Schemas und Tabellen (ca. 2-3 Minuten)
-- Kopiere Inhalt von 01_schema_and_tables.sql
-- Klicke "Run"

-- 2. Security und RLS (ca. 1 Minute)  
-- Kopiere Inhalt von 02_security_rls_triggers.sql
-- Klicke "Run"

-- 3. Indexes und Performance (ca. 2-5 Minuten)
-- Kopiere Inhalt von 03_indexes_performance.sql
-- Klicke "Run"
```

---

### Methode 2: psql Command Line

```bash
# Mit Supabase verbinden
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Migrationen ausführen
\i 01_schema_and_tables.sql
\i 02_security_rls_triggers.sql
\i 03_indexes_performance.sql
```

---

### Methode 3: Python Script

```python
from supabase import create_client
import os

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Dateien einlesen und ausführen
migrations = [
    '01_schema_and_tables.sql',
    '02_security_rls_triggers.sql',
    '03_indexes_performance.sql'
]

for migration_file in migrations:
    print(f"Executing {migration_file}...")
    with open(f'database_migrations/{migration_file}', 'r', encoding='utf-8') as f:
        sql = f.read()
        # Hinweis: Supabase Python Client unterstützt keine direkten SQL-Executes
        # Nutze stattdessen psycopg2 oder SQL Editor
```

---

## 📊 Was wird erstellt?

### 01_schema_and_tables.sql: Schemas & Tabellen

**10 Schemas:**
- `krai_core` - Manufacturers, Products, Documents
- `krai_intelligence` - Chunks, Embeddings, Error Codes
- `krai_content` - Images, Links, Videos
- `krai_config` - Features, Options, Compatibility
- `krai_system` - Queue, Audit, Metrics
- `krai_ml` - ML Models
- `krai_parts` - Parts Catalog
- `krai_service` - Technicians, Service Calls
- `krai_users` - Users, Sessions
- `krai_integrations` - API Keys, Webhooks

**33 Tabellen** mit allen Foreign Keys

**Neue Features:**
- ✅ `krai_content.links` - PDF Link Extraction
- ✅ `krai_service.technicians` - Service Management
- ✅ `images.figure_number` - Figure References
- ✅ `images.figure_context` - Context around figures

**2 Views:**
- `document_media_context` - Unified media view
- `public_products` - Public product view

---

### 02_security_rls_triggers.sql: Security & RLS

**4 Roles:**
- `krai_service_role` - Backend full access
- `krai_admin_role` - Admin operations
- `krai_readonly_role` - Read-only access
- `krai_authenticated` - Authenticated users

**33 RLS Policies:**
- Service Role = Full Access auf alle Tabellen
- Alle Tabellen mit RLS aktiviert

**7 Triggers:**
- `update_updated_at` für Timestamp-Updates
- Automatisches Audit Logging

---

### 03_indexes_performance.sql: Indexes & Performance

**100+ Indexes:**
- Basic Indexes (manufacturer_id, document_id, etc.)
- HNSW Index für Vector Similarity Search
- GIN Indexes für Full-Text Search
- Composite Indexes für komplexe Queries
- Partial Indexes für filtered queries
- Foreign Key Indexes

**4 Performance Functions:**
- `search_documents_optimized()` - Optimierte Dokumentensuche
- `find_similar_chunks()` - Vector Similarity Search
- `get_processing_statistics()` - Processing Stats
- `refresh_document_processing_summary()` - View refresh

**1 Materialized View:**
- `document_processing_summary` - Aggregierte Statistiken

---

## ⏱️ Geschätzte Dauer

| Migration | Dauer | Beschreibung |
|-----------|-------|--------------|
| 01_schema_and_tables.sql | 2-3 Min | Schemas, Tabellen, Foreign Keys |
| 02_security_rls_triggers.sql | 1 Min | RLS, Policies, Triggers |
| 03_indexes_performance.sql | 2-5 Min | Indexes (abhängig von Datenmenge) |
| **Total** | **5-9 Min** | Komplett-Setup |

---

## ✅ Verifizierung

Nach erfolgreicher Migration prüfen:

```sql
-- 1. Schemas prüfen
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'krai_%' 
ORDER BY schema_name;
-- Erwartet: 10 Schemas

-- 2. Tabellen zählen
SELECT schemaname, COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname LIKE 'krai_%'
GROUP BY schemaname;
-- Erwartet: 33 Tabellen gesamt

-- 3. RLS prüfen
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname LIKE 'krai_%' 
AND rowsecurity = true;
-- Erwartet: Alle 33 Tabellen mit RLS

-- 4. Indexes prüfen
SELECT schemaname, COUNT(*) as index_count
FROM pg_indexes 
WHERE schemaname LIKE 'krai_%'
GROUP BY schemaname;
-- Erwartet: 100+ Indexes

-- 5. Functions prüfen
SELECT routine_schema, routine_name
FROM information_schema.routines
WHERE routine_schema LIKE 'krai_%'
ORDER BY routine_schema, routine_name;
-- Erwartet: 4+ Functions

-- 6. Test Query
SELECT * FROM krai_intelligence.search_documents_optimized(
    'printer error',
    NULL,
    NULL,
    10
);
-- Sollte ohne Fehler laufen (auch wenn leer)
```

---

## 🔧 Troubleshooting

### Problem: "relation already exists"

**Lösung:** Das ist OK! Die Migrationen sind idempotent und überspringen existierende Objekte.

### Problem: "permission denied"

**Lösung:** Stelle sicher, dass du den **Service Role Key** verwendest (nicht Anon Key).

### Problem: "extension vector does not exist"

**Lösung:** 
```sql
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
```

### Problem: Langsame Index-Erstellung

**Lösung:** Bei großen Datenmengen können Indexes länger dauern. Das ist normal.

---

## 📦 Storage Buckets (Separat)

Storage Buckets können **NICHT über SQL** erstellt werden. Siehe `STORAGE_SETUP_GUIDE.md`:

```
Erforderliche Buckets (manuell erstellen):
- krai-document-images
- krai-error-images  
- krai-parts-images
```

---

## 🆚 Unterschied zu alten Migrationen

### Alte Struktur (01-06 + add_links):
```
01_krai_complete_schema.sql      ← Basis
02_security_and_rls.sql           ← RLS
03_performance_and_indexes.sql    ← Indexes
04_extensions_and_storage.sql     ← Storage (Fehler!)
05_performance_test.sql           ← Tests
06_fix_service_schema.sql         ← Service Fix
add_links_and_figures.sql         ← Links
```

**Probleme:**
- ❌ Unlogische Reihenfolge
- ❌ Abhängigkeiten nicht aufgelöst
- ❌ Duplikate und Konflikte
- ❌ Storage-Fehler

### Neue Struktur (01-03):
```
01_schema_and_tables.sql          ← ALLES: Schemas, Tabellen, FKs
02_security_rls_triggers.sql      ← RLS + Triggers
03_indexes_performance.sql        ← Indexes + Functions
```

**Vorteile:**
- ✅ Logische Gruppierung
- ✅ Alle Abhängigkeiten aufgelöst
- ✅ Keine Duplikate
- ✅ Fehlerfreie Ausführung

---

## 🎯 Best Practices

1. **Backup erstellen** vor Migration
2. **Service Role Key** verwenden
3. **Reihenfolge einhalten**: 01 → 02 → 03
4. **Verifizierung** nach jeder Migration
5. **Storage Buckets** separat über Dashboard erstellen
6. **Bei Fehlern:** Migration ist idempotent, einfach nochmal ausführen

---

## 📚 Weitere Dokumentation

- `DATABASE_SCHEMA_DOCUMENTATION.md` - Vollständige Schema-Dokumentation
- `STORAGE_SETUP_GUIDE.md` - Storage Bucket Setup
- `.cursor/rules/guidelines.mdc` - Development Guidelines

---

## ✅ Checkliste

Nach Abschluss aller Migrationen:

- [ ] 10 Schemas erstellt
- [ ] 33 Tabellen erstellt
- [ ] Alle Foreign Keys funktionieren
- [ ] RLS auf allen Tabellen aktiv
- [ ] 100+ Indexes erstellt
- [ ] Performance Functions verfügbar
- [ ] Views erstellt
- [ ] Triggers aktiv
- [ ] Storage Buckets manuell erstellt
- [ ] Test-Query erfolgreich

---

**Bei Fragen:** Siehe KRAI Development Team Lead  
**Version:** 2.0 Consolidated (Oktober 2025)

