# KRAI Technician Agent V2.1 - Setup Guide

## 📊 **Database Schema Overview**

The KRAI system uses a well-organized PostgreSQL database with the following schemas:

### **`krai_agent`** - AI Agent System
All agent-related data in one place:
- `memory` - Chat history and conversations
- `tool_usage` - Analytics on which tools are used
- `feedback` - User ratings and feedback
- `session_context` - Conversation context tracking
- `agent_performance` - Performance metrics (VIEW)
- `user_satisfaction` - Satisfaction metrics (VIEW)

### **`krai_intelligence`** - AI/ML Processing
- `chunks` - Document text chunks
- `embeddings` - Vector embeddings for semantic search
- `error_codes` - Extracted error codes
- `search_analytics` - Search metrics

### **`krai_core`** - Master Data
- `manufacturers`, `products`, `documents`
- `product_series`, `product_types`

### **`krai_parts`** - Parts Catalog
- `parts_catalog` - Parts with numbers and compatibility

### **`krai_content`** - Media
- `images`, `videos` - Screenshots and video links

### **`public`** - n8n Interface
- `n8n_chat_histories` - VIEW that maps to `krai_agent.memory`

---

# KRAI Technician Agent V2.1 - Setup Guide

## 🚀 **Quick Start**

### **1. Datenbank Migration ausführen**

```bash
# Migration anwenden
psql -h your-supabase-host -U postgres -d postgres -f database/migrations/75_agent_tool_functions.sql
```

**Oder via Supabase Dashboard:**
1. Öffne Supabase Dashboard → SQL Editor
2. Kopiere Inhalt von `75_agent_tool_functions.sql`
3. Klicke "Run"

### **2. n8n Workflows importieren**

**Hauptworkflow:**
1. n8n öffnen → Workflows → Import from File
2. Wähle: `n8n/workflows/v2/Technician-Agent-V2.1.json`
3. Aktiviere Workflow

**Tool-Workflows (Sub-Workflows):**
1. Importiere: `Tool-ErrorCodeSearch.json`
2. Importiere: `Tool-PartsSearch.json`
3. Importiere weitere Tool-Workflows (siehe unten)

### **3. Credentials konfigurieren**

**Supabase Postgres:**
```
Host: your-project.supabase.co
Port: 5432
Database: postgres
User: postgres
Password: your-password
SSL: Require
```

**Ollama:**
```
Base URL: http://localhost:11434
Model: llama3.2:latest
```

---

## 📋 **Vollständige Workflow-Liste**

### **Haupt-Workflow:**
- ✅ `Technician-Agent-V2.1.json` (Main Agent)

### **Tool-Workflows:**
- ✅ `Tool-ErrorCodeSearch.json` (Fehlercode-Suche)
- ✅ `Tool-PartsSearch.json` (Ersatzteil-Suche)
- ⏳ `Tool-ProductInfo.json` (Produkt-Info) - TODO
- ⏳ `Tool-VideoSearch.json` (Video-Suche) - TODO
- ⏳ `Tool-DocumentationSearch.json` (Dokumentation) - TODO

---

## 🧪 **Testing**

### **Test 1: Fehlercode-Suche**
```
User: "Lexmark CX963 Fehlercode C-9402"
Expected: Fehler-Beschreibung, Ursache, Lösung, Teile
```

### **Test 2: Ersatzteil-Suche**
```
User: "Welche Fuser Unit brauche ich für CX963?"
Expected: Teilenummer, Kompatibilität, Quelle
```

### **Test 3: Kontext-Bewusstsein**
```
User: "Ich habe einen Lexmark CX963"
Agent: "Verstanden. Welches Problem hast du?"
User: "Fehlercode C-9402"
Expected: Agent nutzt CX963 aus Kontext
```

### **Test 4: Video-Suche**
```
User: "Zeig mir ein Video wie ich die Fuser Unit tausche"
Expected: YouTube-Links mit Beschreibung
```

---

## 🔧 **Troubleshooting**

### **Problem: Tools werden nicht aufgerufen**
**Lösung:**
1. Prüfe ob Sub-Workflows importiert sind
2. Prüfe Workflow-IDs in Tool-Definitionen
3. Erhöhe Temperature auf 0.3-0.5

### **Problem: Keine Ergebnisse**
**Lösung:**
1. Prüfe ob Daten in DB vorhanden: `SELECT COUNT(*) FROM krai_core.error_codes;`
2. Teste SQL Functions direkt: `SELECT * FROM krai_intelligence.search_error_codes('C-9402');`
3. Prüfe Permissions: `GRANT EXECUTE ON FUNCTION ... TO authenticated;`

