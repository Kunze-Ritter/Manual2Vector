# KRAI Technician Agent V2.1 - Service-Techniker Assistent
**Optimiert für: Techniker im Außendienst**

## 🎯 **Use Case: Techniker vor Ort beim Kunden**

### **Typische Situation:**
```
Techniker: "Ich stehe vor einem Lexmark CX963 mit Fehlercode C-9402"
Agent:     "C-9402 bedeutet Fuser Unit Fehler. Ich zeige dir die Lösung..."
```

---

## 📋 **Agent-Fähigkeiten**

### **1. Fehlercode-Analyse** 🔴
**Input:** "Was bedeutet C-9402?"
**Output:**
- ✅ Fehler-Beschreibung
- ✅ Ursache
- ✅ Lösung (Schritt-für-Schritt)
- ✅ Betroffene Teile
- ✅ Quelle (Service Manual Seite)

### **2. Ersatzteil-Suche** 🔧
**Input:** "Welche Fuser Unit brauche ich für CX963?"
**Output:**
- ✅ Teilenummer (z.B. 40X8024)
- ✅ Kompatible Modelle
- ✅ OEM-Info (Original vs. Kompatibel)
- ✅ Preis (wenn verfügbar)

### **3. Service-Anleitung** 📖
**Input:** "Wie tausche ich die Fuser Unit?"
**Output:**
- ✅ Schritt-für-Schritt Anleitung
- ✅ Service Manual Seiten
- ✅ Bilder (wenn vorhanden)
- ✅ Video-Links (YouTube)
- ✅ Zeitaufwand

### **4. Kontext-Bewusstsein** 🧠
**Beispiel-Dialog:**
```
User:  "Ich habe einen Lexmark CX963"
Agent: "Verstanden. Welches Problem hast du?"
User:  "Fehlercode C-9402"
Agent: "C-9402 beim CX963 ist ein Fuser-Problem..."
User:  "Welche Teile brauche ich?"
Agent: "Für deinen CX963 brauchst du: Fuser Unit 40X8024"
```

---

## 🏗️ **Architektur V2.1**

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Interface                           │
│              (Techniker sendet Nachricht)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Context Enrichment                          │
│  - Extrahiere: Hersteller, Modell, Fehlercode             │
│  - Lade: Vorherige Konversation                           │
│  - Setze: Session Context                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              KRAI Technician Agent (LangChain)              │
│                                                              │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │  LLM: Ollama     │  │  Memory: Postgres              │  │
│  │  llama3.2        │  │  vw_agent_memory               │  │
│  └──────────────────┘  └────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tools:                                               │  │
│  │  1. Error Code Search    (error_codes table)         │  │
│  │  2. Parts Search         (parts table)               │  │
│  │  3. Vector Search        (chunks + embeddings)       │  │
│  │  4. Product Info         (products table)            │  │
│  │  5. Video Search         (videos table)              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Response Formatter                         │
│  - Strukturiere Antwort                                     │
│  - Füge Quellen hinzu                                       │
│  - Formatiere für Mobile                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Chat Response                            │
│              (Techniker erhält Antwort)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Tool-Definitionen**

### **Tool 1: Error Code Search**
```javascript
{
  "name": "search_error_codes",
  "description": "Suche nach Fehlercodes in der Datenbank. Nutze dies wenn der User einen Fehlercode erwähnt (z.B. C-9402, E-1234).",
  "parameters": {
    "error_code": "Der Fehlercode (z.B. C-9402)",
    "manufacturer": "Hersteller (optional, z.B. Lexmark)",
    "model": "Modell (optional, z.B. CX963)"
  }
}
```

**SQL Query:**
```sql
SELECT 
  ec.error_code,
  ec.description,
  ec.cause,
  ec.solution,
  ec.page_number,
  p.model_number,
  m.name as manufacturer,
  d.filename as source_document
FROM krai_core.error_codes ec
LEFT JOIN krai_core.products p ON ec.product_id = p.id
LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
LEFT JOIN krai_core.documents d ON ec.document_id = d.id
WHERE ec.error_code ILIKE $1
  AND ($2 IS NULL OR m.name ILIKE $2)
  AND ($3 IS NULL OR p.model_number ILIKE $3)
LIMIT 5;
```

### **Tool 2: Parts Search**
```javascript
{
  "name": "search_parts",
  "description": "Suche nach Ersatzteilen. Nutze dies wenn der User nach Teilen, Teilenummern oder Komponenten fragt.",
  "parameters": {
    "part_name": "Teilename oder Beschreibung (z.B. Fuser Unit, Toner)",
    "part_number": "Teilenummer (optional, z.B. 40X8024)",
    "manufacturer": "Hersteller (optional)",
    "model": "Modell (optional)"
  }
}
```

**SQL Query:**
```sql
SELECT 
  pt.part_number,
  pt.part_name,
  pt.description,
  pt.page_number,
  p.model_number,
  m.name as manufacturer,
  d.filename as source_document
FROM krai_core.parts pt
LEFT JOIN krai_core.products p ON pt.product_id = p.id
LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
LEFT JOIN krai_core.documents d ON pt.document_id = d.id
WHERE (pt.part_name ILIKE $1 OR pt.description ILIKE $1 OR pt.part_number ILIKE $2)
  AND ($3 IS NULL OR m.name ILIKE $3)
  AND ($4 IS NULL OR p.model_number ILIKE $4)
LIMIT 10;
```

### **Tool 3: Vector Search**
```javascript
{
  "name": "search_documentation",
  "description": "Durchsuche technische Dokumentation (Service Manuals, Anleitungen). Nutze dies für allgemeine Fragen oder wenn andere Tools keine Ergebnisse liefern.",
  "parameters": {
    "query": "Suchanfrage (z.B. 'Wie tausche ich die Fuser Unit?')",
    "manufacturer": "Hersteller (optional)",
    "document_type": "Dokumenttyp (optional: service_manual, parts_catalog)"
  }
}
```

