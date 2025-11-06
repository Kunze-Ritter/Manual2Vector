# Docker Setup für KRAI Engine

## Schnellstart für andere PCs

### 🚀 Methode 1: Automatisches Setup (empfohlen)

**Linux/macOS:**
```bash
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

Das Skript generiert automatisch sichere Passwörter und erstellt die `.env` Datei!

### 📋 Methode 2: Manuelle Einrichtung

1. **Environment Datei kopieren:**

```bash
cp .env.example .env
```

2. **Passwörter anpassen** (optional - die Standardwerte funktionieren für Docker)

3. **Docker starten:**

```bash
docker-compose -f docker-compose.simple.yml up --build -d
```

## Zugängliche Dienste

- **KRAI Engine API**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Frontend**: `http://localhost:80`
- **MinIO Console**: `http://localhost:9001` (minioadmin/minioadmin123)

## Environment Variables

Die `.env` Datei enthält alle notwendigen Konfigurationen für Docker:

- **DATABASE_HOST=krai-postgres** (intern für Docker)
- **OBJECT_STORAGE_ENDPOINT=`http://krai-minio:9000`** (intern für Docker)
- **AI_SERVICE_URL=`http://krai-ollama:11434`** (intern für Docker)

Diese Werte sind für Docker-Container optimiert und sollten nicht geändert werden.

## 🔐 Setup-Skripte

### setup.sh (Linux/macOS)
- Generiert 25-stellige, sichere Passwörter mit OpenSSL
- Erstellt `.env` Datei automatisch
- Zeigt generierte Zugangsdaten an

### setup.bat (Windows)
- Generiert sichere Passwörter mit PowerShell
- Erstellt `.env` Datei automatisch
- Benutzerfreundliche Ausgabe

**Sicherheit:** Die Passwörter werden kryptographisch sicher generiert und nur lokal gespeichert.

## Fertig! 🎉

Die Anwendung läuft mit allen Services:

- ✅ PostgreSQL (krai-postgres)
- ✅ MinIO Object Storage (krai-minio)
- ✅ Ollama AI Service (krai-ollama)
- ✅ KRAI Engine API (krai-engine)
- ✅ Frontend (krai-frontend)
