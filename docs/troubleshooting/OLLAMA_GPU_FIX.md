# 🎮 Ollama GPU/RAM Optimierung

**Problem:** LLaVA Model zu groß für 8GB VRAM → Crashes beim Image-Processing

---

## 🔧 Lösung 1: Kleineres Model (Empfohlen!)

### **Option A: llava:7b (Klein, Schnell)**

```bash
# Aktuelles Model stoppen
ollama stop

# Kleineres Model pullen (nur 4GB VRAM!)
ollama pull llava:7b

# In .env ändern:
OLLAMA_MODEL_VISION=llava:7b
```

**Vorteile:**
- ✅ Passt in 8GB VRAM (braucht nur ~4GB)
- ✅ Schneller (weniger Parameter)
- ✅ Stabil, kein Crash
- ✅ Gute Qualität für Dokument-OCR

---

### **Option B: llava:7b-q4 (Noch kleiner, quantisiert)**

```bash
ollama pull llava:7b-q4

# In .env:
OLLAMA_MODEL_VISION=llava:7b-q4
```

**Vorteile:**
- ✅ Nur ~2.5GB VRAM!
- ✅ Sehr schnell
- ✅ Minimal weniger Qualität (aber OK für OCR)

---

## 🔧 Lösung 2: System RAM nutzen (CPU Fallback)

### **Ollama Umgebungsvariablen setzen**

**Windows (PowerShell als Admin):**
```powershell
# System RAM limit erhöhen (nutzt mehr CPU RAM)
[System.Environment]::SetEnvironmentVariable('OLLAMA_MAX_LOADED_MODELS', '1', 'Machine')
[System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_PARALLEL', '1', 'Machine')
[System.Environment]::SetEnvironmentVariable('OLLAMA_MAX_QUEUE', '512', 'Machine')

# CPU/GPU Split forcieren (mehr auf CPU)
[System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_GPU', '14', 'Machine')
# 14 Layers auf GPU, Rest auf CPU RAM

# Ollama neustarten
Restart-Service Ollama
```

**Windows (CMD als Admin):**
```cmd
setx OLLAMA_MAX_LOADED_MODELS "1" /M
setx OLLAMA_NUM_PARALLEL "1" /M
setx OLLAMA_MAX_QUEUE "512" /M
setx OLLAMA_NUM_GPU "14" /M

# PC neu starten oder Ollama Service neustarten
```

---

## 🎯 Empfohlene Kombination (Beste Performance)

```bash
# 1. Kleineres Model
ollama pull llava:7b

# 2. Umgebungsvariablen (Windows PowerShell als Admin)
[System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_GPU', '20', 'Machine')
# Mehr GPU-Layers weil Model kleiner ist

# 3. .env anpassen
OLLAMA_MODEL_VISION=llava:7b

# 4. Ollama neu starten
taskkill /F /IM ollama.exe
ollama serve
```

---

## 📊 Model-Vergleich

| Model | VRAM | System RAM | Speed | Quality | Empfehlung |
|-------|------|------------|-------|---------|------------|
| **llava:latest** (13B) | 11.2GB | 8GB | Mittel | Sehr gut | ❌ Zu groß |
| **llava:7b** | 4GB | 4GB | Schnell | Gut | ✅ **Empfohlen** |
| **llava:7b-q4** | 2.5GB | 2GB | Sehr schnell | OK | ✅ Backup |
| **llava:34b** | 20GB+ | 16GB+ | Langsam | Exzellent | ❌ Overkill |

---

## 🧪 Testen

```bash
# Model testen
ollama run llava:7b

# In Chat:
>>> Can you describe this image? [Bild einfügen mit /add image.png]

# Sollte funktionieren ohne Crash!
```

---

## 🔍 Aktuelle System-Info

**Von deinem System:**
```
GPU: NVIDIA RTX 2000 Ada Generation Laptop GPU
VRAM: 7.1 GB verfügbar
System RAM: 63.4 GB total, 24.2 GB frei
```

**Aktuelles Problem:**
```
llava:latest braucht: 11.2 GB VRAM
Verfügbar: 7.1 GB VRAM
→ Crash! ❌
```

**Mit llava:7b:**
```
llava:7b braucht: 4 GB VRAM
Verfügbar: 7.1 GB VRAM
→ Passt! ✅
```

---

## 🚀 Quick Start (Jetzt ausführen!)

```bash
# 1. Ollama stoppen
taskkill /F /IM ollama.exe

# 2. Kleineres Model holen
ollama pull llava:7b

# 3. Ollama starten
ollama serve

# 4. In neuem Terminal: Pipeline weiterlaufen lassen
cd c:\Users\haast\Docker\KRAI-minimal\backend\tests
python krai_master_pipeline.py
# Option 9

# Sollte jetzt funktionieren! 🎉
```

---

## 🛠️ Troubleshooting

### **Model lädt nicht**
```bash
# Models checken
ollama list

# Model manuell pullen
ollama pull llava:7b --verbose
```

### **Noch immer Crash**
```bash
# Auf quantisiert downgraden
ollama pull llava:7b-q4

# Oder Image-Processing deaktivieren (siehe unten)
```

### **Performance zu langsam**
```bash
# Mehr GPU Layers
[System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_GPU', '25', 'Machine')

# Ollama neu starten
```

---

## 💡 Alternative: Image-Processing optional machen

Falls Ollama weiter Probleme macht, können wir Image-Processing als **non-critical** machen:

```python
# Pipeline läuft durch, auch wenn Image-Processing crasht
# Andere Stages (Text, Links, Embeddings) laufen normal
```

---

**Created:** Oktober 2025  
**Status:** ✅ Ready to Fix
