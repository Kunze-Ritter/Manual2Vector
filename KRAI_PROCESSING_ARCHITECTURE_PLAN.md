# 🚀 KR-AI-Engine - Processing Architecture Plan

**Vollständiger Plan für Datenverarbeitung, Module-Organisation und System-Architektur**

## 📊 **Projekt-Übersicht**

### **🎯 Zielsetzung**
- **Dokumentenverarbeitung**: PDF Service Manuals, Parts Catalogs, Bulletins
- **AI-gestützte Extraktion**: Hersteller, Modelle, Versionen, Fehlercodes
- **Semantic Search**: Vector-basierte Suche mit pgvector
- **Object Storage**: Nur für Bilder (Cloudflare R2)
- **Defect Detection**: Separate Dashboard-Funktion für Techniker
- **Modulare Architektur**: 5 spezialisierte Prozessoren

### **🏗️ Architektur (Minimal Setup)**
- **Database**: Supabase Cloud (PostgreSQL + Vector Extensions)
- **Object Storage**: Cloudflare R2 (NUR für Bilder)
- **AI Models**: Ollama Windows App mit intelligenter Hardware-Detection (Auto-Auswahl: Llama3.2:70b, EmbeddingGemma:2b, LLaVA:34b)
- **API**: FastAPI mit modularer Architektur

---

## 🔄 **Processing Pipeline (9-Stage)**

### **📋 Pipeline Stages**
1. **📤 Upload & Validation** → `krai_core.documents` (Database only)
2. **📄 Text Extraction** → `krai_content.chunks`
3. **🖼️ Image Processing** → `krai_content.images` (Object Storage)
4. **🏷️ Document Classification** → `krai_core.documents` (metadata)
5. **📑 Metadata Extraction** → `krai_intelligence.error_codes`
6. **💾 Document Storage** → Database only (kein Object Storage)
7. **🔪 Text Chunking** → `krai_intelligence.chunks`
8. **🔮 Embedding Generation** → `krai_intelligence.embeddings`
9. **✅ Finalization** → `krai_system.processing_queue`

---

## 🏗️ **Module-Organisation**

### **📁 Projektstruktur**
```
backend/
├── main.py                             # FastAPI Hauptanwendung
├── requirements.txt                    # Dependencies
├── config/
│   ├── database_config.py              # Supabase Database Config
│   ├── object_storage_config.py        # Cloudflare R2 Config
│   ├── ai_config.py                    # Ollama AI Config (mit Hardware-Detection)
│   ├── features_config.py              # Features Config
│   ├── processing_config.py            # Processing Pipeline Config
│   ├── chunk_settings.json             # Text Chunking Strategies
│   ├── error_code_patterns.json        # Error Code Patterns
│   ├── version_patterns.json           # Version Extraction Patterns
│   └── model_placeholder_patterns.json # Model Placeholder Patterns
├── core/
│   ├── __init__.py
│   ├── base_processor.py               # Base Processor Interface
│   ├── processing_pipeline.py          # Pipeline Orchestrator
│   └── data_models.py                  # Pydantic Models
├── processors/
│   ├── __init__.py
│   ├── upload_processor.py             # Upload & Validation
│   ├── text_processor.py               # Text Extraction & Chunking
│   ├── image_processor.py              # Image Processing (OCR, Classification)
│   ├── classification_processor.py     # Document Classification
│   ├── metadata_processor.py           # Metadata & Error Code Extraction
│   ├── storage_processor.py            # Object Storage (Images only)
│   ├── embedding_processor.py          # Vector Embeddings
│   └── search_processor.py             # Semantic Search
├── services/
│   ├── __init__.py
│   ├── database_service.py             # Supabase Database Service
│   ├── object_storage_service.py       # Cloudflare R2 Service
│   ├── ai_service.py                   # Ollama AI Service
│   ├── config_service.py               # Configuration Service
│   ├── features_service.py             # Features Extraction & Inheritance
│   └── update_service.py               # Update Management
├── utils/
│   ├── __init__.py
│   ├── chunk_utils.py                  # Text Chunking Utilities
│   ├── pattern_utils.py                # Pattern Matching Utilities
│   ├── image_utils.py                  # Image Processing Utilities
│   ├── validation_utils.py             # Data Validation Utilities
│   ├── version_utils.py                # Version Detection Utilities
│   └── model_utils.py                  # Model Placeholder Resolution
├── api/
│   ├── __init__.py
│   ├── document_api.py                 # Document Processing API
│   ├── search_api.py                   # Search API
│   ├── features_api.py                 # Features Management API
│   └── defect_detection_api.py         # Defect Detection API (Separate)
└── tests/
    ├── __init__.py
    ├── test_processors.py
    ├── test_services.py
    └── test_api.py
```

