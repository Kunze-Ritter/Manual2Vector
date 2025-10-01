# 🤖 KRAI AI Agent - Modern n8n Setup

## 🎯 Modern n8n Features

Dieser Workflow nutzt die **neuesten n8n Nodes**:
- **AI Agent Node** - Intelligenter Chat Agent
- **Ollama Node** - Direkte LLM Integration
- **Supabase Vector Store Node** - Vector Search
- **Supabase Node** - Database Operations

---

## 🚀 Quick Start

### **1. n8n starten:**
```bash
docker-compose up -d
# n8n: http://localhost:5678
# Login: admin / krai_chat_agent_2024
```

### **2. Credentials konfigurieren:**

#### **Supabase API Credential:**
1. Gehe zu **Settings → Credentials**
2. Erstelle **Supabase API** mit:
   - **Host**: `https://your-project.supabase.co`
   - **Service Role Key**: `your-service-role-key`

#### **Ollama ist bereits konfiguriert:**
- **Base URL**: `http://host.docker.internal:11434`
- **Model**: `llama3.2:latest`

### **3. Workflow importieren:**
1. Gehe zu **Workflows**
2. **Import from File**: `n8n_workflows/krai-ai-agent-modern.json`

### **4. Supabase Vector Store einrichten:**

```sql
-- Vector Store Tabelle erstellen
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

### **5. Workflow aktivieren:**
- Aktiviere den **KRAI AI Agent - Modern** Workflow

---

## 🧠 AI Agent Features

### **Intelligente Command Detection:**
- **`/search [text]`** → Vector Search in Dokumenten
- **`/models [name]`** → Produkt-Modell Suche
- **`/status`** → System-Status
- **Alles andere** → AI Chat mit Kontext

### **AI Agent Capabilities:**
- **System Message**: Speziell für technische Dokumentation
- **Temperature**: 0.7 für kreative aber präzise Antworten
- **Max Tokens**: 1000 für detaillierte Antworten
- **Context Awareness**: Nutzt Vector Search Ergebnisse

---

## 🔍 Vector Search Integration

### **Supabase Vector Store Node:**
```json
{
  "resource": "vectorSearch",
  "operation": "search",
  "query": "user search term",
  "limit": 5,
  "filter": {
    "metadata": "{}"
  }
}
```

### **Automatische Context Integration:**
- Vector Search Ergebnisse werden automatisch an AI Agent weitergegeben
- Kontext wird intelligent formatiert
- Relevante Dokumente werden als Basis für Antworten verwendet

---

## 🎮 Usage Examples

### **Vector Search:**
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/search Fehler Code 13"}'
```

### **Model Search:**
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/models HP LaserJet"}'
```

### **AI Chat:**
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Wie kann ich den Papierstau beheben?"}'
```

### **System Status:**
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/status"}'
```

---

## 🔧 Advanced Configuration

### **AI Agent System Message anpassen:**
```javascript
"Du bist der KRAI AI Agent, ein intelligenter Assistent für technische Dokumentation und Service-Manuals. Du hilfst bei Fragen zu Druckern, Kopierern und technischen Geräten. Antworte immer auf Deutsch und sei hilfreich und präzise."
```

### **Ollama Model wechseln:**
```javascript
{
  "model": "qwen3:8b",  // oder anderes Modell
  "baseURL": "http://host.docker.internal:11434"
}
```

### **Vector Search Parameter:**
```javascript
{
  "limit": 10,  // Mehr Ergebnisse
  "filter": {
    "metadata": "{\"document_type\": \"manual\"}"  // Spezifische Filter
  }
}
```

---

## 📊 Workflow Architecture

### **Flow Logic:**
```
User Message → Command Detection → Specialized Processing → AI Agent → Response
```

### **Node Types:**
1. **Webhook Trigger** - Empfängt Nachrichten
2. **IF Conditions** - Command Detection
3. **Supabase Nodes** - Database & Vector Operations
4. **AI Agent Node** - Intelligente Verarbeitung
5. **Ollama Node** - LLM Integration
6. **Response Node** - JSON Response

### **Parallel Processing:**
- **Search Query** → Vector Search → AI Response
- **Model Lookup** → Database Query → AI Response  
- **Status Check** → System Query → Direct Response
- **General Chat** → AI Agent → Direct Response

---

## 🔌 Integration Options

### **1. WhatsApp Business API:**
```json
{
  "trigger": "WhatsApp",
  "webhook": "http://localhost:5678/webhook/chat",
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
  "webhook": "http://localhost:5678/webhook/chat"
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

#### **1. AI Agent Node nicht verfügbar:**
```bash
# Update n8n to latest version
docker-compose pull
docker-compose up -d
```

#### **2. Supabase Vector Store Fehler:**
```sql
-- Check if pgvector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check if table exists
SELECT * FROM document_vectors LIMIT 1;
```

#### **3. Ollama Connection Failed:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Update docker-compose.yml:
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

#### **4. Vector Search keine Ergebnisse:**
```sql
-- Check if embeddings exist
SELECT COUNT(*) FROM document_vectors WHERE embedding IS NOT NULL;

-- Test vector search manually
SELECT * FROM document_vectors 
ORDER BY embedding <=> (SELECT embedding FROM document_vectors LIMIT 1)
LIMIT 5;
```

---

## 📈 Performance Optimization

### **AI Agent Optimization:**
- **Temperature**: 0.7 für beste Balance
- **Max Tokens**: 1000 für detaillierte Antworten
- **System Message**: Präzise und spezifisch

### **Vector Search Optimization:**
- **Limit**: 5 für relevante Ergebnisse
- **Indexes**: ivfflat für schnelle Suche
- **Filters**: Spezifische Metadaten nutzen

### **Database Optimization:**
- **Connection Pooling**: Supabase automatisch
- **Indexes**: Auf häufig abgefragte Felder
- **Caching**: Supabase automatisch

---

## 🎯 Next Steps

### **Phase 1: Basic AI Agent** ✅
- [x] Modern n8n Workflow
- [x] AI Agent Node Integration
- [x] Supabase Vector Store
- [x] Ollama Integration

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

**🎉 Dein moderner KRAI AI Agent ist bereit! Nutze die neuesten n8n Features für maximale Intelligenz!**
