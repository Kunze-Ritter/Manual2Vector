# 🧪 QA Test Suite - KRAI Engine Production Readiness

**Date:** 2025-10-05
**Version:** 1.0.0
**Status:** Ready for Testing

---

## ✅ **TEST CHECKLIST**

### **1. Database Migrations (CRITICAL)**
- [ ] Migration 30: Service role permissions
- [ ] Migration 31: Public views + triggers
- [ ] Migration 32: Foreign key fix
- [ ] Migration 33: Video dedup indexes
- [ ] Migration 34: Video view triggers
- [ ] All migrations applied without errors
- [ ] All tables accessible
- [ ] All triggers functioning

### **2. Video Enrichment System**
- [ ] YouTube API connection working
- [ ] YouTube metadata extraction (title, views, etc.)
- [ ] Vimeo API working (oEmbed)
- [ ] Brightcove API working
- [ ] Video deduplication working (same video = one record)
- [ ] Contextual metadata (manufacturer, series, error codes)
- [ ] Database inserts successful
- [ ] No duplicate videos created

### **3. Link Management System**
- [ ] Link validation working
- [ ] URL cleaning (trailing punctuation)
- [ ] Redirect following (301/302/307/308)
- [ ] GET fallback working
- [ ] Auto-fixing (http→https, www)
- [ ] Database updates working
- [ ] Broken links marked inactive

### **4. Content Management API**
- [ ] POST /content/videos/enrich (async) working
- [ ] POST /content/videos/enrich/sync working
- [ ] POST /content/links/check (async) working
- [ ] POST /content/links/check/sync working
- [ ] GET /content/tasks/{task_id} working
- [ ] GET /content/tasks working
- [ ] Background tasks executing
- [ ] Progress tracking working

### **5. Master Pipeline (All 8 Stages)**
- [ ] Stage 1: Upload - File validation & dedup
- [ ] Stage 2: Text extraction & chunking
- [ ] Stage 3: Image extraction + OCR + Vision
- [ ] Stage 4: Product extraction (Pattern + LLM)
- [ ] Stage 5: Error code & version extraction
- [ ] Stage 6: R2 storage upload
- [ ] Stage 7: Embedding generation (pgvector)
- [ ] Stage 8: Search analytics tracking
- [ ] Full pipeline executes without errors
- [ ] All data stored correctly

### **6. Search & Embeddings**
- [ ] Embedding generation working
- [ ] pgvector storage working
- [ ] Semantic search working
- [ ] Similarity threshold working
- [ ] Query performance acceptable (<1s)

### **7. Production Configuration**
- [ ] All environment variables set
- [ ] Supabase connection working
- [ ] R2 storage accessible
- [ ] Ollama models available (qwen2.5, llava, embeddinggemma)
- [ ] API keys configured (YouTube)
- [ ] No hardcoded secrets
- [ ] Logging configured
- [ ] Error handling working

### **8. Performance & Security**
- [ ] API response times acceptable
- [ ] No memory leaks
- [ ] Error handling robust
- [ ] Rate limiting working (if enabled)
- [ ] CORS configured properly
- [ ] Health check endpoint working
- [ ] No sensitive data in logs

---

## 🧪 **DETAILED TEST CASES**

### **TEST 1: Database Migration Verification**

**Command:**
```sql
-- In Supabase SQL Editor
-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'krai_content' 
AND table_name IN ('videos', 'links', 'images', 'chunks');

-- Check triggers exist
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
AND trigger_name LIKE '%video%';

-- Check indexes exist
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'krai_content'
AND indexname LIKE '%video%';
```

**Expected Result:**
- All tables exist
- Triggers: videos_insert_trigger, videos_update_trigger, videos_delete_trigger
- Indexes: idx_videos_youtube_id, idx_videos_vimeo_id, idx_videos_brightcove_id, idx_videos_link_id

---

### **TEST 2: Video Enrichment - YouTube**

**Command:**
```bash
python scripts/enrich_video_metadata.py --limit 3
```

**Expected Result:**
```
✅ Processing complete!
   Enriched: 3
   Errors: 0
   
Expected in DB:
- videos table has 3 new records
- youtube_id populated
- title, description, thumbnail_url populated
- view_count, like_count populated
- manufacturer_id, series_id populated (if available)
```

**Manual Verification:**
```sql
-- Check YouTube videos
SELECT 
    id,
    youtube_id,
    title,
    view_count,
    manufacturer_id,
    series_id
FROM krai_content.videos
WHERE youtube_id IS NOT NULL
ORDER BY created_at DESC
LIMIT 3;
```

---

### **TEST 3: Video Deduplication**

**Command:**
```bash
# Run enrichment twice on same videos
python scripts/enrich_video_metadata.py --limit 5
python scripts/enrich_video_metadata.py --limit 5
```

**Expected Result:**
```
First run: Enriched 5 videos
Second run: Enriched 0 videos (all duplicates detected)

Expected in DB:
- Only 5 video records (not 10!)
- Deduplication logs show "Video exists from another link, reusing"
```

---

### **TEST 4: Link Checker - URL Cleaning**

**Command:**
```bash
python scripts/check_and_fix_links.py --check-only --limit 10
```

**Expected Result:**
```
✅ Summary:
   Total checked: 10
   Working: X
   Broken: Y
   Fixed: Z (auto-cleaned trailing punctuation)
   
Expected behavior:
- URLs with trailing "." cleaned automatically
- Marked as "fixed" with cleaned URL
- Database updated with correct URL
```

---

### **TEST 5: Link Checker - Redirects**

