#!/bin/bash

# KRAI Engine Docker Setup Script
# Generates all required secrets from .env.example automatically
# For production: Review and customize generated values before deployment
# Note: For Windows 10/11, use setup.ps1 (PowerShell) instead of setup.bat
#       setup.ps1 is more modern and maintainable than the legacy batch script.

set -e

FORCE_OVERWRITE=false

while [ $# -gt 0 ]; do
    case "$1" in
        --force)
            FORCE_OVERWRITE=true
            shift
            ;;
        -* )
            echo "❌ Error: Unknown option $1" >&2
            exit 1
            ;;
        * )
            echo "❌ Error: Unexpected argument $1" >&2
            exit 1
            ;;
    esac
done

if [ "${FORCE:-0}" = "1" ]; then
    FORCE_OVERWRITE=true
fi

echo "🚀 KRAI Engine Docker Setup"
echo "============================"

if ! command -v openssl >/dev/null 2>&1; then
    echo "❌ Error: openssl is required but not installed." >&2
    exit 1
fi

if ! command -v base64 >/dev/null 2>&1; then
    echo "❌ Error: base64 utility is required but not available." >&2
    exit 1
fi

BASE64_HAS_WRAP_FLAG=false
if base64 --help 2>&1 | grep -q -- "-w"; then
    BASE64_HAS_WRAP_FLAG=true
fi

TEMP_FILES=()