---

## 🤖 **Intelligente AI Model-Auswahl**

### **🔍 Hardware Auto-Detection**
```python
# Automatische Hardware-Erkennung
class HardwareDetector:
    def detect_hardware(self):
        """Erkennt RAM, CPU, GPU automatisch"""
        return {
            'total_ram_gb': 63.4,  # Dein System
            'cpu_cores': 16,
            'cpu_threads': 22,
            'gpu_available': True
        }
    
    def recommend_tier(self):
        """Empfiehlt Modell-Tier basierend auf Hardware"""
        if ram >= 32 and cores >= 8:
            return 'HIGH_PERFORMANCE'  # 70B Modelle
        elif ram >= 16 and cores >= 4:
            return 'BALANCED'           # 13B Modelle
        else:
            return 'CONSERVATIVE'      # 7B Modelle
```

### **🎯 Modell-Tier Auswahl**
```python
# Deine Hardware → HIGH_PERFORMANCE Tier
MODEL_CONFIGS = {
    'HIGH_PERFORMANCE': {
        'text_classification': 'llama3.2:70b',    # Beste Qualität
        'embeddings': 'embeddinggemma:2b',       # Effizient
        'vision': 'llava:34b',                    # Hochauflösend
        'estimated_ram_gb': 32.0,
        'parallel_processing': False  # Sequential bei großen Modellen
    },
    'BALANCED': {
        'text_classification': 'llama3.2:13b',
        'embeddings': 'embeddinggemma:2b',
        'vision': 'llava:13b',
        'estimated_ram_gb': 16.0,
        'parallel_processing': True
    },
    'CONSERVATIVE': {
        'text_classification': 'llama3.2:7b',
        'embeddings': 'embeddinggemma:2b',
        'vision': 'llava:7b',
        'estimated_ram_gb': 8.0,
        'parallel_processing': True
    }
}
```

### **⚡ Task-spezifische Modell-Zuordnung**
```python
# Welches Modell für welche Aufgabe
TASK_MODELS = {
    'document_classification': 'llama3.2:70b',
    'manufacturer_detection': 'llama3.2:70b',
    'features_extraction': 'llama3.2:70b',
    'error_code_extraction': 'llama3.2:70b',
    'semantic_search': 'embeddinggemma:2b',
    'image_ocr': 'llava:34b',
    'defect_detection': 'llava:34b'
}
```

---

## ⚡ **Resource Management & Load Balancing**

### **🔄 Resource-based Processing Strategy**
```python
# Resource Management Configuration
PROCESSING_RESOURCES = {
    'low_resource': {
        'processors': ['upload', 'metadata', 'storage'],
        'max_instances': 2,
        'parallel_execution': True,
        'resource_threshold': 0.3
    },
    'medium_resource': {
        'processors': ['text', 'classification', 'search'],
        'max_instances': 3,
        'parallel_execution': True,
        'resource_threshold': 0.6
    },
    'high_resource': {
        'processors': ['image', 'embedding'],
        'max_instances': 5,
        'parallel_execution': False,  # Sequential bei hohem Load
        'resource_threshold': 0.8
    }
}
```

### **⚖️ Load Balancing Strategy**
```python
# Load Balancing Configuration
LOAD_BALANCING = {
    'upload_service': {'instances': 1, 'weight': 1},
    'text_service': {'instances': 2, 'weight': 2},
    'image_service': {'instances': 3, 'weight': 3},
    'classification_service': {'instances': 2, 'weight': 2},
    'metadata_service': {'instances': 1, 'weight': 1},
    'storage_service': {'instances': 1, 'weight': 1},
    'embedding_service': {'instances': 4, 'weight': 4},
    'search_service': {'instances': 2, 'weight': 2}
}
```

