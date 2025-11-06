# 🚀 KRAI - Knowledge Retrieval and Intelligence

Advanced Multimodal AI Document Processing Pipeline with Local-First Architecture and Vector Search

## 🚀 Quick Start

### 🏢 Production Deployment (Recommended)
```bash
git clone <repository-url>
cd KRAI-minimal
docker-compose -f docker-compose.production-final.yml up -d --build
```

**Access your system:**
- 🖥️ **Dashboard:** http://localhost:3000
- ⚙️ **API:** http://localhost:8000  
- 📊 **API Docs:** http://localhost:8000/docs
- 💾 **Storage:** http://localhost:9001 (minioadmin/minioadmin)

### 🏠 Local Development
```bash
# Development setup
docker-compose -f docker-compose.yml up -d

# Or run services locally
cd backend && python -m uvicorn main:app --reload
cd frontend && npm run dev
```

## 📋 Production Services

| Service | Port | Technology | Description |
|---------|------|------------|-------------|
| **Frontend** | 3000 | React + Nginx | Production Dashboard |
| **Backend** | 8000 | FastAPI + Gunicorn | API Server |
| **Database** | 5432 | PostgreSQL + pgvector | Vector Database |
| **Storage** | 9000/9001 | MinIO | Object Storage |
| **AI Service** | 11434 | Ollama | Large Language Models |

## 📖 Documentation

- 📋 **[Deployment Guide](DEPLOYMENT.md)** - Complete production setup
- 🏗️ **[Architecture](docs/architecture/)** - System design and components
- 🔧 **[API Documentation](docs/api/)** - REST API reference
- 🧪 **[Testing](tests/)** - Test suites and E2E tests

---

## 🎯 Overview

KRAI is a comprehensive multimodal AI system that automatically extracts, analyzes, and indexes technical documents with advanced features including hierarchical structure detection, SVG vector graphics processing, and intelligent multimodal search. Built with a **local-first architecture**, KRAI provides complete control over your data while offering cloud migration capabilities when needed.

## ✨ Key Features

### 🤖 **Advanced AI-Powered Processing**

- **Hierarchical Document Structure Detection** with automatic section linking
- **Smart Document Classification** using local Ollama LLM models
- **Intelligent Text Chunking** with semantic analysis and error code boundaries
- **SVG Vector Graphics Processing** with Vision AI analysis and PNG conversion
- **Multimodal Context Extraction** for images, videos, links, and tables
- **Vector Embeddings** for semantic search across all content types
- **Manufacturer & Model Detection** with normalization
- **Error Code Extraction** with 17 manufacturer patterns
- **Multimodal Search** across text, images, videos, tables, and links
- **Content APIs** for error codes, videos, and images with role-based access
- **Advanced Web Scraping** with Firecrawl (JavaScript rendering, LLM extraction) and BeautifulSoup fallback

### 🏗️ **Local-First Architecture**

- **Docker Compose Setup** - Complete local deployment in 5 minutes
- **PostgreSQL Database** - Self-hosted with pgvector extension
- **MinIO Object Storage** - S3-compatible local storage
- **Ollama AI Models** - Local AI model serving with privacy
- **Zero Cloud Dependencies** - Works completely offline
- **Data Sovereignty** - Your data never leaves your infrastructure
- **Cloud Migration Path** - Optional cloud setup when ready
- **Firecrawl Services** - Optional self-hosted web scraping with JavaScript rendering

### 🎬 **Enhanced Video Enrichment System**

- **11 Video Formats** (MP4, WebM, MOV, AVI, MKV, M4V, FLV, WMV, MPEG, MPG, 3GP)
- **4 Platforms** (YouTube, Vimeo, Brightcove, Direct)
- **Thumbnail Generation** with OpenCV
- **Context-Aware Video Analysis** with AI-generated descriptions
- **Auto-Create** manufacturers & products
- **Video ↔ Product Linking** (many-to-many)
- **Video ↔ Error Code Linking**

### 🔧 **Advanced Error Code System**

- **17 Manufacturers** supported (HP, Canon, Lexmark, etc.)
- **Product-Specific** error codes
- **Manufacturer Filters** (HP technician-only solutions)
- **Multi-Source Search** (documents + videos + images + tables + links)
- **Confidence Scoring** (0.60 threshold)
- **Smart Deduplication**
- **Error Code Boundary Detection** in document chunks

