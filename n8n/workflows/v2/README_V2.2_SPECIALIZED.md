# KRAI Technician Agent V2.2 - Specialized Sub-Agents

## 🎯 **Revolutionary Architecture**

### **Multi-Agent System with Specialized Experts**

```
User Question
    ↓
Main Coordinator Agent (llama3.1:8b)
    ├─ Memory: Postgres
    └─ Specialized Sub-Agents:
        ├─ Error Code Specialist
        │   ├─ Own LLM (llama3.1:8b)
        │   ├─ Own Prompt (Error diagnosis expert)
        │   └─ Tool: HTTP Request → error_codes API
        ├─ Parts Specialist
        │   ├─ Own LLM (llama3.1:8b)
        │   ├─ Own Prompt (Parts expert)
        │   └─ Tool: HTTP Request → parts API
        ├─ Video Specialist
        │   ├─ Own LLM (llama3.1:8b)
        │   ├─ Own Prompt (Video expert)
        │   └─ Tool: HTTP Request → videos API
        └─ Manual Specialist
            ├─ Own LLM (llama3.1:8b)
            ├─ Own Prompt (Service manual expert)
            └─ Tool: Vector Store → krai.chunks
```

## 🚀 **Key Innovation**

### **Each Sub-Agent has:**
1. ✅ **Own LLM instance** → Independent reasoning
2. ✅ **Specialized prompt** → Expert in ONE domain
3. ✅ **Own tool** → Direct database/API access
4. ✅ **Focused output** → Precise, structured responses

### **Main Agent:**
- 🎯 **Coordinator role** → Decides which specialists to call
- 🎯 **Context manager** → Remembers conversation history
- 🎯 **Synthesizer** → Combines specialist responses into coherent answer

## 📋 **Prerequisites**

### **1. Ollama Model**
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### **2. Database**
```sql
-- Run migration 78 (vector search function)
\i database/migrations/78_vector_search_function.sql
```

### **3. Backend API**
Ensure these endpoints are running:
- `POST /api/v1/error-codes/search`
- `POST /api/v1/parts/search`
- `POST /api/v1/videos/search`

## 🎭 **Specialized Prompts**

### **Main Coordinator Agent**
```
Role: Technical Support Coordinator
Task: Coordinate between specialists
Strategy: Extract info → Call specialists → Synthesize response
```

### **Error Code Specialist**
```
Role: Error Code Diagnosis Expert
Task: Diagnose error codes precisely
Output: Fehlercode, Ursache, Lösung, Betroffene Komponenten
```

### **Parts Specialist**
```
Role: Spare Parts Expert
Task: Find exact part numbers and compatibility
Output: Teilenummer, Beschreibung, Kompatible Modelle
```

### **Video Specialist**
```
Role: Video Tutorial Expert
Task: Find relevant repair videos
Output: Video title, Link, Beschreibung
```

### **Manual Specialist**
```
Role: Service Manual Expert
Task: Provide step-by-step procedures
Output: Schritte, Hinweise, Werkzeug, Quelle
```

## 🔄 **Execution Flow**

### **Example: "Lexmark CX963 Fehlercode 88.10"**

```
1. Main Agent receives question
   ↓
2. Extracts: manufacturer=Lexmark, model=CX963, error_code=88.10
   ↓
3. Calls error_code_specialist(error_code="88.10", manufacturer="Lexmark", model="CX963")
   ↓
4. Error Specialist:
   - Receives parameters
   - Calls search_database tool (HTTP Request)
   - Formats response: "Fehlercode 88.10 - Fuser Unit defekt..."
   ↓
5. Main Agent receives error diagnosis
   ↓
6. Calls parts_specialist(search_term="Fuser Unit", manufacturer="Lexmark", model="CX963")
   ↓
7. Parts Specialist:
   - Calls search_database tool
   - Formats response: "Teilenummer: 40X8024..."
   ↓
8. Main Agent receives parts info
   ↓
9. Calls manual_specialist(query="Fuser Unit replacement CX963")
   ↓
10. Manual Specialist:
    - Calls search_manuals tool (Vector Store)
    - Formats response: "Schritte: 1. Gerät ausschalten..."
    ↓
11. Main Agent receives procedure
    ↓
12. Calls video_specialist(search_term="Fuser Unit Lexmark CX963")
    ↓
13. Video Specialist:
    - Calls search_database tool
    - Formats response: "Video: https://youtube.com/..."
    ↓
14. Main Agent synthesizes all responses:

🔴 **Fehlercode 88.10 - Fuser Unit defekt**

**Ursache:** [From error_code_specialist]

**Lösung:**
[From manual_specialist]

**Benötigte Teile:**
[From parts_specialist]

🎥 **Video:**
[From video_specialist]
```

## ✅ **Advantages over V2.1**

