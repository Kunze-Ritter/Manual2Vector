# ⚠️ DEPRECATED - n8n Deployment Guide

**Status**: Deprecated (Januar 2025)

Diese Deployment-Anleitung ist **nicht mehr gültig** für die aktuelle PostgreSQL-only Architektur.

## Aktuelle Deployment-Optionen

### 1. Laravel Dashboard (Empfohlen)
```bash
cd laravel-admin
composer install
php artisan serve
```
Siehe: `docs/LARAVEL_DASHBOARD_INTEGRATION.md`

### 2. FastAPI Backend
```bash
cd backend
uvicorn api.app:app --host 0.0.0.0 --port 8000
```
Siehe: `DEPLOYMENT.md`

### 3. Docker Compose (Komplett-Setup)
```bash
docker-compose up -d
```
Siehe: `DOCKER_SETUP.md`

---

## Historische n8n Deployment-Dokumentation (Read-Only)

Die folgende Anleitung beschreibt das **veraltete** n8n Deployment mit Supabase.

---

# KRAI Technician Agent V2.1 - Deployment Guide (Legacy)

> **⚠️ DEPRECATED - Legacy Supabase Architecture**  
> This deployment guide references legacy Supabase architecture (pre-KRAI-002).  
> **Status:** Deprecated as of November 2024  
> **Alternative:** Use Laravel Dashboard or FastAPI endpoints  
> **Reference:** See `README_DEPRECATION.md` for current alternatives

> **Note**: n8n is not part of the core KRAI stack. This guide references archived configurations available in `archive/docker/docker-compose.yml`. For the main KRAI system, use the active compose files: `docker-compose.simple.yml`, `docker-compose.with-firecrawl.yml`, or `docker-compose.production.yml`.

## 🚀 **Production Deployment Checklist**

### **Phase 1: Database Setup** ✅

#### **1.1 Apply Migrations**
```bash
# Connect to Supabase
psql -h your-project.supabase.co -U postgres -d postgres

# Apply migrations in order
\i database/migrations/75_agent_tool_functions.sql
\i database/migrations/76_agent_enhancements.sql
```

**Verify:**
```sql
-- Check functions exist
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'krai_intelligence' 
  AND routine_name LIKE 'search_%';

-- Expected output:
-- search_error_codes
-- search_parts
-- search_videos
-- search_documentation_context
-- get_product_info
-- get_session_context
-- smart_search
```

#### **1.2 Test Functions**
```sql
-- Test error code search
SELECT * FROM krai_intelligence.search_error_codes('C-9402', 'Lexmark', 'CX963');

-- Test parts search
SELECT * FROM krai_intelligence.search_parts('Fuser Unit', NULL, 'Lexmark', NULL);

-- Test product info
SELECT * FROM krai_intelligence.get_product_info('CX963', 'Lexmark');

-- Should return results if data exists
```

---

### **Phase 2: n8n Setup** ✅

#### **2.1 Import Workflows**

**Main Workflow:**
1. n8n → Workflows → Import from File
2. Select: `n8n/workflows/v2/Technician-Agent-V2.1.json`
3. Click "Import"

**Tool Workflows (Sub-Workflows):**
1. Import: `Tool-ErrorCodeSearch.json`
2. Import: `Tool-PartsSearch.json`
3. Import: `Tool-ProductInfo.json`
4. Import: `Tool-VideoSearch.json`
5. Import: `Tool-DocumentationSearch.json`

#### **2.2 Configure Credentials**

**Supabase Postgres:**
```
Name: Supabase Postgres
Type: Postgres
Host: your-project.supabase.co
Port: 6543 (Pooler) or 5432 (Direct)
Database: postgres
User: postgres
Password: your-supabase-password
SSL: Require
```

**Test Connection:**
```sql
SELECT 1;
-- Should return: 1
```

**Ollama:**
```
Name: Ollama
Type: Ollama
Base URL: http://localhost:11434
```