### 📊 **10-Stage Advanced Processing Pipeline**

1. **Upload Processor** - Document ingestion and deduplication
2. **Text Processor** - Smart chunking with hierarchical structure detection
3. **SVG Processor** - Vector graphics extraction and Vision AI analysis
4. **Image Processor** - Original format preservation, OCR, AI vision
5. **Table Processor** - Structure extraction and context generation
6. **Video Processor** - Metadata extraction and context analysis
7. **Context Extractor** - Multimodal context extraction for all media
8. **Embedding Processor** - Vector embeddings for multimodal search
9. **Search Processor** - Multimodal search indexing and analytics
10. **Quality Processor** - Validation and quality assurance

## 🚀 Quick Start

### **Local Docker Setup** ⚡ (Recommended)

Get KRAI running locally in 5 minutes with zero cloud costs:

```bash
# 1. Clone repository
git clone <https://github.com/your-org/KRAI-minimal.git>
cd KRAI-minimal

# 2. Copy environment configuration
cp .env.example .env

# 3. Start all services (PostgreSQL, MinIO, Ollama, pgAdmin)
docker-compose up -d

# 4. Initialize MinIO storage buckets
python scripts/init_minio.py

# 5. Pull AI models (takes a few minutes)
docker exec krai-ollama ollama pull nomic-embed-text:latest
docker exec krai-ollama ollama pull llama3.2:latest

# 6. Optional: Start Firecrawl for advanced web scraping
docker-compose up -d krai-redis krai-playwright krai-firecrawl-api krai-firecrawl-worker
curl http://localhost:3002/health

# 7. Verify everything is working
python scripts/verify_local_setup.py
```

**Access Points:**

- **API Documentation**: <http://localhost:8000/docs>
- **MinIO Console**: <http://localhost:9001> (minioadmin/minioadmin123)
- **pgAdmin**: <http://localhost:5050> (admin@krai.local/krai_admin_2024)
- **Ollama API**: <http://localhost:11434>
- **Firecrawl API**: <http://localhost:3002> (optional)

**Prerequisites:**

- Docker Desktop 4.25+ with Docker Compose v2
- 16GB RAM minimum (32GB recommended)
- 40GB free disk space
- NVIDIA GPU optional but recommended

📖 **For detailed setup, see [docs/QUICK_START_PHASES_1_6.md](docs/QUICK_START_PHASES_1_6.md)**

### **Cloud Setup** ☁️ (Optional)

> **Note**: Local setup is recommended for optimal performance, data privacy, and cost efficiency. Cloud setup is provided for users with specific cloud requirements.

For users preferring cloud services, see [docs/setup/CLOUD_SETUP_GUIDE.md](docs/setup/CLOUD_SETUP_GUIDE.md) and [docs/MIGRATION_GUIDE_CLOUD_TO_LOCAL.md](docs/MIGRATION_GUIDE_CLOUD_TO_LOCAL.md) for cloud migration instructions.

### **Version Management**

The project uses automatic version synchronization via a **commit-msg** git hook:

```bash
# Install Git hook for automatic version updates
python scripts/install_git_hooks.py
```

The hook runs after you write the commit message and updates `backend/processors/__version__.py` with the correct semantic version and current date. The commit hash is left untouched locally and will be written by CI after push.

**Semantic Versioning via Commit Messages:**
- `MAJOR:` or `RELEASE:` → Increment Major Version (2.1.3 → 3.0.0)
- `MINOR:` or `FEATURE:` → Increment Minor Version (2.1.3 → 2.2.0)
- `PATCH:` or `FIX:` → Increment Patch Version (2.1.3 → 2.1.4)

Details: [Version Management Guide](docs/development/VERSION_MANAGEMENT.md)

📖 **For detailed installation instructions, see [docs/setup/INSTALLATION_GUIDE.md](docs/setup/INSTALLATION_GUIDE.md)**

## 🎮 Usage

### **Master Pipeline Interface**

```bash
python backend/pipeline/master_pipeline.py

# Menu Options:
# 1. Status Check - View processing status
# 2. Pipeline Reset - Process failed documents
# 3. Hardware Waker - Process new PDFs
# 4. Single Document - Process one file
# 5. Batch Processing - Process multiple files
# 6. Exit
```

### **Processing Documents**

```bash
# Place PDF files in service_documents/ directory
# Run pipeline reset to process failed documents
# Or use batch processing for new documents
```


