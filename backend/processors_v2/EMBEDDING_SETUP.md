# 🔍 Embedding Setup Guide

This guide helps you set up the embedding processor for semantic search.

---

## ⚠️ Why Are Embeddings Important?

**Embeddings enable semantic search!**

Without embeddings:
- ❌ No similarity search
- ❌ No "find similar documents"
- ❌ No intelligent search results
- ❌ Only keyword-based search

With embeddings:
- ✅ Semantic similarity search
- ✅ "Find documents similar to this"
- ✅ Context-aware search results
- ✅ Better search experience

**→ Embeddings are REQUIRED for production use!**

---

## 📋 Requirements

### 1. **Ollama** (Local AI Server)
- Runs the embedding model locally
- Fast and private
- No API costs

### 2. **embeddinggemma Model**
- 768-dimensional embeddings
- Optimized for semantic search
- Good balance of speed and quality

### 3. **Supabase with pgvector**
- Stores embeddings
- Vector similarity search
- Already configured in your database

---

## 🚀 Setup Instructions

### Step 1: Install Ollama

**Windows:**
```powershell
# Download from: https://ollama.ai/download
# Or use winget:
winget install Ollama.Ollama
```

**Linux/Mac:**
```bash
curl https://ollama.ai/install.sh | sh
```

### Step 2: Start Ollama Service

```bash
ollama serve
```

**Note:** On Windows, Ollama usually runs as a background service automatically.

### Step 3: Pull the Embedding Model

```bash
ollama pull embeddinggemma
```

This downloads the `embeddinggemma` model (~274MB).

### Step 4: Verify Configuration

```bash
cd backend/processors_v2
python test_embedding_config.py
```

**Expected output:**
```
✅ EMBEDDING PROCESSOR IS FULLY CONFIGURED!
   Ready to generate embeddings for semantic search.

🧪 Testing embedding generation...
✅ Test embedding generated successfully!
   • Dimension: 768
   • Sample values: [0.123, -0.456, 0.789]
```

---

## 🔧 Troubleshooting

### Problem: "Ollama is not available"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# Check if model is installed:
ollama list

# If embeddinggemma not in list:
ollama pull embeddinggemma
```

### Problem: "Model embeddinggemma not found"

**Solution:**
```bash
# Pull the model:
ollama pull embeddinggemma

# Wait for download to complete, then verify:
ollama list
```

### Problem: "Supabase client not configured"

**Solution:**
- Check your `.env` file
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are set
- Make sure supabase_client is passed to DocumentProcessor

### Problem: "Connection refused to localhost:11434"

**Solutions:**
1. Ollama not running → `ollama serve`
2. Different port → Set `OLLAMA_URL` in .env
3. Firewall blocking → Allow localhost connections

---

## 🧪 Test Embedding Generation

### Quick Test

```python
from processors_v2.embedding_processor import EmbeddingProcessor

processor = EmbeddingProcessor()

if processor.is_configured():
    # Test embedding
    text = "This is a test sentence"
    embedding = processor._generate_embedding(text)
    print(f"✅ Generated {len(embedding)}-dimensional embedding")
else:
    print("❌ Not configured")
    status = processor.get_configuration_status()
    print(status)
```

### Full Test with Script

```bash
python backend/processors_v2/test_embedding_config.py
```

---

## 📊 Configuration Check

The embedding processor checks configuration on startup:

```python
# In your processing pipeline:
emb_status = processor.get_configuration_status()

if emb_status['is_configured']:
    print("✅ Ready to generate embeddings")
else:
    print("❌ Configuration problem:")
    print(f"  • Ollama: {emb_status['ollama_available']}")
    print(f"  • Supabase: {emb_status['supabase_configured']}")
```

---

## ⚙️ Configuration Options

### Environment Variables

```bash
# .env file
OLLAMA_URL=http://localhost:11434  # Ollama API URL
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key-here
```

### Code Configuration

```python
from processors_v2.embedding_processor import EmbeddingProcessor

processor = EmbeddingProcessor(
    supabase_client=supabase,
    ollama_url="http://localhost:11434",
    model_name="embeddinggemma",
    batch_size=100,
    embedding_dimension=768
)
```

---

## 🎯 Expected Performance

With proper configuration:
- **Speed:** ~100-200 chunks/second
- **Dimension:** 768D vectors
- **Storage:** ~3KB per chunk (768 floats * 4 bytes)
- **Quality:** Excellent for semantic search

Example output:
```
INFO     Generating embeddings for 96 chunks...
INFO     Processing batch 1/1 (96 chunks)...
SUCCESS  Created 96 embeddings in 0.5s (192.0 chunks/s)
```

---

## 📝 Integration Checklist

Before processing documents:

- [ ] Ollama is installed
- [ ] Ollama service is running (`ollama serve`)
- [ ] embeddinggemma model is installed (`ollama pull embeddinggemma`)
- [ ] Supabase credentials are in .env
- [ ] Test script passes (`python test_embedding_config.py`)
- [ ] Pipeline shows "✅ Embedding processor configured"

---

## 🚨 Production Checklist

For production use:

- [ ] Ollama runs as a system service (auto-start)
- [ ] Sufficient RAM (4GB+ recommended for embeddings)
- [ ] Supabase pgvector extension enabled
- [ ] Monitoring for Ollama uptime
- [ ] Fallback handling if embeddings fail

---

## 📚 Related Documentation

- [Ollama Documentation](https://github.com/ollama/ollama)
- [embeddinggemma Model](https://ollama.ai/library/embeddinggemma)
- [Supabase pgvector Guide](https://supabase.com/docs/guides/ai/vector-columns)

---

## ❓ FAQ

**Q: Can I use a different embedding model?**
A: Yes, change `model_name` parameter. Models: `embeddinggemma`, `nomic-embed-text`, `mxbai-embed-large`

**Q: What if Ollama is down during processing?**
A: Embeddings will be skipped with a warning. Documents are still processed, but semantic search won't work.

**Q: How much disk space do embeddings need?**
A: ~3KB per chunk. For 10,000 chunks = ~30MB.

**Q: Can I run Ollama on a different machine?**
A: Yes, set `OLLAMA_URL=http://other-machine:11434` in .env

**Q: Do I need a GPU?**
A: No, CPU is fine for embeddings. GPU speeds it up but isn't required.

---

## ✅ Success Criteria

You'll know it's working when you see:

```
🔍 CHECKING EMBEDDING CONFIGURATION...
✅ Embedding processor configured and ready
   • Ollama: http://localhost:11434
   • Model: embeddinggemma (768D)

INFO     Generating embeddings for 96 chunks...
SUCCESS  Created 96 embeddings in 0.8s (120.0 chunks/s)

📦 Extracted:
   ...
   Embeddings: 96  ← This should appear!
```

**If you see this → Everything is working! 🎉**
