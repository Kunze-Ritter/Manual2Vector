# KRAI AI Agent Workflow - Komplettanleitung

## 🎯 Übersicht

Der KRAI AI Agent ist ein intelligenter Chat-Assistent mit Zugriff auf:
- **Vector Search** → Durchsucht technische Dokumentation
- **Postgres Memory** → Speichert Konversations-Historie
- **System Status Tool** → Zeigt Statistiken
- **Ollama LLM** → llama3.2 für Chat-Antworten

---

## 📋 Workflow-Architektur

```
┌─────────────────────────────────────────────────────────┐
│              When chat message received                 │
│                  (Chat Trigger)                         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                  KRAI AI Agent                          │
│            (LangChain Agent Node)                       │
│                                                          │
│  ┌─────────────────┐  ┌────────────────────────────┐   │
│  │  Language Model │  │  Postgres Chat Memory      │   │
│  │  llama3.2       │  │  (vw_agent_memory)         │   │
│  └─────────────────┘  └────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Tools:                                          │   │
│  │  - KRAI Vector Store (krai_intelligence)        │   │
│  │  - System Status Tool (get_system_status)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Hauptkomponenten

### 1. **Chat Trigger**
- **Node**: `When chat message received`
- **Type**: Chat Trigger
- **Input**: User-Nachricht vom Chat-Interface
- **Output**: `chatInput`, `sessionId`

### 2. **AI Agent**
- **Node**: `KRAI AI Agent`
- **Type**: LangChain Agent
- **Model**: Ollama llama3.2:latest
- **Temperature**: 0.7
- **Max Tokens**: 2000

**System Prompt:**
```
Du bist der KRAI AI Agent - ein intelligenter technischer Assistent.

Aufgaben:
- Technische Hilfe (Drucker, Kopierer, Geräte)
- Fehlercode-Analyse
- Modell-Informationen
- System-Status

Tools:
1. Vector Search (krai_intelligence) - Dokumentation
2. System Status - Statistiken

Antworte: Deutsch, präzise, strukturiert, mit Quellen
```

### 3. **Postgres Chat Memory**
- **Node**: `Postgres Chat Memory`
- **Table**: `vw_agent_memory`
- **Session Key**: `{{ $json.sessionId }}`
- **Context Window**: 10 Messages
- **Fields**:
  - `session_id` → Session Identifier
  - `role` → technician, user, ai, etc.
  - `message` → Chat-Inhalt
  - `metadata` → Zusätzliche Daten

**✅ Wichtig**: 
- Memory wird **automatisch** vom Agent verwaltet
- Keine manuellen INSERT/UPDATE nötig!
- Agent liest automatisch Historie aus DB

### 4. **KRAI Vector Store**
- **Node**: `KRAI Vector Store`
- **Type**: Supabase Vector Store (Tool)
- **Table**: `vw_embeddings`
- **Embedding Column**: `embedding`
- **Top K**: 5 (best matches)
- **Embeddings**: nomic-embed-text:latest

**Tool-Beschreibung für Agent:**
```
Durchsuche die KRAI Dokumentation und technische Handbücher.

Nutze für:
- Fehlercode-Informationen (z.B. 'Error E045')
- Reparatur-Anleitungen
- Technische Spezifikationen
- Wartungshinweise
- Bedienungsanleitungen