## 📊 Database Schema

### **Core Schemas**
- **`krai_core`**: Documents, manufacturers, products, product_series
- **`krai_content`**: Chunks, images, videos, links, structured tables
- **`krai_intelligence`**: Embeddings v2, error_codes, search_analytics, context data
- **`krai_system`**: Processing_queue, audit_log, system_metrics
- **`krai_agent`**: Memory for n8n AI agent integration

### **Phase 6 Enhanced Features**
- **Hierarchical Chunk Structure** with section linking and boundaries
- **Multimodal Embeddings** in unified `embeddings_v2` table
- **Vector Graphics Support** with SVG content and PNG conversion
- **Context Extraction** for all media types with embeddings
- **Advanced Search Indexes** with ivfflat vector optimization
- **Cross-Chunk Linking** with previous/next relationships

### **Key Features**
- **Deduplication** at document, image, and chunk levels
- **Vector Search** with pgvector embeddings and multimodal support
- **Manufacturer Normalization** (HP → HP Inc.)
- **Model Detection** for all variants and options
- **Error Code Extraction** with pattern matching + AI
- **SVG to PNG Conversion** for vision model compatibility
- **Context-Aware Search** across all content types
- **Hierarchical Navigation** with section structure preservation


## 🔧 Configuration


### **Environment Variables**
```env
# PostgreSQL Database (Local)
DATABASE_URL=postgresql://krai_user:krai_password@localhost:5432/krai_db
# Or individual components:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=krai_db
POSTGRES_USER=krai_user
POSTGRES_PASSWORD=krai_password

# MinIO Object Storage (Local)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_USE_SSL=false
MINIO_BUCKET_DOCUMENTS=krai-documents
MINIO_BUCKET_IMAGES=krai-images
MINIO_BUCKET_VIDEOS=krai-videos

# Ollama AI Service (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_KEEP_ALIVE=30s

# Feature Flags
ENABLE_SVG_EXTRACTION=true
ENABLE_HIERARCHICAL_CHUNKING=true
ENABLE_MULTIMODAL_SEARCH=true
ENABLE_VISION_ANALYSIS=true
ENABLE_CONTEXT_EXTRACTION=true

# Web Scraping Configuration
SCRAPING_BACKEND=firecrawl  # or 'beautifulsoup'
FIRECRAWL_API_URL=http://localhost:3002
FIRECRAWL_LLM_PROVIDER=ollama  # or 'openai'
ENABLE_LINK_ENRICHMENT=false
ENABLE_MANUFACTURER_CRAWLING=false

# Processing Configuration
MAX_WORKERS=8
CHUNK_SIZE=1000
LOG_LEVEL=INFO

# Logging
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_DIR=backend/logs
LOG_ROTATION=size          # "size" (RotatingFileHandler) or "time" (TimedRotatingFileHandler)
LOG_MAX_BYTES=10000000     # Only used for size-based rotation
LOG_BACKUP_COUNT=5         # Retained rotated files
LOG_ROTATION_WHEN=midnight # Only used for time-based rotation
LOG_ROTATION_INTERVAL=1

# Optional OCR fallback for text extraction
ENABLE_OCR_FALLBACK=false  # Requires pytesseract + Pillow + system Tesseract binary
```

📖 **For the complete list of environment variables, see [docs/ENVIRONMENT_VARIABLES_REFERENCE.md](docs/ENVIRONMENT_VARIABLES_REFERENCE.md)**

### **Hardware Detection**
The system automatically detects:
- CPU cores and threads
- RAM capacity
- GPU type and VRAM
- Performance tier selection
- Optimal model configuration

## 📈 Performance

### **Optimization Features**
- **Smart Stage Parallelization** - Different PDFs in different stages
- **GPU Acceleration** - NVIDIA CUDA support
- **Streaming Processing** - Memory-efficient chunking
- **Batch Operations** - Database optimization
  - Bulk delete/update/status change with transactional asyncpg support
  - Background task queue with progress tracking and rollback metadata
  - Dedicated [/docs/api/BATCH_OPERATIONS.md](docs/api/BATCH_OPERATIONS.md) guide
- **Resource Monitoring** - Real-time performance tracking
- **Vision Model Keep-Alive** - Optimized VRAM management
- **Structured Text Capping** - Limits structured table extraction to configurable line and length caps
- **Configurable Logger Rotation** - Size/time-based rotation with retention controls
- **Extraction Telemetry** - Tracks primary PDF engine, fallback usage, and failed pages

