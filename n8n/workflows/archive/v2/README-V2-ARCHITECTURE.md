# KRAI Agent V2 - Architektur

---

## ⚠️ **DEPRECATION NOTICE - SUPABASE REFERENCES**

**This document contains historical Supabase references that are NO LONGER VALID.**

**Current Architecture (as of November 2024):**
- ✅ **PostgreSQL-only** (direct asyncpg connection pools)
- ❌ **Supabase** (deprecated and removed)
- ❌ **PostgREST** (deprecated and removed)

**For current setup instructions, see:**
- `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` - Migration guide
- `DOCKER_SETUP.md` - Current PostgreSQL setup
- `DATABASE_SCHEMA.md` - Current schema reference

**This document is preserved for historical reference only.**

---

**Erstellt:** 09.10.2025  
**Status:** In Entwicklung (DEPRECATED)

---

## 🏗️ SYSTEM-ARCHITEKTUR

```
┌─────────────────────────────────────────┐
│   MICROSOFT TEAMS                       │
│   User Input                            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   KRAI MASTER AGENT                     │
│   - Webhook Receiver                    │
│   - Command Parser                      │
│   - AI Intent Detection                 │
│   - Router                              │
└─────────────────────────────────────────┘
              ↓
    ┌─────────┴─────────┬─────────────┬──────────────┐
    ↓                   ↓             ↓              ↓
┌─────────┐      ┌──────────┐  ┌──────────┐  ┌──────────┐
│ ERROR   │      │ PRODUCT  │  │ DEVICE   │  │ HELP     │
│ AGENT   │      │ INFO     │  │ STATUS   │  │ AGENT    │
│         │      │ AGENT    │  │ AGENT    │  │          │
└─────────┘      └──────────┘  └──────────┘  └──────────┘
    ↓                   ↓             ↓              ↓
KRAI DB          KRAI DB      Monitoring    Static
(Fehlercodes)    (Products)   API           Content
```

---

## 📋 INPUT-METHODEN

### 1. Slash Commands (Power-User)
```
/fehler HP X580 12.34.56
/status 12345
/info X580 duplexscan
/commands
/help
```

### 2. Natural Language (Alle User)
```
"HP X580 Fehler 12.34.56"
"Zeig mir alle Commands"
"Wie viel Toner hat Gerät 12345?"
"Kann X580 Duplexscan?"
```

---

## 🤖 AGENTS

### 1. ERROR AGENT (Priorität: HOCH)
**Funktion:** Fehlercode-Informationen aus KRAI DB

**Input:**
- Command: `/fehler [Hersteller] [Modell] [Code]`
- Natural: "HP X580 Fehler 12.34.56"

**Workflow:**
1. Hersteller erkennen/validieren
2. KRAI DB durchsuchen (Priorität):
   - Service Manual
   - CPMD
   - Bulletins
3. Antwort formatieren:
   - Schritt-für-Schritt Lösung
   - Bilder (inline wenn vorhanden)
   - Links & Videos
   - Quellen-Hierarchie
4. Fallback: Hersteller-Kontakt
   - support_email
   - support_phone

**Output:**
- Mehrere Nachrichten wenn nötig
- Service Manual IMMER zuerst
- Adaptive Cards für Rich Formatting

---

### 2. PRODUCT INFO AGENT (Priorität: MITTEL)
**Funktion:** Produktspezifikationen aus KRAI DB

**Input:**
- Command: `/info [Modell] [Frage]`
- Natural: "Kann X580 Duplexscan?"

**Workflow:**
1. Produktmodell erkennen
2. KRAI DB → products Tabelle
3. Spezifikationen abrufen
4. Antwort formatieren

**Output:**
- Ja/Nein + Details
- Technische Specs
- Link zu Datenblatt

---

### 3. DEVICE STATUS AGENT (Priorität: NIEDRIG - Zukunft)
**Funktion:** Live-Daten aus Printer Monitoring

**Input:**
- Command: `/status [Geräte-ID]`
- Natural: "Trommel Restlaufzeit Gerät 12345"

**Workflow:**
1. Geräte-ID extrahieren
2. Printer Monitoring API abfragen
3. Daten formatieren

**Output:**
- Toner/Trommel Levels
- Zählerstände
- Letzte Wartung
- Status (Online/Offline)

---

### 4. HELP AGENT (Priorität: HOCH)
**Funktion:** Command-Liste & Hilfe

**Input:**
- Command: `/help`, `/commands`
- Natural: "Was kannst du?", "Zeig Commands"

**Workflow:**
1. Command-Liste generieren
2. Formatieren mit Beispielen

