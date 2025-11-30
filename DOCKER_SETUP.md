# Docker Setup für KRAI Engine

## 🐳 Überblick

Dieses Handbuch beschreibt das vollständige Docker-Setup für die KRAI Engine. Es basiert auf der konsolidierten `.env`-Struktur mit 10 Sektionen und mehr als 15 automatisch generierten Secrets. Für einen schnellen Einstieg nutze die Setup-Skripte und validiere anschließend die Umgebung, bevor du Docker-Services startest.

Weitere Einstiegsinformationen findest du im [README.md](README.md). Dieses Dokument konzentriert sich ausschließlich auf Docker.

---

## 🚀 Schnellstart

### Methode 1 – Automatisches Setup (empfohlen)

**Linux/macOS**

```bash
./setup.sh
```

**Windows (Empfohlen: PowerShell)**

```powershell
./setup.ps1
```

**Windows (Legacy: Batch)**

```cmd
setup.bat
```

**Welches Skript soll ich verwenden?**

- **Linux/macOS:** `./setup.sh` (Bash)
- **Windows 10/11:** `./setup.ps1` (PowerShell) – **Empfohlen**
- **Ältere Windows-Versionen:** `setup.bat` (Batch) – Nur als Fallback

**Warum setup.ps1 statt setup.bat?**
- ✅ Kürzer und wartbarer (299 vs. 744 Zeilen)
- ✅ Nutzt moderne .NET Crypto APIs
- ✅ Bessere Fehlerbehandlung (Try-Catch)
- ✅ Klarere Syntax (PowerShell vs. Batch)
- ✅ Gleiche Funktionalität wie setup.sh

Beide Skripte generieren:

- 15+ kryptographisch sichere Passwörter
- Ein RSA-2048 Keypair für JWT-Authentifizierung
- Eine vollständige `.env` Datei mit allen 10 Sektionen
- Eine Validierung über `scripts/validate_env.py`

### Methode 2 – Manuelle Einrichtung (nur wenn zwingend nötig)

```bash
cp .env.example .env
# ⚠️ 15+ Secrets müssen händisch nachgetragen werden – nur verwenden, wenn Setup-Skript nicht möglich ist!
```

### Validierung durchführen

```bash
python scripts/validate_env.py          # Pflichtvariablen prüfen
python scripts/validate_env.py --strict # Warnungen als Fehler behandeln
python scripts/validate_env.py --no-complexity   # Nur Mindestlänge erzwingen
python scripts/validate_env.py --docker-context off  # Docker-spezifische Checks überspringen
```

> ℹ️  Der Validator sucht automatisch nach `.env`, `.env.local` und `.env.database` (in dieser Reihenfolge). Bei Bedarf kannst du mit `--env-file path/to/custom.env` eine konkrete Datei prüfen.

### Docker starten

- Entwicklung (minimal):

  ```bash
  docker-compose -f docker-compose.simple.yml up -d
  ```

- Mit Firecrawl:

  ```bash
  docker-compose -f docker-compose.with-firecrawl.yml up -d
  ```

- Production-Parität:

  ```bash
  docker-compose -f docker-compose.production.yml up -d
  ```

---

## 🐳 Docker Compose Files Übersicht

Das Projekt bietet 3 produktionsreife Docker Compose Konfigurationen:

### docker-compose.simple.yml
**Anwendungsfall**: Minimale Entwicklungsumgebung
**Services**: Frontend, Backend, PostgreSQL, MinIO, Ollama (5 Services)
**Best für**: Schnelles Testen, Entwicklung, ressourcenbeschränkte Umgebungen
**Features**: Kein Firecrawl, keine GPU erforderlich, saubere Minimal-Stack

### docker-compose.with-firecrawl.yml
**Anwendungsfall**: Entwicklung mit erweitertem Web Scraping
**Services**: Alle simple.yml Services + Redis, Playwright, Firecrawl API (10 Services)
**Best für**: Testen von Web Scraping Features, Dokumentenverarbeitung mit Web-Quellen
**Features**: Firecrawl für bessere Web-Inhaltsextraktion

### docker-compose.production.yml
**Anwendungsfall**: Production Deployment
**Services**: Alle with-firecrawl.yml Services + Firecrawl Worker (11 Services)
**Best für**: Production Deployments, GPU-beschleunigte Inferenz
**Features**: GPU-Unterstützung für Ollama, optimierte PostgreSQL-Einstellungen, Production Healthchecks

> **Hinweis**: 7 veraltete Docker Compose Dateien wurden archiviert, um Verwirrung zu reduzieren. Siehe `archive/docker/README.md` für Details.