### **Expected Performance**
- **CPU**: 12+ cores utilization
- **GPU**: 80%+ VRAM usage during AI processing
- **RAM**: Optimized streaming processing
- **Throughput**: 10-50 documents/hour (depending on hardware)

## 🛠️ Technical Stack

### **Backend**
- **FastAPI** - Web framework
- **PostgreSQL** - Database with pgvector extension
- **Ollama** - Local AI model serving
- **PyMuPDF** - PDF processing with SVG extraction
- **PyTorch** - AI/ML framework
- **Tesseract OCR** - Text recognition
- **svglib** - SVG to PNG conversion
- **Rich** - Formatted console output
- **Firecrawl** - Advanced web scraping with JavaScript rendering
- **BeautifulSoup** - HTML parsing and fallback scraping
- **Asyncio** - Asynchronous processing

### **AI Models**
- **llama3.1:8b** - Text classification and analysis
- **nomic-embed-text** - Vector embeddings (768 dimensions)
- **llava-phi3** - Vision analysis for images and diagrams

### **Services**
- **Multimodal Search Service** - Unified search across all content types
- **Context Extraction Service** - AI-powered context generation
- **SVG Processor** - Vector graphics extraction and conversion
- **Smart Chunker** - Hierarchical structure detection
- **Database Service** - Production-ready database adapter
- **AI Service** - Centralized AI model management
- **Storage Service** - Object storage with deduplication

### **Storage**
- **PostgreSQL** - Relational data with pgvector for vector search
- **MinIO** - S3-compatible object storage for images, videos, and documents
- **Redis** - Caching and session management (optional)

### **Frontend**
- **React 18+** - Modern web interface
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first styling
- **shadcn/ui** - Component library
- **Vite** - Fast build tool


## 📁 Project Structure


```text
KRAI-minimal/
├── backend/
│   ├── pipeline/         # Main processing pipelines ⭐ NEW
│   ├── processors/       # Active processor implementations
│   ├── services/         # Database, AI, storage, web scraping services
│   ├── api/              # REST API endpoints
│   │   ├── routes/       # Modular routers (documents, products, content APIs)
│   ├── config/           # Configuration files
│   ├── core/             # Base classes and data models
│   ├── utils/            # Utility functions
│   ├── scripts/          # Utility scripts
│   ├── tests/            # Unit tests
│   └── requirements.txt  # Python dependencies
├── examples/             # Firecrawl web scraping examples ⭐ NEW
│   ├── firecrawl_basic_scraping.py
│   ├── firecrawl_site_crawling.py
│   ├── firecrawl_structured_extraction.py
│   ├── firecrawl_link_enrichment.py
│   ├── firecrawl_manufacturer_crawler.py
│   └── README.md
├── docs/                 # Documentation (see breakdown below)
│   ├── processor/        # Processor design docs & checklists
│   ├── video_enrichment/ # Video enrichment & linking
│   ├── database/         # Schema references & migrations
│   ├── features/         # Feature-specific guides
│   ├── releases/         # Release notes & changelogs
│   ├── project_management/ # TODOs, QA reports, planning
│   ├── setup/            # Installation guides
│   ├── architecture/     # System architecture
│   ├── troubleshooting/  # Troubleshooting guides
│   └── n8n/              # n8n integration docs
├── database/
│   └── migrations/       # Database migrations
├── n8n/                  # n8n integration ⭐ NEW
│   ├── workflows/        # n8n workflow files
│   └── credentials/      # n8n credential templates
├── scripts/              # Helper scripts (checks, migrations, utilities)
├── archive/              # Archived temp files and legacy assets
├── .env                  # Environment variables
└── README.md             # This file
```

For reorganization details, consult `docs/PROJECT_CLEANUP_LOG.md`.

## 🔍 Monitoring & Alerts

### **Real-Time Monitoring System** 🆕
- **Pipeline Metrics** - Document counts, success rates, throughput
- **Queue Monitoring** - Processing queue status and wait times
- **Hardware Metrics** - CPU/RAM/Disk utilization tracking
- **Data Quality** - Duplicate detection and validation errors
- **WebSocket API** - Real-time updates with permission-based filtering
- **Alert System** - Configurable rules with severity levels
- **Performance** - Server-side aggregated views for scalability

### **Monitoring API**

