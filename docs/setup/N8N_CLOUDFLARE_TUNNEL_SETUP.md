# N8N mit Cloudflare Tunnel Setup

Vollständige Anleitung zur Einrichtung von n8n mit Cloudflare Tunnel für HTTPS-Zugriff und Microsoft Teams Integration.

## 🎯 Warum Cloudflare Tunnel?

**Vorteile**:
- ✅ **SSL-Zertifikat automatisch vertrauenswürdig** - Keine manuelle Installation
- ✅ **Microsoft Teams funktioniert sofort** - Keine Zertifikat-Probleme
- ✅ **Von überall erreichbar** - Lokal, remote, mobil
- ✅ **Kostenlos** - Mit `*.trycloudflare.com` Subdomain
- ✅ **Sicher** - Cloudflare Zero Trust Protection
- ✅ **Einfach** - Keine Port-Weiterleitung oder Firewall-Konfiguration

## ⚡ Automatisches Setup (3 Minuten)

```powershell
# Führe das interaktive Setup-Script aus
.\scripts\setup-cloudflare-tunnel.ps1
```

Das Script:
1. Zeigt dir die Anleitung zum Tunnel-Erstellen
2. Fragt nach deinem Token
3. Fragt nach deiner URL
4. Aktualisiert die `.env` automatisch
5. Startet alle Container

**→ Fertig! n8n läuft auf deiner HTTPS-URL**

---

## 📋 Manuelle Schritte

Falls du das Setup manuell durchführen möchtest:

### Schritt 1: Cloudflare Zero Trust Account

1. Gehe zu: https://one.dash.cloudflare.com/
2. Erstelle einen (kostenlosen) Cloudflare-Account, falls noch nicht vorhanden
3. Navigiere zu **"Zero Trust"**

### Schritt 2: Tunnel erstellen

1. **Im Cloudflare Dashboard**:
   - Klicke auf **"Access"** → **"Tunnels"**
   - Klicke auf **"Create a tunnel"**

2. **Tunnel-Typ wählen**:
   - Wähle **"Cloudflared"**
   - Klicke **"Next"**

3. **Tunnel benennen**:
   - Name: `krai-n8n` (oder beliebig)
   - Klicke **"Save tunnel"**

4. **Token kopieren**:
   - Du erhältst ein Token wie: `eyJhIjoiXXXXXXXXXXXX...`
   - **Kopiere dieses Token** → Du brauchst es gleich!

### Schritt 3: Public Hostname konfigurieren

1. **Im Tunnel-Setup**, unter **"Public Hostnames"**:
   - Klicke **"Add a public hostname"**

2. **Konfiguration**:
   - **Subdomain**: Wähle einen Namen (z.B. `krai-n8n`)
   - **Domain**: 
     - Wenn du eine eigene Domain bei Cloudflare hast → Wähle diese
     - Sonst → Wähle `*.trycloudflare.com` (kostenlos)
   - **Path**: Leer lassen
   - **Type**: `HTTP`
   - **URL**: `krai-n8n-chat-agent:5678`

3. **Speichern**

**Deine URL ist jetzt**: `https://krai-n8n.trycloudflare.com` (oder deine eigene Domain)

### Schritt 4: Token in .env eintragen

Öffne die `.env` Datei und trage ein:

```env
# Dein Tunnel Token (von Schritt 2)
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiXXXXXXXXXXXX...

# Deine öffentliche URL (ohne https://)
N8N_HOST=krai-n8n.trycloudflare.com

# Webhook URL
WEBHOOK_URL=https://krai-n8n.trycloudflare.com/
```

### Schritt 5: Container starten

```powershell
# Stoppe alte Container
docker-compose down

# Starte mit Cloudflare Tunnel
docker-compose up -d

# Prüfe Status
docker-compose ps
```

### Schritt 6: Testen

1. **Öffne Browser**: `https://krai-n8n.trycloudflare.com`
2. **Login**: `admin` / `krai_chat_agent_2024`
3. **Keine SSL-Warnung** → Alles funktioniert! ✅

---

## 🏗️ Architektur

```
[Microsoft Teams]
       ↓ HTTPS
[https://krai-n8n.trycloudflare.com]
       ↓ Cloudflare Tunnel
   [cloudflared Container]
       ↓ HTTP (intern)
   [n8n Container :5678]
```

**Wichtig**: Die Verbindung ist von außen bis Cloudflare verschlüsselt (HTTPS). Intern zwischen cloudflared und n8n läuft HTTP, was aber sicher ist, da es innerhalb des Docker-Netzwerks bleibt.