---

## 🧩 Struktur der `.env` Datei

Die konsolidierte `.env` enthält 10 Sektionen mit 60+ Variablen. Die folgenden Bereiche werden automatisch befüllt:

| Sektion | Umfang | Secrets |
| ------- | ------ | ------- |
| 1. Application Settings | 4 Variablen | – |
| 2. Database Configuration | 16 Variablen | `DATABASE_PASSWORD` |
| 3. Object Storage | 28 Variablen | `OBJECT_STORAGE_SECRET_KEY` |
| 4. AI Service | 58 Variablen | – |
| 5. Authentication & Security | 64 Variablen | `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`, `DEFAULT_ADMIN_PASSWORD` |
| 6. Processing Pipeline | 27 Variablen | – |
| 7. Web Scraping | 45 Variablen | `OPENAI_API_KEY` (optional) |
| 8. External API Keys | 19 Variablen | `YOUTUBE_API_KEY`, `CLOUDFLARE_TUNNEL_TOKEN` |
| 9. Docker Compose | 64 Variablen | n8n, pgAdmin, Firecrawl, Test-Credentials |
| 10. Security Reminders | Hinweise | – |

> **Hinweis:** Supabase- und R2-Variablen sind in der `.env` auskommentiert und deprecated. Verwende PostgreSQL + MinIO für Production-Deployments.

### Kritische Variablen (müssen gesetzt sein)

- `DATABASE_PASSWORD`
- `OBJECT_STORAGE_SECRET_KEY`
- `JWT_PRIVATE_KEY` & `JWT_PUBLIC_KEY`
- `DEFAULT_ADMIN_PASSWORD`
- `OLLAMA_URL`

Diese Werte werden durch die Setup-Skripte erzeugt und sollten nicht manuell geändert werden.

> **Deprecated:** `SUPABASE_*` und `R2_*` Variablen sind nicht mehr erforderlich. Verwende stattdessen `DATABASE_*` und `OBJECT_STORAGE_*` Variablen.

### Optionale Variablen (Warnungen bei fehlender Konfiguration)

- `YOUTUBE_API_KEY` → Google Cloud Console
- `CLOUDFLARE_TUNNEL_TOKEN` → Cloudflare Dashboard
- `OPENAI_API_KEY` → Nur erforderlich, wenn `FIRECRAWL_LLM_PROVIDER=openai`

### Docker-spezifische Standardwerte (nicht anpassen)

- `DATABASE_HOST=krai-postgres` (nicht `SUPABASE_URL`)
- `OBJECT_STORAGE_ENDPOINT=http://krai-minio:9000` (nicht `MINIO_ENDPOINT`)
- `OLLAMA_URL=http://krai-ollama:11434` (nicht `OLLAMA_BASE_URL`)

Für lokale Host-Verbindungen separate `.env.local` oder Overrides nutzen. Kopiere dazu
`.env.local.example` nach `.env.local` und setze dort `DATABASE_HOST`/
`POSTGRES_HOST`/`DATABASE_CONNECTION_URL` auf `localhost`, damit Host-Prozesse über
die veröffentlichten Ports mit den Docker-Containern sprechen.

> **Wichtig:** Diese Werte sind für Docker Compose optimiert. Für Host-Zugriff verwende `localhost` statt Service-Namen.

---

## 🌐 Zugängliche Dienste

| Service | URL | Benutzer | Credentials | Verfügbar in |
| ------- | --- | -------- | ----------- | ------------ |
| Frontend | http://localhost | – | – | Alle Compose-Dateien |
| Backend API | http://localhost:8000 | – | – | Alle Compose-Dateien |
| API Docs | http://localhost:8000/docs | – | – | Alle Compose-Dateien |
| Health Check | http://localhost:8000/health | – | – | Alle Compose-Dateien |
| MinIO Console | http://localhost:9001 | minioadmin | aus `.env` | Alle Compose-Dateien |
| Redis | localhost:6379 | – | – | with-firecrawl, production |
| Playwright | localhost:3000 | – | – | with-firecrawl, production |
| Firecrawl API | http://localhost:9002 | – | – | with-firecrawl, production |
| Ollama API | http://localhost:11434 | – | – | Alle Compose-Dateien |

> **Hinweis**: n8n und pgAdmin sind nur in archivierten Compose-Dateien verfügbar. Siehe `archive/docker/README.md`.

---

## 🛠️ Setup-Skripte im Detail

### setup.ps1 (Windows 10/11 - Empfohlen)

