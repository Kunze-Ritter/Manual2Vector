"""
Test NEW upload with stage tracking
"""

import requests
from pathlib import Path

API_BASE = "http://localhost:8000"

print("="*80)
print("  Testing NEW Upload with Stage Tracking")
print("="*80)

# Find test PDF
test_pdf = Path("../../CX833 CX961 CX962 CX963 XC8355 XC9635 XC9645 SM.pdf")
if not test_pdf.exists():
    test_pdf = Path("C:/Users/haast/Docker/KRAI-minimal/CX833 CX961 CX962 CX963 XC8355 XC9635 XC9645 SM.pdf")

if not test_pdf.exists():
    print("\n❌ Test PDF not found!")
    print("   Please provide path to a PDF")
    exit(1)

print(f"\n📄 Uploading: {test_pdf.name}")

# Upload
try:
    with open(test_pdf, 'rb') as f:
        files = {'file': (test_pdf.name, f, 'application/pdf')}
        data = {
            'document_type': 'service_manual',
            'force_reprocess': 'true'  # Force new upload
        }
        
        response = requests.post(
            f"{API_BASE}/upload",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        
        if result['success']:
            print(f"\n✅ Upload successful!")
            doc_id = result['document_id']
            print(f"   Document ID: {doc_id}")
            print(f"   Status: {result['status']}")
            
            # Get detailed status
            print(f"\n📊 Checking stage_status...")
            import time
            time.sleep(1)  # Wait a bit
            
            status_response = requests.get(f"{API_BASE}/status/{doc_id}")
            if status_response.status_code == 200:
                status = status_response.json()
                
                print(f"\n   Current Stage: {status['current_stage']}")
                print(f"   Progress: {status['progress']}%")
                
                if status.get('stage_status'):
                    print(f"\n   🎯 Per-Stage Status:")
                    for stage, stage_data in status['stage_status'].items():
                        stage_status = stage_data.get('status', 'unknown')
                        
                        if stage_status == "completed":
                            icon = "✅"
                            duration = stage_data.get('duration_seconds', 0)
                            print(f"      {icon} {stage:20} COMPLETED ({duration:.1f}s)")
                        elif stage_status == "processing":
                            icon = "⏳"
                            progress = stage_data.get('progress', 0)
                            print(f"      {icon} {stage:20} PROCESSING ({progress}%)")
                        elif stage_status == "failed":
                            icon = "❌"
                            error = stage_data.get('error', 'Unknown')
                            print(f"      {icon} {stage:20} FAILED - {error}")
                        else:
                            icon = "⏸️"
                            print(f"      {icon} {stage:20} {stage_status.upper()}")
                    
                    print(f"\n   🎉 Stage Tracking is WORKING!")
                else:
                    print(f"\n   ⚠️  No stage_status in response")
                    print(f"   Response: {status}")
        else:
            print(f"\n❌ Upload failed: {result.get('message')}")
    else:
        print(f"\n❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*80)
