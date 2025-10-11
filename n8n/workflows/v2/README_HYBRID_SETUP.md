# KRAI Technician Agent V2.1 - Hybrid Setup Guide

## 🎯 **Architecture Overview**

```
User Question
    ↓
AI Agent (Ollama llama3.1:8b)
    ├─ Memory: Postgres (conversation history)
    ├─ Tools (Structured Data):
    │   ├─ search_error_codes → SQL Database
    │   ├─ search_parts → SQL Database
    │   └─ search_videos → SQL Database
    └─ Vector Store (Unstructured Data):
        └─ query_service_manuals → PDF Embeddings
```

## 📋 **Prerequisites**

### **1. Ollama Models**
```bash
# Pull required models
ollama pull llama3.1:8b          # Main agent model
ollama pull nomic-embed-text     # Embedding model (768 dimensions)
```

### **2. Vector Store (Choose One)**

#### **Option A: Pinecone (Recommended for Testing)**
1. Create free account: https://pinecone.io
2. Create index:
   - Name: `krai-manuals`
   - Dimension: `768`
   - Metric: `cosine`
3. Get API key from dashboard
4. Add to n8n credentials

#### **Option B: Supabase pgvector (Self-hosted)**
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE service_manuals_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for similarity search
CREATE INDEX ON service_manuals_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### **3. Backend API**
Ensure your backend is running with these endpoints:
- `POST /api/v1/error-codes/search`
- `POST /api/v1/parts/search`
- `POST /api/v1/videos/search`

## 🚀 **Setup Steps**

### **Step 1: Import Workflows**

1. **Import Main Workflow:**
   - n8n → Import → `KRAI_Agent_Hybrid_Main.json`
   - This is the production chat workflow

2. **Import Setup Workflow:**
   - n8n → Import → `KRAI_Vector_Store_Setup.json`
   - This is for one-time PDF embedding

### **Step 2: Configure Credentials**

#### **Supabase (for PDF storage)**
- n8n → Credentials → Add Supabase
- URL: Your Supabase URL
- API Key: `service_role` key

#### **Pinecone (if using)**
- n8n → Credentials → Add Pinecone
- API Key: From Pinecone dashboard
- Environment: Your Pinecone environment

#### **Ollama**
- n8n → Credentials → Add Ollama
- Base URL: `http://ollama:11434` (if using Docker)

#### **Postgres (for memory)**
- Already configured in previous setup
- Uses `n8n_chat_histories` view

### **Step 3: Prepare Service Manuals**

1. **Upload PDFs to Supabase:**
   ```bash
   # Upload to bucket: service-manuals
   # Naming convention: Manufacturer_Model_Manual.pdf
   
   Examples:
   - Lexmark_CX963_ServiceManual.pdf
   - KonicaMinolta_bizhubC750i_ServiceManual.pdf
   - Lexmark_CX860_ServiceManual.pdf
   ```

2. **Run Vector Store Setup:**
   - Open `KRAI Vector Store Setup` workflow
   - Click "Test workflow"
   - Wait for processing (1-2 min per PDF)
   - Check logs for success

### **Step 4: Test Main Workflow**

1. **Activate Main Workflow:**
   - Open `KRAI Technician Agent V2.1 - Hybrid (Main)`
   - Click "Activate"

2. **Open Chat:**
   - Click "Open Chat" button
   - Test with these queries:

#### **Test 1: Error Code (Uses Tools)**
```
Lexmark CX963 Fehlercode 88.10
```

**Expected:**
- ✅ Calls `search_error_codes`
- ✅ Calls `search_parts`
- ✅ Calls `query_service_manuals`
- ✅ Calls `search_videos`
- ✅ Returns structured response with all info

#### **Test 2: General Question (Uses Vector Store)**
```
Wie tausche ich die Fuser Unit beim CX963?
```

**Expected:**
- ✅ Calls `query_service_manuals` (semantic search)
- ✅ Calls `search_videos`
- ✅ Returns step-by-step instructions from manual

#### **Test 3: Parts Question (Uses Tools)**
```
Welche Fuser Unit passt zum CX963?
```

**Expected:**
- ✅ Calls `search_parts`
- ✅ Returns part number and compatibility

#### **Test 4: Context Awareness (Uses Memory)**
```
1. "Ich habe einen Lexmark CX963"
2. "Fehlercode 88.10"
3. "Welche Teile brauche ich?"
```

**Expected:**
- ✅ Remembers context (CX963, 88.10)
- ✅ Calls tools with context
- ✅ No need to repeat device info

## 🔍 **Debugging**

### **Tools Not Called?**

1. **Check Ollama Model:**
   ```bash
   ollama list
   # Must be llama3.1:8b or higher!
   ```

2. **Check Agent Options:**
   - Agent Node → Options
   - Max Iterations: 5
   - Return Intermediate Steps: ON

3. **Check Tool Descriptions:**
   - Each tool must have clear description
   - Must include parameter examples

### **Vector Store Not Working?**

1. **Check Embeddings:**
   ```bash
   # Test embedding model
   ollama run nomic-embed-text "test"
   ```

2. **Check Vector Store:**
   - Pinecone: Check dashboard for vectors
   - Supabase: `SELECT COUNT(*) FROM service_manuals_embeddings;`

3. **Re-run Setup:**
   - Delete old embeddings
   - Run setup workflow again

### **Memory Issues?**

1. **Check Database:**
   ```sql
   SELECT * FROM public.n8n_chat_histories LIMIT 5;
   ```

2. **Check Triggers:**
   ```sql
   SELECT * FROM krai_agent.memory ORDER BY created_at DESC LIMIT 5;
   ```

3. **Clear Memory:**
   ```sql
   DELETE FROM krai_agent.memory WHERE session_id = 'your-session-id';
   ```

## 📊 **Performance Tuning**

### **Ollama Settings**
```bash
# In docker-compose.yml
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_FLASH_ATTENTION=1
```

### **Agent Settings**
- Temperature: 0.1 (more deterministic)
- Max Iterations: 5 (balance speed/accuracy)
- Context Window: 10 messages

### **Vector Store Settings**
- Chunk Size: 2000 chars (optimal for technical docs)
- Chunk Overlap: 200 chars (maintains context)
- Top K: 3 (number of results to return)

## 🎯 **Expected Tool Usage**

| User Query | Tools Called | Order |
|------------|--------------|-------|
| "Fehlercode C-9402" | `search_error_codes` → `search_parts` → `query_service_manuals` → `search_videos` | 1-4 |
| "Wie tausche ich die Trommel?" | `query_service_manuals` → `search_videos` | 1-2 |
| "Welche Teile für CX963?" | `search_parts` | 1 |
| "Zeig mir ein Video" | `search_videos` | 1 |

## 📝 **Next Steps**

1. ✅ Test all scenarios from `TEST_SCENARIOS.md`
2. ✅ Add more service manuals to vector store
3. ✅ Fine-tune prompts based on results
4. ✅ Monitor tool usage in production
5. ✅ Collect feedback from technicians

## 🆘 **Support**

If issues persist:
1. Check n8n execution logs
2. Check Ollama logs: `docker logs ollama`
3. Check backend logs: `docker logs backend`
4. Review `TEST_SCENARIOS.md` for expected outputs

---

**Ready to test!** 🚀

Start with the main workflow and test with: `"Lexmark CX963 Fehlercode 88.10"`
