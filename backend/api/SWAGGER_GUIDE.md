# 🎯 Swagger UI - Einfacher Guide

## 📖 Was ist Swagger UI?

Swagger UI ist eine **interaktive Dokumentation** für deine API. Du kannst direkt im Browser API-Calls testen, ohne Code zu schreiben!

---

## 🚀 Schritt-für-Schritt Anleitung

### **Schritt 1: API öffnen**

1. API muss laufen (in deinem Terminal siehst du: `Uvicorn running on http://0.0.0.0:8000`)
2. Browser öffnen
3. Diese URL eingeben: **http://localhost:8000/docs**

---

### **Schritt 2: Die Oberfläche verstehen**

Wenn du die Seite öffnest, siehst du:

```
┌─────────────────────────────────────────────┐
│  KRAI Processing Pipeline API               │
│  Version 2.0.0                              │
└─────────────────────────────────────────────┘

┌─ System ─────────────────────────────────────┐
│  GET  /            Root endpoint             │
│  GET  /health      Health check              │
└──────────────────────────────────────────────┘

┌─ Upload ─────────────────────────────────────┐
│  POST /upload            Upload document     │
│  POST /upload/directory  Batch upload        │
└──────────────────────────────────────────────┘

┌─ Status ─────────────────────────────────────┐
│  GET  /status/{id}   Document status         │
│  GET  /status        Pipeline status         │
└──────────────────────────────────────────────┘

┌─ Monitoring ─────────────────────────────────┐
│  GET  /logs/{id}     Document logs           │
│  GET  /metrics       System metrics          │
└──────────────────────────────────────────────┘
```

---

### **Schritt 3: Erste Test - Health Check**

#### **1. Klicke auf `GET /health`**
   - Der Bereich klappt auf

#### **2. Klicke auf den blauen Button "Try it out"**
   - Der Button wird zu "Execute"

#### **3. Klicke auf "Execute"**
   - Die API wird aufgerufen

#### **4. Schau dir die Response an:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T07:00:00.000Z",
  "services": {
    "api": {
      "status": "healthy",
      "message": "API is running"
    },
    "database": {
      "status": "healthy",
      "message": "Database connected"
    },
    "ollama": {
      "status": "healthy",
      "message": "3 models available"
    },
    "storage": {
      "status": "configured",
      "message": "R2 credentials present"
    }
  }
}
```

✅ **Wenn du das siehst, funktioniert alles!**

---

### **Schritt 4: Document Upload testen**

#### **1. Klicke auf `POST /upload`**
   - Der Bereich klappt auf

#### **2. Klicke auf "Try it out"**

#### **3. Fülle die Felder aus:**

```
┌─────────────────────────────────────────────┐
│  file                                       │
│  ┌──────────────────────────────────────┐  │
│  │  Choose File  [Keine Datei ausgewählt]│  │
│  └──────────────────────────────────────┘  │
│                                             │
│  document_type          [service_manual ▼] │
│                                             │
│  force_reprocess        [ ] false           │
└─────────────────────────────────────────────┘
```

- **file:** Klicke auf "Choose File" und wähle ein PDF aus
- **document_type:** Lass auf "service_manual" stehen
- **force_reprocess:** Lass auf "false" stehen

#### **4. Klicke auf "Execute"**

#### **5. Warte 2-3 Sekunden...**

#### **6. Schau dir die Response an:**
```json
{
  "success": true,
  "document_id": "5a30739d-d8d4-4a1a-b033-a32e39cf33ba",
  "status": "new",
  "message": "Upload successful",
  "metadata": {
    "filename": "test.pdf",
    "page_count": 4386,
    "file_size_bytes": 348721152,
    "title": "AccurioPress Service Manual"
  }
}
```

✅ **Du hast gerade ein PDF hochgeladen!**

📋 **Kopiere die `document_id`** für den nächsten Schritt!

---

### **Schritt 5: Status abfragen**

#### **1. Klicke auf `GET /status/{document_id}`**

#### **2. Klicke auf "Try it out"**

#### **3. Füge die Document ID ein:**
```
┌─────────────────────────────────────────────┐
│  document_id (required)                     │
│  ┌──────────────────────────────────────┐  │
│  │ 5a30739d-d8d4-4a1a-b033-a32e39cf33ba │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

