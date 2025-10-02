# 🤖 KRAI AI Agent - LangChain n8n Setup

## 🎯 Echte n8n LangChain Nodes

Dieser Workflow nutzt die **echten n8n LangChain Nodes**:
- **`@n8n/n8n-nodes-langchain.chatTrigger`** - Chat Interface
- **`@n8n/n8n-nodes-langchain.agent`** - AI Agent
- **`@n8n/n8n-nodes-langchain.vectorStoreSupabase`** - Vector Store
- **`@n8n/n8n-nodes-langchain.lmOllama`** - Ollama LLM
- **`@n8n/n8n-nodes-langchain.lmChatOllama`** - Ollama Chat Model

---

## 🚀 Quick Start

### **1. n8n starten:**
```bash
docker-compose up -d
# n8n: http://localhost:5678
# Login: admin / krai_chat_agent_2024
```

### **2. LangChain Nodes installieren:**
```bash
# In n8n Container
docker exec -it krai-n8n-chat-agent npm install @n8n/n8n-nodes-langchain
```

### **3. Credentials konfigurieren:**

#### **Supabase API Credential:**
1. Gehe zu **Settings → Credentials**
2. Erstelle **Supabase API** mit:
   - **Host**: `https://your-project.supabase.co`
   - **Service Role Key**: `your-service-role-key`

#### **Ollama ist automatisch konfiguriert:**
- **Base URL**: `http://host.docker.internal:11434`
- **Model**: `llama3.2:latest`

### **4. Vector Store Tabelle erstellen:**

```sql
-- Vector Store Tabelle
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für Vector Search
CREATE INDEX ON document_vectors USING ivfflat (embedding vector_cosine_ops);
```

### **5. Workflow importieren:**
1. Gehe zu **Workflows**
2. **Import from File**: `n8n_workflows/krai-ai-agent-langchain.json`

### **6. Workflow aktivieren:**
- Aktiviere den **KRAI AI Agent - LangChain** Workflow

---

## 🧠 LangChain AI Agent Features

### **Chat Trigger Node:**
- **Webhook Interface** für Chat-Nachrichten
- **Automatische Response** Handling
- **Real-time Chat** Support

### **AI Agent Node:**
- **System Message**: Speziell für technische Dokumentation
- **Context Awareness**: Nutzt Vector Search Ergebnisse
- **Intelligente Responses**: Basierend auf verfügbaren Daten

### **Vector Store Supabase Node:**
- **Direkte Integration** mit Supabase pgvector
- **Automatische Similarity Search**
- **Metadata Filtering** Support

### **Ollama LangChain Nodes:**
- **`lmOllama`**: Standard LLM Integration
- **`lmChatOllama`**: Chat-spezifische Integration
- **Model Selection**: llama3.2:latest

---

## 🔍 Command Detection

### **Intelligente Command Routing:**
- **`/search [text]`** → Vector Store Search → AI Agent
- **`/models [name]`** → Database Query → AI Agent
- **`/status`** → System Status → AI Agent
- **Alles andere** → Direct AI Agent

### **Context Integration:**
- **Search Results** werden als Kontext formatiert
- **Model Data** wird strukturiert angezeigt
- **System Status** wird übersichtlich dargestellt

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

## 🔧 Node Configuration

### **Chat Trigger Node:**
```json
{
  "type": "@n8n/n8n-nodes-langchain.chatTrigger",
  "typeVersion": 1.3,
  "parameters": {
    "options": {}
  }
}
```

### **AI Agent Node:**
```json
{
  "type": "@n8n/n8n-nodes-langchain.agent",
  "typeVersion": 2.2,
  "parameters": {
    "options": {
      "systemMessage": "Du bist der KRAI AI Agent..."
    }
  }
}
```

### **Vector Store Supabase Node:**
```json
{
  "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
  "typeVersion": 1.3,
  "parameters": {
    "mode": "load",
    "tableName": {
      "value": "document_vectors"
    }
  }
}
```

### **Ollama LangChain Nodes:**
```json
{
  "type": "@n8n/n8n-nodes-langchain.lmOllama",
  "typeVersion": 1,
  "parameters": {
    "options": {}
  }
}
```

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

#### **2. Vector Store Node Fehler:**
```sql
-- Check if pgvector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check if table exists
SELECT * FROM document_vectors LIMIT 1;

-- Check if embeddings exist
SELECT COUNT(*) FROM document_vectors WHERE embedding IS NOT NULL;
```

#### **3. Ollama LangChain Connection:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check if model is available
curl http://localhost:11434/api/generate -d '{"model": "llama3.2:latest", "prompt": "test"}'
```

#### **4. Chat Trigger Webhook:**
```bash
# Check webhook URL
curl -X POST http://localhost:5678/webhook/krai-chat-agent-langchain \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

## 📈 Performance Optimization

### **LangChain Optimization:**
- **System Message**: Präzise und spezifisch
- **Context Length**: Optimal für verfügbare Tokens
- **Vector Search Limit**: 5 für relevante Ergebnisse

### **Vector Store Optimization:**
- **Index Type**: ivfflat für schnelle Suche
- **Embedding Dimension**: 1536 für OpenAI/OpenAI-compatible
- **Metadata Indexing**: Auf häufig abgefragte Felder

### **Ollama Optimization:**
- **Model Selection**: llama3.2:latest für beste Balance
- **Temperature**: 0.7 für kreative aber präzise Antworten
- **Max Tokens**: 1000 für detaillierte Antworten

---

## 🎯 Next Steps

### **Phase 1: Basic LangChain Agent** ✅
- [x] LangChain Nodes Integration
- [x] Chat Trigger Interface
- [x] AI Agent mit System Message
- [x] Vector Store Supabase Integration
- [x] Ollama LangChain Integration

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

**🎉 Dein KRAI AI Agent mit echten n8n LangChain Nodes ist bereit! Nutze die professionellen LangChain Features für maximale Intelligenz!**