### **🛑 Error Handling & Logging**
```python
# Error Handling Strategy
ERROR_HANDLING = {
    'on_error': 'STOP_PIPELINE',  # Fehler = Stopp
    'logging_level': 'DEBUG',
    'log_file': 'logs/processing.log',
    'error_notification': True,
    'retry_attempts': 0,  # Keine Retries bei Fehlern
    'rollback_on_error': True
}
```

### **🔄 Update Management**
```python
# Update Management Strategy
UPDATE_MANAGEMENT = {
    'version_detection': True,
    'remove_old_versions': True,
    'keep_latest_only': True,
    'backup_before_update': False,  # Alte Versionen werden gelöscht
    'update_notification': True
}
```

---

## 🔧 **Prozessor-Module**

### **1. 📤 Upload Processor (`processors/upload_processor.py`)**
**Verantwortlichkeit**: Dokumenten-Upload und Validierung

**Input**: PDF-Datei
**Output**: `krai_core.documents` (Database only)

**Datenfluss**:
```python
# Upload & Validation (Database only)
document_data = {
    'filename': 'HP_X580_SM.pdf',
    'original_filename': 'HP LaserJet Pro X580 Service Manual.pdf',
    'file_size': 15728640,  # bytes
    'file_hash': 'sha256_hash',
    'storage_path': None,  # Kein Object Storage für Dokumente
    'storage_url': None,    # Kein Object Storage für Dokumente
    'document_type': 'service_manual',
    'language': 'en',
    'processing_status': 'pending',
    'manufacturer': 'HP',
    'series': 'LaserJet Pro',
    'models': ['X580', 'X580dn', 'X580dtn']
}
```

**Database Tables**:
- ✅ `krai_core.documents` - Hauptdokumententabelle (Database only)
- ✅ `krai_system.processing_queue` - Verarbeitungswarteschlange

**Module Dependencies**:
- `services.database_service` - Database Operations
- `utils.validation_utils` - File Validation
- `core.data_models` - Document Models

---

### **2. 📄 Text Processor (`processors/text_processor.py`)**
**Verantwortlichkeit**: PDF-Text-Extraktion und Chunking

**Input**: PDF-Datei
**Output**: `krai_content.chunks` + `krai_intelligence.chunks`

**Datenfluss**:
```python
# Text Extraction & Chunking
text_chunks = [
    {
        'content': 'Troubleshooting paper jam issues...',
        'chunk_type': 'text',
        'chunk_index': 1,
        'page_number': 45,
        'section_title': 'Paper Handling',
        'confidence_score': 0.95,
        'language': 'en'
    }
]

# Intelligent Chunking für Embeddings
intelligent_chunks = [
    {
        'text_chunk': 'Error code E123: Paper jam in tray 2...',
        'chunk_index': 1,
        'page_start': 45,
        'page_end': 45,
        'processing_status': 'completed',
        'fingerprint': 'chunk_hash',
        'metadata': {
            'section': 'Error Codes',
            'confidence': 0.98,
            'contains_error_code': True
        }
    }
]
```

**Database Tables**:
- ✅ `krai_content.chunks` - Content Chunks
- ✅ `krai_intelligence.chunks` - Intelligence Chunks

**Module Dependencies**:
- `utils.chunk_utils` - Chunking Strategies
- `services.database_service` - Database Operations
- `config.processing_config` - Chunk Settings

---

### **3. 🖼️ Image Processor (`processors/image_processor.py`)**
**Verantwortlichkeit**: Bildextraktion, OCR, Bildklassifizierung (KEIN Defect Detection)

**Input**: PDF-Datei
**Output**: `krai_content.images` (Object Storage)

