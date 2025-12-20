# KRAI Database Migrations

## ⚠️ Alte Migrationen archiviert

**Alle alten Migrationen (130+ SQL-Dateien) wurden nach `archive/` verschoben.**

---

## ✅ Für NEUE Installationen

Verwende die **konsolidierten PostgreSQL-Migrationen** in `../migrations_postgresql/`:

1. **`001_core_schema.sql`** - Schemas, Tabellen, Extensions, Indexes
2. **`002_views.sql`** - Alle public vw_* Views  
3. **`003_functions.sql`** - RPC Functions, Triggers, Stage Tracking

**Siehe:** `../migrations_postgresql/README.md` für Details

---

## 📁 Archiv

Alle alten Migrationen befinden sich in `archive/` für Referenzzwecke.

**Wichtig:** Diese archivierten Dateien sollten **nicht** mehr für neue Installationen verwendet werden!

---

## 🎯 **KONSOLIDIERTE STRUKTUR:**

### **1️⃣ Complete Schema** (`01_schema_and_tables.sql`)

- **Konsolidiert**: `00_schema_architecture` + `01_krai_core_tables` + `02-05_tables`
- **Erstellt**: Alle 10 Schemas mit 31+ Tabellen
- **Includes**: Extensions (uuid-ossp, pgvector), Optimized Indexes (No Duplicates)

### **2️⃣ Security & RLS** (`02_security_rls_triggers.sql`)

- **Konsolidiert**: `06_security_rls_policies` + `10_security_fixes`
- **Erstellt**: RLS Policies, Security Roles, Permissions
- **Includes**: Audit Functions, Security Views

### **3️⃣ Performance & Indexes** (`03_indexes_performance.sql`)

- **Umfasst**: HNSW Vector Indexes, GIN Full-Text, Composite Indexes
- **Erstellt**: 32+ Foreign Key Indexes für optimale JOIN Performance
- **Includes**: Materialized Views, Search Functions, Analytics
- **⚡ OPTIMIERT**: Alle Duplicate Indexes entfernt, Smart Index Cleanup

### **4️⃣ Extensions & Storage** (`04_extensions_and_storage.sql`)

- **Umfasst**: Validation Functions, Sample Data, Specialized Storage Buckets
- **Erstellt**: 3 Image Storage Buckets (Error, Manual, Parts) - Cost Optimized
- **Includes**: DSGVO-compliant Storage, Configuration Examples

### **5️⃣ Performance Testing** (`05_performance_test.sql`) ⭐ **NEU!**

- **Erstellt**: Umfassende Performance Test Suite
- **Testet**: Index Effectiveness, Vector Search, System Health
- **Includes**: Benchmark Functions, Health Monitoring, Performance Analytics

---

## 🚀 **QUICK START:**

```bash
# 1. Navigate to database migrations
cd database_migrations/

# 2. Run automatic migration (recommended)
./run_krai_migration.sh

# 3. Or run manually step by step:
docker exec -i supabase_db_KR-AI-Engine psql -U postgres -d postgres < 01_schema_and_tables.sql
docker exec -i supabase_db_KR-AI-Engine psql -U postgres -d postgres < 02_security_rls_triggers.sql
docker exec -i supabase_db_KR-AI-Engine psql -U postgres -d postgres < 03_indexes_performance.sql
docker exec -i supabase_db_KR-AI-Engine psql -U postgres -d postgres < 04_extensions_and_storage.sql
docker exec -i supabase_db_KR-AI-Engine psql -U postgres -d postgres < 05_performance_test.sql

# 4. Run standalone performance tests anytime:
./test_performance_standalone.sh
./test_performance_standalone.sh --detailed
./test_performance_standalone.sh --benchmark
```

---

## ✅ **ERFOLGS-VALIDIERUNG:**

Nach der Migration solltest du haben:

- **🏗️ 10 Schemas**: `krai_core`, `krai_intelligence`, `krai_content`, `krai_config`, `krai_system`, `krai_ml`, `krai_parts`, `krai_service`, `krai_users`, `krai_integrations`
- **📊 31+ Tabellen** mit korrekten Foreign Keys
- **🔢 400+ Spalten** optimiert für Performance  
- **🗄️ 3 Storage Buckets**: `krai-documents`, `krai-images`, `krai-videos`
- **🔒 RLS Policies** auf allen Tabellen aktiv
- **⚡ Performance Indexes** (HNSW für Vectors, GIN für Full-Text)
- **📈 Analytics Functions** für Monitoring
- **🧪 Sample Data** für Testing
- **⚡ Performance Test Suite** mit Index- und Health-Checks

---

## 🔧 **NEUE FEATURES IN DER KONSOLIDIERTEN VERSION:**

### ✨ **Automatische Storage Integration**

- **Storage Buckets** werden direkt in Step 4 erstellt
- **RLS Policies für Storage** automatisch angewendet
- **Utility Functions** für Storage-Management

### 🛡️ **Enhanced Security**

- Alle **Security Fixes** aus der 12-Schritt Version integriert
- **Improved Role Management** mit proper permissions
- **Audit Functions** mit besserer Performance

### ⚡ **Performance Optimiert**

- **Redundante Indexes entfernt** (aus Step 11)
- **HNSW Indexes** für Vector Search optimiert
- **Materialized Views** für Analytics

### 🧪 **Production Ready**

- **Sample Data** für sofortiges Testing
- **Validation Functions** für Konfigurationscheck
- **Real Error Codes** aus HP Documentation

### ⚡ **Performance Testing** ⭐ **NEU!**

- **Automated Index Testing** - Überprüft alle Performance Indexes
- **Vector Search Benchmarks** - HNSW Index Effectiveness
- **System Health Monitoring** - Cache Hit Ratio, Connections, etc.
- **Stress Testing** - Concurrent Query Performance
- **Standalone Test Tool** - Jederzeit ausführbar für Monitoring

