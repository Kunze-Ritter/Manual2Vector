# Document Data Deletion Script

## Übersicht

Das `delete_document_data.py` Script löscht **ALLE** Daten, die mit einem oder mehreren Dokumenten verbunden sind.

## Was wird gelöscht?

Für jede Dokument-ID werden folgende Daten gelöscht:

1. **Products** - Alle extrahierten Produkte
2. **Error Codes** - Alle extrahierten Error Codes
3. **Parts** - Alle extrahierten Ersatzteile
4. **Chunks** - Alle Text-Chunks für RAG
5. **Junction Tables** - Alle Verknüpfungen (document_products, document_error_codes, etc.)
6. **Document Metadata** - Das Dokument selbst

## Verwendung

### 1. Interaktiver Modus (Empfohlen)

```powershell
python scripts/delete_document_data.py
```

**Zeigt:**
- Liste der letzten 20 Dokumente
- Titel, Hersteller, Upload-Datum
- Dokument-IDs

**Workflow:**
1. Wähle Dokumente per Nummer (z.B. `1,3,5`)
2. Bestätige mit `DELETE`
3. Daten werden gelöscht

### 2. Direkte Löschung (mit Dokument-ID)

```powershell
# Einzelnes Dokument
python scripts/delete_document_data.py f05a555b-626b-4e90-990e-f1108a43eccf

# Mehrere Dokumente
python scripts/delete_document_data.py f05a555b-626b-4e90-990e-f1108a43eccf 379da86a-7294-4692-99ef-8f34e8ad17ec
```

### 3. Dry Run (Test ohne Löschen)

```powershell
python scripts/delete_document_data.py --dry-run f05a555b-626b-4e90-990e-f1108a43eccf
```

**Zeigt:**
- Dokument-Infos
- Anzahl der zu löschenden Items
- **Löscht NICHTS** (nur Vorschau)

## Beispiel-Output

```
================================================================================
Document Data Deletion
================================================================================

Processing document: f05a555b-626b-4e90-990e-f1108a43eccf
📄 Document: UTAX_4008ci_5008ci_6008ci_7008ci.pdf
   Manufacturer: UTAX
   Uploaded: 2025-10-10

📊 Related data:
   - products: 12 items
   - error_codes: 3914 items
   - parts: 245 items
   - chunks: 156 items
   - document_products: 12 items
   - document_error_codes: 3914 items
   - document_parts: 245 items

   Total items to delete: 8498

🗑️  Deleting data...
   ✓ Deleted 12 items from document_products
   ✓ Deleted 3914 items from document_error_codes
   ✓ Deleted 245 items from document_parts
   ✓ Deleted 156 items from chunks
   ✓ Deleted 3914 items from error_codes
   ✓ Deleted 245 items from parts
   ✓ Deleted 12 items from products
   ✓ Deleted 1 items from documents

✅ Successfully deleted all data for document: f05a555b-626b-4e90-990e-f1108a43eccf
```

## Use Cases

### 1. Dokument neu verarbeiten

**Szenario:** Neue Patterns (UTAX, Kyocera, Accessories) wurden hinzugefügt

```powershell
# 1. Lösche alte Daten
python scripts/delete_document_data.py f05a555b-626b-4e90-990e-f1108a43eccf

# 2. Verarbeite Dokument neu
python backend/processors/process_production.py
```

### 2. Fehlerhafte Daten bereinigen

**Szenario:** Accessories wurden als Produkte erkannt

```powershell
# Lösche Dokument mit falschen Daten
python scripts/delete_document_data.py 379da86a-7294-4692-99ef-8f34e8ad17ec

# Verarbeite mit neuen Accessory-Patterns
python backend/processors/process_production.py
```

### 3. Mehrere Dokumente aufräumen

**Szenario:** Bulk-Cleanup nach Pattern-Updates

```powershell
# Interaktiver Modus
python scripts/delete_document_data.py

# Wähle mehrere Dokumente: 1,2,3,4,5
# Bestätige mit: DELETE
```

## Sicherheit

### ⚠️ WARNUNG

- **Permanente Löschung!** Keine Undo-Funktion!
- **Alle Daten** werden gelöscht (Products, Error Codes, Parts, Chunks)
- **Bestätigung erforderlich** im interaktiven Modus

### Best Practices

1. **Immer erst Dry Run:**
   ```powershell
   python scripts/delete_document_data.py --dry-run <document_id>
   ```

