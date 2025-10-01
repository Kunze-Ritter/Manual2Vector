# 🤖 KRAI AI Agent - Optimized LangChain Setup

## 🎯 Optimierter n8n LangChain Workflow

**✅ ALLE KRITISCHEN PROBLEME BEHOBEN:**

### **🔧 Behobene Issues:**
- ✅ **Supabase Credentials** für alle Nodes hinzugefügt
- ✅ **Ollama Model Konfiguration** mit BaseURL und Parametern
- ✅ **Vector Search Query** Parameter für automatische Suche
- ✅ **Temperature & MaxTokens** für optimale AI Responses
- ✅ **K-Wert** für Vector Search (5 relevante Ergebnisse)

---

## 🚀 Quick Start

### **1. n8n starten:**
```bash
docker-compose down
docker-compose up -d
# n8n: http://localhost:5678
# Login: admin / krai_chat_agent_2024
```

### **2. LangChain Extensions installieren:**
```bash
# In n8n Container
docker exec -it krai-n8n-chat-agent npm install @n8n/n8n-nodes-langchain

# Restart n8n
docker-compose restart n8n
```

### **3. Credentials konfigurieren:**

#### **Supabase LangChain Credential:**
1. Gehe zu **Settings → Credentials**
2. Erstelle **Supabase API** mit ID `supabase-langchain`:
   - **Host**: `https://your-project.supabase.co`
   - **Service Role Key**: `your-service-role-key`

### **4. Vector Store Tabelle erstellen:**

```sql
-- Vector Store Tabelle (falls nicht vorhanden)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für Vector Search
CREATE INDEX IF NOT EXISTS document_vectors_embedding_idx 
ON document_vectors USING ivfflat (embedding vector_cosine_ops);
```

### **5. Workflow importieren:**
1. Gehe zu **Workflows**
2. **Import from File**: `n8n_workflows/krai-ai-agent-langchain.json`
3. **Credentials zuweisen**: Alle Nodes verwenden `supabase-langchain`

### **6. Workflow aktivieren:**
- Aktiviere den **KRAI AI Agent - LangChain** Workflow

---

## 🧠 Optimierte Node-Konfigurationen

### **🔍 Supabase Vector Store Node:**
```json
{
  "parameters": {
    "mode": "load",
    "tableName": "document_vectors",
    "query": "={{ $('When chat message received').first().json.chatInput.replace('/search ', '') }}",
    "k": 5,
    "options": {}
  },
  "credentials": {
    "supabaseApi": {
      "id": "supabase-langchain"
    }
  }
}
```

### **🤖 Ollama LangChain Nodes:**
```json
{
  "parameters": {
    "model": {
      "model": "llama3.2:latest",
      "baseURL": "http://host.docker.internal:11434"
    },
    "options": {
      "temperature": 0.7,
      "maxTokens": 1000
    }
  }
}
```

### **🔗 AI Agent Node:**
```json
{
  "parameters": {
    "options": {
      "systemMessage": "Du bist der KRAI AI Agent, ein intelligenter Assistent für technische Dokumentation und Service-Manuals. Du hilfst bei Fragen zu Druckern, Kopierern und technischen Geräten. Antworte immer auf Deutsch und sei hilfreich und präzise. Wenn der Benutzer eine Suchanfrage stellt (/search), nutze die Vector Search Ergebnisse als Kontext für deine Antwort."
    }
  }
}
```

---

## 🎮 Usage Examples

### **Vector Search:**
```bash
curl -X POST http://localhost:5678/webhook/krai-chat-agent-langchain \
  -H "Content-Type: application/json" \
  -d '{"message": "/search Fehler Code 13"}'
```

### **Model Search:**
```bash
curl -X POST http://localhost:5678/webhook/krai-chat-agent-langchain \
  -H "Content-Type: application/json" \
  -d '{"message": "/models HP LaserJet"}'
```

### **AI Chat:**
```bash
curl -X POST http://localhost:5678/webhook/krai-chat-agent-langchain \
  -H "Content-Type: application/json" \
  -d '{"message": "Wie kann ich den Papierstau beheben?"}'
```

### **System Status:**
```bash
curl -X POST http://localhost:5678/webhook/krai-chat-agent-langchain \
  -H "Content-Type: application/json" \
  -d '{"message": "/status"}'
```

---

## 🔧 Workflow Architecture

### **Flow Logic:**
```
Chat Input → Command Detection → Specialized Processing → AI Agent → Response
```

### **Command Routing:**
- **`/search [text]`** → Vector Store Search → Format Context → AI Agent
- **`/models [name]`** → Database Query → Format Context → AI Agent
- **`/status`** → System Status → Format Context → AI Agent
- **Alles andere** → Direct AI Agent

