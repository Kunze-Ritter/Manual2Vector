"""
Monitoring API - Real-time monitoring of pipeline stages and hardware usage
"""

import asyncio
import psutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.middleware.auth_middleware import require_permission
from models.monitoring import (
    Alert,
    AlertListResponse,
    AlertRule,
    AlertSeverity,
    CreateAlertRule,
    DataQualityResponse,
    PipelineStatusResponse,
    ProcessorHealthResponse,
    QueueStatusResponse,
    StageErrorLogsResponse,
    StageQueueResponse,
)
from services.alert_service import AlertService
from services.metrics_service import MetricsService

router = APIRouter()

# Global service instances will be initialized by app.py
# These functions are used as dependencies
async def get_metrics_service() -> MetricsService:
    """Get metrics service instance from app.py."""
    from api.app import get_metrics_service as app_get_metrics
    return await app_get_metrics()


async def get_alert_service() -> AlertService:
    """Get alert service instance from app.py."""
    from api.app import get_alert_service as app_get_alert
    return await app_get_alert()

class StageStatus(BaseModel):
    stage_name: str
    documents_processed: int
    is_active: bool
    last_activity: str
    current_document: str = ""

class HardwareStatus(BaseModel):
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    gpu_percent: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0

class PipelineStatus(BaseModel):
    total_documents: int
    documents_completed: int
    documents_in_progress: int
    current_stages: List[StageStatus]
    hardware: HardwareStatus
    processing_speed: float  # documents per minute
    estimated_completion: str

# Global monitoring data
monitoring_data = {
    'stages': {
        'upload': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'text': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'image': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'classification': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'metadata': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'storage': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'embedding': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''},
        'search': {'processed': 0, 'active': False, 'last_activity': '', 'current_doc': ''}
    },
    'total_documents': 0,
    'documents_completed': 0,
    'start_time': None,
    'last_update': None
}

def update_stage_status(stage_name: str, document_name: str = "", completed: bool = False):
    """Update stage status - called by pipeline workers"""
    global monitoring_data
    
    if stage_name in monitoring_data['stages']:
        stage_data = monitoring_data['stages'][stage_name]
        stage_data['active'] = True
        stage_data['last_activity'] = datetime.now().strftime('%H:%M:%S')
        
        if document_name:
            stage_data['current_doc'] = document_name
        
        if completed:
            stage_data['processed'] += 1
            stage_data['active'] = False
            stage_data['current_doc'] = ""
            
            # Update total completed
            monitoring_data['documents_completed'] = sum(
                stage['processed'] for stage in monitoring_data['stages'].values()
            )
        
        monitoring_data['last_update'] = datetime.now()

