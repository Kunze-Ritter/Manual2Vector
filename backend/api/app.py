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
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import os
import secrets
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.upload_processor import UploadProcessor, BatchUploadProcessor
from processors.document_processor import DocumentProcessor
from processors.stage_tracker import StageTracker
from api.dependencies.auth import set_auth_service
from api.dependencies.auth_factory import create_auth_service
from api.middleware.auth_middleware import AuthMiddleware, require_permission
from api.middleware.rate_limit_middleware import (
    IPFilterMiddleware,
    limiter,
    rate_limit_health,
    rate_limit_search,
    rate_limit_standard,
    rate_limit_upload,
    rate_limit_exception_handler,
)
from api.middleware.request_validation_middleware import RequestValidationMiddleware
from services.database_service import DatabaseService
from services.auth_service import AuthService, AuthenticationError
from services.database_adapter import DatabaseAdapter
from services.database_factory import create_database_adapter
from services.batch_task_service import BatchTaskService
from services.transaction_manager import TransactionManager

# Import API routers
from api.agent_api import create_agent_api
from api.routes import documents, products
from api.routes.error_codes import router as error_codes_router
from api.routes.videos import router as videos_router
from api.routes.images import router as images_router
from api.routes.batch import router as batch_router
from api.routes.search import router as search_router
from api.routes.api_keys import router as api_keys_router
from api import websocket as websocket_api
from services.metrics_service import MetricsService
from services.alert_service import AlertService
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

# IP blacklist/whitelist enforcement
app.add_middleware(IPFilterMiddleware)

# Request validation middleware
app.add_middleware(RequestValidationMiddleware)

# Rate limit configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

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
supabase_adapter: DatabaseAdapter | None = None  # Now holds DatabaseAdapter (unified interface)
upload_processor = None
document_processor = None
agent_app = None
auth_service: AuthService | None = None
batch_task_service: BatchTaskService | None = None
transaction_manager: TransactionManager | None = None
metrics_service: MetricsService | None = None
alert_service: AlertService | None = None
websocket_manager: websocket_api.WebSocketManager | None = None


# === AUTH SERVICE INITIALIZATION ===

def ensure_auth_service() -> AuthService:
    """Ensure the singleton AuthService is available and registered."""
    global auth_service
    if auth_service is None:
        # Use database adapter for authentication
        adapter = get_database_adapter()
        return create_auth_service(adapter)
    return auth_service


# === DEPENDENCY INJECTION ===


def get_database_adapter() -> DatabaseAdapter:
    """Provide shared DatabaseAdapter instance (singleton)."""
    global supabase_adapter
    if supabase_adapter is None:
        supabase_adapter = create_database_adapter()
    return supabase_adapter


def get_upload_processor():
    """Get Upload Processor instance"""
    global upload_processor
    if upload_processor is None:
        # UploadProcessor accepts DatabaseAdapter
        adapter = get_database_adapter()
        return UploadProcessor(
            adapter=adapter,
            stage_tracker=None  # StageTracker may need refactoring for PostgreSQL
        )
    return upload_processor