- Generiert 15+ sichere Passwörter mit .NET `RNGCryptoServiceProvider`
- Generiert RSA 2048-bit Schlüsselpaar mit .NET Crypto API
- Fallback zu OpenSSL wenn .NET APIs nicht verfügbar
- Erstellt vollständige `.env` mit allen 10 Sektionen
- Zeigt generierte Credentials strukturiert an
- Validiert `.env` nach Erstellung
- Warnt bei fehlenden optionalen Variablen
- **Vorteile:** Modern, wartbar, sicher, kurz (299 Zeilen)
- **Anforderungen:** PowerShell 5.0+ (in Windows 10/11 enthalten)

**Ausführung:**

```powershell
# Standard-Ausführung
./setup.ps1

# Mit Force-Flag (überschreibt .env ohne Nachfrage)
./setup.ps1 -Force
```

**Troubleshooting:**
- **Execution Policy blockiert:** `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- **OpenSSL nicht gefunden:** Installiere OpenSSL oder nutze PowerShell 7+
- **Skript nicht gefunden:** Nutze `./setup.ps1` (mit Backslash in PowerShell: `.\setup.ps1`)

### setup.sh (Linux/macOS)

- Passwörter per `openssl rand -base64`
- RSA-2048 Keypair für JWT
- Vollständige `.env` mit allen Sektionen
- Automatische Validierung via `scripts/validate_env.py`
- Hinweise auf fehlende optionale Variablen

### setup.bat (Windows - Legacy Fallback)

- Gleiche Funktionalität wie setup.ps1
- Nutzt PowerShell-Aufrufe für Passwort-Generierung
- RSA-Keys via PowerShell Crypto API oder OpenSSL
- **Nachteile:** Komplex (744 Zeilen), schwer zu debuggen, Batch-Syntax fehleranfällig
- **Nur verwenden wenn:** PowerShell 5.0+ nicht verfügbar (sehr alte Windows-Versionen)

**Ausführung:**

```cmd
REM Standard-Ausführung
setup.bat

REM Mit Force-Flag
set FORCE=1
setup.bat
```

### Sicherheitshinweise

- Secrets werden nur lokal erzeugt
- `.env` steht in `.gitignore` (niemals committen)
- Kopiere `.env` nur auf vertrauenswürdige Systeme

---

## ✅ Validierung & Healthchecks

### Automatische Validierung

```bash
python scripts/validate_env.py          # Pflichtvariablen prüfen
python scripts/validate_env.py --verbose
python scripts/validate_env.py --strict
```

Der Validator prüft u. a.:

- Vollständigkeit aller kritischen Variablen
- Passwortlängen & optional aktivierte Komplexitätsregeln (`PASSWORD_REQUIRE_*`, `PASSWORD_MIN_LENGTH`)
- Base64-Format der JWT-Keys
- Docker-Service-Namen (`krai-postgres`, `krai-minio`, `krai-ollama`) – nur im Docker-Kontext aktiv
- Optionale Variablen mit Warnungen
- Firecrawl API Key Pflicht nur, wenn `FIRECRAWL_REQUIRE_API_KEY=true` oder `FIRECRAWL_API_URL` auf eine externe Domain zeigt

Exit-Codes: `0` (OK), `1` (Warnungen), `2` (Fehler oder Warnungen in `--strict`).

### Service-Validierung nach dem Start

```bash
python scripts/verify_local_setup.py
python scripts/verify_local_setup.py --service postgresql
```

Der Service-Checker nutzt Healthchecks aus `docker-compose.*`:

- PostgreSQL → `pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"`
- MinIO → `wget -qO- http://localhost:9000/minio/health/live`
- Ollama → `curl -f http://localhost:11434/api/tags`
- Redis → `redis-cli PING`
- Frontend → `wget --spider http://localhost/`
- Backend → `curl -f http://localhost:8000/health`

---

## 🆘 Troubleshooting

### Häufige Probleme & Lösungen

1. **`.env` fehlt oder ist unvollständig**
   - Symptom: Container starten nicht, Fehler wie `DATABASE_PASSWORD not set`
   - Lösung: `./setup.sh` bzw. `setup.bat` ausführen oder `.env.example` kopieren
   - Validierung: `python scripts/validate_env.py`

2. **Port-Konflikte (5432, 9000, 11434, 8000)**
   - Symptom: "port already in use"
   - Lösung: `netstat -tulpn | grep :5432` (Linux) oder `netstat -ano | findstr :5432` (Windows)
   - Alternative: Ports in `docker-compose.*` anpassen

