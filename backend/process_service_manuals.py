#!/usr/bin/env python3
"""
Service Manuals Processing Script
Verarbeitet alle Service Manuals aus dem Downloads-Ordner über die KR-AI-Engine API
"""

import os
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any

class ServiceManualProcessor:
    """Verarbeitet Service Manuals über die KR-AI-Engine API"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.processed_files = []
        self.failed_files = []
    
    def check_api_health(self) -> bool:
        """Prüft ob die API verfügbar ist"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Health Check: {health_data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ API Health Check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health Check failed: {e}")
            return False
    
    def upload_document(self, file_path: str, document_type: str = "service_manual") -> Dict[str, Any]:
        """Lädt ein Dokument über die API hoch"""
        try:
            print(f"📤 Uploading: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file, 'application/pdf')}
                data = {
                    'document_type': document_type,
                    'language': 'en'
                }
                
                response = self.session.post(
                    f"{self.api_base_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Upload successful: {result.get('document_id', 'unknown')}")
                    return result
                else:
                    print(f"❌ Upload failed: {response.status_code} - {response.text}")
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return {"error": str(e)}
    
    def check_document_status(self, document_id: str) -> Dict[str, Any]:
        """Prüft den Verarbeitungsstatus eines Dokuments"""
        try:
            response = self.session.get(f"{self.api_base_url}/documents/{document_id}/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def wait_for_processing(self, document_id: str, max_wait_time: int = 300) -> bool:
        """Wartet auf die Verarbeitung eines Dokuments"""
        print(f"⏳ Waiting for processing: {document_id}")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.check_document_status(document_id)
            if "error" in status:
                print(f"❌ Status check failed: {status['error']}")
                return False
            
            document_status = status.get('document_status', 'unknown')
            queue_position = status.get('queue_position', 0)
            
            print(f"📊 Status: {document_status}, Queue: {queue_position}")
            
            if document_status == 'completed':
                print(f"✅ Processing completed: {document_id}")
                return True
            elif document_status == 'failed':
                print(f"❌ Processing failed: {document_id}")
                return False
            
            time.sleep(5)  # Wait 5 seconds before next check
        
        print(f"⏰ Timeout waiting for processing: {document_id}")
        return False
    
    def process_directory(self, directory_path: str) -> Dict[str, Any]:
        """Verarbeitet alle PDFs in einem Verzeichnis"""
        print(f"🔍 Scanning directory: {directory_path}")
        
        # Find all PDF files
        pdf_files = []
        for file in os.listdir(directory_path):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(directory_path, file))
        
        print(f"📄 Found {len(pdf_files)} PDF files")
        
        if not pdf_files:
            return {"error": "No PDF files found"}
        
        # Check API health first
        if not self.check_api_health():
            return {"error": "API not available"}
        
        # Process each file
        results = []
        for i, file_path in enumerate(pdf_files, 1):
            print(f"\n📋 Processing {i}/{len(pdf_files)}: {os.path.basename(file_path)}")
            
            # Upload document
            upload_result = self.upload_document(file_path)
            
            if "error" in upload_result:
                print(f"❌ Upload failed: {upload_result['error']}")
                self.failed_files.append({
                    "file": file_path,
                    "error": upload_result['error']
                })
                continue
            
            document_id = upload_result.get('document_id')
            if not document_id:
                print(f"❌ No document ID returned")
                self.failed_files.append({
                    "file": file_path,
                    "error": "No document ID returned"
                })
                continue
            
            # Wait for processing
            processing_success = self.wait_for_processing(document_id)
            
            if processing_success:
                self.processed_files.append({
                    "file": file_path,
                    "document_id": document_id,
                    "status": "completed"
                })
                print(f"✅ Successfully processed: {os.path.basename(file_path)}")
            else:
                self.failed_files.append({
                    "file": file_path,
                    "document_id": document_id,
                    "error": "Processing timeout or failure"
                })
                print(f"❌ Processing failed: {os.path.basename(file_path)}")
            
            # Small delay between files
            time.sleep(2)
        
        return {
            "total_files": len(pdf_files),
            "processed": len(self.processed_files),
            "failed": len(self.failed_files),
            "processed_files": self.processed_files,
            "failed_files": self.failed_files
        }
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Verarbeitung zurück"""
        return {
            "processed_count": len(self.processed_files),
            "failed_count": len(self.failed_files),
            "success_rate": len(self.processed_files) / (len(self.processed_files) + len(self.failed_files)) * 100 if (len(self.processed_files) + len(self.failed_files)) > 0 else 0,
            "processed_files": [f["file"] for f in self.processed_files],
            "failed_files": [f["file"] for f in self.failed_files]
        }

def main():
    """Hauptfunktion"""
    print("🚀 KR-AI-Engine Service Manuals Processor")
    print("=" * 50)
    
    # Service Manuals Verzeichnis
    service_manuals_dir = r"C:\Users\haast\Downloads\Office Printing\Service Manuals"
    
    if not os.path.exists(service_manuals_dir):
        print(f"❌ Directory not found: {service_manuals_dir}")
        return
    
    # Processor initialisieren
    processor = ServiceManualProcessor()
    
    # Verzeichnis verarbeiten
    print(f"📁 Processing directory: {service_manuals_dir}")
    results = processor.process_directory(service_manuals_dir)
    
    # Ergebnisse anzeigen
    print("\n" + "=" * 50)
    print("📊 PROCESSING SUMMARY")
    print("=" * 50)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"📄 Total files: {results['total_files']}")
    print(f"✅ Processed: {results['processed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success rate: {results['processed'] / results['total_files'] * 100:.1f}%")
    
    if results['processed'] > 0:
        print(f"\n✅ Successfully processed files:")
        for file_info in results['processed_files']:
            print(f"   - {os.path.basename(file_info['file'])} (ID: {file_info['document_id']})")
    
    if results['failed'] > 0:
        print(f"\n❌ Failed files:")
        for file_info in results['failed_files']:
            print(f"   - {os.path.basename(file_info['file'])}: {file_info.get('error', 'Unknown error')}")
    
    print(f"\n🎯 Processing complete!")
    print(f"📊 Check the KR-AI-Engine dashboard for detailed results")

if __name__ == "__main__":
    main()