**Output:**
- Liste aller Commands
- Beispiele
- Hinweis auf Natural Language

---

## 🔀 ROUTING LOGIC

### Command-basiert (Direkt)
```javascript
if (text.startsWith('/')) {
  const command = parseCommand(text);
  switch(command.name) {
    case 'fehler': return errorAgent(command.args);
    case 'status': return statusAgent(command.args);
    case 'info': return productInfoAgent(command.args);
    case 'help': return helpAgent();
  }
}
```

### AI-basiert (Intent Detection)
```javascript
const intent = await detectIntent(text);
switch(intent.type) {
  case 'ERROR_CODE': return errorAgent(intent);
  case 'DEVICE_STATUS': return statusAgent(intent);
  case 'PRODUCT_INFO': return productInfoAgent(intent);
  case 'HELP': return helpAgent();
  default: return unknownIntent();
}
```

---

## 📊 DATENQUELLEN

### Aktuell (Phase 1)
- ✅ KRAI Database (PostgreSQL)
  - krai_intelligence.error_codes
  - krai_core.products
  - krai_core.documents
  - krai_content.links
  - krai_content.videos
  - krai_core.manufacturers

### Zukunft (Phase 2+)
- ⏳ Printer Monitoring API
- ⏳ Ticket System
- ⏳ ERP/CRM

---

## 📱 RESPONSE FORMAT

### Adaptive Card Struktur
```json
{
  "type": "AdaptiveCard",
  "body": [
    {
      "type": "TextBlock",
      "text": "# 🔧 Fehlercode 12.34.56",
      "weight": "bolder",
      "size": "large"
    },
    {
      "type": "TextBlock",
      "text": "**Hersteller:** HP | **Modell:** X580",
      "wrap": true
    },
    {
      "type": "TextBlock",
      "text": "## Lösung (Service Manual)",
      "weight": "bolder"
    },
    {
      "type": "TextBlock",
      "text": "1. Schritt 1...\n2. Schritt 2...",
      "wrap": true
    },
    {
      "type": "Image",
      "url": "https://...",
      "altText": "Diagram"
    },
    {
      "type": "TextBlock",
      "text": "## Weitere Quellen",
      "weight": "bolder"
    },
    {
      "type": "FactSet",
      "facts": [
        {"title": "CPMD", "value": "Link..."},
        {"title": "Video", "value": "Link..."}
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "Service Manual öffnen",
      "url": "https://..."
    }
  ]
}
```

---

## 🚀 IMPLEMENTIERUNGS-PHASEN

### Phase 1 (JETZT - 09.10.2025)
- ✅ Master Agent mit Routing
- ✅ Help Agent (funktionsfähig)
- ⏳ Error Agent (in Arbeit)
- ⏳ Product Info Agent (basic)

### Phase 2 (Später)
- ⏳ Device Status Agent
- ⏳ Printer Monitoring Integration
- ⏳ Erweiterte Fehlersuche
- ⏳ Multi-Language Support

### Phase 3 (Zukunft)
- ⏳ Ticket System Integration
- ⏳ ERP/CRM Integration
- ⏳ Predictive Maintenance
- ⏳ Analytics & Logging

---

## 🔧 TECHNISCHE DETAILS

### n8n Workflows
- `KRAI-Master-Agent-V2.json` - Hauptworkflow
- `Error-Agent-V2.json` - Fehlercode-Suche
- `Product-Info-Agent-V2.json` - Produktinfos
- `Device-Status-Agent-V2.json` - Monitoring (Platzhalter)
- `Help-Agent-V2.json` - Hilfe (in Master integriert)

### AI Models
- **Intent Detection:** Ollama qwen2.5:7b
- **Response Generation:** Ollama qwen2.5:7b
- **Fallback:** OpenAI GPT-4 (optional)

### Database
- **PostgreSQL** (direct connection)
- **Schemas:** krai_core, krai_intelligence, krai_content, krai_agent
- **Connection:** postgresql://postgres:password@localhost:5432/krai
- **Neue Spalten:** manufacturers.support_email, manufacturers.support_phone

---

## 📝 NÄCHSTE SCHRITTE

1. ✅ Master Agent Workflow erstellt
2. ⏳ Error Agent implementieren
3. ⏳ Manufacturers Tabelle erweitern (support_email, support_phone)
4. ⏳ Teams Bot registrieren
5. ⏳ Testing mit echten Daten
6. ⏳ Deployment

---

**Erstellt von:** Cascade AI  
**Für:** Kunze-Ritter GmbH  
**Projekt:** KRAI Agent V2
