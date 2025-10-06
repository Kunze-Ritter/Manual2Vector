# 🧪 N8N Agent V2.1 - Quick Test Guide

**Date:** 2025-10-06  
**Version:** V2.1  
**Status:** Ready to Test

---

## 🚀 **SETUP (5 Minutes)**

### **1. Backend starten:**
```powershell
cd c:\Users\haast\Docker\KRAI-minimal\backend
python main.py
```

**Verify:**
```powershell
# Should return "healthy"
Invoke-RestMethod "http://localhost:8000/health"
```

### **2. N8N starten:**
```powershell
cd c:\Users\haast\Docker\KRAI-minimal\n8n
.\start-n8n-chat-agent.ps1
```

**Verify:**
- Browser öffnet: `http://localhost:5678`
- N8N UI lädt

### **3. Workflow öffnen:**
- In N8N UI: Workflows → "KRAI-Agent-Fixed"
- Oder: Import `KRAI-Agent-Fixed.json`

---

## 🧪 **TESTS (10 Minutes)**

### **TEST 1: Basic Health** ✅
**User Message:**
```
Hi! Kannst du mir den System Status zeigen?
```

**Expected Response:**
```
📊 System Status:

📝 Inhalte:
  - Dokumente: XX
  - Text-Chunks: XX,XXX
  - Bilder: XX,XXX
  - Videos: XX (NEW!)
  - Links: XX (NEW!)
  - Error Codes: XX

🤖 AI Services:
  - Ollama: Running
  - GPU: Enabled
  ...
```

**Status:** [ ] Pass [ ] Fail

---

### **TEST 2: Error Code Search** 🔍
**User Message:**
```
Was bedeutet Error Code C-2801?
```

**Expected Response:**
```
🔴 Error Code: C-2801

📝 Beschreibung:
Paper jam in duplex unit

🔧 Lösung:
1. Open duplex unit cover
2. Remove jammed paper
3. Close cover and restart

📄 Context (aus Manual):
[Text snippet from page]

🖼️ Screenshot:
[Image URL if available]

Quelle: [Document name]
```

**Status:** [ ] Pass [ ] Fail

---

### **TEST 3: Document Search** 📄
**User Message:**
```
Suche nach "Wartung" in den Dokumenten
```

**Expected Response:**
```
🔍 Suchergebnisse für "Wartung":

1. [Document 1]
   Relevanz: 95%
   Text: "...Wartung sollte regelmäßig..."

2. [Document 2]
   Relevanz: 87%
   Text: "...vor der Wartung..."

Gefunden: X Ergebnisse
```

**Status:** [ ] Pass [ ] Fail

---

### **TEST 4: Video Enrichment** 🎬 NEW!
**User Message:**
```
Ich habe ein Wartungsvideo gefunden: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Expected Response:**
```
🎬 Video analysiert!

Titel: [Video Title]
Dauer: XX:XX
Kanal: [Channel Name]
Aufrufe: XX,XXX

📝 Beschreibung:
[Video description]

✅ Video wurde in der Datenbank gespeichert!
```

**Status:** [ ] Pass [ ] Fail

**IMPORTANT:** 
- Agent should call `/content/videos/enrich/sync`
- Should extract metadata
- Should save to database

---

### **TEST 5: Link Validation** 🔗 NEW!
**User Message:**
```
Überprüfe die Links im System
```

**Expected Response:**
```
🔗 Link Überprüfung:

✅ Aktiv: XX Links
⚠️ Weitergeleitet: X Links
❌ Defekt: X Links

Details:
- X http→https Fixes
- X Weiterleitungen gefolgt
- X defekte Links gefunden

Status: Überprüfung abgeschlossen
```

**Status:** [ ] Pass [ ] Fail

**IMPORTANT:**
- Agent should call `/content/links/check/sync`
- Should return link statistics
- Should mention fixes

---

### **TEST 6: Multi-Turn Conversation** 💬
**Turn 1:**
```
User: "Was ist KRAI?"
Expected: Explanation of KRAI system
```

**Turn 2:**
```
User: "Welche Features hat es?"
Expected: List of features (should remember context)
```

**Turn 3:**
```
User: "Zeige mir Error Code C-2801"
Expected: Error code details
```

**Status:** [ ] Pass [ ] Fail

---

## 📊 **TEST RESULTS:**

**Summary:**
- [ ] Test 1: Basic Health
- [ ] Test 2: Error Code Search
- [ ] Test 3: Document Search
- [ ] Test 4: Video Enrichment (NEW!)
- [ ] Test 5: Link Validation (NEW!)
- [ ] Test 6: Multi-Turn Conversation

**Overall:** [ ] All Pass [ ] Some Fail

---

## 🐛 **TROUBLESHOOTING:**

### **Problem 1: Agent doesn't respond**
```powershell
# Check backend
Invoke-RestMethod "http://localhost:8000/health"

# Check N8N
# Browser: http://localhost:5678
```

### **Problem 2: Video enrichment fails**
```powershell
# Test endpoint directly
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/content/videos/enrich/sync" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### **Problem 3: Link validation fails**
```powershell
# Test endpoint directly
$body = @{
    limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/content/links/check/sync" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### **Problem 4: Database connection error**
```
✅ Check Supabase credentials in N8N
✅ Check .env file has SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
✅ Restart backend
```

---

## ✅ **SUCCESS CRITERIA:**

**Agent is working if:**
- [x] Responds to basic questions
- [x] Can search documents
- [x] Can find error codes
- [x] Can enrich videos (NEW!)
- [x] Can validate links (NEW!)
- [x] Remembers conversation context
- [x] Provides helpful responses

---

## 📝 **NOTES:**

**Write your test results here:**

```
Date: ___________
Time: ___________

Test 1: ________________
Test 2: ________________
Test 3: ________________
Test 4: ________________
Test 5: ________________
Test 6: ________________

Issues found:
-
-
-

Next steps:
-
-
-
```

---

## 🎉 **AFTER SUCCESSFUL TESTING:**

```bash
# Commit results
git add n8n/
git commit -m "test: N8N Agent V2.1 tested and working!"

# Optional: Create test report
# Write summary in TEST_REPORT.md
```

---

**READY TO TEST!** 🚀

**Good luck!** 😊
