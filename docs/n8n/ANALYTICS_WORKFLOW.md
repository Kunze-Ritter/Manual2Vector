# KRAI Analytics Workflow

## Architecture

### Overview
```
┌─────────────────────────────────────────────────────────────┐
│ KRAI Agent Workflow (Chat)                                  │
│                                                              │
│  User → Chat Trigger → Agent → [Output to User]            │
│                           │                                  │
│                           └──→ HTTP Request (async) ─┐      │
└─────────────────────────────────────────────────────┼──────┘
                                                       │
                                                       ├ Fire & Forget
                                                       │ (3s timeout)
                                                       │
┌──────────────────────────────────────────────────────┼──────┐
│ KRAI Analytics Logger Workflow                      ▼      │
│                                                              │
│  Webhook → Parse & Validate → Save to DB → Respond         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. KRAI Agent Workflow (Main Chat)
**File:** `n8n/workflows/KRAI-Agent.json`

**New Node:** `Log to Analytics (async)`
- Type: HTTP Request
- Method: POST
- URL: `http://n8n:5678/webhook/krai-analytics`
- Timeout: 3s
- `continueOnFail: true` → Chat works even if logging fails!

**Data sent:**
```json
{
  "search_query": "HP E877 Fehler 12.34.56",
  "session_id": "abc-123-def",
  "tools_used": ["krai_intelligence"],
  "results_count": 0,
  "response_length": 245
}
```

---

### 2. KRAI Analytics Logger Workflow
**File:** `n8n/workflows/KRAI-Analytics-Logger.json`

**Nodes:**
1. **Analytics Webhook** - Receives POST requests
2. **Parse & Validate** - Validates & structures data
3. **Save to Analytics DB** - Inserts into `vw_search_analytics`
4. **Respond Success** - Returns confirmation

---

## Setup Instructions

### Step 1: Import Analytics Workflow
1. Open n8n
2. Click **"+"** → **"Import from File"**
3. Select: `n8n/workflows/KRAI-Analytics-Logger.json`
4. **Activate** the workflow

### Step 2: Get Webhook URL
1. Open **KRAI Analytics Logger** workflow
2. Click **Analytics Webhook** node
3. Click **"Test URL"** or **"Production URL"**
4. Copy URL (e.g., `http://n8n:5678/webhook/krai-analytics`)

### Step 3: Update Chat Workflow
1. Open **KRAI Agent** workflow
2. Reload from file (F5) or import updated version
3. Check **Log to Analytics (async)** node exists
4. Verify URL matches webhook from Step 2
5. **Activate** the workflow

### Step 4: Run Migration
```sql
-- In Supabase SQL Editor
-- Execute: database/migrations/16_create_search_analytics_view.sql
-- (If not already done)
```

### Step 5: Test
1. Send test message in chat:
   ```
   HP E877 Fehler 12.34.56
   ```

2. Check Analytics Logger workflow executions
   - Should see successful execution

3. Query analytics database:
   ```sql
   SELECT 
     search_query,
     results_count,
     result_relevance_scores,
     created_at
   FROM vw_search_analytics
   ORDER BY created_at DESC
   LIMIT 10;
   ```

---

## Benefits

### ✅ Non-Blocking
- Chat responds immediately
- Analytics logged asynchronously
- Timeout prevents hanging (3s max)

### ✅ Failure-Resistant
- `continueOnFail: true` on HTTP Request
- Chat works even if analytics fails
- No user-facing errors

### ✅ Decoupled
- Analytics workflow completely separate
- Can be modified independently
- Easy to debug

### ✅ Scalable
- Webhook can handle high volume
- Can add multiple data sinks later
- Easy to add more analytics workflows

---

## Analytics Queries

### Most common queries
```sql
SELECT 
  search_query,
  COUNT(*) as frequency,
  AVG(results_count) as avg_results
FROM vw_search_analytics
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY search_query
ORDER BY frequency DESC
LIMIT 20;
```

### Queries with no results (improve docs!)
```sql
SELECT 
  search_query,
  COUNT(*) as frequency
FROM vw_search_analytics
WHERE results_count = 0
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY search_query
ORDER BY frequency DESC;
```

### Tool usage statistics
```sql
SELECT 
  result_relevance_scores->>'tools_used' as tools,
  COUNT(*) as usage_count
FROM vw_search_analytics
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY tools
ORDER BY usage_count DESC;
```

### Daily analytics summary
```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_queries,
  AVG(results_count) as avg_results,
  COUNT(CASE WHEN results_count = 0 THEN 1 END) as no_results_count
FROM vw_search_analytics
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Troubleshooting

### Analytics not logging
1. **Check Analytics Logger workflow is ACTIVE**
2. **Verify webhook URL in Chat workflow**
3. **Check Analytics Logger executions for errors**
4. **Test webhook directly:**
   ```bash
   curl -X POST http://localhost:5678/webhook/krai-analytics \
     -H "Content-Type: application/json" \
     -d '{
       "search_query": "test",
       "session_id": "test-123",
       "tools_used": [],
       "results_count": 0,
       "response_length": 10
     }'
   ```

### Chat is slow after adding analytics
- Check timeout setting (should be 3s)
- Verify `continueOnFail: true` is set
- Analytics should not block chat!

### Data not appearing in database
1. Check Supabase credentials in Analytics Logger
2. Verify view exists: `SELECT * FROM vw_search_analytics;`
3. Check INSTEAD OF trigger exists
4. Test direct insert to view

---

## Future Enhancements

### Planned
- [ ] Add response time tracking
- [ ] Track user feedback (thumbs up/down)
- [ ] A/B testing support
- [ ] Export to external analytics (Google Analytics, Mixpanel)
- [ ] Real-time dashboard (Grafana/Metabase)

### Ideas
- Sentiment analysis of queries
- Automatic FAQ generation from common queries
- Alert on spike in "no results" queries
- ML model to predict query intent
