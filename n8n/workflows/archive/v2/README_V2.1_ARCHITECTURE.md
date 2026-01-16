# KRAI Technician Agent V2.1 - Architecture Guide

---

## ⚠️ **DEPRECATION NOTICE - SUPABASE REFERENCES**

**This document contains historical Supabase references that are NO LONGER VALID.**

**Current Architecture (as of November 2024):**
- ✅ **PostgreSQL-only** (direct asyncpg connection pools)
- ❌ **Supabase** (deprecated and removed)
- ❌ **PostgREST** (deprecated and removed)

**For current setup instructions, see:**
- `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` - Migration guide
- `DOCKER_SETUP.md` - Current PostgreSQL setup
- `DATABASE_SCHEMA.md` - Current schema reference

**This document is preserved for historical reference only.**

---

## 🎯 **Correct Multi-Agent Architecture**

### **Key Discovery: Agent Tools ARE Sub-Agents!**

In n8n, `@n8n/n8n-nodes-langchain.agentTool` nodes have **built-in agent functionality**. You don't need separate Agent nodes for sub-agents!

## 📐 **Architecture Overview**

```
User Question
    ↓
Main Coordinator Agent
├─ Main LLM (llama3.2:latest)
├─ Postgres Chat Memory
└─ 4 Specialized Agent Tools:
    │
    ├─ error_code_specialist (Agent Tool)
    │   ├─ Error Code LLM (llama3.1:8b)
    │   ├─ Specialized Prompt
    │   └─ Search Error Codes (HTTP Tool)
    │
    ├─ parts_specialist (Agent Tool)
    │   ├─ Parts LLM (llama3.2:latest)
    │   ├─ Specialized Prompt
    │   └─ Search Parts (HTTP Tool)
    │
    ├─ video_specialist (Agent Tool)
    │   ├─ Video LLM (llama3.1:8b)
    │   ├─ Specialized Prompt
    │   └─ Search Videos (HTTP Tool)
    │
    └─ manual_specialist (Agent Tool)
        ├─ Manual LLM (llama3.2:latest)
        ├─ Specialized Prompt
        └─ Answer questions with vector store (Tool)
            ├─ Search Manuals Vector Store (PostgreSQL)
            ├─ Embeddings (embeddinggemma:latest)
            └─ Ollama Chat Model (for vector store queries)
```

## 🔧 **Component Breakdown**

### **1. Main Coordinator Agent**

**Type:** `@n8n/n8n-nodes-langchain.agent`

**Role:** Orchestrates specialists and synthesizes responses

**Prompt Strategy:**
- Extract information (manufacturer, model, error code)
- Decide which specialists to call
- Synthesize responses into coherent answer

**Key Responsibilities:**
- Context management (remembers conversation)
- Tool selection (calls right specialists)
- Response synthesis (combines specialist outputs)

---

### **2. Agent Tools (Specialists)**

Each Agent Tool is a **complete sub-agent** with:
1. **Name** → Tool identifier for Main Agent
2. **Description** → When to use this specialist
3. **Input Schema** → Expected parameters (JSON)
4. **System Message** → Specialized prompt
5. **LLM** → Own reasoning capability
6. **Tool** → Data access (HTTP or Vector Store)

---

#### **2.1 error_code_specialist**

**Type:** `@n8n/n8n-nodes-langchain.agentTool`

**When to call:**
- User mentions error code (e.g., "88.10", "C-9402")

**Input:**
```json
{
  "error_code": "88.10",
  "manufacturer": "Lexmark",
  "model": "CX963"
}
```

**Specialized Prompt:**
```
You are an Error Code Diagnosis Specialist.

Task: Diagnose error codes precisely using search_database tool.

Output Format (German):
**Fehlercode:** [code]
**Beschreibung:** [what it means]
**Ursache:** [root cause]
**Betroffene Komponenten:** [affected parts]
**Lösung:** [solution steps]
**Quelle:** [document, page]

Rules:
✅ ALWAYS use the tool
✅ Be precise and technical
✅ Cite sources
❌ NEVER make up information
```

