# KRAI Agent - TODO & Roadmap

## ✅ FERTIG

- [x] Basic Agent mit LangChain
- [x] 3 Tools: Error Codes, Parts, Videos
- [x] Ollama Integration
- [x] FastAPI Endpoints
- [x] Streaming Support
- [x] In-Memory Conversation History
- [x] Test Suite

## 🔧 VERBESSERUNGEN (Kurzfristig)

### 1. Semantic Search implementieren

**Ziel:** Embedding-basierte Suche über alle Inhalte

**Implementation:**
```python
def semantic_search(self, query: str, limit: int = 5) -> str:
    # 1. Generate embedding for query
    embedding_response = requests.post(
        f"{os.getenv('OLLAMA_URL')}/api/embeddings",
        json={
            "model": "nomic-embed-text:latest",
            "prompt": query
        }
    )
    query_embedding = embedding_response.json()['embedding']
    
    # 2. Search in Supabase with pgvector
    response = self.supabase.rpc(
        'match_documents',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.7,
            'match_count': limit
        }
    ).execute()
    
    # 3. Return formatted results
    return json.dumps(response.data)
```

**Benötigt:**
- [ ] Supabase RPC Function `match_documents`
- [ ] Embeddings in DB (bereits vorhanden?)
- [ ] Testing

**Priorität:** HOCH 🔥

---

### 2. PostgreSQL Memory wiederherstellen

**Problem:** psycopg3 Kompatibilität mit `PostgresChatMessageHistory`

**Lösungen:**
- Option A: Warten auf LangChain Update
- Option B: Custom PostgreSQL Memory implementieren
- Option C: Redis für Session Storage nutzen

**Priorität:** MITTEL

---

### 3. Prompt Tuning

**Aktuell:** Agent halluziniert manchmal noch

**Verbesserungen:**
- [ ] Few-shot Examples hinzufügen
- [ ] Output Format strikter definieren
- [ ] Tool-Auswahl verbessern

**Priorität:** HOCH 🔥

---

## 🚀 FEATURES (Mittelfristig)

### 4. RAG für Service Manuals

**Ziel:** Volltext-Suche in PDFs mit Embeddings

**Features:**
- Chunk-basierte Suche
- Relevanz-Ranking
- Quellenangaben mit Seitenzahl

**Priorität:** HOCH 🔥

---

### 5. Multi-Modal Support (Bilder)

**Ziel:** Techniker kann Fotos hochladen

**Features:**
- OCR für Error Codes auf Display
- Visual Similarity Search
- Error Pattern Recognition

**Benötigt:**
- OpenCV (bereits installiert!)
- Vision Model (llava:7b bereits in .env)
- Image Upload Endpoint

**Priorität:** MITTEL

---

### 6. Conversation Analytics

**Ziel:** Tracking & Insights

**Metriken:**
- Häufigste Fehler
- Tool Usage Stats
- Response Times
- User Satisfaction

**Priorität:** NIEDRIG

---

## 🎯 PRODUCTION (Langfristig)

### 7. Caching

**Ziel:** Schnellere Antworten für häufige Queries

**Implementation:**
- Redis Cache für Tool-Ergebnisse
- LLM Response Cache
- Embedding Cache

**Priorität:** MITTEL

---

### 8. Rate Limiting

**Ziel:** API Schutz

**Features:**
- Per-User Limits
- Token Bucket Algorithm
- Graceful Degradation

**Priorität:** MITTEL

---

### 9. Monitoring & Logging

**Ziel:** Production-Ready Observability

**Tools:**
- Prometheus Metrics
- Grafana Dashboards
- Error Tracking (Sentry)
- Log Aggregation

**Priorität:** HOCH (für Production)

---

### 10. Multi-Language Support

**Ziel:** Englisch, Französisch, Italienisch

**Implementation:**
- Language Detection
- Multi-Language Prompts
- Translated Responses

**Priorität:** NIEDRIG

---

## 📝 NOTES

### Embedding Search - Supabase Setup

```sql
-- Create RPC function for vector search
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) as similarity
  FROM document_chunks
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
```

### Performance Targets

- **Response Time:** < 3s (95th percentile)
- **Tool Call Time:** < 500ms
- **Embedding Generation:** < 200ms
- **Concurrent Users:** 50+

### Known Issues

1. Agent stoppt manchmal bei Conversation Memory (max_iterations)
   - **Fix:** Context Window erhöht auf 32k ✅
   
2. Agent halluziniert manchmal
   - **Fix:** Temperature auf 0.0, strengerer Prompt ✅
   
3. PostgreSQL Memory funktioniert nicht
   - **Status:** In-Memory Fallback aktiv
   - **TODO:** Custom Implementation oder warten auf LangChain Update

---

## 🎉 NEXT STEPS

1. **Test mit neuem Prompt** - Halluzination behoben?
2. **Semantic Search implementieren** - Embedding-basierte Suche
3. **n8n Integration** - Einfacher HTTP Request
4. **Production Deployment** - Docker, Monitoring, etc.
