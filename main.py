"""
KR-AI-Engine Main Application
FastAPI application with all endpoints and services
"""

import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

print("DEBUG: main.py is being loaded!")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"DEBUG: DATABASE_TYPE = {os.getenv('DATABASE_TYPE')}")
except ImportError:
    pass

# Add current directory to Python path
sys.path.insert(0, '/app')

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

# Import services (relative imports)
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService

# Import the API app factory and routes
from api.routes import auth as auth_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
database_service = None
object_storage_service = None
ai_service = None
config_service = None
features_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    global database_service, object_storage_service, ai_service, config_service, features_service
    
    try:
        logger.info("Starting KRAI Engine initialization...")
        
        # Initialize configuration service
        config_service = ConfigService(config_dir="config")
        
        # Debug database type
        db_type = os.getenv("DATABASE_TYPE", "not_set")
        logger.info(f"Environment DATABASE_TYPE: {db_type}")
        
        # Initialize database service
        database_service = DatabaseService(
            database_type=os.getenv('DATABASE_TYPE', 'postgresql'),
            postgres_host=os.getenv('DATABASE_HOST', 'krai-postgres'),
            postgres_port=int(os.getenv('DATABASE_PORT', '5432')),
            postgres_db=os.getenv('DATABASE_NAME', 'krai'),
            postgres_user=os.getenv('DATABASE_USER', 'krai_user'),
            postgres_password=os.getenv('DATABASE_PASSWORD', 'krai_secure_password')
        )
        await database_service.connect()
        logger.info("Database service initialized")
        
        # Initialize object storage service
        object_storage_service = ObjectStorageService(
            access_key_id=os.getenv('OBJECT_STORAGE_ACCESS_KEY', 'minioadmin'),
            secret_access_key=os.getenv('OBJECT_STORAGE_SECRET_KEY', 'minioadmin123'),
            endpoint_url=os.getenv('OBJECT_STORAGE_ENDPOINT', 'http://krai-minio:9000'),
            public_url_documents=os.getenv('OBJECT_STORAGE_PUBLIC_URL', 'http://localhost:9000'),
            public_url_error=os.getenv('OBJECT_STORAGE_PUBLIC_URL', 'http://localhost:9000'),
            public_url_parts=os.getenv('OBJECT_STORAGE_PUBLIC_URL', 'http://localhost:9000'),
            use_ssl=os.getenv('OBJECT_STORAGE_USE_SSL', 'false').lower() == 'true',
            region=os.getenv('OBJECT_STORAGE_REGION', 'us-east-1')
        )
        await object_storage_service.connect()
        logger.info("Object storage service initialized")
        
        # Initialize AI service
        ai_service = AIService(ollama_url=os.getenv('AI_SERVICE_URL', 'http://krai-ollama:11434'))
        await ai_service.connect()
        logger.info("AI service initialized")
        
        # Initialize features service
        features_service = FeaturesService(ai_service, database_service)
        logger.info("Features service initialized")
        
        # Store services in app state
        app.state.database_service = database_service
        app.state.object_storage_service = object_storage_service
        app.state.ai_service = ai_service
        app.state.config_service = config_service
        app.state.features_service = features_service
        
        logger.info("About to load auth routes...")
        
        # Include all API routes after services are initialized
        try:
            # Initialize auth routes
            auth_router = auth_routes.initialize_auth_routes(database_service)
            app.include_router(auth_router, prefix="/api/v1")
            logger.info("Auth routes loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load auth routes: {e}")
            raise  # Re-raise to see the actual error
        
        # Create default admin user
        try:
            from services.auth_service import AuthService
            auth_service = AuthService(database_service)
            
            admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
            admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            admin_first_name = os.getenv("DEFAULT_ADMIN_FIRST_NAME", "System")
            admin_last_name = os.getenv("DEFAULT_ADMIN_LAST_NAME", "Administrator")
            admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
            
            if admin_password:
                logger.info(f"Ensuring default admin user: {admin_username}")
                await auth_service.ensure_default_admin(
                    email=admin_email,
                    username=admin_username,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                    password=admin_password
                )
                logger.info("✅ Default admin user verified/created")
            else:
                logger.warning("⚠️  DEFAULT_ADMIN_PASSWORD not set - skipping admin user creation")
        except Exception as e:
            logger.error(f"Failed to ensure default admin user: {e}")
            # Don't raise - allow app to start even if admin creation fails
        
        logger.info("KRAI Engine initialization completed")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize KRAI Engine: {str(e)}")
        raise
    finally:
        # Cleanup
        try:
            if database_service:
                await database_service.close()
                logger.info("Database service closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="KRAI Engine API",
    description="Knowledge Retrieval and AI Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add our custom health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Run the application
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting KRAI Engine on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=False
    )
