## 🎯 KRAI Database - Clean Migration Guide

**Version:** 3.0 Phase 6 Enhanced  
**Letzte Aktualisierung:** Dezember 2025

---

## 📋 Übersicht

Die Datenbank-Migrationen wurden **für Phase 6 erweitert** und enthalten jetzt **erweiterte Multimodal-Funktionen**:

```sql
01_schema_and_tables.sql          → Schemas, Tabellen, Foreign Keys, Views
02_security_rls_triggers.sql      → RLS, Policies, Roles, Triggers  
03_indexes_performance.sql        → Indexes, Functions, Materialized Views
04_phase6_multimodal.sql          → Phase 6: Multimodal Search, Context Extraction
05_phase6_hierarchical.sql        → Phase 6: Hierarchical Chunking, SVG Processing
```

**Phase 6 Neue Features:**
- ✅ **Multimodal Embeddings** - Unified `embeddings_v2` table
- ✅ **Hierarchical Chunking** - Section structure and linking
- ✅ **SVG Vector Graphics** - Vector graphics support
- ✅ **Context Extraction** - AI-powered context for all media
- ✅ **Advanced Search** - Multimodal search with context awareness

**Vorteile:**
- ✅ **Logisch getrennt** - keine Import-Fehler mehr
- ✅ **Idempotent** - kann mehrfach ausgeführt werden
- ✅ **Phase 6 Ready** - alle neuen Multimodal-Funktionen
- ✅ **Vollständig** - enthält alle Updates bis Dezember 2025

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

-- 4. Phase 6 Multimodal Features (ca. 2-3 Minuten)
-- Kopiere Inhalt von 04_phase6_multimodal.sql
-- Klicke "Run"

-- 5. Phase 6 Hierarchical Features (ca. 1-2 Minuten)
-- Kopiere Inhalt von 05_phase6_hierarchical.sql
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
\i 04_phase6_multimodal.sql
\i 05_phase6_hierarchical.sql
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
    '03_indexes_performance.sql',
    '04_phase6_multimodal.sql',
    '05_phase6_hierarchical.sql'
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
- `krai_content` - Images, Links, Videos, Tables
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
- ✅ `krai_content.instructional_videos` - Enhanced video support
- ✅ `krai_intelligence.structured_tables` - Table structure and context
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

### 04_phase6_multimodal.sql: Phase 6 Multimodal Features

**Multimodal Embeddings:**
- `krai_intelligence.embeddings_v2` - Unified multimodal embedding table
- Support for text, image, video, table, and link embeddings
- Enhanced metadata with source_type and source_id
- Improved vector indexing with ivfflat

**Context Extraction:**
- Enhanced `krai_content.images` with context columns
- `krai_content.instructional_videos` with AI-generated descriptions
- `krai_content.links` with extracted content and summaries
- `krai_intelligence.structured_tables` with context and analysis

**Advanced Search Functions:**
- `match_multimodal()` - Unified search across all content types
- `match_images_by_context()` - Context-aware image search
- `get_document_statistics()` - Enhanced document analytics
- `search_chunks_by_content()` - Content-based chunk search

---

### 05_phase6_hierarchical.sql: Phase 6 Hierarchical Features

**Hierarchical Chunking:**
- Enhanced `krai_intelligence.chunks` with hierarchical structure
- `section_hierarchy` JSONB column for section paths
- `section_level` for hierarchy depth
- `previous_chunk_id` and `next_chunk_id` for cross-chunk linking
- `error_code` column for error code boundary detection

**SVG Vector Graphics:**
- Enhanced `krai_content.images` with SVG support
- `image_type` column (raster/vector)
- `svg_content` TEXT column for original SVG data
- `vector_graphic` BOOLEAN flag for vector graphics
- SVG to PNG conversion workflow support

**Performance Optimizations:**
- Enhanced vector indexes for hierarchical search
- Improved chunk linking queries
- Optimized section navigation functions
- Enhanced error code detection and boundary queries

---

## ⏱️ Geschätzte Dauer

