"""
KR-AI-Engine Main Application
FastAPI application with all endpoints and services
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

# Load environment variables from multiple .env files
# Priority: Later files override earlier ones
try:
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Determine project root (parent of backend/)
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    
    # Load all .env files in priority order (later overrides earlier)
    env_files = [
        '.env',           # Base config (lowest priority)
        '.env.database',  # Database credentials
        '.env.storage',   # R2/Storage config
        '.env.external',  # External APIs (YouTube, etc.)
        '.env.pipeline',  # Pipeline settings
        '.env.ai',        # AI settings (LLM_MAX_PAGES, OLLAMA models)
    ]
    
    loaded_count = 0
    for env_file in env_files:
        env_path = project_root / env_file
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ Loaded: {env_file}")
            loaded_count += 1
    
    if loaded_count == 0:
        print("⚠️  No .env files found - using system environment variables")
    else:
        print(f"✅ Loaded {loaded_count} configuration file(s)")
    
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

# Import services
from backend.services.database_service import DatabaseService
from backend.services.object_storage_service import ObjectStorageService
from backend.services.ai_service import AIService
from backend.services.config_service import ConfigService
from backend.services.features_service import FeaturesService
from backend.services.video_enrichment_service import VideoEnrichmentService
from backend.services.link_checker_service import LinkCheckerService

# Import APIs
from backend.api.document_api import DocumentAPI
from backend.api.search_api import SearchAPI
from backend.api.defect_detection_api import DefectDetectionAPI
from backend.api.features_api import FeaturesAPI
from backend.api.content_management_api import ContentManagementAPI
from backend.api.openai_compatible_api import OpenAICompatibleAPI

# Global services
database_service = None
storage_service = None
ai_service = None
config_service = None
features_service = None
video_enrichment_service = None
link_checker_service = None

# Global APIs (initialized in lifespan)
document_api = None
search_api = None
defect_detection_api = None
features_api = None
content_management_api = None
openai_api = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup event handler"""
    global database_service, storage_service, ai_service, config_service, features_service
    global video_enrichment_service, link_checker_service
    global document_api, search_api, defect_detection_api, features_api, content_management_api, openai_api
    
    # Startup
    print("🚀 Starting KR-AI-Engine...")
    
    try:
        # Initialize configuration service
        config_service = ConfigService()
        print("✅ Configuration service initialized")
        
        # Initialize database service
        database_service = DatabaseService(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_ANON_KEY"),
            postgres_url=os.getenv("DATABASE_CONNECTION_URL")
        )
        await database_service.connect()
        print("✅ Database service connected")
        if database_service.pg_pool:
            print("✅ PostgreSQL connection pool initialized")
        
        # Initialize object storage service
        storage_service = ObjectStorageService(
            r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            r2_endpoint_url=os.getenv("R2_ENDPOINT_URL"),
            r2_public_url_documents=os.getenv("R2_PUBLIC_URL_DOCUMENTS"),
            r2_public_url_error=os.getenv("R2_PUBLIC_URL_ERROR"),
            r2_public_url_parts=os.getenv("R2_PUBLIC_URL_PARTS")
        )
        await storage_service.connect()
        print("✅ Object storage service connected")
        
        # Initialize AI service
        ai_service = AIService(
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434")
        )
        await ai_service.connect()
        print("✅ AI service connected")
        
        # Initialize features service
        features_service = FeaturesService(ai_service, database_service)
        print("✅ Features service initialized")
        
        # Initialize video enrichment service
        video_enrichment_service = VideoEnrichmentService()
        print("✅ Video enrichment service initialized")
        
        # Initialize link checker service
        link_checker_service = LinkCheckerService()
        print("✅ Link checker service initialized")
        
        # NOW initialize APIs with services
        document_api = DocumentAPI(database_service, storage_service, ai_service)
        search_api = SearchAPI(database_service, ai_service)
        defect_detection_api = DefectDetectionAPI(ai_service, database_service)
        features_api = FeaturesAPI(database_service, features_service)
        content_management_api = ContentManagementAPI(
            database_service=database_service,
            video_enrichment_service=video_enrichment_service,
            link_checker_service=link_checker_service
        )
        openai_api = OpenAICompatibleAPI(database_service, ai_service)
        
        # Include routers
        app.include_router(document_api.router)
        app.include_router(search_api.router)
        app.include_router(defect_detection_api.router)
        app.include_router(features_api.router)
        app.include_router(content_management_api.router)
        app.include_router(openai_api.router)
        print("✅ API routers registered (including OpenAI-compatible)")
        
        print("🎯 KR-AI-Engine ready!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
    
    # Yield control to the application
    yield
    
    # Shutdown
    print("🛑 Shutting down KR-AI-Engine...")
    if database_service:
        print("✅ Database service disconnected")
    if storage_service:
        print("✅ Storage service disconnected")
    if ai_service:
        print("✅ AI service disconnected")
    print("👋 KR-AI-Engine stopped")

# Create FastAPI application with lifespan
app = FastAPI(
    title="KR-AI-Engine",
    description="AI-powered document processing system for technical documentation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "KR-AI-Engine API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "documents": "/documents",
            "search": "/search",
            "defect_detection": "/defect-detection",
            "features": "/features",
            "content_management": "/content",
            "openai_compatible": "/v1/chat/completions",
            "health": "/health"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Check database service
        if database_service:
            db_health = await database_service.health_check()
            health_status["services"]["database"] = db_health
        else:
            health_status["services"]["database"] = {"status": "not_initialized"}
        
        # Check storage service
        if storage_service:
            storage_health = await storage_service.health_check()
            health_status["services"]["storage"] = storage_health
        else:
            health_status["services"]["storage"] = {"status": "not_initialized"}
        
        # Check AI service
        if ai_service:
            ai_health = await ai_service.health_check()
            health_status["services"]["ai"] = ai_health
        else:
            health_status["services"]["ai"] = {"status": "not_initialized"}
        
        # Check config service
        if config_service:
            config_health = config_service.health_check()
            health_status["services"]["config"] = config_health
        else:
            health_status["services"]["config"] = {"status": "not_initialized"}
        
        # Determine overall status
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in health_status["services"].values()
        )
        
        if not all_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# System info endpoint
@app.get("/info")
async def system_info():
    """System information"""
    try:
        return {
            "application": "KR-AI-Engine",
            "version": "1.0.0",
            "environment": {
                "python_version": "3.11+",
                "fastapi_version": "0.104+",
                "ollama_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
                "database_url": os.getenv("DATABASE_URL", "Not configured"),
                "storage_provider": os.getenv("STORAGE_PROVIDER", "database")
            },
            "features": {
                "document_processing": True,
                "semantic_search": True,
                "defect_detection": True,
                "features_management": True,
                "vector_search": True,
                "ai_classification": True,
                "video_enrichment": True,
                "link_checking": True
            },
            "processing_pipeline": [
                "Upload Processor",
                "Text Processor", 
                "Image Processor",
                "Classification Processor",
                "Metadata Processor",
                "Storage Processor",
                "Embedding Processor",
                "Search Processor"
            ],
            "content_management": {
                "video_enrichment": {
                    "platforms": ["YouTube", "Vimeo", "Brightcove"],
                    "features": ["metadata", "thumbnails", "duration", "deduplication"]
                },
                "link_checking": {
                    "features": ["validation", "redirect_following", "auto_fixing", "url_cleaning"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 error handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 error handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