**Datenfluss**:
```python
# Image Processing (Object Storage für Bilder)
images = [
    {
        'filename': 'HP_X580_diagram_001.png',
        'original_filename': 'page_45_diagram.png',
        'storage_path': 'images/2024/01/HP_X580_diagram_001.png',
        'storage_url': 'https://r2.cloudflare.com/krai-document-images/...',
        'file_size': 245760,
        'image_format': 'png',
        'width_px': 1920,
        'height_px': 1080,
        'page_number': 45,
        'image_index': 1,
        'image_type': 'diagram',  # diagram, screenshot, photo, chart
        'ai_description': 'Technical diagram showing paper path',
        'ai_confidence': 0.92,
        'contains_text': True,
        'ocr_text': 'Paper Path Diagram\nTray 1 → Paper Path → Output',
        'ocr_confidence': 0.88,
        'tags': ['diagram', 'paper_path', 'technical'],
        'file_hash': 'image_hash'
    }
]
```

**Database Tables**:
- ✅ `krai_content.images` - Bildverarbeitung (Object Storage)

**Module Dependencies**:
- `services.object_storage_service` - Cloudflare R2
- `services.ai_service` - OCR & Vision AI
- `utils.image_utils` - Image Processing
- `services.database_service` - Database Operations

---

### **4. 🏷️ Classification Processor (`processors/classification_processor.py`)**
**Verantwortlichkeit**: Dokumenttyp, Hersteller, Modell-Erkennung + Features-Extraktion

**Input**: Text Chunks + Filename
**Output**: `krai_core.manufacturers`, `krai_core.products`, `krai_core.product_series`, `krai_core.documents` (metadata)

**Datenfluss**:
```python
# Document Classification + Features
classification_result = {
    'document_type': 'service_manual',
    'manufacturer': 'HP',
    'manufacturer_id': 'uuid_manufacturer_hp',
    'product_id': 'uuid_product_x580',
    'series_id': 'uuid_series_laserjet_pro',
    'models': ['X580', 'X580dn', 'X580dtn'],
    'series': 'LaserJet Pro',
    'version': '1.0',
    'confidence_score': 0.95,
    'extraction_method': 'hybrid'  # filename + content
}

# Features-Extraktion (Serie + Produkt)
series_features = {
    'key_features': {
        'print_technology': 'Laser',
        'target_market': 'Enterprise',
        'price_range': 'High-End',
        'common_features': ['Duplex', 'Network', 'Mobile Print']
    },
    'target_market': 'Enterprise',
    'price_range': 'High-End',
    'series_description': 'Professional laser printer series'
}

product_features = {
    'duplex_capable': True,
    'network_capable': True,
    'mobile_print_support': True,
    'energy_star_certified': True,
    'warranty_months': 36,
    'color_options': ['Black'],
    'connectivity_options': ['Ethernet', 'WiFi', 'USB']
}
```

**Database Tables**:
- ✅ `krai_core.manufacturers` - Hersteller
- ✅ `krai_core.products` - Produkte (mit Features)
- ✅ `krai_core.product_series` - Produktserien (mit globalen Features)
- ✅ `krai_core.documents` - Dokument-Metadaten

**Module Dependencies**:
- `services.ai_service` - LLM Classification
- `services.database_service` - Database Operations
- `services.features_service` - Features Extraction & Inheritance
- `utils.pattern_utils` - Pattern Matching
- `config.processing_config` - Classification Rules

---

### **5. 📑 Metadata Processor (`processors/metadata_processor.py`)**
**Verantwortlichkeit**: Version, Serie, Fehlercodes, Zusatzinfos

**Input**: Text Chunks + Classification
**Output**: `krai_intelligence.error_codes`

**Datenfluss**:
```python
# Metadata Extraction (mit Config-Patterns)
error_codes = [
    {
        'error_code': '13.20.01',  # HP Pattern
        'error_description': 'Paper jam in duplex unit',
        'solution_text': 'Remove paper from duplex unit and clear jam',
        'page_number': 45,
        'confidence_score': 0.98,
        'extraction_method': 'pattern_matching',
        'requires_technician': False,
        'requires_parts': False,
        'estimated_fix_time_minutes': 5,
        'severity_level': 'low'
    }
]

# Version Extraction (mit Config-Patterns)
version_info = {
    'version': 'Edition 3, 5/2024',  # HP Pattern
    'extraction_method': 'edition_patterns',
    'confidence_score': 0.95
}
```

