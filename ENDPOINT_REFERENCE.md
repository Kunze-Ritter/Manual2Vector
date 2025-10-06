# 🔌 KRAI Engine - API Endpoints Reference

**Base URL:** `http://localhost:8000`

---

## ✅ WORKING ENDPOINTS (V2.1)

### **Core Endpoints**
```
GET  /                    - Root endpoint
GET  /health             - Health check ✅
GET  /info               - API information ✅
GET  /docs               - Swagger UI ✅
GET  /redoc              - ReDoc UI ✅
```

### **Search API** (`/search`)
```
POST /search/                           - Semantic search
GET  /search/suggestions?q={query}      - Search suggestions
POST /search/vector                     - Vector similarity search
GET  /search/error-codes?q={query}      - Search error codes
GET  /search/health                     - Search health check
```

### **Document API** (`/documents`)
```
POST /documents/upload                  - Upload document
GET  /documents/{document_id}           - Get document info
GET  /documents/{document_id}/status    - Get processing status
POST /documents/{document_id}/reprocess - Reprocess document
GET  /documents/{document_id}/chunks    - Get document chunks
GET  /documents/{document_id}/images    - Get document images
```

### **Features API** (`/features`)
```
GET  /features/series/{series_id}                     - Get series features
GET  /features/product/{product_id}                   - Get product features
GET  /features/effective/{series_id}/{product_id}     - Get effective features
POST /features/search                                 - Search by features
GET  /features/inheritance/{series_id}                - Get inheritance info
GET  /features/health                                 - Features health check
```

### **Defect Detection API** (`/defects`)
```
POST /defects/analyze                   - Analyze defect
GET  /defects/history                   - Get detection history
POST /defects/feedback                  - Submit feedback
GET  /defects/health                    - Defect detection health check
```

### **Content Management API** (`/content`) ⭐ NEW in V2!
```
POST /content/videos/enrich             - Enrich videos (async)
POST /content/videos/enrich/sync        - Enrich videos (sync)
POST /content/links/check               - Check links (async)
POST /content/links/check/sync          - Check links (sync)
GET  /content/tasks/{task_id}           - Get task status
GET  /content/tasks                     - List all tasks
```

---

## 🧪 TESTING COMMANDS

### **PowerShell:**

```powershell
# Health Check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# API Info
Invoke-RestMethod -Uri "http://localhost:8000/info"

# Search Suggestions
Invoke-RestMethod -Uri "http://localhost:8000/search/suggestions?q=error"

# Search Health
Invoke-RestMethod -Uri "http://localhost:8000/search/health"

# Features Health
Invoke-RestMethod -Uri "http://localhost:8000/features/health"

# Defects Health
Invoke-RestMethod -Uri "http://localhost:8000/defects/health"

# Content Tasks
Invoke-RestMethod -Uri "http://localhost:8000/content/tasks"
```

### **cURL:**

```bash
# Health Check
curl http://localhost:8000/health

# API Info
curl http://localhost:8000/info

# Search Suggestions
curl "http://localhost:8000/search/suggestions?q=error"

# Search Error Codes
curl "http://localhost:8000/search/error-codes?q=E001"
```

---

## ⚠️ DEPRECATED/REMOVED ENDPOINTS

These endpoints don't exist (404):
```
❌ GET /features              - Use /features/... instead
❌ GET /search?query=...      - Use POST /search/ instead
❌ GET /defects               - Use /defects/... instead
```

---

## 📊 ENDPOINT CATEGORIES

**Working (Core):**
- `/` ✅
- `/health` ✅
- `/info` ✅
- `/docs` ✅

**Working (Features):**
- All `/search/*` endpoints ✅
- All `/documents/*` endpoints ✅
- All `/features/*` endpoints ✅
- All `/defects/*` endpoints ✅
- All `/content/*` endpoints ✅

---

## 🎯 QUICK TEST SCRIPT

```powershell
# Test all health endpoints
@(
    "http://localhost:8000/health",
    "http://localhost:8000/search/health",
    "http://localhost:8000/features/health",
    "http://localhost:8000/defects/health"
) | ForEach-Object {
    Write-Host "Testing: $_"
    try {
        $result = Invoke-RestMethod -Uri $_
        Write-Host "  [OK]" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL]" -ForegroundColor Red
    }
}
```