3. **Falsche Credentials**
   - Symptom: "Authentication failed"
   - Lösung: Docker-Hostnamen beibehalten (`krai-postgres`, `krai-minio`, `krai-ollama`)
   - Für Host-Zugriff separate `.env.local` nutzen

4. **GPU wird nicht erkannt**
   - Symptom: Ollama läuft nur auf CPU
   - Lösung: NVIDIA Container Toolkit installieren, `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`
   - Fallback: `USE_GPU=false`

5. **Out-of-Memory (OOM)**
   - Symptom: Container `OOMKilled`
   - Lösung: Kleinere Ollama-Modelle (`llama3.2:1b`), Docker Memory Limit erhöhen, Batch-Sizes reduzieren

6. **MinIO-Buckets fehlen**
   - Symptom: "Bucket not found"
   - Lösung: `python scripts/init_minio.py` oder manuell über http://localhost:9001

7. **Ollama-Modelle fehlen**
   - Symptom: "Model not found"
   - Lösung: `docker exec krai-ollama ollama pull nomic-embed-text:latest`
   - Überprüfen mit `docker exec krai-ollama ollama list`

8. **Vision-Model stürzt ab**
   - Symptom: CUDA Out-of-memory
   - Lösung: `DISABLE_VISION_PROCESSING=true`, `MAX_VISION_IMAGES=1`, kleineres Modell (`llava:7b`)

9. **Firecrawl startet nicht (Restart Loop)**
   - **Symptom:** Container `krai-firecrawl-api-prod` und `krai-playwright-prod` in Restart-Schleife
   - **Ursachen & Lösungen:**

     a) **Playwright Healthcheck schlägt fehl:**
        - Prüfen: `docker logs krai-playwright-prod --tail 20`
        - Lösung: Healthcheck muss `/pressure` Endpoint verwenden
        - Test: `curl http://localhost:3000/pressure` (sollte 200 zurückgeben)
        - Fix: `HEALTH=true` Environment Variable in Playwright Service setzen

     b) **Falsche Playwright URL:**
        - Prüfen: `docker exec krai-firecrawl-api-prod env | grep PLAYWRIGHT`
        - Problem: `PLAYWRIGHT_MICROSERVICE_URL` enthält `/scrape` Suffix
        - Lösung: URL muss `http://krai-playwright:3000` sein (ohne `/scrape`)

     c) **Firecrawl API Healthcheck fehlerhaft:**
        - Prüfen: `docker inspect krai-firecrawl-api-prod | grep -A 5 Healthcheck`
        - Problem: Endpoint `/api/v1/status` existiert nicht
        - Lösung: Healthcheck auf `/health` oder TCP-Check ändern

     d) **Ollama Modelle fehlen:**
        - Prüfen: `docker exec krai-ollama ollama list`
        - Lösung: Modelle pullen (siehe Punkt 7)

   - **Vollständige Diagnose:**

     ```bash
     # Container Status prüfen
     docker-compose -f docker-compose.with-firecrawl.yml ps

     # Logs aller Firecrawl Services
     docker-compose -f docker-compose.with-firecrawl.yml logs krai-playwright krai-firecrawl-api krai-firecrawl-worker

     # Playwright Health testen
     curl -v http://localhost:3000/pressure

     # Firecrawl API testen
     curl -v http://localhost:9002/health
     ```

   - **Reset-Prozedur:**

     ```bash
     # Services stoppen
     docker-compose -f docker-compose.with-firecrawl.yml down

     # .env Variablen prüfen
     grep -E "PLAYWRIGHT|FIRECRAWL" .env

     # Services neu starten
     docker-compose -f docker-compose.with-firecrawl.yml up -d krai-redis krai-playwright

     # Warten bis Playwright healthy ist
     docker-compose -f docker-compose.with-firecrawl.yml ps krai-playwright

     # Firecrawl Services starten
     docker-compose -f docker-compose.with-firecrawl.yml up -d krai-firecrawl-api krai-firecrawl-worker
     ```

10. **JWT-Authentifizierung schlägt fehl**
    - Symptom: "Invalid token"
    - Lösung: `JWT_PRIVATE_KEY` & `JWT_PUBLIC_KEY` prüfen, Base64-Format sicherstellen, bei Bedarf `./setup.sh`

11. **PowerShell-Skript wird nicht ausgeführt**
    - Symptom: "setup.ps1 cannot be loaded because running scripts is disabled"
    - Lösung: Execution Policy anpassen:
      ```powershell
      Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
      ```
    - Alternative: Batch-Skript verwenden: `setup.bat`
    - Dokumentation: <https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy>

