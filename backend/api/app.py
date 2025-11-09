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
from supabase import create_client
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
from services.database_service import DatabaseService
from services.auth_service import AuthService, AuthenticationError
from services.supabase_adapter import SupabaseAdapter
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
from api import websocket as websocket_api
from services.metrics_service import MetricsService
from services.alert_service import AlertService
from processors.env_loader import load_all_env_files

# Load consolidated environment configuration
project_root = Path(__file__).parent.parent.parent
load_all_env_files(project_root)

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

# CORS configuration
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://krai.example.com",
]

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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
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
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    
    return response

security_scheme = HTTPBearer(auto_error=False)

# Global state
supabase_client = None
supabase_adapter: SupabaseAdapter | None = None
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
        service = create_auth_service()
        set_auth_service(service)
        auth_service = service
    return auth_service


# === DEPENDENCY INJECTION ===

def get_supabase():
    """Get Supabase client"""
    global supabase_client
    if supabase_client is None:
        supabase_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
    return supabase_client


def get_supabase_adapter() -> SupabaseAdapter:
    """Provide shared SupabaseAdapter instance."""

    global supabase_adapter
    if supabase_adapter is None:
        database_service = DatabaseService(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            postgres_url=os.getenv("DATABASE_CONNECTION_URL") or os.getenv("POSTGRES_URL"),
        )
        supabase_adapter = database_service
    return supabase_adapter


def get_upload_processor():
    """Get Upload Processor instance"""
    global upload_processor
    if upload_processor is None:
        upload_processor = UploadProcessor(
            supabase_client=get_supabase(),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "500"))
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
        agent_app = create_agent_api(get_supabase())
    return agent_app


async def get_batch_task_service() -> BatchTaskService:
    """Return singleton BatchTaskService."""

    global batch_task_service
    if batch_task_service is None:
        adapter = get_supabase_adapter()
        batch_task_service = BatchTaskService(adapter)
    return batch_task_service


async def get_transaction_manager() -> TransactionManager:
    """Return singleton TransactionManager."""

    global transaction_manager
    if transaction_manager is None:
        adapter = get_supabase_adapter()
        transaction_manager = TransactionManager(adapter)
    return transaction_manager


async def get_metrics_service() -> MetricsService:
    """Return singleton MetricsService."""
    global metrics_service
    if metrics_service is None:
        adapter = get_supabase_adapter()
        # Import broadcast function for WebSocket integration
        from api.websocket import broadcast_stage_event
        stage_tracker = StageTracker(get_supabase(), websocket_callback=broadcast_stage_event)
        metrics_service = MetricsService(adapter, stage_tracker)
    return metrics_service


async def get_alert_service() -> AlertService:
    """Return singleton AlertService."""
    global alert_service
    if alert_service is None:
        adapter = get_supabase_adapter()
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
async def health_check(
    supabase=Depends(get_supabase),
):
    """
    Health check endpoint
    
    Checks:
    - API status
    - Database connectivity
    - Ollama status
    - Storage access
    """
    adapter = get_supabase_adapter()
    transaction_support = adapter.pg_pool is not None

    services = {
        "api": {"status": "healthy", "message": "API is running"},
        "database": {"status": "unknown", "message": ""},
        "ollama": {"status": "unknown", "message": ""},
        "storage": {"status": "unknown", "message": ""},
        "batch_operations": {"status": "unknown", "message": ""},
    }
    
    # Check database
    try:
        result = supabase.table("vw_documents").select("id").limit(1).execute()
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

    adapter = get_supabase_adapter()
    if hasattr(adapter, "connect"):
        try:
            await adapter.connect()
        except Exception as exc:  # pragma: no cover - startup logging
            logger.warning("Supabase adapter connection failed: %s", exc)

    await get_batch_task_service()
    await get_transaction_manager()
    logger.info("Batch services initialized (transaction support=%s)", adapter.pg_pool is not None)
    
    # Initialize monitoring services
    metrics_svc = await get_metrics_service()
    alert_svc = await get_alert_service()
    ws_manager = get_websocket_manager()
    
    # Start background tasks
    import asyncio
    asyncio.create_task(alert_svc.start_alert_monitoring())
    asyncio.create_task(websocket_api.start_periodic_broadcast(metrics_svc))
    
    logger.info("Monitoring services initialized (metrics, alerts, websocket)")