**Database Tables**:
- ✅ `krai_intelligence.error_codes` - Fehlercodes
- ✅ `krai_core.documents` - Metadaten-Update

**Module Dependencies**:
- `utils.pattern_utils` - Pattern Matching
- `services.database_service` - Database Operations
- `config.processing_config` - Error & Version Patterns
- `services.ai_service` - LLM Extraction

---

### **6. 💾 Storage Processor (`processors/storage_processor.py`)**
**Verantwortlichkeit**: Object Storage NUR für Bilder

**Input**: Bilder aus PDF
**Output**: Cloudflare R2 Storage (NUR Bilder)

**Datenfluss**:
```python
# Object Storage (NUR für Bilder)
storage_buckets = {
    'document_images': 'krai-document-images',  # Aus Dokumenten
    'error_images': 'krai-error-images',        # Defect Detection
    'parts_images': 'krai-parts-images'         # Parts Catalog
}

# Image Storage
image_storage = {
    'bucket': 'krai-document-images',
    'key': 'images/2024/01/HP_X580_diagram_001.png',
    'url': 'https://r2.cloudflare.com/krai-document-images/...',
    'file_hash': 'image_hash',
    'size': 245760
}
```

**Storage Strategy**:
- **Dokumente**: ❌ Kein Object Storage (nur Database)
- **Dokument-Bilder**: ✅ `krai-document-images` Bucket
- **Fehler-Bilder**: ✅ `krai-error-images` Bucket (Defect Detection)
- **Teile-Bilder**: ✅ `krai-parts-images` Bucket

**Module Dependencies**:
- `services.object_storage_service` - Cloudflare R2
- `utils.validation_utils` - File Validation
- `services.database_service` - Database Operations

---

### **7. 🔮 Embedding Processor (`processors/embedding_processor.py`)**
**Verantwortlichkeit**: Vector Embeddings für Semantic Search

**Input**: Text Chunks
**Output**: `krai_intelligence.embeddings`

**Datenfluss**:
```python
# Embedding Generation
embeddings = [
    {
        'chunk_id': 'uuid_chunk_1',
        'embedding': [0.1, 0.2, 0.3, ...],  # 768-dimensional vector
        'model_name': 'embeddinggemma',
        'model_version': 'latest'
    }
]
```

**Database Tables**:
- ✅ `krai_intelligence.embeddings` - Vector Embeddings (768-dim)

**Module Dependencies**:
- `services.ai_service` - EmbeddingGemma
- `services.database_service` - Database Operations
- `config.ai_config` - AI Model Settings

---

### **8. 🔍 Search Processor (`processors/search_processor.py`)**
**Verantwortlichkeit**: Semantic Search und Analytics

**Input**: Search Query
**Output**: Search Results + Analytics

**Datenfluss**:
```python
# Search Processing
search_results = {
    'query': 'paper jam error E123',
    'results': [
        {
            'document_id': 'uuid_doc_1',
            'chunk_id': 'uuid_chunk_1',
            'similarity_score': 0.95,
            'content': 'Error code E123: Paper jam in tray 2...',
            'page_number': 45,
            'document_type': 'service_manual',
            'manufacturer': 'HP',
            'model': 'X580'
        }
    ]
}
```

**Database Tables**:
- ✅ `krai_intelligence.search_analytics` - Search Analytics

**Module Dependencies**:
- `services.database_service` - Vector Search
- `services.ai_service` - Query Processing
- `utils.pattern_utils` - Search Patterns

---

## 🏷️ **Features Management System**

### **🔧 Features Service (`services/features_service.py`)**
**Verantwortlichkeit**: Features-Extraktion und Vererbung von Serie zu Produkt