**Test Connection:**
```bash
curl http://localhost:11434/api/tags
# Should return list of models
```

#### **2.3 Update Workflow IDs**

**IMPORTANT:** Tool-Workflows müssen die richtigen Workflow-IDs haben!

1. Öffne jeden Tool-Workflow
2. Kopiere die Workflow-ID aus der URL: `https://n8n.../workflow/{ID}`
3. Öffne `Technician-Agent-V2.1.json`
4. Suche nach `"workflowId": "={{ $workflow.id }}"`
5. Ersetze mit der tatsächlichen ID

**Oder:** Nutze die dynamische Referenz (empfohlen):
- Workflows müssen aktiviert sein
- n8n findet sie automatisch über den Namen

#### **2.4 Activate Workflows**

1. Aktiviere alle Tool-Workflows (Sub-Workflows)
2. Aktiviere Haupt-Workflow (Technician-Agent-V2.1)
3. Prüfe Status: Alle sollten "Active" sein

---

### **Phase 3: Testing** ✅

#### **3.1 Unit Tests (SQL Functions)**

```bash
# Run test script
psql -h your-project.supabase.co -U postgres -d postgres -f tests/test_agent_functions.sql
```

**Expected Results:**
- ✅ All functions return results
- ✅ No errors
- ✅ Response time < 1s

#### **3.2 Integration Tests (n8n Workflows)**

**Test Each Tool:**
1. Open Tool-Workflow
2. Click "Execute Workflow"
3. Provide test input:
   ```json
   {
     "error_code": "C-9402",
     "manufacturer": "Lexmark",
     "model": "CX963"
   }
   ```
4. Check output

**Expected Results:**
- ✅ Workflow executes successfully
- ✅ Returns formatted results
- ✅ No errors

#### **3.3 End-to-End Tests (Chat Interface)**

**Test Scenarios:**
```
1. "Lexmark CX963 Fehlercode C-9402"
2. "Welche Fuser Unit brauche ich für CX963?"
3. "Zeig mir ein Video"
4. "Wie tausche ich die Drum Unit?"
```

**Expected Results:**
- ✅ Agent responds within 5s
- ✅ Uses correct tools
- ✅ Provides structured answers
- ✅ Includes sources
- ✅ Memory works (context-aware)

---

### **Phase 4: Monitoring** 📊

#### **4.1 Setup Monitoring Dashboard**

**Supabase Dashboard:**
```sql
-- Create monitoring view
CREATE OR REPLACE VIEW krai_analytics.live_monitoring AS
SELECT 
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as calls_last_hour,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as calls_last_day,
    AVG(response_time_ms) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as avg_response_time,
    COUNT(*) FILTER (WHERE success = false AND created_at > NOW() - INTERVAL '1 hour') as errors_last_hour
FROM krai_analytics.tool_usage;
```

**Query Dashboard:**
```sql
SELECT * FROM krai_analytics.live_monitoring;
```

#### **4.2 Setup Alerts**

**Supabase Edge Function (Webhook):**
```javascript
// Alert if error rate > 10%
const { data } = await supabase
  .from('krai_analytics.tool_usage')
  .select('*')
  .gte('created_at', new Date(Date.now() - 3600000).toISOString())
  .eq('success', false);

if (data.length > 10) {
  // Send alert (Slack, Email, etc.)
  await fetch('https://hooks.slack.com/...', {
    method: 'POST',
    body: JSON.stringify({
      text: `⚠️ High error rate: ${data.length} errors in last hour`
    })
  });
}
```

#### **4.3 Performance Metrics**

**Track:**
- ✅ Response time (avg, p95, p99)
- ✅ Tool usage (which tools are used most)
- ✅ Error rate (% of failed calls)
- ✅ User satisfaction (feedback ratings)

