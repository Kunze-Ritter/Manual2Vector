# 🔧 Environment Configuration Structure

## Modular .env Files

Die Konfiguration ist in mehrere Dateien aufgeteilt für bessere Übersicht:

### 📁 File Structure

```text
.env.auth        # Authentication service & admin bootstrap
.env.database    # Database configuration (Supabase)
.env.storage     # Object storage (Cloudflare R2)
.env.ai          # AI services (Ollama)
.env.pipeline    # Processing pipeline settings
.env.external    # External APIs (YouTube, Cloudflare Tunnels)
.env             # Main config (optional, for overrides)
```

---

## 📋 File Details

### `.env.auth` - Authentication Service

Use this file to configure JWT signing keys and the bootstrap admin account.

#### Key Variables

- `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` - RS256 key pair
- `JWT_ALGORITHM` - Token signing algorithm
- `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_USERNAME` - Bootstrap admin account
- `DEFAULT_ADMIN_FIRST_NAME` / `DEFAULT_ADMIN_LAST_NAME`
- `DEFAULT_ADMIN_PASSWORD` - Optional (leave blank to prompt)

### `.env.database` - Database Configuration

This file stores credentials for the primary database connection.

#### Connection Values

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Public anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (full access)
- `DATABASE_CONNECTION_URL` - Direct PostgreSQL connection
- `DATABASE_PASSWORD` - Database password

### `.env.storage` - Object Storage

Holds credentials and settings for Cloudflare R2 object storage.

#### Storage Settings

- `R2_ACCESS_KEY_ID` - R2 access key
- `R2_SECRET_ACCESS_KEY` - R2 secret key
- `R2_BUCKET_NAME_DOCUMENTS` - Bucket name
- `R2_ENDPOINT_URL` - R2 endpoint
- `R2_PUBLIC_URL_*` - Public URLs for buckets
- `UPLOAD_IMAGES_TO_R2` - Enable/disable image upload
- `UPLOAD_DOCUMENTS_TO_R2` - Enable/disable document upload

### `.env.ai` - AI Services

Contains Ollama model selections and AI runtime tuning.

#### AI Settings

- `OLLAMA_URL` - Ollama server URL
- `OLLAMA_MODEL_EMBEDDING` - Embedding model
- `OLLAMA_MODEL_TEXT` - Text generation model
- `OLLAMA_MODEL_VISION` - Vision model
- `DISABLE_VISION_PROCESSING` - Skip vision AI
- `MAX_VISION_IMAGES` - Max images to process

### `.env.pipeline` - Processing Pipeline

Controls which processing pipeline features are enabled.

#### Pipeline Settings

- `ENABLE_PRODUCT_EXTRACTION` - Extract products
- `ENABLE_PARTS_EXTRACTION` - Extract spare parts
- `ENABLE_ERROR_CODE_EXTRACTION` - Extract error codes
- `ENABLE_VERSION_EXTRACTION` - Extract versions
- `ENABLE_IMAGE_EXTRACTION` - Extract images
- `ENABLE_OCR` - Run OCR on images
- `ENABLE_VISION_AI` - Run Vision AI
- `ENABLE_LINK_EXTRACTION` - Extract links/videos
- `ENABLE_EMBEDDINGS` - Generate embeddings

### `.env.external` - External APIs

Captures API keys and integration URLs for external services.

#### External Settings

- `YOUTUBE_API_KEY` - YouTube Data API key
- `CLOUDFLARE_TUNNEL_TOKEN` - N8N tunnel token
- `CLOUDFLARE_TUNNEL_TOKEN_OLLAMA` - Ollama tunnel token
- `N8N_HOST` - N8N hostname
- `WEBHOOK_URL` - Webhook URL
- `OLLAMA_BASE_URL` - Public Ollama URL

---

## 🔄 Loading Order

Files are loaded in this order (later files can override earlier ones):

1. `.env.auth` - Authentication keys & admin defaults
2. `.env.database` - Core database config
3. `.env.storage` - Storage configuration
4. `.env.ai` - AI services
5. `.env.pipeline` - Pipeline settings
6. `.env.external` - External APIs
7. `.env` - Main config (optional overrides)

---

## 🛠️ Usage

### Automatic Loading

All files are automatically loaded when you import any processor:

```python
from processors.document_processor import DocumentProcessor

# All .env.* files are already loaded!
processor = DocumentProcessor()
```

### Manual Loading

```python
from processors.env_loader import load_all_env_files, get_env_summary

# Load all .env files
loaded = load_all_env_files()
print(f"Loaded: {loaded}")

# Get summary
summary = get_env_summary()
print(summary)
```

---

## 🔒 Security

### Private Repository

- ✅ All `.env.*` files are tracked in git
- ✅ Repository is private
- ✅ Team members get full config automatically

### Local Overrides

Create `.env.*.local` files for local overrides (not tracked):

- `.env.database.local` - Override database config
- `.env.storage.local` - Override storage config
- etc.

---

## 📝 Setup on New Computer

```bash
# 1. Clone repository
git clone https://github.com/Kunze-Ritter/Manual2Vector.git
cd Manual2Vector

# 2. All .env files are already there!
# No setup needed - just run:
python backend/processors/process_production.py
```

---

## 🎯 Benefits

1. **✅ Better Organization** - Each file has a clear purpose
2. **✅ Easy to Find** - Settings grouped by category
3. **✅ Selective Sharing** - Share only relevant files
4. **✅ Override Support** - Use `.local` files for local changes
5. **✅ Auto-Loading** - No manual loading needed
6. **✅ Backwards Compatible** - Old `.env` still works

---

## 🔧 Troubleshooting

### Check Loaded Configuration

```python
from processors.env_loader import get_env_summary

summary = get_env_summary()
print(summary)
```

### Missing Settings

If settings are missing, check:

1. All `.env.*` files exist
2. Files are in project root
3. No syntax errors in files
4. Run `python backend/scripts/check_config.py`

**Last Updated:** 2025-10-09
