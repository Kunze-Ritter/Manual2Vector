# Environment Variables Reference

## Overview

This document provides a comprehensive reference for all environment variables used in the KRAI system. Environment variables are used to configure services, enable/disable features, and manage deployment settings across different environments.

## Configuration Files

### Primary Configuration Files

- `.env` - Main application configuration
- `.env.database` - Database and connection settings
- `.env.ai` - AI service and model configuration
- `.env.storage` - Object storage and file handling
- `.env.auth` - Authentication and authorization
- `.env.external` - External service integrations
- `.env.pipeline` - Document processing pipeline settings

### Template Files

- `.env.example` - Main configuration template
- `.env.database.example` - Database configuration template
- `.env.ai.example` - AI service configuration template
- `.env.storage.example` - Storage configuration template
- `.env.auth.example` - Authentication configuration template
- `.env.external.example` - External services template
- `.env.pipeline.example` - Pipeline configuration template

## Core Application Configuration (.env)

### Application Settings

```bash
# Application Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Service Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
NGINX_PORT=80
NGINX_SSL_PORT=443

# Application URLs
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000/api

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization
```

### Phase 6 Advanced Features

```bash
# Hierarchical Chunking
ENABLE_HIERARCHICAL_CHUNKING=true
DETECT_ERROR_CODE_SECTIONS=true
LINK_CHUNKS=true
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
MIN_CHUNK_SIZE=30

# SVG Processing
ENABLE_SVG_EXTRACTION=true
SVG_CONVERSION_DPI=300
SVG_MAX_DIMENSION=2048
SVG_QUALITY=95
SVG_BACKGROUND_COLOR=white

# Multimodal Search
ENABLE_MULTIMODAL_SEARCH=true
MULTIMODAL_SEARCH_THRESHOLD=0.5
MULTIMODAL_SEARCH_LIMIT=10
ENABLE_TWO_STAGE_RETRIEVAL=true
SEARCH_RESULT_MAX_AGE=3600

# Context Extraction
ENABLE_CONTEXT_EXTRACTION=true
VISION_AI_MODEL=llava-phi3
CONTEXT_EMBEDDING_MODEL=nomic-embed-text
CONTEXT_EXTRACTION_BATCH_SIZE=5
MAX_CONTEXT_LENGTH=1000

# Feature Toggles
ENABLE_DOCUMENT_UPLOAD=true
ENABLE_BULK_PROCESSING=true
ENABLE_REAL_TIME_SEARCH=true
ENABLE_ADVANCED_FILTERING=true
ENABLE_EXPORT_FEATURES=true
```

### Performance Settings

```bash
# Processing Performance
MAX_CONCURRENT_UPLOADS=5
PROCESSING_TIMEOUT=300
EMBEDDING_BATCH_SIZE=10
VISION_AI_BATCH_SIZE=3

# Caching Settings
ENABLE_QUERY_CACHE=true
QUERY_CACHE_TTL=300
ENABLE_RESULT_CACHE=true
RESULT_CACHE_TTL=600

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
ENABLE_RATE_LIMITING=true
```

## Database Configuration (.env.database)

### PostgreSQL Settings

```bash
# Connection Settings
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=krai
POSTGRES_USER=krai_user
POSTGRES_PASSWORD=your_secure_password_here

# SSL Configuration
POSTGRES_SSL_MODE=prefer
POSTGRES_SSL_CERT=
POSTGRES_SSL_KEY=
POSTGRES_SSL_CA=

# Connection Pooling
DB_POOL_SIZE=20
DB_MAX_CONNECTIONS=50
DB_MIN_CONNECTIONS=5
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### pgvector Configuration

```bash
# Vector Database Settings
PGVECTOR_ENABLED=true
VECTOR_DIMENSION=768
VECTOR_INDEX_TYPE=ivfflat
VECTOR_INDEX_LISTS=100
VECTOR_DISTANCE_METRIC=cosine

# Vector Search Settings
VECTOR_SEARCH_THRESHOLD=0.5
VECTOR_SEARCH_LIMIT=10
ENABLE_VECTOR_INDEXING=true
```

### Database Performance

```bash
# Query Optimization
ENABLE_QUERY_OPTIMIZATION=true
STATEMENT_TIMEOUT=30000
IDLE_IN_TRANSACTION_SESSION_TIMEOUT=60000

