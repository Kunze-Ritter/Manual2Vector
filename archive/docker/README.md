# Archived Docker Compose Files

This directory contains Docker Compose files that have been archived as part of the KRAI project consolidation effort. The project has been simplified from 10 Docker Compose files to 3 production-ready configurations to reduce confusion and maintenance burden.

## Overview

The following files have been archived:
- `docker-compose.yml` - Legacy default with n8n, pgAdmin, Laravel
- `docker-compose.test.yml` - Test environment with isolated services  
- `docker-compose.production-final.yml` - Duplicate production configuration
- `docker-compose.production-complete.yml` - Production duplicate with Firecrawl
- `docker-compose.prod.yml` - Enterprise setup with advanced features
- `docker-compose.infrastructure.yml` - Infrastructure-only (no API/frontend)
- `docker-compose-ollama-tunnel.yml` - Cloudflare tunnel for Ollama

## Archived Files Details

| Filename | Purpose | Reason for Archival | Superseded By |
|----------|---------|---------------------|---------------|
| `docker-compose.yml` | Legacy default compose file with n8n, pgAdmin, Laravel | Contains services not part of core KRAI stack | `docker-compose.simple.yml` |
| `docker-compose.test.yml` | Test environment with isolated services | Valuable for testing but not primary deployment | Still available in archive |
| `docker-compose.production-final.yml` | Production configuration duplicate | Nearly identical to production.yml | `docker-compose.production.yml` |
| `docker-compose.production-complete.yml` | Production with Firecrawl duplicate | Redundant with better configuration | `docker-compose.production.yml` |
| `docker-compose.prod.yml` | Enterprise production setup | Too complex for current needs | `docker-compose.production.yml` |
| `docker-compose.infrastructure.yml` | Infrastructure-only services | Superseded by full stack setup | `docker-compose.simple.yml` |
| `docker-compose-ollama-tunnel.yml` | Cloudflare tunnel for Ollama | Specific deployment use case | Still available in archive |

### File Descriptions

#### docker-compose.yml
**Purpose**: Legacy default compose file  
**Contents**: n8n automation platform, pgAdmin database UI, Laravel admin panel, plus core KRAI services  
**Reason**: Contains additional services (n8n, pgAdmin, Laravel) that are not part of the core KRAI stack and add unnecessary complexity for most users.  
**Superseded by**: `docker-compose.simple.yml` which provides a cleaner minimal setup.

#### docker-compose.test.yml
**Purpose**: Comprehensive test environment  
**Contents**: Isolated test services (PostgreSQL on port 5433, MinIO on 9001, Redis on 6380, Ollama on 11435) with separate test credentials and Firecrawl testing profiles  
**Reason**: While valuable for testing, this is not a primary deployment configuration and can cause confusion.  
**Status**: Still available for reference when setting up test environments.

#### docker-compose.production-final.yml
**Purpose**: Production configuration  
**Contents**: Similar to production.yml but with frontend on port 3000, uses gunicorn instead of uvicorn, lacks Firecrawl services  
**Reason**: Nearly identical to the canonical production configuration with minor differences that don't justify maintaining a separate file.  
**Superseded by**: `docker-compose.production.yml`

#### docker-compose.production-complete.yml
**Purpose**: Production with Firecrawl services  
**Contents**: All production services plus Redis, Playwright (browserless/chrome), Firecrawl API/Worker  
**Reason**: Redundant with `docker-compose.production.yml` which has the same services with better configuration (uses ghcr.io/firecrawl/playwright-service instead of browserless/chrome).  
**Superseded by**: `docker-compose.production.yml`

#### docker-compose.prod.yml
**Purpose**: Enterprise production setup  
**Contents**: Advanced features including Docker Secrets for credentials, Nginx reverse proxy with SSL, Redis cache, Prometheus monitoring, Grafana dashboards  
**Reason**: These enterprise features add significant complexity and are not required for the current deployment model. Requires additional setup (secrets files, SSL certificates, monitoring configs).  
**Superseded by**: `docker-compose.production.yml` (simpler approach)

