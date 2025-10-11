# KRAI Technician Agent V2.1 - Test Scenarios

## 🧪 **Test Suite für den Agent**

### **Test 1: Fehlercode-Analyse** 🔴

**Input:**
```
"Lexmark CX963 Fehlercode C-9402"
```

**Expected Output:**
```
🔴 **Fehlercode C-9402 - Fuser Unit Fehler**

**Ursache:** Fuser Unit defekt oder überhitzt

**Lösung:**
1. Gerät ausschalten, 30 Min abkühlen lassen
2. Fuser Unit prüfen (Seite 245)
3. Falls defekt: Fuser Unit tauschen

**Benötigte Teile:**
📦 Fuser Unit: 40X8024 (Original Lexmark)

📄 **Quelle:** CX963 Service Manual, Seite 245
```

**Tool-Calls:**
- ✅ `search_error_codes("C-9402", "Lexmark", "CX963")`
- ✅ `search_parts("Fuser Unit", NULL, "Lexmark", "CX963")`

---

### **Test 2: Ersatzteil-Suche** 🔧

**Input:**
```
"Welche Fuser Unit brauche ich für den CX963?"
```

**Expected Output:**
```
🔧 **Fuser Unit für Lexmark CX963**

**Verfügbare Teile:**
📦 **40X8024** - Fuser Unit (Standard)
   - Kompatibel: CX963, CX961, CX962
   - Original Lexmark

📦 **40X8025** - Fuser Unit (High Capacity)
   - Kompatibel: CX963, CX961, CX962
   - Längere Lebensdauer

📄 **Quelle:** CX963 Parts Catalog, Seite 89
```

**Tool-Calls:**
- ✅ `get_product_info("CX963", "Lexmark")`
- ✅ `search_parts("Fuser Unit", NULL, "Lexmark", "CX963")`

---

### **Test 3: Kontext-Bewusstsein** 🧠

**Dialog:**
```
User:  "Ich habe einen Lexmark CX963"
Agent: "Verstanden. Welches Problem hast du mit dem CX963?"

User:  "Fehlercode C-9402"
Agent: "🔴 Fehlercode C-9402 beim CX963 ist ein Fuser-Problem..."

User:  "Welche Teile brauche ich?"
Agent: "Für deinen CX963 brauchst du: Fuser Unit 40X8024"

User:  "Zeig mir ein Video"
Agent: "🎥 Hier ist ein Video für den Fuser-Wechsel beim CX963..."
```

**Tool-Calls:**
- ✅ `get_product_info("CX963", "Lexmark")` (bei erster Erwähnung)
- ✅ `search_error_codes("C-9402", "Lexmark", "CX963")` (nutzt Kontext)
- ✅ `search_parts("Fuser Unit", NULL, "Lexmark", "CX963")` (nutzt Kontext)
- ✅ `search_videos("Fuser Unit replacement", "Lexmark", "CX963")` (nutzt Kontext)

---

### **Test 4: Video-Suche** 🎥

**Input:**
```
"Zeig mir ein Video wie ich die Fuser Unit beim CX963 tausche"
```

**Expected Output:**
```
🎥 **Reparatur-Videos für Lexmark CX963**

**1. Lexmark CX963 Fuser Unit Replacement**
   📺 [Video ansehen](https://youtube.com/watch?v=...)
   👤 Kanal: Lexmark Support
   👁️ 45.2K Aufrufe
   ⏱️ Dauer: 8:34

**2. How to Replace Fuser - CX Series**
   📺 [Video ansehen](https://youtube.com/watch?v=...)
   👤 Kanal: Tech Repair Guide
   👁️ 12.5K Aufrufe
   ⏱️ Dauer: 6:12

💡 **Tipp:** Achte darauf, dass das Gerät vollständig abgekühlt ist!
```

**Tool-Calls:**
- ✅ `search_videos("Fuser Unit replacement", "Lexmark", "CX963")`

---

### **Test 5: Allgemeine Anleitung** 📖

**Input:**
```
"Wie tausche ich die Drum Unit beim bizhub C750i?"
```

