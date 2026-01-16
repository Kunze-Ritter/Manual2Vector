# Metadata → Parts → Series → Storage Test Suite

Diese README beschreibt die wichtigsten Tests für die vier zusammenhängenden Prozessoren:

- MetadataProcessorAI
- PartsProcessor
- SeriesProcessor
- StorageProcessor

Sie soll helfen, schnell zu verstehen, **was** wo getestet wird und **wie** man gezielt Teil-Suiten ausführt.

---

## 1. MetadataProcessorAI

- **Dateien**
  - `tests/processors/test_metadata_processor_unit.py`
  - `tests/processors/test_metadata_processor_e2e.py`

- **Unit (test_metadata_processor_unit.py)**
  - Testet ErrorCodeExtractor / VersionExtractor isoliert.
  - Fokus auf deterministische Extraktion und Randfälle.

- **E2E (test_metadata_processor_e2e.py)**
  - Ältere E2E-Klassen für den Legacy-API-Contract sind per `@pytest.mark.skip` neutralisiert.
  - Neue Tests decken die **DB-Persistenz v2** ab:
    - Inserts in `error_codes` via `client.table('error_codes').insert(...).execute()`.
    - Update von `documents.version` via `client.table('documents').update(...).eq(...).execute()`.
  - Läuft über `MetadataProcessorAI.safe_process` und `ProcessingResult`.

- **Marker**
  - `@pytest.mark.metadata`
  - `@pytest.mark.e2e` (für die neuen E2E-Pfade)

---

## 2. PartsProcessor

- **Dateien**
  - `tests/processors/test_parts_processor_unit.py`
  - `tests/processors/test_parts_processor_e2e.py`

- **Unit-Helper-Tests (test_parts_processor_unit.py)**
  - `_extract_part_name` – diverse Kontext-Patterns, Längenbegrenzung, No-Match.
  - `_extract_description_and_category` – Keyword-basierte Kategorien + Description-Truncation.
  - `_extract_and_link_parts_from_text` – erfolgreicher Link-Path, keine Teile, fehlende Teile, DB-Fehler, ungültige Extractor-Ausgaben, Exceptions.
  - Nutzung von `mock_database_adapter` und `patch('backend.processors.parts_processor.extract_parts_with_context')`.

- **E2E / Integration (test_parts_processor_e2e.py)**
  - Verwendet `mock_database_adapter` aus `tests/processors/conftest.py`.
  - Behandelt Teile-Persistenz als **Dicts**, die `krai_parts.parts_catalog`-ähnlich sind.
  - Szenarien u. a.:
    - Teile-Erstellung/Update je nach bestehendem Datensatz.
    - Hersteller-spezifische Extraktion.
    - Chunk-basierte Verarbeitung eines Dokuments.

- **Marker**
  - `@pytest.mark.parts`
  - `@pytest.mark.e2e` für die End-to-End-Fälle.

---

## 3. SeriesProcessor

- **Dateien**
  - `tests/processors/test_series_processor_unit.py`
  - `tests/processors/test_series_processor_e2e.py`

- **Unit (test_series_processor_unit.py)**
  - Kleinere, gezielte Tests für Hilfsfunktionen (sofern vorhanden).

- **E2E (test_series_processor_e2e.py)**
  - Nutzt `mock_database_adapter` und patched `utils.series_detector.detect_series` (bzw. den Legacy-Import-Pfad).
  - Szenarien:
    - Serie erkannt und Produkt verlinkt.
    - Vorhandene Serie wird wiederverwendet (kein doppelter Insert).
    - Batch-Verarbeitung via `process_all_products`.
    - Kein Serien-Treffer → `series_detected=False`.
    - `process(context)`-Wrapper mit `SimpleNamespace(product_id=...)`.

- **Marker**
  - `@pytest.mark.series`
  - `@pytest.mark.e2e`

---

## 4. StorageProcessor

- **Dateien**
  - `tests/processors/test_storage_processor_unit.py`
  - `tests/processors/test_storage_processor_e2e.py`