@app.post("/upload/directory", tags=["Upload"])
async def upload_directory(
    directory_path: str,
    document_type: str = "service_manual",
    recursive: bool = False,
    force_reprocess: bool = False,
    supabase=Depends(get_supabase),
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
    
    batch_processor = BatchUploadProcessor(supabase, max_file_size_mb=500)
    
    results = batch_processor.process_directory(
        directory=directory,
        document_type=document_type,
        recursive=recursive,
        force_reprocess=force_reprocess
    )
    
    return results


# === PROCESSING STATUS ===

@app.get("/status/{document_id}", response_model=ProcessingStatus, tags=["Status"])
async def get_document_status(
    document_id: str,
    supabase=Depends(get_supabase),
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
        # Get document
        doc_result = supabase.table("vw_documents") \
            .select("*") \
            .eq("id", document_id) \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = doc_result.data[0]
        
        # Get stage status using StageTracker
        tracker = StageTracker(supabase)
        
        current_stage = tracker.get_current_stage(document_id)
        progress = tracker.get_progress(document_id)
        stage_status = tracker.get_stage_status(document_id)
        
        # Get timestamps
        started_at = doc.get("created_at")
        completed_at = None
        error = None
        
        # Check if all stages completed
        if stage_status and current_stage == "completed":
            # Get last stage completion time
            for stage_name in reversed(StageTracker.STAGES):
                stage_data = stage_status.get(stage_name, {})
                if stage_data.get("completed_at"):
                    completed_at = stage_data["completed_at"]
                    break
        
        # Check for any errors
        if stage_status:
            for stage_name, stage_data in stage_status.items():
                if stage_data.get("status") == "failed":
                    error = stage_data.get("error")
                    break
        
        return ProcessingStatus(
            document_id=document_id,
            status=doc.get("processing_status", "unknown"),
            current_stage=current_stage,
            progress=progress,
            started_at=started_at,
            completed_at=completed_at,
            error=error,
            stage_status=stage_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/pipeline", response_model=List[StageStatistics], tags=["Status"])
async def get_pipeline_status(
    supabase=Depends(get_supabase),
    current_user: dict = Depends(require_permission('documents:read'))
):
    """
    Get overall pipeline status
    
    Returns:
        Statistics for all pipeline stages
    """
    try:
        # Get all documents
        documents = supabase.table("vw_documents").select("*").execute()
        
        # Get queue
        queue = supabase.table("processing_queue").select("*").execute()
        
        stats = {
            "total_documents": len(documents.data),
            "in_queue": len([q for q in queue.data if q.get("status") == "pending"]),
            "processing": len([q for q in queue.data if q.get("status") == "processing"]),
            "completed": len([d for d in documents.data if d.get("processing_status") == "completed"]),
            "failed": len([d for d in documents.data if d.get("processing_status") == "failed"]),
            "by_task_type": {}
        }
        
        # Count by task_type from queue
        task_types = ["text_extraction", "image_processing", "classification",
                      "metadata_extraction", "storage", "embedding", "search"]
        
        for task_type in task_types:
            count = len([q for q in queue.data if q.get("task_type") == task_type])
            stats["by_task_type"][task_type] = count
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === LOGS & MONITORING ===

@app.get("/logs/{document_id}", tags=["Monitoring"])
async def get_document_logs(
    document_id: str,
    supabase=Depends(get_supabase),
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
        # Get audit logs
        logs = supabase.table("audit_log") \
            .select("*") \
            .eq("entity_type", "document") \
            .eq("entity_id", document_id) \
            .order("created_at", desc=True) \
            .limit(100) \
            .execute()
        
        return {
            "document_id": document_id,
            "log_count": len(logs.data),
            "logs": logs.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stages/statistics", response_model=List[StageStatistics], tags=["Monitoring"])
async def get_stage_statistics(
    supabase=Depends(get_supabase),
    current_user: dict = Depends(require_permission('monitoring:read'))
):
    """
    Get statistics for all processing stages
    
    Returns:
        Stage-wise statistics including pending, processing, completed counts
    """
    try:
        tracker = StageTracker(supabase)
        stats = tracker.get_statistics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stages": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/system", tags=["Monitoring"])
async def get_system_metrics(
    supabase=Depends(get_supabase),
    current_user: dict = Depends(require_permission('monitoring:read'))
):
    """
    Get system performance metrics
    
    Returns:
        Performance statistics
    """
    try:
        # Get metrics from database
        metrics = supabase.table("vw_system_metrics") \
            .select("*") \
            .order("timestamp", desc=True) \
            .limit(1) \
            .execute()
        
        if metrics.data:
            return metrics.data[0]
        else:
            return {
                "message": "No metrics available yet",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Include API routes
from api.routes import auth as auth_routes

# Initialize auth routes
auth_router = auth_routes.initialize_auth_routes(DatabaseService())
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(error_codes_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
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