**Query:**
```sql
-- Daily performance report
SELECT 
    date,
    tool_name,
    total_calls,
    avg_response_time_ms,
    p95_response_time_ms,
    (failed_calls::FLOAT / total_calls * 100) as error_rate_percent
FROM krai_analytics.agent_performance
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, total_calls DESC;
```

---

### **Phase 5: Optimization** ⚡

#### **5.1 Database Optimization**

**Indexes:**
```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname IN ('krai_core', 'krai_intelligence')
ORDER BY idx_scan DESC;
```

**Vacuum:**
```sql
-- Run weekly
VACUUM ANALYZE krai_core.error_codes;
VACUUM ANALYZE krai_core.parts;
VACUUM ANALYZE krai_intelligence.chunks;
```

#### **5.2 Query Optimization**

**Slow Queries:**
```sql
-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%krai_%'
ORDER BY mean_time DESC
LIMIT 10;
```

**Optimize:**
- Add missing indexes
- Reduce LIMIT if too many results
- Use materialized views for heavy queries

#### **5.3 Caching**

**Redis Cache (optional):**
```javascript
// Cache frequent queries
const cacheKey = `error_code:${errorCode}:${manufacturer}`;
const cached = await redis.get(cacheKey);

if (cached) {
  return JSON.parse(cached);
}

const result = await supabase.rpc('search_error_codes', { ... });
await redis.setex(cacheKey, 3600, JSON.stringify(result)); // 1 hour TTL
return result;
```

---

### **Phase 6: Scaling** 📈

#### **6.1 Horizontal Scaling**

**n8n:**
```yaml
# docker-compose.yml
services:
  n8n-worker-1:
    image: n8nio/n8n
    environment:
      - N8N_EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
  
  n8n-worker-2:
    image: n8nio/n8n
    environment:
      - N8N_EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
  
  redis:
    image: redis:alpine
```

**Supabase:**
- Upgrade to Pro plan (more connections)
- Enable connection pooling (PgBouncer)
- Use read replicas for analytics

#### **6.2 Load Balancing**

**NGINX:**
```nginx
upstream n8n_backend {
    least_conn;
    server n8n-worker-1:5678;
    server n8n-worker-2:5678;
}

server {
    listen 443 ssl;
    server_name agent.krai.de;
    
    location / {
        proxy_pass http://n8n_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### **6.3 Rate Limiting**

**Supabase Edge Function:**
```javascript
// Rate limit: 100 requests per hour per session
const { data: usage } = await supabase
  .from('krai_analytics.tool_usage')
  .select('*', { count: 'exact' })
  .eq('session_id', sessionId)
  .gte('created_at', new Date(Date.now() - 3600000).toISOString());

if (usage.length >= 100) {
  return new Response('Rate limit exceeded', { status: 429 });
}
```

---

### **Phase 7: Security** 🔐

#### **7.1 API Authentication**

**Supabase RLS:**
```sql
-- Enable RLS on analytics tables
ALTER TABLE krai_analytics.tool_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_analytics.feedback ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY "Users see own analytics"
ON krai_analytics.tool_usage
FOR SELECT
TO authenticated
USING (session_id = current_setting('request.jwt.claims')::json->>'session_id');
```

#### **7.2 Input Validation**

**n8n Code Node:**
```javascript
// Sanitize user input
const sanitizeInput = (input) => {
  return input
    .replace(/[<>]/g, '') // Remove HTML tags
    .replace(/[;]/g, '') // Remove SQL injection attempts
    .substring(0, 500); // Limit length
};

const cleanInput = sanitizeInput($json.chatInput);
```

#### **7.3 Secrets Management**

**Environment Variables:**
```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key # NEVER expose to frontend!
OLLAMA_BASE_URL=http://localhost:11434
```

**n8n:**
- Use Credentials (encrypted)
- Never hardcode secrets in workflows
- Use environment variables

---

### **Phase 8: Backup & Recovery** 💾

#### **8.1 Database Backups**

**Supabase:**
- Daily automatic backups (Pro plan)
- Point-in-time recovery (PITR)
- Manual backups before migrations

**Manual Backup:**
```bash
pg_dump -h your-project.supabase.co -U postgres -d postgres \
  --schema=krai_core \
  --schema=krai_intelligence \
  --schema=krai_analytics \
  > backup_$(date +%Y%m%d).sql
