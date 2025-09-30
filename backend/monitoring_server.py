"""
Monitoring Server - Standalone server for pipeline monitoring
"""

import uvicorn
from fastapi import FastAPI
from api.monitoring_api import router as monitoring_router

app = FastAPI(title="KR-AI Pipeline Monitoring", version="1.0.0")

# Include monitoring routes
app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

@app.get("/")
async def root():
    return {
        "message": "KR-AI Pipeline Monitoring Server",
        "endpoints": {
            "/monitoring/status": "Get complete pipeline status",
            "/monitoring/stages": "Get detailed stage status", 
            "/monitoring/hardware": "Get hardware status",
            "/monitoring/health": "Health check"
        }
    }

if __name__ == "__main__":
    print("Starting KR-AI Pipeline Monitoring Server...")
    print("Access at: http://localhost:8001")
    print("Status: http://localhost:8001/monitoring/status")
    print("Hardware: http://localhost:8001/monitoring/hardware")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
