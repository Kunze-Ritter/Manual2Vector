# 🚀 KR-AI-Engine - Manual2Vector

**Intelligent Document Processing Pipeline with AI-Powered Classification and Vector Search**

## 🎯 Overview

KR-AI-Engine is a comprehensive document processing system that automatically extracts, analyzes, and indexes technical manuals and service documents. It combines advanced AI models with efficient data processing to create a searchable knowledge base from PDF documents.

## ✨ Key Features

### 🤖 **AI-Powered Processing**
- **Smart Document Classification** using Ollama LLM models
- **Intelligent Text Chunking** with semantic analysis
- **Image Recognition** and OCR with vision models (with SVG support!)
- **Vector Embeddings** for semantic search
- **Manufacturer & Model Detection** with normalization
- **Error Code Extraction** with 17 manufacturer patterns
- **Multi-Source Search** (documents, videos, keywords)

### 🎬 **Video Enrichment System**
- **11 Video Formats** (MP4, WebM, MOV, AVI, MKV, M4V, FLV, WMV, MPEG, MPG, 3GP)
- **4 Platforms** (YouTube, Vimeo, Brightcove, Direct)
- **Thumbnail Generation** with OpenCV
- **Auto-Create** manufacturers & products
- **Video ↔ Product Linking** (many-to-many)
- **Video ↔ Error Code Linking**

### 🔧 **Error Code System**
- **17 Manufacturers** supported (HP, Canon, Lexmark, etc.)
- **Product-Specific** error codes
- **Manufacturer Filters** (HP technician-only solutions)
- **Multi-Source Search** (documents + videos + related)
- **Confidence Scoring** (0.60 threshold)
- **Smart Deduplication**

### 📊 **8-Stage Processing Pipeline**
1. **Upload Processor** - Document ingestion and deduplication
2. **Text Processor** - Smart chunking with AI analysis
3. **Image Processor** - Original format preservation, OCR, AI vision
4. **Classification Processor** - Manufacturer/product detection
5. **Metadata Processor** - Error codes and version extraction
6. **Storage Processor** - Cloudflare R2 object storage
7. **Embedding Processor** - Vector embeddings for search
8. **Search Processor** - Search analytics and indexing

### 🏗️ **Production-Ready Architecture**
- **Database Adapter Pattern** - Support for Supabase, PostgreSQL, Docker PostgreSQL
- **Flexible Database Backend** - Switch between cloud and self-hosted
- **Cloudflare R2** object storage
- **GPU Acceleration** for AI models
- **Parallel Processing** for optimal performance
- **Comprehensive Monitoring** and logging

## 🚀 Quick Start

### **Prerequisites**
- Python 3.9+
- NVIDIA GPU (recommended)
- 16+ GB RAM
- Supabase account
- Cloudflare R2 account
- Ollama installed

### **Installation**
```bash
# Clone repository
git clone https://github.com/Kunze-Ritter/Manual2Vector.git
cd Manual2Vector

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Install Ollama models
ollama pull llama3.2:latest
ollama pull nomic-embed-text:latest
ollama pull llava-phi3:latest

# Run the application
python backend/pipeline/master_pipeline.py
```

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
- **`krai_content`**: Chunks, images, print_defects  
- **`krai_intelligence`**: Embeddings, error_codes, search_analytics
- **`krai_system`**: Processing_queue, audit_log, system_metrics
- **`krai_agent`**: Memory for n8n AI agent integration

### **Key Features**
- **Deduplication** at document, image, and chunk levels
- **Vector Search** with pgvector embeddings
- **Manufacturer Normalization** (HP → HP Inc.)
- **Model Detection** for all variants and options
- **Error Code Extraction** with pattern matching + AI
- **SVG to PNG Conversion** for vision model compatibility

## 🔧 Configuration

### **Environment Variables**
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# Cloudflare R2
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_ENDPOINT_URL=your_r2_endpoint

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_KEEP_ALIVE=30s

# Vision Model
VISION_MODEL=llava-phi3:latest
VISION_ENABLED=true

