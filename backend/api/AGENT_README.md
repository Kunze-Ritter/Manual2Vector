# KRAI AI Agent

LangChain-based conversational AI agent for technical support.

## Features

✅ **Error Code Search** - Sucht Fehlercodes in der Datenbank
✅ **Parts Search** - Findet Ersatzteile und Teilenummern
✅ **Video Tutorials** - Sucht Reparatur-Videos
✅ **Conversation Memory** - Speichert Konversationen in PostgreSQL
✅ **Streaming Support** - Echtzeit-Antworten
✅ **Tool-based Architecture** - Verwendet LangChain Tools für strukturierte Suche

## Architecture

```
┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
┌────────▼────────┐
│  KRAI Agent     │
│  (LangChain)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Tools │  │Ollama│
│      │  │ LLM  │
└───┬──┘  └──────┘
    │
┌───▼──────────┐
│ Supabase DB  │
└──────────────┘
```

## API Endpoints

### POST /agent/chat

Chat with the AI agent (non-streaming).

**Request:**
```json
{
  "message": "Konica Minolta C3320i Fehler C9402",
  "session_id": "unique-session-id",
  "stream": false
}
```

**Response:**
```json
{
  "response": "**Fehlercode:** C9402\n**Beschreibung:** CIS LED lighting abnormally...",
  "session_id": "unique-session-id",
  "timestamp": "2025-10-16T08:00:00"
}
```

### POST /agent/chat/stream

Chat with the AI agent (streaming).

**Request:**
```json
{
  "message": "Konica Minolta C3320i Fehler C9402",
  "session_id": "unique-session-id",
  "stream": true
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"chunk": "**Fehlercode:**"}
data: {"chunk": " C9402"}
data: {"chunk": "\n**Beschreibung:**"}
...
data: [DONE]
```

### GET /agent/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "agent": "KRAI AI Agent",
  "version": "1.0.0"
}
```

## Tools

### 1. search_error_codes

Sucht Fehlercodes in der Datenbank.

**Input:** Fehlercode oder Suchbegriff (z.B. "C9402", "Fehler 10.00.33")

**Output:**
```json
{
  "found": true,
  "count": 7,
  "error_codes": [
    {
      "error_code": "C9402",
      "description": "CIS LED lighting abnormally (front side)",
      "solution": "1. Turn OFF the machine...",
      "manufacturer": "Konica Minolta",
      "page_number": 450,
      "severity_level": "medium",
      "source_document": "KM_C3320i_C3321i_SM.pdf",
      "confidence": 1.0
    }
  ]
}
```

### 2. search_parts

Sucht Ersatzteile in der Datenbank.

**Input:** Teilename oder Teilenummer (z.B. "Fuser Unit", "A1234567")

**Output:**
```json
{
  "found": true,
  "count": 5,
  "parts": [
    {
      "part_number": "A1234567",
      "part_name": "Fuser Unit",
      "description": "Fixing unit for...",
      "manufacturer": "HP",
      "compatible_models": ["E877", "E877z"],
      "page_number": 123
    }
  ]
}
```

### 3. search_videos

Sucht Reparatur-Videos.

**Input:** Suchbegriff (z.B. "Fuser austauschen", "HP E877")

**Output:**
```json
{
  "found": true,
  "count": 3,
  "videos": [
    {
      "title": "HP E877 Fuser Replacement",
      "url": "https://youtube.com/watch?v=...",
      "description": "Step-by-step guide...",
      "duration": "10:30",
      "manufacturer": "HP",
      "model_series": "E877"
    }
  ]
}
```

## Installation

1. **Install dependencies:**
```bash
cd backend/api
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
# .env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OLLAMA_BASE_URL=http://ollama:11434
```

3. **Start the API:**
```bash
python app.py
```

The agent will be available at: `http://localhost:8000/agent`

## Usage Examples

### Python Client

```python
import requests

# Non-streaming chat
response = requests.post(
    "http://localhost:8000/agent/chat",
    json={
        "message": "Konica Minolta C3320i Fehler C9402",
        "session_id": "my-session-123"
    }
)

print(response.json()["response"])
```

### Streaming Chat

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/agent/chat/stream",
    json={
        "message": "Konica Minolta C3320i Fehler C9402",
        "session_id": "my-session-123"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data == '[DONE]':
                break
            chunk = json.loads(data)
            print(chunk['chunk'], end='', flush=True)
```

### cURL

```bash
# Non-streaming
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Konica Minolta C3320i Fehler C9402",
    "session_id": "test-123"
  }'

# Streaming
curl -X POST http://localhost:8000/agent/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Konica Minolta C3320i Fehler C9402",
    "session_id": "test-123"
  }'
```

## Integration with n8n

You can still use n8n as a chat interface!

1. **Create a Chat Trigger** in n8n
2. **Add HTTP Request Node:**
   - Method: POST
   - URL: `http://host.docker.internal:8000/agent/chat`
   - Body:
     ```json
     {
       "message": "{{ $json.chatInput }}",
       "session_id": "{{ $json.sessionId }}"
     }
     ```
3. **Return response** to user

**That's it!** No complex agent setup in n8n needed!

## Conversation Memory

The agent stores conversation history in PostgreSQL using LangChain's `PostgresChatMessageHistory`.

**Table:** `message_store`

Each session has its own conversation history identified by `session_id`.

## Logging

The agent logs all tool calls and responses:

```
INFO - Tool called: search_error_codes with query='C9402'
INFO - Extracted error code: 'C9402' from query: 'Konica Minolta C3320i Fehler C9402'
INFO - Agent response: **Fehlercode:** C9402...
```

## Error Handling

- **Tool errors** are caught and returned as JSON
- **Agent errors** return user-friendly error messages
- **API errors** return HTTP 500 with error details

## Performance

- **Response time:** ~2-5 seconds (depending on LLM)
- **Streaming:** Real-time chunks as they're generated
- **Memory:** Minimal overhead with conversation history

## Future Enhancements

- [ ] Add RAG for service manual search
- [ ] Support multiple languages
- [ ] Add voice input/output
- [ ] Implement caching for common queries
- [ ] Add analytics dashboard
- [ ] Support image uploads for visual diagnostics

## Troubleshooting

### Agent not responding

Check Ollama connection:
```bash
curl http://ollama:11434/api/tags
```

### Database connection errors

Verify DATABASE_URL in .env:
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Tool errors

Check Supabase connection:
```bash
curl -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  "$SUPABASE_URL/rest/v1/error_codes?limit=1"
```

## License

Internal use only - Kunze-Ritter GmbH