# Maintenance Settings
AUTO_VACUUM_ENABLED=true
AUTO_ANALYZE_ENABLED=true
MAINTENANCE_WORK_MEM=256MB
EFFECTIVE_CACHE_SIZE=4GB
```

## AI Service Configuration (.env.ai)

### Ollama Settings

```bash
# Ollama Service
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_VISION_MODEL=llava-phi3

# Model Configuration
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_BATCH=512
OLLAMA_TEMPERATURE=0.7
OLLAMA_TOP_P=0.9
OLLAMA_TOP_K=40
```

### GPU Configuration

```bash
# CUDA Settings
CUDA_VISIBLE_DEVICES=0
OLLAMA_GPU_LAYERS=35
ENABLE_GPU_ACCELERATION=true
GPU_MEMORY_UTILIZATION=0.8

# Alternative GPU Settings
ROCR_VISIBLE_DEVICES=0  # AMD GPUs
OLLAMA_ROCM_LAYERS=35
```

### AI Service Performance

```bash
# Service Settings
AI_SERVICE_TIMEOUT=30
AI_SERVICE_RETRY_ATTEMPTS=3
AI_SERVICE_RETRY_DELAY=1
ENABLE_AI_SERVICE_CACHING=true

# Batch Processing
EMBEDDING_BATCH_SIZE=10
VISION_AI_BATCH_SIZE=3
TEXT_GENERATION_BATCH_SIZE=5
MAX_CONCURRENT_AI_REQUESTS=20
```

### Model Settings

```bash
# Embedding Models
DEFAULT_EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
EMBEDDING_NORMALIZE=true
EMBEDDING_TRUNCATE=true

# Language Models
DEFAULT_LLM_MODEL=llama3.1:8b
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.9

# Vision Models
DEFAULT_VISION_MODEL=llava-phi3
VISION_MAX_IMAGE_SIZE=2048
VISION_IMAGE_QUALITY=95
VISION_ENABLE_DETAIL=true
```

## Storage Configuration (.env.storage)

### MinIO Settings

```bash
# MinIO Service
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Bucket Configuration
MINIO_BUCKET_NAME=krai-storage
MINIO_DOCUMENTS_BUCKET=documents
MINIO_IMAGES_BUCKET=images
MINIO_VIDEOS_BUCKET=videos
MINIO_TEMP_BUCKET=temp
```

### Object Storage Settings

```bash
# Storage Connection
STORAGE_ENDPOINT=http://minio:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin123
STORAGE_SECURE=false
STORAGE_REGION=us-east-1

# Storage Settings
STORAGE_MAX_FILE_SIZE=100MB
STORAGE_ALLOWED_EXTENSIONS=pdf,doc,docx,txt,md,jpg,jpeg,png,gif,svg
STORAGE_AUTO_DELETE_TEMP=true
TEMP_FILE_TTL=3600
```

### File Processing

```bash
# File Upload Settings
MAX_UPLOAD_SIZE=100MB
MULTIPART_UPLOAD_THRESHOLD=50MB
CHUNK_SIZE=8MB
ENABLE_FILE_DEDUPLICATION=true

# Image Processing
IMAGE_MAX_WIDTH=2048
IMAGE_MAX_HEIGHT=2048
IMAGE_QUALITY=85
IMAGE_FORMAT=jpeg
ENABLE_IMAGE_OPTIMIZATION=true

# Video Processing
VIDEO_MAX_DURATION=3600
VIDEO_THUMBNAIL_INTERVAL=10
ENABLE_VIDEO_TRANSCRIPTION=true
```

### CDN Configuration (Optional)

```bash
# CDN Settings
ENABLE_CDN=false
CDN_ENDPOINT=https://cdn.example.com
CDN_ACCESS_KEY=your_cdn_access_key
CDN_SECRET_KEY=your_cdn_secret_key
CDN_BUCKET=krai-cdn
```

## Authentication Configuration (.env.auth)

### JWT Settings

```bash
# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Token Settings
ENABLE_JWT_REFRESH=true
JWT_ISSUER=krai-system
JWT_AUDIENCE=krai-users
```

### OAuth2 Settings

```bash
# OAuth2 Configuration
ENABLE_OAUTH2=false
OAUTH2_GOOGLE_CLIENT_ID=your_google_client_id
OAUTH2_GOOGLE_CLIENT_SECRET=your_google_client_secret
OAUTH2_MICROSOFT_CLIENT_ID=your_microsoft_client_id
OAUTH2_MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
```

### Security Settings

```bash
# Security Configuration
BCRYPT_ROUNDS=12
ENABLE_PASSWORD_STRENGTH_CHECK=true
MIN_PASSWORD_LENGTH=8
ENABLE_ACCOUNT_LOCKOUT=true
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=900