# System
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
- **Supabase** - Database and authentication
- **Ollama** - Local AI model serving
- **PyMuPDF** - PDF processing
- **PyTorch** - AI/ML framework
- **Tesseract OCR** - Text recognition
- **svglib** - SVG to PNG conversion

### **AI Models**
- **llama3.2:latest** - Text classification (2.0 GB)
- **nomic-embed-text:latest** - Vector embeddings (274 MB)
- **llava-phi3:latest** - Vision analysis (3.8 GB, stable)

### **Storage**
- **Supabase PostgreSQL** - Relational data with pgvector
- **Cloudflare R2** - Object storage for images and documents
- **Local Processing** - Temporary file handling

## 📁 Project Structure

```
KRAI-minimal/
├── backend/
│   ├── pipeline/         # Main processing pipelines ⭐ NEW
│   ├── processors/       # Active processor implementations
│   ├── services/         # Database, AI, storage services
│   ├── api/              # REST API endpoints
│   ├── config/           # Configuration files
│   ├── core/             # Base classes and data models
│   ├── utils/            # Utility functions
│   ├── scripts/          # Utility scripts
│   ├── tests/            # Unit tests
│   └── requirements.txt  # Python dependencies
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
├── examples/             # Example scripts and usage demonstrations
├── n8n/                  # n8n integration ⭐ NEW
│   ├── workflows/        # n8n workflow files
│   └── credentials/      # n8n credential templates
├── scripts/              # Helper scripts (checks, migrations, utilities)
├── archive/              # Archived temp files and legacy assets
├── .env                  # Environment variables
└── README.md             # This file
```

For reorganization details, consult `docs/PROJECT_CLEANUP_LOG.md`.

## 🔍 Monitoring

### **Real-time Status**
- Document processing progress
- Stage-by-stage completion
- Hardware utilization (CPU/GPU/RAM)
- Error tracking and logging
- Performance metrics

### **Health Checks**
- Database connectivity
- Ollama service status
- R2 storage access
- GPU availability
- Model loading status

## 🚨 Troubleshooting

### **Common Issues**
1. **GPU not detected** - See `docs/troubleshooting/GPU_AUTO_DETECTION.md`
2. **Ollama connection failed** - See `docs/troubleshooting/OLLAMA_GPU_FIX.md`
3. **Vision model crashes** - See `docs/troubleshooting/VISION_MODEL_TROUBLESHOOTING.md`
4. **Database errors** - Check Supabase credentials and RLS policies
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
- **Version Management**: `docs/development/VERSION_MANAGEMENT.md` - Automatic version synchronization
- **Troubleshooting**: `docs/troubleshooting/` - Common issues and fixes
- **n8n Integration**: `docs/n8n/` - Automation workflows
- **Performance Features**: `docs/PERFORMANCE_FEATURES.md` - Structured text capping, OCR fallback, telemetry, statistics

## 🤖 N8N Integration

KRAI supports n8n automation with PostgreSQL Memory integration:

```bash
# See n8n/README.md for setup
# Database view: public.vw_agent_memory
# Access: Via Supabase service_role or anon key
# Documentation: docs/n8n/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local AI model serving
- **Supabase** for database infrastructure
- **Cloudflare** for object storage
- **PyMuPDF** for PDF processing
- **Hugging Face** for AI models

## 📞 Support

- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - See `docs/` folder
- **Database Migrations** - See `database/migrations/`

---

**🎉 Ready to transform your documents into intelligent, searchable knowledge!**

## 📝 Recent Updates

- ✅ **October 2025**: Complete refactoring - organized structure
- ✅ **SVG Support**: Automatic SVG to PNG conversion with fallback
- ✅ **Vision Model Optimization**: llava-phi3 with keep-alive management
- ✅ **n8n Integration**: Dedicated database user with RLS policies
- ✅ **Performance**: 100x faster embedding queries with batch operations
- ✅ **Documentation**: Organized into docs/ folder with categories