### **Problem: Postgres Connection Error**
**Lösung:**
1. Prüfe Supabase Credentials
2. Aktiviere "Pooler" in Supabase (Port 6543)
3. Nutze Connection String: `postgresql://postgres:password@host:6543/postgres`

---

## 📊 **Performance-Optimierung**

### **1. Indexes erstellt:**
- ✅ `error_codes.error_code` (GIN trigram)
- ✅ `parts.part_name` (GIN trigram)
- ✅ `parts.part_number` (GIN trigram)
- ✅ `products.model_number` (GIN trigram)
- ✅ `videos.title` (GIN trigram)
- ✅ `chunks.text_chunk` (GIN trigram)

### **2. Query-Optimierung:**
- Limit auf 5-10 Ergebnisse
- Similarity-Ranking für beste Matches
- Exact Match bevorzugt

### **3. Caching:**
- Postgres Chat Memory (10 Messages)
- Session-basiert (kein User-übergreifendes Bleeding)

---

## 🎯 **Nächste Schritte**

### **Phase 1: Basis-Funktionalität** ✅
- [x] SQL Functions erstellen
- [x] Haupt-Workflow erstellen
- [x] Error Code Search Tool
- [x] Parts Search Tool

### **Phase 2: Erweiterte Tools** ⏳
- [ ] Product Info Tool
- [ ] Video Search Tool
- [ ] Documentation Search Tool (Vector)

### **Phase 3: UI/UX** ⏳
- [ ] Mobile-optimiertes Chat-Interface
- [ ] Rich Formatting (Markdown, Emojis)
- [ ] Image-Support (Teile-Bilder, Diagramme)

### **Phase 4: Advanced Features** ⏳
- [ ] Voice Input (für Techniker mit schmutzigen Händen)
- [ ] Offline-Modus (PWA)
- [ ] Push-Notifications
- [ ] Multi-Language (EN, DE, FR)

---

## 📱 **Mobile App Integration**

### **Option 1: PWA (Progressive Web App)**
```javascript
// manifest.json
{
  "name": "KRAI Technician Assistant",
  "short_name": "KRAI Tech",
  "start_url": "/chat",
  "display": "standalone",
  "theme_color": "#2563eb",
  "icons": [...]
}
```

### **Option 2: Native App (React Native)**
```javascript
// API Integration
const response = await fetch('https://n8n.your-domain.com/webhook/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: userInput,
    sessionId: deviceId
  })
});
```

---

## 🔐 **Security**

### **1. API Authentication:**
```sql
-- RLS Policy für Tools
CREATE POLICY "Tools nur für authenticated users"
ON krai_intelligence.chunks
FOR SELECT
TO authenticated
USING (true);
```

### **2. Rate Limiting:**
```javascript
// n8n Webhook mit Rate Limit
{
  "rateLimit": {
    "limit": 100,
    "window": "1h",
    "key": "{{ $json.sessionId }}"
  }
}
```

### **3. Input Validation:**
```javascript
// Sanitize user input
const sanitized = userInput
  .replace(/[<>]/g, '')
  .substring(0, 500);
```

---

## 📈 **Analytics**

### **Track Tool Usage:**
```sql
CREATE TABLE krai_analytics.tool_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id TEXT,
  tool_name TEXT,
  query TEXT,
  results_count INTEGER,
  response_time_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Track User Satisfaction:**
```sql
CREATE TABLE krai_analytics.feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id TEXT,
  message_id TEXT,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🎓 **Training & Onboarding**

### **Für Techniker:**
1. **Quick Start Video** (2 Min)
2. **Beispiel-Fragen** (Cheat Sheet)
3. **Best Practices** (Wie stelle ich gute Fragen?)

### **Beispiel-Fragen:**
```
✅ "Lexmark CX963 Fehlercode C-9402"
✅ "Welche Fuser Unit für CX963?"
✅ "Wie tausche ich die Drum Unit?"
✅ "Zeig mir ein Video"

❌ "Drucker kaputt" (zu unspezifisch)
❌ "Hilfe" (keine Info)
```

---

## 📞 **Support**

Bei Fragen oder Problemen:
- 📧 Email: support@krai.de
- 💬 Slack: #krai-agent
- 📖 Docs: https://docs.krai.de

---

**Version:** 2.1.0  
**Letzte Aktualisierung:** 2025-10-11  
**Status:** ✅ Ready for Testing