# Session Settings
SESSION_TIMEOUT=3600
ENABLE_SESSION_REFRESH=true
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

## External Services Configuration (.env.external)

### Email Configuration

```bash
# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Email Settings
EMAIL_FROM=noreply@krai-system.com
EMAIL_FROM_NAME=KRAI System
ENABLE_EMAIL_NOTIFICATIONS=true
```

### Webhook Configuration

```bash
# Webhook Settings
ENABLE_WEBHOOKS=false
WEBHOOK_SECRET=your_webhook_secret
WEBHOOK_TIMEOUT=10
WEBHOOK_RETRY_ATTEMPTS=3

# Webhook Events
WEBHOOK_ON_DOCUMENT_UPLOAD=true
WEBHOOK_ON_PROCESSING_COMPLETE=true
WEBHOOK_ON_ERROR=true
```

### External AI Services (Optional)

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
ENABLE_OPENAI_FALLBACK=false

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ENABLE_ANTHROPIC_FALLBACK=false
```

## Pipeline Configuration (.env.pipeline)

### Processing Pipeline

```bash
# Pipeline Settings
ENABLE_PROCESSING_PIPELINE=true
PIPELINE_WORKER_COUNT=4
PIPELINE_QUEUE_SIZE=100
PIPELINE_RETRY_ATTEMPTS=3
PIPELINE_RETRY_DELAY=5

# Processing Stages
ENABLE_TEXT_EXTRACTION=true
ENABLE_SVG_PROCESSING=true
ENABLE_TABLE_EXTRACTION=true
ENABLE_CONTEXT_EXTRACTION=true
ENABLE_EMBEDDING_GENERATION=true
ENABLE_SEARCH_INDEXING=true
```

### OCR Configuration

```bash
# OCR Settings
ENABLE_OCR=true
OCR_ENGINE=tesseract
OCR_LANGUAGES=eng,deu
OCR_CONFIDENCE_THRESHOLD=60
ENABLE_OCR_CORRECTION=true

# Tesseract Configuration
TESSERACT_PATH=/usr/bin/tesseract
TESSERACT_DATA_PATH=/usr/share/tesseract-ocr/4.00/tessdata
```

### Quality Control

```bash
# Quality Settings
ENABLE_QUALITY_CHECK=true
MIN_TEXT_QUALITY_SCORE=0.7
MIN_IMAGE_QUALITY_SCORE=0.6
ENABLE_CONTENT_VALIDATION=true
VALIDATION_STRICT_MODE=false

# Error Handling
ENABLE_ERROR_RECOVERY=true
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_BASE=2
RETRY_DELAY_MAX=60
```

## Development Configuration

### Debug Settings

```bash
# Debug Configuration
DEBUG=true
VERBOSE_LOGGING=true
ENABLE_SQL_DEBUG=false
ENABLE_REQUEST_LOGGING=true
ENABLE_PERFORMANCE_LOGGING=true

# Development Tools
ENABLE_PROFILING=false
ENABLE_DEBUG_TOOLBAR=true
ENABLE_SWAGGER_UI=true
ENABLE_REDOC=true
```

### Testing Configuration

```bash
# Test Settings
TESTING=false
TEST_DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/krai_test
ENABLE_TEST_MOCKS=true
TEST_DATA_CLEANUP=true

# Coverage Settings
ENABLE_COVERAGE=true
COVERAGE_THRESHOLD=80
COVERAGE_REPORT_FORMAT=html
```

## Production Configuration

### Security Settings

```bash
# Production Security
DEBUG=false
ENABLE_SECURITY_HEADERS=true
ENABLE_CONTENT_SECURITY_POLICY=true
ENABLE_FRAME_PROTECTION=true
ENABLE_XSS_PROTECTION=true

# SSL/TLS Settings
FORCE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/krai.crt
SSL_KEY_PATH=/etc/ssl/private/krai.key
SSL_PROTOCOLS=TLSv1.2,TLSv1.3
```

### Performance Settings

```bash
# Production Performance
ENABLE_GZIP=true
COMPRESSION_LEVEL=6
ENABLE_BROTLI=true
BROTLI_COMPRESSION_LEVEL=4

# Caching
ENABLE_REDIS_CACHE=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
CACHE_DEFAULT_TIMEOUT=300
```

### Monitoring Settings

```bash
# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_PATH=/metrics
ENABLE_HEALTH_CHECKS=true
HEALTH_CHECK_PATH=/health

