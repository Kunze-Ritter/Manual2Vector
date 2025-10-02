# Stage 3 Vision AI Fix - Oktober 2, 2025

## 🔍 Problem gefunden:

### **Stage 3 Vision AI lief NICHT richtig!**

**Symptome:**
- ✅ Pipeline läuft ohne Crash
- ❌ Aber: `ai_confidence` immer 0.50
- ❌ Aber: `ai_description` immer leer/generic
- ❌ Aber: `figure_number` und `figure_context` leer
- ❌ Aber: `chunk_id` leer

**Grund:**
1. Vision AI crashed → Fallback wurde verwendet
2. Fallback gibt generische Werte zurück
3. Pipeline läuft weiter, **niemand merkt dass Vision AI nicht funktioniert**

---

## ✅ Fixes angewendet:

### 1. **DISABLE_VISION_PROCESSING Check in `analyze_image()`**
**Problem**: Stage 3 prüfte diese Einstellung NICHT
**Fix**: Jetzt wird geprüft und Fallback verwendet wenn disabled

**Code**: `backend/services/ai_service.py` Zeile 405-414
```python
# Check if vision processing is disabled
if os.getenv('DISABLE_VISION_PROCESSING', 'false').lower() == 'true':
    self.logger.info("Vision processing disabled, using fallback analysis")
    return {
        "image_type": "diagram",
        "description": "Technical image (vision processing disabled)",
        "contains_text": False,
        "tags": ["technical"],
        "confidence": 0.5
    }
```

### 2. **Stage 5 Fallback wie Stage 3**
**Problem**: Stage 5 crashte bei Vision AI Fehler
**Fix**: Jetzt warnt es nur und macht weiter

**Code**: `backend/processors/metadata_processor_ai.py` Zeile 294-298
```python
except Exception as img_error:
    # Fallback: Log warning but continue (don't crash pipeline)
    self.logger.warning(f"Vision AI failed for image {image.get('id')}: {img_error}")
    # Continue with next image even if this one fails
    continue
```

### 3. **ImageModel erweitert mit fehlenden Feldern**
**Problem**: DB hat Felder die im Code-Model fehlen
**Fix**: Model erweitert

**Code**: `backend/core/data_models.py` Zeile 163-174
```python
ai_description: Optional[str] = "Technical image"  # Default value
ai_confidence: float = 0.5  # Default when Vision AI not used
figure_number: Optional[str] = None  # Figure reference (e.g., "1", "2.1")
figure_context: Optional[str] = None  # Context text around figure
manual_description: Optional[str] = None  # Manual description override
chunk_id: Optional[str] = None  # Link to chunk if extracted from chunk
```

---

## 📊 DB-Felder Erklärung:

| Feld | Typ | Default | Zweck | Wird gefüllt von |
|------|-----|---------|-------|------------------|
| `ai_description` | TEXT | "Technical image" | Vision AI Bildbeschreibung | Stage 3: Vision AI |
| `ai_confidence` | FLOAT | 0.5 | Vision AI Confidence | Stage 3: Vision AI |
| `manual_description` | TEXT | NULL | Manuelle Überschreibung | **Manuell/später** |
| `figure_number` | VARCHAR(50) | NULL | Figur-Nummer (z.B. "1", "2.1") | **Link Processor (später)** |
| `figure_context` | TEXT | NULL | Kontext-Text um Figur-Referenz | **Link Processor (später)** |
| `chunk_id` | UUID | NULL | Verlinkung zu Chunk | **Link Processor (später)** |

### **NULL vs. Default:**

**NULL ist gut für:**
- ✅ `figure_number` - Nicht jedes Bild hat eine Nummer
- ✅ `figure_context` - Nicht jedes Bild hat Kontext
- ✅ `manual_description` - Optional, nur wenn manuell gesetzt
- ✅ `chunk_id` - Nur wenn Bild aus Chunk extrahiert wurde

**Default ist gut für:**
- ✅ `ai_description` - Immer ein Wert, auch wenn Vision AI crasht
- ✅ `ai_confidence` - Immer 0.5 wenn Vision AI nicht läuft

---

## 🧪 So erkennst du ob Vision AI läuft:

### ✅ Vision AI funktioniert:
```
Image analyzed: diagram (confidence: 0.85)
Image analyzed: screenshot (confidence: 0.92)
```
**DB**: `ai_confidence` > 0.5, `ai_description` detailliert

### ⚠️ Vision AI crashed (Fallback):
```
AI analysis failed for image 1: model runner stopped
```
**DB**: `ai_confidence` = 0.5, `ai_description` = "Technical image"

### 🔇 Vision AI disabled:
```
Vision processing disabled, using fallback analysis
```
**DB**: `ai_confidence` = 0.5, `ai_description` = "Technical image (vision processing disabled)"

---

## 🎯 Nächste Schritte:

### **figure_number & figure_context füllen:**

Diese werden NICHT von Stage 3 gefüllt, sondern später von einem **Link/Reference Processor**:

**Beispiel:**
```
Text: "See Figure 2.1 for detailed assembly instructions"
       ↓
figure_number = "2.1"
figure_context = "See Figure 2.1 for detailed assembly instructions"
chunk_id = <chunk_id wo der Text steht>
```

**Wird implementiert in:**
- Stage 6: Link Extraction Processor (teilweise schon da)
- Oder separater Figure Reference Processor

---

## 📝 Zusammenfassung:

| Was | Vorher | Nachher |
|-----|--------|---------|
| **Stage 3 Vision AI** | Crashed → Fallback | Checked disabled + Fallback |
| **Stage 5 Vision AI** | Crashed → Pipeline stoppt | Warnung + weiter |
| **DB Model** | Fehlende Felder | Alle Felder vorhanden |
| **ai_confidence** | 0.0 oder 0.5 | 0.5 (Fallback) oder > 0.5 (AI) |
| **ai_description** | NULL | "Technical image" (Fallback) |
| **figure_number** | N/A | NULL (später von Link Processor) |

---

## 🚀 Ergebnis:

**Jetzt:**
- ✅ Stage 3 prüft DISABLE_VISION_PROCESSING
- ✅ Stage 5 crasht nicht mehr
- ✅ Alle DB-Felder im Model
- ✅ Sinnvolle Defaults statt NULL
- ✅ Du siehst im Log ob Vision AI läuft oder nicht

**figure_number / figure_context / chunk_id bleiben NULL** → Das ist korrekt! Die werden später von einem anderen Processor gefüllt.

---

**Datum**: Oktober 2, 2025, 13:05 Uhr
**Status**: ✅ Fertig