---

## 🚨 **MIGRATION VON ALTER VERSION:**

Falls du die **alte 12-Schritt Version** bereits ausgeführt hast:

```bash
# Option 1: Database Reset (empfohlen)
cd supabase && supabase db reset

# Option 2: Manual cleanup (advanced)
# Lösche alle krai_* Schemas und führe Konsolidierte Version aus
```

---

## 🎯 **WARUM KONSOLIDIERUNG?**

### ❌ **Probleme der 12-Schritt Version:**

- Zu **viele kleine Dateien** schwer zu überblicken
- **Hohe Fehlerrate** bei partieller Ausführung
- **Fixes kamen später** → Inkonsistente Struktur
- **Storage Buckets** waren separater Schritt
- **Wartung kompliziert**

### ✅ **Vorteile der Konsolidierten Version:**

- **4 logische Blöcke** statt 12 fragmentierte Schritte
- **Alle Fixes integriert** von Anfang an
- **Storage inklusive** - keine separaten Schritte
- **Atomic Execution** - weniger Fehlerrisiko
- **Bessere Wartbarkeit** und Dokumentation

---

## 🏆 **RESULT:**

**Die KRAI Consolidated Schema Migration ist die definitive, production-ready Version für alle zukünftigen Deployments!**

*Erstellt: September 2025*  
*Status: ✅ Production Ready*  
*Empfehlung: 🚀 Verwende diese Version für alle neuen Installationen*

---

## Phase 2: Context-Aware Media & Multi-Modal Embeddings (Migrations 116-118)

### Migration 116: Context-Aware Media Fields

**Purpose**: Add context extraction fields to images, videos, and links

**Tables modified**: krai_content.images, krai_content.videos, krai_content.links

**New columns**:

- context_caption, page_header, surrounding_paragraphs, related_error_codes, related_products, related_chunks, context_embedding (images)
- context_description, related_products, related_chunks, page_number, context_embedding (videos)
- context_description, related_chunks, context_embedding (links)

**Indexes**: HNSW for context_embedding, GIN for array columns

**Triggers updated**: public.videos and public.links view triggers

### Migration 117: Multi-Vector Embeddings

**Purpose**: Support multiple embeddings per source (text, visual, table, context)

**New table**: krai_intelligence.unified_embeddings

**Supports**: Text embeddings (nomic-embed-text), Visual embeddings (ColQwen2.5), Table embeddings, Context embeddings

**Schema**: source_id, source_type, embedding, model_name, embedding_context, metadata

**Helper function**: krai_intelligence.get_embeddings_by_source()

**Features**:

- Multiple embeddings per source entity
- Model tracking for embedding provenance
- Flexible metadata storage
- Performance-optimized indexes

### Migration 118: Structured Tables & Unified Search

**Purpose**: Store structured table data and enable unified multimodal search

**New table**: krai_intelligence.structured_tables

**Schema**: table_data (JSONB), table_markdown, column_headers, table_embedding, context_embedding, column_embeddings

**New RPC functions**:

- krai_intelligence.match_multimodal() - Unified search across text chunks, images, videos, links, tables
- krai_intelligence.match_images_by_context() - Context-aware image search

**Features**:

- Preserved table structure with JSONB storage
- Per-column embeddings for advanced table search
- Unified semantic search across all modalities
- Context-aware retrieval

### Migration Order & Dependencies

**Important**: Migrations 116-118 must be run in order as 118 depends on columns added in 116

**Verification query**:

```sql
SELECT migration_name, applied_at FROM krai_system.migrations WHERE migration_name LIKE '11%' ORDER BY migration_name;
```

### Usage Examples

#### Example 1: Search across all modalities

```sql
SELECT * FROM krai_intelligence.match_multimodal(
  (SELECT embedding FROM krai_intelligence.chunks LIMIT 1),
  0.7,  -- similarity threshold
  10    -- max results
);
```

#### Example 2: Search images by context

```sql
SELECT * FROM krai_intelligence.match_images_by_context(
  (SELECT context_embedding FROM krai_content.images WHERE context_embedding IS NOT NULL LIMIT 1),
  0.6,
  5
);
```

#### Example 3: Get all embeddings for a chunk

```sql
SELECT * FROM krai_intelligence.get_embeddings_by_source(
  'chunk-uuid-here',
  'text'  -- optional: filter by type
);
```

### Troubleshooting

**Issue**: "HNSW index creation fails"

- **Solution**: Ensure pgvector extension is loaded and vector dimension matches (768)
- **Check**: `SELECT extname FROM pg_extension WHERE extname = 'vector';`

**Issue**: "Triggers not updating new columns"

- **Solution**: Verify triggers were recreated in migration 116
- **Check**: `SELECT tgname FROM pg_trigger WHERE tgrelid = 'public.videos'::regclass;`

**Issue**: "krai_intelligence.match_multimodal returns no results"

- **Solution**: Ensure embedding vectors are populated in target tables
- **Check**: `SELECT COUNT(*) FROM krai_content.images WHERE context_embedding IS NOT NULL;`

---

## 🔧 **AKTUELLE FIXES (Oktober 2025):**

### **Neue Migrations:**

- `100_update_rpc_function_add_chunk_id.sql` - Fügt chunk_id zu insert_error_code hinzu
- `101_fix_links_manufacturer_id.sql` - Setzt manufacturer_id für alle Links
- `116_add_context_aware_media.sql` - Context-aware fields for media tables
- `117_add_multi_vector_embeddings.sql` - Multi-vector embeddings support
- `118_add_structured_tables.sql` - Structured tables and unified search

**Siehe:** `DB_FIXES_CHECKLIST.md` im Root für Details!
