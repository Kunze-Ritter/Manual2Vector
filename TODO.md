# KRAI Complete Pipeline Refactor - TODO List

## 🎯 Project Status: 40% Complete

**IMPORTANT:** This TODO covers the COMPLETE 8-Stage Pipeline refactor!

---

## 📊 ORIGINAL vs REFACTORED Pipeline Comparison

### Original 8-Stage Pipeline (backend/processors/):
1. **Upload Processor** - Document ingestion & deduplication
2. **Text Processor** - Smart chunking with AI analysis
3. **Image Processor** - OCR, AI vision (SVG support)
4. **Classification Processor** - Manufacturer/product detection
5. **Metadata Processor** - Error codes & version extraction
6. **Storage Processor** - Cloudflare R2 object storage
7. **Embedding Processor** - Vector embeddings for search
8. **Search Processor** - Search analytics & indexing

### Current Refactored Pipeline (backend/processors_v2/):
- Step 1: Text extraction ✅ (Partial Stage 2)
- Step 2: Product extraction ✅ (Partial Stage 4)
- Step 3: Error code extraction ✅ (Partial Stage 5)
- Step 4: Chunking ✅ (Partial Stage 2)
- Step 5: Statistics ✅

**Missing Stages:** 1, 3, 6, 7, 8 (5 out of 8!)

---

## ✅ COMPLETED (Stages 2, 4, 5 - Partial)

### Phase 1: Database Schema
- [x] JSONB restructure (specifications, pricing, lifecycle, urls, metadata)
- [x] Product accessories table with relationships
- [x] Helper functions (meets_requirements, get_product_accessories, compare_products)
- [x] Compatibility system with 7 relationship types
- [x] Remove model_name redundancy (display_name property)

### Phase 2: Product Extraction
- [x] Pattern-based extraction (HP, Canon, Konica Minolta, Lexmark)
- [x] LLM integration (Ollama + qwen2.5:7b)
- [x] Universal page scanning (all pages, not just spec sections)
- [x] Series detection (AccurioPress, LaserJet, etc.)
- [x] Deduplication logic (prefer bare model numbers)
- [x] Extended product types (11 types: printer, scanner, multifunction, copier, plotter, finisher, feeder, tray, cabinet, accessory, consumable)
- [x] Manufacturer auto-detection from context

### Phase 3: Configuration Validation
- [x] ConfigurationValidator class (Python)
- [x] ConfigurationAgent (AI-powered Q&A)
- [x] Dependency tracking
- [x] Conflict detection
- [x] Natural language interface

### Phase 4: Testing
- [x] AccurioPress PDF: 22 products (vs 6 before, +267%)
- [x] LLM extraction tests
- [x] Configuration validation tests
- [x] All unit tests passing

---

## 🚧 IN PROGRESS

### Vision Extraction
- [x] LLaVA integration code (vision_extractor.py)
- [ ] Test on real PDF pages with tables
- [ ] Optimize image resolution vs speed
- [ ] Compare Vision vs Text-only extraction quality
  - **Priority:** Medium
  - **Effort:** 2-3 hours
  - **Blocker:** Need complex table-heavy PDFs for testing

### Product Type Refinement
- [x] Types defined and validated
- [ ] Improve LLM prompt for better type detection
- [ ] Post-processing rules (MK-* = finisher, SD-* = finisher, PF-* = feeder)
- [ ] Confidence scoring per type
  - **Priority:** Medium
  - **Effort:** 1-2 hours

---

## ❌ TODO - MISSING PIPELINE STAGES (CRITICAL!)

### 🚨 STAGE 1: Upload Processor (NOT STARTED)
**Priority:** CRITICAL | **Effort:** 6-8 hours

- [ ] **Document Ingestion**
  - [ ] File validation (PDF format, size limits, corruption check)
  - [ ] Duplicate detection (hash-based)
  - [ ] Database record creation (krai_core.documents)
  - [ ] Processing queue management (krai_system.processing_queue)
  - **File:** `backend/processors_v2/upload_processor.py`