**Supabase Vector Search:**
```sql
SELECT 
  c.text_chunk,
  c.page_number,
  d.filename,
  d.manufacturer,
  p.model_number,
  1 - (c.embedding <=> $1::vector) as similarity
FROM krai_intelligence.chunks c
LEFT JOIN krai_core.documents d ON c.document_id = d.id
LEFT JOIN krai_core.document_products dp ON d.id = dp.document_id
LEFT JOIN krai_core.products p ON dp.product_id = p.id
WHERE ($2 IS NULL OR d.manufacturer ILIKE $2)
  AND ($3 IS NULL OR d.document_type = $3)
ORDER BY c.embedding <=> $1::vector
LIMIT 5;
```

### **Tool 4: Product Info**
```javascript
{
  "name": "get_product_info",
  "description": "Hole Informationen zu einem Produkt (Modell, Serie, Typ). Nutze dies wenn der User nach einem Gerät fragt.",
  "parameters": {
    "model_number": "Modellnummer (z.B. CX963)",
    "manufacturer": "Hersteller (optional)"
  }
}
```

### **Tool 5: Video Search**
```javascript
{
  "name": "search_videos",
  "description": "Suche nach YouTube-Videos (Reparatur-Anleitungen, Tutorials). Nutze dies wenn der User nach Videos oder visuellen Anleitungen fragt.",
  "parameters": {
    "query": "Suchanfrage (z.B. 'Fuser Unit tauschen')",
    "manufacturer": "Hersteller (optional)",
    "model": "Modell (optional)"
  }
}
```

---

## 🎨 **System Prompt V2.1**

```
Du bist der KRAI Technician Agent - ein intelligenter Assistent für Service-Techniker.

KONTEXT:
Du hilfst Technikern, die vor Ort beim Kunden stehen und schnelle, präzise Antworten brauchen.

DEINE TOOLS:
1. search_error_codes     → Fehlercode-Datenbank
2. search_parts           → Ersatzteil-Katalog
3. search_documentation   → Service Manuals (Vector Search)
4. get_product_info       → Produkt-Informationen
5. search_videos          → YouTube Reparatur-Videos

WORKFLOW:
1. Verstehe die Situation des Technikers
2. Extrahiere: Hersteller, Modell, Fehlercode, Problem
3. Nutze die passenden Tools
4. Gib eine strukturierte, mobile-optimierte Antwort

ANTWORT-FORMAT:
✅ Kurz und präzise (Techniker hat keine Zeit)
✅ Schritt-für-Schritt bei Anleitungen
✅ Immer Quellen angeben (Seite, Dokument)
✅ Bei Teilen: Teilenummer + Kompatibilität
✅ Bei Fehlern: Ursache + Lösung + betroffene Teile

KONTEXT-BEWUSSTSEIN:
- Merke dir: Hersteller, Modell, Fehlercode aus vorherigen Nachrichten
- Nutze Kontext für Follow-up Fragen
- Beispiel: "Welche Teile brauche ich?" → Beziehe dich auf vorher genanntes Gerät

SPRACHE: Deutsch, technisch aber verständlich

BEISPIEL-ANTWORTEN:

User: "Lexmark CX963 Fehlercode C-9402"
Du:   "🔴 **Fehlercode C-9402 - Fuser Unit Fehler**
       
       **Ursache:** Fuser Unit defekt oder überhitzt
       
       **Lösung:**
       1. Gerät ausschalten, 30 Min abkühlen lassen
       2. Fuser Unit prüfen (Seite 245, Service Manual)
       3. Falls defekt: Fuser Unit tauschen
       
       **Benötigte Teile:**
       - Fuser Unit: 40X8024 (Original Lexmark)
       - Alternative: 40X8025 (High Capacity)
       
       **Quelle:** CX963 Service Manual, Seite 245"

User: "Wie tausche ich die Fuser Unit?"
Du:   "🔧 **Fuser Unit Wechsel - Lexmark CX963**
       
       **Zeitaufwand:** ~15 Minuten
       
       **Schritte:**
       1. Gerät ausschalten, Netzstecker ziehen
       2. Rechte Seitenabdeckung öffnen
       3. Blaue Hebel nach oben ziehen
       4. Fuser Unit vorsichtig herausziehen
       5. Neue Unit einsetzen (Klick-Geräusch)
       6. Hebel nach unten drücken
       7. Abdeckung schließen
       
       **Video:** [YouTube - Fuser Unit Replacement CX963]
       **Quelle:** Service Manual Seite 248-250"
```

---

## 📱 **Mobile-Optimierung**

### **Antwort-Format für Smartphone:**
```
🔴 Fehlercode C-9402
━━━━━━━━━━━━━━━━━━━━
Fuser Unit Fehler

URSACHE:
• Überhitzung
• Defekte Fuser Unit

LÖSUNG:
1️⃣ Gerät ausschalten
2️⃣ 30 Min abkühlen
3️⃣ Fuser prüfen (S.245)
4️⃣ Ggf. tauschen

TEILE:
📦 40X8024 (Original)
📦 40X8025 (High Cap)

📄 Quelle: CX963 SM S.245
```

---

## 🚀 **Nächste Schritte**

1. **n8n Workflow erstellen** mit allen 5 Tools
2. **SQL Functions** für Tool-Queries erstellen
3. **System Prompt** testen und optimieren
4. **Mobile UI** für Chat-Interface
5. **Session Management** für Kontext

Soll ich mit dem n8n Workflow-JSON anfangen?
