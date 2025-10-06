# 🔧 N8N Tool Parameter Configuration

**Problem:** "No parameters are set up to be filled by AI"  
**Solution:** Configure AI parameter mapping for each tool

---

## 📋 **CONFIGURATION FOR EACH TOOL:**

### **Tool 1: System Status** ✅

**Parameters:** None (leeres Object)

**Config:**
```
Specify Input Schema: ✅ ON
JSON Schema Example: {}
```

**Fields to Send:** (None - tool needs no parameters)

---

### **Tool 2: Error Code Search** 🔴

**Parameters:** `error_code` (String)

**Config:**
```
Specify Input Schema: ✅ ON
JSON Schema Example:
{
  "error_code": "C-2801"
}
```

**Fields to Send:**
```
Field 1:
  Name: error_code
  Type: String
  Value: {{ $json.error_code }}
  AI Can Fill: ✅ ON
```

**Alternative in N8N UI:**
1. Click auf Node
2. Scroll zu "Fields to Send"
3. Click "+ Add Field"
4. Name: `error_code`
5. Click ✨ (sparkle icon) um "AI Can Fill" zu aktivieren

---

### **Tool 3: Document Type Filter** 📑

**Parameters:** `document_type`, `manufacturer` (optional), `limit` (optional)

**Config:**
```
Specify Input Schema: ✅ ON
JSON Schema Example:
{
  "document_type": "service_bulletin",
  "manufacturer": null,
  "limit": 10
}
```

**Fields to Send:**
```
Field 1:
  Name: document_type
  Type: String
  Value: {{ $json.document_type }}
  AI Can Fill: ✅ ON

Field 2:
  Name: manufacturer
  Type: String
  Value: {{ $json.manufacturer }}
  AI Can Fill: ✅ ON
  Optional: ✅ ON

Field 3:
  Name: limit
  Type: Number
  Value: {{ $json.limit || 10 }}
  AI Can Fill: ✅ ON
  Optional: ✅ ON
```

---

### **Tool 4: Video Enrichment** 🎬

**Parameters:** `url` (required), `document_id` (optional), `manufacturer_id` (optional)

**Config:**
```
Specify Input Schema: ✅ ON
JSON Schema Example:
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "document_id": null,
  "manufacturer_id": null
}
```

**Fields to Send:**
```
Field 1:
  Name: url
  Type: String
  Value: {{ $json.url }}
  AI Can Fill: ✅ ON

Field 2:
  Name: document_id
  Type: String
  Value: {{ $json.document_id }}
  AI Can Fill: ✅ ON
  Optional: ✅ ON

Field 3:
  Name: manufacturer_id
  Type: String
  Value: {{ $json.manufacturer_id }}
  AI Can Fill: ✅ ON
  Optional: ✅ ON
```

---

### **Tool 5: Link Validation** 🔗

**Parameters:** `document_id` (optional), `limit` (optional)

**Config:**
```
Specify Input Schema: ✅ ON
JSON Schema Example:
{
  "document_id": null,
  "limit": 50
}
```

**Fields to Send:**
```
Field 1:
  Name: document_id
  Type: String
  Value: {{ $json.document_id }}
  AI Can Fill: ✅ ON
  Optional: ✅ ON

Field 2:
  Name: limit
  Type: Number
  Value: {{ $json.limit || 50 }}
  AI Can Fill: ✅ ON
  Optional: ✅ ON
```

---

## 🎯 **QUICK FIX CHECKLIST:**

**For each Tool Node in Main Workflow:**

1. ✅ Click auf Tool Node
2. ✅ "Specify Input Schema" → ON
3. ✅ "JSON Schema Example" → Paste JSON
4. ✅ Scroll to "Fields to Send"
5. ✅ Add required fields
6. ✅ Click ✨ (sparkle) for each field
7. ✅ Save workflow

---

## 📸 **WIE ES AUSSEHEN SOLLTE:**

### **Tool Node Settings (Example: Error Code Search)**

```
┌─────────────────────────────────────────────┐
│ Tool: Error Code Search                     │
├─────────────────────────────────────────────┤
│ Name: search_error_code                     │
│ Description: [...]                          │
│ Workflow ID: TOOL: Error Code Search        │
│                                             │
│ ✅ Specify Input Schema: ON                 │
│                                             │
│ JSON Schema Example:                        │
│ ┌─────────────────────────────────────┐    │
│ │ {                                   │    │
│ │   "error_code": "C-2801"            │    │
│ │ }                                   │    │
│ └─────────────────────────────────────┘    │
│                                             │
│ Fields to Send:                             │
│ ┌─────────────────────────────────────┐    │
│ │ error_code                          │    │
│ │   Type: String                      │    │
│ │   Value: {{ $json.error_code }}     │    │
│ │   ✨ AI Can Fill: ON                │    │ ← WICHTIG!
│ └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

---

## ⚠️ **HÄUFIGE FEHLER:**

### **Fehler 1:** "No parameters are set up"
**Ursache:** ✨ Sparkle Icon nicht aktiviert  
**Fix:** Click auf ✨ neben jedem Parameter

### **Fehler 2:** "Could not get parameter"
**Ursache:** Field Name stimmt nicht mit JSON Schema überein  
**Fix:** Field Name MUSS exakt matchen (z.B. `error_code`, nicht `errorCode`)

### **Fehler 3:** Tool wird nicht aufgerufen
**Ursache:** Workflow ID nicht gesetzt  
**Fix:** Workflow ID Dropdown → Wähle Sub-Workflow

---

## 🎯 **ALTERNATIVE: EINFACHERE KONFIGURATION**

**N8N hat verschiedene Modi:**

**Option A: JSON Schema + Fields (Current)**
- JSON Schema definiert Struktur
- Fields to Send definiert Mapping
- ✨ Icon aktiviert AI-Füllung

**Option B: Nur JSON Schema (Einfacher)**
- Nur JSON Schema setzen
- N8N leitet automatisch Fields ab
- **ABER:** Funktioniert nicht immer zuverlässig!

**Empfehlung:** Option A (explizite Fields)

---

## 📝 **TESTEN NACH CONFIG:**

**Test 1: Error Code**
```
User: "Was ist Error Code C-2801?"
Expected: Tool wird aufgerufen mit {"error_code": "C-2801"}
```

**Test 2: Document Type**
```
User: "Zeige Service Bulletins"
Expected: Tool wird aufgerufen mit {"document_type": "service_bulletin"}
```

**Test 3: Video**
```
User: "https://www.youtube.com/watch?v=abc123"
Expected: Tool wird aufgerufen mit {"url": "https://..."}
```

---

## 🚀 **NÄCHSTE SCHRITTE:**

1. **Öffne Main Workflow** in N8N
2. **Für jeden Tool Node:**
   - Click auf Node
   - Aktiviere "Specify Input Schema"
   - Paste JSON Schema Example
   - Add Fields to Send
   - Click ✨ für jeden Field
3. **Save Workflow**
4. **Test!**

---

**Das ist der letzte Schritt!** Danach sollte alles funktionieren! 🎉
