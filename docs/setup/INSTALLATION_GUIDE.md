# 🚀 KR-AI-Engine - Complete Installation Guide

## 📋 System Requirements

### **Hardware Requirements:**
- **CPU**: 8+ cores recommended (16 cores optimal)
- **RAM**: 16+ GB recommended (32+ GB optimal)
- **GPU**: NVIDIA GPU with CUDA support (8+ GB VRAM recommended)
- **Storage**: 50+ GB free space for models and data

### **Software Requirements:**
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS
- **Python**: 3.9+ (3.11 recommended)
- **Git**: Latest version
- **Docker**: Optional but recommended

---

## 🔧 Step 1: System Dependencies

### **Windows:**
```bash
# Install Python 3.11
# Download from: https://www.python.org/downloads/

# Install Git
# Download from: https://git-scm.com/downloads

# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR

# Install Visual Studio Build Tools (for some Python packages)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### **Linux (Ubuntu):**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Install system dependencies
sudo apt install tesseract-ocr tesseract-ocr-deu libtesseract-dev -y
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 -y
sudo apt install build-essential cmake pkg-config -y

# Install Git
sudo apt install git -y
```

### **macOS:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 tesseract git cmake
```

---

## 📥 Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/Kunze-Ritter/Manual2Vector.git
cd Manual2Vector

# Or if you have SSH configured:
git clone git@github.com:Kunze-Ritter/Manual2Vector.git
cd Manual2Vector
```

---

## 🐍 Step 3: Python Environment Setup

```bash
# Create virtual environment
python -m venv krai_env

# Activate virtual environment

# Windows:
krai_env\Scripts\activate

# Linux/macOS:
source krai_env/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

---

## 📦 Step 4: Install Python Dependencies

```bash
# Install all dependencies
pip install -r backend/requirements.txt

# If you encounter issues with specific packages, install them individually:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers
pip install supabase
pip install fastapi uvicorn
pip install PyMuPDF
pip install Pillow
pip install pytesseract
pip install easyocr
pip install psutil
pip install python-dotenv
pip install httpx
pip install boto3
pip install ollama
```

---

## 🔑 Step 5: Environment Configuration

### **Create `.env` file in the backend directory:**

```bash
# Navigate to backend directory
cd backend

# Create .env file
touch .env  # Linux/macOS
# or create manually on Windows
```

### **Add the following to `.env`:**

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_DOCUMENTS=krai-documents-images
R2_BUCKET_ERRORS=krai-error-images
R2_BUCKET_PARTS=krai-parts-images

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# System Configuration
LOG_LEVEL=INFO
MAX_WORKERS=8
CHUNK_SIZE=1000
```

---

## 🤖 Step 6: Install and Configure Ollama

### **Install Ollama:**
```bash
# Windows/Linux/macOS
# Download from: https://ollama.ai/download

# Or using curl (Linux/macOS):
curl -fsSL https://ollama.ai/install.sh | sh
```

### **Start Ollama Service:**
```bash
# Start Ollama service
ollama serve

# In another terminal, pull required models:
ollama pull llama3.2:latest      # Text classification (2.0 GB)
ollama pull embeddinggemma:latest # Embeddings (621 MB)
ollama pull llava:latest         # Vision analysis (4.7 GB)

# Verify models are installed:
ollama list
```

---

## 🗄️ Step 7: Database Setup (Supabase)

### **Create Supabase Project:**
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Copy URL and anon key to `.env` file

### **Database Schema:**
The database schema is automatically created by the application. The following schemas are used:
- `krai_core`: Documents, manufacturers, products, product_series
- `krai_content`: Chunks, images, print_defects
- `krai_intelligence`: Embeddings, error_codes, search_analytics
- `krai_system`: Processing_queue, audit_log, system_metrics

---

## ☁️ Step 8: Cloudflare R2 Setup

### **Create R2 Buckets:**
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to R2 Object Storage
3. Create three buckets:
   - `krai-documents-images`
   - `krai-error-images`
   - `krai-parts-images`
4. Configure public access if needed
5. Create API token with R2 permissions
6. Add credentials to `.env` file

---

## 🧪 Step 9: Test Installation