- [ ] **Deduplication Logic**
  - [ ] SHA-256 hash calculation
  - [ ] Database lookup for existing documents
  - [ ] Skip or re-process logic
  - [ ] Update existing records

- [ ] **Document Metadata Extraction**
  - [ ] PDF metadata (title, author, creation date)
  - [ ] File info (size, page count)
  - [ ] Document type detection (service_manual, parts_catalog, user_guide)
  
- [ ] **Integration with master_pipeline.py**
  - [ ] Replace old upload logic
  - [ ] Queue management
  - [ ] Status tracking

---

### 🚨 STAGE 3: Image Processor (NOT STARTED)
**Priority:** HIGH | **Effort:** 8-10 hours

- [ ] **Image Extraction from PDFs**
  - [ ] Extract all images from PDF pages
  - [ ] SVG to PNG conversion (existing logic)
  - [ ] Image deduplication (hash-based)
  - [ ] Store in krai_content.images
  - **File:** `backend/processors_v2/image_processor.py`

- [ ] **OCR Processing**
  - [ ] Tesseract OCR integration
  - [ ] Text extraction from images
  - [ ] Confidence scoring
  - [ ] Store OCR results in database

- [ ] **Vision AI Analysis**
  - [ ] LLaVA model integration (use existing vision_extractor.py)
  - [ ] Image classification (diagram, photo, table, schematic)
  - [ ] Object detection (parts, assemblies)
  - [ ] Text-in-image extraction
  - [ ] Store vision results in metadata

- [ ] **Print Defect Detection**
  - [ ] Existing logic from krai_content.print_defects
  - [ ] Integrate into pipeline
  - [ ] Error pattern recognition

---

### 🚨 STAGE 6: Storage Processor (NOT STARTED)
**Priority:** HIGH | **Effort:** 4-6 hours

- [ ] **Cloudflare R2 Integration**
  - [ ] Upload PDFs to R2
  - [ ] Upload extracted images to R2
  - [ ] Generate presigned URLs
  - [ ] Store URLs in database
  - **File:** `backend/processors_v2/storage_processor.py`

- [ ] **File Organization**
  - [ ] Path structure: {manufacturer}/{product_series}/{document_id}/
  - [ ] Original PDF storage
  - [ ] Processed images storage
  - [ ] Thumbnail generation

- [ ] **Cleanup Logic**
  - [ ] Delete local temp files after upload
  - [ ] R2 retention policies
  - [ ] Orphan file detection

---

### 🚨 STAGE 7: Embedding Processor (NOT STARTED)
**Priority:** HIGH | **Effort:** 6-8 hours

- [ ] **Vector Embedding Generation**
  - [ ] Use existing embedding service (nomic-embed-text)
  - [ ] Batch processing for efficiency
  - [ ] Store in krai_intelligence.embeddings
  - **File:** `backend/processors_v2/embedding_processor.py`

- [ ] **Chunk Embeddings**
  - [ ] Generate embeddings for all chunks
  - [ ] pgvector integration
  - [ ] Batch insert optimization

- [ ] **Image Embeddings** (Optional)
  - [ ] Visual embeddings for image search
  - [ ] Multimodal search capability

- [ ] **Embedding Updates**
  - [ ] Re-embed on document updates
  - [ ] Incremental embedding logic

---

### 🚨 STAGE 8: Search Processor (NOT STARTED)
**Priority:** MEDIUM | **Effort:** 4-6 hours

- [ ] **Search Analytics**
  - [ ] Track search queries
  - [ ] Store in krai_intelligence.search_analytics
  - [ ] Performance metrics
  - **File:** `backend/processors_v2/search_processor.py`

- [ ] **Search Indexing**
  - [ ] Full-text search optimization
  - [ ] Vector similarity indexing
  - [ ] Hybrid search (text + vector)

- [ ] **Search Quality Metrics**
  - [ ] Relevance scoring
  - [ ] Click-through tracking
  - [ ] Query refinement suggestions

---

## ❌ TODO - ADDITIONAL FEATURES

### Phase 5: Data Population & Extraction (HIGH PRIORITY)