#### docker-compose.infrastructure.yml
**Purpose**: Infrastructure-only services  
**Contents**: PostgreSQL, MinIO, and Ollama services without KRAI Engine API or frontend  
**Reason**: Designed for running just the infrastructure layer, but this use case is now covered by `docker-compose.simple.yml` which includes the full stack.  
**Superseded by**: `docker-compose.simple.yml`

#### docker-compose-ollama-tunnel.yml
**Purpose**: Cloudflare tunnel for Ollama  
**Contents**: Single Cloudflare tunnel service exposing Ollama at llm.kunze-ritter.com (tunnel ID: d31cf264-168b-430b-9ffc-160aa6ffdf24)  
**Reason**: Very specific deployment use case that doesn't belong in the main compose file set.  
**Status**: Still available for users needing this specific functionality.

## Current Compose Files

The project now maintains 3 active Docker Compose files:

### docker-compose.simple.yml
**Use Case**: Minimal development setup  
**Services**: Frontend, Backend, PostgreSQL, MinIO, Ollama (5 services)  
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

## Migration Guide

If you were using an archived compose file, here's how to migrate:

### From docker-compose.yml
**Use**: `docker-compose.simple.yml`  
**Note**: You'll lose n8n, pgAdmin, and Laravel services. These were not part of the core KRAI stack.

### From docker-compose.production-final.yml
**Use**: `docker-compose.production.yml`  
**Note**: Frontend will be on port 80 instead of 3000, uses uvicorn instead of gunicorn, includes Firecrawl services.

### From docker-compose.production-complete.yml
**Use**: `docker-compose.production.yml`  
**Note**: Same functionality but uses better Firecrawl configuration (ghcr.io/firecrawl/playwright-service).

### From docker-compose.prod.yml
**Use**: `docker-compose.production.yml`  
**Note**: You'll lose enterprise features (Docker Secrets, Nginx, Prometheus, Grafana). These can be added separately if needed.

### From docker-compose.infrastructure.yml
**Use**: `docker-compose.simple.yml`  
**Note**: You'll get the full stack including API and frontend, not just infrastructure.

### From docker-compose.test.yml
**Use**: `docker-compose -f archive/docker/docker-compose.test.yml`  
**Note**: The test environment is still available but has been moved to the archive directory.

### From docker-compose-ollama-tunnel.yml
**Use**: `docker-compose -f archive/docker/docker-compose-ollama-tunnel.yml`  
**Note**: This specific use case is still available in the archive.

## Restoration Instructions

If you need to use an archived compose file:

1. Navigate to the archive directory:
   ```bash
   cd archive/docker
   ```

2. Use the archived compose file with the `-f` flag:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. Or copy it back to the root directory if you need it temporarily:
   ```bash
   cp archive/docker/docker-compose.yml .
   docker-compose up -d
   ```

## Testing Checklist

After consolidation, verify all 3 active compose files work correctly:

- [ ] `docker-compose -f docker-compose.simple.yml up -d` starts successfully
- [ ] `docker-compose -f docker-compose.with-firecrawl.yml up -d` starts successfully  
- [ ] `docker-compose -f docker-compose.production.yml up -d` starts successfully
- [ ] All services are healthy in each configuration
- [ ] Documentation references are updated correctly

## Benefits of Consolidation

1. **Reduced Confusion**: Clear choice between 3 well-defined configurations
2. **Easier Maintenance**: Fewer files to maintain and test
3. **Better Documentation**: Focused documentation on active configurations
4. **Cleaner Project Structure**: Less clutter in root directory
5. **Clear Migration Paths**: Obvious upgrade paths from archived files

## Questions?

If you have questions about the consolidation or need help migrating from an archived file, please refer to the main project documentation or create an issue in the project repository.