#### **4. Klicke auf "Execute"**

#### **5. Response:**
```json
{
  "document_id": "5a30739d-d8d4-4a1a-b033-a32e39cf33ba",
  "status": "uploaded",
  "current_stage": "text_extraction",
  "progress": 14.285714285714286,
  "started_at": "2025-10-04T07:55:46.123Z",
  "completed_at": null,
  "error": null
}
```

✅ **Du siehst jetzt den Processing-Status!**

---

### **Schritt 6: Alle Documents anzeigen**

#### **1. Klicke auf `GET /status`** (ohne ID!)

#### **2. Klicke auf "Try it out"**

#### **3. Klicke auf "Execute"**

#### **4. Response:**
```json
{
  "total_documents": 2,
  "in_queue": 1,
  "processing": 0,
  "completed": 1,
  "failed": 0,
  "by_task_type": {
    "text_extraction": 1,
    "image_processing": 0,
    "classification": 0,
    "metadata_extraction": 0,
    "storage": 0,
    "embedding": 0,
    "search": 0
  }
}
```

✅ **Pipeline-Übersicht!**

---

## 🎨 Swagger UI - Cheat Sheet

### **Farben verstehen:**
- 🟢 **GET** (Grün) = Daten abrufen, nichts ändern
- 🔵 **POST** (Blau) = Daten erstellen/hochladen
- 🟡 **PUT** (Gelb) = Daten aktualisieren
- 🔴 **DELETE** (Rot) = Daten löschen

### **Response Codes:**
- ✅ **200** = OK, alles gut!
- ✅ **201** = Created (Dokument wurde erstellt)
- ⚠️ **400** = Bad Request (Fehlerhafte Eingabe)
- ⚠️ **404** = Not Found (Dokument nicht gefunden)
- ❌ **500** = Server Error (Etwas ist schiefgelaufen)

### **Wichtige Buttons:**
- **Try it out** = Eingabefelder aktivieren
- **Execute** = API Call ausführen
- **Cancel** = Abbrechen
- **Clear** = Felder leeren

---

## 📋 Quick Tests zum Ausprobieren

### **Test 1: Health Check** ⏱️ 5 Sekunden
```
GET /health
→ Zeigt Status aller Services
```

### **Test 2: Upload PDF** ⏱️ 30 Sekunden
```
POST /upload
→ Wähle PDF aus
→ Upload
→ Kopiere document_id
```

### **Test 3: Status prüfen** ⏱️ 10 Sekunden
```
GET /status/{document_id}
→ Füge document_id ein
→ Siehe Processing-Status
```

### **Test 4: Pipeline Overview** ⏱️ 5 Sekunden
```
GET /status
→ Siehe alle Documents
```

---

## 🆘 Probleme?

### **"Connection refused" / "Cannot connect"**
→ API läuft nicht! Im Terminal `python app.py` ausführen

### **"404 Not Found"**
→ Falsche document_id verwendet oder Dokument existiert nicht

### **"500 Internal Server Error"**
→ Schau ins Terminal wo die API läuft, dort siehst du den Fehler

### **"Unauthorized"**
→ Supabase credentials fehlen (.env File prüfen)

---

## 💡 Pro-Tips

1. **Response kopieren:** Klicke auf "Copy" Button rechts oben in der Response
2. **Curl Command:** Klicke auf "Curl" um den Command zum Copy-Pasten zu sehen
3. **Schema anzeigen:** Klicke auf "Schema" Tab um JSON-Struktur zu sehen
4. **Mehrere Tabs:** Öffne mehrere Browser-Tabs für verschiedene Endpoints

---

## 🎯 Zusammenfassung

```
1. API starten:    python app.py
2. Browser öffnen: http://localhost:8000/docs
3. Endpoint wählen (z.B. GET /health)
4. "Try it out" klicken
5. Felder ausfüllen (wenn nötig)
6. "Execute" klicken
7. Response ansehen
```

**So einfach ist das!** 🎉

---

## 📞 Noch Fragen?

- Swagger funktioniert nicht? → API läuft wahrscheinlich nicht
- Response zu kompliziert? → Schau nur auf "status" und "message"
- Upload funktioniert nicht? → Prüfe Dateigröße (<500MB) und Format (PDF)

---

**Viel Erfolg beim Testen!** 🚀