```bash
# Get pipeline status
GET /api/v1/monitoring/pipeline

# Get queue metrics
GET /api/v1/monitoring/queue

# Get hardware metrics
GET /api/v1/monitoring/metrics

# WebSocket connection
ws://localhost:8000/ws/monitoring?token=<jwt_token>
```

**Documentation:** See [docs/api/MONITORING_API.md](docs/api/MONITORING_API.md) for complete API reference

### **Alert Management**
- **Configurable Rules** - Set thresholds for failures, queue overflow, hardware, data quality
- **Severity Levels** - Low, Medium, High, Critical
- **Real-Time Triggers** - Immediate WebSocket broadcast on alert
- **Acknowledgment** - Track and dismiss alerts via API
- **Permissions** - Role-based access (monitoring:read, alerts:manage)

### **Health Checks**
- Database connectivity
- Ollama service status
- MinIO storage access
  - MinIO API reachable
  - Console reachable
  - Bucket existence/listing
  - Test upload/download
- GPU availability
- Model loading status
- **Monitoring services** (metrics, alerts, WebSocket connections)

## 🚨 Troubleshooting

### **Common Issues**
1. **GPU not detected** - See `docs/troubleshooting/GPU_AUTO_DETECTION.md`
2. **Ollama connection failed** - See `docs/troubleshooting/OLLAMA_GPU_FIX.md`
3. **Vision model crashes** - See `docs/troubleshooting/VISION_MODEL_TROUBLESHOOTING.md`
4. **Database errors** - Check database credentials and connection settings
5. **Memory issues** - Reduce OLLAMA_KEEP_ALIVE or batch size
6. **Log file grows too large** - Adjust `LOG_ROTATION`, `LOG_MAX_BYTES`, or `LOG_BACKUP_COUNT`
7. **Scanned PDFs contain no text** - Enable `ENABLE_OCR_FALLBACK` and install Tesseract OCR

### **Debug Mode**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python backend/pipeline/master_pipeline.py
```

### **Documentation**
- **Setup**: `docs/setup/` - Installation and configuration
- **Architecture**: `docs/architecture/` - System design and pipeline
- **API Reference**: `docs/api/` - REST API documentation
  - **Monitoring API**: `docs/api/MONITORING_API.md` - Real-time monitoring and alerts
  - **Batch Operations**: `docs/api/BATCH_OPERATIONS.md` - Bulk operations guide
  - **Content API**: `docs/api/CONTENT_API.md` - Error codes, videos, images
- **Version Management**: `docs/development/VERSION_MANAGEMENT.md` - Automatic version synchronization
- **Troubleshooting**: `docs/troubleshooting/` - Common issues and fixes
- **n8n Integration**: `docs/n8n/` - Automation workflows
- **Performance Features**: `docs/PERFORMANCE_FEATURES.md` - Structured text capping, OCR fallback, telemetry, statistics

## 🤖 N8N Integration

KRAI supports n8n automation with PostgreSQL Memory integration:


```bash
# See n8n/README.md for setup
# Database view: public.vw_agent_memory
# Access: Via database service credentials
# Documentation: docs/n8n/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## 📄 License



## 📊 Dashboard Setup


1. **Frontend**
   
```bash
   cd frontend
   npm install
   cp .env.example .env.local   # adjust API base URL if needed
   npm run dev
   ```
   - The dev server runs on `<http://localhost:3000>`.
   - Ensure the backend is running (see below) before logging in.
2. **Create admin user** (optional, if not already created):
   
```bash
   python backend/scripts/create_admin_user.py
   ```
   - Use the credentials to log in to the dashboard.


## 🧪 Testing


### End‑to‑End (E2E) Tests
- Run: `npm run test:e2e`
- UI mode: `npm run test:e2e:ui`
- Single spec: `npx playwright test path/to/spec.ts`

### API Tests
- Run: `pytest tests/api/`
- With coverage: `pytest tests/api/ --cov=backend --cov-report=xml`

### Performance Tests
- Load test (HTTP): `locust -f tests/performance/load_test.py`
- WebSocket load test: `python tests/performance/websocket_load_test.py`

### WebSocket Tests
- Reconnection is verified by closing the socket in the test and asserting UI recovers.
- Alert dismissal is covered in the E2E suite.


## 📚 Documentation

