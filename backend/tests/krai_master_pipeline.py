"""
KR-AI-Engine Master Pipeline
============================
Ein einziges Script für alle Pipeline-Funktionen:
- Pipeline Reset & Fix
- Document Processing
- Hardware Monitoring
- Batch Processing
- Status Management
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import multiprocessing as mp
import psutil

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Import services
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService

from processors.upload_processor import UploadProcessor
from processors.text_processor_optimized import OptimizedTextProcessor
from processors.image_processor import ImageProcessor
from processors.classification_processor import ClassificationProcessor
from processors.metadata_processor import MetadataProcessor
from processors.storage_processor import StorageProcessor
from processors.embedding_processor import EmbeddingProcessor
from processors.search_processor import SearchProcessor

from core.base_processor import ProcessingContext

class KRMasterPipeline:
    """
    Master Pipeline für alle KR-AI-Engine Funktionen
    """
    
    def __init__(self):
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        
        # Setup logging (minimal)
        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger("krai.master_pipeline")
        
        # Get hardware info
        cpu_count = mp.cpu_count()
        self.max_concurrent = min(cpu_count, 8)
        
        self.logger.info(f"KR Master Pipeline initialized with {self.max_concurrent} concurrent documents")
        
    async def initialize_services(self):
        """Initialize all services"""
        print("Initializing KR Master Pipeline Services...")
        
        # Load environment variables
        load_dotenv('../credentials.txt')
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_ANON_KEY')
        )
        await self.database_service.connect()
        
        # Initialize object storage service
        self.storage_service = ObjectStorageService(
            r2_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            r2_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            r2_endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            r2_public_url_documents=os.getenv('R2_PUBLIC_URL_DOCUMENTS'),
            r2_public_url_error=os.getenv('R2_PUBLIC_URL_ERROR'),
            r2_public_url_parts=os.getenv('R2_PUBLIC_URL_PARTS')
        )
        await self.storage_service.connect()
        
        # Initialize AI service
        self.ai_service = AIService(ollama_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'))
        await self.ai_service.connect()
        
        # Initialize config service
        self.config_service = ConfigService()
        
        # Initialize features service
        self.features_service = FeaturesService(self.ai_service, self.database_service)
        
        # Initialize all processors
        self.processors = {
            'upload': UploadProcessor(self.database_service),
            'text': OptimizedTextProcessor(self.database_service, self.config_service),
            'image': ImageProcessor(self.database_service, self.storage_service, self.ai_service),
            'classification': ClassificationProcessor(self.database_service, self.ai_service, self.features_service),
            'metadata': MetadataProcessor(self.database_service, self.config_service),
            'storage': StorageProcessor(self.database_service, self.storage_service),
            'embedding': EmbeddingProcessor(self.database_service, self.ai_service),
            'search': SearchProcessor(self.database_service, self.ai_service)
        }
        print("All services initialized!")
    
    async def get_documents_status(self) -> Dict[str, Any]:
        """Get comprehensive documents status"""
        print("Checking documents status...")
        
        try:
            # Use direct database service
            all_docs = self.database_service.client.table('documents').select('processing_status').execute()
            
            status = {
                'total_documents': len(all_docs.data),
                'completed': 0,
                'pending': 0,
                'failed': 0,
                'processing': 0
            }
            
            for doc in all_docs.data:
                status_value = doc['processing_status']
                if status_value in status:
                    status[status_value] += 1
            
            return status
                
        except Exception as e:
            print(f"Error getting documents status: {e}")
            return {'total_documents': 0, 'completed': 0, 'pending': 0, 'failed': 0, 'processing': 0}
    
    async def get_documents_needing_processing(self) -> List[Dict[str, Any]]:
        """Get documents that need further processing (all pending documents)"""
        print("Finding documents that need remaining stages...")
        
        try:
            # Get ALL pending AND failed documents directly (no chunk check)
            pending_docs = []
            all_docs = self.database_service.client.table('documents').select('*').in_('processing_status', ['pending', 'failed']).execute()
            
            for doc in all_docs.data:
                # Add ALL pending documents (chunks already exist)
                # Use original filename to construct file path
                filename = doc['filename']
                file_path = f"../service_documents/{filename}"  # Construct path from filename
                
                pending_docs.append({
                    'id': doc['id'],
                    'filename': filename,
                    'file_path': file_path,
                    'processing_status': doc['processing_status'],
                    'chunk_count': 0,  # We don't check chunks anymore
                    'created_at': doc['created_at']
                })
            
            print(f"Found {len(pending_docs)} documents (pending + failed) that need further processing")
            return pending_docs
            
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
    
    async def process_document_remaining_stages(self, document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
        """Process remaining stages for a document"""
        try:
            print(f"\nProcessing remaining stages for: {filename}")
            print(f"  Document ID: {document_id}")
            print(f"  Stages: Image → Classification → Metadata → Storage → Embedding → Search")
            
            # Create processing context
            print(f"  Using file_path: {file_path}")
            context = ProcessingContext(
                file_path=file_path,
                document_id=document_id,
                file_hash="",
                document_type="",
                processing_config={'filename': filename},
                file_size=0
            )
            
            # Get document info from database
            doc_info = await self.database_service.get_document(document_id)
            if doc_info:
                context.file_hash = doc_info.file_hash if doc_info.file_hash else ''
                context.document_type = doc_info.document_type if doc_info.document_type else ''
                # Keep the constructed file_path, don't override with null storage_path
                # context.file_path should remain as constructed above
            
            # Stage 3: Image Processor (GPU intensive)
            print(f"  [3/8] Image Processing: {filename}")
            result3 = await self.processors['image'].process(context)
            images_count = result3.data.get('images_processed', 0)
            
            # Stage 4: Classification Processor
            print(f"  [4/8] Classification: {filename}")
            result4 = await self.processors['classification'].process(context)
            
            # Stage 5: Metadata Processor
            print(f"  [5/8] Metadata: {filename}")
            result5 = await self.processors['metadata'].process(context)
            
            # Stage 6: Storage Processor
            print(f"  [6/8] Storage: {filename}")
            result6 = await self.processors['storage'].process(context)
            
            # Stage 7: Embedding Processor (GPU intensive)
            print(f"  [7/8] Embeddings: {filename}")
            result7 = await self.processors['embedding'].process(context)
            
            # Stage 8: Search Processor
            print(f"  [8/8] Search Index: {filename}")
            result8 = await self.processors['search'].process(context)
            
            # Update document status to completed
            await self.database_service.update_document(document_id, {'processing_status': 'completed'})
            
            print(f"  [OK] Completed: {filename}")
            
            return {
                'success': True,
                'document_id': document_id,
                'filename': filename,
                'images': images_count
            }
            
        except Exception as e:
            print(f"  [ERROR] Error processing {filename}: {e}")
            # Mark as failed
            await self.database_service.update_document(document_id, {'processing_status': 'failed'})
            
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def process_single_document_full_pipeline(self, file_path: str, doc_index: int, total_docs: int) -> Dict[str, Any]:
        """Process a single document through all 8 stages"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            print(f"[{doc_index}/{total_docs}] Processing: {filename} ({file_size/1024/1024:.1f}MB)")
            
            # Create processing context
            context = ProcessingContext(
                file_path=file_path,
                document_id="",
                file_hash="",
                document_type="",
                processing_config={
                    'filename': filename,
                    'file_size': file_size
                },
                file_size=file_size
            )
            
            # Stage 1: Upload Processor
            print(f"  [{doc_index}] Upload: {filename}")
            result1 = await self.processors['upload'].process(context)
            context.document_id = result1.data.get('document_id')
            context.file_hash = result1.data.get('file_hash', '')
            context.document_type = result1.data.get('document_type', '')
            
            # Stage 2: Text Processor (This will wake up CPU!)
            print(f"  [{doc_index}] Text Processing: {filename}")
            result2 = await self.processors['text'].process(context)
            chunks_count = result2.data.get('chunks_created', 0)
            
            # Stage 3: Image Processor (This will wake up GPU!)
            print(f"  [{doc_index}] Image Processing: {filename}")
            result3 = await self.processors['image'].process(context)
            images_count = result3.data.get('images_processed', 0)
            
            # Stage 4: Classification Processor
            print(f"  [{doc_index}] Classification: {filename}")
            result4 = await self.processors['classification'].process(context)
            
            # Stage 5: Metadata Processor
            print(f"  [{doc_index}] Metadata: {filename}")
            result5 = await self.processors['metadata'].process(context)
            
            # Stage 6: Storage Processor
            print(f"  [{doc_index}] Storage: {filename}")
            result6 = await self.processors['storage'].process(context)
            
            # Stage 7: Embedding Processor (This will wake up GPU for AI!)
            print(f"  [{doc_index}] Embeddings: {filename}")
            result7 = await self.processors['embedding'].process(context)
            
            # Stage 8: Search Processor
            print(f"  [{doc_index}] Search Index: {filename}")
            result8 = await self.processors['search'].process(context)
            
            print(f"  [{doc_index}] Completed: {filename}")
            
            return {
                'success': True,
                'document_id': context.document_id,
                'filename': filename,
                'file_size': file_size,
                'chunks': chunks_count,
                'images': images_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': os.path.basename(file_path)
            }
    
    async def process_batch_hardware_waker(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents simultaneously to wake up hardware"""
        print(f"HARDWARE WAKER - Processing {len(file_paths)} files with {self.max_concurrent} concurrent documents!")
        print("This WILL wake up your CPU and GPU!")
        
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'start_time': time.time(),
            'concurrent_documents': self.max_concurrent
        }
        
        try:
            # Create semaphore to limit concurrent document processing
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_with_semaphore(file_path: str, doc_index: int):
                """Process document with semaphore to limit concurrency"""
                async with semaphore:
                    return await self.process_single_document_full_pipeline(file_path, doc_index, len(file_paths))
            
            # Create tasks for all files - THIS IS THE KEY: Multiple docs processing simultaneously
            tasks = [process_with_semaphore(file_path, i+1) for i, file_path in enumerate(file_paths)]
            
            # Process all files in parallel - Multiple documents running through all stages simultaneously
            print(f"Starting HARDWARE WAKER processing of {len(tasks)} files...")
            print("Multiple documents will be processed simultaneously - CPU and GPU will be busy!")
            
            # Monitor hardware while processing
            monitor_task = asyncio.create_task(self.monitor_hardware())
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Cancel monitoring
            monitor_task.cancel()
            
            # Process results
            for i, result in enumerate(completed_tasks):
                if isinstance(result, Exception):
                    results['failed'].append({
                        'success': False,
                        'error': str(result),
                        'filename': os.path.basename(file_paths[i])
                    })
                elif result['success']:
                    results['successful'].append(result)
                else:
                    results['failed'].append(result)
        
        except Exception as e:
            print(f"Error in hardware waker processing: {e}")
        
        # Calculate final statistics
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']
        results['success_rate'] = len(results['successful']) / len(file_paths) * 100
        
        return results
    
    async def monitor_hardware(self):
        """Monitor hardware usage during processing"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Get hardware status
                cpu_percent = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory()
                ram_percent = ram.percent
                ram_used_gb = (ram.total - ram.available) / 1024 / 1024 / 1024
                
                print(f"\n--- HARDWARE STATUS ---")
                print(f"CPU: {cpu_percent:5.1f}% | RAM: {ram_percent:5.1f}% ({ram_used_gb:.1f}GB)")
                
                # Check if hardware is waking up
                if cpu_percent > 50:
                    print("CPU IS WAKING UP!")
                if ram_percent > 60:
                    print("RAM IS BEING USED!")
                
            except asyncio.CancelledError:
                break
            except Exception:
                pass
    
    def find_pdf_files(self, directory: str, limit: int = None) -> List[str]:
        """Find PDF files in directory with optional limit"""
        pdf_files = []
        
        # Check if directory exists
        if not os.path.exists(directory):
            print(f"⚠️  Directory not found: {directory}")
            return []
        
        # Check if directory is empty
        try:
            files_in_dir = os.listdir(directory)
            if not files_in_dir:
                print(f"⚠️  Directory is empty: {directory}")
                return []
        except Exception as e:
            print(f"⚠️  Cannot read directory: {directory} - {e}")
            return []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
                    if limit and len(pdf_files) >= limit:
                        return sorted(pdf_files)
        
        print(f"📁 Found {len(pdf_files)} PDF files in {directory}")
        return sorted(pdf_files)
    
    def find_service_documents_directory(self) -> str:
        """Find the service_documents directory with intelligent path detection"""
        possible_paths = [
            "service_documents",  # Same directory
            "../service_documents",  # Parent directory
            "../../service_documents",  # Two levels up
            "./service_documents",  # Explicit current directory
            os.path.join(os.getcwd(), "service_documents"),  # Absolute current + service_documents
            os.path.join(os.path.dirname(os.getcwd()), "service_documents"),  # Parent + service_documents
        ]
        
        print("🔍 Searching for service_documents directory...")
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # Check if it contains PDF files
                try:
                    files = os.listdir(path)
                    pdf_count = sum(1 for f in files if f.lower().endswith('.pdf'))
                    if pdf_count > 0:
                        print(f"✅ Found service_documents with {pdf_count} PDF files: {os.path.abspath(path)}")
                        return path
                    else:
                        print(f"📁 Found directory but no PDFs: {os.path.abspath(path)}")
                except Exception as e:
                    print(f"⚠️  Cannot read directory {path}: {e}")
            else:
                print(f"❌ Not found: {path}")
        
        print("⚠️  No service_documents directory with PDFs found!")
        print("💡 Please create a 'service_documents' directory and add PDF files")
        return None
    
    def print_status_summary(self, results: Dict[str, Any]):
        """Print status summary"""
        print(f"\n{'='*80}")
        print(f"KR MASTER PIPELINE SUMMARY")
        print(f"{'='*80}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        if 'duration' in results:
            print(f"Total Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
            print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"{'='*80}")

async def main():
    """Main function with menu system"""
    print("KR-AI-ENGINE MASTER PIPELINE")
    print("="*50)
    print("Ein einziges Script für alle Pipeline-Funktionen!")
    print("="*50)
    
    # Initialize pipeline
    pipeline = KRMasterPipeline()
    await pipeline.initialize_services()
    
    while True:
        print("\nMASTER PIPELINE MENU:")
        print("1. Status Check - Zeige aktuelle Dokument-Status")
        print("2. Pipeline Reset - Verarbeite hängende Dokumente")
        print("3. Hardware Waker - Verarbeite neue PDFs (CPU/GPU)")
        print("4. Einzelnes Dokument verarbeiten")
        print("5. Batch Processing - Alle PDFs verarbeiten")
        print("6. Debug - Zeige Pfad-Informationen")
        print("7. Exit")
        
        choice = input("\nWähle Option (1-7): ").strip()
        
        if choice == "1":
            # Status Check
            print("\n=== STATUS CHECK ===")
            status = await pipeline.get_documents_status()
            print(f"Total Documents: {status['total_documents']}")
            print(f"Completed: {status['completed']}")
            print(f"Pending: {status['pending']}")
            print(f"Failed: {status['failed']}")
            print(f"Processing: {status['processing']}")
            
        elif choice == "2":
            # Pipeline Reset
            print("\n=== PIPELINE RESET ===")
            documents = await pipeline.get_documents_needing_processing()
            
            if not documents:
                print("Keine Dokumente gefunden die weitere Verarbeitung brauchen!")
                continue
            
            print(f"Gefunden: {len(documents)} Dokumente (pending + failed) die weitere Stages brauchen")
            print("Dokumente:")
            for i, doc in enumerate(documents[:5]):  # Show first 5
                status_icon = "[FAILED]" if doc['processing_status'] == 'failed' else "[PENDING]"
                print(f"  {i+1}. {doc['filename']} {status_icon}")
            if len(documents) > 5:
                print(f"  ... und {len(documents) - 5} weitere")
            
            response = input(f"\nVerarbeite {len(documents)} Dokumente? (y/n): ").lower().strip()
            if response != 'y':
                print("Pipeline Reset abgebrochen.")
                continue
            
            # Process documents
            results = {'successful': [], 'failed': [], 'total_files': len(documents)}
            
            for i, doc in enumerate(documents):
                print(f"\n[{i+1}/{len(documents)}] Processing: {doc['filename']}")
                result = await pipeline.process_document_remaining_stages(
                    doc['id'], doc['filename'], doc['file_path']
                )
                
                if result['success']:
                    results['successful'].append(result)
                else:
                    results['failed'].append(result)
            
            results['success_rate'] = len(results['successful']) / len(documents) * 100
            pipeline.print_status_summary(results)
            
        elif choice == "3":
            # Hardware Waker
            print("\n=== HARDWARE WAKER ===")
            
            # Find service_documents directory intelligently
            pdf_directory = pipeline.find_service_documents_directory()
            if not pdf_directory:
                print("❌ Cannot find service_documents directory with PDFs!")
                print("💡 Please create a 'service_documents' directory and add PDF files")
                continue
            
            print("Options:")
            print("1. Test mit 3 PDFs (schneller Test)")
            print("2. Test mit 5 PDFs (mittlerer Test)")
            print("3. Verarbeite alle PDFs (vollständig)")
            
            sub_choice = input("Wähle Option (1-3): ").strip()
            
            if sub_choice == "1":
                pdf_files = pipeline.find_pdf_files(pdf_directory, limit=3)
            elif sub_choice == "2":
                pdf_files = pipeline.find_pdf_files(pdf_directory, limit=5)
            elif sub_choice == "3":
                pdf_files = pipeline.find_pdf_files(pdf_directory)
            else:
                pdf_files = pipeline.find_pdf_files(pdf_directory, limit=3)
            
            if not pdf_files:
                print(f"Keine PDF-Dateien in {pdf_directory} gefunden!")
                continue
            
            print(f"\nAusgewählt: {len(pdf_files)} Dateien für Hardware Waker")
            print(f"Verarbeite {pipeline.max_concurrent} Dokumente gleichzeitig!")
            print("Das SOLLTE deine Hardware aufwecken!")
            
            response = input(f"\nWAKE UP HARDWARE und verarbeite {len(pdf_files)} Dateien? (y/n): ").lower().strip()
            if response != 'y':
                print("Hardware Waker abgebrochen.")
                continue
            
            # Process batch
            results = await pipeline.process_batch_hardware_waker(pdf_files)
            pipeline.print_status_summary(results)
            
        elif choice == "4":
            # Single Document Processing
            print("\n=== EINZELNES DOKUMENT ===")
            document_id = input("Document ID eingeben: ").strip()
            
            if not document_id:
                print("Keine Document ID eingegeben.")
                continue
            
            # Get document info
            doc_info = await pipeline.database_service.get_document(document_id)
            if not doc_info:
                print(f"Document {document_id} nicht gefunden!")
                continue
            
            filename = doc_info.filename if doc_info.filename else 'Unknown'
            file_path = doc_info.storage_path if doc_info.storage_path else ''
            
            print(f"Gefunden: {filename}")
            print(f"File path: {file_path}")
            
            response = input(f"\nVerarbeite verbleibende Stages für {filename}? (y/n): ").lower().strip()
            if response != 'y':
                print("Verarbeitung abgebrochen.")
                continue
            
            result = await pipeline.process_document_remaining_stages(document_id, filename, file_path)
            
            if result['success']:
                print(f"\n[SUCCESS] Erfolgreich verarbeitet: {result['filename']}!")
                print(f"Images processed: {result['images']}")
            else:
                print(f"\n[FAILED] Fehler bei {result['filename']}: {result['error']}")
                
        elif choice == "5":
            # Batch Processing
            print("\n=== BATCH PROCESSING ===")
            
            # Find service_documents directory intelligently
            pdf_directory = pipeline.find_service_documents_directory()
            if not pdf_directory:
                print("❌ Cannot find service_documents directory with PDFs!")
                print("💡 Please create a 'service_documents' directory and add PDF files")
                continue
            
            pdf_files = pipeline.find_pdf_files(pdf_directory)
            
            if not pdf_files:
                print(f"Keine PDF-Dateien in {pdf_directory} gefunden!")
                continue
            
            print(f"Gefunden: {len(pdf_files)} PDF-Dateien")
            response = input(f"\nVerarbeite ALLE {len(pdf_files)} PDFs? (y/n): ").lower().strip()
            if response != 'y':
                print("Batch Processing abgebrochen.")
                continue
            
            results = await pipeline.process_batch_hardware_waker(pdf_files)
            pipeline.print_status_summary(results)
            
        elif choice == "6":
            # Debug
            print("\n=== DEBUG INFORMATIONEN ===")
            print(f"Current Working Directory: {os.getcwd()}")
            print(f"Script Location: {os.path.abspath(__file__)}")
            print(f"Script Directory: {os.path.dirname(os.path.abspath(__file__))}")
            
            print("\n🔍 Searching for service_documents...")
            pdf_directory = pipeline.find_service_documents_directory()
            
            if pdf_directory:
                print(f"\n✅ Service Documents Directory: {os.path.abspath(pdf_directory)}")
                pdf_files = pipeline.find_pdf_files(pdf_directory)
                print(f"📁 PDF Files found: {len(pdf_files)}")
                if pdf_files:
                    print("First 5 PDF files:")
                    for i, pdf in enumerate(pdf_files[:5]):
                        print(f"  {i+1}. {os.path.basename(pdf)}")
            else:
                print("\n❌ No service_documents directory found!")
                print("💡 Create a 'service_documents' directory and add PDF files")
            
        elif choice == "7":
            # Exit
            print("\nAuf Wiedersehen! KR-AI-Engine Master Pipeline beendet.")
            break
            
        else:
            print("Ungültige Option. Bitte 1-7 wählen.")

if __name__ == "__main__":
    asyncio.run(main())