---

## 📱 Microsoft Teams Integration

### 1. Webhook in n8n erstellen

1. Öffne n8n: `https://krai-n8n.trycloudflare.com`
2. Erstelle neuen Workflow
3. Füge **"Webhook"** Node hinzu
4. Konfiguration:
   - **HTTP Method**: POST
   - **Path**: `teams-webhook` (oder beliebig)
5. Kopiere die Webhook-URL: `https://krai-n8n.trycloudflare.com/webhook/teams-webhook`

### 2. Microsoft Teams konfigurieren

**Incoming Webhook**:
1. Öffne Microsoft Teams
2. Gehe zu deinem Team → **"Connectors"**
3. Suche **"Incoming Webhook"**
4. Konfigurieren:
   - Name: `KRAI n8n Bot`
   - Webhook-URL: `https://krai-n8n.trycloudflare.com/webhook/teams-webhook`
5. **Speichern**

**Testen**:
- Sende eine Test-Nachricht von Teams
- n8n sollte die Nachricht empfangen ✅

### 3. Bot Framework (Erweitert)

Für einen vollständigen Teams-Bot:

1. **Registriere Bot im Azure Portal**:
   - https://portal.azure.com
   - Erstelle **Bot Channels Registration**

2. **In n8n**:
   - Nutze **"Microsoft Teams Trigger"** Node
   - Trage App ID und Secret ein

3. **Bot Messaging Endpoint**:
   - `https://krai-n8n.trycloudflare.com/webhook/teams`

---

## 🔐 Sicherheit

### Basic Authentication

n8n ist durch Basic Auth geschützt:
- **Benutzer**: `admin`
- **Passwort**: `krai_chat_agent_2024`

**Passwort ändern** in `docker-compose.yml` (available in `archive/docker/docker-compose.yml`):
```yaml
- N8N_BASIC_AUTH_PASSWORD=dein_sicheres_passwort
```

### Webhook-Authentication

Für sensible Webhooks nutze n8n's eingebaute Authentifizierung:
1. Im Webhook-Node → **"Authentication"** aktivieren
2. Wähle Method (Header Auth, Basic Auth, etc.)
3. Teams muss dann entsprechende Credentials senden

### Cloudflare Zero Trust

Optional kannst du zusätzlich Cloudflare Access aktivieren:
1. Im Cloudflare Dashboard → **"Access"** → **"Applications"**
2. Erstelle Policy für deine URL
3. Nur bestimmte Email-Adressen erlauben

---

## 🐛 Troubleshooting

### Tunnel verbindet nicht

**Symptom**: Container läuft, aber URL nicht erreichbar

**Debug**:
```powershell
# Prüfe Tunnel-Logs
docker logs krai-cloudflare-tunnel -f

# Sollte zeigen: "Connection established"
```

**Häufige Ursachen**:
1. **Token falsch**: Prüfe in `.env`, muss mit `eyJ` beginnen
2. **Public Hostname nicht konfiguriert**: Im Cloudflare Dashboard prüfen
3. **Service-URL falsch**: Muss `krai-n8n-chat-agent:5678` sein (Container-Name!)

### 502 Bad Gateway

**Symptom**: Tunnel erreichbar, aber 502 Fehler

**Ursache**: n8n-Container läuft nicht

**Lösung**:
```powershell
# Prüfe n8n-Status
docker ps | Select-String n8n

# Prüfe n8n-Logs
docker logs krai-n8n-chat-agent -f

# Container neu starten
docker-compose restart n8n
```

### Webhook erhält keine Daten

**Debug-Schritte**:
```powershell
# 1. Teste Webhook manuell
Invoke-WebRequest -Uri "https://krai-n8n.trycloudflare.com/webhook/test" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"test": "data"}'

# 2. Prüfe n8n-Logs
docker logs krai-n8n-chat-agent -f

# 3. Prüfe ob Workflow aktiv ist
# In n8n → Workflow muss "Active" sein!
```

### Microsoft Teams lehnt Webhook ab

**Symptom**: "URL ungültig" oder "Verbindung fehlgeschlagen"

**Prüfung**:
1. ✅ URL beginnt mit `https://`
2. ✅ URL ist öffentlich erreichbar (im Browser testen)
3. ✅ n8n-Webhook ist aktiv
4. ✅ Webhook-Path ist korrekt

**Test**:
```powershell
# Öffne URL im Browser
Start-Process "https://krai-n8n.trycloudflare.com"

# Sollte n8n-Login zeigen (kein SSL-Fehler!)
```