**Expected Output:**
```
🔧 **Drum Unit Wechsel - Konica Minolta bizhub C750i**

**Zeitaufwand:** ~20 Minuten

**Schritte:**
1. Gerät ausschalten, Netzstecker ziehen
2. Vordere Abdeckung öffnen
3. Toner-Cartridges entfernen
4. Drum Unit Verriegelung lösen (blaue Hebel)
5. Alte Drum Unit vorsichtig herausziehen
6. Neue Drum Unit einsetzen (bis Klick)
7. Toner-Cartridges wieder einsetzen
8. Abdeckung schließen

**Benötigte Teile:**
📦 Drum Unit: A0DE-R70 (Original Konica Minolta)

📄 **Quelle:** bizhub C750i Service Manual, Seite 312-315

🎥 **Video:** [Drum Unit Replacement C750i](https://youtube.com/...)
```

**Tool-Calls:**
- ✅ `get_product_info("C750i", "Konica Minolta")`
- ✅ `search_documentation("Drum Unit replacement", "Konica Minolta", "C750i", "service_manual")`
- ✅ `search_parts("Drum Unit", NULL, "Konica Minolta", "C750i")`
- ✅ `search_videos("Drum Unit replacement", "Konica Minolta", "C750i")`

---

### **Test 6: Unbekannter Fehlercode** ❓

**Input:**
```
"Was bedeutet Fehlercode X-9999?"
```

**Expected Output:**
```
❓ **Fehlercode X-9999 nicht gefunden**

Ich konnte diesen Fehlercode nicht in meiner Datenbank finden.

**Mögliche Gründe:**
- Fehlercode falsch geschrieben
- Fehlercode ist sehr neu
- Fehlercode ist gerätespezifisch

**Was du tun kannst:**
1. Prüfe die Schreibweise (z.B. C-9999 statt X-9999)
2. Nenne mir das Gerätemodell
3. Schau im Service Manual nach

💡 **Tipp:** Nenne mir Hersteller und Modell, dann kann ich besser helfen!
```

**Tool-Calls:**
- ✅ `search_error_codes("X-9999", NULL, NULL)` (keine Ergebnisse)

---

### **Test 7: Multi-Tool Kombination** 🎯

**Input:**
```
"Ich habe einen Konica Minolta bizhub C750i mit Fehler C-2557. Was muss ich tun?"
```

**Expected Output:**
```
🔴 **Fehlercode C-2557 - Polygon Motor Fehler**

**Ursache:** Polygon Motor defekt oder Verbindungsproblem

**Lösung:**
1. Gerät ausschalten, 5 Min warten
2. Polygon Motor Kabel prüfen (Seite 456)
3. Falls Kabel OK: Polygon Motor tauschen

**Benötigte Teile:**
📦 Polygon Motor: A1RF-R00 (Original Konica Minolta)
📦 Alternative: A1RF-R01 (Refurbished)

**Produkt-Info:**
- Modell: bizhub C750i
- Serie: bizhub C-Series
- Typ: Production Printer
- Dokumentation: 3 Service Manuals verfügbar

📄 **Quelle:** bizhub C750i Service Manual, Seite 456-458

🎥 **Video:** [Polygon Motor Replacement](https://youtube.com/...)

⏱️ **Geschätzte Reparaturzeit:** 45 Minuten
```

**Tool-Calls:**
- ✅ `get_product_info("C750i", "Konica Minolta")`
- ✅ `search_error_codes("C-2557", "Konica Minolta", "C750i")`
- ✅ `search_parts("Polygon Motor", NULL, "Konica Minolta", "C750i")`
- ✅ `search_videos("Polygon Motor replacement", "Konica Minolta", "C750i")`

---

### **Test 8: Teilenummer-Suche** 🔍

**Input:**
```
"Für welche Geräte passt Teil 40X8024?"
```

**Expected Output:**
```
📦 **Teilenummer: 40X8024 - Fuser Unit**

**Kompatible Geräte:**
- ✅ Lexmark CX963
- ✅ Lexmark CX961
- ✅ Lexmark CX962
- ✅ Lexmark XC9635
- ✅ Lexmark XC9645

**Technische Daten:**
- Typ: Fuser Unit (Fixiereinheit)
- Hersteller: Lexmark (Original)
- Lebensdauer: ~100.000 Seiten

📄 **Quelle:** CX Series Parts Catalog, Seite 89
```

**Tool-Calls:**
- ✅ `search_parts("", "40X8024", NULL, NULL)`

---

### **Test 9: Serie-basierte Suche** 📊

**Input:**
```
"Welche Fehler treten häufig bei der CX Series auf?"
```