def get_document_processor():
    """Get Document Processor instance"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor(
            manufacturer="AUTO",
            use_llm=True,
            debug=False
        )
    return document_processor


def get_agent_app():
    """Get Agent API app"""
    global agent_app
    if agent_app is None:
        agent_app = create_agent_api(get_database_adapter())
    return agent_app


async def get_batch_task_service() -> BatchTaskService:
    """Return singleton BatchTaskService."""

    global batch_task_service
    if batch_task_service is None:
        adapter = get_database_adapter()
        batch_task_service = BatchTaskService(adapter)
    return batch_task_service


async def get_transaction_manager() -> TransactionManager:
    """Return singleton TransactionManager."""

    global transaction_manager
    if transaction_manager is None:
        adapter = get_database_adapter()
        transaction_manager = TransactionManager(adapter)
    return transaction_manager


async def get_metrics_service() -> MetricsService:
    """Return singleton MetricsService."""
    global metrics_service
    if metrics_service is None:
        adapter = get_database_adapter()
        stage_tracker = StageTracker(adapter)
        metrics_service = MetricsService(adapter, stage_tracker)
    return metrics_service


async def get_alert_service() -> AlertService:
    """Return singleton AlertService."""
    global alert_service
    if alert_service is None:
        adapter = get_database_adapter()
        metrics_svc = await get_metrics_service()
        alert_service = AlertService(adapter, metrics_svc)
    return alert_service


def get_websocket_manager() -> websocket_api.WebSocketManager:
    """Return singleton WebSocketManager."""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = websocket_api.WebSocketManager()
    return websocket_manager


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
@limiter.limit(rate_limit_health)
async def health_check(
    adapter: DatabaseAdapter = Depends(get_database_adapter),
):
    """
    Health check endpoint
    
    Checks:
    - API status
    - Database connectivity
    - Ollama status
    - Storage access
    """
    transaction_support = getattr(adapter, 'pg_pool', None) is not None

    services = {
        "api": {"status": "healthy", "message": "API is running"},
        "database": {"status": "unknown", "message": ""},
        "ollama": {"status": "unknown", "message": ""},
        "storage": {"status": "unknown", "message": ""},
        "batch_operations": {"status": "unknown", "message": ""},
    }
    
    # Check database
    try:
        # Use direct krai.documents table instead of view
        result = await adapter.execute_query(
            "SELECT id FROM krai_core.documents LIMIT 1",
            []
        )
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
        # Test object storage credentials exist with fallback to R2
        storage_key = os.getenv("OBJECT_STORAGE_ACCESS_KEY") or os.getenv("R2_ACCESS_KEY_ID")
        storage_secret = os.getenv("OBJECT_STORAGE_SECRET_KEY") or os.getenv("R2_SECRET_ACCESS_KEY")
        storage_type = os.getenv("OBJECT_STORAGE_TYPE", "r2")
        
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
@limiter.limit(rate_limit_standard)
async def upload_document(
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
    service = ensure_auth_service()
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
        logger.error("Failed to ensure default admin user: %s", exc)
        raise

    adapter = get_database_adapter()
    if hasattr(adapter, "connect"):
        try:
            await adapter.connect()
        except Exception as exc:  # pragma: no cover - startup logging
            logger.warning("Database adapter connection failed: %s", exc)

    await get_batch_task_service()
    await get_transaction_manager()
    logger.info("Batch services initialized (transaction support=%s)", getattr(adapter, 'pg_pool', None) is not None)
    
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
@limiter.limit(rate_limit_upload)
async def upload_directory(
    directory_path: str,
    document_type: str = "service_manual",
    recursive: bool = False,
    force_reprocess: bool = False,
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    current_user: dict = Depends(require_permission('documents:write'))
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
@limiter.limit(rate_limit_standard)
async def get_document_status(
    document_id: str,
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    current_user: dict = Depends(require_permission('documents:read'))
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
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    current_user: dict = Depends(require_permission('documents:read'))
):
    """
    Get overall pipeline status
    
    Returns:
        Statistics for all pipeline stages
    """
    try:
        # Get all documents using direct table
        documents = await adapter.execute_query(
            "SELECT id, filename, processing_status, created_at FROM krai_core.documents",
            []
        )
        
        # Get queue
        queue = await adapter.execute_query(
            "SELECT * FROM krai_core.processing_queue",
            []
        )
        
        stats = {
            "total_documents": len(documents),
            "in_queue": len([q for q in queue if q.get("status") == "pending"]),
            "processing": len([q for q in queue if q.get("status") == "processing"]),
            "completed": len([d for d in documents if d.get("processing_status") == "completed"]),
            "failed": len([d for d in documents if d.get("processing_status") == "failed"]),
            "by_task_type": {}
        }
        
        # Count by task_type from queue
        task_types = ["text_extraction", "image_processing", "classification",
                      "metadata_extraction", "storage", "embedding", "search"]
        
        for task_type in task_types:
            count = len([q for q in queue if q.get("task_type") == task_type])
            stats["by_task_type"][task_type] = count
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === LOGS & MONITORING ===

@app.get("/logs/{document_id}", tags=["Monitoring"])
async def get_document_logs(
    document_id: str,
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    current_user: dict = Depends(require_permission('monitoring:read'))
):
    """
    Get processing logs for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Processing logs
    """
    try:
        # Get audit logs using adapter
        logs = await adapter.execute_query(
            """SELECT * FROM krai_core.audit_log 
               WHERE entity_type = %s AND entity_id = %s 
               ORDER BY created_at DESC 
               LIMIT 100""",
            ["document", document_id]
        )
        
        return {
            "document_id": document_id,
            "log_count": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stages/statistics", tags=["Monitoring"])
async def get_stage_statistics(
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    current_user: dict = Depends(require_permission('monitoring:read'))
):
    """
    Get statistics for all processing stages
    
    Returns:
        Stage-wise statistics including pending, processing, completed counts
    """
    try:
        # Stage statistics require PostgreSQL equivalent of Supabase RPC
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
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    current_user: dict = Depends(require_permission('monitoring:read'))
):
    """
    Get system performance metrics
    
    Returns:
        Performance statistics
    """
    try:
        # Get metrics from direct table
        metrics = await adapter.execute_query(
            """SELECT timestamp, cpu_usage, memory_usage, disk_usage, query_count 
               FROM krai_system.system_metrics 
               ORDER BY timestamp DESC 
               LIMIT 1""",
            []
        )
        
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

# Initialize auth routes
auth_router = auth_routes.initialize_auth_routes(get_database_adapter())
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(error_codes_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(api_keys_router, prefix="/api/v1")
app.include_router(images_router, prefix="/api/v1")
app.include_router(batch_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")

# Mount Monitoring API
from api import monitoring_api
app.include_router(monitoring_api.router, prefix="/api/v1/monitoring", tags=["Monitoring"])

# Mount WebSocket API
app.include_router(websocket_api.router, tags=["WebSocket"])

# Mount Agent API
agent_api = get_agent_app()
app.mount("/agent", agent_api)

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