**LLM:** llama3.1:8b (temp: 0.1)

**Tool:** HTTP Request → `POST /api/v1/error-codes/search`

---

#### **2.2 parts_specialist**

**Type:** `@n8n/n8n-nodes-langchain.agentTool`

**When to call:**
- User asks about parts, replacements, part numbers

**Input:**
```json
{
  "search_term": "Fuser Unit",
  "manufacturer": "Lexmark",
  "model": "CX963"
}
```

**Specialized Prompt:**
```
You are a Spare Parts Specialist.

Task: Find exact part numbers using search_database tool.

Output Format (German):
**Ersatzteil:** [part name]
**Teilenummer:** [part number]
**Beschreibung:** [what it does]
**Kompatible Modelle:** [compatible devices]
**Quelle:** [catalog, page]

Rules:
✅ ALWAYS use the tool
✅ Provide exact part numbers
✅ List compatible models
❌ NEVER make up part numbers
```

**LLM:** llama3.2:latest (temp: 0.1)

**Tool:** HTTP Request → `POST /api/v1/parts/search`

---

#### **2.3 video_specialist**

**Type:** `@n8n/n8n-nodes-langchain.agentTool`

**When to call:**
- User needs visual guidance or asks for videos

**Input:**
```json
{
  "search_term": "Fuser Unit replacement",
  "manufacturer": "Lexmark",
  "model": "CX963"
}
```

**Specialized Prompt:**
```
You are a Video Tutorial Specialist.

Task: Find relevant repair videos using search_database tool.

Output Format (German):
**Video:** [title]
**Link:** [URL]
**Beschreibung:** [what the video shows]
**Dauer:** [length]

Rules:
✅ ALWAYS use the tool
✅ Provide working video links
✅ Describe what the video shows
❌ NEVER make up video links
```

**LLM:** llama3.1:8b (temp: 0.1)

**Tool:** HTTP Request → `POST /api/v1/videos/search`

---

#### **2.4 manual_specialist**

**Type:** `@n8n/n8n-nodes-langchain.agentTool`

**When to call:**
- User asks "how to" questions
- Needs step-by-step instructions

**Input:**
```json
{
  "query": "How to replace fuser unit",
  "manufacturer": "Lexmark",
  "model": "CX963"
}
```

**Specialized Prompt:**
```
You are a Service Manual Specialist.

Task: Provide step-by-step procedures using search_manuals tool.

Output Format (German):
**Anleitung:** [procedure name]

**Schritte:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Hinweise:** [important notes, warnings]
**Werkzeug:** [required tools]
**Quelle:** [manual, page]

Rules:
✅ ALWAYS use the tool
✅ Provide clear step-by-step instructions
✅ Include safety warnings
❌ NEVER make up procedures
```

**LLM:** llama3.2:latest (temp: 0.1)

**Tool:** Answer questions with vector store
- Vector Store: PostgreSQL (`krai_intelligence.chunks`)
- Embeddings: embeddinggemma:latest
- Query LLM: Ollama Chat Model

---

## 🔄 **Execution Flow**

### **Example: "Lexmark CX963 Fehlercode 88.10"**