Gib relevante Suchbegriffe ein.
```

### 5. **System Status Tool**
- **Node**: `Tool: System Status`
- **Type**: Workflow Tool
- **Function**: `get_system_status`
- **Query**: SQL-Abfrage auf Supabase

**Rückgabe:**
```json
{
  "total_documents": 34,
  "completed_documents": 30,
  "pending_documents": 4,
  "total_chunks": 58614,
  "total_images": 9223,
  "total_embeddings": 45000,
  "total_products": 150,
  "total_manufacturers": 6,
  "last_document_added": "2025-10-02T15:30:00Z"
}
```

---

## 🚀 Setup-Anleitung

### Schritt 1: Credentials konfigurieren

**Ollama API:**
```
Host: http://localhost:11434
```

**Supabase API:**
```
Host: https://crujfdpqdjzcfqeyhang.supabase.co
Service Role Key: [AUS .env]
```

**Postgres (für Memory):**
```
Host: aws-1-eu-central-1.pooler.supabase.com
Port: 6543
Database: postgres
User: postgres.crujfdpqdjzcfqeyhang
Password: [AUS credentials.txt]
SSL: require
```

### Schritt 2: Memory-Tabelle konfigurieren

**Postgres Chat Memory Node → Settings:**

1. **Connection**: Postgres Supabase
2. **Table Name**: `vw_agent_memory`
3. **Session ID Type**: Custom Key
4. **Session Key**: `={{ $json.sessionId }}`
5. **Advanced Settings**:
   - **Session ID Column**: `session_id`
   - **Message Column**: `message`
   - **Role Column**: `role`
   - **Context Window**: 10

### Schritt 3: Vector Store konfigurieren

**KRAI Vector Store Node → Settings:**

1. **Connection**: Supabase account
2. **Mode**: Retrieve as Tool
3. **Tool Name**: `krai_intelligence`
4. **Tool Description**: [Siehe oben]
5. **Table**: `vw_embeddings`
6. **Query Column**: `embedding`
7. **Top K**: 5
8. **Embeddings**: Connect to `Embeddings Ollama` node

### Schritt 4: Workflow aktivieren

1. **Import**: `KRAI-Agent-Fixed.json` in n8n
2. **Update Credentials**: Alle Credentials prüfen
3. **Test Execution**: Test-Nachricht senden
4. **Activate**: Workflow aktivieren

---

## 💡 Verwendungs-Beispiele

### Beispiel 1: Fehlercode-Abfrage

**User Input:**
```
Was bedeutet Error Code E045 bei einem HP LaserJet Drucker?
```

**Agent Verhalten:**
1. ✅ Lädt Konversations-Historie (Postgres Memory)
2. ✅ Analysiert Frage → Erkennt Fehlercode
3. ✅ Nutzt **krai_intelligence Tool** (Vector Search)
4. ✅ Findet relevante Dokumentation
5. ✅ Antwortet mit Lösung + Quelle
6. ✅ Speichert Antwort in Memory

**Agent Output:**
```
Error Code E045 bei HP LaserJet bedeutet "Paper Jam" (Papierstau).

📋 Lösung:
1. Drucker ausschalten
2. Papierkassette öffnen
3. Gestautes Papier vorsichtig entfernen
4. Papierpfad prüfen
5. Kassette schließen und Drucker neustarten

📖 Quelle: HP LaserJet Service Manual, Seite 45
```

### Beispiel 2: System-Status Abfrage

**User Input:**
```
Zeige mir den aktuellen System-Status
```

**Agent Verhalten:**
1. ✅ Erkennt Status-Anfrage
2. ✅ Nutzt **get_system_status Tool**
3. ✅ Führt SQL-Query aus
4. ✅ Formatiert Ergebnis

**Agent Output:**
```
📊 KRAI System Status:

📄 Dokumente:
  - Gesamt: 34
  - Abgeschlossen: 30
  - In Bearbeitung: 4

📝 Inhalte:
  - Text-Chunks: 58,614
  - Bilder: 9,223
  - Vector-Embeddings: 45,000

🏭 Katalog:
  - Produkte: 150
  - Hersteller: 6

⏱️ Letzte Aktivität: 02.10.2025, 15:30
```

### Beispiel 3: Modell-Information

**User Input:**
```
Welche HP LaserJet Modelle unterstützen duplex printing?
```

**Agent Verhalten:**
1. ✅ Nutzt Vector Store für Modell-Specs
2. ✅ Filtert nach Duplex-Feature
3. ✅ Listet Modelle auf

### Beispiel 4: Kontext-basiertes Follow-up

**User Input 1:**
```
Was kostet der Toner für den HP LaserJet Pro M404dn?
```

**Agent Output 1:**
```
Der originale HP 58A Toner (CF258A) kostet ca. 75-85 EUR.
```

**User Input 2:**
```
Wie oft muss ich den wechseln?
```

**Agent Verhalten:**
- ✅ **Memory** lädt vorherige Konversation
- ✅ Versteht "den" = HP 58A Toner
- ✅ Antwortet kontextbasiert

**Agent Output 2:**
```
Der HP 58A Toner hat eine Reichweite von ca. 3.000 Seiten bei 5% Deckung.

Bei durchschnittlichem Druck (500 Seiten/Monat) → ca. alle 6 Monate.
Bei hohem Volumen (1.500 Seiten/Monat) → ca. alle 2 Monate.
```

---

## 🐛 Troubleshooting

### Problem 1: Memory funktioniert nicht

**Symptome:**
- Agent vergisst vorherige Nachrichten
- Keine Kontext-Awareness

**Lösung:**
```sql
-- Prüfe Memory-Einträge:
SELECT * FROM vw_agent_memory 
WHERE session_id = 'YOUR_SESSION_ID' 
ORDER BY created_at DESC 
LIMIT 10;
```

**Checkliste:**
- ✅ Table Name = `vw_agent_memory`
- ✅ Session Key = `={{ $json.sessionId }}`
- ✅ Postgres Credentials korrekt
- ✅ Session ID wird vom Chat Trigger generiert

### Problem 2: Vector Search findet nichts

**Symptome:**
- Agent sagt "Keine Informationen gefunden"
- Tool wird nicht genutzt

**Lösung:**
```sql
-- Prüfe Embeddings:
SELECT COUNT(*) FROM krai_intelligence.embeddings;

