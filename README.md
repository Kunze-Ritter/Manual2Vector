# 🚀 KRAI - Knowledge Retrieval and Intelligence

Advanced Multimodal AI Document Processing Pipeline with Local-First Architecture and Vector Search

## 🚀 Quick Start (Docker - Recommended)

### ⚡ One-Command Setup (Linux/macOS)

```bash
git clone https://github.com/Kunze-Ritter/Manual2Vector
cd Manual2Vector
./setup.sh  # Generates all 15+ secrets, RSA keys, and passwords automatically
docker-compose -f docker-compose.simple.yml up --build -d
```

### ⚡ One-Command Setup with Firecrawl (Advanced Web Scraping)

```bash
git clone https://github.com/Kunze-Ritter/Manual2Vector
cd Manual2Vector
./setup.sh  # Generates all 15+ secrets, RSA keys, and passwords automatically
docker-compose -f docker-compose.with-firecrawl.yml up --build -d
```

### ⚡ One-Command Setup (Windows)

```cmd
git clone https://github.com/Kunze-Ritter/Manual2Vector
cd Manual2Vector
# Recommended: PowerShell (Windows 10/11)
.\setup.ps1  # Modern, secure, and maintainable

# Alternative: Batch (legacy fallback for older Windows)
setup.bat
docker-compose -f docker-compose.simple.yml up --build -d
```

### ⚡ One-Command Setup with Firecrawl (Windows)

```cmd
git clone https://github.com/Kunze-Ritter/Manual2Vector
cd Manual2Vector
# Recommended: PowerShell (Windows 10/11)
.\setup.ps1  # Modern, secure, and maintainable

# Alternative: Batch (legacy fallback for older Windows)
setup.bat
docker-compose -f docker-compose.with-firecrawl.yml up --build -d
```

**🎉 That's it! Your system is running!**

### 🔄 Quick Start from Scratch (Clean Environment)

If you need to completely reset your Docker environment or start fresh:

**Linux/macOS:**
```bash
./scripts/docker-clean-setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\docker-clean-setup.ps1
```

This script performs:
- ✅ Stops all containers with `docker-compose down` 
- ✅ Removes all KRAI volumes (postgres, minio, ollama, redis, laravel)
- ✅ Prunes Docker networks
- ✅ Starts fresh containers with `docker-compose up -d` 
- ✅ Waits 60 seconds for service initialization
- ✅ Verifies seed data (14 manufacturers, 4 retry policies)

**Exit Codes:**
- `0` - Success: All steps completed, seed data verified
- `1` - Failure: One or more steps failed

> **⚠️ Warning:** This script removes all Docker volumes and data. Use only when you need a completely fresh start.

