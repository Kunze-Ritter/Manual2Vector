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
docker-compose -f docker-compose.production-final.yml up -d --build
```

## 📋 Services Overview

| Service | Port | Description | Access |
|---------|------|-------------|--------|
| **Frontend Dashboard** | 3000 | React-based KRAI Dashboard | http://localhost:3000 |
| **Backend API** | 8000 | FastAPI Python Backend | http://localhost:8000 |
| **API Documentation** | 8000/docs | Interactive API Docs | http://localhost:8000/docs |
| **PostgreSQL Database** | 5432 | pgvector-enabled Database | localhost:5432 |
| **MinIO Console** | 9001 | S3-compatible Object Storage | http://localhost:9001 |
| **MinIO API** | 9000 | Object Storage API | http://localhost:9000 |
| **Ollama AI Service** | 11434 | Large Language Models | localhost:11434 |

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
# Database
DATABASE_URL=postgresql://krai_user:krai_secure_password@krai-postgres:5432/krai

# Storage
MINIO_ENDPOINT=krai-minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# AI Services
OLLAMA_BASE_URL=http://krai-ollama:11434

# Application
ENV=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Default Credentials
- **MinIO Console:** minioadmin / minioadmin
- **PostgreSQL:** krai_user / krai_secure_password
- **Database:** krai

## 🏗️ Architecture

### Docker Compose Structure
```
docker-compose.production-final.yml
├── krai-frontend (React + Nginx)
├── krai-engine (FastAPI + Gunicorn)
├── krai-postgres (PostgreSQL + pgvector)
├── krai-minio (Object Storage)
└── krai-ollama (AI Service)
```

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
docker-compose -f docker-compose.production-final.yml ps

# View logs
docker-compose -f docker-compose.production-final.yml logs -f [service-name]

# Restart specific service
docker-compose -f docker-compose.production-final.yml restart [service-name]
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
# In docker-compose.production-final.yml
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
docker-compose -f docker-compose.production-final.yml up -d --scale krai-engine=3
```

## 🐛 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Change ports in docker-compose.production-final.yml
```

#### Build Failures
```bash
# Clean rebuild
docker-compose -f docker-compose.production-final.yml down --volumes
docker-compose -f docker-compose.production-final.yml build --no-cache
docker-compose -f docker-compose.production-final.yml up -d
```

#### Service Not Starting
```bash
# Check logs
docker logs krai-[service-name]-prod

# Check health status
docker-compose -f docker-compose.production-final.yml ps
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
docker-compose -f docker-compose.production-final.yml up -d --build
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.production-final.yml down
docker-compose -f docker-compose.production-final.yml up -d --build
```

### System Updates
```bash
# Update Docker images
docker-compose -f docker-compose.production-final.yml pull

# Restart with new images
docker-compose -f docker-compose.production-final.yml up -d
```

## 📞 Support

### Log Analysis
```bash
# Aggregate logs for debugging
docker-compose -f docker-compose.production-final.yml logs --tail=100

# Monitor specific service
docker-compose -f docker-compose.production-final.yml logs -f krai-engine
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Container health
docker-compose -f docker-compose.production-final.yml exec krai-engine curl -f http://localhost:8000/health
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