2. **Backup vor Bulk-Deletion:**
   ```sql
   -- Backup mit pg_dump erstellen
   pg_dump -h localhost -U krai_user -d krai > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Teste mit einem Dokument:**
   ```powershell
   # Teste mit einem unwichtigen Dokument
   python scripts/delete_document_data.py <test_document_id>
   ```

## Troubleshooting

### Fehler: "Document not found"

**Ursache:** Dokument-ID existiert nicht

**Lösung:**
```powershell
# Liste alle Dokumente
python scripts/delete_document_data.py --interactive
```

### Fehler: "DATABASE_CONNECTION_URL not found"

**Ursache:** Environment Variables nicht geladen

**Lösung:**
```powershell
# Prüfe .env Dateien
ls .env*

# Stelle sicher, dass .env.database existiert
```

### Fehler: "Permission denied"

**Ursache:** Keine Service Key Rechte

**Lösung:**
```powershell
# Verwende DATABASE_CONNECTION_URL für PostgreSQL
# In .env.database:
DATABASE_CONNECTION_URL=postgresql://krai_user:password@localhost:5432/krai
```

## Technische Details

### Lösch-Reihenfolge

Das Script löscht in dieser Reihenfolge (wichtig für Foreign Keys):

1. Junction Tables (document_products, document_error_codes, document_parts)
2. Child Tables (chunks, error_codes, parts, products)
3. Parent Table (documents)

### Cascade Delete

Falls Cascade Delete in der DB konfiguriert ist, werden manche Tabellen automatisch gelöscht. Das Script ist aber defensiv und löscht explizit alle Tabellen.

### Performance

- **Kleine Dokumente** (<100 items): <1 Sekunde
- **Mittlere Dokumente** (100-1000 items): 1-5 Sekunden
- **Große Dokumente** (>1000 items): 5-30 Sekunden

## Beispiele

### Beispiel 1: UTAX Dokumente neu verarbeiten

```powershell
# Lösche beide UTAX Dokumente
python scripts/delete_document_data.py f05a555b-626b-4e90-990e-f1108a43eccf 379da86a-7294-4692-99ef-8f34e8ad17ec

# Verarbeite neu mit UTAX Patterns
python backend/processors/process_production.py
```

### Beispiel 2: Nur Vorschau (Dry Run)

```powershell
# Zeige, was gelöscht würde
python scripts/delete_document_data.py --dry-run f05a555b-626b-4e90-990e-f1108a43eccf
```

### Beispiel 3: Interaktive Auswahl

```powershell
# Starte interaktiven Modus
python scripts/delete_document_data.py

# Output:
# Recent documents:
#  1. UTAX_4008ci_5008ci_6008ci_7008ci.pdf | UTAX | 2025-10-10
#     ID: f05a555b-626b-4e90-990e-f1108a43eccf
#  2. UTAX_2508ci_3508ci_SM.pdf | UTAX | 2025-10-10
#     ID: 379da86a-7294-4692-99ef-8f34e8ad17ec
#
# Enter document numbers to delete (comma-separated), or 'q' to quit:
# > 1,2
#
# Documents to delete:
#   - UTAX_4008ci_5008ci_6008ci_7008ci.pdf (f05a555b-626b-4e90-990e-f1108a43eccf)
#   - UTAX_2508ci_3508ci_SM.pdf (379da86a-7294-4692-99ef-8f34e8ad17ec)
#
# ⚠️  WARNING: This will permanently delete all data for these documents!
# Type 'DELETE' to confirm: DELETE
#
# [Löscht Daten...]
```

## FAQ

**Q: Kann ich nur bestimmte Daten löschen (z.B. nur Products)?**  
A: Nein, das Script löscht ALLE Daten. Für selektive Löschung nutze SQL direkt.

**Q: Werden auch die PDF-Dateien gelöscht?**  
A: Nein, nur die Datenbank-Einträge. PDFs in R2/Storage bleiben erhalten.

**Q: Kann ich gelöschte Daten wiederherstellen?**  
A: Nein, Löschung ist permanent. Erstelle vorher ein Backup!

**Q: Wie finde ich die Dokument-ID?**  
A: Nutze den interaktiven Modus oder frage PostgreSQL direkt:
```sql
SELECT id, title FROM krai_core.documents ORDER BY created_at DESC LIMIT 10;
```

---

**Autor:** KRAI Development Team  
**Version:** 1.0  
**Letzte Aktualisierung:** 10. Oktober 2025
