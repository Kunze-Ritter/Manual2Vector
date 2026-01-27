# 🚀 KRAI Installation Guide - Local-First Architecture

This guide provides comprehensive instructions for installing KRAI with a local-first approach using Docker Compose. The local setup provides optimal performance, data privacy, and cost efficiency.

## 📋 System Requirements

### **Hardware Requirements:**
- **CPU**: 4+ cores recommended (8+ cores optimal)
- **RAM**: 8GB minimum (16GB+ recommended)
- **GPU**: NVIDIA GPU optional but recommended (4GB+ VRAM)
- **Storage**: 20GB+ free space for Docker containers and data

### **Software Requirements:**
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS
- **Docker Desktop**: 4.25+ with Docker Compose v2
- **Git**: Latest version

---

## 🐳 Option 1: Local Docker Setup (Recommended)

**Why choose Docker setup?**
- ✅ **5-minute installation** with zero configuration
- ✅ **Complete data privacy** - nothing leaves your infrastructure
- ✅ **Offline capability** - works without internet connection
- ✅ **Consistent environment** - eliminates "works on my machine" issues
- ✅ **Easy maintenance** - single command updates and backups
- ✅ **Resource efficient** - optimized containers with minimal overhead

### **Step 1: Install Docker Desktop**

#### **Windows:**
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Run the installer and restart when prompted
3. Start Docker Desktop from the Start menu
4. Verify installation: `docker --version` and `docker-compose --version`

#### **Linux (Ubuntu):**
```bash
# Update system packages
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group (logout/in required)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker compose version
```

#### **macOS:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop from Applications
```

### **Step 2: Clone Repository**

```bash
# Clone the repository
git clone https://github.com/your-org/KRAI-minimal.git
cd KRAI-minimal
```

### **Step 3: Quick Start Setup**

```bash
# Copy environment configuration
cp .env.example .env

# Start all services (PostgreSQL, MinIO, Ollama, API)
docker-compose up -d

# Wait for services to be ready (automated)
python scripts/wait_for_services.py

# Initialize database and storage
python scripts/initialize_system.py

# Pull AI models (takes a few minutes)
docker exec krai-ollama ollama pull nomic-embed-text:latest
docker exec krai-ollama ollama pull llama3.2:latest

# Verify everything is working
python scripts/health_check.py
```

### **Step 4: Access Your KRAI Instance**

Once setup is complete, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Laravel Dashboard**: http://localhost:9100
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)
- **pgAdmin**: http://localhost:5050 (admin@krai.local/krai_admin_2024)
- **Ollama API**: http://localhost:11434

### **Step 5: Test Your Installation**

```bash
# Run comprehensive test suite
python scripts/test_full_pipeline_phases_1_6.py --verbose

# Test document processing
python scripts/test_single_document.py service_documents/sample.pdf

# Test search functionality
python scripts/test_multimodal_search.py --query "fuser unit error"
```

---

## 🐳 Option 2: Cloud Setup (Optional)

> **Note**: Cloud setup is provided for users with specific cloud requirements. Local setup is recommended for optimal performance, data privacy, and cost efficiency.

See [docs/setup/CLOUD_SETUP_GUIDE.md](docs/setup/CLOUD_SETUP_GUIDE.md) and [docs/MIGRATION_GUIDE_CLOUD_TO_LOCAL.md](docs/MIGRATION_GUIDE_CLOUD_TO_LOCAL.md) for detailed cloud installation and migration instructions.

---

## 🔧 Advanced Configuration

### **Environment Customization**

For advanced users, you can customize the environment by editing `.env`:

```bash
# Database configuration
POSTGRES_DB=krai_db
POSTGRES_USER=krai_user
POSTGRES_PASSWORD=your_secure_password

# AI Model configuration
OLLAMA_KEEP_ALIVE=60s
ENABLE_VISION_ANALYSIS=true
ENABLE_HIERARCHICAL_CHUNKING=true

# Performance tuning
MAX_WORKERS=12
CHUNK_SIZE=1500
LOG_LEVEL=DEBUG
```

📖 **For complete configuration options, see [docs/DOCKER_SETUP_GUIDE.md](docs/DOCKER_SETUP_GUIDE.md)**

---

## 🚀 Production Deployment

For production deployments, consider:

### **Security**
- Change default passwords
- Use SSL/TLS certificates
- Configure firewall rules
- Enable authentication

### **Performance**
- Allocate sufficient resources
- Configure connection pooling
- Enable monitoring and logging
- Set up backup strategies

### **Scaling**
- Use docker-compose.production.yml
- Consider load balancers
- Implement caching layers
- Monitor resource usage

---

## 📚 Additional Resources

### **Documentation**
- [Docker Setup Guide](docs/DOCKER_SETUP_GUIDE.md) - Detailed Docker configuration
- [Cloud Setup Guide](docs/setup/CLOUD_SETUP_GUIDE.md) - Cloud deployment instructions
- [Migration Guide](docs/MIGRATION_GUIDE_CLOUD_TO_LOCAL.md) - Cloud to local migration
- [Environment Variables](docs/ENVIRONMENT_VARIABLES_REFERENCE.md) - Complete configuration reference

### **Troubleshooting**
- [GPU Issues](docs/troubleshooting/GPU_AUTO_DETECTION.md)
- [Ollama Problems](docs/troubleshooting/OLLAMA_GPU_FIX.md)
- [Performance Tuning](docs/PERFORMANCE_FEATURES.md)

---

## ✅ Verification Checklist

Before starting production processing, verify:

- [ ] Docker Desktop installed and running
- [ ] Repository cloned successfully
- [ ] Environment configured (.env file)
- [ ] All services started (`docker-compose up -d`)
- [ ] MinIO buckets initialized
- [ ] AI models downloaded
- [ ] Health checks passing
- [ ] Test suite running successfully

---

**🎉 Congratulations! Your KRAI system is now ready for production use!**

For questions or support, please refer to the GitHub repository or create an issue.