def get_hardware_status() -> HardwareStatus:
    """Get current hardware status"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # RAM usage
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = (ram.total - ram.available) / 1024 / 1024 / 1024
    ram_total_gb = ram.total / 1024 / 1024 / 1024
    
    # GPU usage (simplified - would need nvidia-ml-py for real GPU monitoring)
    gpu_percent = 0.0
    gpu_memory_used_mb = 0.0
    gpu_memory_total_mb = 8192.0  # RTX 2000 has 8GB VRAM
    
    return HardwareStatus(
        cpu_percent=cpu_percent,
        ram_percent=ram_percent,
        ram_used_gb=ram_used_gb,
        ram_total_gb=ram_total_gb,
        gpu_percent=gpu_percent,
        gpu_memory_used_mb=gpu_memory_used_mb,
        gpu_memory_total_mb=gpu_memory_total_mb
    )

def calculate_processing_speed() -> float:
    """Calculate documents per minute"""
    global monitoring_data
    
    if not monitoring_data['start_time']:
        return 0.0
    
    elapsed_minutes = (datetime.now() - monitoring_data['start_time']).total_seconds() / 60
    if elapsed_minutes == 0:
        return 0.0
    
    return monitoring_data['documents_completed'] / elapsed_minutes

def estimate_completion() -> str:
    """Estimate completion time"""
    global monitoring_data
    
    if monitoring_data['documents_completed'] == 0:
        return "Unknown"
    
    speed = calculate_processing_speed()
    if speed == 0:
        return "Unknown"
    
    remaining = monitoring_data['total_documents'] - monitoring_data['documents_completed']
    minutes_remaining = remaining / speed
    
    if minutes_remaining < 60:
        return f"{minutes_remaining:.1f} minutes"
    else:
        hours = minutes_remaining / 60
        return f"{hours:.1f} hours"

@router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read"))
):
    """Get current pipeline status (DEPRECATED: Use /pipeline instead)"""
    global monitoring_data
    
    # Get hardware status
    hardware = get_hardware_status()
    
    # Build stage status list
    current_stages = []
    for stage_name, stage_data in monitoring_data['stages'].items():
        current_stages.append(StageStatus(
            stage_name=stage_name,
            documents_processed=stage_data['processed'],
            is_active=stage_data['active'],
            last_activity=stage_data['last_activity'],
            current_document=stage_data['current_doc']
        ))
    
    # Calculate documents in progress
    documents_in_progress = sum(1 for stage in monitoring_data['stages'].values() if stage['active'])
    
    return PipelineStatus(
        total_documents=monitoring_data['total_documents'],
        documents_completed=monitoring_data['documents_completed'],
        documents_in_progress=documents_in_progress,
        current_stages=current_stages,
        hardware=hardware,
        processing_speed=calculate_processing_speed(),
        estimated_completion=estimate_completion()
    )

@router.get("/stages", response_model=List[StageStatus])
async def get_stage_status(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read"))
):
    """Get detailed stage status (DEPRECATED: Use /pipeline instead)"""
    global monitoring_data
    
    stages = []
    for stage_name, stage_data in monitoring_data['stages'].items():
        stages.append(StageStatus(
            stage_name=stage_name,
            documents_processed=stage_data['processed'],
            is_active=stage_data['active'],
            last_activity=stage_data['last_activity'],
            current_document=stage_data['current_doc']
        ))
    
    return stages

@router.get("/hardware", response_model=HardwareStatus)
async def get_hardware_status_endpoint(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read"))
):
    """Get current hardware status (DEPRECATED: Use /metrics instead)"""
    return get_hardware_status()

@router.post("/reset")
async def reset_monitoring(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:write"))
):
    """Reset monitoring data (DEPRECATED: Admin only)"""
    global monitoring_data
    
    for stage_data in monitoring_data['stages'].values():
        stage_data['processed'] = 0
        stage_data['active'] = False
        stage_data['last_activity'] = ''
        stage_data['current_doc'] = ''
    
    monitoring_data['total_documents'] = 0
    monitoring_data['documents_completed'] = 0
    monitoring_data['start_time'] = datetime.now()
    monitoring_data['last_update'] = datetime.now()
    
    return {"message": "Monitoring data reset"}

@router.post("/start")
async def start_monitoring(
    total_documents: int,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:write"))
):
    """Start monitoring for a batch (DEPRECATED: Admin only)"""
    global monitoring_data
    
    monitoring_data['total_documents'] = total_documents
    monitoring_data['start_time'] = datetime.now()
    monitoring_data['last_update'] = datetime.now()
    
    return {"message": f"Started monitoring for {total_documents} documents"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "monitoring_active": monitoring_data['start_time'] is not None
    }


# New monitoring endpoints

@router.get("/pipeline", response_model=PipelineStatusResponse)
async def get_pipeline_monitoring(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
):
    """Get comprehensive pipeline monitoring data."""
    pipeline_metrics = await metrics_svc.get_pipeline_metrics()
    stage_metrics = await metrics_svc.get_stage_metrics()
    hardware_status = await metrics_svc.get_hardware_metrics()
    
    return PipelineStatusResponse(
        pipeline_metrics=pipeline_metrics,
        stage_metrics=stage_metrics,
        hardware_status=hardware_status,
    )


@router.get("/queue", response_model=QueueStatusResponse)
async def get_queue_monitoring(
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
):
    """Get queue monitoring data."""
    queue_metrics = await metrics_svc.get_queue_metrics()
    queue_items = await metrics_svc.get_queue_items(limit, status_filter)
    
    return QueueStatusResponse(
        queue_metrics=queue_metrics,
        queue_items=queue_items,
    )


@router.get("/metrics")
async def get_aggregated_metrics(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
) -> Dict[str, Any]:
    """Get aggregated metrics for all systems."""
    pipeline_metrics = await metrics_svc.get_pipeline_metrics()
    queue_metrics = await metrics_svc.get_queue_metrics()
    hardware_metrics = await metrics_svc.get_hardware_metrics()
    
    return {
        "pipeline": pipeline_metrics.model_dump(),
        "queue": queue_metrics.model_dump(),
        "hardware": hardware_metrics.model_dump(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/data-quality", response_model=DataQualityResponse)
async def get_data_quality_metrics(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
):
    """Get data quality metrics."""
    return await metrics_svc.get_data_quality_metrics()


# Processor-level monitoring endpoints

@router.get("/processors", response_model=ProcessorHealthResponse)
async def get_processor_health(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
):
    """Get processor health status for all stages."""
    processors = await metrics_svc.get_processor_health()
    return ProcessorHealthResponse(processors=processors)


@router.get("/stages/{stage_name}/queue", response_model=StageQueueResponse)
async def get_stage_queue(
    stage_name: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
):
    """Get queue items for a specific stage."""
    return await metrics_svc.get_stage_queue(stage_name, limit)


@router.get("/stages/{stage_name}/errors", response_model=StageErrorLogsResponse)
async def get_stage_errors(
    stage_name: str,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
):
    """Get error logs for a specific stage."""
    return await metrics_svc.get_stage_errors(stage_name, limit)


@router.post("/stages/{stage_name}/retry")
async def retry_stage_processing(
    stage_name: str,
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:write")),
    metrics_svc: MetricsService = Depends(get_metrics_service),
) -> Dict[str, Any]:
    """Retry a failed stage for a document."""
    success = await metrics_svc.retry_stage(document_id, stage_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document or stage not found, or stage not in failed state")
    
    return {"success": True, "message": f"Stage {stage_name} retry triggered for document {document_id}"}


# Alert endpoints

@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    limit: int = 50,
    severity: Optional[AlertSeverity] = None,
    acknowledged: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    alert_svc: AlertService = Depends(get_alert_service),
):
    """List alerts with optional filtering."""
    return await alert_svc.get_alerts(limit, severity, acknowledged)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:write")),
    alert_svc: AlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Acknowledge an alert."""
    user_id = current_user.get("id", "unknown")
    success = await alert_svc.acknowledge_alert(alert_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True, "message": "Alert acknowledged"}