**Features Inheritance Logic**:
```python
class FeaturesService:
    def extract_series_features(self, document):
        """Extrahiert globale Features der Serie"""
        return {
            'key_features': {
                'print_technology': 'Laser',
                'target_market': 'Enterprise',
                'price_range': 'High-End',
                'common_features': ['Duplex', 'Network', 'Mobile Print']
            },
            'target_market': 'Enterprise',
            'price_range': 'High-End',
            'series_description': 'Professional laser printer series'
        }
    
    def extract_product_features(self, document):
        """Extrahiert modell-spezifische Features"""
        return {
            'duplex_capable': True,
            'network_capable': True,
            'mobile_print_support': True,
            'energy_star_certified': True,
            'warranty_months': 36,
            'color_options': ['Black'],
            'connectivity_options': ['Ethernet', 'WiFi', 'USB']
        }
    
    def get_effective_features(self, series_id, product_id):
        """Features-Vererbung: Serie → Produkt"""
        series_features = self.get_series_features(series_id)
        product_features = self.get_product_features(product_id)
        
        # Serie-Features als Basis
        effective_features = series_features.copy()
        
        # Produkt-Features überschreiben Serie-Features
        effective_features.update(product_features)
        
        return effective_features
```

### **🔍 Features-based Search**
```python
# Features-basierte Suche
def search_by_features(features_query):
    """Suche nach Features in Serie UND Produkt"""
    query = """
    SELECT p.*, ps.key_features, ps.target_market
    FROM products p
    JOIN product_series ps ON p.series_id = ps.id
    WHERE ps.key_features @> %s
    OR p.duplex_capable = %s
    OR p.network_capable = %s
    """
    return execute_query(query, features_query)
```

### **📊 Features API (`api/features_api.py`)**
```python
# Features Management API
@app.get("/features/series/{series_id}")
async def get_series_features(series_id: str):
    """Serie-Features abrufen"""
    return features_service.get_series_features(series_id)

@app.get("/features/product/{product_id}")
async def get_product_features(product_id: str):
    """Produkt-Features abrufen (mit Vererbung)"""
    return features_service.get_effective_features(product_id)

@app.post("/features/search")
async def search_by_features(features_query: FeaturesQuery):
    """Features-basierte Suche"""
    return features_service.search_by_features(features_query)
```

---

## 🆕 **Separate Defect Detection System**

### **🔧 Defect Detection Dashboard (`api/defect_detection_api.py`)**
**Zweck**: Techniker im Feld können Bilder senden → AI schlägt Lösung vor

**Datenfluss**:
```python
# Defect Detection (Separate System)
defect_analysis = {
    'image_url': 'https://r2.cloudflare.com/krai-error-images/...',
    'ai_analysis': {
        'defect_type': 'paper_jam',
        'confidence': 0.92,
        'suggested_solutions': [
            'Check paper path for obstructions',
            'Verify paper type and size',
            'Clean paper sensors'
        ],
        'estimated_fix_time': '5-10 minutes',
        'required_parts': [],
        'difficulty_level': 'easy'
    },
    'related_error_codes': ['13.20.01', '13.20.02'],
    'similar_cases': [
        {
            'case_id': 'uuid_case_1',
            'similarity': 0.88,
            'solution': 'Remove jammed paper from tray 2'
        }
    ]
}
```

**Database Tables**:
- ✅ `krai_content.print_defects` - Defect Detection
- ✅ `krai_content.images` - Defect Images (krai-error-images)

**Object Storage**:
- ✅ `krai-error-images` - Defect Images
- ✅ `krai-parts-images` - Parts Images

---

## 🗄️ **Database Schema Mapping**

### **📊 Core Tables (krai_core)**
| Tabelle | Prozessor | Zweck |
|---------|-----------|-------|
| `manufacturers` | Classification | Hersteller-Informationen |
| `products` | Classification | Produkt-Informationen |
| `product_series` | Classification | Produktserien |
| `documents` | Upload + Classification | Hauptdokumententabelle (Database only) |
| `document_relationships` | Metadata | Dokument-Beziehungen |

### **📝 Content Tables (krai_content)**
| Tabelle | Prozessor | Zweck |
|---------|-----------|-------|
| `chunks` | Text | Content Chunks |
| `images` | Image | Bildverarbeitung (Object Storage) |
| `instructional_videos` | Metadata | Video-Referenzen |
| `print_defects` | Defect Detection | Defect Detection (Separate System) |

