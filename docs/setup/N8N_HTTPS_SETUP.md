# N8N HTTPS Setup für Microsoft Teams

Diese Anleitung zeigt, wie du n8n mit HTTPS lokal laufen lässt, um Microsoft Teams als Chat-Trigger zu nutzen.

## 🎯 Ziel

Microsoft Teams erfordert HTTPS für Webhooks. Mit **Cloudflare Tunnel** kannst du deine lokale n8n-Instanz sicher über HTTPS von außen erreichbar machen.

## 🛠️ Voraussetzungen

- Docker und Docker Compose installiert
- Cloudflare Account (kostenlos)
- Laufende n8n-Instanz

## 📋 Setup-Schritte

### Schritt 1: Cloudflare Tunnel erstellen

1. **Gehe zu Cloudflare Zero Trust Dashboard**
   - Öffne: https://one.dash.cloudflare.com/
   - Melde dich mit deinem Cloudflare-Account an
   - Wähle "Zero Trust" aus dem Menü

2. **Erstelle einen neuen Tunnel**
   - Klicke auf "Access" → "Tunnels"
   - Klicke auf "Create a tunnel"
   - Wähle "Cloudflared" als Typ
   - Gib einen Namen ein: `krai-n8n-tunnel`

3. **Kopiere das Tunnel-Token**
   - Nach dem Erstellen des Tunnels erhältst du einen Token
   - Dieser sieht ungefähr so aus: `eyJhIjoiXXXXXXXXXXXXXXXXXXXX...`
   - Kopiere diesen Token

4. **Konfiguriere die Public Hostname**
   - In den Tunnel-Einstellungen, füge eine Public Hostname hinzu:
     - **Subdomain**: Wähle einen Namen (z.B. `krai-n8n`)
     - **Domain**: Wähle eine deiner Cloudflare-Domains ODER nutze eine kostenlose `trycloudflare.com` Subdomain
     - **Type**: HTTP
     - **URL**: `krai-n8n-chat-agent:5678` (der Docker-Container-Name)

### Schritt 2: .env-Datei konfigurieren

Öffne die `.env`-Datei und trage deine Tunnel-Informationen ein:

```env
# ===========================================
# N8N HTTPS CONFIGURATION (for Microsoft Teams)
# ===========================================
# Dein Cloudflare Tunnel Token
CLOUDFLARE_TUNNEL_TOKEN=dein_tunnel_token_hier

# Deine Tunnel-URL (ohne https://)
N8N_HOST=krai-n8n.trycloudflare.com
N8N_PROTOCOL=https
WEBHOOK_URL=https://krai-n8n.trycloudflare.com/
```

**Beispiel:**
```env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiZjg5MjM0NTY3ODkwYWJjZGVmIiwidCI6IjEyMzQ1Njc4OTBhYmNkZWYiLCJzIjoiWVhKaFlXNWpNRGd6TkRVMk56ZzVNREV5In0=
N8N_HOST=krai-n8n.trycloudflare.com
N8N_PROTOCOL=https
WEBHOOK_URL=https://krai-n8n.trycloudflare.com/
```

### Schritt 3: Container neu starten

```powershell
# Stoppe die aktuellen Container
docker-compose down

# Starte die Container neu mit HTTPS-Konfiguration
docker-compose up -d
```

### Schritt 4: Verbindung testen

1. **Öffne deinen Browser**
   - Gehe zu: `https://krai-n8n.trycloudflare.com` (deine Tunnel-URL)
   - Du solltest die n8n-Login-Seite sehen

2. **Melde dich an**
   - Benutzername: `admin`
   - Passwort: `krai_chat_agent_2024`

3. **Teste einen Webhook**
   - Erstelle einen Test-Workflow mit einem Webhook-Trigger
   - Die Webhook-URL sollte jetzt mit `https://` beginnen

## 🔧 Alternative: ngrok (schnelle temporäre Lösung)

Falls du keine Cloudflare-Domain hast, kannst du auch ngrok nutzen:

### ngrok Setup (ohne Docker-Änderungen)

1. **Installiere ngrok**
   ```powershell
   # Mit Chocolatey
   choco install ngrok
   
   # Oder lade es von https://ngrok.com/download herunter
   ```

2. **Starte n8n normal**
   ```powershell
   docker-compose up -d
   ```

3. **Starte ngrok**
   ```powershell
   ngrok http 5678
   ```

4. **Notiere die HTTPS-URL**
   - ngrok zeigt dir eine URL wie: `https://xxxx-xx-xx-xxx-xxx.ngrok-free.app`
   - Diese URL kannst du in Microsoft Teams nutzen

### Nachteil von ngrok Free

- URL ändert sich bei jedem Neustart
- Limitierte Anzahl von Anfragen
- Cloudflare Tunnel ist stabiler für dauerhafte Nutzung

## 🔐 Sicherheit

- ✅ Basic Auth ist aktiviert (admin/krai_chat_agent_2024)
- ✅ HTTPS verschlüsselt die Verbindung
- ⚠️ Ändere das Passwort in `.env` → `N8N_BASIC_AUTH_PASSWORD`
- ⚠️ Nutze starke Passwörter für Produktion

## 📱 Microsoft Teams Integration

### Webhook in Teams nutzen

1. **Öffne n8n** über deine HTTPS-URL
2. **Erstelle einen Workflow** mit einem Webhook-Trigger
3. **Kopiere die Webhook-URL** (beginnt mit `https://`)
4. **In Microsoft Teams**:
   - Gehe zu deinem Team → Connectors
   - Wähle "Incoming Webhook"
   - Füge deine n8n-Webhook-URL ein

### Bot Framework (erweitert)

Für einen vollständigen Teams-Bot:
- Nutze den Microsoft Bot Framework Connector in n8n
- Registriere deinen Bot im Azure Portal
- Konfiguriere die Messaging-Endpoint mit deiner HTTPS-URL

## 🐛 Troubleshooting

### Tunnel verbindet nicht

1. **Token überprüfen**
   ```powershell
   docker logs krai-cloudflare-tunnel
   ```
   - Der Token sollte korrekt in der `.env` sein

2. **Cloudflare Dashboard prüfen**
   - Ist der Tunnel im Dashboard als "Healthy" markiert?
   - Ist die Public Hostname korrekt konfiguriert?

### 502 Bad Gateway

- n8n-Container läuft nicht:
  ```powershell
  docker ps | Select-String n8n
  docker logs krai-n8n-chat-agent
  ```

### Webhooks funktionieren nicht

- Überprüfe `WEBHOOK_URL` in `.env`
- Diese muss mit deiner Cloudflare Tunnel-URL übereinstimmen

## 📚 Weitere Ressourcen

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [n8n Webhook Docs](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [Microsoft Teams Bot Framework](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/)

## ✅ Checkliste

- [ ] Cloudflare Tunnel erstellt
- [ ] Token in `.env` eingetragen
- [ ] `N8N_HOST`, `N8N_PROTOCOL`, `WEBHOOK_URL` konfiguriert
- [ ] Container neu gestartet
- [ ] HTTPS-Verbindung erfolgreich getestet
- [ ] Webhook in Microsoft Teams hinzugefügt
- [ ] Passwort geändert (empfohlen)

---

**Tipp**: Für Entwicklung reicht ein temporärer ngrok-Tunnel. Für produktiven Einsatz nutze Cloudflare Tunnel mit einer eigenen Domain.
