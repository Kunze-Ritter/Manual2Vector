# KRAI Frontend - Production Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Environment Configuration](#environment-configuration)
3. [Build Process](#build-process)
4. [Docker Deployment](#docker-deployment)
5. [Nginx Configuration](#nginx-configuration)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)
9. [Performance Optimization](#performance-optimization)
10. [Maintenance](#maintenance)

---

## Overview

### Architecture

The KRAI frontend is built with:
- **React 19** - UI framework
- **Vite 7** - Build tool and dev server
- **Nginx (Alpine)** - Production web server
- **Docker** - Containerization

### Environment Variables: Build-Time vs Runtime

**Critical Concept:** Vite environment variables work differently from traditional server-side applications.

```
┌─────────────────────────────────────────────────────────────┐
│ BUILD TIME (Docker build)                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Read .env.production                                 │ │
│ │ 2. Vite replaces import.meta.env.VITE_* in source code │ │
│ │ 3. Output: Static JS bundle with hardcoded values      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ RUNTIME (Browser)                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ - Environment variables already in the code             │ │
│ │ - No .env files needed                                  │ │
│ │ - Changing values requires rebuilding Docker image      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Important:** Changing environment variables requires rebuilding the Docker image!

### Nginx Proxy Setup

The production deployment uses nginx to:
1. Serve static frontend files
2. Proxy `/api/*` requests to the backend
3. Handle React Router (SPA routing)
4. Provide security headers and gzip compression

```
Browser → Nginx (port 3000) → Frontend static files
                            → /api/* → Backend (krai-engine:8000)
```

See: `nginx/nginx-simple.conf`

---

## Environment Configuration

### Production Environment File

**File:** `frontend/.env.production`

This file contains production-specific environment variables that are **baked into the build** at compile time.

### Configuration Variables

| Variable | Production Value | Purpose |
|----------|-----------------|---------|
| `VITE_API_BASE_URL` | `/api` | Relative path for API requests (uses nginx proxy) |
| `VITE_API_TIMEOUT` | `30000` | API request timeout in milliseconds (30 seconds) |
| `VITE_TOKEN_STORAGE_KEY` | `krai_auth_token` | LocalStorage key for auth token |
| `VITE_REFRESH_TOKEN_STORAGE_KEY` | `krai_refresh_token` | LocalStorage key for refresh token |
| `VITE_ENABLE_DEVTOOLS` | `false` | Disable React Query DevTools in production |
| `VITE_USE_MOCK_AUTH` | `false` | Use real authentication (not mock) |

### Development vs Production Comparison

| Setting | Development | Production | Reason |
|---------|-------------|------------|--------|
| API Base URL | `/api` or `http://localhost:8000` | `/api` | Use nginx proxy in production |
| DevTools | `true` | `false` | Performance and security |
| Mock Auth | `false` | `false` | Real auth in both environments |
| Source Maps | `true` | `true` or `'hidden'` | Error tracking vs bundle size |

### Why `/api` for API Base URL?

**Development:** Vite dev server proxies `/api` → `http://localhost:8000` (configured in `vite.config.ts`)

**Production:** Nginx proxies `/api` → `http://krai-engine:8000` (configured in `nginx/nginx-simple.conf`)

This allows the same relative path to work in both environments without code changes.

### Modifying Environment Variables

**To change production environment variables:**

1. Edit `frontend/.env.production`
2. Rebuild the Docker image:
   ```bash
   docker-compose -f docker-compose.production.yml build krai-frontend
   ```
3. Restart the container:
   ```bash
   docker-compose -f docker-compose.production.yml up -d krai-frontend
   ```

> **Note:** `docker-compose.production-final.yml` has been consolidated into `docker-compose.production.yml`. The new production file includes Firecrawl services and uses uvicorn instead of gunicorn.

---

## Build Process

### Local Production Build

Test the production build locally before deploying:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already installed)
npm ci

# Build for production
npm run build:production

# Preview the production build
npm run preview:production
```

The preview server will start on `http://localhost:3000`.

### Build Scripts

Defined in `frontend/package.json`:

| Script | Command | Purpose |
|--------|---------|---------|
| `build` | `tsc -b && vite build` | General build (development mode) |
| `build:production` | `cross-env NODE_ENV=production vite build` | Production build (uses `.env.production`, cross-platform) |
| `build:production:verbose` | `cross-env NODE_ENV=production vite build --mode production` | Production build with verbose output |
| `preview:production` | `vite preview --port 3000` | Preview production build locally |

### Build Output

The build process creates:
- `dist/` directory with static files
- Optimized and minified JavaScript bundles
- Code-split vendor chunks for better caching
- CSS files with production optimizations

**Build Optimizations:**
- Minification with esbuild (faster than terser)
- CSS code splitting
- Vendor chunk separation (react, ui libraries, query libraries)
- Tree shaking to remove unused code

### Troubleshooting Build Issues

**Problem:** Build fails with "Cannot find module"
```bash
# Solution: Clean install dependencies
rm -rf node_modules package-lock.json
npm ci
```

**Problem:** Environment variables not working
```bash
# Solution: Ensure .env.production exists and variables are prefixed with VITE_
ls -la frontend/.env.production
cat frontend/.env.production | grep VITE_
```

**Problem:** Build succeeds but app doesn't work
```bash
# Solution: Test locally with preview
npm run build:production
npm run preview:production
# Open browser and check console for errors
```

---

## Docker Deployment

### Dockerfile Overview

**File:** `frontend/Dockerfile`

The Dockerfile uses a multi-stage build:

**Stage 1: Builder**
- Base: `node:20-alpine`
- Installs dependencies
- Copies `.env.production`
- Builds the application with `NODE_ENV=production`

**Stage 2: Production**
- Base: `nginx:alpine`
- Copies built files from builder stage
- Copies nginx configuration
- Serves the application

### Building the Docker Image

**Build frontend only:**
```bash
docker-compose -f docker-compose.production.yml build krai-frontend
```

**Build with no cache (clean build):**
```bash
docker-compose -f docker-compose.production.yml build --no-cache krai-frontend
```

**Build all services:**
```bash
docker-compose -f docker-compose.production.yml build
```

### Running the Container

**Start frontend only:**
```bash
docker-compose -f docker-compose.production.yml up -d krai-frontend
```

**Start full stack:**
```bash
docker-compose -f docker-compose.production.yml up -d
```

**View logs:**
```bash
docker-compose -f docker-compose.production.yml logs -f krai-frontend
```

**Stop container:**
```bash
docker-compose -f docker-compose.production.yml stop krai-frontend
```

### Docker Compose Configuration

**File:** `docker-compose.production.yml`

```yaml
krai-frontend:
  build:
    context: .
    dockerfile: frontend/Dockerfile
  ports:
    - "3000:80"
  depends_on:
    - krai-engine
  restart: unless-stopped
```

**Key Points:**
- Exposes port 3000 (maps to container port 80)
- Depends on `krai-engine` backend service
- Auto-restarts unless explicitly stopped
- No environment variables passed (they're baked into the build)

### Health Checks

The Dockerfile includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
```

**Check container health:**
```bash
docker-compose -f docker-compose.production.yml ps
```

Look for "healthy" status in the output.

---

## Nginx Configuration

### Configuration File

**File:** `nginx/nginx-simple.conf`

This configuration is copied into the Docker container at `/etc/nginx/nginx.conf`.

### Key Configuration Sections

#### 1. API Proxy

```nginx
location /api/ {
    proxy_pass http://krai-engine:8000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**What it does:**
- Forwards `/api/*` requests to backend at `http://krai-engine:8000/`
- Strips `/api` prefix (note the trailing slash in `proxy_pass`)
- Preserves client IP and protocol information
- Supports WebSocket upgrades

**Example:**
- Browser requests: `http://localhost:3000/api/documents`
- Nginx forwards to: `http://krai-engine:8000/documents`

#### 2. Static File Serving

```nginx
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
}
```

**What it does:**
- Serves static files from `/usr/share/nginx/html` (where Vite build output is copied)
- Falls back to `index.html` for React Router (SPA routing)
- Enables client-side routing to work correctly

#### 3. Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

**What it does:**
- Prevents clickjacking attacks
- Prevents MIME type sniffing
- Enables XSS protection

#### 4. Gzip Compression

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript 
           application/x-javascript application/xml+rss 
           application/javascript application/json;
```

**What it does:**
- Compresses responses to reduce bandwidth
- Only compresses files larger than 1KB
- Compresses text-based files (HTML, CSS, JS, JSON)

### Testing Nginx Configuration

**Test configuration syntax:**
```bash
docker-compose -f docker-compose.production.yml exec krai-frontend nginx -t
```

**Reload configuration (without restart):**
```bash
docker-compose -f docker-compose.production.yml exec krai-frontend nginx -s reload
```

### Customizing Nginx Configuration

**To modify nginx configuration:**

1. Edit `nginx/nginx-simple.conf`
2. Rebuild the frontend image:
   ```bash
   docker-compose -f docker-compose.production.yml build krai-frontend
   ```
3. Restart the container:
   ```bash
   docker-compose -f docker-compose.production.yml up -d krai-frontend
   ```

---

## Testing & Validation

### Pre-Deployment Checklist

- [ ] `.env.production` file exists and has correct values
- [ ] `VITE_ENABLE_DEVTOOLS=false` in `.env.production`
- [ ] `VITE_USE_MOCK_AUTH=false` in `.env.production`
- [ ] Local production build succeeds (`npm run build:production`)
- [ ] Local preview works (`npm run preview:production`)
- [ ] Docker image builds successfully
- [ ] Container starts and passes health check

### Post-Deployment Validation

#### 1. Container Health

```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Check logs for errors
docker-compose -f docker-compose.production.yml logs krai-frontend
```

**Expected:** Container status is "healthy", no errors in logs.

#### 2. Frontend Accessibility

```bash
# Test frontend loads
curl -I http://localhost:3000

# Should return: HTTP/1.1 200 OK
```

**Browser test:** Open `http://localhost:3000` - should load the KRAI dashboard.

#### 3. API Connectivity

**Test API proxy:**
```bash
# Test API endpoint through nginx
curl http://localhost:3000/api/health

# Should return backend health check response
```

**Browser test:** Open browser DevTools → Network tab → Trigger an API call → Check:
- Request URL starts with `/api/`
- Response is successful (200 OK)
- No CORS errors

#### 4. DevTools Disabled

**Browser test:**
1. Open `http://localhost:3000`
2. Open browser DevTools (F12)
3. Look for React Query DevTools button (should NOT be visible)

**Expected:** No DevTools button in production.

#### 5. Authentication Flow

**Test login:**
1. Navigate to login page
2. Enter credentials
3. Submit form
4. Check browser DevTools → Application → Local Storage
5. Verify `krai_auth_token` and `krai_refresh_token` are stored

**Expected:** Tokens are stored with correct keys from `.env.production`.

#### 6. React Router

**Test client-side routing:**
1. Navigate to `http://localhost:3000/documents`
2. Refresh the page (F5)

**Expected:** Page loads correctly (not 404), nginx serves `index.html` for all routes.

### Performance Testing

**Lighthouse audit:**
1. Open Chrome DevTools
2. Go to Lighthouse tab
3. Run audit for Production mode
4. Check scores for Performance, Accessibility, Best Practices, SEO

**Expected scores:**
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 80

**Bundle size check:**
```bash
# After build, check dist folder size
du -sh frontend/dist

# For more verbose build output (cross-platform)
npm run build:production:verbose
```

**Expected:** < 5MB total (with gzip compression, served size will be much smaller).

**Note:** The `build:production:verbose` script provides more detailed build output but does not include bundle analysis tooling. To implement real bundle analysis, consider adding a plugin like `rollup-plugin-visualizer` or `vite-bundle-visualizer`.

---

## Troubleshooting

### Common Issues

#### Issue 1: API Requests Fail with 404

**Symptoms:**
- Browser console shows 404 errors for `/api/*` requests
- Network tab shows requests to `/api/...` returning 404

**Possible Causes:**
1. Backend is not running
2. Nginx proxy configuration is incorrect
3. `VITE_API_BASE_URL` is not set to `/api`

**Solutions:**

```bash
# Check backend is running
docker-compose -f docker-compose.production.yml ps krai-engine

# Check nginx configuration
docker-compose -f docker-compose.production.yml exec krai-frontend cat /etc/nginx/nginx.conf | grep -A 10 "location /api"

# Verify environment variable in build
docker-compose -f docker-compose.production.yml exec krai-frontend cat /usr/share/nginx/html/index.html | grep -o 'VITE_API_BASE_URL'
# Note: Won't find the variable name, but will show if build used correct value
```

#### Issue 2: CORS Errors

**Symptoms:**
- Browser console shows CORS policy errors
- Requests are blocked by CORS

**Possible Causes:**
1. Backend CORS configuration doesn't allow frontend origin
2. Nginx proxy headers not set correctly

**Solutions:**

```bash
# Check nginx proxy headers
docker-compose -f docker-compose.production.yml exec krai-frontend cat /etc/nginx/nginx.conf | grep proxy_set_header

# Check backend CORS configuration
# Backend should allow origin: http://localhost:3000
```

#### Issue 3: React Router 404 on Refresh

**Symptoms:**
- Direct navigation to `/documents` works
- Refreshing the page shows nginx 404 error

**Possible Causes:**
- Nginx `try_files` directive is missing or incorrect

**Solutions:**

```bash
# Check nginx configuration for try_files
docker-compose -f docker-compose.production.yml exec krai-frontend cat /etc/nginx/nginx.conf | grep try_files

# Should see: try_files $uri $uri/ /index.html;
```

If missing, update `nginx/nginx-simple.conf` and rebuild.

#### Issue 4: Environment Variables Not Working

**Symptoms:**
- App uses wrong API URL
- DevTools appear in production
- Mock auth is used instead of real auth

**Possible Causes:**
1. `.env.production` file is missing
2. Variables are not prefixed with `VITE_`
3. Docker image not rebuilt after changing `.env.production`

**Solutions:**

```bash
# Check .env.production exists
ls -la frontend/.env.production

# Check variables are prefixed correctly
cat frontend/.env.production | grep VITE_

# Rebuild Docker image (REQUIRED after changing .env.production)
docker-compose -f docker-compose.production.yml build --no-cache krai-frontend
docker-compose -f docker-compose.production.yml up -d krai-frontend
```

#### Issue 5: Container Fails Health Check

**Symptoms:**
- Container status shows "unhealthy"
- Container restarts repeatedly

**Possible Causes:**
1. Nginx failed to start
2. Build output is missing or corrupted
3. Port 80 is not accessible inside container

**Solutions:**

```bash
# Check container logs
docker-compose -f docker-compose.production.yml logs krai-frontend

# Check nginx is running
docker-compose -f docker-compose.production.yml exec krai-frontend ps aux | grep nginx

# Test health check manually
docker-compose -f docker-compose.production.yml exec krai-frontend wget --no-verbose --tries=1 --spider http://localhost/
```

#### Issue 6: Slow Initial Load

**Symptoms:**
- First page load takes > 5 seconds
- Large JavaScript bundle sizes

**Possible Causes:**
1. Bundle not optimized
2. Gzip compression not working
3. Too many dependencies in main bundle

**Solutions:**

```bash
# Check gzip is enabled
curl -I -H "Accept-Encoding: gzip" http://localhost:3000/assets/index-*.js
# Should see: Content-Encoding: gzip

# Check bundle size with verbose output
npm run build:production:verbose

# Check vendor chunk splitting in vite.config.ts
cat frontend/vite.config.ts | grep -A 10 manualChunks
```

### Debugging Tips

**Enable verbose nginx logging:**

Edit `nginx/nginx-simple.conf`:
```nginx
error_log /var/log/nginx/error.log debug;
```

Rebuild and check logs:
```bash
docker-compose -f docker-compose.production.yml build krai-frontend
docker-compose -f docker-compose.production.yml up -d krai-frontend
docker-compose -f docker-compose.production.yml logs -f krai-frontend
```

**Inspect built files:**
```bash
# List built files
docker-compose -f docker-compose.production.yml exec krai-frontend ls -lah /usr/share/nginx/html

# Check index.html
docker-compose -f docker-compose.production.yml exec krai-frontend cat /usr/share/nginx/html/index.html
```

**Test API from inside container:**
```bash
# Test backend connectivity from frontend container
docker-compose -f docker-compose.production.yml exec krai-frontend wget -O- http://krai-engine:8000/health
```

---

## Security Considerations

### 1. DevTools Disabled

**Why:** React Query DevTools expose internal application state and query cache, which could leak sensitive information.

**Verification:**
```bash
# Check .env.production
cat frontend/.env.production | grep VITE_ENABLE_DEVTOOLS
# Should show: VITE_ENABLE_DEVTOOLS=false
```

**Impact:** ~50KB smaller bundle, no internal state exposure.

### 2. Security Headers

**Configured in nginx:**
- `X-Frame-Options: SAMEORIGIN` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection: 1; mode=block` - Enables XSS protection

**Verification:**
```bash
curl -I http://localhost:3000 | grep -E "X-Frame-Options|X-Content-Type-Options|X-XSS-Protection"
```

### 3. Token Storage

**Configuration:**
- Tokens stored in `localStorage` (not `sessionStorage` or cookies)
- Keys: `krai_auth_token` and `krai_refresh_token`

**Security considerations:**
- `localStorage` is vulnerable to XSS attacks
- Ensure Content Security Policy (CSP) is configured
- Consider using `httpOnly` cookies for tokens (requires backend changes)

**Best practices:**
- Implement token expiration and refresh
- Clear tokens on logout
- Validate tokens on each request

### 4. CORS Configuration

**Backend must allow:**
- Origin: `http://localhost:3000` (or production domain)
- Credentials: `true` (if using cookies)
- Methods: `GET, POST, PUT, DELETE, PATCH, OPTIONS`

**Verification:**
```bash
# Test CORS preflight
curl -X OPTIONS http://localhost:3000/api/documents \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

### 5. Source Maps

**Current configuration:** `sourcemap: true`

**Security considerations:**
- Source maps expose original source code
- Useful for error tracking and debugging
- Consider `sourcemap: 'hidden'` for production (generates maps but doesn't reference them)

**To disable source maps:**

Edit `frontend/vite.config.ts`:
```typescript
build: {
  sourcemap: false, // or 'hidden'
}
```

### 6. Environment Variable Exposure

**What's exposed:**
- All `VITE_*` variables are compiled into the JavaScript bundle
- Anyone can view these by inspecting the built files

**Best practices:**
- Never put secrets in `VITE_*` variables
- API keys should be handled by backend
- Only put non-sensitive configuration in frontend env vars

---

## Performance Optimization

### 1. Vite Build Optimizations

**Configured in `vite.config.ts`:**

```typescript
build: {
  minify: 'esbuild',        // Fast minification
  cssCodeSplit: true,       // Split CSS for parallel loading
  chunkSizeWarningLimit: 1000,
  rollupOptions: {
    output: {
      manualChunks: {
        'react-vendor': ['react', 'react-dom', 'react-router-dom'],
        'ui-vendor': ['@radix-ui/...'],
        'query-vendor': ['@tanstack/react-query'],
      },
    },
  },
}
```

**Benefits:**
- Faster builds with esbuild (vs terser)
- Better caching with vendor chunk separation
- Parallel CSS loading
- Smaller initial bundle size

### 2. Nginx Gzip Compression

**Configured in `nginx/nginx-simple.conf`:**

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript 
           application/javascript application/json;
```

**Benefits:**
- 60-80% size reduction for text files
- Faster page loads
- Reduced bandwidth usage

**Verification:**
```bash
# Check compression ratio
curl -H "Accept-Encoding: gzip" http://localhost:3000/assets/index-*.js -o /tmp/compressed.js.gz
curl http://localhost:3000/assets/index-*.js -o /tmp/uncompressed.js
ls -lh /tmp/compressed.js.gz /tmp/uncompressed.js
```

### 3. Code Splitting

**Automatic code splitting:**
- Vite automatically splits code at dynamic imports
- Each route can be lazy-loaded

**Example:**
```typescript
// Lazy load route components
const Documents = lazy(() => import('./pages/Documents'))
const Products = lazy(() => import('./pages/Products'))
```

**Benefits:**
- Smaller initial bundle
- Faster first page load
- Load code only when needed

### 4. Asset Optimization

**Images:**
- Use modern formats (WebP, AVIF)
- Implement lazy loading
- Optimize image sizes

**Fonts:**
- Use font-display: swap
- Subset fonts to include only needed characters
- Preload critical fonts

### 5. Caching Strategy

**Nginx caching headers:**

Add to `nginx/nginx-simple.conf`:
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Benefits:**
- Browser caches static assets for 1 year
- Vite adds content hashes to filenames (cache busting)
- Faster subsequent page loads

### 6. Performance Monitoring

**Tools:**
- Chrome DevTools Lighthouse
- WebPageTest
- Google PageSpeed Insights

**Key metrics to track:**
- First Contentful Paint (FCP): < 1.8s
- Largest Contentful Paint (LCP): < 2.5s
- Time to Interactive (TTI): < 3.8s
- Cumulative Layout Shift (CLS): < 0.1

**Monitoring in production:**
- Implement Real User Monitoring (RUM)
- Track Core Web Vitals
- Monitor bundle sizes over time

---

## Maintenance

### Updating Environment Variables

**Process:**
1. Edit `frontend/.env.production`
2. Rebuild Docker image:
   ```bash
   docker-compose -f docker-compose.production.yml build krai-frontend
   ```
3. Restart container:
   ```bash
   docker-compose -f docker-compose.production.yml up -d krai-frontend
   ```
4. Verify changes:
   ```bash
   # Test in browser
   # Check API calls use new configuration
   ```

**Important:** Environment variables are baked into the build - runtime changes are not possible.

### Updating Dependencies

**Process:**
1. Update `package.json`:
   ```bash
   cd frontend
   npm update
   # or for specific package
   npm install package-name@latest
   ```
2. Test locally:
   ```bash
   npm run build:production
   npm run preview:production
   ```
3. Run tests:
   ```bash
   npm run test:unit
   npm run test:e2e
   ```
4. Rebuild Docker image:
   ```bash
   docker-compose -f docker-compose.production.yml build krai-frontend
   ```
5. Deploy and verify

**Security updates:**
```bash
# Check for vulnerabilities
npm audit

# Fix automatically
npm audit fix

# Fix with breaking changes (careful!)
npm audit fix --force
```

### Monitoring Frontend Performance

**Log analysis:**
```bash
# View nginx access logs
docker-compose -f docker-compose.production.yml logs krai-frontend | grep "GET"

# Count requests by endpoint
docker-compose -f docker-compose.production.yml logs krai-frontend | grep "GET" | awk '{print $7}' | sort | uniq -c | sort -rn
```

**Error tracking:**
```bash
# View nginx error logs
docker-compose -f docker-compose.production.yml logs krai-frontend | grep "error"

# Count errors by type
docker-compose -f docker-compose.production.yml logs krai-frontend | grep "error" | awk '{print $NF}' | sort | uniq -c
```

**Container resource usage:**
```bash
# Check CPU and memory usage
docker stats krai-frontend

# Check disk usage
docker-compose -f docker-compose.production.yml exec krai-frontend df -h
```

### Backup and Rollback

**Backup current image:**
```bash
# Tag current image
docker tag krai-minimal-krai-frontend:latest krai-minimal-krai-frontend:backup-$(date +%Y%m%d)

# List backups
docker images | grep krai-frontend
```

**Rollback to previous version:**
```bash
# Stop current container
docker-compose -f docker-compose.production.yml stop krai-frontend

# Tag backup as latest
docker tag krai-minimal-krai-frontend:backup-20250118 krai-minimal-krai-frontend:latest

# Start container
docker-compose -f docker-compose.production.yml up -d krai-frontend
```

### Cleaning Up

**Remove old images:**
```bash
# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a
```

**Clean build cache:**
```bash
# Remove node_modules and build artifacts
cd frontend
rm -rf node_modules dist .vite
npm ci
```

---

## Quick Reference

### Essential Commands

```bash
# Build production image
docker-compose -f docker-compose.production.yml build krai-frontend

# Start container
docker-compose -f docker-compose.production.yml up -d krai-frontend

# View logs
docker-compose -f docker-compose.production.yml logs -f krai-frontend

# Restart container
docker-compose -f docker-compose.production.yml restart krai-frontend

# Stop container
docker-compose -f docker-compose.production.yml stop krai-frontend

# Check health
docker-compose -f docker-compose.production.yml ps krai-frontend

# Test locally
cd frontend && npm run build:production && npm run preview:production
```

### Important Files

| File | Purpose |
|------|---------|
| `frontend/.env.production` | Production environment variables |
| `frontend/Dockerfile` | Docker build configuration |
| `frontend/vite.config.ts` | Vite build configuration |
| `frontend/package.json` | Dependencies and scripts |
| `nginx/nginx-simple.conf` | Nginx server configuration |
| `docker-compose.production.yml` | Docker Compose configuration |

### Support

For issues or questions:
1. Check this documentation
2. Review logs: `docker-compose logs krai-frontend`
3. Check [DEPLOYMENT.md](../../DEPLOYMENT.md) for general deployment info
4. Check [frontend/README.md](../../frontend/README.md) for development info

---

**Last Updated:** 2025-01-18
**Version:** 1.0.0