**Expected Output:**
```
📊 **Häufige Fehler - Lexmark CX Series**

**Top 5 Fehlercodes:**

1. **C-9402** - Fuser Unit Fehler (45 Vorkommen)
   - Betrifft: CX963, CX961, CX962
   - Lösung: Fuser Unit tauschen

2. **C-1234** - Paper Jam (32 Vorkommen)
   - Betrifft: Alle CX Modelle
   - Lösung: Papierweg reinigen

3. **C-5678** - Toner Sensor Fehler (28 Vorkommen)
   - Betrifft: CX963, XC9635
   - Lösung: Sensor reinigen oder tauschen

📄 **Quelle:** Analyse von 156 Service-Fällen
```

**Tool-Calls:**
- ✅ `get_product_info("CX", "Lexmark")` (findet CX Series)
- ✅ `search_error_codes("", "Lexmark", "CX")` (alle CX Fehler)

---

### **Test 10: Offline-Fallback** 📴

**Input:**
```
"Ich habe keinen Internetzugang. Was kann ich tun?"
```

**Expected Output:**
```
📴 **Offline-Modus**

Ohne Internetzugang kann ich dir leider nicht helfen, da ich auf die Datenbank zugreifen muss.

**Alternativen:**
1. **Service Manual PDF** (falls lokal vorhanden)
   - Suche nach: "Fehlercode" im PDF
   - Nutze Inhaltsverzeichnis

2. **Offline-App** (in Entwicklung)
   - Speichert häufige Fehler lokal
   - Funktioniert ohne Internet

3. **Hotspot** vom Smartphone
   - Aktiviere mobilen Hotspot
   - Verbinde dich kurz für Abfrage

💡 **Tipp:** Lade wichtige Infos vorher herunter!
```

**Tool-Calls:**
- ❌ Keine (Agent erkennt, dass Tools nicht verfügbar sind)

---

## 🎯 **Success Criteria**

### **Für jeden Test:**
- ✅ Agent ruft die richtigen Tools auf
- ✅ Antwort ist strukturiert und lesbar
- ✅ Quellen werden angegeben
- ✅ Emojis für bessere Lesbarkeit
- ✅ Kontext wird korrekt genutzt
- ✅ Antwort ist mobile-optimiert (kurz, prägnant)

### **Performance:**
- ⏱️ Antwortzeit < 5 Sekunden
- 📊 Tool-Calls < 3 pro Anfrage (wenn möglich)
- 💾 Memory funktioniert (10 Messages)

### **Qualität:**
- ✅ Keine Halluzinationen (nur Daten aus Tools)
- ✅ Korrekte Teilenummern
- ✅ Korrekte Seitenzahlen
- ✅ Funktionierende Video-Links

---

## 🔧 **Testing Workflow**

### **1. Unit Tests (einzelne Tools):**
```bash
# Test Error Code Search
curl -X POST http://localhost:5432/rest/v1/rpc/search_error_codes \
  -H "Content-Type: application/json" \
  -d '{"p_error_code": "C-9402", "p_manufacturer": "Lexmark"}'

# Test Parts Search
curl -X POST http://localhost:5432/rest/v1/rpc/search_parts \
  -H "Content-Type: application/json" \
  -d '{"p_search_term": "Fuser Unit", "p_manufacturer": "Lexmark"}'
```

### **2. Integration Tests (n8n Workflows):**
```
1. Import alle Workflows
2. Teste jeden Tool-Workflow einzeln
3. Teste Haupt-Agent mit allen Tools
```

### **3. End-to-End Tests (Chat Interface):**
```
1. Öffne Chat-Interface
2. Durchlaufe alle 10 Test-Szenarien
3. Prüfe Antworten auf Korrektheit
4. Prüfe Memory (Kontext-Bewusstsein)
```

---

## 📊 **Test Results Template**

```markdown
## Test Results - [Date]

### Test 1: Fehlercode-Analyse
- Status: ✅ PASS / ❌ FAIL
- Response Time: 3.2s
- Tools Called: search_error_codes, search_parts
- Notes: Perfekt, alle Infos korrekt

### Test 2: Ersatzteil-Suche
- Status: ✅ PASS
- Response Time: 2.1s
- Tools Called: get_product_info, search_parts
- Notes: Gut, könnte mehr Alternativen zeigen

[... weitere Tests ...]

### Summary:
- Total Tests: 10
- Passed: 9
- Failed: 1
- Average Response Time: 3.5s
```

---

## 🚀 **Next Steps**

1. **Automatisierte Tests** mit Playwright/Cypress
2. **Load Testing** (100 concurrent users)
3. **A/B Testing** (verschiedene Prompts)
4. **User Feedback** (Techniker-Umfrage)

**Happy Testing!** 🎉