@router.delete("/alerts/{alert_id}")
async def dismiss_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:write")),
    alert_svc: AlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Dismiss (delete) an alert."""
    success = await alert_svc.dismiss_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True, "message": "Alert dismissed"}


# Alert rules endpoints

@router.get("/alert-rules", response_model=List[AlertRule])
async def list_alert_rules(
    current_user: Dict[str, Any] = Depends(require_permission("monitoring:read")),
    alert_svc: AlertService = Depends(get_alert_service),
):
    """List all alert rules."""
    return await alert_svc.load_alert_rules()


@router.post("/alert-rules")
async def create_alert_rule(
    rule: CreateAlertRule,
    current_user: Dict[str, Any] = Depends(require_permission("alerts:manage")),
    alert_svc: AlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Create new alert rule (requires alerts:manage permission)."""
    rule_id = await alert_svc.add_alert_rule(rule)
    return {"success": True, "rule_id": rule_id}


@router.put("/alert-rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_permission("alerts:manage")),
    alert_svc: AlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Update alert rule (requires alerts:manage permission)."""
    success = await alert_svc.update_alert_rule(rule_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    return {"success": True}


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("alerts:manage")),
    alert_svc: AlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Delete alert rule (requires alerts:manage permission)."""
    success = await alert_svc.delete_alert_rule(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    return {"success": True}
