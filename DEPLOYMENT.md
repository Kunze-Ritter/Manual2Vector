# KRAI Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU (optional, for Ollama acceleration)
- 8GB+ RAM (16GB+ recommended)
- 20GB+ free disk space

### One-Command Deployment
```bash
git clone <repository-url>
cd KRAI-minimal
docker-compose -f docker-compose.production.yml up -d --build
```

## 📋 Services Overview

| Service | Port | Description | Access |
|---------|------|-------------|--------|
| **Frontend Dashboard** | 3000 | React + Vite + Nginx (with API proxy) | http://localhost:3000 |
| **Backend API** | 8000 | FastAPI Python Backend | http://localhost:8000 |
| **API Documentation** | 8000/docs | Interactive API Docs | http://localhost:8000/docs |
| **PostgreSQL Database** | 5432 | pgvector-enabled Database | localhost:5432 |
| **MinIO Console** | 9001 | S3-compatible Object Storage | http://localhost:9001 |
| **MinIO API** | 9000 | Object Storage API | http://localhost:9000 |
| **Ollama AI Service** | 11434 | Large Language Models | localhost:11434 |

## 🔧 Configuration

### Backend Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
# Database (PostgreSQL)
DATABASE_TYPE=postgresql
DATABASE_CONNECTION_URL=postgresql://krai_user:krai_secure_password@krai-postgres:5432/krai

# Storage (MinIO)
OBJECT_STORAGE_TYPE=s3
OBJECT_STORAGE_ENDPOINT=http://krai-minio:9000
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=minioadmin

# AI Services (Ollama)
OLLAMA_URL=http://krai-ollama:11434

# Application
ENV=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

> **Note:** This deployment uses PostgreSQL + MinIO for local-first architecture. Legacy Supabase and Cloudflare R2 configurations are deprecated. See `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` for migration guidance.

### Frontend Configuration

**Production environment variables** are configured in `frontend/.env.production` and are **baked into the build** at compile time.

**Key settings:**
- `VITE_API_BASE_URL=/api` - Uses nginx proxy for API requests
- `VITE_ENABLE_DEVTOOLS=false` - DevTools disabled in production
- `VITE_USE_MOCK_AUTH=false` - Real authentication only

**Important:** Changing frontend environment variables requires rebuilding the Docker image:
```bash
docker-compose -f docker-compose.production.yml build krai-frontend
```

**For detailed frontend deployment information, see:**
- [Frontend Production Deployment Guide](docs/setup/FRONTEND_PRODUCTION_DEPLOYMENT.md)
- [Frontend README](frontend/README.md)

### Default Credentials
- **MinIO Console:** See `OBJECT_STORAGE_ACCESS_KEY` / `OBJECT_STORAGE_SECRET_KEY` in `.env`
- **PostgreSQL:** See `DATABASE_USER` / `DATABASE_PASSWORD` in `.env`
- **Database Name:** `krai` (configured via `DATABASE_NAME`)

> **Security:** Change all default credentials before production deployment. Use `./setup.sh` or `./setup.ps1` to generate secure passwords.

## 🏗️ Architecture

### Docker Compose Structure
```
docker-compose.production.yml
├── krai-frontend (React + Vite + Nginx)
│   ├── Build-time: Vite compiles with .env.production
│   ├── Runtime: Nginx serves static files + proxies /api
│   └── Port 80 → Container port 80
├── krai-engine (FastAPI + Uvicorn)
├── krai-postgres (PostgreSQL + pgvector)
├── krai-minio (Object Storage)
├── krai-ollama (AI Service)
├── krai-redis (Cache)
├── krai-playwright (Browser Automation)
├── krai-firecrawl-api (Web Scraping API)
└── krai-firecrawl-worker (Web Scraping Worker)
```

> **Note:** `docker-compose.production-final.yml` has been archived and replaced by `docker-compose.production.yml`. The new production file includes Firecrawl services and uses uvicorn instead of gunicorn.

### Network Configuration
- All services communicate via internal Docker network `krai-network`
- Only necessary ports exposed to host
- Health checks implemented for all services
- Automatic restart on failure

## 📊 Monitoring & Health

### Health Check Endpoints
- **Frontend:** http://localhost:3000/health
- **Backend:** http://localhost:8000/health
- **Database:** `pg_isready -U krai_user -d krai`
- **MinIO:** http://localhost:9000/minio/health/live
- **Ollama:** http://localhost:11434/api/tags

### Container Status
```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f [service-name]

# Restart specific service
docker-compose -f docker-compose.production.yml restart [service-name]
```

## 🔄 Data Persistence

### Volume Mapping
- **PostgreSQL Data:** `krai_postgres_data:/var/lib/postgresql/data`
- **MinIO Data:** `minio_data:/data`
- **Ollama Models:** `ollama_data:/root/.ollama`
- **Application Data:** `./data:/app/data`
- **Logs:** `./logs:/app/logs`