cleanup() {
    if [ ${#TEMP_FILES[@]} -gt 0 ]; then
        rm -f "${TEMP_FILES[@]}"
    fi
}

trap cleanup EXIT

b64_no_wrap() {
    local input_file="$1"
    if [ "$BASE64_HAS_WRAP_FLAG" = true ]; then
        base64 -w0 "$input_file"
    else
        base64 "$input_file" | tr -d '\n'
    fi
}

generate_secure_password() {
    local length=${1:-32}
    local chars='A-Za-z0-9!@#$%^&*()_+=\-[]{}:,.?'
    local password

    while true; do
        password=$(LC_ALL=C tr -dc "$chars" < /dev/urandom | head -c "$length")
        if [ "${#password}" -lt "$length" ]; then
            continue
        fi
        [[ "$password" =~ [A-Z] ]] || continue
        [[ "$password" =~ [a-z] ]] || continue
        [[ "$password" =~ [0-9] ]] || continue
        [[ "$password" =~ [!@#$%^&*()_+=\-\[\]{}:,.?] ]] || continue
        echo "$password"
        break
    done
}

generate_urlsafe_password() {
    local length=${1:-32}
    local chars='A-Za-z0-9_.~-'
    local password

    while true; do
        password=$(LC_ALL=C tr -dc "$chars" < /dev/urandom | head -c "$length")
        if [ "${#password}" -lt "$length" ]; then
            continue
        fi
        [[ "$password" =~ [A-Z] ]] || continue
        [[ "$password" =~ [a-z] ]] || continue
        [[ "$password" =~ [0-9] ]] || continue
        echo "$password"
        break
    done
}

generate_rsa_keypair() {
    local private_key_pem
    local private_key_der
    local public_key_der

    private_key_pem=$(mktemp)
    private_key_der=$(mktemp)
    public_key_der=$(mktemp)

    TEMP_FILES+=("$private_key_pem" "$private_key_der" "$public_key_der")

    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$private_key_pem" >/dev/null 2>&1
    openssl pkcs8 -topk8 -inform PEM -outform DER -nocrypt -in "$private_key_pem" -out "$private_key_der" >/dev/null 2>&1
    openssl rsa -in "$private_key_pem" -pubout -outform DER -out "$public_key_der" >/dev/null 2>&1

    JWT_PRIVATE_KEY_B64=$(b64_no_wrap "$private_key_der")
    JWT_PUBLIC_KEY_B64=$(b64_no_wrap "$public_key_der")
}

get_env_value() {
    local key="$1"
    sed -n "s/^${key}=\(.*\)$/\1/p" .env | tail -n 1
}

backup_env_file() {
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path=".env.bak.${timestamp}"

    if ! cp .env "$backup_path"; then
        echo "❌ Error: Failed to create backup at ${backup_path}." >&2
        exit 1
    fi

    echo "📦 Existing .env backed up to ${backup_path}."
}

prepare_env_output() {
    if [ ! -f .env ]; then
        return 0
    fi

    if [ "$FORCE_OVERWRITE" = true ]; then
        backup_env_file
        return 0
    fi

    if [ ! -t 0 ]; then
        echo "❌ Error: .env already exists and no interactive terminal is available to confirm overwrite." >&2
        echo "   Re-run with --force or set FORCE=1 to overwrite automatically." >&2
        exit 1
    fi

    read -r -p "⚠️  .env already exists. Overwrite and create backup? [y/N]: " response || {
        echo "❌ Error: Unable to read user input. Use --force or FORCE=1 for non-interactive runs." >&2
        exit 1
    }

    case "$response" in
        [yY][eE][sS]|[yY])
            backup_env_file
            ;;
        *)
            echo "ℹ️  Aborting without modifying .env."
            exit 0
            ;;
    esac
}

validate_env_file() {
    local errors=0
    local warnings=0

    if [ ! -f .env ]; then
        echo "❌ Error: .env file not found." >&2
        return 1
    fi

    local database_password object_storage_secret jwt_private_key jwt_public_key admin_password
    database_password=$(get_env_value "DATABASE_PASSWORD")
    object_storage_secret=$(get_env_value "OBJECT_STORAGE_SECRET_KEY")
    jwt_private_key=$(get_env_value "JWT_PRIVATE_KEY")
    jwt_public_key=$(get_env_value "JWT_PUBLIC_KEY")
    admin_password=$(get_env_value "DEFAULT_ADMIN_PASSWORD")

    if [ -z "$database_password" ]; then
        echo "❌ Error: DATABASE_PASSWORD is missing." >&2
        errors=$((errors + 1))
    fi

    if [ -z "$object_storage_secret" ]; then
        echo "❌ Error: OBJECT_STORAGE_SECRET_KEY is missing." >&2
        errors=$((errors + 1))
    fi

    if [ -z "$jwt_private_key" ]; then
        echo "❌ Error: JWT_PRIVATE_KEY is missing." >&2
        errors=$((errors + 1))
    elif ! echo "$jwt_private_key" | grep -Eq '^[A-Za-z0-9+/=]+$'; then
        echo "❌ Error: JWT_PRIVATE_KEY is not valid Base64." >&2
        errors=$((errors + 1))
    fi

    if [ -z "$jwt_public_key" ]; then
        echo "❌ Error: JWT_PUBLIC_KEY is missing." >&2
        errors=$((errors + 1))
    elif ! echo "$jwt_public_key" | grep -Eq '^[A-Za-z0-9+/=]+$'; then
        echo "❌ Error: JWT_PUBLIC_KEY is not valid Base64." >&2
        errors=$((errors + 1))
    fi

    if [ -z "$admin_password" ]; then
        echo "❌ Error: DEFAULT_ADMIN_PASSWORD is missing." >&2
        errors=$((errors + 1))
    elif [ ${#admin_password} -lt 12 ]; then
        echo "❌ Error: DEFAULT_ADMIN_PASSWORD must be at least 12 characters." >&2
        errors=$((errors + 1))
    fi

    local upload_images_to_r2 r2_secret_access_key r2_access_key_id r2_endpoint_url upload_images_to_r2_lower
    upload_images_to_r2=$(get_env_value "UPLOAD_IMAGES_TO_R2")
    r2_secret_access_key=$(get_env_value "R2_SECRET_ACCESS_KEY")
    r2_access_key_id=$(get_env_value "R2_ACCESS_KEY_ID")
    r2_endpoint_url=$(get_env_value "R2_ENDPOINT_URL")
    upload_images_to_r2_lower=$(printf '%s' "$upload_images_to_r2" | tr '[:upper:]' '[:lower:]')

    if { [ "$upload_images_to_r2_lower" = "true" ] || [ -n "$r2_access_key_id" ] || [ -n "$r2_endpoint_url" ]; } && [ -z "$r2_secret_access_key" ]; then
        echo "❌ Error: R2_SECRET_ACCESS_KEY is required when Cloudflare R2 uploads are enabled." >&2
        errors=$((errors + 1))
    fi

    local n8n_db_password pgadmin_default_password firecrawl_bull_auth_key
    n8n_db_password=$(get_env_value "N8N_DATABASE_PASSWORD")
    pgadmin_default_password=$(get_env_value "PGADMIN_DEFAULT_PASSWORD")
    firecrawl_bull_auth_key=$(get_env_value "FIRECRAWL_BULL_AUTH_KEY")

    if [ -z "$n8n_db_password" ]; then
        echo "❌ Error: N8N_DATABASE_PASSWORD is missing." >&2
        errors=$((errors + 1))
    fi

    if [ -z "$pgadmin_default_password" ]; then
        echo "❌ Error: PGADMIN_DEFAULT_PASSWORD is missing." >&2
        errors=$((errors + 1))
    fi

    if [ -z "$firecrawl_bull_auth_key" ]; then
        echo "❌ Error: FIRECRAWL_BULL_AUTH_KEY is missing." >&2
        errors=$((errors + 1))
    fi

    local youtube_key cloudflare_token
    youtube_key=$(get_env_value "YOUTUBE_API_KEY")
    cloudflare_token=$(get_env_value "CLOUDFLARE_TUNNEL_TOKEN")

    if [ -z "$youtube_key" ]; then
        echo "⚠️  Warning: YOUTUBE_API_KEY is not set. YouTube integrations will be disabled." >&2
        warnings=$((warnings + 1))
    fi

    if [ -z "$cloudflare_token" ]; then
        echo "⚠️  Warning: CLOUDFLARE_TUNNEL_TOKEN is not set. Cloudflare tunnels will be disabled." >&2
        warnings=$((warnings + 1))
    fi

    if [ "$errors" -gt 0 ]; then
        return 1
    fi

    return 0
}

prepare_env_output

echo "🔐 Generating secure passwords and keys..."
echo "   This may take a moment for RSA key generation..."

# Database credentials
DB_PASSWORD=$(generate_secure_password 32)

# Object storage credentials
MINIO_SECRET_KEY=$(generate_secure_password 32)
R2_SECRET_KEY=$(generate_secure_password 32)

# Authentication & Security
echo "   Generating RSA keypair for JWT..."
generate_rsa_keypair
ADMIN_PASSWORD=$(generate_secure_password 16)

# Docker Compose services
N8N_PASSWORD=$(generate_secure_password 24)
N8N_DB_PASSWORD=$(generate_secure_password 32)
PGADMIN_PASSWORD=$(generate_secure_password 24)
FIRECRAWL_BULL_KEY=$(generate_secure_password 32)

# Test environment
TEST_DB_PASSWORD=$(generate_urlsafe_password 32)
TEST_DB_PASSWORD_URL=${TEST_DB_PASSWORD}
TEST_STORAGE_KEY=$(generate_secure_password 32)
TEST_FIRECRAWL_KEY=$(generate_secure_password 32)

echo "📝 Creating .env file with generated credentials..."

cat > .env <<EOF
# ==========================================
# KRAI ENGINE ENVIRONMENT CONFIGURATION
# ==========================================
# Auto-generated by setup.sh on $(date)
# NEVER commit this populated .env file to version control!
# Review and customize these values before production deployment.
# ----------------------------------------------------------------------------
# Copy this file to `.env` and adjust values before running the stack.
# Use `./setup.sh` (Linux/macOS) or `setup.bat` (Windows) to generate secrets automatically.
# Keep this file version-controlled for reference, but never commit a populated `.env` file.
# Store production credentials in a secure secrets manager (1Password, Vault, etc.).
# ----------------------------------------------------------------------------
# Environment loading guidance:
# - Prefer maintaining a single `.env` at the repository root.
# - Legacy scripts that call `load_dotenv(".env.database")` should be updated to call `load_dotenv()` without arguments.
# - Until updated, you may create a local `.env.database` that mirrors the variables defined in your root `.env`.
# - Prefer using `scripts/_env.load_env()` in Python helpers and passing `extra_files=['.env.database']` only when a legacy override is required.
# ----------------------------------------------------------------------------
# Pro Tip: Comment out sections you do not use to avoid accidentally mixing configs.

# ==========================================
# APPLICATION SETTINGS
# ==========================================
# Runtime environment: production, staging, development
ENV=production

# Backend API host binding (0.0.0.0 for Docker, 127.0.0.1 for local only)
API_HOST=0.0.0.0

# Backend API port (FastAPI / Uvicorn)
API_PORT=8000

# Global log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=DEBUG


# ==========================================
# DATABASE CONFIGURATION
# ==========================================
# Choose PostgreSQL OR Supabase, not both at the same time.

# --- PostgreSQL (Docker/Local) ---
# Database backend type: postgresql or sqlite (PostgreSQL recommended)
DATABASE_TYPE=postgresql

# Hostname for local Docker Compose service
DATABASE_HOST=krai-postgres

# PostgreSQL service port
DATABASE_PORT=5432

# Database name for local deployment
DATABASE_NAME=krai

# PostgreSQL username used by the application
DATABASE_USER=krai_user

# PostgreSQL password (change for production!)
DATABASE_PASSWORD=${DB_PASSWORD}

# --- Supabase (Cloud) ---
# Supabase project URL (https://<project>.supabase.co)
SUPABASE_URL=https://your-project.supabase.co

# Supabase anonymous key (client-side usage)
SUPABASE_ANON_KEY=your-anon-key-here

# Supabase service role key (server-side only, keep secret!)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Supabase storage API base URL
SUPABASE_STORAGE_URL=https://your-project.supabase.co/storage/v1

# Optional password for direct Supabase PostgreSQL connections (deprecated scripts only)
#SUPABASE_DB_PASSWORD=your-supabase-db-password

# Direct PostgreSQL connection string (optional alternative to local DB)
DATABASE_CONNECTION_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Optional (deprecated) legacy alias used by older scripts — prefer DATABASE_CONNECTION_URL
#DATABASE_URL=postgresql://krai_user:krai_secure_password@krai-postgres:5432/krai            # Local PostgreSQL example
#DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres  # Supabase example


# ==========================================
# OBJECT STORAGE CONFIGURATION
# ==========================================
# Choose MinIO OR Cloudflare R2 depending on your deployment target.

# --- MinIO (Docker/Local) ---
# Object storage implementation (s3-compatible for both MinIO & R2)
OBJECT_STORAGE_TYPE=s3

# Internal endpoint for MinIO service in Docker
OBJECT_STORAGE_ENDPOINT=http://krai-minio:9000

# Optional (deprecated) legacy alias mirroring OBJECT_STORAGE_ENDPOINT
#MINIO_ENDPOINT=http://krai-minio:9000

# MinIO access key (change for production!)
OBJECT_STORAGE_ACCESS_KEY=minioadmin

# MinIO secret key (change for production!)
OBJECT_STORAGE_SECRET_KEY=${MINIO_SECRET_KEY}

# AWS region style identifier (MinIO accepts any string)
OBJECT_STORAGE_REGION=us-east-1

# Set to true if MinIO endpoint uses HTTPS (self-hosted defaults to false)
OBJECT_STORAGE_USE_SSL=false

# Public URL used by the frontend to access stored files
OBJECT_STORAGE_PUBLIC_URL=http://localhost:9000

# --- Cloudflare R2 (Cloud) ---
# Cloudflare R2 access key ID
R2_ACCESS_KEY_ID=your-r2-access-key-id

# Cloudflare R2 secret access key
R2_SECRET_ACCESS_KEY=${R2_SECRET_KEY}

# Bucket name for processed documents (documents/manuals)
R2_BUCKET_NAME_DOCUMENTS=your-bucket-name

# R2 S3-compatible API endpoint URL
R2_ENDPOINT_URL=https://your-account-id.eu.r2.cloudflarestorage.com

# R2 selected region (use `auto` unless you have a specific requirement)
R2_REGION=auto

# Public CDN URL for shared documents bucket
R2_PUBLIC_URL_DOCUMENTS=https://pub-your-documents-bucket.r2.dev

# Public CDN URL for error screenshots or diagnostic assets
R2_PUBLIC_URL_ERROR=https://pub-your-error-bucket.r2.dev

# Public CDN URL for spare parts assets
R2_PUBLIC_URL_PARTS=https://pub-your-parts-bucket.r2.dev

# Upload extracted images to R2 (recommended true for cloud deployments)
UPLOAD_IMAGES_TO_R2=true

# Upload original source documents to R2 (enable for cloud backup)
UPLOAD_DOCUMENTS_TO_R2=false


# ==========================================
# AI SERVICE CONFIGURATION
# ==========================================
# Consolidated configuration for Ollama-based AI services and GPU controls.

# --- Ollama Base ---
# AI service provider type (ollama or openai). Currently supports `ollama`.
AI_SERVICE_TYPE=ollama

# Base URL for internal AI service abstraction (used by backend)
AI_SERVICE_URL=http://krai-ollama:11434

# Ollama server URL (used by backend - consistent naming)
# Note: Backend uses OLLAMA_URL, not OLLAMA_BASE_URL or AI_SERVICE_URL
OLLAMA_URL=http://krai-ollama:11434
# For host CLI/testing, you may override with http://localhost:11434

# --- Ollama Models ---
# Embedding model (vector generation for semantic search)
OLLAMA_MODEL_EMBEDDING=nomic-embed-text:latest

# Structured extraction model (product specs as JSON)
OLLAMA_MODEL_EXTRACTION=qwen2.5:3b

# Conversational model (agent/chat responses)
OLLAMA_MODEL_CHAT=llama3.2:3b

# Vision-capable model (diagram/OCR understanding)
OLLAMA_MODEL_VISION=llava:7b

# Legacy/fallback text model (deprecated path support)
OLLAMA_MODEL_TEXT=qwen2.5:3b

# Context window tokens for Ollama prompts (higher requires more VRAM)
OLLAMA_NUM_CTX=8192

# --- Vision Processing ---
# Disable AI-based vision analysis entirely (images still extracted locally)
DISABLE_VISION_PROCESSING=false

# Maximum number of images analyzed per document (tune for VRAM limits)
MAX_VISION_IMAGES=5

# --- Solution Translation ---
# Enable automatic translation of troubleshooting steps via LLM
ENABLE_SOLUTION_TRANSLATION=false

# Target language for solution translation (ISO code, e.g. de, en, fr)
SOLUTION_TRANSLATION_LANGUAGE=de

# --- LLM Extraction Controls ---
# Maximum document pages scanned by LLM extraction (0 = all pages, -1 = disabled)
LLM_MAX_PAGES=50

# --- GPU Configuration ---
# Enable GPU acceleration for OpenCV/ML pipelines (requires CUDA drivers)
USE_GPU=false

# CUDA device index to target (0 = primary GPU)
CUDA_VISIBLE_DEVICES=0

# --- Visual Embeddings ---
# Vision embedding model identifier (used for multimodal search indexing)
AI_VISUAL_EMBEDDING_MODEL=vidore/colqwen2.5-v0.2


# ==========================================
# AUTHENTICATION & SECURITY
# ==========================================
# Generate fresh RSA keys for production and keep them secret!

# --- JWT Configuration ---
# JWT signing algorithm (RS256 recommended for asymmetric keys)
JWT_ALGORITHM=RS256

# Access token lifetime in minutes
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Refresh token lifetime in days
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Base64-encoded PKCS8 private key (see instructions below)
JWT_PRIVATE_KEY=${JWT_PRIVATE_KEY_B64}

# Base64-encoded SubjectPublicKeyInfo public key
JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY_B64}

# PowerShell key generation:
#   $key = New-Object System.Security.Cryptography.RSACryptoServiceProvider 2048
#   [Convert]::ToBase64String($key.ExportPkcs8PrivateKey())
#   [Convert]::ToBase64String($key.ExportSubjectPublicKeyInfo())
# OpenSSL alternative:
#   openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out jwt_private.pem
#   openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
#   base64 -w0 jwt_private.pem
#   base64 -w0 jwt_public.pem

# --- Security Controls ---
# Maximum failed login attempts before account lockout
MAX_LOGIN_ATTEMPTS=5

# Account lockout duration in minutes
ACCOUNT_LOCKOUT_DURATION_MINUTES=15

# Password complexity requirements
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBER=true
PASSWORD_REQUIRE_SPECIAL=true

# Minimum password length enforced by backend validation
PASSWORD_MIN_LENGTH=12

# --- Session Management ---
# Session idle timeout in minutes
SESSION_TIMEOUT_MINUTES=60

# Remember-me token lifetime in days
REMEMBER_ME_DAYS=30

# --- Default Admin Bootstrap ---
# Default admin email created on first startup (override before production!)
DEFAULT_ADMIN_EMAIL=admin@example.com

# Default admin username
DEFAULT_ADMIN_USERNAME=admin

# Default admin first name
DEFAULT_ADMIN_FIRST_NAME=System

# Default admin last name
DEFAULT_ADMIN_LAST_NAME=Administrator

# Default admin password (leave blank to prompt during setup)
DEFAULT_ADMIN_PASSWORD=${ADMIN_PASSWORD}


# ==========================================
# PROCESSING PIPELINE SETTINGS
# ==========================================
# Toggle specific extraction steps for debugging or resource management.

# Extract product models from manuals (recommended: true)
ENABLE_PRODUCT_EXTRACTION=true

# Extract spare parts catalogs (recommended for service manuals)
ENABLE_PARTS_EXTRACTION=true

# Extract diagnostic error codes (recommended: true)
ENABLE_ERROR_CODE_EXTRACTION=true

# Extract document version metadata (recommended: true)
ENABLE_VERSION_EXTRACTION=true

# Extract inline images from PDFs (recommended: true)
ENABLE_IMAGE_EXTRACTION=true

# Run OCR on extracted images for searchable text (depends on Tesseract/OpenCV)
ENABLE_OCR=true

# Run AI-based vision analysis on extracted images (set false if low VRAM)
ENABLE_VISION_AI=true

# Extract outbound links and embedded videos for enrichment
ENABLE_LINK_EXTRACTION=true

# Generate embeddings for semantic search (required for vector search)
ENABLE_EMBEDDINGS=true


# ==========================================
# WEB SCRAPING CONFIGURATION
# ==========================================
# Controls the scraping backend (BeautifulSoup, Firecrawl) and related services.

# --- Scraping Backend Selection ---
# Available options: beautifulsoup (local HTML parsing), firecrawl (cloud service)
SCRAPING_BACKEND=beautifulsoup

# Enable post-processing link enrichment to fetch additional metadata
ENABLE_LINK_ENRICHMENT=true

# Enable manufacturer crawling workflows (Firecrawl recommended)
ENABLE_MANUFACTURER_CRAWLING=false

# --- Firecrawl Configuration (Only if SCRAPING_BACKEND=firecrawl) ---
# Firecrawl API base URL (self-hosted or cloud endpoint)
FIRECRAWL_API_URL=http://localhost:3002

# LLM provider name used by Firecrawl (openai, ollama, etc.)
FIRECRAWL_LLM_PROVIDER=ollama

# Default LLM model for summarization/extraction via Firecrawl
FIRECRAWL_MODEL_NAME=qwen2.5:3b

# Embedding model for Firecrawl vector outputs
FIRECRAWL_EMBEDDING_MODEL=nomic-embed-text:latest

# Maximum concurrent Firecrawl jobs allowed
FIRECRAWL_MAX_CONCURRENCY=3

# Block heavy media downloads during scraping (true/false)
FIRECRAWL_BLOCK_MEDIA=true

# Allow callbacks to local webhook endpoints (set false for production)
FIRECRAWL_ALLOW_LOCAL_WEBHOOKS=true

# Optional proxy configuration (leave blank if unused)
FIRECRAWL_PROXY_SERVER=
FIRECRAWL_PROXY_USERNAME=
FIRECRAWL_PROXY_PASSWORD=

# Maximum scrape duration per request in seconds
FIRECRAWL_SCRAPE_TIMEOUT=120

# Maximum crawl duration for multi-page jobs in seconds
FIRECRAWL_CRAWL_TIMEOUT=600

# Retry attempts for failed Firecrawl jobs
FIRECRAWL_RETRIES=2

# Optional OpenAI API key (required if FIRECRAWL_LLM_PROVIDER=openai)
OPENAI_API_KEY=


# ==========================================
# EXTERNAL API KEYS & TUNNELS
# ==========================================
# Keep all third-party credentials secret. Rotate keys regularly.

# --- YouTube Data API ---
# Obtain from https://console.cloud.google.com/apis/credentials (10k daily quota)
YOUTUBE_API_KEY=

# --- Cloudflare Tunnels (Optional) ---
# Tunnel token for exposing n8n or automation webhook endpoints
CLOUDFLARE_TUNNEL_TOKEN=

# Public hostname for n8n automation platform
N8N_HOST=workflow.your-domain.com

# Public webhook URL for n8n workflows
WEBHOOK_URL=https://workflow.your-domain.com/

# Tunnel token for exposing Ollama securely over the internet
CLOUDFLARE_TUNNEL_TOKEN_OLLAMA=your-ollama-tunnel-token-here

# Public hostname for remote Ollama access (Cloudflare Tunnel)
# This is different from OLLAMA_URL (internal Docker network)
OLLAMA_BASE_URL=https://llm.your-domain.com


# ==========================================
# DOCKER COMPOSE CONFIGURATION
# ==========================================
# Variables specific to Docker Compose deployments

# --- n8n Configuration ---
# n8n basic auth username
N8N_BASIC_AUTH_USER=admin

# n8n basic auth password (change for production!)
N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}

# n8n separate database password (different from main KRAI DB)
N8N_DATABASE_PASSWORD=${N8N_DB_PASSWORD}

# --- pgAdmin Configuration ---
# pgAdmin default admin email
PGADMIN_DEFAULT_EMAIL=admin@krai.local

# pgAdmin default admin password (change for production!)
PGADMIN_DEFAULT_PASSWORD=${PGADMIN_PASSWORD}

# --- MinIO Browser Configuration ---
# MinIO browser redirect URL (for console access)
MINIO_BROWSER_REDIRECT_URL=http://localhost:9001

# --- Firecrawl Bull Queue ---
# Firecrawl Bull queue authentication key (change for production!)
FIRECRAWL_BULL_AUTH_KEY=${FIRECRAWL_BULL_KEY}

# --- Playwright Configuration ---
# Playwright workspace auto-cleanup (true/false)
PLAYWRIGHT_WORKSPACE_DELETE_EXPIRED=true

# Playwright workspace expiry in days
PLAYWRIGHT_WORKSPACE_EXPIRY_DAYS=1

# --- Grafana Configuration (Enterprise) ---
# Grafana allow user sign-up (true/false)
GRAFANA_ALLOW_SIGN_UP=false

# --- Redis Configuration ---
# Redis URL for application cache (optional)
REDIS_URL=redis://krai-redis:6379

# --- Test Environment Variables ---
# Test database name (separate from production)
TEST_DATABASE_NAME=krai_test

# Test database user
TEST_DATABASE_USER=krai_test

# Test database password
TEST_DATABASE_PASSWORD=${TEST_DB_PASSWORD}

# Test database connection URL
TEST_DATABASE_URL=postgresql://krai_test:${TEST_DB_PASSWORD_URL}@postgresql-test:5432/krai_test

# Test storage access key
TEST_STORAGE_ACCESS_KEY=test_access_key

# Test storage secret key
TEST_STORAGE_SECRET_KEY=${TEST_STORAGE_KEY}

# Test storage endpoint
TEST_STORAGE_ENDPOINT=minio-test:9000

# Test Firecrawl Bull auth key
TEST_FIRECRAWL_BULL_AUTH_KEY=${TEST_FIRECRAWL_KEY}


# ==========================================
# SECURITY REMINDERS & DOCUMENTATION
# ==========================================
# - NEVER commit your populated `.env` file to version control.
# - Rotate secrets immediately if they leak or when personnel changes.
# - Store production secrets in a secure, access-controlled vault.
# - Review `docs/DOCKER_SETUP.md` for full deployment instructions.
# - Use `./setup.sh` or `setup.bat` to bootstrap local development safely.
EOF

chmod 600 .env

echo "✅ .env file created successfully!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔑 GENERATED CREDENTIALS (Keep these secure!)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 DATABASE:"
echo "   PostgreSQL Password:     ${DB_PASSWORD}"
echo "   n8n Database Password:   ${N8N_DB_PASSWORD}"
echo "   Test Database Password:  ${TEST_DB_PASSWORD}"
echo ""
echo "💾 OBJECT STORAGE:"
echo "   MinIO Secret Key:        ${MINIO_SECRET_KEY}"
echo "   R2 Secret Key:           ${R2_SECRET_KEY}"
echo "   Test Storage Key:        ${TEST_STORAGE_KEY}"
echo ""
echo "🔐 AUTHENTICATION:"
echo "   Admin Password:          ${ADMIN_PASSWORD}"
echo "   JWT Private Key:         [Generated - see .env]"
echo "   JWT Public Key:          [Generated - see .env]"
echo ""
echo "🐳 DOCKER SERVICES:"
echo "   n8n Password:            ${N8N_PASSWORD}"
echo "   pgAdmin Password:        ${PGADMIN_PASSWORD}"
echo "   Firecrawl Bull Key:      ${FIRECRAWL_BULL_KEY}"
echo "   Test Firecrawl Key:      ${TEST_FIRECRAWL_KEY}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "   • NEVER commit .env to version control (already in .gitignore)"
echo "   • Store these credentials in a secure password manager"
echo "   • For production: Review and customize all values in .env"
echo "   • Rotate secrets regularly (every 90 days recommended)"
echo ""
echo "📝 MANUAL CONFIGURATION REQUIRED:"
echo "   • YOUTUBE_API_KEY: Get from https://console.cloud.google.com/apis/credentials"
echo "   • CLOUDFLARE_TUNNEL_TOKEN: Get from https://dash.cloudflare.com/"
echo "   • Review all AI model names in AI SERVICE CONFIGURATION section"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 NEXT STEPS:"
echo "   1. Review .env file and customize as needed"
echo "   2. Start Docker: docker-compose -f docker-compose.simple.yml up -d"
echo "   3. Check status:  docker-compose -f docker-compose.simple.yml ps"
echo "   4. View logs:     docker-compose -f docker-compose.simple.yml logs -f"
echo "   5. Access API:    curl http://localhost:8000/health"
echo "   6. Access UI:     http://localhost:3000"
echo ""
echo "📚 DOCUMENTATION:"
echo "   • Full setup guide: DOCKER_SETUP.md"
echo "   • Deployment guide: DEPLOYMENT.md"
echo "   • Database schema: DATABASE_SCHEMA.md"
echo ""
echo "🎉 Setup complete! Your KRAI Engine is ready to start."
echo ""
echo "🔍 Validating generated .env file..."
if validate_env_file; then
    echo "✅ Validation passed!"
else
    echo "❌ Validation failed! Please review .env file."
    exit 1
fi