#### 5.1 Compatibility Data Extraction
- [ ] Extract compatibility info from service manuals with LLM
  - **Task:** Parse "Options/Accessories" sections
  - **Detect:** "requires", "compatible with", "cannot be used with"
  - **Priority:** HIGH
  - **Effort:** 4-6 hours
  - **File:** `backend/processors_v2/compatibility_extractor.py`

- [ ] Populate product_accessories table
  - **Task:** Insert extracted relationships into database
  - **Priority:** HIGH
  - **Effort:** 2 hours

#### 5.2 Multi-Document Processing
- [ ] Process Parts Catalogs
  - **Extract:** Part numbers, compatibility, replacement info
  - **Priority:** MEDIUM
  - **Effort:** 3-4 hours

- [ ] Process User Guides
  - **Extract:** Installation requirements, setup dependencies
  - **Priority:** LOW
  - **Effort:** 2-3 hours

- [ ] Process Quick Reference Guides
  - **Extract:** Feature comparisons, model differences
  - **Priority:** LOW
  - **Effort:** 1-2 hours

#### 5.3 Series Mappings
- [ ] Create comprehensive series mapping table
  - **Manufacturers:** HP, Canon, Konica Minolta, Lexmark, Xerox, Brother, Epson
  - **Data:** Series name, model pattern, launch year
  - **Priority:** MEDIUM
  - **Effort:** 2-3 hours
  - **File:** `database/seed_data/product_series.sql`

---

### Phase 6: API Development (HIGH PRIORITY)

#### 6.1 Configuration Validation API
- [ ] POST /api/validate-configuration
  - **Input:** base_product_id, accessory_ids[]
  - **Output:** is_valid, errors[], recommendations[]
  - **Priority:** HIGH
  - **Effort:** 2-3 hours
  - **File:** `backend/api/configuration.py`

- [ ] GET /api/products/{id}/required-accessories
  - **Output:** List of required accessories with reasons
  - **Priority:** HIGH
  - **Effort:** 1 hour

- [ ] GET /api/products/{id}/incompatible-products
  - **Output:** List of conflicting products
  - **Priority:** MEDIUM
  - **Effort:** 1 hour

#### 6.2 Product Search API
- [ ] GET /api/products/search
  - **Params:** q, manufacturer, type, series
  - **Output:** Paginated product list
  - **Priority:** MEDIUM
  - **Effort:** 2-3 hours

- [ ] GET /api/products/{id}/specifications
  - **Output:** Full JSONB specifications
  - **Priority:** MEDIUM
  - **Effort:** 1 hour

#### 6.3 AI Agent API
- [ ] POST /api/config-agent/ask
  - **Input:** question (natural language)
  - **Output:** answer, confidence, sources
  - **Priority:** MEDIUM
  - **Effort:** 2-3 hours
  - **File:** `backend/api/agent.py`

---

### Phase 7: Tender Matching Integration (MEDIUM PRIORITY)

#### 7.1 Configuration Builder
- [ ] Algorithm: Match tender requirements to products
  - **Input:** Tender specs (speed, capacity, features)
  - **Output:** Ranked product configurations
  - **Priority:** HIGH
  - **Effort:** 6-8 hours
  - **File:** `backend/tender/config_builder.py`

- [ ] Scoring system for configuration quality
  - **Metrics:** Spec match %, price, availability
  - **Priority:** HIGH
  - **Effort:** 3-4 hours

#### 7.2 Alternative Suggestions
- [ ] Find alternative products when exact match not available
  - **Priority:** MEDIUM
  - **Effort:** 2-3 hours

- [ ] Cost optimization (suggest cheaper alternatives)
  - **Priority:** LOW
  - **Effort:** 2-3 hours

---

### Phase 8: Frontend Integration (MEDIUM PRIORITY)

#### 8.1 Configuration Wizard
- [ ] UI: Step-by-step product configuration
  - **Step 1:** Select base product
  - **Step 2:** Choose accessories
  - **Step 3:** Validate configuration
  - **Step 4:** Review & export
  - **Priority:** MEDIUM
  - **Effort:** 8-10 hours
  - **Stack:** React + TailwindCSS