**Test URL:** `http://example.com/old` (that redirects to `https://example.com/new`)

**Expected Result:**
```
✅ Working (Status: 200)
🔀 Redirects to: https://example.com/new
Status: fixed

Expected in DB:
- link.url updated to final URL
- Marked as working
```

---

### **TEST 6: Content Management API**

**Start Backend:**
```bash
cd backend
python main.py
```

**Test in Browser:**
```
http://localhost:8000/docs
```

**Test Endpoints:**

1. **GET /health**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected: `{"status":"healthy", "services":{"database":"healthy", ...}}`

2. **POST /content/videos/enrich/sync**
   ```bash
   curl -X POST http://localhost:8000/content/videos/enrich/sync \
     -H "Content-Type: application/json" \
     -d '{"limit": 3}'
   ```
   Expected: `{"status":"completed", "enriched_count":3, ...}`

3. **POST /content/links/check/sync**
   ```bash
   curl -X POST http://localhost:8000/content/links/check/sync \
     -H "Content-Type: application/json" \
     -d '{"limit": 5, "check_only": true}'
   ```
   Expected: `{"status":"completed", "checked_count":5, ...}`

---

### **TEST 7: Master Pipeline End-to-End**

**Command:**
```bash
cd backend/processors_v2
python test_pipeline_live.py
```

**Expected Result:**
```
🧪 TEST 1: Upload & Validation ✅
🧪 TEST 2: Text Extraction ✅
🧪 TEST 3: Image Processing ✅
🧪 TEST 4: Product Extraction ✅
🧪 TEST 5: Embeddings ✅

>>> ALL TESTS PASSED!
The pipeline is working end-to-end!
```

---

### **TEST 8: Search & Embeddings**

**Command:**
```bash
cd backend/processors_v2
python test_embedding_processor.py
```

**Expected Result:**
```
✅ Test 1: Configuration check PASSED
✅ Test 2: Single embedding PASSED
✅ Test 3: Batch embeddings PASSED
✅ Test 4: Similarity search PASSED

🎉 ALL TESTS PASSED!
Embedding processor ready for semantic search!
```

---

### **TEST 9: Performance Test**

**Test:** Process a medium-sized PDF (50-100 pages)

**Metrics to Check:**
- Upload: < 5s
- Text extraction: < 30s
- Image processing: < 2 min
- Embeddings: < 1 min
- Total: < 5 min

**Memory usage:** < 2GB RAM

---

### **TEST 10: Production Config Verification**

**Checklist:**
```bash
# Check .env file
cat .env | grep -E "SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY|R2_ACCESS_KEY|OLLAMA_URL|YOUTUBE_API_KEY"

# All should be set (not empty, not "your_key_here")
```

**Check Ollama models:**
```bash
curl http://localhost:11434/api/tags
```

Expected models:
- qwen2.5:7b ✅
- llava:13b ✅
- embeddinggemma ✅

---

## 🐛 **COMMON ISSUES & FIXES**

### **Issue 1: Migration Fails**
**Error:** "relation already exists"
**Fix:** Migrations are idempotent, check if already applied

### **Issue 2: Video Enrichment - YouTube Quota Exceeded**
**Error:** "YouTube quota exceeded"
**Fix:** Wait 24 hours or upgrade quota

### **Issue 3: Link Checker Timeout**
**Error:** "Timeout"
**Fix:** Timeout is 30s, slow servers may still fail. Check logs for details.

### **Issue 4: Embeddings Not Working**
**Error:** "Ollama connection failed"
**Fix:** 
```bash
# Check Ollama is running
curl http://localhost:11434/api/version

# Pull model if missing
ollama pull embeddinggemma
```

### **Issue 5: API 503 Service Unavailable**
**Error:** "Service not available"
**Fix:** Services not initialized. Check backend startup logs.

---

## ✅ **SIGN-OFF CRITERIA**

**Project is READY FOR PRODUCTION when:**
- [ ] All migrations applied (30-34) ✅
- [ ] All 8 pipeline stages tested ✅
- [ ] Video enrichment working (all 3 platforms) ✅
- [ ] Link checker working ✅
- [ ] API endpoints working ✅
- [ ] Search & embeddings working ✅
- [ ] Performance acceptable ✅
- [ ] No critical bugs ✅
- [ ] Documentation complete ✅
- [ ] Production config verified ✅

**Sign-off:** ____________________ Date: __________

---

## 📊 **TEST EXECUTION LOG**

| Test # | Test Name | Status | Date | Notes |
|--------|-----------|--------|------|-------|
| 1 | Database Migrations | ⏳ | | |
| 2 | Video Enrichment | ⏳ | | |
| 3 | Video Deduplication | ⏳ | | |
| 4 | Link Checker | ⏳ | | |
| 5 | Redirects | ⏳ | | |
| 6 | Content API | ⏳ | | |
| 7 | Master Pipeline | ⏳ | | |
| 8 | Search & Embeddings | ⏳ | | |
| 9 | Performance | ⏳ | | |
| 10 | Production Config | ⏳ | | |

**Legend:** ⏳ Pending | ✅ Passed | ❌ Failed | ⚠️ Warning

---

## 🚀 **NEXT STEPS AFTER QA**

1. ✅ All tests passing → **PRODUCTION DEPLOYMENT**
2. ❌ Tests failing → Fix issues, re-test
3. ⚠️ Warnings → Document known issues, decide if blocker

**After successful QA:**
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Verify health
curl https://your-domain.com/health

# 🎉 GO LIVE!
```
