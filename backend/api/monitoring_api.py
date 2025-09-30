"""
Monitoring API - Real-time monitoring of pipeline stages and hardware usage
"""

import asyncio
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

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
async def get_pipeline_status():
    """Get current pipeline status"""
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
async def get_stage_status():
    """Get detailed stage status"""
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
async def get_hardware_status_endpoint():
    """Get current hardware status"""
    return get_hardware_status()

@router.post("/reset")
async def reset_monitoring():
    """Reset monitoring data"""
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
async def start_monitoring(total_documents: int):
    """Start monitoring for a batch"""
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
