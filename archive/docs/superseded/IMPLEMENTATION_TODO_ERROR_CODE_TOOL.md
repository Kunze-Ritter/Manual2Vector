# 🔧 KR-AI Error Code Tool Implementation - CRITICAL PRIORITY

## ❌ PROBLEM IDENTIFIED
- Agent System Message referenziert `search_error_code_multi_source` Tool
- **Tool ist NICHT implementiert** → Kritischer Systemausfall!
- Agent kann keine Error Code Lösungen liefern
- System funktioniert nur teilweise

---

## 📊 CURRENT STATE ANALYSIS

### ✅ Already Implemented
1. **Error Code Extraction** (`backend/processors/error_code_extractor.py`)
   - Hersteller-spezifische Patterns (HP, Canon, Konica Minolta, etc.)
   - Strikte Validierung und Confidence Scoring
   - Context-basierte Extraktion

2. **Database Schema**
   - `krai_intelligence.error_codes` Tabelle
   - `error_code_parts` Verknüpfungstabelle
   - `chunks` für Dokument-Kontext

3. **Parts Integration** (`backend/processors/parts_linker.py`)
   - Error Codes ↔ Parts Verknüpfung
   - Solution text mining für Teilenummern
   - Proximity-based linking

4. **Pipeline Integration**
   - Automatische Extraction bei PDF-Verarbeitung
   - Enrichment mit vollständigen Lösungen
   - N8N Agent ready (ohne Such-Tool)

### ❌ Missing Critical Component
**`search_error_code_multi_source` Tool** - NICHT IMPLEMENTIERT!

---

## 🎯 IMPLEMENTATION PLAN

### 1. FastAPI Tool Endpoint
**File:** `backend/api/tools/error_code_search.py`
- Multi-source Error Code Search
- Database query optimization
- Response formatting

### 2. Agent Integration
**File:** `backend/api/agent_tools.py`
- Tool registration
- Parameter validation
- Error handling

### 3. Database Query Logic
- Enhanced vw_error_codes view
- Parts linking optimization
- Search indexing

### 4. Response System
- Standardized error code format
- Multi-source aggregation
- Solution highlighting

---

## 🚀 IMMEDIATE ACTIONS

### Phase 1: Core Tool Implementation
- [ ] Create `search_error_code_multi_source` FastAPI endpoint
- [ ] Implement database query logic
- [ ] Add response formatting
- [ ] Test with existing error codes

### Phase 2: Agent Integration  
- [ ] Register tool in agent system
- [ ] Add parameter validation
- [ ] Test agent tool calling

### Phase 3: System Integration
- [ ] Update agent system message (remove strict tool requirements)
- [ ] Test end-to-end workflow
- [ ] Performance optimization

---

## 🔍 TECHNICAL REQUIREMENTS

### Input Parameters
```json
{
  "error_code": "30.03.30",    // Required
  "manufacturer": "HP",        // Required  
  "product": "X580"            // Optional
}
```

### Output Format (exactly as in Agent System Message)
```
🔴 ERROR CODE: 30.03.30
📝 Scanner motor failure

📖 DOKUMENTATION (2):
1. HP_X580_Service_Manual.pdf (Seite 325)
   💡 Lösung: Check cable connections...
   🔧 Parts: ABC123

2. HP_X580_CPMD.pdf (Seite 45)
   💡 Clean scanner motor
   🔧 Parts: XYZ789

🎬 VIDEOS (1):
1. HP X580 Scanner Repair (5:23)
   🔗 https://youtube.com/...

💡 Möchtest du mehr Details?
```

---

## 🎯 SUCCESS METRICS
- [ ] Tool responds with exact format as specified
- [ ] Multi-source aggregation works
- [ ] Parts linking functional
- [ ] Agent integration seamless
- [ ] Performance < 2s response time

---

## ⚠️ CRITICAL NOTES
- **MUST** return exact tool response (no modifications)
- **NO** prefixes ("User:", "Du:")
- **NO** additional recommendations
- **EXACTLY** as specified in Agent System Message V2.4

---

**STATUS:** 🔴 CRITICAL - Tool missing, system partially broken
**PRIORITY:** 🔥 HIGHEST - Agent functionality depends on this
**ESTIMATE:** 4-6 hours implementation
