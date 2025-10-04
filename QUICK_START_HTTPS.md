# 🚀 Quick Start: n8n mit HTTPS für Microsoft Teams

Schnellstart-Anleitung um n8n mit **lokalem HTTPS** für Microsoft Teams Chat-Trigger zu nutzen.

## ⚡ Automatisches Setup (2 Minuten)

```powershell
# Führe das Setup-Script aus
.\scripts\setup-n8n-https.ps1
```

Das Script:
1. ✅ Erstellt SSL-Zertifikat für localhost
2. ✅ Installiert Zertifikat im Windows Trust Store (optional)
3. ✅ Startet n8n mit nginx SSL-Proxy
4. ✅ Testet die Verbindung

**Ergebnis**: n8n läuft auf `https://localhost`

---

## 📱 Microsoft Teams einrichten

### 1. Webhook in n8n erstellen

1. Öffne n8n: `https://localhost`
2. Erstelle neuen Workflow
3. Füge "Webhook" Node hinzu
4. Wähle HTTP Method (meist POST)
5. Kopiere die Webhook-URL: `https://localhost/webhook/...`

### 2. In Microsoft Teams konfigurieren

**Incoming Webhook (einfach)**:
1. Gehe zu deinem Team → ⚙️ Einstellungen
2. Connectors → Incoming Webhook
3. Füge deine n8n-Webhook-URL ein: `https://localhost/webhook/...`
4. Teste den Webhook

**Bot Framework (erweitert)**:
1. Registriere Bot im [Azure Portal](https://portal.azure.com)
2. Nutze n8n's "Microsoft Teams" Node
3. Konfiguriere Bot Messaging Endpoint: `https://localhost/webhook/teams`

⚠️ **Wichtig**: Das SSL-Zertifikat muss im Windows Trust Store installiert sein!

---

## 🔍 Troubleshooting

### Browser zeigt SSL-Warnung
```powershell
# Zertifikat ist nicht installiert
# Lösung: Führe das Setup-Script erneut aus und installiere das Zertifikat
.\scripts\setup-n8n-https.ps1
```

### Microsoft Teams akzeptiert Webhook nicht
```powershell
# Prüfe ob Zertifikat im Trust Store ist
certutil -store -user Root | Select-String "localhost"

# Installiere Zertifikat manuell:
# Rechtsklick auf nginx/ssl/localhost.crt -> Zertifikat installieren
# Speicherort: "Vertrauenswürdige Stammzertifizierungsstellen"
```

### Webhook erhält keine Daten
```powershell
# Prüfe n8n-Logs
docker logs krai-n8n-chat-agent -f

# Prüfe nginx-Logs
docker logs krai-nginx-ssl -f
```

### 502 Bad Gateway
```powershell
# Container neu starten
docker-compose restart
```

### Port 443 bereits belegt
```powershell
# Prüfe welcher Prozess Port 443 nutzt
netstat -ano | Select-String ":443"

# Stoppe IIS oder anderen Webserver der Port 443 nutzt
```

---

## 📚 Ausführliche Anleitungen

- **HTTPS Setup**: `docs/setup/N8N_HTTPS_LOCAL_SETUP.md`
- **n8n Workflows**: `docs/n8n/N8N_AI_AGENT_MODERN_SETUP.md`
- **Microsoft Teams Bot**: `docs/n8n/KRAI_AGENT_WORKFLOW_GUIDE.md`

---

## 🎯 Nächste Schritte

1. ✅ HTTPS funktioniert auf `https://localhost`
2. 📱 Erstelle einen Test-Workflow in n8n
3. 🔗 Verbinde Microsoft Teams mit Webhook-URL
4. 🤖 Baue deinen Chat-Agent mit LangChain
5. 💾 Nutze Supabase für Konversations-Speicher

**Beispiel-Workflows** findest du in `n8n/workflows/`

---

## 🔐 Wichtige Hinweise

- **Zertifikat installieren**: Für Microsoft Teams zwingend erforderlich!
- **Firewall**: Stelle sicher, dass Port 443 offen ist
- **Produktion**: Für öffentliche Server nutze Let's Encrypt statt selbst-signiertem Zertifikat

**Support**: Siehe `docs/troubleshooting/` oder `docs/setup/N8N_HTTPS_LOCAL_SETUP.md` für Details.