```
1. User sends message
   ↓
2. Main Coordinator Agent receives input
   - Extracts: manufacturer=Lexmark, model=CX963, error_code=88.10
   - Decides: Call error_code_specialist
   ↓
3. error_code_specialist (Agent Tool)
   - Receives: { error_code: "88.10", manufacturer: "Lexmark", model: "CX963" }
   - Error Code LLM reasons: "I need to search the database"
   - Calls: Search Error Codes (HTTP Tool)
   ↓
4. Search Error Codes (HTTP Request)
   - POST http://backend:8000/api/v1/error-codes/search
   - Body: { "code": "88.10", "manufacturer": "Lexmark", "model": "CX963" }
   - Returns: Error code data
   ↓
5. error_code_specialist formats response
   - Uses specialized prompt
   - Formats in German
   - Returns to Main Agent
   ↓
6. Main Agent decides: "I need parts info"
   - Calls parts_specialist
   ↓
7. parts_specialist (Agent Tool)
   - Receives: { search_term: "Fuser Unit", manufacturer: "Lexmark", model: "CX963" }
   - Parts LLM reasons: "I need to search parts database"
   - Calls: Search Parts (HTTP Tool)
   ↓
8. Search Parts returns part numbers
   ↓
9. Main Agent decides: "I need repair instructions"
   - Calls manual_specialist
   ↓
10. manual_specialist (Agent Tool)
    - Receives: { query: "Fuser Unit replacement CX963" }
    - Manual LLM reasons: "I need to search manuals"
    - Calls: Answer questions with vector store
    ↓
11. Vector Store Tool
    - Embeddings Ollama creates query embedding
    - Search Manuals Vector Store searches Supabase
    - Returns relevant chunks
    - Ollama Chat Model formats response
    ↓
12. manual_specialist formats procedure
    ↓
13. Main Agent decides: "I need a video"
    - Calls video_specialist
    ↓
14. video_specialist returns video link
    ↓
15. Main Agent synthesizes final response:

🔴 **Fehlercode 88.10 - Fuser Unit defekt**

**Ursache:** [From error_code_specialist]

**Lösung:**
[From manual_specialist]

**Benötigte Teile:**
[From parts_specialist]

🎥 **Video:**
[From video_specialist]
```

---

## ✅ **Why This Architecture Works**

### **1. Agent Tools = Sub-Agents**
- No need for separate Agent nodes
- Each Agent Tool has own LLM + Prompt + Tool
- Built-in agent reasoning

### **2. Specialized Prompts**
- Each specialist is expert in ONE domain
- Clear task definition
- Consistent output format

### **3. Independent LLMs**
- Each specialist has own reasoning
- No prompt conflicts
- Better quality responses

### **4. Simple Connections**
```
Main Agent ← Agent Tools (4 specialists)
Each Agent Tool ← LLM + Tool
```

### **5. Easy to Maintain**
- One workflow file
- Clear structure
- Easy to debug

---

## 🧪 **Testing Scenarios**

### **Test 1: Error Code**
```
Input: "Lexmark CX963 Fehlercode 88.10"

Expected Flow:
1. Main Agent calls error_code_specialist
2. error_code_specialist calls HTTP API
3. Main Agent calls parts_specialist
4. Main Agent calls manual_specialist
5. Main Agent calls video_specialist
6. Main Agent synthesizes complete response

Expected Output:
✅ Error diagnosis
✅ Part numbers
✅ Step-by-step procedure
✅ Video link
✅ All in German
✅ Sources cited
```

### **Test 2: Parts Question**
```
Input: "Welche Fuser Unit passt zum CX963?"

Expected Flow:
1. Main Agent calls parts_specialist
2. parts_specialist calls HTTP API
3. Main Agent calls manual_specialist (installation)
4. Main Agent synthesizes response

Expected Output:
✅ Part number
✅ Compatible models
✅ Installation instructions
```

### **Test 3: How-To Question**
```
Input: "Wie tausche ich die Trommel beim bizhub C750i?"

Expected Flow:
1. Main Agent calls manual_specialist
2. manual_specialist calls Vector Store
3. Main Agent calls video_specialist
4. Main Agent synthesizes response

Expected Output:
✅ Step-by-step procedure
✅ Safety warnings
✅ Required tools
✅ Video link
```

### **Test 4: Context Awareness**
```
Conversation:
User: "Ich habe einen Lexmark CX963"
Agent: [Acknowledges]
User: "Fehlercode 88.10"
Agent: [Full diagnosis]
User: "Welche Teile brauche ich?"

Expected:
✅ Main Agent remembers context (Lexmark CX963)
✅ Calls parts_specialist with context
✅ No need to repeat device info
```

---

