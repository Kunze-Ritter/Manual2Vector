# KRAI Master TODO
> Kompakte Projekt-Übersicht - Letzte Aktualisierung: 05.03.2026

---

## ✅ Erledigt (Kurzübersicht)

### Pipeline & Processing
- [x] 16-Stage Processing Pipeline
- [x] Safe Process mit Retry-Logic
- [x] Idempotency Checks
- [x] Stage Tracking mit WebSocket
- [x] Performance Metrics Collection
- [x] Retry Orchestrator mit Advisory Locks

### Datenbank & Suche
- [x] PostgreSQL + pgvector Embeddings
- [x] Error Code Hierarchy (Migration 018)
- [x] Chunks mit direkter embedding-Spalte
- [x] Full-Text Search
- [x] Similarity Search

### AI/ML
- [x] Ollama Integration (nomic-embed-text, llava)
- [x] Visual Embeddings
- [x] Error Code Extraction
- [x] Parts Extraction
- [x] Series Detection

### Infrastructure
- [x] Docker Compose (Production/Staging/Simple)
- [x] CUDA Support im Dockerfile
- [x] Redis Caching
- [x] MinIO Storage

### Testing & Quality
- [x] E2E Test Suite
- [x] Smoke Tests
- [x] Processor-spezifische Fixtures

---

## 🎯 Offene Tasks

### Hohe Priorität

| # | Task | Beschreibung |
|---|------|--------------|
| 1 | **master_pipeline.py Refactor** | 2717 Zeilen → in kleinere Module aufteilen |
| 2 | **Import-Zeit optimieren** | >30s beim Import - zu viele Abhängigkeiten |
| 3 | **Unit-Tests fehlen** | Embedding/Image Processor haben wenige Tests |

### Mittlere Priorität

| # | Task | Beschreibung |
|---|------|--------------|
| 4 | **Type Annotations** | MyPy konfigurieren, viele `Any` entfernen |
| 5 | **CI/CD Performance** | Linting + Tests in CI beschleunigen |
| 6 | **Dokumentation aktualisieren** | DATABASE_SCHEMA.md, API-Docs |

### Niedrige Priorität

| # | Task | Beschreibung |
|---|------|--------------|
| 7 | **Logging konsolidieren** | Einheitliches Logging-Format |
| 8 | **Config zentralisieren** | Alle ENV-Variablen an einem Ort |
| 9 | **Foliant-System** | Siehe `TODO_FOLIANT.md` |
| 10 | **Product Accessories** | Siehe `TODO_PRODUCT_ACCESSORIES.md` |

---

## 📊 Heutige Änderungen (05.03.2026)

### Refactorings
- [x] error_code_extractor.py → 3 Module aufgeteilt
- [x] embedding_processor.py → 2 Module aufgeteilt  
- [x] image_processor.py → 2 Module aufgeteilt
- [x] master_pipeline.py → **ABGEBROCHEN** (zu komplex)

### Infrastructure
- [x] Database Migration 024 (fehlende Indizes)
- [x] Redis Memory-Limit (512MB)
- [x] Dockerfile Multi-Stage mit CUDA

### Code Quality
- [x] pyproject.toml (Ruff, Black, MyPy)
- [x] .pre-commit-config.yaml
- [x] .github/workflows/lint.yml
- [x] .gitattributes

### Aufräumen
- [x] tests/legacy/ erstellt (deprecated Dateien)
- [x] Backend deprecated/archive aufgeräumt

---

## 📁 Detail-TODOs (für spezifische Bereiche)

| Datei | Bereich |
|-------|---------|
| `TODO.md` | Hauptsächliche Bug-Fixes |
| `docs/project_management/TODO.md` | E2E Tests |
| `docs/project_management/TODO_FOLIANT.md` | Foliant PDF-System |
| `docs/project_management/TODO_PRODUCT_ACCESSORIES.md` | Zubehör-System |
| `docs/project_management/TODO_PRODUCT_CONFIGURATION_DASHBOARD.md` | Dashboard |

---

## 🚀 Nächste Schritte

```
1. master_pipeline.py Refactor planen (größeres Projekt)
2. Unit-Tests für Embedding/Image Processor schreiben
3. Type Annotations verbessern
```