```

#### **8.2 n8n Backups**

**Export Workflows:**
```bash
# Export all workflows
n8n export:workflow --all --output=./backups/workflows/

# Export credentials (encrypted)
n8n export:credentials --all --output=./backups/credentials/
```

#### **8.3 Disaster Recovery Plan**

**RTO (Recovery Time Objective):** < 1 hour
**RPO (Recovery Point Objective):** < 24 hours

**Steps:**
1. Restore database from latest backup
2. Import n8n workflows
3. Reconfigure credentials
4. Test all workflows
5. Activate workflows
6. Monitor for issues

---

### **Phase 9: Documentation** 📚

#### **9.1 User Documentation**

**For Technicians:**
- Quick Start Guide (2 pages)
- Example Questions (cheat sheet)
- Troubleshooting (common issues)
- Video Tutorial (5 min)

#### **9.2 Developer Documentation**

**For Developers:**
- Architecture Overview
- API Reference
- Database Schema
- Deployment Guide (this document)

#### **9.3 Runbook**

**For Operations:**
- How to restart services
- How to check logs
- How to apply hotfixes
- Escalation procedures

---

### **Phase 10: Go-Live** 🎉

#### **10.1 Pre-Launch Checklist**

- [ ] All migrations applied
- [ ] All workflows imported and activated
- [ ] Credentials configured
- [ ] Tests passing (unit, integration, e2e)
- [ ] Monitoring setup
- [ ] Alerts configured
- [ ] Backups enabled
- [ ] Documentation complete
- [ ] Team trained

#### **10.2 Soft Launch**

**Week 1: Beta (10 users)**
- Select 10 technicians
- Provide training (30 min)
- Collect feedback daily
- Fix critical bugs

**Week 2: Pilot (50 users)**
- Expand to 50 technicians
- Monitor performance
- Optimize based on usage patterns
- Collect satisfaction scores

**Week 3: Full Launch (all users)**
- Roll out to all technicians
- Announce via email/Slack
- Provide support channel
- Monitor closely for 1 week

#### **10.3 Post-Launch**

**Day 1:**
- Monitor every hour
- Fix critical issues immediately
- Collect feedback

**Week 1:**
- Daily performance review
- Address top issues
- Optimize slow queries

**Month 1:**
- Weekly performance review
- Feature requests prioritization
- User satisfaction survey

---

## 🎯 **Success Metrics**

### **Technical Metrics:**
- ✅ Uptime: > 99.5%
- ✅ Response time: < 5s (p95)
- ✅ Error rate: < 1%
- ✅ Tool success rate: > 95%

### **Business Metrics:**
- ✅ User adoption: > 80% of technicians
- ✅ Daily active users: > 50
- ✅ User satisfaction: > 4.0/5.0
- ✅ Time saved per technician: > 30 min/day

### **Quality Metrics:**
- ✅ Answer accuracy: > 95%
- ✅ Source citation: 100%
- ✅ Context awareness: > 90%
- ✅ Hallucination rate: < 1%

---

## 📞 **Support**

**Technical Issues:**
- 📧 Email: tech-support@krai.de
- 💬 Slack: #krai-agent-support
- 🐛 GitHub Issues: github.com/krai/agent/issues

**User Questions:**
- 📖 Docs: https://docs.krai.de/agent
- 🎥 Videos: https://youtube.com/krai-tutorials
- 💬 Slack: #krai-agent-users

---

**Version:** 2.1.0  
**Last Updated:** 2025-10-11  
**Status:** ✅ Production Ready
