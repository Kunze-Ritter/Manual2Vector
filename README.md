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

**Access your services:**

- 🖥️ **Frontend**: `http://localhost:80`
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

| Service | Port | Technology | Description |
|---------|------|------------|-------------|
| **Frontend** | 80 | React + Nginx | Production Dashboard |
| **Backend API** | 8000 | FastAPI + Uvicorn | REST API Server |
| **Database** | 5432 | PostgreSQL + pgvector | Vector Database |
| **Storage** | 9000/9001 | MinIO | Object Storage |
| **AI Service** | 11434 | Ollama | Large Language Models |
| **Redis** | 6379 | Redis | Cache/Queue (Firecrawl) |
| **Playwright** | 3000 | Chrome | Browser Automation |
| **Firecrawl API** | 9002 | Firecrawl | Advanced Web Scraping |

*Firecrawl, Redis und Playwright sind optional und nur mit `docker-compose.with-firecrawl.yml` verfügbar*

## 📖 Documentation

- 🐳 **[Docker Setup Guide](DOCKER_SETUP.md)** - Complete installation instructions
- 🔐 **Setup Scripts** - Automatic password generation (`./setup.sh`, `./setup.ps1`, or `setup.bat`)
- 🏗️ **[Architecture](docs/architecture/)** - System design and components
- 🔧 **[API Documentation](docs/api/)** - REST API reference
- 🧪 **[Testing](tests/)** - Test suites and E2E tests

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

KRAI is a comprehensive multimodal AI system that automatically extracts, analyzes, and indexes technical documents with advanced features including hierarchical structure detection, SVG vector graphics processing, and intelligent multimodal search. Built with a **local-first architecture**, KRAI provides complete control over your data while offering cloud migration capabilities when needed.

## ✨ Key Features

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
- **PostgreSQL + pgvector** - Vector database with semantic search
- **MinIO Object Storage** - S3-compatible storage for documents and images
- **Ollama AI Service** - Local LLM inference with multiple models
- **FastAPI Backend** - High-performance REST API with async support
- **React Frontend** - Modern web interface with real-time updates

### 🔍 Intelligent Search & Discovery

- **Semantic Vector Search** across all document content
- **Multimodal Search** - Find documents by text, images, or visual similarity
- **Error Code Search** - Search for specific error codes across manufacturers
- **Product & Model Search** - Find documents by product names and models
- **Hierarchical Navigation** - Browse documents by structure and sections
- **Context-Aware Results** - Search with surrounding context for better relevance

### 📊 Advanced Document Processing

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

## 🏥 Health & Monitoring

### Service Health Checks

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
# Database Configuration
DATABASE_TYPE=postgresql
DATABASE_HOST=krai-postgres
DATABASE_PORT=5432
DATABASE_NAME=krai
DATABASE_USER=krai_user
DATABASE_PASSWORD=<generated-password>

# Object Storage
OBJECT_STORAGE_ENDPOINT=http://krai-minio:9000
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=<generated-password>

# AI Service
OLLAMA_URL=http://krai-ollama:11434
AI_SERVICE_URL=http://krai-ollama:11434
```

> **Note:** The backend reads `OLLAMA_URL`. Keep `AI_SERVICE_URL` for tooling only if needed, and ensure both values stay synchronized.

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

# Frontend development
cd frontend
npm install
npm run dev
```

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
- **PostgreSQL + pgvector** - Vector database
- **MinIO** - Object storage
- **FastAPI** - Web framework
- **React** - Frontend framework

---

## Built with ❤️ for the open-source community
