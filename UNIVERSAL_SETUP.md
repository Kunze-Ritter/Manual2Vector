# 🚀 KR-AI-Engine - Universal Setup Guide

## 📋 **Übersicht**

Dieses Setup funktioniert **auf jedem PC**, egal wo das Projekt liegt oder wie der Benutzer heißt.

---

## 🔧 **Setup auf neuem PC (Universal)**

### **1. Repository klonen:**
```bash
git clone https://github.com/Kunze-Ritter/Manual2Vector.git
cd Manual2Vector
```

### **2. Dependencies installieren:**
```bash
cd backend
pip install -r requirements.txt
```

### **3. Environment-Datei erstellen:**
```bash
# Das Script erstellt automatisch .env aus Template
python tests/krai_master_pipeline.py
```

**Falls das nicht funktioniert:**
```bash
# Manuell kopieren
copy env.template .env
# ODER
copy backend/env.example .env
```

### **4. Credentials eintragen:**
```bash
# .env Datei bearbeiten
notepad .env
# ODER
code .env
```

---

## 🎯 **Universelle Pfad-Erkennung**

Das Script sucht automatisch in **allen möglichen Verzeichnissen**:

### **Relative zum Script:**
- `backend/tests/.env` (gleiches Verzeichnis)
- `backend/.env` (ein Level hoch)
- `.env` (zwei Level hoch)
- `../.env` (drei Level hoch)

### **Relative zum Arbeitsverzeichnis:**
- `./.env` (aktuelles Verzeichnis)
- `../.env` (ein Level hoch)
- `../../.env` (zwei Level hoch)

### **Fallback (relative):**
- `.env`, `../.env`, `../../.env`

---

## 📁 **Unterstützte Projektstrukturen**

Das Script funktioniert mit **allen** dieser Strukturen:

### **Struktur 1: Standard (Git Clone)**
```
C:\Users\[USERNAME]\Manual2Vector\
├── .env
├── backend/
│   └── tests/
│       └── krai_master_pipeline.py
└── env.template
```

### **Struktur 2: Direkt in C:\**
```
C:\Manual2Vector\
├── .env
├── backend/
│   └── tests/
│       └── krai_master_pipeline.py
└── env.template
```

### **Struktur 3: In Docker/Projekte**
```
C:\Users\[USERNAME]\Docker\KRAI-minimal\
├── .env
├── backend/
│   └── tests/
│       └── krai_master_pipeline.py
└── env.template
```

### **Struktur 4: Beliebige Tiefe**
```
C:\Projects\AI\KRAI\Development\
├── .env
├── backend/
│   └── tests/
│       └── krai_master_pipeline.py
└── env.template
```

---

## 🚀 **Ausführung von überall**

### **Option 1: Vom Projekt-Root**
```bash
cd C:\Manual2Vector
python backend/tests/krai_master_pipeline.py
```

### **Option 2: Von backend/ Verzeichnis**
```bash
cd C:\Manual2Vector\backend
python tests/krai_master_pipeline.py
```

### **Option 3: Von tests/ Verzeichnis**
```bash
cd C:\Manual2Vector\backend\tests
python krai_master_pipeline.py
```

### **Option 4: Absoluter Pfad**
```bash
python C:\Manual2Vector\backend\tests\krai_master_pipeline.py
```

---

## 🔍 **Automatische .env-Erstellung**

Falls keine `.env` Datei gefunden wird:

1. **Script sucht nach Templates:**
   - `env.template`
   - `backend/env.example`
   - `../env.template`
   - `../../env.template`

2. **Erstellt automatisch .env:**
   ```bash
   ✅ .env file created from template!
   ⚠️  Please edit .env file with your actual credentials
   ```

3. **Template-Inhalt:**
   ```bash
   SUPABASE_URL=your-supabase-url-here
   SUPABASE_ANON_KEY=your-supabase-key-here
   # ... weitere Variablen
   ```

---

## 🛠️ **Troubleshooting**

### **Problem: "Environment file not found"**

**Lösung 1:** Prüfe Pfade:
```bash
# Script zeigt alle gesuchten Pfade
🔍 Searched paths:
   - C:\Users\Username\Manual2Vector\.env
   - C:\Users\Username\Manual2Vector\backend\.env
   # ...
```

**Lösung 2:** Erstelle manuell:
```bash
copy env.template .env
# ODER
copy backend/env.example .env
```

**Lösung 3:** Verwende absoluten Pfad:
```bash
# In .env Datei alle Pfade absolut machen
SUPABASE_URL=https://your-project.supabase.co
```

### **Problem: "SUPABASE_URL not found"**

**Lösung:** Prüfe .env-Inhalt:
```bash
type .env | findstr SUPABASE_URL
```

### **Problem: Script läuft von falschem Verzeichnis**

**Lösung:** Script funktioniert von überall:
```bash
# Funktioniert von jedem Verzeichnis aus
python C:\path\to\Manual2Vector\backend\tests\krai_master_pipeline.py
```

---

## ✅ **Test der Universalität**

### **Test 1: Verschiedene Verzeichnisse**
```bash
# Von Root
cd C:\Manual2Vector
python backend/tests/krai_master_pipeline.py

# Von backend
cd C:\Manual2Vector\backend
python tests/krai_master_pipeline.py

# Von tests
cd C:\Manual2Vector\backend\tests
python krai_master_pipeline.py
```

### **Test 2: Verschiedene Benutzer**
```bash
# Funktioniert mit jedem Benutzernamen
C:\Users\Admin\Manual2Vector\
C:\Users\Demo\Manual2Vector\
C:\Users\Test\Manual2Vector\
```

### **Test 3: Verschiedene Laufwerke**
```bash
# Funktioniert auf allen Laufwerken
C:\Manual2Vector\
D:\Projects\Manual2Vector\
E:\AI\Manual2Vector\
```

---

## 🎯 **Vorteile der Universalität**

1. **✅ Jeder PC** - Funktioniert unabhängig vom Benutzernamen
2. **✅ Jede Struktur** - Funktioniert mit jeder Verzeichnisstruktur
3. **✅ Jeder Pfad** - Funktioniert von jedem Verzeichnis aus
4. **✅ Auto-Setup** - Erstellt .env automatisch aus Template
5. **✅ Robuste Suche** - Sucht in allen möglichen Verzeichnissen

---

**Bei Fragen:** Siehe KRAI Development Team Lead  
**Version:** 1.0 Universal (Oktober 2025)
