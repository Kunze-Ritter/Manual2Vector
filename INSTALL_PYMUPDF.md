# 🔧 PyMuPDF Installation Guide

## 🚨 Problem:
```
PyMuPDF not available - cannot extract text from PDF
```

## ✅ Lösung:

### **1. Windows (PowerShell/CMD):**
```bash
pip install PyMuPDF
```

### **2. Linux/Mac:**
```bash
pip install PyMuPDF
```

### **3. Mit Conda:**
```bash
conda install -c conda-forge pymupdf
```

### **4. Für bessere Performance (optional):**
```bash
pip install PyMuPDF[extra]
```

---

## 🔍 Verifikation:

### **Test ob PyMuPDF funktioniert:**
```python
try:
    import fitz
    print("✅ PyMuPDF erfolgreich installiert!")
    print(f"Version: {fitz.__version__}")
except ImportError:
    print("❌ PyMuPDF nicht installiert!")
```

---

## 🐛 Häufige Probleme:

### **Problem 1: Permission Error**
```bash
# Lösung:
pip install --user PyMuPDF
```

### **Problem 2: Build Error**
```bash
# Lösung:
pip install --upgrade pip setuptools wheel
pip install PyMuPDF
```

### **Problem 3: Microsoft Visual C++ fehlt (Windows)**
```bash
# Lösung: Installiere Microsoft C++ Build Tools
# Oder verwende:
pip install --only-binary=all PyMuPDF
```

---

## 🎯 Nach der Installation:

### **1. Script neu starten:**
```bash
cd backend/tests
python krai_master_pipeline.py
```

### **2. Testen:**
```
Wähle Option (1-7): 5
```

### **3. Erwarteter Output:**
```
[1/5] Processing: A93E.pdf (21.6MB)
  [1] Upload: A93E.pdf ✅
  [1] Text Processing: A93E.pdf ✅ (ohne PyMuPDF Fehler!)
  [1] Image Processing: A93E.pdf ✅
  [1] Classification: A93E.pdf ✅
```

---

## 📋 Vollständige Dependencies für KR-AI-Engine:

```bash
pip install PyMuPDF
pip install supabase
pip install python-dotenv
pip install psutil
pip install pillow
pip install pytesseract
pip install easyocr
pip install boto3
pip install requests
pip install asyncio
```

**🎯 Nach PyMuPDF Installation sollte der "PyMuPDF not available" Fehler verschwinden!**