### Tunnel-URL ändert sich

**Bei kostenlosen trycloudflare.com URLs**:
- URL kann sich nach einiger Zeit ändern
- Für permanente URL: Nutze eigene Domain bei Cloudflare

**Mit eigener Domain**:
1. Domain bei Cloudflare registrieren/übertragen
2. Im Tunnel-Setup eigene Domain wählen
3. URL bleibt permanent gleich

---

## 📝 Nützliche Befehle

```powershell
# Container-Status
docker-compose ps

# Logs anzeigen
docker logs krai-n8n-chat-agent -f
docker logs krai-cloudflare-tunnel -f

# Container neu starten
docker-compose restart

# Container stoppen
docker-compose down

# Container neu bauen
docker-compose up -d --force-recreate

# Tunnel-Status im Cloudflare Dashboard prüfen
# → https://one.dash.cloudflare.com/ → Access → Tunnels
```

---

## 🔄 Token erneuern

Falls du den Token ändern musst:

1. **Neuen Tunnel erstellen** oder **Token regenerieren** im Cloudflare Dashboard
2. **Token in .env aktualisieren**:
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=neuer_token
   ```
3. **Container neu starten**:
   ```powershell
   docker-compose restart cloudflared
   ```

---

## 🌐 Eigene Domain nutzen

### Voraussetzung
- Domain bei Cloudflare registriert oder DNS auf Cloudflare zeigen

### Setup
1. **Im Tunnel-Setup** (Public Hostname):
   - Domain: Wähle deine eigene Domain
   - Subdomain: `n8n` (oder beliebig)
   - Ergebnis: `https://n8n.deine-domain.de`

2. **In .env**:
   ```env
   N8N_HOST=n8n.deine-domain.de
   WEBHOOK_URL=https://n8n.deine-domain.de/
   ```

3. **Container neu starten**:
   ```powershell
   docker-compose restart
   ```

**Vorteile**:
- Permanente URL
- Professioneller
- Mehr Kontrolle

---

## 💡 Best Practices

### Produktion

1. **Starkes Passwort** für n8n:
   ```yaml
   - N8N_BASIC_AUTH_PASSWORD=sehr_sicheres_passwort_hier
   ```

2. **Webhook-Authentication** aktivieren in n8n

3. **Cloudflare Access** für zusätzliche Sicherheit:
   - Nur bestimmte Email-Adressen erlauben
   - 2FA erzwingen

4. **Eigene Domain** nutzen statt trycloudflare.com

### Monitoring

```powershell
# Tunnel-Status überwachen
docker logs krai-cloudflare-tunnel --tail 50

# n8n-Status überwachen
docker logs krai-n8n-chat-agent --tail 50

# Cloudflare Dashboard
# → Analytics für Traffic-Überwachung
```

---

## 🆚 Vergleich: Cloudflare Tunnel vs. Lokales HTTPS

| Feature | Cloudflare Tunnel | Lokales HTTPS |
|---------|------------------|---------------|
| SSL-Zertifikat | ✅ Automatisch vertrauenswürdig | ❌ Selbst-signiert, muss installiert werden |
| Microsoft Teams | ✅ Funktioniert sofort | ❌ Nur mit Zertifikat-Installation |
| Erreichbarkeit | ✅ Von überall | ❌ Nur lokal (localhost) |
| Setup | ⚡ 3 Minuten | ⏱️ 5-10 Minuten |
| Kosten | ✅ Kostenlos | ✅ Kostenlos |
| Externe Abhängigkeit | Cloudflare | Keine |

**Empfehlung**: Für Microsoft Teams → **Cloudflare Tunnel**

---

## 📚 Weitere Ressourcen

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [n8n Documentation](https://docs.n8n.io/)
- [Microsoft Teams Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/)
- [n8n Microsoft Teams Node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.microsoftteams/)

---

## ✅ Checkliste

Setup erfolgreich, wenn:

- [ ] Cloudflare Tunnel erstellt
- [ ] Token in `.env` eingetragen
- [ ] `N8N_HOST` und `WEBHOOK_URL` konfiguriert
- [ ] Container laufen (`docker-compose ps`)
- [ ] URL im Browser erreichbar (ohne SSL-Warnung)
- [ ] n8n-Login funktioniert
- [ ] Webhook in n8n erstellt
- [ ] Microsoft Teams Webhook konfiguriert
- [ ] Test-Nachricht von Teams empfangen

---

**Hilfe benötigt?** Siehe `docs/troubleshooting/` oder öffne ein Issue im Repository.