### **🧠 Intelligence Tables (krai_intelligence)**
| Tabelle | Prozessor | Zweck |
|---------|-----------|-------|
| `chunks` | Text | Intelligence Chunks |
| `embeddings` | Embedding | Vector Embeddings (768-dim) |
| `error_codes` | Metadata | Fehlercode-Extraktion |
| `search_analytics` | Search | Search Analytics |

### **⚙️ System Tables (krai_system)**
| Tabelle | Prozessor | Zweck |
|---------|-----------|-------|
| `processing_queue` | All | Verarbeitungswarteschlange |
| `audit_log` | All | Audit Logging |
| `system_metrics` | All | System Metrics |
| `health_checks` | All | Health Monitoring |

---

## 🔄 **Processing Flow Diagram**

```
📤 Upload Processor (Database only)
    ↓
📄 Text Processor → krai_content.chunks
    ↓
🖼️ Image Processor → krai_content.images (Object Storage)
    ↓
🏷️ Classification Processor → krai_core.manufacturers, products, documents
    ↓
📑 Metadata Processor → krai_intelligence.error_codes
    ↓
💾 Storage Processor → Cloudflare R2 (NUR Bilder)
    ↓
🔪 Text Chunking → krai_intelligence.chunks
    ↓
🔮 Embedding Processor → krai_intelligence.embeddings
    ↓
✅ Finalization → krai_system.processing_queue
```

---

## 🚀 **Clean Start Implementation**

### **📋 Nächste Schritte**
1. **Module-Struktur** erstellen
2. **Base Processor Interface** implementieren
3. **Service Layer** implementieren
4. **Processor Module** implementieren
5. **API Endpoints** implementieren
6. **Database Integration** mit Supabase MCP
7. **Object Storage** mit Cloudflare R2
8. **AI Integration** mit Ollama
9. **Defect Detection Dashboard** (Separate Funktion)

### **🔧 Technische Anforderungen**
- **FastAPI** für API
- **Supabase Client** für Database
- **Boto3** für Cloudflare R2 (NUR Bilder)
- **Ollama Client** für AI
- **pgvector** für Vector Search
- **Async Processing** für Performance

### **📦 Dependencies (requirements.txt)**
```python
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
pydantic-settings>=2.1.0

# Database & Storage
supabase>=2.0.0
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
boto3>=1.34.0
botocore>=1.34.0

# Document Processing
PyMuPDF>=1.23.0
python-docx>=0.8.0
pytesseract>=0.3.0
Pillow>=10.0.0
pdfplumber>=0.9.0
opencv-python>=4.8.0

# AI & ML
sentence-transformers>=2.2.0
transformers>=4.35.0
torch>=2.2.0
ollama>=0.1.0

# HTTP & API
httpx>=0.26.0
aiohttp>=3.8.0

# Resource Management & Load Balancing
celery>=5.3.0
redis>=5.0.0
kubernetes>=28.0.0

# Utilities
python-dotenv>=1.0.0
loguru>=0.7.0
rich>=13.6.0
```

### **🔧 Configuration Files**
```json
// config/chunk_settings.json - Text Chunking Strategies
{
  "chunk_settings": {
    "default_strategy": "contextual_chunking",
    "strategies": { ... },
    "document_type_specific": { ... },
    "manufacturer_specific": { ... }
  }
}

// config/error_code_patterns.json - Error Code Patterns
{
  "error_code_patterns": {
    "hp": { "patterns": [...], "examples": [...] },
    "konica_minolta": { "patterns": [...], "examples": [...] }
  }
}

// config/version_patterns.json - Version Extraction
{
  "version_patterns": {
    "edition_patterns": [...],
    "date_patterns": [...],
    "firmware_patterns": [...]
  }
}

// config/model_placeholder_patterns.json - Model Placeholders
{
  "model_placeholder_patterns": {
    "numeric_wildcards": [...],
    "letter_wildcards": [...],
    "range_wildcards": [...]
  }
}
```

**📄 Dieser Plan definiert die komplette Module-Organisation und System-Architektur für den KR-AI-Engine!**
