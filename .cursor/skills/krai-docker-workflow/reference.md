## Compose-Dateien (Kurzmatrix)

| Datei | Wann nutzen | Hinweise |
|------|-------------|----------|
| `docker-compose.simple.yml` | Minimaler Dev-Stack | Weniger Services, schnellster Start |
| `docker-compose.with-firecrawl.yml` | Dev + Web-Scraping | Zusätzliche Services: Redis/Playwright/Firecrawl |
| `docker-compose.production.yml` | “Production parity” | Voller Stack, Healthchecks, Firecrawl Worker |
| `docker-compose.staging.yml` | Benchmark/isoliert | Typisch separate Ports/DB (für Performance-Tests) |
| `docker-compose.cuda.yml` | GPU/CUDA | Nutzt `Dockerfile.cuda`, reserviert GPU via NVIDIA runtime |

## Setup/Validation-Skripte

### Secrets & `.env` erzeugen

- Windows (empfohlen): `.\setup.ps1`
- Linux/macOS: `./setup.sh`

### `.env` validieren

```bash
python scripts/validate_env.py
python scripts/validate_env.py --strict
```

## Healthcheck / Integration / Orchestrator

- **Health check**
  - Windows: `.\scripts\docker-health-check.ps1`
  - Linux/macOS: `./scripts/docker-health-check.sh`
- **Integration tests**
  - Windows: `.\scripts\docker-integration-tests.ps1`
  - Linux/macOS: `./scripts/docker-integration-tests.sh`
- **Full orchestrator**
  - Windows: `.\scripts\full-docker-setup.ps1`
  - Linux/macOS: `./scripts/full-docker-setup.sh`
  - Typische Optionen:
    - `--skip-clean` / `-SkipClean`
    - `--skip-integration` / `-SkipIntegration`
    - `--log-file setup.log` / `-LogFile "setup.log"`

## Standard-Commands (Compose)

> Default: zuerst `ps`, dann `logs`, dann gezielt `restart`. Keine “großen” Resets ohne explizite Anforderung.

```bash
docker-compose -f <compose-file> up -d --build
docker-compose -f <compose-file> ps
docker-compose -f <compose-file> logs -f <service>
docker-compose -f <compose-file> restart <service>
docker-compose -f <compose-file> down
```

## Typische Services (Namen aus Compose)

- Backend: `krai-engine`
- PostgreSQL: `krai-postgres`
- MinIO: `krai-minio`
- Ollama: `krai-ollama`
- Redis: `krai-redis` (nicht überall)
- Laravel: `laravel-admin` + `laravel-nginx`
- Firecrawl: `krai-firecrawl-api`, `krai-firecrawl-nuq-worker`, `krai-playwright` (nicht überall)

## Typische Endpunkte (bei Zweifel Compose-Ports prüfen)

- Backend Health: `http://localhost:8000/health`
- Backend Docs: `http://localhost:8000/docs`
- MinIO Console: `http://localhost:9001`
- MinIO API: `http://localhost:9000`
- Ollama: `http://localhost:11434`
- Laravel Dashboard (dev oft): `http://localhost:8080`

## GPU/CUDA Referenz

- Start:
  - `docker-compose -f docker-compose.cuda.yml up -d --build`
- Verifizieren:
  - `docker exec krai-engine-cuda nvidia-smi`
  - `docker exec krai-engine-cuda python -c "import torch; print(torch.cuda.is_available())"`

## “Clean Reset” (destruktiv – nur bei explizitem Wunsch)

- Windows: `.\scripts\docker-clean-setup.ps1`
- Linux/macOS: `./scripts/docker-clean-setup.sh`

Diese Skripte stoppen Container, entfernen KRAI-Volumes und starten frisch. Nicht für Produktion/Staging verwenden, wenn Daten wichtig sind.