- [ ] Real-time validation feedback
  - **Show:** Conflicts, missing requirements, recommendations
  - **Priority:** HIGH
  - **Effort:** 3-4 hours

#### 8.2 Product Comparison View
- [ ] Side-by-side product comparison
  - **Compare:** Specifications, pricing, accessories
  - **Priority:** LOW
  - **Effort:** 4-5 hours

#### 8.3 Tender Matching UI
- [ ] Upload tender document
- [ ] AI analyzes requirements
- [ ] Suggests optimal configurations
- [ ] Export proposal
  - **Priority:** HIGH
  - **Effort:** 10-12 hours

---

### Phase 9: Performance & Optimization (LOW PRIORITY)

#### 9.1 LLM Optimization
- [ ] Reduce page scanning from 20 to most relevant pages
  - **Strategy:** Keyword-based page filtering
  - **Priority:** MEDIUM
  - **Effort:** 2-3 hours

- [ ] Batch LLM requests for better throughput
  - **Priority:** LOW
  - **Effort:** 3-4 hours

- [ ] Cache LLM results per document
  - **Priority:** MEDIUM
  - **Effort:** 2 hours

#### 9.2 Database Optimization
- [ ] Add indexes for common queries
  - **Queries:** Search by model, filter by type, manufacturer lookup
  - **Priority:** MEDIUM
  - **Effort:** 1-2 hours

- [ ] Materialized views for complex joins
  - **Priority:** LOW
  - **Effort:** 2-3 hours

#### 9.3 Vision Optimization
- [ ] Test different DPI settings (100, 150, 200)
- [ ] Compare LLaVA models (7b vs 13b vs 34b)
- [ ] Selective page rendering (only pages with tables)
  - **Priority:** LOW
  - **Effort:** 3-4 hours

---

### Phase 10: Additional Features (FUTURE)

#### 10.1 Multi-Language Support
- [ ] Extract products from German/French/Spanish manuals
  - **Priority:** FUTURE
  - **Effort:** 6-8 hours

#### 10.2 Historical Data
- [ ] Track product lifecycle (launch, EOL dates)
- [ ] Price history
- [ ] Replacement product tracking
  - **Priority:** FUTURE
  - **Effort:** 4-6 hours

#### 10.3 Integration
- [ ] ERP integration (SAP, etc.)
- [ ] CRM integration
- [ ] Automatic tender response generation
  - **Priority:** FUTURE
  - **Effort:** 20+ hours

---

## 📝 CONFIGURATION TASKS

### Environment Setup
1. ⚠️ **YouTube API Key (OPTIONAL)** - For full video metadata
   - **Task:** Get YouTube Data API v3 key from Google Cloud Console
   - **Purpose:** Extract full video metadata (duration, view count, description, tags)
   - **Fallback:** oEmbed (basic title, thumbnail) works without key
   - **Priority:** LOW
   - **Effort:** 5 minutes
   - **Steps:**
     1. Go to https://console.cloud.google.com/
     2. Create Project
     3. Enable "YouTube Data API v3"
     4. Create Credentials → API Key
     5. Add to .env: `YOUTUBE_API_KEY=AIzaSy...`

---

## 🐛 BUGS & ISSUES

### Known Issues
1. ⚠️ **Product Type Mapping**: Some accessories still categorized as "printer"
   - **Fix:** Improve LLM prompt + post-processing rules
   - **Priority:** MEDIUM
   - **Effort:** 2 hours

2. ⚠️ **Migration 09**: Not applied to production database
   - **Fix:** Manual application via Supabase dashboard
   - **Priority:** HIGH
   - **Effort:** 15 minutes

3. ⚠️ **LLM Timeout**: Occasionally times out on very dense pages
   - **Fix:** Increase timeout to 180s or implement retry logic
   - **Priority:** LOW
   - **Effort:** 30 minutes

4. ⚠️ **Vision Results Empty**: Test showed 0 products
   - **Fix:** Debug keyword detection, test with known good pages
   - **Priority:** MEDIUM
   - **Effort:** 1-2 hours

---

## 📈 Success Metrics

