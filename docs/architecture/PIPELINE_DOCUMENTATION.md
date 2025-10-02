# 🚀 KR-AI-Engine - Complete Pipeline Documentation

## 📋 Overview

The KR-AI-Engine is a production-ready document processing pipeline that automatically extracts, analyzes, and stores technical documentation with AI-powered classification and intelligent search capabilities.

## 🏗️ Architecture

### **8-Stage Processing Pipeline:**

```
1. 📤 Upload Processor → krai_core.documents (Database only)
2. 📄 Text Processor → krai_content.chunks + krai_intelligence.chunks  
3. 🖼️ Image Processor → krai_content.images (Object Storage)
4. 🏷️ Classification Processor → krai_core.manufacturers, products, product_series
5. 📑 Metadata Processor → krai_intelligence.error_codes
6. 💾 Storage Processor → Cloudflare R2 (NUR Bilder)
7. 🔪 Text Chunking → krai_intelligence.chunks
8. 🔮 Embedding Processor → krai_intelligence.embeddings
9. ✅ Finalization → krai_system.processing_queue
```

### **Database Schemas:**

- **`krai_core`**: Core entities (documents, manufacturers, products, product_series)
- **`krai_content`**: Content storage (chunks, images, print_defects)
- **`krai_intelligence`**: AI data (chunks, embeddings, error_codes, search_analytics)
- **`krai_system`**: System data (processing_queue, audit_log, system_metrics)

## 🔧 Installation & Setup

### **Prerequisites:**
- Python 3.11+
- Ollama with models: `llama3.2:latest`, `embeddinggemma:latest`, `llava:latest`
- Supabase database
- Cloudflare R2 account
- Tesseract OCR

### **Environment Variables:**
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

# Cloudflare R2
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_ENDPOINT_URL=https://your_account_id.r2.cloudflarestorage.com
R2_PUBLIC_URL_DOCUMENTS=https://your_domain.com/documents
R2_PUBLIC_URL_ERROR=https://your_domain.com/error
R2_PUBLIC_URL_PARTS=https://your_domain.com/parts

# Ollama
OLLAMA_URL=http://localhost:11434
```

### **Installation:**
```bash
cd backend
pip install -r requirements.txt

# Install Tesseract OCR (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Start Ollama
ollama serve
ollama pull llama3.2:latest
ollama pull embeddinggemma:latest
ollama pull llava:latest
```

## 🚀 Usage

### **Complete Pipeline Test:**
```bash
cd backend
python tests/test_complete_pipeline_advanced.py
```

### **Individual Stage Tests:**
```bash
# Stage 3: Image Processor
python tests/test_stage_3_image_processor.py

# Stage 4: Classification Processor
python tests/test_stage_4_classification_processor.py

