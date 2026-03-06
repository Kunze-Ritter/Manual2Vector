# 🚀 KRAI - Knowledge Retrieval and Intelligence

Advanced Multimodal AI Document Processing Pipeline with Local-First Architecture and Vector Search

## ⚡ Quick Start

### Docker (Recommended)
```bash
git clone https://github.com/Kunze-Ritter/Manual2Vector
cd Manual2Vector
./setup.sh  # or .\setup.ps1 on Windows
docker-compose -f docker-compose.simple.yml up --build -d
```

### With GPU Support (CUDA)
```bash
docker-compose -f docker-compose.yml up --build -d
```

**That's it!** Access the dashboard at http://localhost:80

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     KRAI Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│  Upload → Text → Table → SVG → Image → Visual Embedding    │
│  → Link → Video → Chunk → Classify → Metadata → Parts     │
│  → Series → Storage → Embedding → Search                   │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 + pgvector
- **Storage**: MinIO (S3-compatible)
- **AI**: Ollama (local LLM)
- **Dashboard**: Laravel + Filament

## 📁 Project Structure

```
├── backend/           # Python application
│   ├── api/         # FastAPI routes
│   ├── processors/  # 16-stage pipeline
│   ├── services/    # Database, Storage, AI
│   └── core/        # BaseProcessor, models
├── database/         # PostgreSQL migrations
├── docs/             # Documentation
├── tests/            # Test suite
└── docker-compose*.yml
```

## 🔧 Common Commands

```bash
# Start services
docker-compose -f docker-compose.simple.yml up -d

# Run tests
python -m pytest tests/ -v

# Lint code
ruff check backend/
black backend/
mypy backend/

# Validate environment
python scripts/validate_env.py
```

## 📚 Documentation

| File | Description |
|------|-------------|
| `CLAUDE.md` | Developer guide (AI assistant) |
| `DATABASE_SCHEMA.md` | Database documentation |
| `DB_QUICK_REFERENCE.md` | Quick DB reference |
| `MASTER-TODO.md` | Project tasks |
| `DOCKER_SETUP.md` | Docker guide |

## 🔌 API Endpoints

- **API**: http://localhost:8000
- **Swagger**: http://localhost:8000/docs
- **Dashboard**: http://localhost:80
- **Metrics**: http://localhost:8000/status/metrics

## 🆘 Support

- **Issues**: GitHub Issues
- **Docs**: See `docs/` directory
- **Environment**: `python scripts/validate_env.py`

## License

MIT License - see LICENSE file