### Current Status:
- ✅ Products extracted: **22** (vs 6 before, **+267%**)
- ✅ With specifications: **8** (NEW!)
- ✅ Accessories found: **16** (NEW!)
- ✅ Avg confidence: **0.83** (up from 0.68, **+22%**)
- ✅ Processing time: **257s** for 4386 pages

### Target Metrics:
- [ ] Products per manual: **25-30** (additional via Vision)
- [ ] Specification completeness: **>80%**
- [ ] Configuration validation accuracy: **>95%**
- [ ] Tender match quality: **>85%** accuracy
- [ ] API response time: **<500ms** for validation

---

## 🚀 Next Sprint Recommendations

### Sprint 1 (1 week): Data & API Foundation
1. Apply Migration 09 to production
2. Build compatibility data extractor
3. Create configuration validation API
4. Populate initial compatibility data

### Sprint 2 (1 week): Tender Integration
1. Build configuration builder algorithm
2. Create tender matching logic
3. API endpoints for tender processing

### Sprint 3 (2 weeks): Frontend
1. Configuration wizard UI
2. Tender matching interface
3. Product comparison view

---

## 📝 Notes

- **LLM Model:** Currently using qwen2.5:7b (good balance of speed/quality)
- **Vision Model:** LLaVA 13b (not yet fully tested)
- **Database:** Supabase (PostgreSQL 15)
- **Processing:** Local (Ollama), can be moved to cloud if needed

---

## 📈 REALISTIC Progress Overview

### Completed (40%):
- ✅ Database Schema (JSONB, compatibility)
- ✅ Product Extraction (Pattern + LLM)
- ✅ Error Code Extraction
- ✅ Configuration Validation System
- ✅ Text Extraction & Chunking

### In Progress (5%):
- ⚠️ Vision Extraction (code ready, not tested)
- ⚠️ Product Type Refinement

### Critical Missing (55%):
- ❌ Stage 1: Upload Processor (8 hours)
- ❌ Stage 3: Image Processor (10 hours)
- ❌ Stage 6: Storage Processor (6 hours)
- ❌ Stage 7: Embedding Processor (8 hours)
- ❌ Stage 8: Search Processor (6 hours)
- ❌ Master Pipeline Integration (12 hours)
- ❌ API Endpoints (12 hours)
- ❌ Testing & QA (8 hours)

### Total Estimated Work Remaining: ~70 hours (2 weeks full-time)

---

## 🎯 Recommended Completion Order

### Phase 1: Core Pipeline (Week 1)
1. **Upload Processor** (Day 1) - Critical foundation
2. **Image Processor** (Day 2-3) - OCR, Vision AI
3. **Storage Processor** (Day 3) - R2 integration
4. **Embedding Processor** (Day 4) - Vector search
5. **Search Processor** (Day 4) - Analytics

### Phase 2: Integration (Week 2)
6. **Master Pipeline Integration** (Day 1-2) - Wire everything together
7. **API Endpoints** (Day 2-3) - REST API for all stages
8. **Testing & QA** (Day 4) - End-to-end tests
9. **Documentation** (Day 4-5) - Update all docs
10. **Deployment** (Day 5) - Production ready

---

## 🚨 CRITICAL DEPENDENCIES

```
Upload Processor (Stage 1)
    ↓
Text Processor (Stage 2) ✅ DONE
    ↓
Image Processor (Stage 3) ❌ MISSING
    ↓
Classification (Stage 4) ✅ DONE
    ↓
Metadata Processor (Stage 5) ✅ DONE
    ↓
Storage Processor (Stage 6) ❌ MISSING
    ↓
Embedding Processor (Stage 7) ❌ MISSING
    ↓
Search Processor (Stage 8) ❌ MISSING
```

**Cannot proceed to production without:**
- Stage 1 (Upload) - No way to ingest documents
- Stage 6 (Storage) - No persistent file storage
- Stage 7 (Embeddings) - No semantic search
- Master Pipeline Integration - Stages not connected

---

**Last Updated:** 2025-10-03
**Actual Progress:** 40% Complete (not 80%!)
**Estimated Remaining:** 70 hours (~2 weeks full-time, ~4 weeks part-time)
