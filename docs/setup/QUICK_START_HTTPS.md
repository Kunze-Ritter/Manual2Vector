# 🚀 Quick Start: n8n mit HTTPS für Microsoft Teams

Schnellstart-Anleitung um n8n mit **Cloudflare Tunnel** für Microsoft Teams Chat-Trigger zu nutzen.

## ⚡ Automatisches Setup (3 Minuten)

```powershell
# Führe das Setup-Script aus
.\scripts\setup-cloudflare-tunnel.ps1
```

Das Script führt dich durch:
1. ✅ Cloudflare Tunnel erstellen (mit Anleitung)
2. ✅ Token und URL in .env eintragen
3. ✅ Container starten
4. ✅ Fertig - n8n über HTTPS erreichbar!

**Ergebnis**: n8n läuft auf `https://deine-subdomain.trycloudflare.com`

**Vorteile**:
- ✅ SSL-Zertifikat automatisch vertrauenswürdig (keine Installation nötig!)
- ✅ Microsoft Teams funktioniert sofort
- ✅ Von überall erreichbar

---

## 📱 Microsoft Teams einrichten

### 1. Webhook in n8n erstellen

1. Öffne n8n: `https://deine-subdomain.trycloudflare.com`
2. Erstelle neuen Workflow
3. Füge "Webhook" Node hinzu
4. Wähle HTTP Method (meist POST)
5. Kopiere die Webhook-URL: `https://deine-subdomain.trycloudflare.com/webhook/...`

### 2. In Microsoft Teams konfigurieren

**Incoming Webhook (einfach)**:
1. Gehe zu deinem Team → ⚙️ Einstellungen
2. Connectors → Incoming Webhook
3. Füge deine n8n-Webhook-URL ein
4. Teste den Webhook → Funktioniert sofort! ✅

**Bot Framework (erweitert)**:
1. Registriere Bot im [Azure Portal](https://portal.azure.com)
2. Nutze n8n's "Microsoft Teams" Node
3. Konfiguriere Bot Messaging Endpoint mit deiner Webhook-URL

✅ **Vorteil**: Cloudflare-Zertifikat ist automatisch vertrauenswürdig!

---

## 🔍 Troubleshooting

### Tunnel verbindet nicht
```powershell
# Prüfe Tunnel-Logs
docker logs krai-cloudflare-tunnel -f

# Häufige Ursachen:
# - Token falsch eingegeben
# - Public Hostname nicht konfiguriert
# - Service-URL nicht korrekt: muss 'krai-n8n-chat-agent:5678' sein
```

### 502 Bad Gateway
```powershell
# n8n läuft nicht oder startet noch
docker logs krai-n8n-chat-agent -f

# Container neu starten
docker-compose restart
```

### Webhook erhält keine Daten
```powershell
# Prüfe n8n-Logs
docker logs krai-n8n-chat-agent -f

# Prüfe Tunnel-Logs
docker logs krai-cloudflare-tunnel -f

# Teste Webhook manuell
Invoke-WebRequest -Uri "https://deine-url/webhook/test" -Method POST
```

### "Invalid credentials" beim Login
```powershell
# Standard-Login:
# Benutzer: admin
# Passwort: krai_chat_agent_2024

# Passwort ändern in docker-compose.yml (available in archive/docker/docker-compose.yml):
# N8N_BASIC_AUTH_PASSWORD=dein_passwort
```

---

## 📚 Ausführliche Anleitungen

- **Cloudflare Tunnel**: `docs/setup/N8N_CLOUDFLARE_TUNNEL_SETUP.md`
- **n8n Workflows**: `docs/n8n/N8N_AI_AGENT_MODERN_SETUP.md`
- **Microsoft Teams Bot**: `docs/n8n/KRAI_AGENT_WORKFLOW_GUIDE.md`

---

## 🎯 Nächste Schritte

1. ✅ Cloudflare Tunnel läuft
2. 📱 Erstelle einen Test-Workflow in n8n
3. 🔗 Verbinde Microsoft Teams mit Webhook-URL
4. 🤖 Baue deinen Chat-Agent mit LangChain
5. 💾 Nutze Supabase für Konversations-Speicher

**Beispiel-Workflows** findest du in `n8n/workflows/`

---

## 🔐 Warum Cloudflare Tunnel?

- ✅ **SSL-Zertifikat automatisch vertrauenswürdig** - Keine manuelle Installation!
- ✅ **Microsoft Teams funktioniert sofort** - Keine Zertifikat-Fehler
- ✅ **Von überall erreichbar** - Lokal, Büro, mobil
- ✅ **Kostenlos** - Mit *.trycloudflare.com Subdomain
- ✅ **Sicher** - Cloudflare Zero Trust Protection

**Alternative**: Für rein lokale Entwicklung siehe `docs/setup/N8N_HTTPS_LOCAL_SETUP.md`

**Support**: Siehe `docs/troubleshooting/` für weitere Hilfe.