| Migration | Dauer | Beschreibung |
|-----------|-------|--------------|
| 01_schema_and_tables.sql | 2-3 Min | Schemas, Tabellen, Foreign Keys |
| 02_security_rls_triggers.sql | 1 Min | RLS, Policies, Triggers |
| 03_indexes_performance.sql | 2-5 Min | Indexes (abhängig von Datenmenge) |
| 04_phase6_multimodal.sql | 2-3 Min | Multimodal Embeddings, Context Extraction |
| 05_phase6_hierarchical.sql | 1-2 Min | Hierarchical Chunking, SVG Support |
| **Total** | **8-14 Min** | Komplett-Setup mit Phase 6 |

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
-- Erwartet: 35+ Tabellen gesamt (inkl. Phase 6)

-- 3. Phase 6 Tabellen prüfen
SELECT table_name, table_schema
FROM information_schema.tables 
WHERE table_name IN ('embeddings_v2', 'structured_tables', 'instructional_videos')
AND table_schema LIKE 'krai_%'
ORDER BY table_schema, table_name;
-- Erwartet: Alle Phase 6 Tabellen vorhanden

-- 4. RLS prüfen
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname LIKE 'krai_%' 
AND rowsecurity = true;
-- Erwartet: Alle Tabellen mit RLS

-- 5. Indexes prüfen
SELECT schemaname, COUNT(*) as index_count
FROM pg_indexes 
WHERE schemaname LIKE 'krai_%'
GROUP BY schemaname;
-- Erwartet: 120+ Indexes (inkl. Phase 6)

-- 6. Functions prüfen
SELECT routine_schema, routine_name
FROM information_schema.routines
WHERE routine_schema LIKE 'krai_%'
ORDER BY routine_schema, routine_name;
-- Erwartet: 8+ Functions (inkl. Phase 6)

-- 7. Phase 6 Test Queries
-- Multimodal Search Test
SELECT * FROM krai_intelligence.match_multimodal(
    '[0.1,0.2,0.3]'::vector,
    0.5,
    10
) LIMIT 1;

-- Hierarchical Chunk Test
SELECT section_hierarchy, section_level, previous_chunk_id, next_chunk_id
FROM krai_intelligence.chunks 
WHERE section_level IS NOT NULL 
LIMIT 1;

-- SVG Graphics Test
SELECT image_type, svg_content, vector_graphic
FROM krai_content.images 
WHERE vector_graphic = true 
LIMIT 1;
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
- [ ] 35+ Tabellen erstellt (inkl. Phase 6)
- [ ] Alle Foreign Keys funktionieren
- [ ] RLS auf allen Tabellen aktiv
- [ ] 120+ Indexes erstellt (inkl. Phase 6)
- [ ] Performance Functions verfügbar
- [ ] Views erstellt
- [ ] Triggers aktiv
- [ ] **Phase 6: `embeddings_v2` Tabelle erstellt**
- [ ] **Phase 6: `structured_tables` Tabelle erstellt**
- [ ] **Phase 6: `instructional_videos` Tabelle enhanced**
- [ ] **Phase 6: Hierarchical chunk columns vorhanden**
- [ ] **Phase 6: SVG support columns vorhanden**
- [ ] **Phase 6: Multimodal search functions verfügbar**
- [ ] Storage Buckets manuell erstellt
- [ ] Test-Query erfolgreich
- [ ] **Phase 6: Multimodal search Test erfolgreich**

---

## 🆕 Phase 6 Features

### Neu in Version 3.0:

**Multimodal Search:**
- Unified search across text, images, videos, tables, and links
- Context-aware image search with Vision AI analysis
- Two-stage retrieval for enhanced results

**Hierarchical Processing:**
- Document structure detection and preservation
- Cross-chunk linking with previous/next relationships
- Error code boundary detection and navigation

**Vector Graphics Support:**
- SVG extraction from PDF documents
- SVG to PNG conversion for Vision AI compatibility
- Vector graphics metadata and analysis

**Enhanced Context Extraction:**
- AI-powered context generation for all media types
- Embedding generation for context-based search
- Rich metadata for improved discoverability

---

**Bei Fragen:** Siehe KRAI Development Team Lead  
**Version:** 3.0 Phase 6 Enhanced (Dezember 2025)