12. **setup.bat schlägt fehl mit "RSA key generation failed"**
    - Symptom: Fehler bei RSA-Key-Generierung in setup.bat
    - Lösung: Nutze setup.ps1 statt setup.bat:
      ```powershell
      ./setup.ps1
      ```
    - Oder: Installiere OpenSSL und füge zu PATH hinzu
    - Grund: setup.bat ist komplexer und fehleranfälliger als setup.ps1

13. **"setup.ps1 not found" auf Windows**
    - Symptom: PowerShell findet setup.ps1 nicht
    - Lösung: Nutze `./setup.ps1` (oder `.\setup.ps1`) statt `setup.ps1`
    - Grund: PowerShell erfordert expliziten Pfad für lokale Skripte

### Diagnosebefehle

- `docker-compose ps`
- `docker-compose logs -f [service]`
- `docker stats`
- `docker inspect [container]`
- `python scripts/validate_env.py --verbose`
- `python scripts/verify_local_setup.py --verbose`

### Reset-Prozeduren

- **Soft Reset:** `docker-compose restart`
- **Hard Reset:** `docker-compose down && docker-compose up -d`
- **Full Reset (löscht Daten!):** `docker-compose down -v && docker-compose up -d --build`

---

## 🔍 Firecrawl Spezifische Diagnose

### Service-Abhängigkeiten

Firecrawl Stack hat folgende Abhängigkeiten:
```
krai-redis (healthy)
  ↓
krai-playwright (healthy)
  ↓
krai-firecrawl-api (healthy)
  ↓
krai-firecrawl-worker (started)
```

### Healthcheck-Endpoints

| Service | Endpoint | Erwartete Antwort |
|---------|----------|-------------------|
| Playwright | `http://localhost:3000/pressure` | HTTP 200 + JSON |
| Firecrawl API | `http://localhost:9002/health` | HTTP 200 |
| Redis | `redis-cli PING` | PONG |

### Häufige Fehlermeldungen

1. **"Error: connect ECONNREFUSED 127.0.0.1:3000"**
   - Ursache: Playwright Service nicht erreichbar
   - Lösung: Playwright Healthcheck korrigieren

2. **"Playwright service unhealthy"**
   - Ursache: `/pressure` Endpoint nicht verfügbar
   - Lösung: `HEALTH=true` Environment Variable setzen

3. **"Worker failed to start"**
   - Ursache: Ollama Service nicht verfügbar oder Modelle fehlen
   - Lösung: Ollama Modelle pullen (siehe Punkt 7)

### Performance-Tuning

```bash
# Playwright Memory-Limit erhöhen
PLAYWRIGHT_MAX_CONCURRENT_SESSIONS=5  # Reduzieren bei wenig RAM

# Firecrawl Worker-Anzahl anpassen
FIRECRAWL_NUM_WORKERS=2  # Reduzieren bei wenig CPU

# Firecrawl Concurrency reduzieren
FIRECRAWL_MAX_CONCURRENCY=2  # Reduzieren bei Instabilität
```

---

## 📚 Weiterführende Links

- [README.md](README.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [docs/ENVIRONMENT_VARIABLES_REFERENCE.md](docs/ENVIRONMENT_VARIABLES_REFERENCE.md)
- [docs/DOCKER_SETUP_GUIDE.md](docs/DOCKER_SETUP_GUIDE.md)

### Hilfreiche Skripte

- `setup.sh` – Linux/macOS Setup (Bash)
- `setup.ps1` – Windows 10/11 Setup (PowerShell) – **Empfohlen**
- `setup.bat` – Windows Legacy Setup (Batch) – Nur als Fallback
- `scripts/validate_env.py`
- `scripts/verify_local_setup.py`
- `scripts/init_minio.py`

---

## 📚 Archivierte Compose-Dateien

7 Docker Compose Dateien wurden archiviert, um das Projekt zu vereinfachen:

- `docker-compose.yml` - Legacy-Standard mit n8n, pgAdmin, Laravel
- `docker-compose.test.yml` - Testumgebung mit isolierten Services
- `docker-compose.production-final.yml` - Produktions-Duplikat
- `docker-compose.production-complete.yml` - Produktions-Duplikat mit Firecrawl
- `docker-compose.prod.yml` - Enterprise-Setup mit erweiterten Features
- `docker-compose.infrastructure.yml` - Infrastructure-only (keine API/Frontend)
- `docker-compose-ollama-tunnel.yml` - Cloudflare Tunnel für Ollama

Siehe `archive/docker/README.md` für Details und Migrationsanleitungen.
