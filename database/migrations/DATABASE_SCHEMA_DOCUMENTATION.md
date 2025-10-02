# 🗄️ KRAI Database Schema - Vollständige Entwickler-Dokumentation

**Version:** 2.0.0  
**Letzte Aktualisierung:** Oktober 2025  
**Datenbank:** PostgreSQL 15+ mit pgvector Extension  
**Cloud Provider:** Supabase

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Schema-Architektur](#schema-architektur)
3. [Core Schema (krai_core)](#core-schema-krai_core)
4. [Intelligence Schema (krai_intelligence)](#intelligence-schema-krai_intelligence)
5. [Content Schema (krai_content)](#content-schema-krai_content)
6. [Config Schema (krai_config)](#config-schema-krai_config)
7. [Service Schema (krai_service)](#service-schema-krai_service)
8. [System Schema (krai_system)](#system-schema-krai_system)
9. [Agent Schema (krai_agent)](#agent-schema-krai_agent)
10. [PostgREST Views (public.vw_*)](#postgrest-views-publicvw_)
11. [Weitere Schemas](#weitere-schemas)
12. [Python Integration](#python-integration)
13. [Best Practices](#best-practices)

---

## 🎯 Übersicht

Das KRAI Database Schema ist in **11 spezialisierte Schemas** unterteilt, die jeweils einen funktionalen Bereich der Anwendung abdecken. Insgesamt umfasst das Schema **34+ Tabellen**, **11 PostgREST Views**, **100+ Indexes** und **vollständige RLS-Policies**.

### Hauptmerkmale

- ✅ **Modular**: 11 funktionale Schemas + public views
- ✅ **Skalierbar**: Optimiert für große Dokumentenmengen (9,223 images, 58,614 chunks)
- ✅ **AI-Ready**: pgvector für Embeddings, n8n Agent Memory, HNSW-Indexes
- ✅ **Secure**: Row Level Security auf allen Tabellen
- ✅ **Performant**: Composite Indexes, Materialized Views, PostgREST Views
- ✅ **IPv4/IPv6-kompatibel**: Public Views als Bridge für PostgREST

---

## 🏗️ Schema-Architektur

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           KRAI DATABASE                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  krai_core  │  │ krai_intel  │  │krai_content │  │ krai_agent  │    │
│  │             │  │  ligence    │  │             │  │             │    │
│  │• manufact.  │  │ • chunks    │  │ • chunks    │  │ • memory    │    │
│  │• products   │  │ • embeddings│  │ • images    │  │ (n8n)       │    │
│  │• documents  │  │ • error_codes│ │ • links     │  └─────────────┘    │
│  └─────────────┘  └─────────────┘  └─────────────┘         │           │
│                                                              │           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │           │
│  │krai_config  │  │krai_service │  │krai_system  │         │           │
│  │             │  │             │  │             │         │           │
│  │ • options   │  │• technicians│  │ • queue     │         │           │
│  │ • features  │  │ • calls     │  │ • audit     │         │           │
│  └─────────────┘  └─────────────┘  └─────────────┘         │           │
│                                                              │           │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │            PUBLIC VIEWS (PostgREST Bridge - IPv4)              │     │
│  │  vw_agent_memory • vw_images • vw_chunks • vw_documents        │     │
│  │  vw_embeddings • vw_error_codes • vw_audit_log • vw_*          │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Schema (krai_core)

Das Core-Schema enthält die **Hauptgeschäftsobjekte**: Hersteller, Produkte, Produktserien und Dokumente.

### 1. `krai_core.manufacturers`

**Beschreibung:** Hersteller von Druckern und verwandten Produkten.

**Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY, DEFAULT uuid_generate_v4() |
| `name` | VARCHAR(100) | Herstellername | NOT NULL, UNIQUE |
| `short_name` | VARCHAR(10) | Kurzname/Akronym | NULLABLE |
| `country` | VARCHAR(50) | Hauptsitzland | NULLABLE |
| `website` | VARCHAR(255) | Webseite | NULLABLE |
| `support_email` | VARCHAR(255) | Support E-Mail | NULLABLE |
| `is_competitor` | BOOLEAN | Konkurrent? | DEFAULT false |
| `market_share_percent` | DECIMAL(5,2) | Marktanteil | NULLABLE |
| `created_at` | TIMESTAMPTZ | Erstellungszeitpunkt | DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | Aktualisierungszeitpunkt | DEFAULT NOW() |

**Python Beispiel:**

```python
from supabase import create_client, Client

supabase: Client = create_client(supabase_url, supabase_key)

# Hersteller erstellen
manufacturer = supabase.table('manufacturers').insert({
    'name': 'HP Inc.',
    'short_name': 'HP',
    'country': 'USA',
    'website': 'https://www.hp.com',
    'is_competitor': False
}).execute()

# Hersteller abfragen
manufacturers = supabase.table('manufacturers').select('*').execute()

# Nach Namen filtern
hp = supabase.table('manufacturers').select('*').eq('name', 'HP Inc.').single().execute()
```

---

### 2. `krai_core.product_series`

**Beschreibung:** Produktserien/Familien eines Herstellers.

**Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY |
| `manufacturer_id` | UUID | Hersteller-Referenz | FOREIGN KEY → manufacturers(id), NOT NULL |
| `series_name` | VARCHAR(100) | Serienname | NOT NULL |
| `series_code` | VARCHAR(50) | Seriencode | NULLABLE |
| `launch_date` | DATE | Markteinführung | NULLABLE |
| `end_of_life_date` | DATE | Ende der Unterstützung | NULLABLE |
| `target_market` | VARCHAR(100) | Zielmarkt | NULLABLE |
| `key_features` | JSONB | Hauptmerkmale | DEFAULT '{}' |
| `successor_series_id` | UUID | Nachfolge-Serie | FOREIGN KEY → product_series(id) |
| `created_at` | TIMESTAMPTZ | Erstellungszeitpunkt | DEFAULT NOW() |

**UNIQUE Constraint:** `(manufacturer_id, series_name)`

**Python Beispiel:**

```python
# Serie erstellen mit JSONB Features
series = supabase.table('product_series').insert({
    'manufacturer_id': '550e8400-e29b-41d4-a716-446655440001',
    'series_name': 'LaserJet Pro',
    'series_code': 'LJ-PRO',
    'target_market': 'Small Business',
    'key_features': {
        'print_technology': 'Laser',
        'color_capable': True,
        'network_ready': True,
        'duplex_standard': True
    }
}).execute()

# Alle Serien eines Herstellers
series_list = supabase.table('product_series')\
    .select('*, manufacturers(name)')\
    .eq('manufacturer_id', manufacturer_id)\
    .execute()
```

---

### 3. `krai_core.products`

**Beschreibung:** Einzelne Produktmodelle mit detaillierten Spezifikationen.

**Wichtige Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY |
| `manufacturer_id` | UUID | Hersteller | FOREIGN KEY → manufacturers(id), NOT NULL |
| `series_id` | UUID | Produktserie | FOREIGN KEY → product_series(id) |
| `parent_id` | UUID | Übergeordnetes Produkt | FOREIGN KEY → products(id) |
| `model_number` | VARCHAR(100) | Modellnummer | NOT NULL |
| `model_name` | VARCHAR(200) | Modellname | NULLABLE |
| `product_type` | VARCHAR(50) | Produkttyp | DEFAULT 'printer' |
| `print_technology` | VARCHAR(50) | Drucktechnologie | NULLABLE |
| `max_print_speed_ppm` | INTEGER | Max. Druckgeschwindigkeit | NULLABLE |
| `duplex_capable` | BOOLEAN | Duplex-fähig? | DEFAULT false |
| `network_capable` | BOOLEAN | Netzwerkfähig? | DEFAULT false |
| `option_dependencies` | JSONB | Optionsabhängigkeiten | DEFAULT '{}' |
| `replacement_parts` | JSONB | Ersatzteile | DEFAULT '{}' |
| `common_issues` | JSONB | Häufige Probleme | DEFAULT '{}' |

**Python Beispiel:**

```python
# Produkt mit komplexen JSONB Daten erstellen
product = supabase.table('products').insert({
    'manufacturer_id': manufacturer_id,
    'series_id': series_id,
    'model_number': 'M404dn',
    'model_name': 'LaserJet Pro M404dn',
    'product_type': 'printer',
    'print_technology': 'Laser',
    'max_print_speed_ppm': 40,
    'duplex_capable': True,
    'network_capable': True,
    'option_dependencies': {
        'memory_upgrade': ['512MB', '1GB'],
        'paper_tray': ['500_sheet', '1500_sheet']
    },
    'replacement_parts': {
        'toner': 'CF259A',
        'drum': 'CF232A',
        'fuser': 'RM2-6431'
    },
    'common_issues': {
        'paper_jam': 'Check paper path and rollers',
        'print_quality': 'Clean drum and check toner level'
    }
}).execute()

# Produkte mit Hersteller und Serie abfragen
products = supabase.table('products')\
    .select('*, manufacturers(name), product_series(series_name)')\
    .eq('product_type', 'printer')\
    .order('model_name')\
    .execute()
```

---

### 4. `krai_core.documents`

**Beschreibung:** Service-Manuals, Datenblätter und andere Dokumente.

**Wichtige Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY |
| `manufacturer_id` | UUID | Hersteller | FOREIGN KEY → manufacturers(id) |
| `product_id` | UUID | Produkt | FOREIGN KEY → products(id) |
| `filename` | VARCHAR(255) | Dateiname | NOT NULL |
| `file_size` | BIGINT | Dateigröße (Bytes) | NULLABLE |
| `file_hash` | VARCHAR(64) | SHA-256 Hash | NULLABLE |
| `storage_path` | TEXT | Speicherpfad | NULLABLE |
| `document_type` | VARCHAR(100) | Dokumenttyp | NULLABLE |
| `language` | VARCHAR(10) | Sprache | DEFAULT 'en' |
| `version` | VARCHAR(50) | Version | NULLABLE |
| `page_count` | INTEGER | Seitenanzahl | NULLABLE |
| `content_text` | TEXT | Extrahierter Text | NULLABLE |
| `extracted_metadata` | JSONB | Extrahierte Metadaten | DEFAULT '{}' |
| `processing_status` | VARCHAR(50) | Verarbeitungsstatus | DEFAULT 'pending' |
| `confidence_score` | DECIMAL(3,2) | Confidence Score | NULLABLE |
| `manufacturer` | VARCHAR(100) | Hersteller (klassifiziert) | NULLABLE |
| `series` | VARCHAR(100) | Serie (klassifiziert) | NULLABLE |
| `models` | TEXT[] | Modelle (klassifiziert) | NULLABLE |

**Python Beispiel:**

```python
import hashlib
from pathlib import Path

# Dokument hochladen und erstellen
def upload_document(file_path: str, manufacturer_id: str):
    # Datei lesen
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Hash berechnen
    file_hash = hashlib.sha256(file_content).hexdigest()
    file_size = len(file_content)
    filename = Path(file_path).name
    
    # Duplikat prüfen
    existing = supabase.table('documents')\
        .select('id')\
        .eq('file_hash', file_hash)\
        .execute()
    
    if existing.data:
        return {'error': 'Document already exists', 'document_id': existing.data[0]['id']}
    
    # Dokument erstellen
    document = supabase.table('documents').insert({
        'manufacturer_id': manufacturer_id,
        'filename': filename,
        'file_size': file_size,
        'file_hash': file_hash,
        'document_type': 'Service Manual',
        'processing_status': 'pending',
        'extracted_metadata': {
            'upload_date': 'now',
            'original_path': file_path
        }
    }).execute()
    
    return document.data[0]

# Dokumente nach Status filtern
pending_docs = supabase.table('documents')\
    .select('*')\
    .eq('processing_status', 'pending')\
    .order('created_at', desc=True)\
    .execute()

# Volltext-Suche (wenn content_text gefüllt)
search_results = supabase.rpc('search_documents_optimized', {
    'search_query': 'paper jam error',
    'manufacturer_filter': manufacturer_id,
    'limit_results': 20
}).execute()
```

---

### 5. `krai_core.document_relationships`

**Beschreibung:** Beziehungen zwischen Dokumenten (z.B. Updates, Revisionen).

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `primary_document_id` | UUID | Hauptdokument |
| `secondary_document_id` | UUID | Bezogenes Dokument |
| `relationship_type` | VARCHAR(50) | Beziehungstyp (update, revision, supplement) |
| `relationship_strength` | DECIMAL(3,2) | Stärke (0.0-1.0) |
| `auto_discovered` | BOOLEAN | Automatisch erkannt? |

**Python Beispiel:**

```python
# Dokumentbeziehung erstellen
relationship = supabase.table('document_relationships').insert({
    'primary_document_id': old_doc_id,
    'secondary_document_id': new_doc_id,
    'relationship_type': 'update',
    'relationship_strength': 0.95,
    'auto_discovered': True
}).execute()

# Alle Updates eines Dokuments finden
updates = supabase.table('document_relationships')\
    .select('secondary_document_id, documents(filename, version)')\
    .eq('primary_document_id', document_id)\
    .eq('relationship_type', 'update')\
    .execute()
```

---

## 🧠 Intelligence Schema (krai_intelligence)

Dieses Schema enthält **AI/ML-bezogene Daten**: Text-Chunks, Embeddings, Error Codes.

### 1. `krai_intelligence.chunks`

**Beschreibung:** Text-Chunks für Semantic Search und RAG.

**Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY |
| `document_id` | UUID | Dokument-Referenz | FOREIGN KEY → documents(id), NOT NULL, ON DELETE CASCADE |
| `text_chunk` | TEXT | Text-Inhalt | NOT NULL |
| `chunk_index` | INTEGER | Chunk-Index | NOT NULL |
| `page_start` | INTEGER | Startseite | NULLABLE |
| `page_end` | INTEGER | Endseite | NULLABLE |
| `processing_status` | VARCHAR(20) | Status | CHECK IN ('pending', 'completed', 'failed') |
| `fingerprint` | VARCHAR(32) | MD5 Fingerprint | NOT NULL |
| `metadata` | JSONB | Zusätzliche Metadaten | DEFAULT '{}' |

**Python Beispiel:**

```python
import hashlib

# Chunk erstellen
def create_chunk(document_id: str, text: str, index: int, page: int):
    fingerprint = hashlib.md5(text.encode()).hexdigest()
    
    chunk = supabase.table('chunks').insert({
        'document_id': document_id,
        'text_chunk': text,
        'chunk_index': index,
        'page_start': page,
        'page_end': page,
        'fingerprint': fingerprint,
        'processing_status': 'pending',
        'metadata': {
            'chunk_size': len(text),
            'chunk_strategy': 'semantic'
        }
    }).execute()
    
    return chunk.data[0]

# Chunks eines Dokuments abrufen
chunks = supabase.table('chunks')\
    .select('*')\
    .eq('document_id', document_id)\
    .order('chunk_index')\
    .execute()
```

---

### 2. `krai_intelligence.embeddings`

**Beschreibung:** Vector Embeddings für Semantic Search.

**Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY |
| `chunk_id` | UUID | Chunk-Referenz | FOREIGN KEY → chunks(id), NOT NULL, ON DELETE CASCADE |
| `embedding` | vector(768) | Embedding-Vektor | NULLABLE |
| `model_name` | VARCHAR(100) | Modellname | NOT NULL |
| `model_version` | VARCHAR(50) | Modellversion | DEFAULT 'latest' |

**WICHTIG:** Nutzt **pgvector Extension** mit **HNSW Index** für schnelle Nearest-Neighbor-Suche!

**Python Beispiel:**

```python
from typing import List
import numpy as np

# Embedding erstellen (z.B. mit embeddinggemma)
def create_embedding(chunk_id: str, embedding_vector: List[float]):
    # Vector muss exakt 768 Dimensionen haben!
    assert len(embedding_vector) == 768
    
    # Vector als String formatieren für PostgreSQL
    vector_str = '[' + ','.join(map(str, embedding_vector)) + ']'
    
    embedding = supabase.table('embeddings').insert({
        'chunk_id': chunk_id,
        'embedding': vector_str,
        'model_name': 'embeddinggemma',
        'model_version': 'latest'
    }).execute()
    
    return embedding.data[0]

# Ähnlichkeitssuche durchführen
def semantic_search(query_vector: List[float], limit: int = 10):
    vector_str = '[' + ','.join(map(str, query_vector)) + ']'
    
    # Nutzt den find_similar_chunks RPC
    results = supabase.rpc('find_similar_chunks', {
        'query_embedding': vector_str,
        'similarity_threshold': 0.7,
        'limit_results': limit
    }).execute()
    
    return results.data

# Embedding eines Chunks abrufen
embedding = supabase.table('embeddings')\
    .select('embedding')\
    .eq('chunk_id', chunk_id)\
    .single()\
    .execute()
```

---

### 3. `krai_intelligence.error_codes`

**Beschreibung:** Extrahierte Fehlercodes aus Dokumenten.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `chunk_id` | UUID | Chunk-Referenz (optional) |
| `document_id` | UUID | Dokument-Referenz (optional) |
| `manufacturer_id` | UUID | Hersteller-Referenz |
| `error_code` | VARCHAR(20) | Fehlercode (z.B. "10.22.15") |
| `error_description` | TEXT | Beschreibung |
| `solution_text` | TEXT | Lösungstext |
| `page_number` | INTEGER | Seitennummer |
| `confidence_score` | DECIMAL(3,2) | Confidence Score |
| `severity_level` | VARCHAR(20) | Schweregrad (low, medium, high, critical) |

**Python Beispiel:**

```python
# Error Code extrahieren und speichern
def extract_error_code(document_id: str, code: str, description: str, solution: str):
    error_code = supabase.table('error_codes').insert({
        'document_id': document_id,
        'manufacturer_id': manufacturer_id,
        'error_code': code,
        'error_description': description,
        'solution_text': solution,
        'page_number': 42,
        'confidence_score': 0.95,
        'extraction_method': 'regex',
        'severity_level': 'medium'
    }).execute()
    
    return error_code.data[0]

# Error Codes nach Hersteller suchen
errors = supabase.table('error_codes')\
    .select('*, manufacturers(name)')\
    .eq('manufacturer_id', manufacturer_id)\
    .order('error_code')\
    .execute()

# Nach Error Code suchen
error = supabase.table('error_codes')\
    .select('*')\
    .eq('error_code', '10.22.15')\
    .single()\
    .execute()
```

---

## 📄 Content Schema (krai_content)

Schema für **Medien-Inhalte**: Bilder, Links, Videos.

### 1. `krai_content.chunks`

**Beschreibung:** Content-Chunks (anders als intelligence.chunks - für verschiedene Content-Typen).

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `document_id` | UUID | Dokument-Referenz |
| `content` | TEXT | Inhalt |
| `chunk_type` | VARCHAR(50) | Typ (text, table, list, code) |
| `chunk_index` | INTEGER | Index |
| `page_number` | INTEGER | Seite |
| `section_title` | VARCHAR(255) | Abschnittstitel |

---

### 2. `krai_content.images`

**Beschreibung:** Extrahierte Bilder aus Dokumenten.

**Wichtige Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `document_id` | UUID | Dokument-Referenz |
| `chunk_id` | UUID | Chunk-Referenz (optional) |
| `storage_url` | TEXT | Cloudflare R2 URL |
| `file_hash` | VARCHAR(64) | Deduplikations-Hash |
| `image_type` | VARCHAR(50) | Typ (diagram, photo, chart, technical_drawing) |
| `ai_description` | TEXT | AI-generierte Beschreibung |
| `ocr_text` | TEXT | OCR-extrahierter Text |
| `figure_number` | VARCHAR(50) | Figurnummer (z.B. "3.2") |
| `figure_context` | TEXT | Kontext um Figur-Referenz |

**Python Beispiel:**

```python
# Bild aus Dokument extrahieren und speichern
def save_document_image(document_id: str, image_bytes: bytes, page: int, figure_num: str = None):
    import hashlib
    
    # Hash für Deduplikation
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    
    # Prüfen ob Bild bereits existiert
    existing = supabase.table('images')\
        .select('id')\
        .eq('file_hash', image_hash)\
        .execute()
    
    if existing.data:
        return existing.data[0]
    
    # Bild zu R2 hochladen (via Storage API)
    filename = f"{document_id}/page_{page}_{image_hash[:8]}.png"
    storage_response = supabase.storage\
        .from_('krai-document-images')\
        .upload(filename, image_bytes)
    
    # Public URL generieren
    storage_url = supabase.storage\
        .from_('krai-document-images')\
        .get_public_url(filename)
    
    # Bild in DB speichern
    image = supabase.table('images').insert({
        'document_id': document_id,
        'filename': filename,
        'storage_url': storage_url,
        'file_size': len(image_bytes),
        'file_hash': image_hash,
        'page_number': page,
        'image_type': 'technical_drawing',
        'figure_number': figure_num,
        'contains_text': False
    }).execute()
    
    return image.data[0]

# Bilder mit Figurnummern finden
figures = supabase.table('images')\
    .select('*')\
    .eq('document_id', document_id)\
    .not_.is_('figure_number', 'null')\
    .order('page_number')\
    .execute()
```

---

### 3. `krai_content.links` ⭐ **NEU!**

**Beschreibung:** Extrahierte Links aus PDFs (Videos, Tutorials, externe Ressourcen).

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `document_id` | UUID | Dokument-Referenz |
| `url` | TEXT | URL |
| `link_type` | VARCHAR(50) | Typ (video, external, tutorial) |
| `page_number` | INTEGER | Seite |
| `description` | TEXT | Beschreibung |
| `position_data` | JSONB | Position im PDF |
| `is_active` | BOOLEAN | Link aktiv? |

**Python Beispiel:**

```python
# Link aus PDF extrahieren
def extract_link(document_id: str, url: str, page: int, link_type: str = 'external'):
    link = supabase.table('links').insert({
        'document_id': document_id,
        'url': url,
        'link_type': link_type,
        'page_number': page,
        'description': 'Extracted from PDF',
        'position_data': {
            'rect': [100, 200, 300, 220],
            'page_height': 792,
            'page_width': 612
        },
        'is_active': True
    }).execute()
    
    return link.data[0]

# Alle Video-Links eines Dokuments
videos = supabase.table('links')\
    .select('*')\
    .eq('document_id', document_id)\
    .eq('link_type', 'video')\
    .eq('is_active', True)\
    .execute()

# View für Agent Context nutzen
media_context = supabase.table('document_media_context')\
    .select('*')\
    .eq('document_id', document_id)\
    .execute()
```

---

### 4. `krai_content.instructional_videos`

**Beschreibung:** Video-Referenzen (nur URLs, keine Dateien gespeichert).

**Python Beispiel:**

```python
# Video-Link speichern
video = supabase.table('instructional_videos').insert({
    'manufacturer_id': manufacturer_id,
    'title': 'How to replace drum cartridge',
    'video_url': 'https://youtube.com/watch?v=...',
    'duration_seconds': 180,
    'language': 'en'
}).execute()
```

---

## ⚙️ Config Schema (krai_config)

Schema für **Konfiguration und Features**.

### `krai_config.option_groups`

**Beschreibung:** Gruppen von Optionen (z.B. "Memory Upgrades", "Paper Handling").

### `krai_config.product_features`

**Beschreibung:** Features eines Produkts mit Werten.

**Python Beispiel:**

```python
# Feature zu Produkt hinzufügen
feature = supabase.table('product_features').insert({
    'product_id': product_id,
    'feature_id': option_group_id,
    'feature_value': '1GB RAM',
    'is_standard': False,
    'additional_cost_usd': 149.99
}).execute()
```

---

## 🔧 Service Schema (krai_service) ⭐ **AKTUALISIERT!**

Schema für **Service-Calls und Techniker**.

### 1. `krai_service.technicians` ⭐ **NEU!**

**Beschreibung:** Techniker-Stammdaten.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `user_id` | UUID | User-Referenz (optional) |
| `technician_name` | VARCHAR(255) | Name |
| `employee_id` | VARCHAR(50) | Mitarbeiter-ID |
| `email` | VARCHAR(255) | E-Mail |
| `certification_level` | VARCHAR(50) | Zertifizierungslevel |
| `specializations` | TEXT[] | Spezialisierungen |
| `is_active` | BOOLEAN | Aktiv? |

**Python Beispiel:**

```python
# Techniker erstellen
technician = supabase.table('technicians').insert({
    'technician_name': 'John Smith',
    'employee_id': 'TECH-001',
    'email': 'john.smith@company.com',
    'certification_level': 'Senior',
    'specializations': ['Laser Printers', 'Network Issues'],
    'is_active': True
}).execute()

# Aktive Techniker abrufen
active_techs = supabase.table('technicians')\
    .select('*')\
    .eq('is_active', True)\
    .order('technician_name')\
    .execute()
```

---

### 2. `krai_service.service_calls`

**Beschreibung:** Service-Anfragen.

**Wichtige Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `manufacturer_id` | UUID | Hersteller |
| `product_id` | UUID | Produkt |
| `assigned_technician_id` | UUID | Zugewiesener Techniker → technicians(id) |
| `call_status` | VARCHAR(50) | Status (open, assigned, in_progress, completed) |
| `customer_name` | VARCHAR(255) | Kundenname |
| `issue_description` | TEXT | Problembeschreibung |
| `scheduled_date` | TIMESTAMPTZ | Geplanter Termin |

**Python Beispiel:**

```python
# Service Call erstellen
call = supabase.table('service_calls').insert({
    'manufacturer_id': manufacturer_id,
    'product_id': product_id,
    'assigned_technician_id': technician_id,
    'call_status': 'open',
    'priority_level': 3,
    'customer_name': 'ABC Company',
    'issue_description': 'Printer shows error 10.22.15',
    'scheduled_date': '2025-10-15T10:00:00Z'
}).execute()

# Service Calls eines Technikers
my_calls = supabase.table('service_calls')\
    .select('*, products(model_name), manufacturers(name)')\
    .eq('assigned_technician_id', technician_id)\
    .in_('call_status', ['open', 'assigned'])\
    .order('priority_level', desc=True)\
    .execute()
```

---

### 3. `krai_service.service_history`

**Beschreibung:** Service-Verlauf.

**Wichtige Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `service_call_id` | UUID | Service Call Referenz |
| `performed_by` | UUID | Durchgeführt von → technicians(id) |
| `service_date` | TIMESTAMPTZ | Service-Datum |
| `service_notes` | TEXT | Notizen |
| `parts_used` | JSONB | Verwendete Teile |
| `service_type` | VARCHAR(50) | Service-Typ |
| `outcome` | VARCHAR(100) | Ergebnis |

**Python Beispiel:**

```python
# Service durchführen und dokumentieren
service = supabase.table('service_history').insert({
    'service_call_id': call_id,
    'performed_by': technician_id,
    'service_date': 'now',
    'service_type': 'repair',
    'service_notes': 'Replaced drum cartridge, cleaned paper path',
    'parts_used': [
        {'part_number': 'CF232A', 'quantity': 1, 'description': 'Drum Unit'},
        {'part_number': 'RM2-6431', 'quantity': 1, 'description': 'Fuser Assembly'}
    ],
    'labor_hours': 2.5,
    'outcome': 'resolved'
}).execute()

# Service-Historie abrufen
history = supabase.table('service_history')\
    .select('*, technicians(technician_name), service_calls(customer_name)')\
    .eq('service_call_id', call_id)\
    .order('service_date', desc=True)\
    .execute()
```

---

## 🎛️ System Schema (krai_system)

Schema für **System-Operations**.

### 1. `krai_system.processing_queue`

**Beschreibung:** Verarbeitungswarteschlange für asynchrone Tasks.

**Python Beispiel:**

```python
# Task in Queue einfügen
task = supabase.table('processing_queue').insert({
    'document_id': document_id,
    'task_type': 'text_extraction',
    'priority': 5,
    'status': 'pending'
}).execute()

# Nächsten Task abrufen
next_task = supabase.table('processing_queue')\
    .select('*')\
    .eq('status', 'pending')\
    .order('priority', desc=True)\
    .order('created_at')\
    .limit(1)\
    .execute()

# Task als abgeschlossen markieren
supabase.table('processing_queue')\
    .update({'status': 'completed', 'completed_at': 'now'})\
    .eq('id', task_id)\
    .execute()
```

---

### 2. `krai_system.audit_log`

**Beschreibung:** Audit-Trail für alle Änderungen.

**Python Beispiel:**

```python
# Automatisch via Trigger - aber manuelles Logging möglich
audit = supabase.table('audit_log').insert({
    'table_name': 'documents',
    'record_id': document_id,
    'operation': 'UPDATE',
    'old_values': {'processing_status': 'pending'},
    'new_values': {'processing_status': 'completed'},
    'changed_by': 'system'
}).execute()
```

---

## 🤖 Agent Schema (krai_agent)

Das Agent-Schema enthält Tabellen für **n8n AI Agent Integration** und **Conversation Memory**.

### 1. `krai_agent.memory`

**Beschreibung:** Conversation Memory für n8n Postgres Memory Module.

**Spalten:**

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | UUID | Primärschlüssel | PRIMARY KEY, DEFAULT uuid_generate_v4() |
| `session_id` | VARCHAR(255) | n8n Session Identifier | NOT NULL |
| `role` | VARCHAR(50) | Message Role | NOT NULL, CHECK IN ('user', 'assistant', 'system', 'function', 'tool') |
| `content` | TEXT | Message Content | NOT NULL |
| `metadata` | JSONB | Additional Data | DEFAULT '{}' |
| `tokens_used` | INTEGER | Token Count | DEFAULT 0 |
| `created_at` | TIMESTAMPTZ | Erstellungszeitpunkt | DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | Aktualisierungszeitpunkt | DEFAULT NOW() |

**Indexes:**

```sql
CREATE INDEX idx_memory_session_id ON krai_agent.memory(session_id);
CREATE INDEX idx_memory_created_at ON krai_agent.memory(created_at DESC);
CREATE INDEX idx_memory_session_created ON krai_agent.memory(session_id, created_at DESC);
```

**Python Beispiel:**

```python
# Get conversation history
memory = supabase.table('vw_agent_memory')\
    .select('*')\
    .eq('session_id', 'user-123')\
    .order('created_at', desc=False)\
    .execute()

# Add new message
supabase.table('vw_agent_memory').insert({
    'session_id': 'user-123',
    'role': 'user',
    'content': 'What is error code E001?',
    'metadata': {'source': 'web_ui'}
}).execute()
```

**Helper Functions:**

```sql
-- Get recent memory for session
SELECT * FROM krai_agent.get_session_memory('session-id', 20);

-- Clear old memory (older than 30 days)
SELECT krai_agent.clear_old_memory(30);
```

---

## 🌐 PostgREST Views (public.vw_*)

**Problem:** Supabase Server ist **IPv6-only**, asyncpg kann von IPv4-Clients nicht verbinden. PostgREST kann nur auf `public` Schema zugreifen.

**Lösung:** **Public Views** als Bridge zu allen krai_* Schemas.

### Verfügbare Views

| View Name | Source Table | Zweck | Rows (Stand 02.10.2025) |
|-----------|--------------|-------|-------------------------|
| `vw_agent_memory` | krai_agent.memory | **AI Agent Memory (n8n)** | 3 |
| `vw_audit_log` | krai_system.audit_log | System Change Log | 0 |
| `vw_processing_queue` | krai_system.processing_queue | Task Status | 0 |
| `vw_documents` | krai_core.documents | Document Metadata | 34 |
| `vw_images` | krai_content.images | **Image Deduplication** | 9,223 |
| `vw_chunks` | krai_content.chunks | Text Chunks | 58,614 |
| `vw_embeddings` | krai_intelligence.embeddings | Vector Embeddings | 0 |
| `vw_error_codes` | krai_intelligence.error_codes | Error Solutions | 0 |
| `vw_manufacturers` | krai_core.manufacturers | Manufacturer Info | 6 |
| `vw_products` | krai_core.products | Product Specs | 0 |
| `vw_webhook_logs` | krai_integrations.webhook_logs | Webhook History | 0 |

### Beispiel-Nutzung

**JavaScript (PostgREST):**

```javascript
const { createClient } = require('@supabase/supabase-js')

// Service Role Key für cross-schema access
const client = createClient(
  'https://crujfdpqdjzcfqeyhang.supabase.co',
  process.env.SUPABASE_SERVICE_ROLE_KEY
)

// Query via View (statt direkter Tabelle)
const { data } = await client
  .from('vw_images')  // View im public schema
  .select('filename, file_hash, ai_description')
  .eq('file_hash', hash)
  .limit(1)

// Count via View
const { count } = await client
  .from('vw_chunks')
  .select('id', { count: 'exact' })
  .eq('document_id', docId)
```

**Python (Supabase Client):**

```python
from supabase import create_client

client = create_client(url, service_role_key)

# Image deduplication via view
existing = client.table('vw_images')\
    .select('id, filename, file_hash')\
    .eq('file_hash', image_hash)\
    .limit(1)\
    .execute()

if existing.data:
    print(f"Duplicate found: {existing.data[0]['filename']}")
```

**Warum Views?**

✅ **IPv4-kompatibel:** Funktioniert auch wenn asyncpg nicht verbinden kann  
✅ **PostgREST-ready:** Public schema ist für PostgREST zugänglich  
✅ **RLS-preserved:** Row Level Security wird beibehalten  
✅ **Cross-schema:** Alle krai_* Schemas in einem Namespace  
✅ **Performance:** Gleich schnell wie direkte Tabellen-Queries  

### Migrations

- `05_public_views_for_postgrest.sql` - Core Views (images, chunks, embeddings)
- `06_agent_views_complete.sql` - Agent Views (documents, logs, queue, etc.)
- `07_agent_memory_table.sql` - Memory Tabelle + View

---

## 🔐 Weitere Schemas

### `krai_ml` - Machine Learning
- `model_registry`: AI-Modell-Versionen
- `model_performance_history`: Performance-Metriken

### `krai_parts` - Ersatzteile
- `parts_catalog`: Ersatzteil-Katalog
- `inventory_levels`: Lagerbestände

### `krai_users` - Benutzer
- `users`: Benutzer-Accounts
- `user_sessions`: Login-Sessions

### `krai_integrations` - Integrationen
- `api_keys`: API-Schlüssel
- `webhook_logs`: Webhook-Aufrufe

---

## 🐍 Python Integration - Vollständiges Beispiel

### Setup

```python
from supabase import create_client, Client
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Client initialisieren
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)
```

---

### Komplettes Document Processing Beispiel

```python
import hashlib
from pathlib import Path
import PyMuPDF  # fitz

class DocumentProcessor:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def process_document(self, file_path: str, manufacturer_id: str) -> Dict[str, Any]:
        """
        Vollständiger Document Processing Workflow
        """
        # 1. Dokument erstellen
        document = self._create_document(file_path, manufacturer_id)
        document_id = document['id']
        
        # 2. PDF öffnen und Text extrahieren
        pdf = PyMuPDF.open(file_path)
        
        # 3. Text-Chunks erstellen
        chunks = self._extract_text_chunks(pdf, document_id)
        
        # 4. Bilder extrahieren
        images = self._extract_images(pdf, document_id)
        
        # 5. Links extrahieren
        links = self._extract_links(pdf, document_id)
        
        # 6. Dokument als "completed" markieren
        self.supabase.table('documents')\
            .update({
                'processing_status': 'completed',
                'page_count': len(pdf)
            })\
            .eq('id', document_id)\
            .execute()
        
        pdf.close()
        
        return {
            'document': document,
            'chunks': len(chunks),
            'images': len(images),
            'links': len(links)
        }
    
    def _create_document(self, file_path: str, manufacturer_id: str) -> Dict:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        file_hash = hashlib.sha256(content).hexdigest()
        
        document = self.supabase.table('documents').insert({
            'manufacturer_id': manufacturer_id,
            'filename': Path(file_path).name,
            'file_size': len(content),
            'file_hash': file_hash,
            'document_type': 'Service Manual',
            'processing_status': 'processing'
        }).execute()
        
        return document.data[0]
    
    def _extract_text_chunks(self, pdf, document_id: str) -> List[Dict]:
        chunks = []
        chunk_index = 0
        
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text = page.get_text()
            
            # Einfaches Chunking (in Produktion: semantic chunking)
            if len(text) > 1000:
                # Text in 1000-Zeichen Chunks aufteilen
                for i in range(0, len(text), 1000):
                    chunk_text = text[i:i+1000]
                    fingerprint = hashlib.md5(chunk_text.encode()).hexdigest()
                    
                    chunk = self.supabase.table('chunks').insert({
                        'document_id': document_id,
                        'text_chunk': chunk_text,
                        'chunk_index': chunk_index,
                        'page_start': page_num + 1,
                        'page_end': page_num + 1,
                        'fingerprint': fingerprint,
                        'processing_status': 'completed'
                    }).execute()
                    
                    chunks.append(chunk.data[0])
                    chunk_index += 1
        
        return chunks
    
    def _extract_images(self, pdf, document_id: str) -> List[Dict]:
        images = []
        
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Bild speichern (vereinfacht)
                image_hash = hashlib.sha256(image_bytes).hexdigest()
                
                image = self.supabase.table('images').insert({
                    'document_id': document_id,
                    'page_number': page_num + 1,
                    'image_index': img_index,
                    'file_hash': image_hash,
                    'file_size': len(image_bytes),
                    'storage_url': f'placeholder_{image_hash[:8]}.png',
                    'image_type': 'technical_drawing'
                }).execute()
                
                images.append(image.data[0])
        
        return images
    
    def _extract_links(self, pdf, document_id: str) -> List[Dict]:
        links = []
        
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            link_list = page.get_links()
            
            for link in link_list:
                if 'uri' in link:
                    url = link['uri']
                    
                    # Link-Typ bestimmen
                    link_type = 'external'
                    if 'youtube.com' in url or 'vimeo.com' in url:
                        link_type = 'video'
                    
                    link_data = self.supabase.table('links').insert({
                        'document_id': document_id,
                        'url': url,
                        'link_type': link_type,
                        'page_number': page_num + 1,
                        'position_data': {
                            'rect': link.get('from', None)
                        }
                    }).execute()
                    
                    links.append(link_data.data[0])
        
        return links

# Verwendung
processor = DocumentProcessor(supabase)
result = processor.process_document(
    'service_manual.pdf',
    '550e8400-e29b-41d4-a716-446655440001'
)
print(f"Processed: {result}")
```

---

## 📊 Best Practices

### 1. **Transaktionen verwenden**

```python
# Für kritische Operations
try:
    # Mehrere abhängige Operationen
    document = supabase.table('documents').insert({...}).execute()
    chunk = supabase.table('chunks').insert({...}).execute()
    
except Exception as e:
    # Rollback nötig - oder Retry-Logik
    print(f"Error: {e}")
```

### 2. **Batch Operations**

```python
# Mehrere Records auf einmal
chunks_data = [
    {'document_id': doc_id, 'text_chunk': text1, ...},
    {'document_id': doc_id, 'text_chunk': text2, ...},
    {'document_id': doc_id, 'text_chunk': text3, ...}
]

result = supabase.table('chunks').insert(chunks_data).execute()
```

### 3. **Pagination**

```python
# Große Datenmengen paginieren
page_size = 100
offset = 0

while True:
    docs = supabase.table('documents')\
        .select('*')\
        .range(offset, offset + page_size - 1)\
        .execute()
    
    if not docs.data:
        break
    
    # Verarbeite docs.data
    offset += page_size
```

### 4. **Error Handling**

```python
from postgrest.exceptions import APIError

try:
    result = supabase.table('documents').insert({...}).execute()
except APIError as e:
    if 'unique constraint' in str(e):
        print("Duplicate document")
    elif 'foreign key' in str(e):
        print("Referenced record doesn't exist")
    else:
        print(f"Database error: {e}")
```

### 5. **JSONB Queries**

```python
# JSONB Felder abfragen
products = supabase.table('products')\
    .select('*')\
    .contains('option_dependencies', {'memory_upgrade': ['1GB']})\
    .execute()

# JSONB Array contains
products = supabase.table('products')\
    .select('*')\
    .cs('color_options', ['Black', 'White'])\
    .execute()
```

### 6. **RLS Beachtung**

```python
# Service Role Key nutzen für Backend-Operationen
# Anon Key für Frontend (mit RLS-Einschränkungen)

# Backend (Service Role)
supabase_backend = create_client(url, service_role_key)

# Frontend (Anon Key)
supabase_frontend = create_client(url, anon_key)
```

---

## 🔍 Nützliche RPC Functions

### Vector Search

```python
# Semantic Search
results = supabase.rpc('find_similar_chunks', {
    'query_embedding': vector_string,
    'similarity_threshold': 0.7,
    'limit_results': 20
}).execute()
```

### Full-Text Search

```python
# Optimierte Dokumentensuche
results = supabase.rpc('search_documents_optimized', {
    'search_query': 'paper jam',
    'manufacturer_filter': manufacturer_id,
    'document_type_filter': 'Service Manual',
    'limit_results': 50
}).execute()
```

### Statistics

```python
# Processing Statistics
stats = supabase.rpc('get_processing_statistics', {
    'date_from': '2025-10-01',
    'date_to': '2025-10-31'
}).execute()
```

---

## 📚 Weitere Ressourcen

- **Supabase Docs**: https://supabase.com/docs
- **pgvector Docs**: https://github.com/pgvector/pgvector
- **Python Client**: https://github.com/supabase-community/supabase-py

---

## 🆘 Troubleshooting

### Problem: Foreign Key Constraint Violation

```python
# Sicherstellen, dass referenzierte Records existieren
manufacturer = supabase.table('manufacturers')\
    .select('id')\
    .eq('id', manufacturer_id)\
    .single()\
    .execute()

if not manufacturer.data:
    print("Manufacturer doesn't exist!")
```

### Problem: Vector Dimension Mismatch

```python
# Vector muss EXAKT 768 Dimensionen haben
assert len(embedding_vector) == 768, "Vector must be 768-dimensional"
```

### Problem: JSONB Validation

```python
import json

# JSONB validieren
try:
    json.dumps(json_data)
except TypeError:
    print("Invalid JSON structure")
```

---

**Erstellt für KRAI Development Team**  
**Bei Fragen:** Siehe Backend Team Lead

