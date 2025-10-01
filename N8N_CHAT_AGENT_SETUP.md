# 🤖 KRAI Chat Agent - n8n Setup Guide

## 🎯 Overview

Der KRAI Chat Agent ist ein intelligenter Chatbot, der mit deiner KR-AI-Engine Datenbank kommuniziert. Er kann:
- **Dokumente durchsuchen** mit Vector Search
- **Modelle finden** in der Produktdatenbank
- **System-Status** abfragen
- **AI-Chat** mit Ollama für allgemeine Fragen
- **Multi-Channel Support** (WhatsApp, Telegram, Discord, etc.)

---

## 🚀 Quick Start

### **1. n8n starten:**
```bash
# Im Projekt-Root-Verzeichnis
docker-compose up -d

# n8n ist dann verfügbar unter:
# http://localhost:5678
# Login: admin / krai_chat_agent_2024
```

### **2. Credentials konfigurieren:**
1. Gehe zu **Settings → Credentials**
2. Erstelle **HTTP Header Auth** mit:
   - **Name**: `Authorization`
   - **Value**: `Bearer YOUR_SUPABASE_ANON_KEY`

### **3. Workflow importieren:**
1. Gehe zu **Workflows**
2. **Import from File**: `n8n_workflows/krai-chat-agent.json`
3. **Aktiviere** den Workflow

### **4. Testen:**
```bash
# Test mit curl
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/status"}'
```

---

## 📋 Verfügbare Commands

### **System Commands:**
- `/status` - System-Status und Datenbankverbindung prüfen
- `/help` - Alle verfügbaren Befehle anzeigen

### **Search Commands:**
- `/search [text]` - Dokumente durchsuchen
  - Beispiel: `/search Fehler Code 13`
  - Beispiel: `/search Drucker Wartung`

### **Model Commands:**
- `/models [name]` - Modelle in der Datenbank suchen
  - Beispiel: `/models HP LaserJet`
  - Beispiel: `/models Canon`

### **AI Chat:**
- Alles andere wird an Ollama weitergeleitet für allgemeine Fragen

---

## 🔧 Konfiguration

### **Environment Variables:**
```env
# In docker-compose.yml oder .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### **Supabase RPC Functions:**
Du brauchst diese SQL-Funktion in Supabase:

```sql
-- Vector Search Function
CREATE OR REPLACE FUNCTION search_documents(
  query_text TEXT,
  limit_count INTEGER DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  filename TEXT,
  content TEXT,
  similarity_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    c.id,
    d.filename,
    c.content,
    (c.embedding <=> (
      SELECT embedding 
      FROM krai_intelligence.embeddings 
      WHERE content = query_text 
      LIMIT 1
    )) as similarity_score
  FROM krai_content.chunks c
  JOIN krai_core.documents d ON c.document_id = d.id
  WHERE c.embedding IS NOT NULL
  ORDER BY similarity_score
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

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

### **5. Web Chat Widget:**
```html
<!-- Einfaches Web Chat Interface -->
<div id="krai-chat-widget">
  <input type="text" id="chat-input" placeholder="Frage eingeben...">
  <button onclick="sendMessage()">Senden</button>
  <div id="chat-response"></div>
</div>

<script>
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const response = await fetch('http://localhost:5678/webhook/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: input.value})
  });
  const data = await response.json();
  document.getElementById('chat-response').innerHTML = data.message;
}
</script>
```

---

## 📊 Workflow Details

### **Flow Logic:**
```
User Message → Command Detection → Database Query → AI Response → User
```

### **Node Types:**
1. **Webhook Trigger** - Empfängt Nachrichten
2. **IF Conditions** - Command Detection
3. **HTTP Requests** - Supabase & Ollama API Calls
4. **Code Nodes** - Response Formatting
5. **Response Node** - Sendet Antwort zurück

### **Error Handling:**
- **Database Errors** - Graceful Fallbacks
- **AI Timeouts** - Default Responses
- **Invalid Commands** - Help Display

---

## 🎨 Customization

### **Response Templates:**
```javascript
// In Code Nodes anpassbar
const customResponse = {
  message: "Custom formatted response",
  timestamp: new Date().toISOString(),
  data: $json
};
```

### **New Commands hinzufügen:**
1. **IF Node** für neuen Command
2. **HTTP Request** für Datenbank-Abfrage
3. **Code Node** für Response-Formatting
4. **Verbindungen** zwischen Nodes

### **Multi-Language Support:**
```javascript
// Language Detection in Code Node
const language = $json.message.includes('hello') ? 'en' : 'de';
const responses = {
  'en': 'Hello! How can I help you?',
  'de': 'Hallo! Wie kann ich dir helfen?'
};
```

---

## 🚀 Advanced Features

### **1. Document Upload via Chat:**
```json
{
  "trigger": "File Upload",
  "processor": "KR-AI-Engine Pipeline",
  "response": "Document processing started..."
}
```

### **2. Real-time Status Updates:**
```json
{
  "trigger": "Cron Job",
  "schedule": "*/5 * * * *",
  "action": "Check processing status"
}
```

### **3. Notification System:**
```json
{
  "trigger": "Database Change",
  "condition": "processing_status = 'completed'",
  "action": "Send notification to user"
}
```

### **4. Analytics Dashboard:**
```json
{
  "trigger": "Webhook",
  "endpoint": "/analytics",
  "data": "Chat usage statistics"
}
```

---

## 🔧 Troubleshooting

### **Common Issues:**

#### **1. n8n nicht erreichbar:**
```bash
# Check Docker Status
docker-compose ps

# Check Logs
docker-compose logs n8n

# Restart
docker-compose restart n8n
```

#### **2. Supabase Connection Failed:**
- Check Credentials in n8n
- Verify Supabase URL und Key
- Test mit curl:
```bash
curl -H "Authorization: Bearer YOUR_KEY" "YOUR_URL/rest/v1/system_metrics"
```

#### **3. Ollama nicht erreichbar:**
```bash
# Check Ollama Status
curl http://localhost:11434/api/tags

# Update docker-compose.yml:
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

#### **4. Webhook nicht aktiv:**
- Workflow muss **aktiviert** sein
- Webhook URL muss **public** erreichbar sein
- Für lokale Tests: **ngrok** verwenden

---

## 📈 Performance Optimization

### **Database Optimization:**
- **Indexes** auf häufig abgefragte Felder
- **Connection Pooling** für Supabase
- **Caching** für häufige Queries

### **AI Optimization:**
- **Model Caching** in Ollama
- **Response Streaming** für lange Antworten
- **Timeout Settings** für API Calls

### **n8n Optimization:**
- **Worker Nodes** für Parallel Processing
- **Queue Management** für hohe Load
- **Memory Limits** für Docker Container

---

## 🎯 Next Steps

### **Phase 1: Basic Chat Agent** ✅
- [x] n8n Setup
- [x] Basic Commands
- [x] Supabase Integration
- [x] Ollama Integration

### **Phase 2: Multi-Channel Support** 🔄
- [ ] WhatsApp Integration
- [ ] Telegram Bot
- [ ] Discord Bot
- [ ] Web Chat Widget

### **Phase 3: Advanced Features** 📋
- [ ] Document Upload via Chat
- [ ] Real-time Processing Status
- [ ] User Authentication
- [ ] Analytics Dashboard

### **Phase 4: Production Deployment** 🚀
- [ ] Cloud Deployment
- [ ] SSL/HTTPS Setup
- [ ] Monitoring & Logging
- [ ] Backup & Recovery

---

**🎉 Dein KRAI Chat Agent ist bereit! Starte mit `docker-compose up -d` und teste die Commands!**
