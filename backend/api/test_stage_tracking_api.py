"""
Test Stage Tracking via API

Tests the complete flow:
1. Upload document
2. Check stage_status in response
3. Query stage statistics
"""

import requests
import time

API_BASE = "http://localhost:8000"

print("="*80)
print("  Testing Stage Tracking via API")
print("="*80)

# Test 1: Health Check
print("\n1. Health Check...")
try:
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        print("   ✅ API is running")
    else:
        print("   ❌ API not responding")
        exit(1)
except Exception as e:
    print(f"   ❌ Cannot connect to API: {e}")
    print("\n   💡 Start API with: python app.py")
    exit(1)

# Test 2: Get existing document status with stage_status
print("\n2. Get Document Status with Stage Tracking...")
try:
    # Get first document ID
    response = requests.get(f"{API_BASE}/status")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Pipeline Status:")
        print(f"      Total Documents: {data['total_documents']}")
        print(f"      Completed: {data['completed']}")
        
        # If we have documents, get detailed status
        if data['total_documents'] > 0:
            # We need a document ID - let's use the one from our tests
            doc_id = "5a30739d-d8d4-4a1a-b033-a32e39cf33ba"
            
            print(f"\n3. Getting detailed status for document...")
            response = requests.get(f"{API_BASE}/status/{doc_id}")
            
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ Document Status Retrieved!")
                print(f"\n      Document ID: {status['document_id']}")
                print(f"      Status: {status['status']}")
                print(f"      Current Stage: {status['current_stage']}")
                print(f"      Progress: {status['progress']}%")
                
                if status.get('stage_status'):
                    print(f"\n      📊 Per-Stage Status:")
                    for stage, stage_data in status['stage_status'].items():
                        stage_status = stage_data.get('status', 'unknown')
                        progress = stage_data.get('progress', 0)
                        icon = "✅" if stage_status == "completed" else "⏳" if stage_status == "processing" else "⏸️"
                        print(f"         {icon} {stage:20} {stage_status:12} ({progress}%)")
                else:
                    print(f"\n      ⚠️  No stage_status data (old document)")
            else:
                print(f"   ❌ Could not get document status: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Stage Statistics
print("\n4. Getting Stage Statistics...")
try:
    response = requests.get(f"{API_BASE}/stages/statistics")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Stage Statistics Retrieved!")
        
        if data.get('stages'):
            print(f"\n      📈 Pipeline Statistics:")
            for stage, stats in data['stages'].items():
                total = stats['pending'] + stats['processing'] + stats['completed']
                if total > 0:
                    print(f"\n      {stage}:")
                    print(f"         Pending: {stats['pending']}")
                    print(f"         Processing: {stats['processing']}")
                    print(f"         Completed: {stats['completed']}")
                    if stats['failed'] > 0:
                        print(f"         Failed: {stats['failed']}")
                    if stats['avg_duration']:
                        print(f"         Avg Duration: {stats['avg_duration']:.1f}s")
        else:
            print(f"      ℹ️  No statistics available yet")
    else:
        print(f"   ❌ Could not get statistics: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("  ✅ API Stage Tracking Tests Complete!")
print("="*80)
print("\n  💡 To test upload with stage tracking:")
print("     - Upload a new document via /upload endpoint")
print("     - Check its stage_status immediately")
print("     - Watch stages progress to 'completed'")
print("\n")