- Dashboard user guide: `docs/dashboard/USER_GUIDE.md`
- API reference: `docs/api/DASHBOARD_API.md`
- Testing guide: `docs/testing/TESTING_GUIDE.md`


## 🛠️ Troubleshooting

- **E2E failures**: ensure Playwright browsers are installed (`npx playwright install`).
- **WebSocket disconnects**: check backend logs for connection errors.
- **Performance test hangs**: verify the test database is reachable and not throttled.


## 📄 License


This project is licensed under the MIT License - see the LICENSE file for details.


## 🙏 Acknowledgments


- **Ollama** for local AI model serving
- **PostgreSQL** for database infrastructure
- **MinIO** for object storage
- **PyMuPDF** for PDF processing
- **Hugging Face** for AI models


## 📞 Support


- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - See `docs/` folder
- **Database Migrations** - See `database/migrations/`

---

**🎉 Ready to transform your documents into intelligent, searchable knowledge!**

## 📝 Recent Updates

### **Phase 6 - Advanced Multimodal AI Features** (December 2025)
- ✅ **Hierarchical Document Structure Detection** with automatic section linking
- ✅ **SVG Vector Graphics Processing** with Vision AI analysis and PNG conversion
- ✅ **Multimodal Search Service** with unified interface across all content types
- ✅ **Advanced Context Extraction** for images, videos, links, and tables
- ✅ **Enhanced Database Schema** with unified embeddings and cross-chunk linking
- ✅ **Comprehensive Test Suite** with 7 validation scripts for all features
- ✅ **Production-Ready Architecture** with scalable service design
- ✅ **Advanced Web Scraping** with Firecrawl integration and structured extraction

### **Previous Updates**
- ✅ **November 2025**: Real-time monitoring system with WebSocket API
- ✅ **Monitoring & Alerts**: Comprehensive metrics, alerts, and real-time updates
- ✅ **Server-Side Aggregation**: Scalable metrics queries with database views
- ✅ **October 2025**: Complete refactoring - organized structure
- ✅ **SVG Support**: Automatic SVG to PNG conversion with fallback
- ✅ **Vision Model Optimization**: llava-phi3 with keep-alive management
- ✅ **n8n Integration**: Dedicated database user with RLS policies
- ✅ **Performance**: 100x faster embedding queries with batch operations
- ✅ **Documentation**: Organized into docs/ folder with categories
- ✅ **Content APIs**: CRUD + enrichment endpoints for error codes, videos, and images

## 🧪 Phase 6 Testing

The comprehensive test suite validates all Phase 1-6 features:

```bash
# Run all Phase 6 tests
python scripts/test_full_pipeline_phases_1_6.py --verbose
python scripts/test_hierarchical_chunking.py --verbose
python scripts/test_svg_extraction.py --verbose
python scripts/test_multimodal_search.py --verbose
python scripts/test_minio_storage_operations.py --verbose
python scripts/test_postgresql_migrations.py --verbose
python scripts/test_context_extraction_integration.py --verbose
```

## 📚 Documentation

### **Phase 6 Documentation**
- **[Phase 6 Advanced Features](docs/PHASE_6_ADVANCED_FEATURES.md)** - Comprehensive feature overview
- **[System Architecture](docs/ARCHITECTURE.md)** - Complete system design and components
- **[Migration Guide](docs/MIGRATION_GUIDE_CLOUD_TO_LOCAL.md)** - Cloud to local setup migration
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES_REFERENCE.md)** - Complete configuration reference

### **Existing Documentation**
- Dashboard user guide: `docs/dashboard/USER_GUIDE.md`
- API reference: `docs/api/DASHBOARD_API.md`
- Testing guide: `docs/testing/TESTING_GUIDE.md`
- **Setup**: `docs/setup/` - Installation and configuration
- **Architecture**: `docs/architecture/` - System design and pipeline
- **API Reference**: `docs/api/` - REST API documentation
- **Version Management**: `docs/development/VERSION_MANAGEMENT.md` - Automatic version synchronization
- **Troubleshooting**: `docs/troubleshooting/` - Common issues and fixes
- **n8n Integration**: `docs/n8n/` - Automation workflows
- **Performance Features**: `docs/PERFORMANCE_FEATURES.md` - Structured text capping, OCR fallback, telemetry, statistics
- **Web Scraping**: `docs/PRODUCT_RESEARCH.md` - Firecrawl integration and examples
- **Firecrawl Examples**: `examples/README.md` - Complete web scraping examples