-- Prüfe Vector Store View:
SELECT COUNT(*) FROM vw_embeddings WHERE embedding IS NOT NULL;
```

**Checkliste:**
- ✅ Embeddings vorhanden (>0)
- ✅ Table = `vw_embeddings`
- ✅ Embedding Model = `nomic-embed-text:latest`
- ✅ Tool ist als "Retrieve as Tool" konfiguriert

### Problem 3: Agent antwortet nicht

**Symptome:**
- Workflow hängt
- Keine Antwort

**Lösung:**
1. **Ollama läuft?**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Model geladen?**
   ```bash
   ollama list
   # Sollte zeigen: llama3.2:latest, nomic-embed-text:latest
   ```

3. **Logs prüfen:**
   - n8n → Executions → Letzte Ausführung
   - Suche nach Fehlern

### Problem 4: "Got unexpected type: undefined"

**Lösung:**
- ✅ Migration 11 + 12 ausgeführt?
- ✅ Alle Memory-Spalten NOT NULL?
- ✅ `message` Spalte existiert?

```sql
-- Prüfe Table Schema:
\d krai_agent.memory;

-- Sollte zeigen:
-- message    | text                     | not null
-- content    | text                     | not null
-- metadata   | jsonb                    | not null | default '{}'::jsonb
-- tokens_used| integer                  | not null | default 0
```

---

## 📊 Monitoring & Logs

### Conversation Logs anzeigen

```sql
-- Alle Sessions:
SELECT DISTINCT session_id, MAX(created_at) as last_activity
FROM vw_agent_memory
GROUP BY session_id
ORDER BY last_activity DESC;

-- Spezifische Session:
SELECT 
    created_at,
    role,
    LEFT(message, 100) as message_preview
FROM vw_agent_memory
WHERE session_id = 'YOUR_SESSION_ID'
ORDER BY created_at ASC;
```

### Tool Usage Tracking

```sql
-- In der Zukunft: Tool-Nutzung tracken
SELECT 
    metadata->>'tool_used' as tool_name,
    COUNT(*) as usage_count
FROM vw_agent_memory
WHERE metadata ? 'tool_used'
GROUP BY tool_name
ORDER BY usage_count DESC;
```

---

## 🎯 Best Practices

### 1. Session IDs

**✅ Gut:**
```
sessionId = "user-123-2025-10-02"
sessionId = "tech-session-{timestamp}"
sessionId = "customer-{customer_id}"
```

**❌ Schlecht:**
```
sessionId = "session"  // Zu generisch, alle Nutzer teilen sich Historie
sessionId = Math.random()  // Nie wiederauffindbar
```

### 2. Role Types nutzen

```javascript
// In Chat Trigger oder vorher:
{
  "sessionId": "tech-001",
  "role": "technician",  // Kontext für Agent
  "chatInput": "Wie behebe ich Error E045?"
}
```

### 3. System Prompt anpassen

```javascript
// Für Techniker:
"Du bist ein technischer Experte für Service-Techniker..."

// Für Kunden:
"Du bist ein freundlicher Kundenservice-Assistent..."

// Für Manager:
"Du bist ein Daten-Analyst für Management-Berichte..."
```

### 4. Tool-Descriptions präzise formulieren

**✅ Gut:**
```
"Durchsuche technische Dokumentation für Fehler-Codes, 
Reparatur-Anleitungen und Wartungshinweise. 
Gib spezifische Suchbegriffe ein (z.B. 'Error E045 paper jam')."
```

**❌ Schlecht:**
```
"Search documents"  // Zu vage, Agent weiß nicht wann er es nutzen soll
```

---

## 🔗 Related Documentation

- **Memory Setup**: `N8N_POSTGRES_MEMORY_INTEGRATION.md`
- **Role Types**: `../database/migrations/AGENT_MEMORY_ROLES.md`
- **Vector Search**: `../architecture/PIPELINE_DOCUMENTATION.md`
- **Database Schema**: `../database/migrations/DATABASE_SCHEMA_DOCUMENTATION.md`

---

## 📝 Changelog

| Date | Change | Version |
|------|--------|---------|
| 2025-10-02 | Initial fixed workflow | 1.0 |
| 2025-10-02 | Added System Status Tool | 1.1 |
| 2025-10-02 | Fixed Memory configuration | 1.2 |
| 2025-10-02 | Updated embedding model to nomic-embed-text | 1.3 |

---

**Fragen? Siehe Troubleshooting oder prüfe die n8n Execution Logs!** 🚀