# Logging
LOG_FORMAT=json
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true
LOG_FILE_PATH=/var/log/krai/app.log
```

## Feature Flags

### Experimental Features

```bash
# Experimental Features
ENABLE_EXPERIMENTAL_FEATURES=false
ENABLE_ADVANCED_AI_FEATURES=false
ENABLE_BETA_MODELS=false
ENABLE_NEW_SEARCH_ALGORITHM=false

# Development Features
ENABLE_HOT_RELOAD=false
ENABLE_DEBUG_ENDPOINTS=false
ENABLE_ADMIN_PANEL=false
```

### Optional Integrations

```bash
# Optional Integrations
ENABLE_SLACK_INTEGRATION=false
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL=#krai-notifications

ENABLE_TEAMS_INTEGRATION=false
TEAMS_WEBHOOK_URL=your_teams_webhook_url

ENABLE_JIRA_INTEGRATION=false
JIRA_API_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_jira_username
JIRA_API_TOKEN=your_jira_api_token
```

## Environment-Specific Variables

### Development Environment

```bash
# Development (.env.development)
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_RELOAD=true
ENABLE_MOCK_SERVICES=true
```

### Staging Environment

```bash
# Staging (.env.staging)
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_STAGING_FEATURES=true
```

### Production Environment

```bash
# Production (.env.production)
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_SECURITY_MONITORING=true
ENABLE_AUDIT_LOGGING=true
```

## Variable Validation

### Required Variables

The following variables are required for basic operation:

```bash
# Database
POSTGRES_HOST
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

# Storage
STORAGE_ENDPOINT
STORAGE_ACCESS_KEY
STORAGE_SECRET_KEY

# AI Service
OLLAMA_HOST
OLLAMA_MODEL

# Authentication
JWT_SECRET_KEY
```

### Optional Variables

These variables have sensible defaults but can be customized:

```bash
# Performance
DB_POOL_SIZE=20
EMBEDDING_BATCH_SIZE=10
MAX_CONCURRENT_UPLOADS=5

# Features
ENABLE_HIERARCHICAL_CHUNKING=true
ENABLE_SVG_EXTRACTION=true
ENABLE_MULTIMODAL_SEARCH=true

# Security
BCRYPT_ROUNDS=12
SESSION_TIMEOUT=3600
```

## Configuration Management

### Variable Precedence

1. Environment variables (highest priority)
2. `.env` files
3. Default values in code
4. Configuration templates (lowest priority)

### Loading Order

1. `.env` - Base configuration
2. `.env.{ENVIRONMENT}` - Environment-specific overrides
3. System environment variables - Runtime overrides

### Validation

```bash
# Validate configuration
python scripts/validate_config.py

# Check required variables
python scripts/check_required_vars.py

# Test database connectivity
python scripts/test_db_connection.py

# Test AI service connectivity
python scripts/test_ai_service.py
```

## Best Practices

### Security

1. **Never commit secrets**: Use `.env.example` templates only
2. **Use strong passwords**: Generate cryptographically secure passwords
3. **Rotate secrets regularly**: Update JWT keys and API keys periodically
4. **Use environment-specific configs**: Separate development and production settings

### Performance

1. **Tune connection pools**: Adjust based on expected load
2. **Optimize batch sizes**: Balance memory usage and throughput
3. **Enable caching**: Use Redis for frequently accessed data
4. **Monitor resource usage**: Adjust settings based on metrics

### Maintenance

1. **Document changes**: Update this reference when adding variables
2. **Use semantic naming**: Choose descriptive variable names
3. **Group related settings**: Organize variables by service/feature
4. **Provide defaults**: Ensure reasonable default values

## Troubleshooting

### Common Issues

1. **Missing variables**: Check `.env.example` for required settings
2. **Invalid values**: Validate variable formats and ranges
3. **Permission issues**: Check file permissions for configuration files
4. **Service connectivity**: Verify network settings and endpoints

### Debug Commands

```bash
# Check loaded environment variables
env | grep KRAI_

# Validate configuration files
docker-compose config

# Test service connectivity
docker-compose exec postgres env
docker-compose exec ollama env
```

---

## Conclusion

This reference provides comprehensive documentation for all environment variables used in the KRAI system. Proper configuration is essential for optimal performance, security, and functionality.

For specific use cases or advanced configurations, refer to the respective service documentation or contact the development team.
