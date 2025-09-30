"""
Simple Monitor - Basic monitoring without FastAPI
"""

import asyncio
import psutil
import time
from datetime import datetime
from typing import Dict, Any

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

def start_monitoring(total_documents: int):
    """Start monitoring for a batch"""
    global monitoring_data
    
    monitoring_data['total_documents'] = total_documents
    monitoring_data['start_time'] = datetime.now()
    monitoring_data['last_update'] = datetime.now()
    
    print(f"Started monitoring for {total_documents} documents")

def get_hardware_status():
    """Get current hardware status"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # RAM usage
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = (ram.total - ram.available) / 1024 / 1024 / 1024
    ram_total_gb = ram.total / 1024 / 1024 / 1024
    
    return {
        'cpu_percent': cpu_percent,
        'ram_percent': ram_percent,
        'ram_used_gb': ram_used_gb,
        'ram_total_gb': ram_total_gb
    }

def calculate_processing_speed():
    """Calculate documents per minute"""
    global monitoring_data
    
    if not monitoring_data['start_time']:
        return 0.0
    
    elapsed_minutes = (datetime.now() - monitoring_data['start_time']).total_seconds() / 60
    if elapsed_minutes == 0:
        return 0.0
    
    return monitoring_data['documents_completed'] / elapsed_minutes

def print_status():
    """Print current status"""
    global monitoring_data
    
    print(f"\n{'='*80}")
    print(f"KR-AI PIPELINE MONITORING - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    
    # Hardware status
    hardware = get_hardware_status()
    print(f"HARDWARE:")
    print(f"  CPU: {hardware['cpu_percent']:5.1f}%")
    print(f"  RAM: {hardware['ram_percent']:5.1f}% ({hardware['ram_used_gb']:.1f}GB / {hardware['ram_total_gb']:.1f}GB)")
    print(f"")
    
    # Pipeline status
    documents_in_progress = sum(1 for stage in monitoring_data['stages'].values() if stage['active'])
    print(f"PIPELINE:")
    print(f"  Total Documents: {monitoring_data['total_documents']}")
    print(f"  Completed: {monitoring_data['documents_completed']}")
    print(f"  In Progress: {documents_in_progress}")
    print(f"  Speed: {calculate_processing_speed():.1f} docs/min")
    print(f"")
    
    # Stage status
    print(f"STAGES:")
    for stage_name, stage_data in monitoring_data['stages'].items():
        status = "ACTIVE" if stage_data['active'] else "IDLE"
        current_doc = stage_data['current_doc'][:30] + "..." if len(stage_data['current_doc']) > 30 else stage_data['current_doc']
        print(f"  {stage_name:12s}: {stage_data['processed']:3d} docs | {status:6s} | {current_doc}")
    
    print(f"{'='*80}")

async def monitor_loop():
    """Monitor loop"""
    while True:
        print_status()
        await asyncio.sleep(10)  # Update every 10 seconds

if __name__ == "__main__":
    print("Starting Simple Monitor...")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
