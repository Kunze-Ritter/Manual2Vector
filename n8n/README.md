# N8N Integration

This folder contains all n8n automation workflows and credentials for KRAI.

## 📁 Structure

```
n8n/
├─ workflows/           # n8n workflow JSON files
├─ credentials/         # Credential templates (no secrets!)
├─ start-n8n-chat-agent.ps1  # Startup script
└─ README.md           # This file
```

## 📚 Documentation

See `docs/n8n/` for detailed setup guides:

- **N8N_AI_AGENT_MODERN_SETUP.md** - Modern AI agent setup
- **N8N_CHAT_AGENT_SETUP.md** - Chat agent configuration
- **N8N_LANGCHAIN_AI_AGENT_SETUP.md** - LangChain integration
- **N8N_POSTGRES_MEMORY_INTEGRATION.md** - Database memory integration

## 🔐 Database Access

n8n has a dedicated database user with access to `krai_agent.memory`:

```
User: n8n_user
Connection: See credentials.txt (not in git)
Migration: database/migrations/create_n8n_user.sql
```

## 🚀 Quick Start

1. **Install n8n**: `npm install -g n8n`
2. **Start n8n**: `n8n start`
3. **Import workflows**: Import JSON files from `workflows/`
4. **Configure credentials**: Use connection string from `credentials.txt`

## 🔗 Related

- Main docs: `../docs/n8n/`
- Database setup: `../database/migrations/N8N_USER_SETUP.md`
- Credentials: `../credentials.txt` (not in git)
