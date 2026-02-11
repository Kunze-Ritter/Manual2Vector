---
name: krai-docker-workflow
description: Orchestrates KRAI Docker Compose setup and operations (setup scripts, selecting compose files, starting/stopping services, health checks, troubleshooting, and optional CUDA/GPU runs). Use when the user mentions docker, docker compose, containers, compose files, setup.ps1/setup.sh, health checks, clean setup, staging/production, Firecrawl, CUDA, GPU, Ollama, MinIO, PostgreSQL, or the Laravel dashboard.
---

# KRAI Docker Workflow

## Ziel

Führe einen sicheren, reproduzierbaren Workflow aus, um KRAI mit Docker Compose zu starten, zu prüfen und zu debuggen. Bevorzuge nicht-destruktive Schritte; **lösche niemals Volumes/Daten**, außer der User fordert es explizit.

## Quick Start (Entscheidungsbaum)

1. **Was ist das Ziel?** Wähle die passende Compose-Datei:
   - **Minimal / dev (kleiner Stack)**: `docker-compose.simple.yml`
   - **Dev + Firecrawl**: `docker-compose.with-firecrawl.yml`
   - **“Production parity” / voller Stack**: `docker-compose.production.yml`
   - **Staging/Benchmark-Isolation**: `docker-compose.staging.yml`
   - **GPU/CUDA**: `docker-compose.cuda.yml` (plus CUDA-Prereqs)

2. **Gibt es bereits eine `.env`?**
   - Wenn **nein**, bevorzuge Setup-Skripte:
     - Windows: `.\setup.ps1`
     - Linux/macOS: `./setup.sh`
   - Fallback (nur wenn nötig): `.env.example` → `.env` kopieren und Werte setzen.

3. **Starten**
   - Standard:
     - `docker-compose -f <compose-file> up -d --build`
   - Wenn `docker compose` verfügbar ist, darf es statt `docker-compose` genutzt werden (Repo-Skripte erkennen i.d.R. beides).

4. **Validieren**
   - Schnell-Healthcheck:
     - Windows: `.\scripts\docker-health-check.ps1`
     - Linux/macOS: `./scripts/docker-health-check.sh`
   - Optional (nur wenn ausdrücklich gewünscht): Persistenztest
     - Windows: `.\scripts\docker-health-check.ps1 -TestPersistency`
     - Linux/macOS: `./scripts/docker-health-check.sh --test-persistency`

## Standard-Workflow (Schritt-für-Schritt)

### 1) Pre-Flight Checks (nicht-destruktiv)

- Prüfe, ob `.env` existiert (und **niemals** Secrets in Chats/Logs kopieren).
- Empfehle vor dem Start:
  - `python scripts/validate_env.py`

### 2) Stack starten/stoppen

- Start:
  - `docker-compose -f <compose-file> up -d --build`
- Status:
  - `docker-compose -f <compose-file> ps`
- Logs (gezielt):
  - `docker-compose -f <compose-file> logs -f <service>`
- Stop (ohne Datenverlust):
  - `docker-compose -f <compose-file> down`

### 3) Health & Kern-Endpunkte prüfen

- Nutze bevorzugt die Health-Check-Skripte:
  - `scripts/docker-health-check.ps1` oder `scripts/docker-health-check.sh`
- Typische Endpunkte (Ports können je nach Compose-Datei abweichen; bei Zweifel Ports in der Compose-Datei prüfen):
  - Backend: `http://localhost:8000/health`
  - Backend Docs: `http://localhost:8000/docs`
  - MinIO: `http://localhost:9000/minio/health/live`
  - Ollama: `http://localhost:11434/api/tags`
  - Laravel Dashboard (dev häufig via `laravel-nginx`): `http://localhost:8080`

### 4) Troubleshooting-Playbook (kurz)

Wenn etwas “nicht startet”:

- **Erst**: `docker-compose -f <compose-file> ps`
- **Dann**: Logs vom betroffenen Service:
  - `docker-compose -f <compose-file> logs --tail=200 <service>`
- **Dann**: Service neu starten:
  - `docker-compose -f <compose-file> restart <service>`
- **Wenn DB-Probleme**:
  - Logs: `docker-compose -f <compose-file> logs --tail=200 krai-postgres`
  - Basic Exec-Checks (nur wenn Container-Namen bekannt/aus `ps`):
    - `docker exec <postgres-container> pg_isready -U <user> -d <db>`

## GPU/CUDA Workflow (wenn User GPU will)

1. Verwende `docker-compose.cuda.yml`.
2. Baue/Starte:
   - `docker-compose -f docker-compose.cuda.yml up -d --build`
3. Verifikation:
   - `docker exec krai-engine-cuda nvidia-smi`
   - `docker exec krai-engine-cuda python -c "import torch; print('CUDA available:', torch.cuda.is_available())"`

## Destruktive Aktionen (nur auf expliziten Wunsch)

- Beispiele (nur wenn User ausdrücklich “reset/clean setup/alles löschen” will):
  - `.\scripts\docker-clean-setup.ps1` oder `./scripts/docker-clean-setup.sh`
  - `.\scripts\full-docker-setup.ps1` oder `./scripts/full-docker-setup.sh` (kann Clean-Setup enthalten)

## Zusätzliche Ressourcen

- Details & Referenz: [reference.md](reference.md)
