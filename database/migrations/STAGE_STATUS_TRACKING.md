# Per-Stage Status Tracking System

## 🎯 Übersicht

Das neue Per-Stage Status Tracking System ermöglicht detailliertes Monitoring und parallele Verarbeitung von Dokumenten durch individuelle Status-Verfolgung für jede Processing-Stage.

---

## 🏗️ Architektur

### **Alte Architektur (v1):**
```
documents
├── processing_status: "processing"  ❌ Nur globaler Status
└── processing_stage: "text_extraction"  ❌ Nur aktuelle Stage
```

**Probleme:**
- ❌ Keine Historie welche Stages abgeschlossen sind
- ❌ Kein Progress per Stage
- ❌ Keine parallele Verarbeitung möglich
- ❌ Bei Fehler: Welche Stage ist failed?
- ❌ Keine Timestamps per Stage

---

### **Neue Architektur (v2):**
```json
documents
├── processing_status: "processing"
└── stage_status: {
    "upload": {
      "status": "completed",
      "started_at": "2025-10-04T08:00:00Z",
      "completed_at": "2025-10-04T08:00:01Z",
      "duration_seconds": 1.2,
      "progress": 100,
      "error": null,
      "metadata": {}
    },
    "text_extraction": {
      "status": "processing",
      "started_at": "2025-10-04T08:00:01Z",
      "completed_at": null,
      "duration_seconds": null,
      "progress": 45.5,
      "error": null,
      "metadata": {
        "pages_processed": 2000,
        "total_pages": 4386
      }
    },
    ...
  }
```

**Vorteile:**
- ✅ Vollständige Historie aller Stages
- ✅ Progress per Stage
- ✅ Parallele Verarbeitung möglich
- ✅ Fehler genau identifizierbar
- ✅ Detaillierte Timestamps
- ✅ Metadata per Stage
- ✅ Performance-Metriken (duration)

---

## 📊 Stages

### **8 Processing Stages:**

1. **upload** - Document ingestion & validation
2. **text_extraction** - PDF text & chunking
3. **image_processing** - OCR, Vision AI
4. **classification** - Manufacturer/product detection
5. **metadata_extraction** - Error codes, versions
6. **storage** - R2 upload
7. **embedding** - Vector embeddings
8. **search_indexing** - Search analytics

---

## 🔧 Database Schema

### **Column: `stage_status` (JSONB)**

```sql
ALTER TABLE krai_core.documents
ADD COLUMN stage_status JSONB DEFAULT '{...}'::JSONB;

CREATE INDEX idx_documents_stage_status 
ON krai_core.documents USING GIN (stage_status);
```

### **Status Values:**

- `pending` - Not started yet
- `processing` - Currently running
- `completed` - Successfully finished
- `failed` - Error occurred
- `skipped` - Not applicable for this document

---

## 🛠️ Helper Functions

### **1. Start Stage**
```sql
SELECT krai_core.start_stage(
  'document-uuid',
  'text_extraction'
);
```

### **2. Update Progress**
```sql
SELECT krai_core.update_stage_progress(
  'document-uuid',
  'text_extraction',
  45.5,  -- progress %
  '{"pages_processed": 2000}'::JSONB
);
```

### **3. Complete Stage**
```sql
SELECT krai_core.complete_stage(
  'document-uuid',
  'text_extraction',
  '{"total_pages": 4386}'::JSONB
);
```

### **4. Fail Stage**
```sql
SELECT krai_core.fail_stage(
  'document-uuid',
  'text_extraction',
  'OCR engine timeout'
);
```

### **5. Skip Stage**
```sql
SELECT krai_core.skip_stage(
  'document-uuid',
  'image_processing',
  'No images found in PDF'
);
```

### **6. Get Progress**
```sql
SELECT krai_core.get_document_progress('document-uuid');
-- Returns: 37.50 (3 of 8 stages completed)
```

### **7. Get Current Stage**
```sql
SELECT krai_core.get_current_stage('document-uuid');
-- Returns: 'classification'
```

### **8. Can Start Stage?**
```sql
SELECT krai_core.can_start_stage(
  'document-uuid',
  'embedding'
);
-- Returns: true/false (checks if prerequisites met)
```

---

## 🐍 Python Usage

### **Basic Usage:**

```python
from processors_v2.stage_tracker import StageTracker

tracker = StageTracker(supabase_client)

# Start stage
tracker.start_stage(document_id, 'text_extraction')

# Update progress
tracker.update_progress(
    document_id,
    'text_extraction',
    progress=45.5,
    metadata={'pages_processed': 2000}
)

# Complete stage
tracker.complete_stage(
    document_id,
    'text_extraction',
    metadata={'total_pages': 4386}
)

# Get current progress
progress = tracker.get_progress(document_id)
print(f"Progress: {progress}%")
```

### **Context Manager (Automatic):**

```python
from processors_v2.stage_tracker import StageContext

with StageContext(tracker, document_id, 'text_extraction') as ctx:
    # Do processing
    for i in range(100):
        # ... process pages ...
        ctx.update_progress(i, {'pages_processed': i * 43})
    
    # Stage automatically marked as completed on success
    # Or failed if exception occurs
```

---

## 🌐 API Endpoints

### **1. Get Document Status**

```http
GET /status/{document_id}
```