### Backups
```bash
# Database backup
docker exec krai-postgres-prod pg_dump -U krai_user krai > backup.sql

# MinIO backup
docker exec krai-minio-prod mc mirror /data ./minio-backup

# Ollama models backup
docker exec krai-ollama-prod cp -r /root/.ollama ./ollama-backup
```

## 🌐 External Access

### Domain Configuration
Update `nginx/nginx-simple.conf` for production domains:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    # ... rest of configuration
}
```

### SSL/TLS Setup
For HTTPS, modify nginx configuration and add certificates:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of configuration
}
```

## 🔒 Security Considerations

### Production Checklist
- [ ] Change default MinIO credentials
- [ ] Update PostgreSQL passwords
- [ ] Configure firewall rules
- [ ] Enable SSL/TLS
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Review environment variables

### Access Control
```bash
# Restrict external access to database
# Only expose frontend and API ports externally
# Use Docker networks for internal communication
```

## 🚀 Scaling & Performance

### Resource Allocation
```yaml
# In docker-compose.production.yml
services:
  krai-engine:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 1G
          cpus: '1'
```

### Horizontal Scaling
```bash
# Scale backend services
docker-compose -f docker-compose.production.yml up -d --scale krai-engine=3
```

## 🔨 Frontend Build Process

### Building the Frontend

The frontend uses a **multi-stage Docker build** that bakes environment variables into the static bundle:

```bash
# Build frontend only
docker-compose -f docker-compose.production.yml build krai-frontend

# Build with no cache (clean build)
docker-compose -f docker-compose.production.yml build --no-cache krai-frontend
```

**Build stages:**
1. **Builder stage:** Installs dependencies, copies `.env.production`, runs Vite build
2. **Production stage:** Copies built files to nginx, configures proxy

**When to rebuild:**
- After changing `frontend/.env.production`
- After updating frontend dependencies
- After modifying frontend source code
- After changing nginx configuration

**For detailed information, see:** [Frontend Production Deployment Guide](docs/setup/FRONTEND_PRODUCTION_DEPLOYMENT.md)

## 🐛 Troubleshooting

### Common Issues

#### Frontend Issues

**API requests fail with 404:**
```bash
# Check backend is running
docker-compose -f docker-compose.production.yml ps krai-engine

# Check nginx proxy configuration
docker-compose -f docker-compose.production.yml exec krai-frontend cat /etc/nginx/nginx.conf | grep -A 10 "location /api"
```

**Environment variables not working:**
```bash
# Verify .env.production exists
ls -la frontend/.env.production

# Rebuild frontend (REQUIRED after changing env vars)
docker-compose -f docker-compose.production.yml build --no-cache krai-frontend
docker-compose -f docker-compose.production.yml up -d krai-frontend
```

**DevTools appear in production:**
```bash
# Check VITE_ENABLE_DEVTOOLS is false
cat frontend/.env.production | grep VITE_ENABLE_DEVTOOLS

# Should show: VITE_ENABLE_DEVTOOLS=false
# If not, edit and rebuild
```

**React Router 404 on refresh:**
- Check nginx `try_files` directive in `nginx/nginx-simple.conf`
- Should have: `try_files $uri $uri/ /index.html;`

#### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Change ports in docker-compose.production.yml
```

#### Build Failures
```bash
# Clean rebuild
docker-compose -f docker-compose.production.yml down --volumes
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

#### Service Not Starting
```bash
# Check logs
docker logs krai-[service-name]-prod

# Check health status
docker-compose -f docker-compose.production.yml ps
```

#### Database Connection Issues
```bash
# Test database connection
docker exec krai-postgres-prod psql -U krai_user -d krai -c "SELECT version();"

# Check database logs
docker logs krai-postgres-prod
```

## 📱 Development vs Production

### Development Setup
```bash
# Use development compose file
docker-compose -f docker-compose.yml up -d

# Or run services locally
cd backend && python -m uvicorn main:app --reload
cd frontend && npm run dev
```

### Production Deployment
```bash
# Use production compose file (this guide)
docker-compose -f docker-compose.production.yml up -d --build
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build
```

### System Updates
```bash
# Update Docker images
docker-compose -f docker-compose.production.yml pull

# Restart with new images
docker-compose -f docker-compose.production.yml up -d
```

## 📞 Support

### Log Analysis
```bash
# Aggregate logs for debugging
docker-compose -f docker-compose.production.yml logs --tail=100

# Monitor specific service
docker-compose -f docker-compose.production.yml logs -f krai-engine
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Container health
docker-compose -f docker-compose.production.yml exec krai-engine curl -f http://localhost:8000/health
```

---

## 🎯 Success Criteria

✅ **Portable:** Single docker-compose file for deployment  
✅ **Complete:** All services included (Frontend, Backend, Database, Storage, AI)  
✅ **Production-Ready:** Health checks, restarts, logging, monitoring  
✅ **Scalable:** Resource limits and scaling capabilities  
✅ **Secure:** Internal networking, configurable credentials  
✅ **Documented:** Comprehensive setup and troubleshooting guide  

**Deployment Status:** ✅ PRODUCTION READY
