# 🚀 KR-AI-Engine - Manual2Vector

**Intelligent Document Processing Pipeline with AI-Powered Classification and Vector Search**

## 🎯 Overview

KR-AI-Engine is a comprehensive document processing system that automatically extracts, analyzes, and indexes technical manuals and service documents. It combines advanced AI models with efficient data processing to create a searchable knowledge base from PDF documents.

## ✨ Key Features

### 🤖 **AI-Powered Processing**
- **Smart Document Classification** using Ollama LLM models
- **Intelligent Text Chunking** with semantic analysis
- **Image Recognition** and OCR with vision models
- **Vector Embeddings** for semantic search
- **Manufacturer & Model Detection** with normalization

### 📊 **8-Stage Processing Pipeline**
1. **Upload Processor** - Document ingestion and deduplication
2. **Text Processor** - Smart chunking with AI analysis
3. **Image Processor** - Original format preservation, OCR, AI vision
4. **Classification Processor** - Manufacturer/product detection
5. **Metadata Processor** - Error codes and version extraction
6. **Storage Processor** - Cloudflare R2 object storage
7. **Embedding Processor** - Vector embeddings for search
8. **Search Processor** - Search analytics and indexing

### 🏗️ **Production-Ready Architecture**
- **Supabase Database** with pgvector support
- **Cloudflare R2** object storage
- **GPU Acceleration** for AI models
- **Parallel Processing** for optimal performance
- **Comprehensive Monitoring** and logging

## 🚀 Quick Start

### **Prerequisites**
- Python 3.9+
- NVIDIA GPU (recommended)
- 16+ GB RAM
- Supabase account
- Cloudflare R2 account
- Ollama installed

### **Installation**
```bash
# Clone repository
git clone https://github.com/Kunze-Ritter/Manual2Vector.git
cd Manual2Vector

# Create virtual environment
python -m venv krai_env
source krai_env/bin/activate  # Linux/macOS
# or krai_env\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# Install Ollama models
ollama pull llama3.2:latest
ollama pull embeddinggemma:latest
ollama pull llava:latest

# Run the application
cd backend
python tests/krai_master_pipeline.py
```

📖 **For detailed installation instructions, see [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)**

## 🎮 Usage

### **Master Pipeline Interface**
```bash
python tests/krai_master_pipeline.py

# Menu Options:
# 1. Status Check - View processing status
# 2. Pipeline Reset - Process failed documents
# 3. Hardware Waker - Process new PDFs
# 4. Single Document - Process one file
# 5. Batch Processing - Process multiple files
# 6. Exit
```

### **Processing Documents**
```bash
# Place PDF files in service_documents/ directory
# Run pipeline reset to process failed documents
# Or use batch processing for new documents
```

## 📊 Database Schema

### **Core Schemas**
- **`krai_core`**: Documents, manufacturers, products, product_series
- **`krai_content`**: Chunks, images, print_defects  
- **`krai_intelligence`**: Embeddings, error_codes, search_analytics
- **`krai_system`**: Processing_queue, audit_log, system_metrics

### **Key Features**
- **Deduplication** at document, image, and chunk levels
- **Vector Search** with pgvector embeddings
- **Manufacturer Normalization** (HP → HP Inc.)
- **Model Detection** for all variants and options
- **Error Code Extraction** with pattern matching

## 🔧 Configuration

### **Environment Variables**
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Cloudflare R2
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# System
MAX_WORKERS=8
CHUNK_SIZE=1000
LOG_LEVEL=INFO
```

### **Hardware Detection**
The system automatically detects:
- CPU cores and threads
- RAM capacity
- GPU type and VRAM
- Performance tier selection
- Optimal model configuration

## 📈 Performance

### **Optimization Features**
- **Smart Stage Parallelization** - Different PDFs in different stages
- **GPU Acceleration** - NVIDIA CUDA support
- **Streaming Processing** - Memory-efficient chunking
- **Batch Operations** - Database optimization
- **Resource Monitoring** - Real-time performance tracking

### **Expected Performance**
- **CPU**: 12+ cores utilization
- **GPU**: 80%+ VRAM usage during AI processing
- **RAM**: Optimized streaming processing
- **Throughput**: 10-50 documents/hour (depending on hardware)

## 🛠️ Technical Stack

### **Backend**
- **FastAPI** - Web framework
- **Supabase** - Database and authentication
- **Ollama** - Local AI model serving
- **PyMuPDF** - PDF processing
- **PyTorch** - AI/ML framework
- **Tesseract OCR** - Text recognition

### **AI Models**
- **llama3.2:latest** - Text classification (2.0 GB)
- **embeddinggemma:latest** - Vector embeddings (621 MB)
- **llava:latest** - Vision analysis (4.7 GB)

### **Storage**
- **Supabase PostgreSQL** - Relational data with pgvector
- **Cloudflare R2** - Object storage for images
- **Local Processing** - Temporary file handling

## 📁 Project Structure

```
KRAI-minimal/
├── backend/
│   ├── config/           # Configuration files
│   ├── core/             # Base classes and data models
│   ├── processors/       # 8-stage processing pipeline
│   ├── services/         # Database, AI, storage services
│   ├── utils/            # Utility functions
│   ├── tests/            # Test scripts and master pipeline
│   └── requirements.txt  # Python dependencies
├── service_documents/    # PDF input directory
├── INSTALLATION_GUIDE.md # Detailed setup instructions
└── README.md            # This file
```

## 🔍 Monitoring

### **Real-time Status**
- Document processing progress
- Stage-by-stage completion
- Hardware utilization (CPU/GPU/RAM)
- Error tracking and logging
- Performance metrics

### **Health Checks**
- Database connectivity
- Ollama service status
- R2 storage access
- GPU availability
- Model loading status

## 🚨 Troubleshooting

### **Common Issues**
1. **GPU not detected** - Check CUDA installation
2. **Ollama connection failed** - Verify service is running
3. **Database errors** - Check Supabase credentials
4. **Memory issues** - Reduce batch size or chunk size
5. **OCR failures** - Verify Tesseract installation

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python tests/krai_master_pipeline.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local AI model serving
- **Supabase** for database infrastructure
- **Cloudflare** for object storage
- **PyMuPDF** for PDF processing
- **Hugging Face** for AI models

## 📞 Support

- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - See INSTALLATION_GUIDE.md
- **Email** - [Your contact information]

---

**🎉 Ready to transform your documents into intelligent, searchable knowledge!**