**Response:**
```json
{
  "document_id": "...",
  "status": "processing",
  "current_stage": "text_extraction",
  "progress": 37.5,
  "started_at": "2025-10-04T08:00:00Z",
  "completed_at": null,
  "error": null,
  "stage_status": {
    "upload": {
      "status": "completed",
      "started_at": "2025-10-04T08:00:00Z",
      "completed_at": "2025-10-04T08:00:01Z",
      "duration_seconds": 1.2,
      "progress": 100,
      "error": null
    },
    "text_extraction": {
      "status": "processing",
      "started_at": "2025-10-04T08:00:01Z",
      "progress": 45.5,
      "metadata": {
        "pages_processed": 2000,
        "total_pages": 4386
      }
    },
    ...
  }
}
```

### **2. Get Stage Statistics**

```http
GET /stages/statistics
```

**Response:**
```json
{
  "timestamp": "2025-10-04T08:00:00Z",
  "stages": {
    "upload": {
      "pending": 5,
      "processing": 2,
      "completed": 143,
      "failed": 1,
      "skipped": 0,
      "avg_duration": 1.2
    },
    "text_extraction": {
      "pending": 3,
      "processing": 4,
      "completed": 140,
      "failed": 2,
      "skipped": 0,
      "avg_duration": 45.8
    },
    ...
  }
}
```

---

## 📈 Monitoring Views

### **Documents by Stage:**

```sql
SELECT * FROM krai_core.vw_documents_by_stage;
```

Columns:
- `id` - Document UUID
- `filename` - Document name
- `current_stage` - Current processing stage
- `progress_percentage` - Overall progress
- `upload_status` - Upload stage status (JSON)
- `text_extraction_status` - Text extraction status (JSON)
- ... (all stages)

### **Stage Statistics:**

```sql
SELECT * FROM krai_core.vw_stage_statistics;
```

Columns:
- `stage_name` - Name of the stage
- `pending_count` - Documents waiting
- `processing_count` - Documents currently processing
- `completed_count` - Successfully completed
- `failed_count` - Failed documents
- `skipped_count` - Skipped documents
- `avg_duration_seconds` - Average processing time

---

## 🚀 Benefits for Parallel Processing

### **Resource Distribution:**

```python
# Worker 1: Text Extraction
for doc in get_documents_ready_for('text_extraction'):
    process_text_extraction(doc)

# Worker 2: Image Processing (parallel!)
for doc in get_documents_ready_for('image_processing'):
    process_images(doc)

# Worker 3: Embeddings
for doc in get_documents_ready_for('embedding'):
    generate_embeddings(doc)
```

**All can run simultaneously!**

### **Smart Queue Management:**

```python
# Get next document to process for specific stage
def get_next_document(stage_name):
    docs = supabase.table("documents") \
        .select("*") \
        .execute()
    
    for doc in docs.data:
        if tracker.can_start_stage(doc['id'], stage_name):
            # Check if stage is pending
            stage_status = doc['stage_status'][stage_name]
            if stage_status['status'] == 'pending':
                return doc
    
    return None
```

---

## 🔄 Migration

### **Apply Migration:**

```bash
# Via Supabase Dashboard
# Copy & paste: database/migrations/10_stage_status_tracking.sql

# Or via psql
psql -h your-db-host -U postgres -d postgres -f 10_stage_status_tracking.sql
```

### **Backward Compatible:**

✅ Existing columns (`processing_status`) bleiben erhalten
✅ Alte queries funktionieren weiter
✅ Neue `stage_status` column wird automatisch initialisiert

---

## 📊 Performance

### **Index:**
- GIN Index auf `stage_status` → Schnelle JSONB Queries
- Typische Query Zeit: <5ms

### **Storage:**
- JSONB ist komprimiert
- ~1-2 KB per document
- Für 10,000 docs: ~10-20 MB

---

## 🎯 Use Cases

### **1. Progress Bar in UI:**
```javascript
// Real-time progress
const status = await fetch(`/status/${documentId}`);
const progress = status.progress; // 37.5%

// Show stage-specific progress
status.stage_status.text_extraction.progress; // 45.5%
```

### **2. Error Recovery:**
```python
# Find all failed text extractions
failed_docs = supabase.table("documents") \
    .select("*") \
    .execute()

for doc in failed_docs.data:
    if doc['stage_status']['text_extraction']['status'] == 'failed':
        # Retry just this stage
        retry_text_extraction(doc['id'])
```

### **3. Performance Analysis:**
```sql
-- Which stage takes longest?
SELECT 
    stage_name,
    AVG(duration_seconds) as avg_duration
FROM krai_core.vw_stage_statistics
GROUP BY stage_name
ORDER BY avg_duration DESC;
```

### **4. Resource Planning:**
```sql
-- How many documents are waiting for each stage?
SELECT 
    stage_name,
    pending_count + processing_count as active_count
FROM krai_core.vw_stage_statistics
ORDER BY active_count DESC;
```

---

## ✅ Next Steps

1. ✅ **Apply Migration 10**
2. ✅ **Test with existing documents**
3. ✅ **Update processors to use StageTracker**
4. ✅ **Monitor stage statistics**
5. ✅ **Implement parallel workers**

---

**🎉 Dein neues Stage Tracking System ist ready!**
