# Processing Checklist für nächsten Durchlauf

## ✅ Was funktioniert aktuell:

1. **Progressive Streaming API** ✅
   - Sucht schrittweise: Service Manuals → Ersatzteile → Videos → Bulletins
   - Streamt Ergebnisse in Echtzeit
   - Keine Fehler mehr

2. **Fehlercode-Erkennung** ✅
   - Erkennt Fehlercodes korrekt
   - Extrahiert Beschreibungen
   - Findet Lösungsschritte

3. **Keyword-basierte Suche** ✅
   - Ersatzteile basierend auf Lösung (formatter, fuser, etc.)
   - Videos basierend auf Keywords
   - Intelligente Filterung

## ⚠️ Was beim nächsten Processing geprüft werden muss:

### 1. **Bilder-Verknüpfung** (KRITISCH!)

**Problem:** Fehlercodes haben `chunk_id`, aber diese Chunks haben keine Bilder.

**Zu prüfen:**
- [ ] `error_code_extractor.py` - Setzt es die richtige `chunk_id`?
- [ ] Werden Bilder beim Processing mit dem richtigen `chunk_id` verknüpft?
- [ ] Sind die Bilder überhaupt im richtigen Schema? (`krai_content.images`)

**Test nach Processing:**
```sql
-- Prüfe ob error_codes chunk_ids mit Bildern haben
SELECT ec.error_code, ec.chunk_id, COUNT(i.id) as image_count
FROM krai_intelligence.error_codes ec
LEFT JOIN krai_content.images i ON i.chunk_id = ec.chunk_id
WHERE ec.chunk_id IS NOT NULL
GROUP BY ec.error_code, ec.chunk_id
HAVING COUNT(i.id) > 0;
```

### 2. **Video-Verknüpfung**

**Problem:** Nur 10 Videos in DB, keine manufacturer_id.

**Zu prüfen:**
- [ ] Video Enrichment Script läuft?
- [ ] `manufacturer_id` wird korrekt gesetzt?
- [ ] YouTube/Vimeo/Brightcove IDs werden extrahiert?

**Test nach Processing:**
```sql
-- Prüfe Videos mit manufacturer_id
SELECT manufacturer_id, COUNT(*) as video_count
FROM krai_content.videos
WHERE manufacturer_id IS NOT NULL
GROUP BY manufacturer_id;
```

### 3. **Service Bulletins**

**Problem:** Keine Documents mit `document_type = 'bulletin'`.

**Zu prüfen:**
- [ ] Werden Bulletins als separater `document_type` erkannt?
- [ ] Oder sind sie in `links` Tabelle?

**Test nach Processing:**
```sql
-- Prüfe Bulletin Documents
SELECT document_type, COUNT(*) 
FROM krai_core.documents 
WHERE document_type ILIKE '%bulletin%'
GROUP BY document_type;
```

### 4. **Chunk-Qualität**

**Aktueller Status:** 80% haben Fehlercode im Chunk, 80% haben Lösungs-Keywords.

**Zu verbessern:**
- [ ] 100% sollten Fehlercode im Chunk haben
- [ ] Mehr Lösungs-Keywords erkennen

**Test nach Processing:**
```python
python check_enrichment_quality.py
```

## 🔧 Processor-Fixes die gemacht werden sollten:

### 1. **error_code_extractor.py**

Prüfe ob `chunk_id` korrekt gesetzt wird:

```python
# In enrich_error_codes_from_document():
# Stelle sicher dass chunk_id gesetzt wird wenn Bilder gefunden werden
if images_found:
    error_code.chunk_id = chunk_id_with_images
```

### 2. **image_processor.py**

Stelle sicher dass Bilder mit dem richtigen `chunk_id` verknüpft werden:

```python
# Beim Image Processing:
# Finde den passenden chunk für das Bild (gleiche Seite, gleicher Kontext)
chunk = find_chunk_for_image(page_number, context)
if chunk:
    image.chunk_id = chunk.id
```

### 3. **video_enrichment_service.py**

Prüfe ob `manufacturer_id` gesetzt wird:

```python
# Beim Video Processing:
# Extrahiere Hersteller aus Video-Titel oder Beschreibung
manufacturer = extract_manufacturer_from_video(title, description)
if manufacturer:
    video.manufacturer_id = manufacturer.id
```

## 📊 Erwartete Ergebnisse nach neuem Processing:

- ✅ **50+ Fehlercodes mit Bildern** (aktuell: 0)
- ✅ **100+ Videos mit manufacturer_id** (aktuell: 0)
- ✅ **10+ Service Bulletins** (aktuell: 0)
- ✅ **95%+ Confidence** bei Fehlercode-Zuordnung (aktuell: 82%)

## 🚀 Test-Kommandos nach Processing:

```bash
# 1. Prüfe Enrichment-Qualität
python check_enrichment_quality.py

# 2. Finde Fehlercode mit Bildern
python find_error_with_real_images.py

# 3. Teste in OpenWebUI
# Suche nach einem Fehlercode der Bilder haben sollte
# Erwartung: Bilder werden angezeigt
```

## 📝 Notizen:

- API läuft auf Port **8000** (Lead Scraper auf anderem Port)
- Progressive Streaming funktioniert perfekt
- Keyword-basierte Suche ist implementiert
- Alle Spalten-Namen sind korrekt (`storage_url`, `ai_description`, etc.)

---

**Status:** Bereit für nächsten Processing-Durchlauf! 🎯
