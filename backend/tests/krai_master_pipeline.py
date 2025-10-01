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
from services.database_service_production import DatabaseService
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
        
        # Load environment variables from specific .env files
        # Try multiple possible locations for .env files (universal approach)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        current_dir = os.getcwd()
        
        # Define specific .env files to load
        env_files = [
            'env.database',      # Database configuration
            'env.storage',       # Storage configuration  
            'env.ai',           # AI configuration
            'env.system',       # System configuration
            '.env'              # Legacy fallback
        ]
        
        # Build search paths for each .env file
        base_paths = [
            # Relative to script location
            script_dir,                                         # Same as script
            os.path.join(script_dir, '..'),                     # Parent of script
            os.path.join(script_dir, '..', '..'),               # Two levels up from script
            os.path.join(script_dir, '..', '..', '..'),         # Three levels up from script
            
            # Relative to current working directory
            current_dir,                                        # Current directory
            os.path.join(current_dir, '..'),                    # Parent of current
            os.path.join(current_dir, '..', '..'),              # Two levels up from current
            
            # Absolute paths (fallback)
            '.',                                                # Same directory (relative)
            '..',                                               # Parent directory (relative)
            '../..',                                            # Two levels up (relative)
        ]
        
        env_paths = []
        for env_file in env_files:
            for base_path in base_paths:
                env_paths.append(os.path.join(base_path, env_file))
        
        env_loaded = False
        loaded_files = []
        
        # Load all found .env files (not just the first one)
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                loaded_files.append(os.path.abspath(env_path))
                env_loaded = True
        
        if loaded_files:
            print(f"✅ Environment loaded from {len(loaded_files)} file(s):")
            for file_path in loaded_files:
                print(f"   📄 {file_path}")
        else:
            env_loaded = False
        
        if not env_loaded:
            print("⚠️  No .env file found in any expected location!")
            print("💡 Please ensure .env files exist in project root")
            print("🔍 Searched for these files:")
            for env_file in env_files:
                print(f"   - {env_file}")
            print("🔍 In these locations:")
            for base_path in base_paths[:3]:  # Show first 3 paths
                print(f"   - {os.path.abspath(base_path)}")
            
            # Try to create .env files from templates if available
            self._try_create_env_from_templates()
            raise RuntimeError("Environment files not found")
        
        # Initialize services after environment is loaded
        await self._initialize_services_after_env_loaded()
    
    def _try_create_env_from_templates(self):
        """Try to create .env files from templates if available"""
        try:
            # Template mappings
            template_mappings = {
                'env.database': ['env.database.template', 'env.template'],
                'env.storage': ['env.storage.template', 'env.template'],
                'env.ai': ['env.ai.template', 'env.template'],
                'env.system': ['env.system.template', 'env.template'],
                '.env': ['env.template', 'backend/env.example']
            }
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, '..', '..')
            
            created_files = []
            
            for env_file, template_options in template_mappings.items():
                target_path = os.path.join(project_root, env_file)
                
                # Skip if file already exists
                if os.path.exists(target_path):
                    continue
                
                # Look for template files
                for template_name in template_options:
                    template_paths = [
                        os.path.join(project_root, template_name),
                        os.path.join(project_root, '..', template_name),
                        os.path.join(script_dir, template_name),
                        template_name  # Relative path
                    ]
                    
                    for template_path in template_paths:
                        if os.path.exists(template_path):
                            print(f"📋 Found template: {template_path}")
                            print(f"💡 Creating: {env_file}")
                            
                            # Create directory if it doesn't exist
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            
                            # Copy template to target
                            import shutil
                            shutil.copy2(template_path, target_path)
                            
                            created_files.append(env_file)
                            break
                    else:
                        continue  # No template found, try next template
                    break  # Template found and copied, move to next env file
            
            if created_files:
                print(f"✅ Created {len(created_files)} .env file(s): {', '.join(created_files)}")
                print("⚠️  Please edit these files with your actual credentials")
                return True
            else:
                print("❌ No template files found to create .env files from")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create .env files from templates: {e}")
            return False
    
    async def _initialize_services_after_env_loaded(self):
        """Initialize services after environment variables are loaded"""
        # Debug: Show loaded environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url:
            print("❌ SUPABASE_URL not found in environment variables!")
        else:
            print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
            
        if not supabase_key:
            print("❌ SUPABASE_ANON_KEY not found in environment variables!")
        else:
            print(f"✅ SUPABASE_ANON_KEY: {supabase_key[:20]}...")
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
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
    
    async def get_document_stage_status(self, document_id: str) -> Dict[str, bool]:
        """Check which stages have been completed for a document"""
        stage_status = {
            'upload': False,
            'text': False,
            'image': False,
            'classification': False,
            'metadata': False,
            'storage': False,
            'embedding': False,
            'search': False
        }
        
        try:
            # Check if document exists (upload stage)
            doc_info = await self.database_service.get_document(document_id)
            if doc_info:
                stage_status['upload'] = True
                
                # Check if document is classified (classification stage)
                if doc_info.manufacturer_id and doc_info.document_type != 'unknown':
                    stage_status['classification'] = True
            
            # Check if chunks exist (text stage)
            chunks_result = self.database_service.client.table('chunks').select('id').eq('document_id', document_id).limit(1).execute()
            if chunks_result.data:
                stage_status['text'] = True
            
            # Check if images exist (image stage)
            images_result = self.database_service.client.table('images').select('id').eq('document_id', document_id).limit(1).execute()
            if images_result.data:
                stage_status['image'] = True
            
            # Check if embeddings exist (embedding stage)
            embeddings_result = self.database_service.client.table('embeddings').select('id').eq('document_id', document_id).limit(1).execute()
            if embeddings_result.data:
                stage_status['embedding'] = True
            
            # Check if search analytics exist (search stage)
            search_result = self.database_service.client.table('search_analytics').select('id').eq('document_id', document_id).limit(1).execute()
            if search_result.data:
                stage_status['search'] = True
            
            # For now, assume metadata and storage are done if other stages are done
            if stage_status['image'] and stage_status['classification']:
                stage_status['metadata'] = True
                stage_status['storage'] = True
            
        except Exception as e:
            print(f"Error checking stage status: {e}")
        
        return stage_status
    
    async def process_document_smart_stages(self, document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
        """Process only the missing stages for a document"""
        try:
            print(f"\nSmart Processing for: {filename}")
            print(f"  Document ID: {document_id}")
            
            # Check current stage status
            stage_status = await self.get_document_stage_status(document_id)
            
            print(f"  Current Status:")
            for stage, completed in stage_status.items():
                status_icon = "✅" if completed else "❌"
                print(f"    {stage.capitalize()}: {status_icon}")
            
            # Find missing stages
            missing_stages = [stage for stage, completed in stage_status.items() if not completed]
            
            if not missing_stages:
                print(f"  ✅ All stages already completed for {filename}")
                return {
                    'success': True,
                    'filename': filename,
                    'stages_completed': len(stage_status),
                    'message': 'All stages already completed'
                }
            
            print(f"  Missing stages: {', '.join(missing_stages)}")
            
            # Create processing context
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
            
            completed_stages = []
            failed_stages = []
            
            # Process only missing stages
            if 'text' in missing_stages:
                print(f"  [2/8] Text Processing: {filename}")
                try:
                    result2 = await self.processors['text'].process(context)
                    if result2.success:
                        completed_stages.append('text')
                        print(f"    ✅ Text processing completed")
                    else:
                        failed_stages.append('text')
                        print(f"    ❌ Text processing failed: {result2.message}")
                except Exception as e:
                    failed_stages.append('text')
                    print(f"    ❌ Text processing error: {e}")
            
            if 'image' in missing_stages:
                print(f"  [3/8] Image Processing: {filename}")
                try:
                    result3 = await self.processors['image'].process(context)
                    if result3.success:
                        completed_stages.append('image')
                        images_count = result3.data.get('images_processed', 0)
                        print(f"    ✅ Image processing completed: {images_count} images")
                    else:
                        failed_stages.append('image')
                        print(f"    ❌ Image processing failed: {result3.message}")
                except Exception as e:
                    failed_stages.append('image')
                    print(f"    ❌ Image processing error: {e}")
            
            if 'classification' in missing_stages:
                print(f"  [4/8] Classification: {filename}")
                try:
                    result4 = await self.processors['classification'].process(context)
                    if result4.success:
                        completed_stages.append('classification')
                        print(f"    ✅ Classification completed")
                    else:
                        failed_stages.append('classification')
                        print(f"    ❌ Classification failed: {result4.message}")
                except Exception as e:
                    failed_stages.append('classification')
                    print(f"    ❌ Classification error: {e}")
            
            if 'metadata' in missing_stages:
                print(f"  [5/8] Metadata: {filename}")
                try:
                    result5 = await self.processors['metadata'].process(context)
                    if result5.success:
                        completed_stages.append('metadata')
                        print(f"    ✅ Metadata processing completed")
                    else:
                        failed_stages.append('metadata')
                        print(f"    ❌ Metadata processing failed: {result5.message}")
                except Exception as e:
                    failed_stages.append('metadata')
                    print(f"    ❌ Metadata processing error: {e}")
            
            if 'storage' in missing_stages:
                print(f"  [6/8] Storage: {filename}")
                try:
                    result6 = await self.processors['storage'].process(context)
                    if result6.success:
                        completed_stages.append('storage')
                        print(f"    ✅ Storage processing completed")
                    else:
                        failed_stages.append('storage')
                        print(f"    ❌ Storage processing failed: {result6.message}")
                except Exception as e:
                    failed_stages.append('storage')
                    print(f"    ❌ Storage processing error: {e}")
            
            if 'embedding' in missing_stages:
                print(f"  [7/8] Embeddings: {filename}")
                try:
                    result7 = await self.processors['embedding'].process(context)
                    if result7.success:
                        completed_stages.append('embedding')
                        embeddings_count = result7.data.get('embeddings_created', 0)
                        print(f"    ✅ Embedding processing completed: {embeddings_count} embeddings")
                    else:
                        failed_stages.append('embedding')
                        print(f"    ❌ Embedding processing failed: {result7.message}")
                except Exception as e:
                    failed_stages.append('embedding')
                    print(f"    ❌ Embedding processing error: {e}")
            
            if 'search' in missing_stages:
                print(f"  [8/8] Search: {filename}")
                try:
                    result8 = await self.processors['search'].process(context)
                    if result8.success:
                        completed_stages.append('search')
                        print(f"    ✅ Search processing completed")
                    else:
                        failed_stages.append('search')
                        print(f"    ❌ Search processing failed: {result8.message}")
                except Exception as e:
                    failed_stages.append('search')
                    print(f"    ❌ Search processing error: {e}")
            
            # Update document status
            if not failed_stages:
                await self.database_service.update_document_status(document_id, 'completed')
                print(f"  ✅ Document {filename} fully processed!")
            else:
                await self.database_service.update_document_status(document_id, 'failed')
                print(f"  ⚠️ Document {filename} partially processed (failed stages: {failed_stages})")
            
            return {
                'success': len(failed_stages) == 0,
                'filename': filename,
                'completed_stages': completed_stages,
                'failed_stages': failed_stages,
                'total_stages': len(completed_stages) + len(failed_stages)
            }
            
        except Exception as e:
            print(f"Error in smart processing: {e}")
            return {
                'success': False,
                'filename': filename,
                'error': str(e)
            }
    
    async def process_document_remaining_stages(self, document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
        """Process remaining stages for a document (legacy method - now uses smart processing)"""
        return await self.process_document_smart_stages(document_id, filename, file_path)
    
    async def process_single_document_full_pipeline(self, file_path: str, doc_index: int, total_docs: int) -> Dict[str, Any]:
        """Process a single document through all 8 stages - Smart version that handles existing documents"""
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
            
            # Check if document already exists (deduplication)
            print(f"  [{doc_index}] DEBUG: result1.success={result1.success}, duplicate={result1.data.get('duplicate')}")
            if result1.success and result1.data.get('duplicate'):
                # Document already exists - use Smart Processing for remaining stages
                print(f"  [{doc_index}] Document exists - using Smart Processing for remaining stages")
                document_id = result1.data.get('document_id')
                file_path = f"../service_documents/{filename}"
                
                # Use Smart Processing to handle only missing stages
                smart_result = await self.process_document_smart_stages(document_id, filename, file_path)
                
                if smart_result['success']:
                    return {
                        'success': True,
                        'document_id': document_id,
                        'filename': filename,
                        'file_size': file_size,
                        'chunks': 0,  # Smart processing handles this
                        'images': 0,  # Smart processing handles this
                        'smart_processing': True,
                        'completed_stages': smart_result.get('completed_stages', []),
                        'message': 'Smart processing completed'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Smart processing failed: {smart_result.get("error", "Unknown error")}',
                        'filename': filename
                    }
            elif result1.success:
                # New document - get info from upload result and continue with all stages
                context.document_id = result1.data.get('document_id')
                context.file_hash = result1.data.get('file_hash', '')
                context.document_type = result1.data.get('document_type', '')
            else:
                # Upload failed
                return {'success': False, 'error': f'Upload failed: {result1.message}'}
            
            # For new documents, continue with all stages
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
                'images': images_count,
                'smart_processing': False
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
        """Monitor hardware usage and pipeline progress during processing"""
        last_doc_count = 0
        last_classified_count = 0
        last_chunk_count = 0
        last_error_count = 0
        show_detailed_view = False
        
        # PowerShell-optimized initial setup
        print(f"\n💡 PowerShell Mode: Press 'd' for detailed view, 'q' to quit")
        print(f"{'='*80}")
        
        # Set PowerShell console properties if available
        try:
            import os
            if os.name == 'nt':  # Windows
                # Enable ANSI color support in PowerShell (simplified approach)
                try:
                    os.system('chcp 65001 >nul 2>&1')  # Set UTF-8 code page
                except:
                    pass
        except:
            pass
        
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Get hardware status
                cpu_percent = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory()
                ram_percent = ram.percent
                ram_used_gb = (ram.total - ram.available) / 1024 / 1024 / 1024
                
                # Get GPU status
                gpu_info = self._get_gpu_status()
                
                # Get pipeline progress
                pipeline_status = await self._get_pipeline_status()
                
                # Get error count
                error_count = await self._get_error_count()
                
                # Check if we should show detailed view
                if error_count > last_error_count:
                    show_detailed_view = True
                    last_error_count = error_count
                
                # Create compact status line
                gpu_status = ""
                if gpu_info:
                    gpu_status = f" | GPU: {gpu_info['memory_used']:.1f}/{gpu_info['memory_total']:.1f}GB"
                    if gpu_info['utilization'] > 0:
                        gpu_status += f" ({gpu_info['utilization']:.1f}%)"
                else:
                    gpu_status = " | GPU: N/A"
                
                # Create activity indicators
                activity_indicators = []
                if cpu_percent > 50:
                    activity_indicators.append("🔥CPU")
                if ram_percent > 60:
                    activity_indicators.append("💾RAM")
                if gpu_info and gpu_info['utilization'] > 10:
                    activity_indicators.append("🎮GPU")
                
                activity_str = " [" + ",".join(activity_indicators) + "]" if activity_indicators else ""
                
                # PowerShell-optimized progress bar (use simpler characters)
                progress_bar_length = 25
                progress_filled = int((pipeline_status['overall_progress'] / 100) * progress_bar_length)
                progress_bar = "█" * progress_filled + "░" * (progress_bar_length - progress_filled)
                
                # Create compact status line with error indicator
                error_indicator = f" ❌{error_count}" if error_count > 0 else ""
                status_line = (
                    f"🔄 KR-AI Pipeline | "
                    f"CPU:{cpu_percent:4.1f}% RAM:{ram_percent:4.1f}%{gpu_status} | "
                    f"Docs:{pipeline_status['total_docs']} Class:{pipeline_status['classified_docs']}{error_indicator} | "
                    f"Progress: {progress_bar} {pipeline_status['overall_progress']:4.1f}%{activity_str}"
                )
                
                # PowerShell-optimized status display
                # Use carriage return to overwrite the same line
                print(f"\r{status_line}", end="", flush=True)
                
                # Get current status values
                current_doc_count = pipeline_status['total_docs']
                current_classified_count = pipeline_status['classified_docs']
                current_chunk_count = pipeline_status['total_chunks']
                
                # Add newline only for detailed updates to prevent PowerShell line wrapping issues
                if (current_doc_count != last_doc_count or 
                    current_classified_count != last_classified_count or 
                    current_chunk_count != last_chunk_count or
                    show_detailed_view):
                    print()  # New line before detailed view
                
                # Check for keyboard input (Windows compatible)
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key == 'd':
                            show_detailed_view = True
                        elif key == 'q':
                            print(f"\n🛑 Monitoring stopped by user")
                            break
                except:
                    # Fallback: skip keyboard input on non-Windows or if msvcrt not available
                    pass
                
                # Check if we should show detailed view
                if (current_doc_count != last_doc_count or 
                    current_classified_count != last_classified_count or 
                    current_chunk_count != last_chunk_count or
                    show_detailed_view):
                    
                    # Print detailed pipeline overview
                    await self._print_detailed_pipeline_view(pipeline_status, error_count)
                    
                    # Update tracking variables
                    last_doc_count = current_doc_count
                    last_classified_count = current_classified_count
                    last_chunk_count = current_chunk_count
                    show_detailed_view = False
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                pass
    
    def _get_gpu_status(self) -> Dict[str, Any]:
        """Get GPU status information"""
        try:
            # Method 1: Try nvidia-smi (NVIDIA GPUs)
            import subprocess
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=name,memory.used,memory.total,utilization.gpu', 
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(', ')
                    if len(parts) >= 4:
                        return {
                            'name': parts[0],
                            'memory_used': float(parts[1]) / 1024,  # MB to GB
                            'memory_total': float(parts[2]) / 1024,  # MB to GB
                            'memory_percent': (float(parts[1]) / float(parts[2])) * 100,
                            'utilization': float(parts[3])
                        }
        except:
            pass
        
        try:
            # Method 2: Try wmic for Intel/AMD GPUs (Windows)
            result = subprocess.run([
                'wmic', 'path', 'win32_VideoController', 'get', 'name,AdapterRAM', 
                '/format:csv'
            ], capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                for line in lines:
                    if 'Name' not in line and line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            gpu_name = parts[1].strip()
                            if gpu_name and gpu_name != '':
                                # Estimate memory for integrated GPUs
                                estimated_memory = 2.0  # Default estimate
                                if 'Intel' in gpu_name:
                                    estimated_memory = 2.0
                                elif 'AMD' in gpu_name or 'Radeon' in gpu_name:
                                    estimated_memory = 4.0
                                
                                return {
                                    'name': gpu_name,
                                    'memory_used': estimated_memory * 0.3,  # Estimate usage
                                    'memory_total': estimated_memory,
                                    'memory_percent': 30.0,  # Estimate
                                    'utilization': 0.0  # Cannot measure for integrated GPUs
                                }
        except:
            pass
        
        return None
    
    async def _get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline processing status"""
        try:
            # Use simple table queries for status
            docs_result = self.database_service.client.table('documents').select('*').execute()
            chunks_result = self.database_service.client.table('chunks').select('*').execute()
            images_result = self.database_service.client.table('images').select('*').execute()
            
            # Process results
            total_docs = len(docs_result.data) if docs_result.data else 0
            classified_docs = len([d for d in docs_result.data if d.get('manufacturer')]) if docs_result.data else 0
            total_chunks = len(chunks_result.data) if chunks_result.data else 0
            total_images = len(images_result.data) if images_result.data else 0
            
            # Get recent documents
            recent_docs = sorted(docs_result.data, key=lambda x: x.get('created_at', ''), reverse=True)[:3] if docs_result.data else []
            
            # Calculate overall progress based on actual pipeline stages
            if total_docs > 0:
                # Stage 1: Upload (always 100% if documents exist)
                upload_progress = 100.0
                
                # Stage 2-3: Text & Image Processing (based on chunks and images)
                text_image_progress = 0
                if total_chunks > 0:
                    # Assume ~1000 chunks per document average
                    expected_chunks = total_docs * 1000
                    text_image_progress = min(100, (total_chunks / expected_chunks) * 100)
                
                # Stage 4: Classification (based on classified documents)
                classification_progress = (classified_docs / total_docs) * 100
                
                # Overall progress: Weighted average
                overall_progress = (
                    upload_progress * 0.1 +           # 10% for upload
                    text_image_progress * 0.4 +       # 40% for text/image processing
                    classification_progress * 0.5     # 50% for classification
                )
            else:
                overall_progress = 0
            
            # Determine current stage
            current_stage = None
            if recent_docs:
                latest_doc = recent_docs[0]
                if latest_doc.get('manufacturer'):
                    current_stage = f"Classification Complete - {latest_doc.get('filename', 'Unknown')}"
                elif latest_doc.get('id') in [c.get('document_id') for c in chunks_result.data]:
                    current_stage = f"Text Processing Complete - {latest_doc.get('filename', 'Unknown')}"
                else:
                    current_stage = f"Upload Complete - {latest_doc.get('filename', 'Unknown')}"
            
            return {
                'total_docs': total_docs,
                'classified_docs': classified_docs,
                'pending_docs': total_docs - classified_docs,
                'total_chunks': total_chunks,
                'total_images': total_images,
                'overall_progress': overall_progress,
                'current_stage': current_stage,
                'recent_activity': recent_docs
            }
            
        except Exception as e:
            print(f"Pipeline status error: {e}")
            return {
                'total_docs': 0,
                'classified_docs': 0,
                'pending_docs': 0,
                'total_chunks': 0,
                'total_images': 0,
                'overall_progress': 0,
                'current_stage': 'Status unavailable',
                'recent_activity': []
            }
    
    async def _get_error_count(self) -> int:
        """Get count of failed documents"""
        try:
            # Use Supabase client directly for error count
            result = self.database_service.client.rpc('get_error_document_count').execute()
            return result.data if result.data else 0
            
        except Exception as e:
            # Fallback: simple count of documents without classification
            try:
                docs_result = self.database_service.client.table('documents').select('id').is_('manufacturer', 'null').execute()
                return len(docs_result.data) if docs_result.data else 0
            except:
                return 0
    
    async def _print_detailed_pipeline_view(self, pipeline_status: Dict[str, Any], error_count: int):
        """Print detailed pipeline overview with progress bars for each stage (PowerShell optimized)"""
        print(f"\n{'='*70}")
        print(f"📊 KR-AI PIPELINE OVERVIEW")
        print(f"{'='*70}")
        
        # Stage 1: Upload
        upload_progress = 100.0 if pipeline_status['total_docs'] > 0 else 0
        upload_bar = "█" * 15 + "░" * 0 if upload_progress == 100 else "░" * 15
        print(f"📤 Upload:        {upload_bar} {upload_progress:5.1f}% ({pipeline_status['total_docs']} docs)")
        
        # Stage 2: Text Processing
        text_progress = 0
        if pipeline_status['total_docs'] > 0:
            expected_chunks = pipeline_status['total_docs'] * 1000
            text_progress = min(100, (pipeline_status['total_chunks'] / expected_chunks) * 100)
        
        text_bar_length = int((text_progress / 100) * 15)
        text_bar = "█" * text_bar_length + "░" * (15 - text_bar_length)
        print(f"📄 Text:          {text_bar} {text_progress:5.1f}% ({pipeline_status['total_chunks']:,} chunks)")
        
        # Stage 3: Image Processing
        image_progress = 0
        if pipeline_status['total_docs'] > 0:
            expected_images = pipeline_status['total_docs'] * 100
            image_progress = min(100, (pipeline_status['total_images'] / expected_images) * 100)
        
        image_bar_length = int((image_progress / 100) * 15)
        image_bar = "█" * image_bar_length + "░" * (15 - image_bar_length)
        print(f"🖼️  Images:        {image_bar} {image_progress:5.1f}% ({pipeline_status['total_images']:,} images)")
        
        # Stage 4: Classification
        class_progress = 0
        if pipeline_status['total_docs'] > 0:
            class_progress = (pipeline_status['classified_docs'] / pipeline_status['total_docs']) * 100
        
        class_bar_length = int((class_progress / 100) * 15)
        class_bar = "█" * class_bar_length + "░" * (15 - class_bar_length)
        print(f"🏷️  Classification: {class_bar} {class_progress:5.1f}% ({pipeline_status['classified_docs']}/{pipeline_status['total_docs']} docs)")
        
        # Overall Progress
        overall_bar_length = int((pipeline_status['overall_progress'] / 100) * 20)
        overall_bar = "█" * overall_bar_length + "░" * (20 - overall_bar_length)
        print(f"\n🎯 OVERALL:       {overall_bar} {pipeline_status['overall_progress']:5.1f}%")
        
        # Error Status
        if error_count > 0:
            print(f"❌ ERRORS: {error_count} docs stuck | 💡 Run: python backend/tests/pipeline_recovery.py")
        
        # Current Activity
        if pipeline_status['current_stage']:
            print(f"🔄 CURRENT: {pipeline_status['current_stage']}")
        
        print(f"{'='*70}")
    
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
        
        # Supported document formats
        supported_extensions = ['.pdf', '.pdfz', '.docx', '.doc', '.txt', '.rtf']
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in supported_extensions:
                    pdf_files.append(os.path.join(root, file))
                    if limit and len(pdf_files) >= limit:
                        return sorted(pdf_files)
        
        # Count by extension
        extension_counts = {}
        for file in pdf_files:
            ext = os.path.splitext(file)[1].lower()
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        print(f"📁 Found {len(pdf_files)} document files in {directory}")
        for ext, count in extension_counts.items():
            print(f"   {ext}: {count} files")
        
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
                    # Count all supported document types
                    supported_extensions = ['.pdf', '.pdfz', '.docx', '.doc', '.txt', '.rtf']
                    doc_count = sum(1 for f in files if os.path.splitext(f)[1].lower() in supported_extensions)
                    
                    if doc_count > 0:
                        print(f"✅ Found service_documents with {doc_count} document files: {os.path.abspath(path)}")
                        return path
                    else:
                        print(f"📁 Found directory but no supported documents: {os.path.abspath(path)}")
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
        print("2. Smart Processing - Nur fehlende Stages verarbeiten")
        print("3. Hardware Waker - Verarbeite neue Dokumente (CPU/GPU)")
        print("4. Einzelnes Dokument verarbeiten")
        print("5. Batch Processing - Alle Dokumente verarbeiten")
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
            # Smart Processing - Only Missing Stages
            print("\n=== SMART PROCESSING - MISSING STAGES ONLY ===")
            documents = await pipeline.get_documents_needing_processing()
            
            if not documents:
                print("Keine Dokumente gefunden die weitere Verarbeitung brauchen!")
                continue
            
            print(f"Gefunden: {len(documents)} Dokumente - prüfe welche Stages fehlen...")
            
            # Show first few documents with their stage status
            print("\nErste 5 Dokumente mit Stage-Status:")
            for i, doc in enumerate(documents[:5]):
                stage_status = await pipeline.get_document_stage_status(doc['id'])
                missing_stages = [stage for stage, completed in stage_status.items() if not completed]
                status_text = f"Missing: {', '.join(missing_stages)}" if missing_stages else "All complete"
                print(f"  {i+1}. {doc['filename']} - {status_text}")
            
            if len(documents) > 5:
                print(f"  ... und {len(documents) - 5} weitere")
            
            response = input(f"\nSmart Process {len(documents)} Dokumente (nur fehlende Stages)? (y/n): ").lower().strip()
            if response != 'y':
                print("Smart Processing abgebrochen.")
                continue
            
            # Process documents with smart processing
            results = {'successful': [], 'failed': [], 'total_files': len(documents)}
            
            for i, doc in enumerate(documents):
                print(f"\n[{i+1}/{len(documents)}] Smart Processing: {doc['filename']}")
                result = await pipeline.process_document_smart_stages(
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
            print("1. Test mit 3 Dokumenten (schneller Test)")
            print("2. Test mit 5 Dokumenten (mittlerer Test)")
            print("3. Verarbeite alle Dokumente (vollständig)")
            
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
                print(f"Keine Dokumente in {pdf_directory} gefunden!")
                continue
            
            print(f"\nAusgewählt: {len(pdf_files)} Dokumente für Hardware Waker")
            print(f"Verarbeite {pipeline.max_concurrent} Dokumente gleichzeitig!")
            print("Das SOLLTE deine Hardware aufwecken!")
            
            response = input(f"\nWAKE UP HARDWARE und verarbeite {len(pdf_files)} Dokumente? (y/n): ").lower().strip()
            if response != 'y':
                print("Hardware Waker abgebrochen.")
                continue
            
            # Process batch
            results = await pipeline.process_batch_hardware_waker(pdf_files)
            pipeline.print_status_summary(results)
            
            # FORCE Smart Processing for all documents (regardless of upload results)
            print("\n=== FORCED SMART PROCESSING - ALL DOCUMENTS ===")
            all_docs = pipeline.database_service.client.table('documents').select('*').execute()
            
            if all_docs.data:
                print(f"Found {len(all_docs.data)} total documents - forcing smart processing...")
                stage_results = {'successful': [], 'failed': [], 'total_files': len(all_docs.data)}
                
                for i, doc in enumerate(all_docs.data):
                    print(f"\n[{i+1}/{len(all_docs.data)}] Forced Smart processing: {doc['filename']}")
                    file_path = f"../service_documents/{doc['filename']}"
                    
                    result = await pipeline.process_document_smart_stages(
                        doc['id'], doc['filename'], file_path
                    )
                    
                    if result['success']:
                        stage_results['successful'].append(result)
                    else:
                        stage_results['failed'].append(result)
                
                stage_results['success_rate'] = len(stage_results['successful']) / len(all_docs.data) * 100
                print("\n=== FORCED SMART PROCESSING SUMMARY ===")
                pipeline.print_status_summary(stage_results)
            else:
                print("No documents found in database!")
            
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
                print(f"Keine Dokumente in {pdf_directory} gefunden!")
                continue
            
            print(f"Gefunden: {len(pdf_files)} Dokumente")
            response = input(f"\nVerarbeite ALLE {len(pdf_files)} Dokumente? (y/n): ").lower().strip()
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
                print(f"📁 Document Files found: {len(pdf_files)}")
                if pdf_files:
                    print("First 5 document files:")
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
