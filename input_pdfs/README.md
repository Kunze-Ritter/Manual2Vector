# PDF Input Folder

## 📁 **Verwendung**

Lege hier alle PDFs rein, die du verarbeiten möchtest!

### **Unterstützte Formate:**
- ✅ **`.pdf`** - Normale PDF-Dateien
- ✅ **`.pdfz`** - Komprimierte PDFs (werden automatisch dekomprimiert)

---

## 🚀 **Batch-Processing**

Das Script verarbeitet **ALLE** PDFs in diesem Ordner automatisch:

```bash
cd backend/processors_v2
python process_production.py
```

---

## 📊 **Was passiert:**

1. **Findet alle PDFs** in diesem Ordner
2. **Dekomprimiert** .pdfz Dateien automatisch
3. **Verarbeitet** jede PDF:
   - Text-Extraktion
   - Produkt-Extraktion (10 Hersteller)
   - Error-Code-Extraktion
   - Link & Video-Extraktion
   - Bild-Extraktion (OCR + Vision AI)
   - Chunk-Erstellung
   - Embedding-Generierung
4. **Speichert alles** in Supabase
5. **Verschiebt** verarbeitete PDFs nach `processed/`

---

## 📦 **Nach der Verarbeitung:**

Erfolgreich verarbeitete PDFs werden automatisch nach `processed/` verschoben:

```
input_pdfs/
├── README.md
├── processed/          ← Hier landen fertige PDFs!
│   ├── Manual1.pdf
│   └── Manual2.pdfz
└── (neue PDFs hier reinlegen)
```

---

## 💡 **Tipps:**

### **Mehrere PDFs auf einmal:**
```
input_pdfs/
├── AccurioPress_C4080.pdf
├── LaserJet_M607.pdf
├── TASKalfa_5053ci.pdfz
└── VersaLink_C7020.pdf
```

→ Alle werden nacheinander verarbeitet!

### **Komprimierte PDFs (.pdfz):**
```bash
# Windows PowerShell - PDF komprimieren:
gzip manual.pdf
# Erstellt: manual.pdf.gz

# Umbenennen zu .pdfz:
mv manual.pdf.gz manual.pdfz
```

→ Script dekomprimiert automatisch!

---

## ⚠️ **Wichtig:**

- **Keine anderen Dateien** hier reinlegen (nur .pdf und .pdfz)
- **Große Dateien** können länger dauern (1-10 Min pro PDF)
- **Duplikate** werden automatisch erkannt (SHA-256 Hash)
- **Fehlgeschlagene PDFs** bleiben im Ordner

---

## 🎯 **Auto-Detection:**

Das Script erkennt automatisch:
- ✅ Hersteller (HP, Canon, Konica Minolta, etc.)
- ✅ Produkttyp (Drucker, Scanner, MFP, etc.)
- ✅ Document Type (Service Manual, Parts Catalog, etc.)

---

**Happy Processing!** 🚀