> **📖 Detailed Documentation:** See [DOCKER_SETUP.md - Clean Setup Scripts](DOCKER_SETUP.md#-clean-setup-scripts) for comprehensive usage examples and troubleshooting.

### 🚀 Complete Docker Setup & Validation (All-in-One)

For a comprehensive setup that includes clean environment reset, health checks, integration tests, and persistency validation:

**Linux/macOS:**
```bash
./scripts/full-docker-setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\full-docker-setup.ps1
```

**What this script does:**
1. ✅ **Clean Setup** - Resets Docker environment (stops containers, removes volumes, starts fresh)
2. ✅ **Health Check** - Validates all services (PostgreSQL, FastAPI, Laravel, MinIO, Ollama)
3. ✅ **Integration Tests** - Tests service-to-service connectivity
4. ✅ **Persistency Tests** - Verifies data survives container restarts

**Duration:** ~8-10 minutes (depending on system performance)

**Exit Codes:**
- `0` - All steps completed successfully
- `1` - Completed with warnings (system functional but degraded)
- `2` - Critical errors detected (manual intervention required)

**Options:**
```bash
# Skip clean setup (faster, for quick validation)
./scripts/full-docker-setup.sh --skip-clean

# Skip integration tests
./scripts/full-docker-setup.sh --skip-integration

# Save logs to file
./scripts/full-docker-setup.sh --log-file setup.log
```

**When to use:**
- 🆕 Initial project setup
- 🔄 After major configuration changes
- 🐛 Troubleshooting environment issues
- ✅ Pre-deployment validation
- 📊 CI/CD pipeline integration

> **💡 Tip:** For faster validation without data reset, use `./scripts/docker-health-check.sh` followed by `./scripts/docker-integration-tests.sh`

> **📖 Detailed Documentation:** See [DOCKER_SETUP.md - Full Docker Setup](DOCKER_SETUP.md#-full-docker-setup-orchestrator) for comprehensive usage and troubleshooting.

---

> **Dashboard Interface:** KRAI uses **Laravel/Filament** as the sole dashboard interface at http://localhost:80. This provides visual pipeline management, document processing control, and real-time monitoring capabilities.

**Access your services:**

- 🖥️ **Laravel Dashboard**: `http://localhost:80`
- ⚙️ **API**: `http://localhost:8000`
- 📊 **API Docs**: `http://localhost:8000/docs`
- 🏥 **Health Check**: `http://localhost:8000/health`
- 💾 **MinIO Console**: `http://localhost:9001` (credentials from `.env`)
  - Setup scripts may randomize MinIO credentials—check your `.env` for the current values.
- 🔥 **Firecrawl API**: `http://localhost:9002` (nur mit Firecrawl-Setup)

**🔐 What the setup script does:**
- ✅ Generates 15+ cryptographically secure passwords
- ✅ Creates RSA 2048-bit keypair for JWT authentication
- ✅ Consolidates all configuration into single `.env` file (10 sections)
- ✅ Validates all required variables are set
- ✅ Shows generated credentials for your reference

**📋 Manual configuration required:**
- YouTube API Key (optional): Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Cloudflare Tunnel Token (optional): Get from [Cloudflare Dashboard](https://dash.cloudflare.com/)

### 📋 Manual Setup (Alternative)

```bash
git clone https://github.com/Kunze-Ritter/Manual2Vector
cd Manual2Vector
cp .env.example .env  # Contains 10 sections with 60+ configuration variables
docker-compose -f docker-compose.simple.yml up --build -d
```

# ⚠️ Warning: Manual setup requires editing 15+ secrets - use setup.sh instead!

**Windows Setup Scripts:**

- **setup.ps1** (Recommended): Modern PowerShell script for Windows 10/11
  - Uses .NET Crypto APIs for secure secret generation
  - Shorter and more maintainable than setup.bat (299 vs. 744 lines)
  - Requires PowerShell 5.0+ (included in Windows 10/11)
  - Fallback to OpenSSL if .NET APIs unavailable

- **setup.bat** (Legacy): Batch script for older Windows versions
  - Use only if PowerShell 5.0+ is not available
  - More complex and harder to debug
  - Requires PowerShell for password generation

## 🏗️ What's Included

| Service | Port | Technology | Description | Available In |
|---------|------|------------|-------------|--------------|
| **Laravel Dashboard** | 80 | Laravel + Filament | Admin Dashboard | All compose files |
| **Backend API** | 8000 | FastAPI + Uvicorn | REST API Server | All compose files |
| **Database** | 5432 | PostgreSQL + pgvector | Vector Database | All compose files |
| **Storage** | 9000/9001 | MinIO | Object Storage | All compose files |
| **AI Service** | 11434 | Ollama | Large Language Models | All compose files |
| **Redis** | 6379 | Redis | Cache/Queue | with-firecrawl, production |
| **Playwright** | 3000 | Chrome | Browser Automation | with-firecrawl, production |
| **Firecrawl API** | 9002 | Firecrawl | Advanced Web Scraping | with-firecrawl, production |
| **Firecrawl Worker** | - | Firecrawl | Web Scraping Worker | production |

*Redis, Playwright, and Firecrawl services are only available with `docker-compose.with-firecrawl.yml` and `docker-compose.production.yml`*

## 🐳 Docker Compose Files

The project provides 4 production-ready Docker Compose configurations:

### docker-compose.simple.yml
**Use Case**: Minimal development setup
**Services**: Laravel Dashboard, Backend, PostgreSQL, MinIO, Ollama (5 services)
**Best for**: Quick testing, development, resource-constrained environments
**Features**: No Firecrawl, no GPU required, clean minimal stack

### docker-compose.with-firecrawl.yml
**Use Case**: Development with advanced web scraping
**Services**: All simple.yml services + Redis, Playwright, Firecrawl API (10 services)
**Best for**: Testing web scraping features, document processing with web sources
**Features**: Includes Firecrawl for better web content extraction

### docker-compose.production.yml
**Use Case**: Production deployment
**Services**: All with-firecrawl.yml services + Firecrawl Worker (11 services)
**Best for**: Production deployments, GPU-accelerated inference
**Features**: GPU support for Ollama, optimized PostgreSQL settings, production healthchecks

### docker-compose.staging.yml
**Use Case**: Isolated staging environment for performance benchmarking
**Services**: Backend (port 8001), PostgreSQL (port 5433), shares production Ollama and MinIO
**Best for**: Performance testing, benchmarking, regression detection
**Features**: BENCHMARK_MODE=true, separate database (krai_staging), benchmark-documents mount
**Quick Start**: `docker-compose -f docker-compose.staging.yml up -d`

> **Note**: 7 deprecated Docker Compose files have been archived to reduce confusion. See `archive/docker/README.md` for details.

## 📖 Documentation

### Core Documentation
- 🎯 **[Master TODO](MASTER-TODO.md)** - Consolidated project-wide task list
- 🐳 **[Docker Setup Guide](DOCKER_SETUP.md)** - Complete installation instructions
- 🗄️ **[Database Schema](DATABASE_SCHEMA.md)** - Database structure and migrations
- 🔐 **[Security Reference](docs/SECURITY.md)** - Hardening checklist and best practices

### Pipeline Documentation
- 🏗️ **[Pipeline Architecture](docs/processor/PIPELINE_ARCHITECTURE.md)** - 15-stage modular pipeline design
- 📋 **[Stage Reference](docs/processor/STAGE_REFERENCE.md)** - Detailed documentation for all processing stages
- 🚀 **[Quick Start](docs/processor/QUICK_START.md)** - CLI, API, and dashboard usage examples

### Technical Documentation
- 🏗️ **[Architecture](docs/architecture/)** - System design and components
- 🔧 **[API Documentation](docs/api/)** - REST API reference with stage-based endpoints
- 🧪 **[Testing](tests/)** - Test suites and E2E tests

### Project Management
- 📋 **[Pipeline TODO](docs/project_management/TODO.md)** - Pipeline-specific tasks
- 🎨 **[Dashboard TODO](docs/project_management/TODO_PRODUCT_CONFIGURATION_DASHBOARD.md)** - Dashboard implementation
- 📦 **[Accessories TODO](docs/project_management/TODO_PRODUCT_ACCESSORIES.md)** - Accessories system
- 🔧 **[Foliant TODO](docs/project_management/TODO_FOLIANT.md)** - Foliant compatibility system

### Archived Documentation
- 📚 **[Archive](archive/docs/)** - Historical documentation and completed implementations
  - `completed/` - Successfully completed features
  - `outdated/` - Superseded analysis and plans
  - `superseded/` - Old task lists (replaced by MASTER-TODO.md)

## 🔐 Security Features

- **Automatic Password Generation**: Setup scripts (setup.sh, setup.ps1, setup.bat) create 15+ cryptographically secure passwords and RSA keys
- **Consolidated Configuration**: Single `.env` file with 10 logical sections for easy management
- **Environment Validation**: Built-in validation script checks all required variables before startup
- **Local-First Architecture**: All data stays on your infrastructure
- **Docker Isolation**: Services run in isolated containers
- **Environment Variables**: Sensitive configuration stored securely in `.env` file

## 🛠️ Requirements

- **Docker** & **Docker Compose** (latest versions recommended)
- **Git** for cloning the repository
- **4GB+ RAM** for optimal performance
- **10GB+ disk space** for Docker images and data

## 🎯 Overview

KRAI is a comprehensive multimodal AI system that automatically extracts, analyzes, and indexes technical documents with advanced features including hierarchical structure detection, SVG vector graphics processing, and intelligent multimodal search. Built with a **local-first architecture** using PostgreSQL and MinIO, KRAI provides complete control over your data while offering optional cloud migration capabilities when needed.

## ✨ Key Features

### 🔄 Stage-Based Processing Pipeline

- **15-Stage Modular Architecture** - Granular control over document processing
- **Stage Orchestration** - UPLOAD → TEXT_EXTRACTION → TABLE_EXTRACTION → SVG_PROCESSING → IMAGE_PROCESSING → VISUAL_EMBEDDING → LINK_EXTRACTION → CHUNK_PREPROCESSING → CLASSIFICATION → METADATA_EXTRACTION → PARTS_EXTRACTION → SERIES_DETECTION → STORAGE → EMBEDDING → SEARCH_INDEXING
- **Individual Stage Execution** - Run specific stages on-demand via CLI or API
- **Smart Processing** - Skip completed stages and resume from failures
- **Real-time Status Tracking** - Monitor progress of each stage independently
- **Error Isolation** - One stage failure doesn't stop the entire pipeline
- **Reference**: `docs/processor/PIPELINE_ARCHITECTURE.md` for detailed architecture

### 🤖 Advanced AI-Powered Processing

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

### 🏗️ Local-First Architecture

- **Docker Compose Setup** - Complete local deployment in 5 minutes
- **PostgreSQL + pgvector** - Production vector database with semantic search
- **MinIO Object Storage** - Production S3-compatible storage for documents and images
- **Ollama AI Service** - Local LLM inference with multiple models
- **FastAPI Backend** - High-performance REST API with async support
- **Laravel/Filament Dashboard** - Admin interface at http://localhost:80 with visual pipeline management
- **PostgreSQL-Only Architecture** - Complete migration from Supabase (November 2024, KRAI-002) for data sovereignty and local-first control

#### 🎛️ Pipeline Control

- **CLI Interface** - `scripts/pipeline_processor.py` with stage selection and batch processing
- **Stage-Based API** - Individual and multiple stage execution via REST endpoints
- **Laravel Dashboard** - Visual pipeline management with real-time status updates
- **Smart Processing** - Automatic detection of completed stages and selective reprocessing
- **Error Recovery** - Individual stage retry and dependency chain reprocessing
- **Performance Monitoring** - Stage-by-stage timing and resource usage tracking
- **Reference**: Comprehensive guides in `docs/processor/` directory

## 🔍 Intelligent Search & Discovery

- **Semantic Vector Search** across all document content
- **Multimodal Search** - Find documents by text, images, or visual similarity
- **Error Code Search** - Search for specific error codes across manufacturers
- **Product & Model Search** - Find documents by product names and models
- **Hierarchical Navigation** - Browse documents by structure and sections
- **Context-Aware Results** - Search with surrounding context for better relevance

### 📊 Advanced Document Processing

- **Stage-Specific Capabilities** - Text extraction, image analysis, table parsing, SVG conversion, link extraction, metadata extraction, parts cataloging, series detection, and more
- **Intelligent Stage Selection** - Choose specific processing stages based on document type and requirements
- **Stage-Based API Endpoints** - Programmatic control over individual stages (`docs/api/STAGE_BASED_PROCESSING.md`)
- **Laravel Dashboard Integration** - Visual stage management and control via Filament UI
- **Automatic Feature Extraction** - Extract technical specifications and features
- **Product Research Integration** - Automatic online research for unknown products
- **Video Content Analysis** - Extract and index video transcripts and metadata
- **Table Extraction & Analysis** - Parse and analyze tabular data
- **Link & Reference Processing** - Extract and resolve document links
- **Version Detection** - Track document versions and updates

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** for version control

### Installation Steps

- **Clone the repository:**

```bash
git clone <repository-url>
cd Manual2Vector
```

- **Run the setup script:**

```bash
# Linux/macOS
./setup.sh

# Windows (PowerShell 5+ recommended)
# Run from an elevated PowerShell prompt if required by your environment
```

```powershell
cd Manual2Vector
.\setup.ps1
```

> **Note:** `setup.bat` remains available as a legacy fallback for Windows versions without PowerShell 5+.

- **Start the services:**

```bash
docker-compose -f docker-compose.simple.yml up --build -d
```

- **Verify installation:**

```bash
curl http://localhost:8000/health
```

- **Start processing documents:**

```bash
# Process with full pipeline
python scripts/pipeline_processor.py --file /path/to/document.pdf

# Or use stage-based processing
python scripts/pipeline_processor.py --document-id <uuid> --stage text_extraction
```

> **Note:** For detailed pipeline usage, see `docs/processor/QUICK_START.md`

## 🏥 Health & Monitoring

### Automated Health Checks

Run comprehensive health checks for all services:

**Linux/macOS:**
```bash
./scripts/docker-health-check.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\docker-health-check.ps1
```

**Checks performed:**
- ✅ PostgreSQL: Connection, schema count (6), table count (44), seed data
- ✅ FastAPI Backend: `/health` endpoint, database connectivity, API docs
- ✅ Laravel Admin: Dashboard, login page, database connection, Filament resources
- ✅ MinIO: API health, console accessibility, bucket operations
- ✅ Ollama: API availability, model presence (`nomic-embed-text`), embedding generation

**Exit Codes:**
- `0` - All checks passed
- `1` - Warnings detected (system functional but degraded)
- `2` - Critical errors (system may not function properly)

### Data Persistency Testing

Verify data survives container restarts:

**Linux/macOS:**
```bash
./scripts/docker-health-check.sh --test-persistency
```

**Windows (PowerShell):**
```powershell
.\scripts\docker-health-check.ps1 -TestPersistency
```

This test:
1. Creates test data in PostgreSQL
2. Stops containers with `docker-compose down` 
3. Restarts containers with `docker-compose up -d` 
4. Verifies data persisted
5. Validates volume mounts (postgres_data, minio_data, ollama_data)

### Integration Testing

Test service-to-service connectivity:

**Windows (PowerShell):**
```powershell
.\scripts\docker-integration-tests.ps1
```

**Tests performed:**
- Backend → PostgreSQL: Query, write, transaction rollback
- Backend → MinIO: Upload, download, delete
- Backend → Ollama: Embedding generation, model availability
- Laravel → Backend: REST API calls, JWT authentication
- Laravel → PostgreSQL: Eloquent models (Product, User, PipelineError)

**Environment Variables:**
- `BACKEND_API_TOKEN` - Required for authenticated tests (optional)

**Exit Codes:**
- `0` - All integration tests passed
- `1` - Some tests passed with warnings
- `2` - Critical integration failures

### Service Health Endpoints

- **API Health**: `http://localhost:8000/health` 
- **Database**: PostgreSQL connection monitoring
- **Storage**: MinIO bucket availability
- **AI Service**: Ollama model status

### Monitoring Endpoints

- **System Metrics**: `http://localhost:8000/metrics` 
- **API Documentation**: `http://localhost:8000/docs` 
- **Service Status**: `http://localhost:8000/status`

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env` (10 sections, 60+ variables):

```bash
# Database Configuration (PostgreSQL)
DATABASE_TYPE=postgresql
DATABASE_HOST=krai-postgres
DATABASE_PORT=5432
DATABASE_NAME=krai
DATABASE_USER=krai_user
DATABASE_PASSWORD=<generated-password>
DATABASE_CONNECTION_URL=postgresql://krai_user:<password>@krai-postgres:5432/krai

# Object Storage (MinIO)
OBJECT_STORAGE_TYPE=s3
OBJECT_STORAGE_ENDPOINT=http://krai-minio:9000
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=<generated-password>

# AI Service (Ollama)
OLLAMA_URL=http://krai-ollama:11434
```

> **Note:** The backend uses `OLLAMA_URL` for AI service communication. All passwords are generated automatically by setup scripts.

### .env.local Example

For host-based runs, you can override specific configuration options in `.env.local`. Create a `.env.local` file by copying `.env.local.example`:

```bash
cp .env.local.example .env.local
```

Then, update the necessary variables, such as `DATABASE_HOST` and `OBJECT_STORAGE_ENDPOINT`, to point to `localhost`:

```bash
DATABASE_HOST=localhost
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
```

### Setup Script Comparison

| Feature | setup.sh | setup.ps1 | setup.bat |
|---------|----------|-----------|----------|
| Platform | Linux/macOS | Windows 10/11 | Windows (all) |
| Lines of Code | 855 | 299 | 744 |
| Crypto API | OpenSSL | .NET + OpenSSL | PowerShell + OpenSSL |
| Maintainability | ✅ High | ✅ High | ⚠️ Medium |
| Recommended | ✅ Yes | ✅ Yes | ⚠️ Legacy only |

**Recommendation:**
- **Linux/macOS:** Use `./setup.sh` 
- **Windows 10/11:** Use `.\setup.ps1` (PowerShell)
- **Older Windows:** Use `setup.bat` as fallback

### Environment Validation

Validate your `.env` file before starting Docker:

```bash
# Check all required variables are set
python scripts/validate_env.py

# Verbose output with detailed checks
python scripts/validate_env.py --verbose

# Treat warnings as errors (strict mode)
python scripts/validate_env.py --strict
```

### Service Verification

After starting Docker, verify all services are healthy:

```bash
# Check all Docker services
python scripts/verify_local_setup.py

# Check specific service
python scripts/verify_local_setup.py --service postgresql
```

### Custom Models

Configure custom AI models:

```bash
# Text Classification Model
AI_TEXT_MODEL=llama3.2:latest

# Embeddings Model
AI_EMBEDDING_MODEL=nomic-embed-text:latest

# Vision Model
AI_VISION_MODEL=llava:7b
```

## 📚 Advanced Usage

### API Integration

```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')

# Document upload
with open('document.pdf', 'rb') as f:
    response = requests.post('http://localhost:8000/documents', files={'file': f})

# Semantic search
response = requests.post('http://localhost:8000/search', json={
    'query': 'error code 900.01',
    'limit': 10
})
```

### Docker Management

```bash
# View logs
docker-compose -f docker-compose.simple.yml logs -f

# Stop services
docker-compose -f docker-compose.simple.yml down

# Update containers
docker-compose -f docker-compose.simple.yml pull
docker-compose -f docker-compose.simple.yml up --build -d
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd Manual2Vector

# Setup development environment
cd backend
pip install -r requirements.txt

# Run development server
python -m uvicorn main:app --reload
```

> **Host-based backend tip:** Before running `uvicorn` outside Docker, copy `.env.local.example` to `.env.local` and override `DATABASE_HOST` / `POSTGRES_HOST` to `localhost` so the backend reaches the containers via published ports.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **API Reference**: `http://localhost:8000/docs`
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Environment Validation**: `python scripts/validate_env.py`
- **Service Verification**: `python scripts/verify_local_setup.py`
- **Troubleshooting**: [DOCKER_SETUP.md](DOCKER_SETUP.md#troubleshooting)

## 🔧 Troubleshooting

### Common Issues

**Environment Configuration:**
- **Missing `.env` file**: Run `./setup.sh` or `.\setup.ps1` to generate
- **Invalid credentials**: Check `python scripts/validate_env.py` output
- **Port conflicts**: See [DOCKER_SETUP.md](DOCKER_SETUP.md#troubleshooting) for solutions
- **Legacy Supabase Migration (Reference Only)**: See [SUPABASE_TO_POSTGRESQL_MIGRATION.md](docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md) - migration completed November 2024 (KRAI-002)

**Docker Services:**
- **Container not starting**: Check logs with `docker-compose logs [service]`
- **Out of memory**: Reduce model sizes or increase Docker memory limit
- **GPU not detected**: Install NVIDIA Container Toolkit (see [DOCKER_SETUP.md](DOCKER_SETUP.md))

**Setup Script Issues:**
- **PowerShell script not found**: Ensure you're using `.\setup.ps1` (with backslash) on Windows
- **PowerShell execution policy**: Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` if blocked
- **setup.bat fails**: Try `.\setup.ps1` instead (recommended for Windows 10/11)
- **OpenSSL not found**: Install OpenSSL or use PowerShell 7+ (includes .NET Crypto APIs)

**For detailed troubleshooting, see [DOCKER_SETUP.md](DOCKER_SETUP.md#troubleshooting)**

## 🎉 Acknowledgments

- **Ollama** - Local LLM inference
- **PostgreSQL** - Vector database
- **MinIO** - Object storage
- **FastAPI** - Web framework
- **Laravel/Filament** - Dashboard framework

---

## Built with ❤️ for the open-source community