```bash
# Navigate to backend directory
cd backend

# Test hardware detection
python -c "
import sys
sys.path.append('.')
from config.ai_config import AIConfig
config = AIConfig()
print('Hardware Detection Test:')
print(f'CPU Cores: {config.cpu_count}')
print(f'RAM: {config.ram_gb:.1f} GB')
print(f'GPU: {config.gpu_name}')
print(f'Recommended Tier: {config.performance_tier}')
"

# Test database connection
python -c "
import sys
sys.path.append('.')
from services.database_service import DatabaseService
import asyncio

async def test_db():
    db = DatabaseService()
    await db.initialize()
    health = await db.health_check()
    print('Database Health:', health)

asyncio.run(test_db())
"

# Test Ollama connection
python -c "
import sys
sys.path.append('.')
from services.ai_service import AIService
import asyncio

async def test_ollama():
    ai = AIService()
    await ai.initialize()
    print('AI Service initialized successfully')

asyncio.run(test_ollama())
"
```

---

## 🚀 Step 10: Run the Application

### **Option 1: Master Pipeline (Recommended)**
```bash
cd backend
python tests/krai_master_pipeline.py
```

### **Option 2: Individual Components**
```bash
# Test single document processing
cd backend
python -c "
import sys
sys.path.append('.')
from tests.krai_master_pipeline import KRMasterPipeline
import asyncio

async def test_single():
    pipeline = KRMasterPipeline()
    await pipeline.initialize_services()
    # Process a single document
    result = await pipeline.process_document_remaining_stages(
        'document_id', 'filename.pdf', 'path/to/file.pdf'
    )
    print('Processing result:', result)

asyncio.run(test_single())
"
```

---

## 📊 Step 11: Monitor Performance

### **Hardware Monitoring:**
```bash
# Monitor GPU usage (NVIDIA)
nvidia-smi

# Monitor system resources
htop  # Linux/macOS
# or Task Manager on Windows
```

### **Application Logs:**
```bash
# Logs are written to console and can be redirected:
python tests/krai_master_pipeline.py > pipeline.log 2>&1
```

---

## 🔧 Troubleshooting

### **Common Issues:**

#### **1. CUDA/GPU Issues:**
```bash
# Check CUDA installation
nvidia-smi

# Reinstall PyTorch with CUDA support
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### **2. Tesseract OCR Issues:**
```bash
# Windows: Add Tesseract to PATH
# Linux: Install language packs
sudo apt install tesseract-ocr-deu tesseract-ocr-eng

# Test Tesseract
tesseract --version
```

#### **3. Ollama Connection Issues:**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve

# Check models
ollama pull llama3.2:latest
```

#### **4. Database Connection Issues:**
```bash
# Verify Supabase credentials in .env
# Test connection:
curl -H "apikey: YOUR_SUPABASE_KEY" "YOUR_SUPABASE_URL/rest/v1/"
```

#### **5. Memory Issues:**
```bash
# Reduce batch size in configuration
# Monitor memory usage:
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().percent}%')"
```

---

## 📈 Performance Optimization

### **GPU Optimization:**
- Ensure NVIDIA drivers are up to date
- Use CUDA 12.1+ for best performance
- Monitor VRAM usage during processing

### **CPU Optimization:**
- Adjust `MAX_WORKERS` in `.env` based on CPU cores
- Use parallel processing for multiple documents

### **Memory Optimization:**
- Process documents in smaller batches
- Monitor RAM usage and adjust `CHUNK_SIZE`

---

## 🎯 Usage Examples

### **Process Single Document:**
```bash
cd backend
python tests/krai_master_pipeline.py
# Choose Option 3: Single Document Processing
```

### **Process Multiple Documents:**
```bash
cd backend
python tests/krai_master_pipeline.py
# Choose Option 2: Pipeline Reset (for failed documents)
# or Option 3: Batch Processing (for new documents)
```

### **Monitor Pipeline Status:**
```bash
cd backend
python tests/krai_master_pipeline.py
# Choose Option 1: Status Check
```

---

## 📚 Additional Resources

### **Documentation:**
- [Supabase Documentation](https://supabase.com/docs)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [Ollama Documentation](https://ollama.ai/docs)
- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)

### **Support:**
- Check GitHub Issues for common problems
- Review application logs for error details
- Monitor system resources during processing

---

## ✅ Verification Checklist

Before starting production processing, verify:

- [ ] Python 3.9+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list`)
- [ ] Ollama service running (`ollama list`)
- [ ] Required models downloaded (llama3.2, embeddinggemma, llava)
- [ ] Supabase connection working
- [ ] R2 buckets created and accessible
- [ ] Tesseract OCR installed and in PATH
- [ ] GPU detected and CUDA working
- [ ] `.env` file configured with all credentials
- [ ] Test run successful

---

**🎉 Congratulations! Your KR-AI-Engine is now ready for production use!**

For questions or support, please refer to the GitHub repository or create an issue.
