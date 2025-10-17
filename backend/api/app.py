"""
KRAI Processing Pipeline API

FastAPI app for monitoring, managing, and controlling the document processing pipeline.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
from supabase import create_client
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.upload_processor import UploadProcessor, BatchUploadProcessor
from processors.document_processor import DocumentProcessor
from processors.stage_tracker import StageTracker

# Import API routers
from api.agent_api import create_agent_api

# Load ALL environment files (they are in project root)
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env.ai')
load_dotenv(project_root / '.env.database')
load_dotenv(project_root / '.env.external')
load_dotenv(project_root / '.env.pipeline')
load_dotenv(project_root / '.env.storage')

# Initialize FastAPI
app = FastAPI(
    title="KRAI Processing Pipeline API",
    description="Document processing pipeline with monitoring and management",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
supabase_client = None
upload_processor = None
document_processor = None
agent_app = None


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


# === HEALTH & STATUS ===

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "service": "KRAI Processing Pipeline API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(supabase=Depends(get_supabase)):
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
        "storage": {"status": "unknown", "message": ""}
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
    
    # Check storage (R2)
    try:
        # Test R2 credentials exist
        if os.getenv("R2_ACCESS_KEY_ID") and os.getenv("R2_SECRET_ACCESS_KEY"):
            services["storage"] = {
                "status": "configured",
                "message": "R2 credentials present"
            }
        else:
            services["storage"] = {
                "status": "unconfigured",
                "message": "R2 credentials missing"
            }
    except Exception as e:
        services["storage"] = {
            "status": "error",
            "message": f"Storage error: {str(e)}"
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
    processor: UploadProcessor = Depends(get_upload_processor)
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


@app.post("/upload/directory", tags=["Upload"])
async def upload_directory(
    directory_path: str,
    document_type: str = "service_manual",
    recursive: bool = False,
    force_reprocess: bool = False,
    supabase=Depends(get_supabase)
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
async def get_document_status(document_id: str, supabase=Depends(get_supabase)):
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


@app.get("/status", tags=["Status"])
async def get_pipeline_status(supabase=Depends(get_supabase)):
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
async def get_document_logs(document_id: str, supabase=Depends(get_supabase)):
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


@app.get("/stages/statistics", tags=["Monitoring"])
async def get_stage_statistics(supabase=Depends(get_supabase)):
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


@app.get("/metrics", tags=["Monitoring"])
async def get_system_metrics(supabase=Depends(get_supabase)):
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


# Mount Agent API
agent_api = get_agent_app()
app.mount("/agent", agent_api)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