# Stage 7: Embedding Processor
python tests/test_stage_7_embedding_processor.py
```

## 🎯 Key Features

### **🔍 AI-Powered Classification:**
- Automatic manufacturer detection (HP, Konica Minolta, Canon, etc.)
- Model number extraction with normalization
- Document type classification (service manual, parts catalog, etc.)
- Language detection

### **🖼️ Advanced Image Processing:**
- PDF image extraction with format preservation
- OCR text recognition (Tesseract + EasyOCR)
- AI vision analysis (Ollama llava)
- Image deduplication by content hash
- Vector graphics detection (SVG)

### **📊 Intelligent Chunking:**
- AI-powered semantic chunking
- Document-type specific strategies
- Metadata preservation
- Foreign key relationships

### **🔮 Vector Search:**
- Embedding generation (embeddinggemma)
- Semantic search capabilities
- Performance analytics

### **💾 Object Storage:**
- Cloudflare R2 integration
- Automatic bucket management
- File deduplication
- Public URL generation

## 🔄 Data Flow Details

### **Stage 1: Upload Processor**
- File validation and hash generation
- Document metadata extraction
- Database storage (NO object storage for documents)

### **Stage 2: Text Processor**
- PDF text extraction (PyMuPDF)
- Intelligent chunking based on document type
- Content and intelligence chunk storage

### **Stage 3: Image Processor**
- Image extraction from PDFs
- OCR processing (Tesseract)
- AI vision analysis (Ollama llava)
- R2 upload with deduplication

### **Stage 4: Classification Processor**
- AI document classification
- Manufacturer normalization
- Model detection and extraction
- Features inheritance (series → product)

### **Stage 5: Metadata Processor**
- Error code pattern matching
- Version extraction
- Document metadata enrichment

### **Stage 6: Storage Processor**
- Object storage management
- File deduplication
- Storage optimization

### **Stage 7: Embedding Processor**
- Vector embedding generation
- Chunk-to-embedding mapping
- Database storage

### **Stage 8: Search Processor**
- Search index creation
- Performance analytics
- Final pipeline completion

## 🛠️ Configuration

### **Chunking Strategies:**
Located in `backend/config/chunk_settings.json`:
```json
{
  "service_manual": {
    "max_chunk_size": 2000,
    "overlap_size": 200,
    "preserve_structure": true
  }
}
```

### **Error Code Patterns:**
Located in `backend/config/error_code_patterns.json`:
```json
{
  "patterns": [
    {
      "name": "HP Error Codes",
      "regex": "Error\\s+(\\d{2,4})",
      "manufacturers": ["HP Inc."]
    }
  ]
}
```

## 📈 Performance

### **Hardware Detection:**
- Automatic GPU detection (RTX 2000+ → HIGH_PERFORMANCE)
- CPU/RAM assessment
- Model selection based on hardware

### **Resource Requirements:**
- **Low Resource**: upload, metadata, storage (1-2 instances)
- **Medium Resource**: text, classification, search (2-3 instances)
- **High Resource**: image, embedding (3-5 instances)

### **Deduplication:**
- Document deduplication by file hash
- Image deduplication by content hash
- Manufacturer name normalization
- Model number standardization

## 🔒 Security & Best Practices

### **Database Security:**
- Row Level Security (RLS) policies
- Supabase authentication
- Audit logging for all operations

### **Object Storage:**
- Secure R2 access keys
- Public URL management
- File hash verification

### **Error Handling:**
- Comprehensive error logging
- Graceful fallbacks
- Processing rollback on failures

## 📊 Monitoring & Analytics

### **Progress Tracking:**
- Real-time progress display
- ETA calculation
- Performance metrics
- Stage-by-stage status

### **Search Analytics:**
- Query tracking
- Success rates
- Response times
- Usage statistics

## 🧪 Testing

### **Test Structure:**
```
backend/tests/
├── test_complete_pipeline_advanced.py    # Full pipeline test
├── test_stage_3_image_processor.py       # Image processing
├── test_stage_4_classification_processor.py # Classification
├── test_stage_7_embedding_processor.py   # Embeddings
├── test_stage_8_search_processor.py      # Search
├── test_document_deduplication.py        # Deduplication
├── test_manufacturer_normalization.py    # Manufacturer logic
└── advanced_progress_tracker.py          # Progress tracking
```

### **Running Tests:**
```bash
# Full pipeline test
python tests/test_complete_pipeline_advanced.py

# Individual stage tests
python tests/test_stage_*_processor.py

# Deduplication test
python tests/test_document_deduplication.py
```

## 🚨 Troubleshooting

### **Common Issues:**

1. **UnicodeEncodeError**: Remove Unicode characters from print statements
2. **Ollama Connection Failed**: Ensure Ollama is running and models are pulled
3. **Tesseract Not Found**: Install Tesseract OCR and set PATH
4. **R2 Upload Failed**: Check credentials and bucket permissions
5. **Database Connection**: Verify Supabase URL and key

### **Logs:**
- Database operations: `Database - INFO`
- Storage operations: `Storage - INFO`
- AI operations: `AI - INFO`
- Processing: `[processor_name] - INFO`

## 🔄 Updates & Maintenance

### **Model Updates:**
```bash
ollama pull llama3.2:latest
ollama pull embeddinggemma:latest
ollama pull llava:latest
```

### **Database Migrations:**
- Automatic schema detection
- View creation for public API
- Index optimization

### **Performance Tuning:**
- GPU acceleration monitoring
- Memory usage optimization
- Batch processing for large documents

---

**🎯 Ready for Production!** The KR-AI-Engine is fully functional with comprehensive error handling, deduplication, and monitoring capabilities.
