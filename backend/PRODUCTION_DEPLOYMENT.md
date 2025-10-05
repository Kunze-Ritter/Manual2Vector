# 🚀 Production Deployment Guide

## ✅ **Pre-Deployment Checklist**

### **1. Environment Variables**
```bash
# .env.production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Cloudflare R2 (Image Storage)
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
R2_PUBLIC_URL_DOCUMENTS=https://your-r2-bucket.domain.com

# Ollama (AI Models)
OLLAMA_URL=http://localhost:11434
# Or: http://your-ollama-server:11434

# YouTube API (Optional, for video enrichment)
YOUTUBE_API_KEY=your_youtube_api_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
LOG_LEVEL=INFO
```

### **2. Database Migrations**
✅ **Run ALL migrations 01-34 in Supabase:**
```sql
-- In Supabase SQL Editor, run migrations in order:
-- 01_schema_and_tables.sql
-- 02_security_rls_triggers.sql
-- ...
-- 30_grant_service_role_permissions.sql
-- 31_create_public_views_for_api_access.sql
-- 32_fix_links_video_id_foreign_key.sql
-- 33_add_video_dedup_indexes.sql
-- 34_fix_videos_view_triggers_add_missing_fields.sql
```

### **3. Required Services**

**Supabase (Database + Auth):**
- ✅ PostgreSQL 15+
- ✅ pgvector extension enabled
- ✅ Row Level Security (RLS) configured
- ✅ Service role permissions granted

**Cloudflare R2 (Object Storage):**
- ✅ Bucket created
- ✅ Access keys generated
- ✅ Public access configured (for images)

**Ollama (AI Models):**
- ✅ Ollama server running
- ✅ Models pulled:
  - `qwen2.5:7b` (LLM for extraction)
  - `llava:13b` (Vision AI)
  - `embeddinggemma` (Embeddings, 768-dim)

---

## 🏗️ **Deployment Steps**

### **Option A: Docker Deployment (Recommended)**

```bash
# 1. Build Docker image
docker build -t krai-engine:latest -f backend/Dockerfile .

# 2. Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# 3. Check logs
docker-compose logs -f krai-engine
```

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  krai-engine:
    image: krai-engine:latest
    container_name: krai-engine-prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - krai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: krai-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - krai-engine
    networks:
      - krai-network

networks:
  krai-network:
    driver: bridge
```

---

### **Option B: Direct Python Deployment**

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Run with gunicorn (production WSGI)
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

---

## 🔒 **Security Configuration**

### **1. HTTPS/SSL**
```nginx
# nginx/nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://krai-engine:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### **2. API Rate Limiting**
Add to `backend/main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/content/videos/enrich")
@limiter.limit("10/minute")
async def enrich_videos(...):
    ...
```

---

## 📊 **Monitoring & Logging**

### **1. Health Checks**
```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "storage": {"status": "healthy"},
    "ai": {"status": "healthy"}
  }
}
```

### **2. Logging Configuration**
```python
# backend/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

# Production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=10),
        logging.StreamHandler()
    ]
)
```

### **3. Monitoring Tools**

**Prometheus Metrics:**
```python
# Install: pip install prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
# Metrics at: /metrics
```

**Sentry Error Tracking:**
```python
# Install: pip install sentry-sdk
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production"
)
```

---

## 🧪 **Post-Deployment Testing**

### **1. API Endpoints**
```bash
# Test document upload
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.pdf"

# Test video enrichment
curl -X POST http://localhost:8000/content/videos/enrich/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# Test link checking
curl -X POST http://localhost:8000/content/links/check/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "check_only": true}'
```

### **2. Pipeline End-to-End Test**
```python
# Run: python backend/processors_v2/test_pipeline_live.py
# Uploads PDF → Processes → Embeddings → Search
```

---

## 🔄 **Backup & Recovery**

### **Database Backups (Supabase)**
- Automatic daily backups (Supabase Pro)
- Point-in-time recovery
- Export: Settings → Database → Backup

### **R2 Storage Backups**
```bash
# Sync R2 to local backup
rclone sync r2:your-bucket /backup/r2
```

---

## 📈 **Performance Optimization**

### **1. Database Indexes**
✅ Already created in migrations:
- Video deduplication indexes (Migration 33)
- Link indexes
- Embedding vector indexes (pgvector)

### **2. Caching**
```python
# Install: pip install fastapi-cache2
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="krai-cache:")
```

### **3. Connection Pooling**
Already configured in Supabase client (default pool size: 10)

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. Ollama Connection Failed**
```bash
# Check Ollama is running
curl http://localhost:11434/api/version

# Pull required models
ollama pull qwen2.5:7b
ollama pull llava:13b
ollama pull embeddinggemma
```

**2. Database Connection Failed**
- Check `SUPABASE_URL` and keys in `.env.production`
- Verify IP whitelist in Supabase settings
- Check RLS policies allow service_role access

**3. R2 Upload Failed**
- Verify R2 credentials
- Check bucket permissions
- Test with: `scripts/test_r2_connection.py`

---

## ✅ **Production Checklist**

- [ ] All migrations applied (01-34)
- [ ] Environment variables configured
- [ ] Supabase service_role permissions granted
- [ ] R2 bucket created and accessible
- [ ] Ollama models pulled and running
- [ ] HTTPS/SSL configured
- [ ] Rate limiting enabled
- [ ] Monitoring/logging configured
- [ ] Health checks passing
- [ ] Backup strategy implemented
- [ ] End-to-end tests passing

---

## 🎉 **Launch!**

```bash
# Final check
curl http://localhost:8000/health

# Start production
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f

# Check status
curl https://your-domain.com/info
```

**Your KRAI Engine is now LIVE!** 🚀🎊

---

## 📞 **Support**

- **Documentation:** `/docs` (Swagger UI)
- **Logs:** `logs/app.log`
- **Health:** `/health`
- **Metrics:** `/metrics` (if Prometheus enabled)
