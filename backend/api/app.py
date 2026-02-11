"""
KRAI Processing Pipeline API

FastAPI app for monitoring, managing, and controlling the document processing pipeline.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import os
import secrets
import sys
import logging
import functools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.upload_processor import UploadProcessor, BatchUploadProcessor
from processors.stage_tracker import StageTracker
from api.dependencies.auth import set_auth_service
from api.dependencies.auth_factory import create_auth_service, create_and_initialize_auth_service
from api.middleware.auth_middleware import AuthMiddleware, require_permission
from api.middleware.rate_limit_middleware import (
    APIKeyValidationMiddleware,
    IPFilterMiddleware,
    limiter,
    rate_limit_health,
    rate_limit_health_dynamic,
    rate_limit_search,
    rate_limit_search_dynamic,
    rate_limit_standard,
    rate_limit_standard_dynamic,
    rate_limit_upload,
    rate_limit_upload_dynamic,
    rate_limit_exception_handler,
)
from api.middleware.request_validation_middleware import RequestValidationMiddleware
from services.auth_service import AuthService, AuthenticationError
from services.db_pool import get_pool
from services.database_factory import create_database_adapter
from services.batch_task_service import BatchTaskService
from services.transaction_manager import TransactionManager

# Import API routers
# DISABLED: agent_api requires langchain dependencies that need to be fixed
# from api.agent_api import create_agent_api
from api.routes import documents, products
from api.routes.error_codes import router as error_codes_router
from api.routes.videos import router as videos_router
from api.routes.images import router as images_router
from api.routes.batch import router as batch_router
from api.routes.search import router as search_router
from api.routes.api_keys import router as api_keys_router
from api.routes.dashboard import router as dashboard_router
from api import websocket as websocket_api
from services.metrics_service import MetricsService
from services.alert_service import AlertService
from services.performance_service import PerformanceCollector
from processors.env_loader import load_all_env_files
from config.security_config import get_security_config, get_cors_config
from slowapi.errors import RateLimitExceeded

# Load consolidated environment configuration
project_root = Path(__file__).parent.parent.parent
load_all_env_files(project_root)

# Security configuration
security_config = get_security_config()
cors_config = get_cors_config(security_config)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Default admin configuration
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_FIRST_NAME = os.getenv("DEFAULT_ADMIN_FIRST_NAME", "System")
DEFAULT_ADMIN_LAST_NAME = os.getenv("DEFAULT_ADMIN_LAST_NAME", "Administrator")

# Initialize FastAPI with security settings
app = FastAPI(
    title="KRAI Processing Pipeline API",
    description="Document processing pipeline with monitoring and management",
    version="2.0.0",
    docs_url=None,  # Disable default docs to add auth
    redoc_url=None,  # Disable default redoc to add auth
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
    expose_headers=cors_config["expose_headers"],
    max_age=cors_config["max_age"],
)

# API key validation (must run before rate limiting)
app.add_middleware(APIKeyValidationMiddleware)

# IP blacklist/whitelist enforcement
app.add_middleware(IPFilterMiddleware)

# Request validation middleware
app.add_middleware(RequestValidationMiddleware)

# Rate limit configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

# Import validation error handling
from api.validation_error_codes import ValidationErrorCode, create_validation_error_response

# Custom Pydantic validation exception handlers
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle FastAPI request validation errors with detailed field-level context.
    
    Extracts field-level errors from Pydantic validation and returns a standardized
    error response with error codes and contextual information.
    """
    field_errors = []
    missing_fields = []
    
    for error in exc.errors():
        # Extract field path (e.g., "body.email" or "query.page")
        field_path = ".".join(str(loc) for loc in error["loc"])
        
        # Extract error details
        error_type = error["type"]
        message = error["msg"]
        
        # Extract constraints from context if available
        constraints = {}
        ctx = error.get("ctx", {})
        
        # Common constraint types
        if "limit_value" in ctx:
            constraints["max_length"] = ctx["limit_value"]
        if "min_length" in ctx:
            constraints["min_length"] = ctx["min_length"]
        if "ge" in ctx:
            constraints["ge"] = ctx["ge"]
        if "le" in ctx:
            constraints["le"] = ctx["le"]
        if "gt" in ctx:
            constraints["gt"] = ctx["gt"]
        if "lt" in ctx:
            constraints["lt"] = ctx["lt"]
        if "pattern" in ctx:
            constraints["pattern"] = ctx["pattern"]
        
        # Derive expected type/constraint from schema or error context
        expected = None
        if "expected_type" in ctx:
            expected = ctx["expected_type"]
        elif "pattern" in ctx:
            expected = f"string matching pattern: {ctx['pattern']}"
        elif "ge" in ctx and "le" in ctx:
            expected = f"number between {ctx['ge']} and {ctx['le']}"
        elif "ge" in ctx:
            expected = f"number >= {ctx['ge']}"
        elif "le" in ctx:
            expected = f"number <= {ctx['le']}"
        elif "limit_value" in ctx:
            expected = f"string with max length {ctx['limit_value']}"
        elif "min_length" in ctx:
            expected = f"string with min length {ctx['min_length']}"
        elif "allowed" in ctx:
            expected = ctx["allowed"]
        elif error_type.startswith("type_error"):
            # Extract expected type from error type (e.g., "type_error.integer" -> "integer")
            expected = error_type.split(".")[-1] if "." in error_type else "valid type"
        
        # Extract received value from exc.body or error input if available
        received = None
        try:
            # Try to get the actual value from the request body
            if hasattr(exc, "body") and exc.body:
                import json
                body_data = json.loads(exc.body) if isinstance(exc.body, (str, bytes)) else exc.body
                # Navigate to the field using the location path
                field_parts = [str(loc) for loc in error["loc"] if str(loc) not in ["body", "query", "path", "header"]]
                current = body_data
                for part in field_parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        break
                if current != body_data:
                    received = current
        except Exception:
            pass
        
        # Fallback to input from error context
        if received is None and "input" in error:
            received = error["input"]
        
        # Check if this is a missing field error
        if error_type == "value_error.missing" or error_type == "missing":
            # Extract location (body, query, path, header)
            location = error["loc"][0] if error["loc"] else "unknown"
            field_name = error["loc"][-1] if len(error["loc"]) > 1 else "unknown"
            
            # Collect missing field instead of returning immediately
            missing_fields.append({
                "field": str(field_name),
                "location": str(location),
                "constraints": constraints if constraints else None
            })
            continue
        
        # Build field error with expected/received context
        field_error = {
            "field": field_path,
            "type": error_type,
            "message": message,
            "constraints": constraints if constraints else None
        }
        
        # Add expected/received context when available
        if expected is not None:
            field_error["expected"] = expected
        if received is not None:
            field_error["received"] = received
        
        field_errors.append(field_error)
    
    # If we have missing fields, return them all in a single response
    if missing_fields:
        if len(missing_fields) == 1:
            # Single missing field - use original format for backward compatibility
            missing = missing_fields[0]
            return create_validation_error_response(
                error_code=ValidationErrorCode.MISSING_REQUIRED_FIELD,
                detail=f"Required field '{missing['field']}' is missing from request {missing['location']}. Please provide this field.",
                context=missing,
                status_code=422
            )
        else:
            # Multiple missing fields - return all in context
            field_names = [f["field"] for f in missing_fields]
            return create_validation_error_response(
                error_code=ValidationErrorCode.MISSING_REQUIRED_FIELD,
                detail=f"Required fields are missing from request: {', '.join(field_names)}. Please provide all required fields.",
                context={"fields": missing_fields},
                status_code=422
            )
    
    # Return standardized error response for field validation errors
    error_count = len(field_errors)
    detail = f"Request validation failed for {error_count} field(s). Please check the field errors in context."
    
    return create_validation_error_response(
        error_code=ValidationErrorCode.FIELD_VALIDATION_ERROR,
        detail=detail,
        context={"fields": field_errors},
        status_code=422
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle direct Pydantic validation errors with detailed field-level context.
    
    Similar to RequestValidationError handler but for direct Pydantic model validation.
    """
    field_errors = []
    
    for error in exc.errors():
        # Extract field path
        field_path = ".".join(str(loc) for loc in error["loc"])
        
        # Extract error details
        error_type = error["type"]
        message = error["msg"]
        
        # Extract constraints from context
        constraints = {}
        ctx = error.get("ctx", {})
        
        if "limit_value" in ctx:
            constraints["max_length"] = ctx["limit_value"]
        if "min_length" in ctx:
            constraints["min_length"] = ctx["min_length"]
        if "ge" in ctx:
            constraints["ge"] = ctx["ge"]
        if "le" in ctx:
            constraints["le"] = ctx["le"]
        if "gt" in ctx:
            constraints["gt"] = ctx["gt"]
        if "lt" in ctx:
            constraints["lt"] = ctx["lt"]
        if "pattern" in ctx:
            constraints["pattern"] = ctx["pattern"]
        
        # Derive expected type/constraint from schema or error context
        expected = None
        if "expected_type" in ctx:
            expected = ctx["expected_type"]
        elif "pattern" in ctx:
            expected = f"string matching pattern: {ctx['pattern']}"
        elif "ge" in ctx and "le" in ctx:
            expected = f"number between {ctx['ge']} and {ctx['le']}"
        elif "ge" in ctx:
            expected = f"number >= {ctx['ge']}"
        elif "le" in ctx:
            expected = f"number <= {ctx['le']}"
        elif "limit_value" in ctx:
            expected = f"string with max length {ctx['limit_value']}"
        elif "min_length" in ctx:
            expected = f"string with min length {ctx['min_length']}"
        elif "allowed" in ctx:
            expected = ctx["allowed"]
        elif error_type.startswith("type_error"):
            # Extract expected type from error type (e.g., "type_error.integer" -> "integer")
            expected = error_type.split(".")[-1] if "." in error_type else "valid type"
        
        # Extract received value from error input if available
        received = None
        if "input" in error:
            received = error["input"]
        
        # Build field error with expected/received context
        field_error = {
            "field": field_path,
            "type": error_type,
            "message": message,
            "constraints": constraints if constraints else None
        }
        
        # Add expected/received context when available
        if expected is not None:
            field_error["expected"] = expected
        if received is not None:
            field_error["received"] = received
        
        field_errors.append(field_error)
    
    # Return standardized error response
    error_count = len(field_errors)
    detail = f"Validation failed for {error_count} field(s). Please check the field errors in context."
    
    return create_validation_error_response(
        error_code=ValidationErrorCode.FIELD_VALIDATION_ERROR,
        detail=detail,
        context={"fields": field_errors},
        status_code=422
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = security_config.CSP_POLICY
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    if request.url.scheme == "https":
        hsts_value = f"max-age={security_config.HSTS_MAX_AGE}"
        if security_config.HSTS_INCLUDE_SUBDOMAINS:
            hsts_value += "; includeSubDomains"
        if security_config.HSTS_PRELOAD:
            hsts_value += "; preload"
        response.headers["Strict-Transport-Security"] = hsts_value

    return response

security_scheme = HTTPBearer(auto_error=False)

# Global state
# Connection pool is managed by db_pool.get_pool()
upload_processor = None
document_processor = None
agent_app = None
auth_service: AuthService | None = None
batch_task_service: BatchTaskService | None = None
transaction_manager: TransactionManager | None = None
metrics_service: MetricsService | None = None
alert_service: AlertService | None = None
performance_collector: PerformanceCollector | None = None
websocket_manager: websocket_api.WebSocketManager | None = None


# === AUTH SERVICE INITIALIZATION ===

async def ensure_auth_service() -> AuthService:
    """Ensure the singleton AuthService is available and registered."""
    global auth_service
    if auth_service is None:
        # Use database pool for authentication
        auth_service = await create_and_initialize_auth_service()
    return auth_service


# === DEPENDENCY INJECTION ===


async def get_database_pool():
    """Provide shared asyncpg connection pool."""
    return await get_pool()


async def get_upload_processor():
    """Get Upload Processor instance"""
    global upload_processor
    if upload_processor is None:
        # UploadProcessor will be refactored to use pool directly
        pool = await get_pool()
        return UploadProcessor(
            pool=pool,
            stage_tracker=None
        )
    return upload_processor


async def get_agent_app():
    """Get Agent API app"""
    # DISABLED: agent_api requires langchain dependencies
    # global agent_app
    # if agent_app is None:
    #     pool = await get_pool()
    #     agent_app = create_agent_api(pool)
    # return agent_app
    raise HTTPException(status_code=503, detail="Agent API temporarily disabled")


async def get_batch_task_service() -> BatchTaskService:
    """Return singleton BatchTaskService."""

    global batch_task_service
    if batch_task_service is None:
        pool = await get_pool()
        batch_task_service = BatchTaskService(pool)
    return batch_task_service


async def get_transaction_manager() -> TransactionManager:
    """Return singleton TransactionManager."""

    global transaction_manager
    if transaction_manager is None:
        pool = await get_pool()
        transaction_manager = TransactionManager(pool)
    return transaction_manager


async def get_metrics_service() -> MetricsService:
    """Return singleton MetricsService. Uses DatabaseAdapter for StageTracker and same connection source for metrics."""
    global metrics_service
    if metrics_service is None:
        adapter = create_database_adapter()
        await adapter.connect()
        stage_tracker = StageTracker(adapter)
        pool = getattr(adapter, 'pg_pool', None) or await get_pool()
        metrics_service = MetricsService(pool, stage_tracker)
    return metrics_service


async def get_alert_service() -> AlertService:
    """Return singleton AlertService."""
    global alert_service
    if alert_service is None:
        # TODO: Replace with direct PostgreSQL connection
        # adapter = await get_database_adapter()
        metrics_svc = await get_metrics_service()
        # alert_service = AlertService(adapter, metrics_svc)
        alert_service = AlertService(None, metrics_svc)  # Temporary fix
    return alert_service


async def get_performance_collector() -> PerformanceCollector:
    """Return singleton PerformanceCollector."""
    global performance_collector
    if performance_collector is None:
        # TODO: Replace with direct PostgreSQL connection
        # adapter = await get_database_adapter()
        # performance_collector = PerformanceCollector(adapter, logger)
        performance_collector = PerformanceCollector(None, logger)  # Temporary fix
    return performance_collector


def get_websocket_manager() -> websocket_api.WebSocketManager:
    """Return singleton WebSocketManager."""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = websocket_api.WebSocketManager()
    return websocket_manager

# TODO: Replace database adapter functions with direct PostgreSQL connections


# === PYDANTIC MODELS ===

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, Any]


class UploadResponse(BaseModel):
    success: bool
    document_id: Optional[str]
    status: str
    message: str
    metadata: Optional[Dict[str, Any]]


class ProcessingStatus(BaseModel):
    document_id: str
    status: str
    current_stage: str
    progress: float
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    stage_status: Optional[Dict[str, Any]] = None  # Detailed per-stage status


class StageStatistics(BaseModel):
    stage_name: str
    total_documents: int
    successful: int
    failed: int
    pending: int
    average_processing_time: Optional[float]


# === AUTHENTICATION ===

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Custom docs endpoints with auth
@app.get("/docs", include_in_schema=False)
async def get_documentation(request: Request):
    """Custom Swagger UI secured by bearer authentication."""
    credentials = await security_scheme(request)
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    ensure_auth_service()
    claims = await AuthMiddleware(ensure_auth_service())(request, allow_expired=True)
    if claims.get("role") not in {"admin", "editor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title,
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(request: Request):
    """Custom ReDoc secured by bearer authentication."""
    credentials = await security_scheme(request)
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    ensure_auth_service()
    claims = await AuthMiddleware(ensure_auth_service())(request, allow_expired=True)
    if claims.get("role") not in {"admin", "editor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
        swagger_ui_parameters={"docExpansion": "none"},
        swagger_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )


# === HEALTH & STATUS ===

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "KRAI Processing Pipeline",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
@limiter.limit(rate_limit_health_dynamic)
async def health_check(request: Request):
    """
    Health check endpoint
    
    Checks:
    - API status
    - Database connectivity
    - Ollama status
    - Storage access
    """
    services = {
        "api": {"status": "healthy", "message": "API is running"},
        "database": {"status": "unknown", "message": ""},
        "ollama": {"status": "unknown", "message": ""},
        "storage": {"status": "unknown", "message": ""},
        "batch_operations": {"status": "unknown", "message": ""},
    }
    
    # Check database
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["database"] = {
            "status": "healthy",
            "message": "Database connected"
        }
    except Exception as e:
        services["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
    
    # Check Ollama
    try:
        import requests
        response = requests.get(
            f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get('models', [])
            services["ollama"] = {
                "status": "healthy",
                "message": f"{len(models)} models available"
            }
        else:
            services["ollama"] = {
                "status": "unhealthy",
                "message": "Ollama not responding"
            }
    except Exception as e:
        services["ollama"] = {
            "status": "unhealthy",
            "message": f"Ollama error: {str(e)}"
        }
    
    # Check storage (Object Storage)
    try:
        # Test object storage credentials exist
        storage_key = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
        storage_secret = os.getenv("OBJECT_STORAGE_SECRET_KEY")
        storage_type = os.getenv("OBJECT_STORAGE_TYPE", "s3")
        
        if storage_key and storage_secret:
            services["storage"] = {
                "status": "configured",
                "message": f"Object storage credentials present ({storage_type})",
                "type": storage_type
            }
        else:
            services["storage"] = {
                "status": "unconfigured",
                "message": "Object storage credentials missing"
            }
    except Exception as e:
        services["storage"] = {
            "status": "error",
            "message": f"Storage error: {str(e)}"
        }

    # Batch operations health
    try:
        task_service = await get_batch_task_service()
        services["batch_operations"] = {
            "status": "healthy",
            "message": "Task service initialized",
            "transaction_support": transaction_support,
        }
    except Exception as exc:
        services["batch_operations"] = {
            "status": "unhealthy",
            "message": f"Batch services unavailable: {exc}",
            "transaction_support": transaction_support,
        }
    
    # Monitoring services health
    try:
        metrics_svc = await get_metrics_service()
        alert_svc = await get_alert_service()
        ws_mgr = get_websocket_manager()
        
        services["monitoring"] = {
            "status": "healthy",
            "message": "Monitoring services active",
            "metrics_service": "initialized",
            "alert_service": "initialized",
            "websocket_connections": len(ws_mgr.active_connections),
        }
    except Exception as exc:
        services["monitoring"] = {
            "status": "unhealthy",
            "message": f"Monitoring services unavailable: {exc}",
            "websocket_connections": 0,
        }
    
    # Overall status
    overall_status = "healthy"
    if any(s["status"] == "unhealthy" for s in services.values()):
        overall_status = "unhealthy"
    elif any(s["status"] == "unknown" for s in services.values()):
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }


# === UPLOAD ENDPOINTS ===

@app.post("/upload", response_model=UploadResponse, tags=["Upload"])
@limiter.limit(rate_limit_standard_dynamic)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = "service_manual",
    force_reprocess: bool = False,
    processor: UploadProcessor = Depends(get_upload_processor),
    current_user: dict = Depends(require_permission('documents:write'))
):
    """
    Upload a document for processing
    
    Args:
        file: PDF file to upload
        document_type: Type of document (service_manual, parts_catalog, user_guide)
        force_reprocess: Force reprocessing if document already exists
        
    Returns:
        Upload result with document ID and status
    """
    # Save uploaded file temporarily
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / file.filename
    
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process upload
        result = processor.process_upload(
            file_path=temp_path,
            document_type=document_type,
            force_reprocess=force_reprocess
        )
        
        return UploadResponse(
            success=result['success'],
            document_id=result.get('document_id'),
            status=result.get('status', 'error'),
            message="Upload successful" if result['success'] else result.get('error', 'Upload failed'),
            metadata=result.get('metadata')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


@app.on_event("startup")
async def startup_events():
    """Initialize shared services and verify default admin user."""
    service = await ensure_auth_service()
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")

    try:
        await service.ensure_default_admin(
            email=DEFAULT_ADMIN_EMAIL,
            username=DEFAULT_ADMIN_USERNAME,
            first_name=DEFAULT_ADMIN_FIRST_NAME,
            last_name=DEFAULT_ADMIN_LAST_NAME,
            password=admin_password
        )
    except AuthenticationError as exc:
        if "already exists" in str(exc):
            logger.info("Default admin user already exists: %s", exc)
        else:
            logger.error("Failed to ensure default admin user: %s", exc)
            raise

    pool = await get_pool()
    
    # Initialize db_pool in app.state for API key validation middleware
    app.state.db_pool = pool
    
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as exc:  # pragma: no cover - startup logging
        logger.warning("Database pool connection failed: %s", exc)

    await get_batch_task_service()
    await get_transaction_manager()
    logger.info("Batch services initialized with asyncpg pool")
    
    # Initialize monitoring services
    metrics_svc = await get_metrics_service()
    alert_svc = await get_alert_service()
    ws_manager = get_websocket_manager()
    
    # Start background tasks
    import asyncio
    asyncio.create_task(alert_svc.start_alert_monitoring())
    asyncio.create_task(websocket_api.start_periodic_broadcast(metrics_svc))
    
    logger.info("Monitoring services initialized (metrics, alerts, websocket)")
    logger.info(
        "Security: CORS origins=%s, Rate limiting=%s, Request validation=%s",
        cors_config["allow_origins"],
        security_config.RATE_LIMIT_ENABLED,
        security_config.REQUEST_VALIDATION_ENABLED,
    )


@app.post("/upload/directory", tags=["Upload"])
@limiter.limit(rate_limit_upload_dynamic)
async def upload_directory(
    request: Request,
    directory_path: str,
    document_type: str = "service_manual",
    recursive: bool = False,
    force_reprocess: bool = False,
    current_user: dict = Depends(require_permission('documents:write'))
    # TODO: Replace with direct PostgreSQL connection
    # adapter: DatabaseAdapter = Depends(get_database_adapter)
):
    """
    Upload all PDFs from a directory
    
    Args:
        directory_path: Path to directory containing PDFs
        document_type: Type of documents
        recursive: Scan subdirectories
        force_reprocess: Force reprocessing existing documents
        
    Returns:
        Batch upload results
    """
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    # BatchUploadProcessor accepts adapter
    batch_processor = BatchUploadProcessor(adapter, max_file_size_mb=500)
    
    results = batch_processor.process_directory(
        directory=directory,
        document_type=document_type,
        recursive=recursive,
        force_reprocess=force_reprocess
    )
    
    return results


# === PROCESSING STATUS ===

@app.get("/status/{document_id}", response_model=ProcessingStatus, tags=["Status"])
@limiter.limit(rate_limit_standard_dynamic)
async def get_document_status(
    request: Request,
    document_id: str,
    current_user: dict = Depends(require_permission('documents:read'))
    # TODO: Replace with direct PostgreSQL connection
    # adapter: DatabaseAdapter = Depends(get_database_adapter)
):
    """
    Get processing status for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Current processing status
    """
    try:
        # Get document using adapter
        doc = await adapter.get_document(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Return proper ProcessingStatus model
        # For now, use basic status from document processing_status field
        processing_status = doc.get('processing_status', 'unknown')
        
        return ProcessingStatus(
            document_id=document_id,
            status=processing_status,
            current_stage='unknown',  # Stage tracking not available in PostgreSQL-only mode
            progress=100.0 if processing_status == 'completed' else 0.0,
            started_at=doc.get('created_at'),
            completed_at=doc.get('updated_at') if processing_status == 'completed' else None,
            error=None,
            stage_status={}  # Empty stage status for now
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/pipeline", tags=["Status"])
async def get_pipeline_status(
    current_user: dict = Depends(require_permission('documents:read'))
    # TODO: Replace with direct PostgreSQL connection
    # adapter: DatabaseAdapter = Depends(get_database_adapter)
):
    """
    Get overall pipeline status
    
    Returns:
        Statistics for all pipeline stages
    """
    try:
        # TODO: Replace with direct PostgreSQL connection
        # Get all documents using direct table
        # documents = await adapter.execute_query(
        #     "SELECT id, filename, processing_status, created_at FROM krai_core.documents",
        #     []
        # )
        
        # Get queue
        # queue = await adapter.execute_query(
        #     "SELECT * FROM krai_core.processing_queue",
        #     []
        # )
        
        # TODO: Replace with direct PostgreSQL connection
        # For now, return empty stats
        stats = {
            "total_documents": 0,
            "in_queue": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "by_task_type": {}
        }
        
        # Count by task_type from queue
        # task_types = ["text_extraction", "image_processing", "classification",
        #               "metadata_extraction", "storage", "embedding", "search"]
        # 
        # for task_type in task_types:
        #     count = len([q for q in queue if q.get("task_type") == task_type])
        #     stats["by_task_type"][task_type] = count
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === LOGS & MONITORING ===

@app.get("/logs/{document_id}", tags=["Monitoring"])
async def get_document_logs(
    document_id: str,
    current_user: dict = Depends(require_permission('monitoring:read'))
    # TODO: Replace with direct PostgreSQL connection
    # adapter: DatabaseAdapter = Depends(get_database_adapter)
):
    """
    Get processing logs for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Processing logs
    """
    try:
        # TODO: Replace with direct PostgreSQL connection
        # Get audit logs using adapter
        # logs = await adapter.execute_query(
        #     """SELECT * FROM krai_core.audit_log 
        #        WHERE entity_type = %s AND entity_id = %s 
        #        ORDER BY created_at DESC 
        #        LIMIT 100""",
        #     ["document", document_id]
        # )
        
        # For now, return empty logs
        logs = []
        
        return {
            "document_id": document_id,
            "log_count": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stages/statistics", tags=["Monitoring"])
async def get_stage_statistics(
    current_user: dict = Depends(require_permission('monitoring:read'))
):
    """
    Get statistics for all processing stages
    
    Returns:
        Stage-wise statistics including pending, processing, completed counts
    """
    try:
        # Stage statistics require PostgreSQL functions
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stage statistics require PostgreSQL functions (not implemented yet)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/system", tags=["Monitoring"])
async def get_system_metrics(
    current_user: dict = Depends(require_permission('monitoring:read'))
    # TODO: Replace with direct PostgreSQL connection
    # adapter: DatabaseAdapter = Depends(get_database_adapter)
):
    """
    Get system performance metrics
    
    Returns:
        Performance statistics
    """
    try:
        # TODO: Replace with direct PostgreSQL connection
        # Get metrics from direct table
        # metrics = await adapter.execute_query(
        #     """SELECT timestamp, cpu_usage, memory_usage, disk_usage, query_count 
        #        FROM krai_system.system_metrics 
        #        ORDER BY timestamp DESC 
        #        LIMIT 1""",
        #     []
        # )
        
        # For now, return empty metrics
        metrics = None
        
        if metrics:
            return metrics[0]
        else:
            return {
                "message": "No metrics available yet",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


# Include API routes
from api.routes import auth as auth_routes
from api.routes import scraping
from api.routes import pipeline_errors
# Note: Auth routes and dashboard will need pool-based initialization
# Temporarily commented out until refactored
# auth_router = auth_routes.initialize_auth_routes(pool)
# app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(error_codes_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(api_keys_router, prefix="/api/v1")
app.include_router(images_router, prefix="/api/v1")
app.include_router(batch_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(scraping.router, prefix="/api/v1")
app.include_router(pipeline_errors.router, prefix="/api/v1")

# Mount Monitoring API
from api import monitoring_api
app.include_router(monitoring_api.router, prefix="/api/v1/monitoring", tags=["Monitoring"])

# Mount WebSocket API
app.include_router(websocket_api.router, tags=["WebSocket"])

# Add Agent API endpoints directly
@app.get("/agent/health")
async def agent_health():
    """Agent health check endpoint"""
    return {
        "status": "healthy",
        "agent": "KRAI AI Agent",
        "version": "1.0.0"
    }

@app.post("/agent/chat")
async def agent_chat(message: dict):
    """Agent chat endpoint"""
    return {
        "response": "Agent chat endpoint is working!",
        "message": message.get("message", ""),
        "agent": "KRAI AI Agent"
    }

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Secure all endpoints by default
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if method.get("tags") != ["authentication"]:
                method["security"] = [{"HTTPBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