| Feature | V2.1 (Workflow Tools) | V2.2 (Agent Tools) |
|---------|----------------------|-------------------|
| **Tool Type** | Workflow Tools (sub-workflows) | Agent Tools (sub-agents) |
| **Prompts** | One generic prompt | 5 specialized prompts |
| **LLM Instances** | 1 shared LLM | 5 independent LLMs |
| **Reasoning** | Generic | Domain-specific |
| **Output Quality** | Good | Excellent |
| **Maintainability** | Complex (5 workflows) | Simple (1 workflow) |
| **Debugging** | Hard (across workflows) | Easy (one place) |
| **Performance** | Slower (workflow overhead) | Faster (direct calls) |

## 🧪 **Testing**

### **Test 1: Error Code**
```
Input: "Lexmark CX963 Fehlercode 88.10"

Expected:
✅ Main Agent calls error_code_specialist
✅ Error Specialist calls HTTP Request
✅ Returns structured error diagnosis
✅ Main Agent calls parts_specialist
✅ Parts Specialist returns part numbers
✅ Main Agent calls manual_specialist
✅ Manual Specialist returns procedure
✅ Main Agent calls video_specialist
✅ Video Specialist returns video link
✅ Main Agent synthesizes complete response
```

### **Test 2: Parts Question**
```
Input: "Welche Fuser Unit passt zum CX963?"

Expected:
✅ Main Agent calls parts_specialist
✅ Parts Specialist returns part info
✅ Main Agent calls manual_specialist (for installation)
✅ Complete response with part number + installation guide
```

### **Test 3: How-To Question**
```
Input: "Wie tausche ich die Trommel beim bizhub C750i?"

Expected:
✅ Main Agent calls manual_specialist
✅ Manual Specialist searches vector store
✅ Returns step-by-step procedure
✅ Main Agent calls video_specialist
✅ Complete response with steps + video
```

### **Test 4: Context Awareness**
```
Conversation:
1. "Ich habe einen Lexmark CX963"
2. "Fehlercode 88.10"
3. "Welche Teile brauche ich?"

Expected:
✅ Main Agent remembers context (Lexmark CX963)
✅ Calls specialists with context
✅ No need to repeat device info
```

## 🔧 **Configuration**

### **Main Agent Settings**
- Temperature: 0.1 (deterministic)
- Max Iterations: 5
- Memory: 10 messages

### **Specialist Agents Settings**
- Temperature: 0.1 (precise)
- Max Iterations: 3 (focused)
- No memory (stateless)

### **Tool Settings**
- HTTP Request timeout: 30s
- Vector Store top_k: 5
- Similarity threshold: 0.7

## 📊 **Performance Metrics**

### **Expected Response Times**
- Simple query (1 specialist): ~2-3 seconds
- Complex query (4 specialists): ~8-10 seconds
- Context follow-up: ~1-2 seconds

### **Token Usage**
- Main Agent: ~500-1000 tokens/query
- Each Specialist: ~200-500 tokens/call
- Total: ~1500-3000 tokens/complex query

## 🐛 **Debugging**

### **Check Specialist Calls**
```
n8n Execution Log:
1. Main Agent: "Calling error_code_specialist..."
2. Error Specialist: "Searching database..."
3. HTTP Request: "POST /api/v1/error-codes/search"
4. Error Specialist: "Found error code..."
5. Main Agent: "Received response from error_code_specialist"
```

### **Common Issues**

**Specialists not called?**
- Check Main Agent prompt
- Check specialist descriptions
- Enable "Return Intermediate Steps"

**Wrong specialist called?**
- Improve specialist descriptions
- Add more examples to Main Agent prompt

**Empty responses?**
- Check backend API
- Check database data
- Check tool configurations

## 🚀 **Deployment**

### **Step 1: Import**
```
n8n → Import → KRAI_Agent_V2.2_Specialized.json
```

### **Step 2: Configure Credentials**
- Ollama API
- Postgres (for memory)
- Supabase (for vector store)

### **Step 3: Activate**
```
Workflow → Activate
```

### **Step 4: Test**
```
Open Chat → Test with: "Lexmark CX963 Fehlercode 88.10"
```

## 📈 **Future Enhancements**

### **V2.3 Ideas**
- [ ] Add caching for specialist responses
- [ ] Add confidence scores from specialists
- [ ] Add fallback strategies
- [ ] Add multi-language support
- [ ] Add image analysis specialist
- [ ] Add diagnostic flowchart specialist

## 🎯 **Summary**

**V2.2 is a MAJOR upgrade:**
- ✅ 5 specialized sub-agents with own prompts
- ✅ Each expert in their domain
- ✅ Better output quality
- ✅ Easier to maintain
- ✅ Faster execution
- ✅ Better debugging

**Ready for production!** 🚀