- **Unit (test_storage_processor_unit.py)**
  - Verwendet `MockDatabaseService` + `AsyncStorageService` (lokale Mocks).
  - Abgedeckte Fälle:
    - Laden aus `vw_processing_queue`.
    - Speichern von Link-, Video-, Chunk-, Embedding- und Image-Artefakten.
    - Reiche Metadaten für Links/Videos/Bilder (z. B. `context_description`, `page_header`, `related_*`).
    - Failure-Handling:
      - Kein Storage-Service (Image wird übersprungen, keine DB-Inserts).
      - Upload-Failure → `_store_image_artifact` wirft `ValueError`.

- **E2E (test_storage_processor_e2e.py)**
  - Simuliert `vw_processing_queue` über ein lokales Mock-Client-Backend.
  - Szenarien:
    - Alle Artifact-Typen in einem Lauf.
    - Upload-Failure → `result.success=False`, `saved_items=0`, `errors` gefüllt, keine `vw_images`-Einträge.
    - Ungültiges JSON im Payload (wird abgefangen, Link wird mit leerem/teilweisem Payload angelegt).
    - Unsupported `artifact_type` wird übersprungen.
    - Fehlender `document_id` im Kontext löst `ValueError` aus.

- **Marker**
  - `@pytest.mark.storage`
  - `@pytest.mark.e2e`

---

## 5. Cross-Stage Flow: Metadata → Parts → Series → Storage

- **Datei**
  - `tests/processors/test_metadata_parts_series_storage_flow_e2e.py`

- **Ziel**
  - Happy-Path über alle vier Prozessoren in einer kontrollierten Mock-Umgebung:
    - `MetadataProcessorAI` extrahiert einen Error-Code + Version und speichert beides.
    - `PartsProcessor` extrahiert Teile aus Chunk-/Solution-Text, speichert sie und erzeugt Error-Code↔Part-Links.
    - `SeriesProcessor` erkennt eine Serie (z. B. für HP M404n) und verlinkt das Produkt.
    - `StorageProcessor` persistiert ein Link-Artefakt aus `vw_processing_queue` nach `vw_links`.

- **Mocks**
  - Eigenständige Mocks im Testmodul:
    - `MockClient` + `MockTable` (PostgreSQL-ähnliches `table().select().insert().execute()`-Interface).
    - `UnifiedMockDatabase` mit Methoden wie `get_document`, `get_chunks_by_document`, `get_error_codes_by_document`, `create_part`, `get_part_by_number*`, `create_product_series`, `update_product`, …
    - `AsyncStorageService` für Bild-/Storage-Aufrufe (hier nur Links genutzt).

- **Marker**
  - `@pytest.mark.metadata`
  - `@pytest.mark.parts`
  - `@pytest.mark.series`
  - `@pytest.mark.storage`
  - `@pytest.mark.e2e`

- **Aufruf-Beispiel**

```bash
python -m pytest tests/processors/test_metadata_parts_series_storage_flow_e2e.py -m e2e
```

---

## 6. Typische Test-Kombinationen

- **Nur Metadata/Parts/Series/Storage E2E-Flows**

```bash
python -m pytest tests/processors/test_metadata_processor_e2e.py -m metadata
python -m pytest tests/processors/test_parts_processor_e2e.py -m parts
python -m pytest tests/processors/test_series_processor_e2e.py -m series
python -m pytest tests/processors/test_storage_processor_e2e.py -m storage
python -m pytest tests/processors/test_metadata_parts_series_storage_flow_e2e.py -m e2e
```

- **Schneller Sanity-Check der Unit-Helper**

```bash
python -m pytest tests/processors/test_metadata_processor_unit.py -m metadata
python -m pytest tests/processors/test_parts_processor_unit.py -m parts
python -m pytest tests/processors/test_series_processor_unit.py -m series
python -m pytest tests/processors/test_storage_processor_unit.py -m storage
```

Diese README soll als Startpunkt dienen. Bei größeren Refactors bitte die Liste der Dateien/Marker und Beispiel-Befehle mitpflegen.