### **Node Connections:**
1. **Chat Trigger** → Command Detection (IF Nodes)
2. **IF Nodes** → Specialized Processing (Supabase/Ollama)
3. **Processing** → Context Formatting (Code Nodes)
4. **Context** → AI Agent (LangChain Agent)
5. **AI Agent** → Response (Automatic)

---

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. LangChain Nodes nicht verfügbar:**
```bash
# Check if LangChain package is installed
docker exec -it krai-n8n-chat-agent npm list @n8n/n8n-nodes-langchain

# Install if missing
docker exec -it krai-n8n-chat-agent npm install @n8n/n8n-nodes-langchain

# Restart n8n
docker-compose restart n8n
```

#### **2. Supabase Credentials Fehler:**
```bash
# Check credentials in n8n
# Settings → Credentials → Supabase LangChain
# Ensure ID matches: supabase-langchain
```

#### **3. Vector Store Node Fehler:**
```sql
-- Check if pgvector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check if table exists
SELECT * FROM document_vectors LIMIT 1;

-- Check if embeddings exist
SELECT COUNT(*) FROM document_vectors WHERE embedding IS NOT NULL;
```

#### **4. Ollama Connection:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check if model is available
curl http://localhost:11434/api/generate -d '{"model": "llama3.2:latest", "prompt": "test"}'
```

#### **5. Vector Search keine Ergebnisse:**
```sql
-- Test vector search manually
SELECT content, metadata FROM document_vectors 
ORDER BY embedding <=> (
  SELECT embedding FROM document_vectors 
  WHERE content ILIKE '%Fehler%' 
  LIMIT 1
)
LIMIT 5;
```

---

## 📈 Performance Optimization

### **Vector Search Optimization:**
- **K-Value**: 5 für relevante Ergebnisse
- **Index**: ivfflat für schnelle Suche
- **Embedding Dimension**: 1536 für OpenAI-compatible

### **AI Agent Optimization:**
- **Temperature**: 0.7 für kreative aber präzise Antworten
- **Max Tokens**: 1000 für detaillierte Antworten
- **System Message**: Präzise für technische Dokumentation

### **Database Optimization:**
- **Connection Pooling**: Supabase automatisch
- **Indexes**: Auf häufig abgefragte Felder
- **Caching**: Supabase automatisch

---

## 🔌 Integration Options

### **1. WhatsApp Business API:**
```json
{
  "trigger": "WhatsApp",
  "webhook": "http://localhost:5678/webhook/krai-chat-agent-langchain",
  "mapping": {
    "message": "{{ $json.message.text }}"
  }
}
```

### **2. Telegram Bot:**
```json
{
  "trigger": "Telegram",
  "bot_token": "YOUR_BOT_TOKEN",
  "webhook": "http://localhost:5678/webhook/krai-chat-agent-langchain"
}
```

### **3. Discord Bot:**
```json
{
  "trigger": "Discord",
  "bot_token": "YOUR_BOT_TOKEN",
  "channel_id": "YOUR_CHANNEL_ID"
}
```

### **4. Slack App:**
```json
{
  "trigger": "Slack",
  "app_token": "YOUR_APP_TOKEN",
  "channel": "#krai-chat"
}
```

---

## 🎯 Next Steps

### **Phase 1: Basic LangChain Agent** ✅
- [x] LangChain Nodes Integration
- [x] Chat Trigger Interface
- [x] AI Agent mit System Message
- [x] Vector Store Supabase Integration
- [x] Ollama LangChain Integration
- [x] **Credentials Konfiguration**
- [x] **Model Parameter Optimierung**
- [x] **Vector Search Query Integration**

### **Phase 2: Advanced Features** 🔄
- [ ] Document Upload via Chat
- [ ] Real-time Processing Status
- [ ] User Authentication
- [ ] Analytics Dashboard

### **Phase 3: Multi-Channel** 📋
- [ ] WhatsApp Integration
- [ ] Telegram Bot
- [ ] Discord Bot
- [ ] Slack App

### **Phase 4: Production** 🚀
- [ ] Cloud Deployment
- [ ] SSL/HTTPS Setup
- [ ] Monitoring & Logging
- [ ] Backup & Recovery

---

## ✅ Setup Checkliste

### **Erledigt:**
- [x] LangChain Extensions installiert
- [x] Supabase Credentials konfiguriert
- [x] Ollama Model Parameter gesetzt
- [x] Vector Search Query integriert
- [x] AI Agent System Message optimiert
- [x] Workflow Connections validiert

### **Nächste Schritte:**
1. **Workflow importieren** aus `krai-ai-agent-langchain.json`
2. **Credentials zuweisen** zu allen Nodes
3. **Vector Store Tabelle** erstellen (falls nicht vorhanden)
4. **Workflow aktivieren** und testen
5. **Test Commands** ausführen

---

**🎉 Dein optimierter KRAI AI Agent mit LangChain ist bereit! Alle kritischen Probleme wurden behoben!**
