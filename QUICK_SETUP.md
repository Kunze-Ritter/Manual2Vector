# ⚡ QUICK SETUP - Anderer PC

## 🎯 **MUST-HAVE (5 Minuten):**

```bash
# Terminal 1: Ollama starten
ollama serve

# Terminal 2: Modelle installieren
ollama pull embeddinggemma
ollama pull qwen2.5:7b
ollama pull llava-phi3

# Prüfen
ollama list
```

**Das war's!** ✅

---

## 📁 **PDFs verarbeiten:**

```bash
# 1. PDFs reinlegen
C:\Users\haast\Docker\KRAI-minimal\input_pdfs\

# 2. Script starten
cd backend/processors_v2
python process_production.py

# 3. Type: YES
```

**Fertig!** 🎉

---

## 📊 **Was du brauchst:**

| Modell | Größe | Zweck |
|--------|-------|-------|
| embeddinggemma | 1.5 GB | Embeddings |
| qwen2.5:7b | 4.7 GB | LLM Extraktion |
| llava-phi3 | 2.9 GB | Vision AI |

**Total:** ~9 GB Disk, ~12 GB RAM

---

## 🚨 **Falls RAM zu wenig (<16 GB):**

```bash
# Nur Basis-Modelle (kein Vision):
ollama pull embeddinggemma
ollama pull qwen2.5:7b
```

**Im Script dann:** `enable_vision=False`

---

**Mehr Details:** Siehe [OLLAMA_MODELS.md](OLLAMA_MODELS.md)
