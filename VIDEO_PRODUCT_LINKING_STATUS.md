# Video-Product Linking Status 🎬

## ✅ Was funktioniert:

1. **manufacturer_id Verknüpfung** ✅
   - 217/217 Videos haben manufacturer_id
   - Vom Document geholt
   - Progressive Search funktioniert

2. **Infrastruktur vorhanden** ✅
   - `krai_content.video_products` Junction Table existiert
   - Script `link_videos_to_products.py` erstellt
   - Zwei Strategien implementiert

## ❌ Was NICHT funktioniert:

### Problem: Documents haben keine Products!

**Status:**
- Videos haben `document_id` ✅
- Documents haben KEINE Products ❌
- Daher: Videos können nicht mit Products verknüpft werden

**Beispiel:**
```
Video: "SD-513_Opening_the_front_console"
  ↓
document_id: b2bf7b0e-3acb-46a9-bcd2-99cce1d5e063
  ↓
document_products: 0 ❌
```

## 🔧 Lösung:

### Option 1: Document-Product Linking zuerst
Bevor Videos mit Products verknüpft werden können, müssen **Documents mit Products** verknüpft werden!

**Workflow:**
1. Document Processing → Extrahiert Products
2. Document-Product Linking → Verknüpft Document mit Products
3. Video-Product Linking → Verknüpft Videos mit Products (via Document)

**Script benötigt:**
```bash
python scripts/link_documents_to_products.py
```

### Option 2: Direkte Verknüpfung aus Video Titel
Videos enthalten oft Model Numbers im Titel:

```
"How to Replace Toner | HP LaserJet Pro M404"
                                        ↑
                                      M404
```

**Strategie:**
1. Extrahiere Model Number aus Titel
2. Suche Product mit diesem Model
3. Verknüpfe direkt

**Vorteil:** Funktioniert auch ohne Document-Product Links
**Nachteil:** Nicht alle Videos haben Model im Titel

### Option 3: Beide kombinieren
```python
# Priority:
# 1. Vom Document (wenn document_products existiert)
# 2. Aus Video Titel (Model Number Extraction)

if document_products:
    link_from_document()
else:
    link_from_title()
```

## 📊 Aktueller Status:

```sql
-- Videos mit document_id
SELECT COUNT(*) FROM krai_content.videos WHERE document_id IS NOT NULL;
-- Result: 217

-- Documents mit Products
SELECT COUNT(DISTINCT document_id) FROM krai_core.document_products;
-- Result: ~10-20 (geschätzt)

-- Videos die Products haben könnten
SELECT COUNT(*) FROM krai_content.videos v
JOIN krai_core.document_products dp ON dp.document_id = v.document_id;
-- Result: 0 ❌
```

## 🚀 Nächste Schritte:

### Kurzfristig (für aktuelle Videos):
1. ✅ Script erstellt: `link_videos_to_products.py`
2. ⏳ Aktiviere Titel-basierte Verknüpfung
3. ⏳ Teste mit Videos die Model Numbers im Titel haben

### Langfristig (für alle Videos):
1. ⏳ Document-Product Linking implementieren
2. ⏳ Beim Processing automatisch verknüpfen
3. ⏳ Re-run Video-Product Linking

## 💡 Workaround für jetzt:

Da die meisten Videos **Konica Minolta** sind und Model Numbers im Titel haben, können wir die Titel-Strategie nutzen:

```python
# In link_videos_to_products.py:
# Aktiviere nur Titel-basierte Suche
# Deaktiviere Document-basierte Suche (da keine Daten)
```

**Erwartung:**
- 20-30% Videos können via Titel verknüpft werden
- Rest benötigt Document-Product Links

## 📝 Test Command:

```bash
# Nach Document-Product Linking:
python scripts/link_videos_to_products.py

# Dann prüfen:
SELECT COUNT(*) FROM krai_content.video_products;

# Erwartung: 50-100 Links
```

---

**Status:** Infrastruktur fertig, aber **Documents haben keine Products**! ⚠️
**Blocker:** Document-Product Linking muss zuerst implementiert werden!
