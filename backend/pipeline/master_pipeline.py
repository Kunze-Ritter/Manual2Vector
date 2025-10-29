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
from backend.services.database_service_production import DatabaseService
from backend.services.object_storage_service import ObjectStorageService
from backend.services.ai_service import AIService
from backend.services.config_service import ConfigService
from backend.services.features_service import FeaturesService
from backend.services.quality_check_service import QualityCheckService
from backend.services.file_locator_service import FileLocatorService
from backend.utils.colored_logging import apply_colored_logging_globally

from backend.processors.upload_processor import UploadProcessor
from backend.processors.text_processor_optimized import OptimizedTextProcessor
from backend.processors.image_processor import ImageProcessor
from backend.processors.classification_processor import ClassificationProcessor
from backend.processors.chunk_preprocessor import ChunkPreprocessor
from backend.processors.metadata_processor_ai import MetadataProcessorAI
from backend.processors.link_extraction_processor_ai import LinkExtractionProcessorAI
from backend.processors.storage_processor import StorageProcessor
from backend.processors.embedding_processor import EmbeddingProcessor
from backend.processors.search_processor import SearchProcessor

from backend.core.base_processor import ProcessingContext

class KRMasterPipeline:
    """
    Master Pipeline für alle KR-AI-Engine Funktionen
    """
    
    def __init__(self, force_continue_on_errors=True):
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        self.force_continue_on_errors = force_continue_on_errors
        
        # Setup colored logging globally (ERROR = RED, WARNING = YELLOW, INFO = GREEN)
        apply_colored_logging_globally(level=logging.INFO)
        self.logger = logging.getLogger("krai.master_pipeline")
        self.interactive_console = sys.stdout.isatty()
        
        # Get hardware info
        cpu_count = mp.cpu_count()
        # Use 75% of cores for concurrent docs
        self.max_concurrent = max(4, int(cpu_count * 0.75))  # Min 4, max 75% of cores
        
        self.logger.info(
            "performance",
            concurrent_documents=self.max_concurrent,
            cpu_cores=cpu_count
        )
        self.logger.info(
            "initialized",
            concurrent_documents=self.max_concurrent
        )
        
    async def initialize_services(self):
        """Initialize all services"""
        self.logger.info("Initializing KR Master Pipeline services")
        
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
            self.logger.info(
                "environment_loaded",
                num_files=len(loaded_files),
                files="; ".join(loaded_files)
            )
        else:
            env_loaded = False
        
        if not env_loaded:
            self.logger.warning("No .env file found in expected locations")
            self.logger.info("Searched for env files: %s", ", ".join(env_files))
            self.logger.info(
                "Search base paths (sample): %s",
                ", ".join(os.path.abspath(path) for path in base_paths[:3])
            )
            
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
                            self.logger.info("📋 Found template: %s", template_path)
                            self.logger.info("💡 Creating: %s", env_file)
                            
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
                self.logger.info(
                    "✅ Created %s .env file(s): %s",
                    len(created_files),
                    ", ".join(created_files)
                )
                self.logger.warning("Please edit newly created .env files with actual credentials")
                return True
            else:
                self.logger.warning("No template files found to create .env files from")
                return False
                
        except Exception as e:
            self.logger.error("Failed to create .env files from templates", exc_info=True)
            return False
    
    async def _initialize_services_after_env_loaded(self):
        """Initialize services after environment variables are loaded"""
        # Debug: Show loaded environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url:
            self.logger.error("SUPABASE_URL not found in environment variables!")
        else:
            self.logger.info("✅ SUPABASE_URL: %s...", supabase_url[:30])
            
        if not supabase_key:
            self.logger.error("SUPABASE_ANON_KEY not found in environment variables!")
        else:
            self.logger.info("✅ SUPABASE_ANON_KEY: %s...", supabase_key[:20])
        
        # Get Service Role Key for elevated permissions (cross-schema via PostgREST)
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if service_role_key:
            self.logger.info(
                "✅ SUPABASE_SERVICE_ROLE_KEY: %s... (PostgREST cross-schema enabled)",
                service_role_key[:20]
            )
        else:
            self.logger.warning("SUPABASE_SERVICE_ROLE_KEY not found - will try POSTGRES_URL fallback")
        
        # Get PostgreSQL URL for direct connection (alternative method)
        postgres_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
        if postgres_url:
            self.logger.info("✅ POSTGRES_URL: %s... (asyncpg fallback enabled)", postgres_url[:40])
        else:
            self.logger.warning("POSTGRES_URL not found - using PostgREST only")
        
        # Initialize database service with multiple connection options
        self.database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            postgres_url=postgres_url,  # asyncpg (if connection works)
            service_role_key=service_role_key  # PostgREST with elevated permissions
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
        
        # Initialize quality check service
        self.quality_service = QualityCheckService(self.database_service)
        
        # Initialize file locator service
        self.file_locator = FileLocatorService()
        
        # Initialize all processors
        self.processors = {
            'upload': UploadProcessor(self.database_service),
            'text': OptimizedTextProcessor(self.database_service, self.config_service),
            'image': ImageProcessor(self.database_service, self.storage_service, self.ai_service),
            'classification': ClassificationProcessor(self.database_service, self.ai_service, self.features_service),
            'chunk_prep': ChunkPreprocessor(self.database_service),
            'links': LinkExtractionProcessorAI(self.database_service, self.ai_service),
            'metadata': MetadataProcessorAI(self.database_service, self.ai_service, self.config_service),
            'storage': StorageProcessor(self.database_service, self.storage_service),
            'embedding': EmbeddingProcessor(self.database_service, self.ai_service),
            'search': SearchProcessor(self.database_service, self.ai_service)
        }
        self.logger.info("All services initialized!")
    
    async def get_documents_status(self) -> Dict[str, Any]:
        """Get comprehensive documents status"""
        self.logger.info("Checking documents status")
        
        try:
            # Use direct database service
            all_docs = self.database_service.client.table('vw_documents').select('processing_status').execute()
            
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
                
        except Exception:
            self.logger.error("Error getting documents status", exc_info=True)
            return {'total_documents': 0, 'completed': 0, 'pending': 0, 'failed': 0, 'processing': 0}
    
    async def get_documents_needing_processing(self) -> List[Dict[str, Any]]:
        """Get documents that need further processing (all pending documents)"""
        self.logger.info("Finding documents that need remaining stages")
        
        try:
            # Get ALL pending AND failed documents directly (no chunk check)
            pending_docs = []
            all_docs = self.database_service.client.table('vw_documents').select('*').in_('processing_status', ['pending', 'failed']).execute()
            
            for doc in all_docs.data:
                # Add ALL pending documents (chunks already exist)
                # Use original filename to construct file path
                filename = doc['filename']
                # Use absolute path to avoid "file not found" errors
                import os
                file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "service_documents", filename))
                
                pending_docs.append({
                    'id': doc['id'],
                    'filename': filename,
                    'file_path': file_path,
                    'processing_status': doc['processing_status'],
                    'chunk_count': 0,  # We don't check chunks anymore
                    'created_at': doc['created_at']
                })
            
            self.logger.info(
                "Found %s documents (pending + failed) that need further processing",
                len(pending_docs)
            )
            return pending_docs
            
        except Exception:
            self.logger.error("Error getting documents needing processing", exc_info=True)
            return []
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents with resolved file paths"""
        try:
            all_docs = self.database_service.client.table('vw_documents').select('*').execute()
            
            # Resolve file paths using file locator
            for doc in all_docs.data:
                filename = doc.get('filename')
                if filename:
                    # Try to find the actual file
                    actual_path = self.file_locator.find_file(filename)
                    doc['resolved_path'] = actual_path
                    doc['file_exists'] = actual_path is not None
                else:
                    doc['resolved_path'] = None
                    doc['file_exists'] = False
            
            return all_docs.data or []
        except Exception:
            self.logger.error("Error getting all documents", exc_info=True)
            return []
    
    async def get_document_stage_status(self, document_id: str) -> Dict[str, bool]:
        """Check which stages have been completed for a document"""
        stage_status = {
            'upload': False,
            'text': False,
            'image': False,
            'classification': False,
            'chunk_prep': False,
            'links': False,
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
                # DocumentModel has 'manufacturer' not 'manufacturer_id'
                if doc_info.manufacturer and doc_info.document_type != 'unknown':
                    stage_status['classification'] = True
            
            # Use direct PostgreSQL connection for cross-schema queries (via database_service)
            # This bypasses Supabase PostgREST limitations
            
            # Check if chunks exist (text stage) - krai_intelligence.chunks
            chunks_count = await self.database_service.count_chunks_by_document(document_id)
            if chunks_count > 0:
                stage_status['text'] = True
            
            # Check if images exist (image stage) - krai_content.images
            images_count = await self.database_service.count_images_by_document(document_id)
            if images_count > 0:
                stage_status['image'] = True
            
            # Check if intelligence chunks exist (chunk_prep stage) - krai_intelligence.chunks
            intelligence_chunks = await self.database_service.get_intelligence_chunks_by_document(document_id)
            if len(intelligence_chunks) > 0:
                stage_status['chunk_prep'] = True
            
            # Check if links exist (links stage) - krai_content.links
            links_count = await self.database_service.count_links_by_document(document_id)
            if links_count > 0:
                stage_status['links'] = True
            
            # Check if error codes exist (metadata stage) - krai_intelligence.error_codes
            if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                try:
                    async with self.database_service.pg_pool.acquire() as conn:
                        error_codes_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.error_codes WHERE document_id = $1",
                            document_id
                        )
                        if error_codes_count > 0:
                            stage_status['metadata'] = True
                except:
                    pass
            
            # Check if embeddings exist (embedding stage)
            if stage_status['text']:  # Only check if chunks exist
                embeddings_exist = await self.database_service.check_embeddings_exist(document_id)
                if embeddings_exist:
                    stage_status['embedding'] = True
            
            # For storage - assume done if image processing is confirmed
            if stage_status['image']:
                stage_status['storage'] = True
            
        except Exception:
            self.logger.error("Error checking stage status", exc_info=True)
        
        return stage_status
    
    async def process_document_smart_stages(self, document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
        """Process only the missing stages for a document using structured logging."""
        try:
            self.logger.info("Smart processing document '%s' (%s)", filename, document_id)

            stage_status = await self.get_document_stage_status(document_id)

            self.logger.info("  Current status:")
            for stage, completed in stage_status.items():
                status_icon = "✅" if completed else "❌"
                self.logger.info("    %s: %s", stage.capitalize(), status_icon)

            missing_stages = [stage for stage, completed in stage_status.items() if not completed]
            if not missing_stages:
                self.logger.info("  ✅ All stages already completed for '%s'", filename)
                return {
                    'success': True,
                    'filename': filename,
                    'stages_completed': len(stage_status),
                    'message': 'All stages already completed'
                }

            self.logger.info("  Missing stages: %s", ', '.join(missing_stages))

            context = ProcessingContext(
                file_path=file_path,
                document_id=document_id,
                file_hash="",
                document_type="",
                processing_config={'filename': filename},
                file_size=0
            )

            doc_info = await self.database_service.get_document(document_id)
            if doc_info:
                context.file_hash = doc_info.file_hash or ''
                context.document_type = doc_info.document_type or ''

            stage_sequence = [
                ("text", "[2/10] Text Processing:", 'text'),
                ("image", "[3/10] Image Processing:", 'image'),
                ("classification", "[4/10] Classification:", 'classification'),
                ("chunk_prep", "[5/10] Chunk Preprocessing:", 'chunk_prep'),
                ("links", "[6/10] Links:", 'links'),
                ("metadata", "[7/10] Metadata (Error Codes):", 'metadata'),
                ("storage", "[8/10] Storage:", 'storage'),
                ("embedding", "[9/10] Embeddings:", 'embedding'),
                ("search", "[10/10] Search:", 'search'),
            ]

            success_messages = {
                'text': lambda res: "Text processing completed",
                'image': lambda res: f"Image processing completed: {res.data.get('images_processed', 0)} images",
                'chunk_prep': lambda res: f"Chunk preprocessing completed: {res.data.get('chunks_preprocessed', 0)} chunks",
                'links': lambda res: (
                    "Link extraction completed: "
                    f"{res.data.get('links_extracted', 0)} links "
                    f"({res.data.get('video_links_created', 0)} videos)"
                ),
                'metadata': lambda res: "Metadata processing completed",
                'storage': lambda res: "Storage processing completed",
                'embedding': lambda res: f"Embedding processing completed: {res.data.get('embeddings_created', 0)} embeddings",
                'search': lambda res: "Search processing completed",
            }

            completed_stages: List[str] = []
            failed_stages: List[str] = []

            for stage_name, label, processor_key in stage_sequence:
                if stage_name not in missing_stages:
                    continue

                self.logger.info("  %s %s", label, filename)
                try:
                    result = await self.processors[processor_key].process(context)
                    if result.success:
                        completed_stages.append(stage_name)
                        formatter = success_messages.get(stage_name)
                        message = formatter(result) if formatter else f"{stage_name.capitalize()} completed"
                        self.logger.info("    ✅ %s", message)
                    else:
                        failed_stages.append(stage_name)
                        failure_message = result.message or "Unknown error"
                        self.logger.warning("    ❌ %s failed: %s", stage_name.capitalize(), failure_message)
                except Exception:
                    failed_stages.append(stage_name)
                    self.logger.error("    ❌ %s raised an exception", stage_name.capitalize(), exc_info=True)

            if not failed_stages:
                await self.database_service.update_document_status(document_id, 'completed')
                self.logger.success(f"  ✅ Document {filename} fully processed!")
            elif completed_stages:
                self.logger.warning(
                    "  Document %s partially processed (✅ %s stages, ❌ %s failed)",
                    filename,
                    len(completed_stages),
                    len(failed_stages)
                )
            else:
                await self.database_service.update_document_status(document_id, 'failed')
                self.logger.error("  Document %s completely failed (all stages failed)", filename)

            self.logger.info("  🔍 Running quality check...")
            quality_result = await self.quality_service.check_document_quality(document_id)

            score = quality_result.get('score', 0)
            issues = quality_result.get('issues') or []
            if score >= 80:
                self.logger.info("  ✅ Quality: %s/100", score)
            else:
                self.logger.warning("  ⚠️  Quality: %s/100", score)
                for issue in issues[:3]:
                    self.logger.warning("      %s", issue)

            return {
                'success': len(completed_stages) > 0,
                'filename': filename,
                'completed_stages': completed_stages,
                'failed_stages': failed_stages,
                'total_stages': len(completed_stages) + len(failed_stages),
                'quality_score': score,
                'quality_passed': quality_result.get('passed')
            }

        except Exception as error:
            self.logger.error("Error in smart processing", exc_info=True)
            return {
                'success': False,
                'filename': filename,
                'error': str(error)
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
            file_size_mb = file_size / 1024 / 1024
            
            self.logger.info("[%s/%s] Processing: %s (%.1fMB)", doc_index, total_docs, filename, file_size_mb)
            
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
            self.logger.info("  [%s] Upload: %s", doc_index, filename)
            result1 = await self.processors['upload'].process(context)
            
            # FORCE DEBUG OUTPUT - ALWAYS SHOW
            self.logger.debug("  [%s] FORCE DEBUG: result1.success = %s", doc_index, result1.success)
            self.logger.debug("  [%s] FORCE DEBUG: result1.data = %s", doc_index, result1.data)
            self.logger.debug(
                "  [%s] FORCE DEBUG: duplicate flag = %s",
                doc_index,
                result1.data.get('duplicate') if result1.data else 'NO DATA'
            )
            
            # Check if document already exists (deduplication)
            self.logger.debug(
                "  [%s] DEBUG: result1.success=%s, duplicate=%s",
                doc_index,
                result1.success,
                result1.data.get('duplicate')
            )
            self.logger.debug("  [%s] FORCE DEBUG: result1.data = %s", doc_index, result1.data)
            
            # FORCE SMART PROCESSING - Always use smart processing for existing documents
            if result1.success and (result1.data.get('duplicate') or result1.data.get('document_id')):
                # Document already exists - use Smart Processing for remaining stages
                self.logger.info("  [%s] Document exists - using Smart Processing for remaining stages", doc_index)
                document_id = result1.data.get('document_id')
                # Use absolute path
                import os
                file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "service_documents", filename))
                
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
            # Stage 2: Text Processor
            self.logger.info("  [%s] Text Processing: %s", doc_index, filename)
            result2 = await self.processors['text'].process(context)
            chunks_count = result2.data.get('chunks_created', 0)
            
            # Stage 3: Image Processor
            self.logger.info("  [%s] Image Processing: %s", doc_index, filename)
            result3 = await self.processors['image'].process(context)
            images_count = result3.data.get('images_processed', 0)
            
            # Stage 4: Classification Processor
            self.logger.info("  [%s] Classification: %s", doc_index, filename)
            result4 = await self.processors['classification'].process(context)
            
            # Stage 5: Chunk Preprocessing (NEW! - AI-ready chunks)
            self.logger.info("  [%s] Chunk Preprocessing: %s", doc_index, filename)
            result4b = await self.processors['chunk_prep'].process(context)
            chunks_preprocessed = result4b.data.get('chunks_preprocessed', 0) if result4b.success else 0
            self.logger.info("    → %s chunks preprocessed", chunks_preprocessed)
            
            # Stage 6: Link Extraction Processor
            self.logger.info("  [%s] Link Extraction: %s", doc_index, filename)
            result4c = await self.processors['links'].process(context)
            links_count = result4c.data.get('links_extracted', 0) if result4c.success else 0
            video_count = result4c.data.get('video_links_created', 0) if result4c.success else 0
            self.logger.info("    → %s links, %s videos", links_count, video_count)
            
            # Stage 7: Metadata Processor (Error Codes)
            self.logger.info("  [%s] Metadata (Error Codes): %s", doc_index, filename)
            result5 = await self.processors['metadata'].process(context)
            error_codes_count = result5.data.get('error_codes_found', 0) if result5.success else 0
            self.logger.info("    → %s error codes", error_codes_count)
            
            # Stage 8: Storage Processor
            self.logger.info("  [%s] Storage: %s", doc_index, filename)
            result6 = await self.processors['storage'].process(context)
            
            # Stage 9: Embedding Processor (Uses intelligence.chunks!)
            self.logger.info("  [%s] Embeddings: %s", doc_index, filename)
            result7 = await self.processors['embedding'].process(context)
            
            # Stage 10: Search Processor
            self.logger.info("  [%s] Search Index: %s", doc_index, filename)
            result8 = await self.processors['search'].process(context)
            
            self.logger.info("  [%s] Completed: %s", doc_index, filename)
            
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
        self.logger.info(
            "HARDWARE WAKER - Processing %s files with %s concurrent documents!",
            len(file_paths),
            self.max_concurrent
        )
        self.logger.info("This WILL wake up your CPU and GPU!")
        
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
            self.logger.info("Starting HARDWARE WAKER processing of %s files...", len(tasks))
            self.logger.info("Multiple documents will be processed simultaneously - CPU and GPU will be busy!")
            
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
            self.logger.error("Error in hardware waker processing: %s", e, exc_info=True)
        
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
        self.logger.info("💡 PowerShell Mode: Press 'd' for detailed view, 'q' to quit")
        self.logger.info("%s", "=" * 80)
        
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
                if self.interactive_console:
                    # Use carriage return only when interactive console is available
                    self._console_write(status_line, carriage_return=True)
                else:
                    self.logger.info(status_line)
                
                # Get current status values
                current_doc_count = pipeline_status['total_docs']
                current_classified_count = pipeline_status['classified_docs']
                current_chunk_count = pipeline_status['total_chunks']
                
                # Add newline only for detailed updates to prevent PowerShell line wrapping issues
                if (current_doc_count != last_doc_count or 
                    current_classified_count != last_classified_count or 
                    current_chunk_count != last_chunk_count or
                    show_detailed_view):
                    if self.interactive_console:
                        self._console_write("", newline=True)  # New line before detailed view
                    else:
                        self.logger.debug("Detailed view triggered for status update")
                
                # Check for keyboard input (Windows compatible)
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key == 'd':
                            show_detailed_view = True
                        elif key == 'q':
                            if self.interactive_console:
                                self._console_write("", newline=True)
                                self._console_write("🛑 Monitoring stopped by user", newline=True)
                            else:
                                self.logger.info("Monitoring stopped by user")
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
                self.logger.error("Monitor error: %s", e, exc_info=True)
    
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
            docs_result = self.database_service.client.table('vw_documents').select('*').execute()
            chunks_result = self.database_service.client.table('vw_chunks').select('*').execute()
            images_result = self.database_service.client.table('vw_images').select('*').execute()
            
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
            self.logger.error("Pipeline status error: %s", e, exc_info=True)
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
                docs_result = self.database_service.client.table('vw_documents').select('id').is_('manufacturer', 'null').execute()
                return len(docs_result.data) if docs_result.data else 0
            except:
                return 0
    
    def _console_write(self, message: str, *, newline: bool = False, carriage_return: bool = False):
        """Write directly to console when running interactively without using print"""
        if not self.interactive_console:
            return
        try:
            if carriage_return:
                sys.stdout.write("\r" + message)
            else:
                sys.stdout.write(message)
                if newline:
                    sys.stdout.write("\n")
            sys.stdout.flush()
        except Exception:
            # Disable further console writes if stdout is not available
            self.interactive_console = False
            self.logger.debug("Console write disabled due to error", exc_info=True)
    
    async def _print_detailed_pipeline_view(self, pipeline_status: Dict[str, Any], error_count: int):
        """Log detailed pipeline overview with progress bars for each stage"""
        self.logger.info("%s", "=" * 70)
        self.logger.info("📊 KR-AI PIPELINE OVERVIEW")
        self.logger.info("%s", "=" * 70)
        
        # Stage 1: Upload
        upload_progress = 100.0 if pipeline_status['total_docs'] > 0 else 0
        upload_bar = "█" * 15 + "░" * 0 if upload_progress == 100 else "░" * 15
        self.logger.info(
            "📤 Upload:        %s %5.1f%% (%s docs)",
            upload_bar,
            upload_progress,
            pipeline_status['total_docs']
        )
        
        # Stage 2: Text Processing
        text_progress = 0
        if pipeline_status['total_docs'] > 0:
            expected_chunks = pipeline_status['total_docs'] * 1000
            text_progress = min(100, (pipeline_status['total_chunks'] / expected_chunks) * 100)
        
        text_bar_length = int((text_progress / 100) * 15)
        text_bar = "█" * text_bar_length + "░" * (15 - text_bar_length)
        self.logger.info(
            "📄 Text:          %s %5.1f%% (%s chunks)",
            text_bar,
            text_progress,
            f"{pipeline_status['total_chunks']:,}"
        )
        
        # Stage 3: Image Processing
        image_progress = 0
        if pipeline_status['total_docs'] > 0:
            expected_images = pipeline_status['total_docs'] * 100
            image_progress = min(100, (pipeline_status['total_images'] / expected_images) * 100)
        
        image_bar_length = int((image_progress / 100) * 15)
        image_bar = "█" * image_bar_length + "░" * (15 - image_bar_length)
        self.logger.info(
            "🖼️  Images:        %s %5.1f%% (%s images)",
            image_bar,
            image_progress,
            f"{pipeline_status['total_images']:,}"
        )
        
        # Stage 4: Classification
        class_progress = 0
        if pipeline_status['total_docs'] > 0:
            class_progress = (pipeline_status['classified_docs'] / pipeline_status['total_docs']) * 100
        
        class_bar_length = int((class_progress / 100) * 15)
        class_bar = "█" * class_bar_length + "░" * (15 - class_bar_length)
        self.logger.info(
            "🏷️  Classification: %s %5.1f%% (%s/%s docs)",
            class_bar,
            class_progress,
            pipeline_status['classified_docs'],
            pipeline_status['total_docs']
        )
        
        # Overall Progress
        overall_bar_length = int((pipeline_status['overall_progress'] / 100) * 20)
        overall_bar = "█" * overall_bar_length + "░" * (20 - overall_bar_length)
        self.logger.info(
            "🎯 OVERALL:       %s %5.1f%%",
            overall_bar,
            pipeline_status['overall_progress']
        )
        
        # Error Status
        if error_count > 0:
            self.logger.warning(
                "❌ ERRORS: %s docs stuck | 💡 Run: python backend/tests/pipeline_recovery.py",
                error_count
            )
        
        # Current Activity
        if pipeline_status['current_stage']:
            self.logger.info("🔄 CURRENT: %s", pipeline_status['current_stage'])
        
        self.logger.info("%s", "=" * 70)
    
    def find_pdf_files(self, directory: str, limit: int = None) -> List[str]:
        """Find PDF files in directory with optional limit"""
        pdf_files = []
        
        # Check if directory exists
        if not os.path.exists(directory):
            self.logger.warning("⚠️  Directory not found: %s", directory)
            return []
        
        # Check if directory is empty
        try:
            files_in_dir = os.listdir(directory)
            if not files_in_dir:
                self.logger.warning("⚠️  Directory is empty: %s", directory)
                return []
        except Exception as e:
            self.logger.error("⚠️  Cannot read directory: %s", directory, exc_info=True)
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
        
        self.logger.info("📁 Found %s document files in %s", len(pdf_files), directory)
        for ext, count in extension_counts.items():
            self.logger.info("   %s: %s files", ext, count)
        
        return sorted(pdf_files)
    
    def find_service_documents_directory(self) -> str:
        """Find the service_documents directory with intelligent path detection"""
        possible_paths = [
            r"C:\service_documents",  # User's absolute path
            "service_documents",  # Same directory
            "../service_documents",  # Parent directory
            "../../service_documents",  # Two levels up
            "./service_documents",  # Explicit current directory
            os.path.join(os.getcwd(), "service_documents"),  # Absolute current + service_documents
            os.path.join(os.path.dirname(os.getcwd()), "service_documents"),  # Parent + service_documents
        ]
        
        self.logger.info("🔍 Searching for service_documents directory...")
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # Check if it contains PDF files
                try:
                    files = os.listdir(path)
                    # Count all supported document types
                    supported_extensions = ['.pdf', '.pdfz', '.docx', '.doc', '.txt', '.rtf']
                    doc_count = sum(1 for f in files if os.path.splitext(f)[1].lower() in supported_extensions)
                    
                    if doc_count > 0:
                        self.logger.info(
                            "✅ Found service_documents with %s document files: %s",
                            doc_count,
                            os.path.abspath(path)
                        )
                        return path
                    else:
                        self.logger.info("📁 Found directory but no supported documents: %s", os.path.abspath(path))
                except Exception as e:
                    self.logger.error("⚠️  Cannot read directory %s", path, exc_info=True)
            else:
                self.logger.debug("❌ Not found: %s", path)
        
        self.logger.warning("⚠️  No service_documents directory with PDFs found!")
        self.logger.info("💡 Please create a 'service_documents' directory and add PDF files")
        return None
    
    def print_status_summary(self, results: Dict[str, Any]):
        """Print status summary"""
        self.logger.info("%s", "=" * 80)
        self.logger.info("KR MASTER PIPELINE SUMMARY")
        self.logger.info("%s", "=" * 80)
        self.logger.info("Total Files: %s", results['total_files'])
        self.logger.info("Successful: %s", len(results['successful']))
        self.logger.info("Failed: %s", len(results['failed']))
        self.logger.info("Success Rate: %.1f%%", results['success_rate'])
        if 'duration' in results:
            self.logger.info(
                "Total Duration: %.1fs (%.1fm)",
                results['duration'],
                results['duration'] / 60
            )
            self.logger.info(
                "Average per File: %.1fs",
                results['duration'] / results['total_files']
            )
        self.logger.info("%s", "=" * 80)

async def main():
    """Main function with menu system"""
    pipeline = KRMasterPipeline()
    await pipeline.initialize_services()
    logger = pipeline.logger

    logger.info("KR-AI-ENGINE MASTER PIPELINE")
    logger.info("%s", "=" * 50)
    logger.info("Ein einziges Script für alle Pipeline-Funktionen!")
    logger.info("%s", "=" * 50)
    
    while True:
        logger.info("")
        logger.info("MASTER PIPELINE MENU:")
        logger.info("1. Status Check - Zeige aktuelle Dokument-Status")
        logger.info("2. Smart Processing - Nur fehlende Stages verarbeiten")
        logger.info("3. Hardware Waker - Verarbeite neue Dokumente (CPU/GPU)")
        logger.info("4. Einzelnes Dokument verarbeiten")
        logger.info("5. Batch Processing - Alle Dokumente verarbeiten")
        logger.info("6. Debug - Zeige Pfad-Informationen")
        logger.info("8. Quality Check - Prüfe Verarbeitungsqualität NEW")
        logger.info("9. Force Smart Processing - Alle Dokumente (mit Quality Check) NEW")
        logger.info("7. Exit")
        
        choice = input("\nWähle Option (1-9): ").strip()
        
        if choice == "1":
            # Status Check
            logger.info("=== STATUS CHECK ===")
            status = await pipeline.get_documents_status()
            logger.info("Total Documents: %s", status['total_documents'])
            logger.info("Completed: %s", status['completed'])
            logger.info("Pending: %s", status['pending'])
            logger.info("Failed: %s", status['failed'])
            logger.info("Processing: %s", status['processing'])
            
        elif choice == "2":
            # Smart Processing - Only Missing Stages
            logger.info("=== SMART PROCESSING - MISSING STAGES ONLY ===")
            documents = await pipeline.get_documents_needing_processing()
            
            if not documents:
                logger.warning("Keine Dokumente gefunden die weitere Verarbeitung brauchen!")
                continue
            
            logger.info("Gefunden: %s Dokumente - prüfe welche Stages fehlen...", len(documents))
            
            # Show first few documents with their stage status
            logger.info("Erste 5 Dokumente mit Stage-Status:")
            for i, doc in enumerate(documents[:5]):
                stage_status = await pipeline.get_document_stage_status(doc['id'])
                missing_stages = [stage for stage, completed in stage_status.items() if not completed]
                status_text = f"Missing: {', '.join(missing_stages)}" if missing_stages else "All complete"
                logger.info("  %s. %s - %s", i + 1, doc['filename'], status_text)
            
            if len(documents) > 5:
                logger.info("  ... und %s weitere", len(documents) - 5)
            
            response = input(f"\nSmart Process {len(documents)} Dokumente (nur fehlende Stages)? (y/n): ").lower().strip()
            if response != 'y':
                logger.info("Smart Processing abgebrochen.")
                continue
            
            # Process documents with smart processing
            results = {'successful': [], 'failed': [], 'total_files': len(documents)}
            
            for i, doc in enumerate(documents):
                logger.info("[%s/%s] Smart Processing: %s", i + 1, len(documents), doc['filename'])
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
            logger.info("=== HARDWARE WAKER ===")
            
            # Find service_documents directory intelligently
            pdf_directory = pipeline.find_service_documents_directory()
            if not pdf_directory:
                logger.error(" Cannot find service_documents directory with PDFs!")
                logger.info(" Please create a 'service_documents' directory and add PDF files")
                continue
            
            logger.info("Options:")
            logger.info("1. Test mit 3 Dokumenten (schneller Test)")
            logger.info("2. Test mit 5 Dokumenten (mittlerer Test)")
            logger.info("3. Verarbeite alle Dokumente (vollständig)")
            
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
                logger.warning("Keine Dokumente in %s gefunden!", pdf_directory)
                continue
            
            logger.info("Ausgewählt: %s Dokumente für Hardware Waker", len(pdf_files))
            logger.info("Verarbeite %s Dokumente gleichzeitig!", pipeline.max_concurrent)
            logger.info("Das SOLLTE deine Hardware aufwecken!")
            
            response = input(f"\nWAKE UP HARDWARE und verarbeite {len(pdf_files)} Dokumente? (y/n): ").lower().strip()
            if response != 'y':
                logger.info("Hardware Waker abgebrochen.")
                continue
            
            # Process batch
            results = await pipeline.process_batch_hardware_waker(pdf_files)
            pipeline.print_status_summary(results)
            
            # FORCE Smart Processing for all documents (regardless of upload results)
            logger.info("=== FORCED SMART PROCESSING - ALL DOCUMENTS ===")
            all_docs = pipeline.database_service.client.table('vw_documents').select('*').execute()
            
            if all_docs.data:
                logger.info("Found %s total documents - forcing smart processing...", len(all_docs.data))
                stage_results = {'successful': [], 'failed': [], 'total_files': len(all_docs.data)}
                
                for i, doc in enumerate(all_docs.data):
                    logger.info("[%s/%s] Forced Smart processing: %s", i + 1, len(all_docs.data), doc['filename'])
                    # Use absolute path
                    import os
                    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "service_documents", doc['filename']))
                    
                    result = await pipeline.process_document_smart_stages(
                        doc['id'], doc['filename'], file_path
                    )
                    
                    if result['success']:
                        stage_results['successful'].append(result)
                    else:
                        stage_results['failed'].append(result)
                
                stage_results['success_rate'] = len(stage_results['successful']) / len(all_docs.data) * 100
                logger.info("=== FORCED SMART PROCESSING SUMMARY ===")
                pipeline.print_status_summary(stage_results)
            else:
                logger.warning("No documents found in database!")
            
        elif choice == "4":
            # Single Document Processing
            logger.info("=== EINZELNES DOKUMENT ===")
            document_id = input("Document ID eingeben: ").strip()
            
            if not document_id:
                logger.info("Keine Document ID eingegeben.")
                continue
            
            # Get document info
            doc_info = await pipeline.database_service.get_document(document_id)
            if not doc_info:
                logger.error("Document %s nicht gefunden!", document_id)
                continue
            
            filename = doc_info.filename if doc_info.filename else 'Unknown'
            file_path = doc_info.storage_path if doc_info.storage_path else ''
            
            logger.info("Gefunden: %s", filename)
            logger.info("File path: %s", file_path)
            
            response = input(f"\nVerarbeite verbleibende Stages für {filename}? (y/n): ").lower().strip()
            if response != 'y':
                logger.info("Verarbeitung abgebrochen.")
                continue
            
            result = await pipeline.process_document_remaining_stages(document_id, filename, file_path)
            
            if result['success']:
                logger.info("[SUCCESS] Erfolgreich verarbeitet: %s!", result['filename'])
                logger.info("Images processed: %s", result['images'])
            else:
                logger.error("[FAILED] Fehler bei %s: %s", result['filename'], result['error'])
                
        elif choice == "5":
            # Batch Processing
            logger.info("=== BATCH PROCESSING ===")
            
            # Find service_documents directory intelligently
            pdf_directory = pipeline.find_service_documents_directory()
            if not pdf_directory:
                logger.error(" Cannot find service_documents directory with PDFs!")
                logger.info(" Please create a 'service_documents' directory and add PDF files")
                continue
            
            pdf_files = pipeline.find_pdf_files(pdf_directory)
            
            if not pdf_files:
                logger.warning("Keine Dokumente in %s gefunden!", pdf_directory)
                continue
            
            logger.info("Gefunden: %s Dokumente", len(pdf_files))
            response = input(f"\nVerarbeite ALLE {len(pdf_files)} Dokumente? (y/n): ").lower().strip()
            if response != 'y':
                logger.info("Batch Processing abgebrochen.")
                continue
            
            results = await pipeline.process_batch_hardware_waker(pdf_files)
            pipeline.print_status_summary(results)
            
        elif choice == "6":
            # Debug
            import os
            logger.info("=== DEBUG INFORMATIONEN ===")
            logger.info("Current Working Directory: %s", os.getcwd())
            logger.info("Script Location: %s", os.path.abspath(__file__))
            logger.info("Script Directory: %s", os.path.dirname(os.path.abspath(__file__)))
            
            # Show file locator information
            pipeline.file_locator.print_debug_info()
            
            logger.info(" Searching for service_documents...")
            pdf_directory = pipeline.find_service_documents_directory()
            
            if pdf_directory:
                logger.info(" Service Documents Directory: %s", os.path.abspath(pdf_directory))
                pdf_files = pipeline.find_pdf_files(pdf_directory)
                logger.info(" Document Files found: %s", len(pdf_files))
                if pdf_files:
                    logger.info("First 5 document files:")
                    for i, pdf in enumerate(pdf_files[:5]):
                        logger.info("  %s. %s", i + 1, os.path.basename(pdf))
            else:
                logger.warning(" No service_documents directory found!")
                logger.info(" Create a 'service_documents' directory and add PDF files")
            
            # Test finding a specific file
            logger.info(" Test File Locator:")
            test_filename = input("Enter a filename to search for (or press Enter to skip): ").strip()
            if test_filename:
                found_path = pipeline.file_locator.find_file(test_filename)
                if found_path:
                    logger.info("  Found: %s", found_path)
                else:
                    logger.warning("  Not found: %s", test_filename)
            
        elif choice == "8":
            # Quality Check
            logger.info("=== QUALITY CHECK ===")
            logger.info("1. Check single document")
            logger.info("2. Check pipeline health")
            logger.info("3. Check all documents")
            
            qc_choice = input("\nWähle (1-3): ").strip()
            
            if qc_choice == "1":
                doc_id = input("Document ID (or 'first' for first document): ").strip()
                if doc_id == 'first':
                    docs = await pipeline.get_all_documents()
                    if docs:
                        doc_id = docs[0]['id']
                        logger.info("Using: %s", docs[0]['filename'])

                quality_result = await pipeline.quality_service.check_document_quality(doc_id)
                pipeline.quality_service.print_quality_report(doc_id, quality_result)
            
            elif qc_choice == "2":
                health = await pipeline.quality_service.check_pipeline_health()
                logger.info("Pipeline Status: %s", health['status'].upper())
                logger.info("Documents: %s", health['checks'].get('documents_count', 0))
                logger.info("Content Chunks: %s", health['checks'].get('content_chunks_count', 0))
                logger.info("Intelligence Chunks: %s", health['checks'].get('intelligence_chunks_count', 0))
                
                if health['issues']:
                    logger.error(" Issues:")
                    for issue in health['issues']:
                        logger.error("  %s", issue)
                
                if health['warnings']:
                    logger.warning("  Warnings:")
                    for warning in health['warnings']:
                        logger.warning("  %s", warning)
            
            elif qc_choice == "3":
                logger.info("Checking all documents...")
                docs = await pipeline.get_all_documents()
                total_score = 0
                passed_count = 0
                
                for i, doc in enumerate(docs[:10]):  # First 10 for demo
                    quality_result = await pipeline.quality_service.check_document_quality(doc['id'])
                    total_score += quality_result['score']
                    if quality_result['passed']:
                        passed_count += 1
                    
                    status_icon = " " if quality_result['passed'] else " "
                    logger.info("%s. %s %s Score: %s/100", i + 1, status_icon, doc['filename'][:40].ljust(40), quality_result['score'])
                
                avg_score = total_score / min(len(docs), 10)
                logger.info("Average Quality Score: %.1f/100", avg_score)
                logger.info("Passed: %s/%s", passed_count, min(len(docs), 10))
        
        elif choice == "9":
            # Force Smart Processing with Quality Check
            logger.info("=== FORCE SMART PROCESSING (with Quality Check) ===")
            
            docs = await pipeline.get_all_documents()
            logger.info("Found %s documents", len(docs))
            
            response = input(f"\nProcess ALL {len(docs)} documents with quality checks? (y/n): ").strip().lower()
            if response != 'y':
                logger.info("Abgebrochen.")
                continue
            
            quality_scores = []
            passed_count = 0
            
            import os  # Explicit import for this scope
            
            for i, doc in enumerate(docs):
                logger.info("[%s/%s] %s", i + 1, len(docs), doc['filename'])
                
                # Use resolved path from file locator
                file_path = doc.get('resolved_path')
                if not file_path:
                    logger.warning("  File not found, processing with database data only")
                    file_path = ""  # Empty path - processors will handle it
                
                result = await pipeline.process_document_smart_stages(doc['id'], doc['filename'], file_path)
                
                if result.get('quality_passed'):
                    passed_count += 1
                    quality_scores.append(result.get('quality_score', 0))
            
            # Summary
            logger.info("%s", "=" * 60)
            logger.info(" QUALITY SUMMARY")
            logger.info("%s", "=" * 60)
            logger.info("Documents Processed: %s", len(docs))
            logger.info("Quality Passed: %s/%s (%.1f%%)", passed_count, len(docs), (passed_count / len(docs) * 100) if docs else 0)
            if quality_scores:
                logger.info("Average Score: %.1f/100", sum(quality_scores) / len(quality_scores))
            logger.info("%s", "=" * 60)
        
        elif choice == "7":
            logger.info("Exiting...")
            logger.info("Auf Wiedersehen! KR-AI-Engine Master Pipeline beendet.")
            break
            
        else:
            logger.warning("Ungültige Option. Bitte 1-9 wählen.")

if __name__ == "__main__":
    asyncio.run(main())