## 🔧 **Configuration Details**

### **Main Agent Settings**
- **Model:** llama3.2:latest
- **Temperature:** 0.1 (deterministic)
- **Memory:** Postgres Chat Memory
- **Context Window:** 10 messages

### **Specialist LLM Settings**
- **error_code_specialist:** llama3.1:8b, temp 0.1
- **parts_specialist:** llama3.2:latest, temp 0.1
- **video_specialist:** llama3.1:8b, temp 0.1
- **manual_specialist:** llama3.2:latest, temp 0.1

### **Vector Store Settings**
- **Table:** krai_intelligence.chunks
- **Function:** match_chunks (PostgreSQL function)
- **Embeddings:** embeddinggemma:latest
- **Top K:** 5 (default)

### **HTTP Tools**
- **Timeout:** 30s (default)
- **Method:** POST
- **Content-Type:** application/json

---

## 🐛 **Debugging Guide**

### **Check Specialist Calls**
```
n8n Execution Log:
1. Main Agent: "Calling error_code_specialist with params..."
2. error_code_specialist: "Using search_database tool..."
3. HTTP Request: "POST /api/v1/error-codes/search"
4. error_code_specialist: "Formatting response..."
5. Main Agent: "Received from error_code_specialist"
```

### **Common Issues**

**Specialist not called?**
- Check Main Agent prompt
- Check specialist description
- Verify specialist is connected to Main Agent

**Wrong specialist called?**
- Improve specialist descriptions
- Add more examples to Main Agent prompt
- Check input schema

**Empty responses?**
- Check backend API is running
- Check database has data
- Verify tool configurations
- Check LLM connections

**Tool not used by specialist?**
- Check specialist system message
- Verify tool is connected to specialist
- Check tool configuration

---

## 📊 **Performance Metrics**

### **Response Times**
- Simple query (1 specialist): ~2-3 seconds
- Complex query (4 specialists): ~8-10 seconds
- Context follow-up: ~1-2 seconds

### **Token Usage**
- Main Agent: ~500-1000 tokens/query
- Each Specialist: ~200-500 tokens/call
- Total: ~1500-3000 tokens/complex query

---

## 🚀 **Deployment**

### **Prerequisites**
```bash
# Ollama models
ollama pull llama3.2:latest
ollama pull llama3.1:8b
ollama pull embeddinggemma:latest

# Database
# Run migration 78 (vector search function)
psql -f database/migrations/78_vector_search_function.sql

# Backend API
# Ensure endpoints are running:
# - POST /api/v1/error-codes/search
# - POST /api/v1/parts/search
# - POST /api/v1/videos/search
```

### **Import Workflow**
```
1. n8n → Import from File
2. Select: Technician-Agent V2.1.json
3. Configure credentials:
   - Ollama API
   - PostgreSQL (for memory and vector store)
     Host: localhost, Port: 5432, Database: krai
4. Activate workflow
5. Test with: "Lexmark CX963 Fehlercode 88.10"
```

---

## 📈 **Future Enhancements**

### **V2.2 Ideas**
- [ ] Add caching for specialist responses
- [ ] Add confidence scores
- [ ] Add fallback strategies
- [ ] Add multi-language support
- [ ] Add image analysis specialist
- [ ] Add diagnostic flowchart specialist
- [ ] Add performance monitoring

---

## 🎯 **Summary**

**V2.1 Architecture:**
- ✅ Agent Tools ARE sub-agents (no separate nodes needed)
- ✅ Each specialist has own LLM + Prompt + Tool
- ✅ Specialized prompts for better quality
- ✅ Independent reasoning per domain
- ✅ Simple, maintainable structure
- ✅ Easy to debug
- ✅ Production-ready

**Key Learnings:**
- `@n8n/n8n-nodes-langchain.agentTool` has built-in agent functionality
- No need for complex sub-workflow architectures
- Specialized prompts > Generic prompts
- Independent LLMs > Shared LLM

**Ready for production!** 🚀
