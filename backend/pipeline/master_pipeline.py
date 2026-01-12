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
from typing import List, Dict, Any, Optional, Callable, Awaitable
import logging
import multiprocessing as mp
import psutil

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files

# Import services
from backend.services.database_service import DatabaseService
from backend.services.object_storage_service import ObjectStorageService
from backend.services.storage_factory import create_storage_service
from backend.services.ai_service import AIService
from backend.services.config_service import ConfigService
from backend.services.features_service import FeaturesService
from backend.services.quality_check_service import QualityCheckService
from backend.services.file_locator_service import FileLocatorService
from backend.services.manufacturer_verification_service import ManufacturerVerificationService
from backend.services.web_scraping_service import create_web_scraping_service
from backend.utils.colored_logging import apply_colored_logging_globally

from backend.processors.upload_processor import UploadProcessor
from backend.processors.text_processor_optimized import OptimizedTextProcessor
from backend.processors.svg_processor import SVGProcessor
from backend.processors.image_processor import ImageProcessor
from backend.processors.classification_processor import ClassificationProcessor
from backend.processors.chunk_preprocessor import ChunkPreprocessor
from backend.processors.metadata_processor_ai import MetadataProcessorAI
from backend.processors.link_extraction_processor_ai import LinkExtractionProcessorAI
from backend.processors.storage_processor import StorageProcessor
from backend.processors.embedding_processor import EmbeddingProcessor
from backend.processors.search_processor import SearchProcessor
from backend.processors.visual_embedding_processor import VisualEmbeddingProcessor
from backend.processors.table_processor import TableProcessor
from backend.processors.thumbnail_processor import ThumbnailProcessor

from backend.core.base_processor import ProcessingContext

class KRMasterPipeline:
    """
    Master Pipeline für alle KR-AI-Engine Funktionen
    """
    
    def __init__(self, database_adapter=None, force_continue_on_errors=True):
        self.database_adapter = database_adapter
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
            f"Performance settings: concurrent_documents={self.max_concurrent}, cpu_cores={cpu_count}"
        )
        self.logger.info(
            f"KR Master Pipeline initialized with {self.max_concurrent} concurrent document capacity"
        )
        
    async def initialize_services(self):
        """Initialize all services"""
        self.logger.info("Initializing KR Master Pipeline services")
        
        project_root = Path(__file__).resolve().parents[2]
        # Extra files primarily for legacy env.* layouts; .env and .env.database are already
        # handled by load_all_env_files. We deliberately do NOT load .env.test here so the
        # master pipeline uses the primary PostgreSQL configuration from .env/.env.database.
        extra_env_files = ['env.database', 'env.storage', 'env.ai', 'env.system']

        loaded_files = load_all_env_files(project_root, extra_files=extra_env_files)

        if loaded_files:
            resolved_paths = [str(project_root / env_file) for env_file in loaded_files]
            self.logger.info(
                "Environment loaded: %s files - %s",
                len(loaded_files),
                '; '.join(resolved_paths)
            )
        else:
            self.logger.warning("No .env files found in project root: %s", project_root)
            self.logger.info("Attempted to load files: %s", ', '.join(extra_env_files + ['.env', '.env.local']))

            postgres_url = (
                os.getenv('POSTGRES_URL')
                or os.getenv('DATABASE_CONNECTION_URL')
                or os.getenv('DATABASE_URL')
            )

            if postgres_url:
                self.logger.info(
                    "Proceeding without env files because database URL is present in environment"
                )
                await self._initialize_services_after_env_loaded()
                return

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
        # Get PostgreSQL URL for direct connection (alternative method)
        # Prefer explicit POSTGRES_URL or DATABASE_CONNECTION_URL; fall back to DATABASE_URL
        postgres_url = (
            os.getenv('POSTGRES_URL')
            or os.getenv('DATABASE_CONNECTION_URL')
            or os.getenv('DATABASE_URL')
        )
        if postgres_url:
            self.logger.info("✅ POSTGRES_URL: %s... (asyncpg fallback enabled)", postgres_url[:40])
        else:
            self.logger.warning("POSTGRES_URL not found - using PostgREST only")
        
        # Initialize database service with PostgreSQL adapter
        self.database_service = DatabaseService(
            postgres_url=postgres_url,
            database_type='postgresql'  # Explicitly use PostgreSQL
        )
        await self.database_service.connect()
        
        # Initialize object storage service
        self.storage_service = create_storage_service()
        # Storage service factory supports MinIO, S3, R2, etc.
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
        
        # Initialize web scraping service for product discovery
        web_scraping_service = create_web_scraping_service()
        
        # Initialize manufacturer verification service for product discovery
        self.manufacturer_verification_service = ManufacturerVerificationService(
            database_service=self.database_service,
            web_scraping_service=web_scraping_service
        )
        
        # Initialize all processors - use sequential variables to avoid initialization ordering issues
        embedding_processor = EmbeddingProcessor(self.database_service, self.ai_service.ollama_url)
        table_processor = TableProcessor(self.database_service, embedding_processor)
        
        self.processors = {
            'upload': UploadProcessor(self.database_service),
            'text': OptimizedTextProcessor(self.database_service, self.config_service),
            'svg': SVGProcessor(self.database_service, self.storage_service, self.ai_service) if os.getenv('ENABLE_SVG_EXTRACTION', 'false').lower() == 'true' else None,
            'embedding': embedding_processor,
            'table': table_processor,
            'image': ImageProcessor(self.database_service, self.storage_service, self.ai_service),
            'visual_embedding': VisualEmbeddingProcessor(self.database_service),
            'classification': ClassificationProcessor(
                self.database_service, 
                self.ai_service, 
                self.features_service,
                manufacturer_verification_service=self.manufacturer_verification_service
            ),
            'chunk_prep': ChunkPreprocessor(self.database_service),
            'links': LinkExtractionProcessorAI(self.database_service, self.ai_service),
            'metadata': MetadataProcessorAI(self.database_service, self.ai_service, self.config_service),
            'storage': StorageProcessor(self.database_service, self.storage_service),
            'search': SearchProcessor(self.database_service, self.ai_service),
            'thumbnail': ThumbnailProcessor(self.database_service, self.storage_service)
        }
        self.logger.info("All services initialized!")

    async def _get_document_row_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Lookup document row by filename (used only to resume processing for local files)."""
        try:
            rows = await self.database_service.execute_query(
                "SELECT id, filename, processing_status, stage_status FROM krai_core.documents WHERE filename = $1 LIMIT 1",
                [filename],
            )
            return rows[0] if rows else None
        except Exception:
            self.logger.error("Error looking up document by filename", exc_info=True)
            return None
    
    async def get_documents_status(self) -> Dict[str, Any]:
        """Get comprehensive documents status"""
        self.logger.info("Checking documents status")
        
        try:
            rows = await self.database_service.execute_query(
                "SELECT processing_status FROM krai_core.documents"
            )

            status = {
                'total_documents': len(rows),
                'completed': 0,
                'pending': 0,
                'failed': 0,
                'processing': 0
            }

            for doc in rows:
                status_value = doc.get('processing_status')
                if status_value in status:
                    status[status_value] += 1
            
            return status
                
        except Exception:
            self.logger.error("Error getting documents status", exc_info=True)
            return {'total_documents': 0, 'completed': 0, 'pending': 0, 'failed': 0, 'processing': 0}
    
    async def get_documents_needing_processing(self) -> List[Dict[str, Any]]:
        """Get documents that need further processing (all pending documents)"""
        self.logger.info("Finding local documents that need remaining stages")
        
        try:
            pending_docs = []

            pdf_directory = self.find_service_documents_directory()
            if not pdf_directory:
                self.logger.warning("No service_documents directory found")
                return []

            pdf_files = self.find_pdf_files(pdf_directory)
            for file_path in pdf_files:
                filename = os.path.basename(file_path)
                doc_row = await self._get_document_row_by_filename(filename)
                status = (doc_row or {}).get('processing_status')
                if status in ('pending', 'failed') or doc_row is None:
                    pending_docs.append({
                        'id': (doc_row or {}).get('id'),
                        'filename': filename,
                        'file_path': file_path,
                        'processing_status': status or 'local_only',
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
            pdf_directory = self.find_service_documents_directory()
            if not pdf_directory:
                return []

            pdf_files = self.find_pdf_files(pdf_directory)
            results: List[Dict[str, Any]] = []
            for file_path in pdf_files:
                filename = os.path.basename(file_path)
                doc_row = await self._get_document_row_by_filename(filename)
                results.append({
                    'id': (doc_row or {}).get('id'),
                    'filename': filename,
                    'resolved_path': file_path,
                    'file_exists': True,
                    'processing_status': (doc_row or {}).get('processing_status') or 'local_only',
                })

            return results
        except Exception:
            self.logger.error("Error getting all documents", exc_info=True)
            return []
    
    async def get_document_stage_status(self, document_id: str) -> Dict[str, bool]:
        """Check which stages have been completed for a document - all 15 canonical stages"""
        stage_status = {
            'upload': False,
            'text_extraction': False,
            'table_extraction': False,
            'svg_processing': False,
            'image_processing': False,
            'visual_embedding': False,
            'link_extraction': False,
            'chunk_preprocessing': False,
            'classification': False,
            'metadata_extraction': False,
            'parts_extraction': False,
            'series_detection': False,
            'storage': False,
            'embedding': False,
            'search_indexing': False
        }
        
        try:
            # Check if document exists (upload stage)
            doc_info = await self.database_service.get_document(document_id)
            if doc_info:
                stage_status['upload'] = True
                
                # Check if document is classified (classification stage)
                if doc_info.manufacturer and doc_info.document_type != 'unknown':
                    stage_status['classification'] = True
            
            # Use direct PostgreSQL connection for cross-schema queries
            if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                try:
                    async with self.database_service.pg_pool.acquire() as conn:
                        # Check text extraction - krai_intelligence.chunks
                        chunks_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.chunks WHERE document_id = $1",
                            document_id
                        )
                        if chunks_count > 0:
                            stage_status['text_extraction'] = True
                            stage_status['chunk_preprocessing'] = True  # Chunks imply preprocessing done
                        
                        # Check table extraction - krai_intelligence.structured_tables
                        tables_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.structured_tables WHERE document_id = $1",
                            document_id
                        )
                        if tables_count > 0:
                            stage_status['table_extraction'] = True
                        
                        # Check SVG processing - krai_content.images with image_type='vector_graphic'
                        svg_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1 AND image_type = 'vector_graphic'",
                            document_id
                        )
                        if svg_count > 0:
                            stage_status['svg_processing'] = True
                        
                        # Check image processing - krai_content.images
                        images_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1",
                            document_id
                        )
                        if images_count > 0:
                            stage_status['image_processing'] = True
                            stage_status['storage'] = True  # Images stored implies storage done
                        
                        # Check visual embeddings - krai_intelligence.embeddings_v2 with embedding_type='image'
                        visual_embeddings_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.embeddings_v2 WHERE document_id = $1 AND embedding_type = 'image'",
                            document_id
                        )
                        if visual_embeddings_count > 0:
                            stage_status['visual_embedding'] = True
                        
                        # Check link extraction - krai_content.links
                        links_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.links WHERE document_id = $1",
                            document_id
                        )
                        if links_count > 0:
                            stage_status['link_extraction'] = True
                        
                        # Check metadata extraction - krai_intelligence.error_codes
                        error_codes_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.error_codes WHERE document_id = $1",
                            document_id
                        )
                        if error_codes_count > 0:
                            stage_status['metadata_extraction'] = True
                        
                        # Check parts extraction - krai_intelligence.parts
                        parts_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.parts WHERE document_id = $1",
                            document_id
                        )
                        if parts_count > 0:
                            stage_status['parts_extraction'] = True
                        
                        # Check series detection - krai_core.product_series linked to document
                        series_count = await conn.fetchval(
                            """
                            SELECT COUNT(DISTINCT ps.id)
                            FROM krai_core.product_series ps
                            JOIN krai_core.documents d ON d.series = ps.series_name
                            WHERE d.id = $1 AND ps.series_name IS NOT NULL
                            """,
                            document_id
                        )
                        if series_count > 0:
                            stage_status['series_detection'] = True
                        
                        # Check embeddings - krai_intelligence.chunks with embedding IS NOT NULL
                        embeddings_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.chunks WHERE document_id = $1 AND embedding IS NOT NULL",
                            document_id
                        )
                        if embeddings_count > 0:
                            stage_status['embedding'] = True
                            stage_status['search_indexing'] = True  # Embeddings imply search indexing done
                        
                except Exception as e:
                    self.logger.error(f"Error checking stage status via pg_pool: {e}", exc_info=True)
            
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

            # Ensure file_path exists before processing stages
            if not Path(file_path).exists():
                self.logger.warning(f"File not found: {file_path} - skipping all stages for document {filename}")
                return {
                    'success': False,
                    'message': f'File not found: {file_path}',
                    'completed_stages': [],
                    # Treat all missing stages as failed for reporting
                    'failed_stages': missing_stages,
                    'filename': filename
                }

            doc_info = await self.database_service.get_document(document_id)
            if doc_info:
                context.file_hash = doc_info.file_hash or ''
                context.document_type = doc_info.document_type or ''

            stage_sequence = [
                ("text", "[2/10] Text Processing:", 'text'),
                ("svg", "[3a/10] SVG Processing:", 'svg'),
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
                'svg': lambda res: f"SVG processing completed: {res.data.get('svgs_extracted', 0)} SVGs, {res.data.get('images_queued', 0)} images queued",
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

                # SVG stage gating with feature flag
                if stage_name == 'svg':
                    if os.getenv('ENABLE_SVG_EXTRACTION', 'false').lower() != 'true':
                        self.logger.info("  %s %s (SKIPPED: SVG extraction disabled)", label, filename)
                        continue
                    if self.processors.get('svg') is None:
                        self.logger.info("  %s %s (SKIPPED: SVG processor not available)", label, filename)
                        continue

                self.logger.info("  %s %s", label, filename)
                try:
                    result = await self.processors[processor_key].process(context)
                    # Handle both dict and ProcessingResult objects
                    if isinstance(result, dict):
                        success = result.get('success', False)
                        message = result.get('message', 'Unknown error')
                    else:
                        success = result.success
                        message = result.message
                    
                    if success:
                        completed_stages.append(stage_name)
                        formatter = success_messages.get(stage_name)
                        formatted_message = formatter(result) if formatter else f"{stage_name.capitalize()} completed"
                        self.logger.info("    ✅ %s", formatted_message)
                    else:
                        failed_stages.append(stage_name)
                        failure_message = message or "Unknown error"
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
            current_stage = "init"
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
            current_stage = "upload"
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
            if result1.success and result1.data.get('duplicate') and result1.data.get('document_id'):
                # Document already exists - use Smart Processing for remaining stages
                self.logger.info("  [%s] Document exists - using Smart Processing for remaining stages", doc_index)
                document_id = result1.data.get('document_id')
                # Use provided path when available, fallback to service_documents for CLI runs
                if not os.path.exists(file_path):
                    file_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "..", "service_documents", filename)
                    )
                
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
                        'message': 'Smart processing completed',
                        'quality_score': smart_result.get('quality_score'),
                        'quality_passed': smart_result.get('quality_passed'),
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
            current_stage = "text"
            self.logger.info("  [%s] Text Processing: %s", doc_index, filename)
            result2 = await self.processors['text'].process(context)
            chunks_count = result2.data.get('chunks_created', 0)
            
            # Stage 2b: Table Processor (NEW! - Multi-modal support)
            current_stage = "table"
            self.logger.info("  [%s] Table Extraction: %s", doc_index, filename)
            try:
                result2b = await self.processors['table'].process(context)
                tables_count = result2b.data.get('tables_extracted', 0) if result2b.success else 0
            except Exception as e:
                if os.getenv('DEBUG_NONFATAL_TABLE_EXTRACTION', 'false').lower() == 'true':
                    self.logger.warning(
                        "  [%s] Table Extraction failed but continuing (DEBUG_NONFATAL_TABLE_EXTRACTION=true): %s",
                        doc_index,
                        e,
                        exc_info=True,
                    )
                    tables_count = 0
                else:
                    raise
            
            # Stage 3a: SVG Processor (NEW! - Vector graphics extraction)
            if self.processors['svg'] is not None:
                current_stage = "svg"
                self.logger.info("  [%s] SVG Processing: %s", doc_index, filename)
                result3a = await self.processors['svg'].process(context)
                svg_count = result3a.data.get('svgs_extracted', 0) if result3a.success else 0
                svg_converted = result3a.data.get('svgs_converted', 0) if result3a.success else 0
                self.logger.info("    → %s SVGs extracted, %s converted", svg_count, svg_converted)
            else:
                svg_count = 0
                svg_converted = 0
            
            # Stage 3: Image Processor
            current_stage = "image"
            self.logger.info("  [%s] Image Processing: %s", doc_index, filename)
            result3 = await self.processors['image'].process(context)

            if isinstance(result3, dict):
                images_count = result3.get('images_processed', 0)
                if not result3.get('success', False):
                    raise Exception(result3.get('error', 'Image processing failed'))
            else:
                images_count = result3.data.get('images_processed', 0)
            
            # Stage 3b: Visual Embedding Processor (NEW! - Multi-modal support)
            current_stage = "visual_embedding"
            self.logger.info("  [%s] Visual Embeddings: %s", doc_index, filename)
            result3b = await self.processors['visual_embedding'].process(context)
            visual_embeddings_count = result3b.data.get('embeddings_created', 0) if result3b.success else 0
            
            # Stage 4: Classification Processor
            current_stage = "classification"
            self.logger.info("  [%s] Classification: %s", doc_index, filename)
            result4 = await self.processors['classification'].process(context)
            
            # Stage 5: Chunk Preprocessing (NEW! - AI-ready chunks)
            current_stage = "chunk_prep"
            self.logger.info("  [%s] Chunk Preprocessing: %s", doc_index, filename)
            result4b = await self.processors['chunk_prep'].process(context)
            chunks_preprocessed = result4b.data.get('chunks_preprocessed', 0) if result4b.success else 0
            self.logger.info("    → %s chunks preprocessed", chunks_preprocessed)
            
            # Stage 6: Link Extraction Processor
            current_stage = "links"
            self.logger.info("  [%s] Link Extraction: %s", doc_index, filename)
            result4c = await self.processors['links'].process(context)
            links_count = result4c.data.get('links_extracted', 0) if result4c.success else 0
            video_count = result4c.data.get('video_links_created', 0) if result4c.success else 0
            self.logger.info("    → %s links, %s videos", links_count, video_count)
            
            # Stage 7: Metadata Processor (Error Codes)
            current_stage = "metadata"
            self.logger.info("  [%s] Metadata (Error Codes): %s", doc_index, filename)
            result5 = await self.processors['metadata'].process(context)
            error_codes_count = result5.data.get('error_codes_found', 0) if result5.success else 0
            self.logger.info("    → %s error codes", error_codes_count)
            
            # Stage 8: Storage Processor
            current_stage = "storage"
            self.logger.info("  [%s] Storage: %s", doc_index, filename)
            result6 = await self.processors['storage'].process(context)
            
            # Stage 9: Embedding Processor (Uses intelligence.chunks!)
            current_stage = "embedding"
            self.logger.info("  [%s] Embeddings: %s", doc_index, filename)
            result7 = await self.processors['embedding'].process(context)
            
            # Stage 10: Search Processor
            current_stage = "search"
            self.logger.info("  [%s] Search Index: %s", doc_index, filename)
            result8 = await self.processors['search'].process(context)
            
            self.logger.info("  [%s] Completed: %s", doc_index, filename)
            
            return {
                'success': True,
                'document_id': context.document_id,
                'filename': filename,
                'file_size': file_size,
                'chunks': chunks_count,
                'tables': tables_count,
                'svgs_extracted': svg_count,
                'svgs_converted': svg_converted,
                'images': images_count,
                'visual_embeddings': visual_embeddings_count,
                'smart_processing': False
            }
            
        except Exception as e:
            self.logger.error(
                "Document processing failed at stage '%s' for %s: %s",
                locals().get('current_stage', 'unknown'),
                os.path.basename(file_path),
                e,
                exc_info=True,
            )

            try:
                failed_stage = locals().get('current_stage', 'unknown')
                context = locals().get('context')
                if (
                    failed_stage not in ('storage', 'embedding', 'search')
                    and context is not None
                    and (getattr(context, 'images', None) or [])
                    and self.processors.get('storage') is not None
                ):
                    self.logger.info(
                        "Attempting storage upload for extracted images despite failure (failed_stage=%s)",
                        failed_stage,
                    )
                    await self.processors['storage'].process(context)
            except Exception:
                self.logger.error(
                    "Failed to persist images via storage stage during failure handling",
                    exc_info=True,
                )

            return {
                'success': False,
                'error': str(e),
                'failed_stage': locals().get('current_stage', 'unknown'),
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
    
    async def monitor_hardware(
        self,
        *,
        sleep_interval: float = 5.0,
        max_iterations: Optional[int] = None,
        sleep_func: Optional[Callable[[float], Awaitable[None]]] = None,
    ):
        """Monitor hardware usage and pipeline progress during processing.

        Args:
            sleep_interval: Delay between status updates (defaults to 5 seconds).
            max_iterations: Optional guard to exit after N loops (used by tests).
            sleep_func: Optional awaitable used instead of asyncio.sleep for tests.
        """
        last_doc_count = 0
        last_classified_count = 0
        last_chunk_count = 0
        last_error_count = 0
        show_detailed_view = False
        iterations = 0
        
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
            if max_iterations is not None and iterations >= max_iterations:
                break
            try:
                if sleep_func:
                    await sleep_func(sleep_interval)
                else:
                    await asyncio.sleep(sleep_interval)
                
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
            finally:
                iterations += 1
    
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
            # Use base tables instead of missing views
            docs_rows = await self.database_service.execute_query(
                "SELECT * FROM krai_core.documents"
            )
            chunks_rows = await self.database_service.execute_query(
                "SELECT * FROM krai_intelligence.chunks"
            )
            images_rows = await self.database_service.execute_query(
                "SELECT * FROM krai_content.images"
            )

            total_docs = len(docs_rows)
            classified_docs = len([d for d in docs_rows if d.get('manufacturer')])
            total_chunks = len(chunks_rows)
            total_images = len(images_rows)

            recent_docs = sorted(docs_rows, key=lambda x: x.get('created_at', ''), reverse=True)[:3] if docs_rows else []
            
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
                elif latest_doc.get('id') in [c.get('document_id') for c in chunks_rows]:
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
            # Use base table instead of missing column
            rows = await self.database_service.execute_query(
                "SELECT COUNT(*) as error_count FROM krai_core.documents WHERE processing_status = 'failed'"
            )
            return rows[0]['error_count'] if rows else 0
        except Exception as e:
            self.logger.error("Error getting error document count: %s", e)
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

    async def run_single_stage(self, document_id: str, stage) -> Dict[str, Any]:
        """
        Run a single processing stage for a document
        
        Args:
            document_id: Document UUID
            stage: Stage enum or stage name
            
        Returns:
            Dict with processing result
        """
        from backend.core.base_processor import Stage
        
        # Convert stage to enum if needed
        if isinstance(stage, str):
            try:
                stage = Stage(stage)
            except ValueError:
                return {'success': False, 'error': f'Invalid stage: {stage}'}
        
        # Get processor for stage
        processor_map = {
            Stage.UPLOAD: 'upload',
            Stage.TEXT_EXTRACTION: 'text',
            Stage.TABLE_EXTRACTION: 'table',
            Stage.SVG_PROCESSING: 'svg',
            Stage.IMAGE_PROCESSING: 'image',
            Stage.VISUAL_EMBEDDING: 'visual_embedding',
            Stage.LINK_EXTRACTION: 'links',
            Stage.CHUNK_PREPROCESSING: 'chunk_prep',
            Stage.CLASSIFICATION: 'classification',
            Stage.METADATA_EXTRACTION: 'metadata',
            Stage.PARTS_EXTRACTION: 'parts',
            Stage.SERIES_DETECTION: 'parts',  # Uses parts processor
            Stage.STORAGE: 'storage',
            Stage.EMBEDDING: 'embedding',
            Stage.SEARCH_INDEXING: 'search'
        }
        
        processor_key = processor_map.get(stage)
        if not processor_key or processor_key not in self.processors:
            return {'success': False, 'error': f'No processor for stage: {stage.value}'}
        
        processor = self.processors[processor_key]
        if not processor:
            return {'success': False, 'error': f'Processor not available for stage: {stage.value}'}
        
        try:
            # Create processing context
            from backend.core.base_processor import ProcessingContext
            
            # Get document info for context
            document = await self.database_service.get_document(document_id)
            if not document:
                return {'success': False, 'error': f'Document not found: {document_id}'}
            
            # Build context based on stage requirements
            context_data = {
                'document_id': document_id,
                'file_hash': '',  # Will be derived if needed
                'document_type': getattr(document, 'document_type', 'service_manual')
            }
            
            # Add file path for stages that need it
            if stage in [Stage.UPLOAD, Stage.TEXT_EXTRACTION, Stage.TABLE_EXTRACTION, Stage.IMAGE_PROCESSING]:
                file_path = getattr(document, 'storage_path', None) or getattr(document, 'resolved_path', None)
                if file_path and os.path.exists(file_path):
                    context_data['file_path'] = file_path
                    context_data['pdf_path'] = file_path
            
            # Add images for visual embedding
            if stage == Stage.VISUAL_EMBEDDING:
                # Get images from database
                images = await self.database_service.execute_query(
                    "SELECT * FROM kai_intelligence.media WHERE document_id = $1",
                    [document_id]
                )
                context_data['images'] = images or []
            
            # Add chunks for embedding
            if stage == Stage.EMBEDDING:
                chunks = await self.database_service.get_chunks_by_document(document_id)
                context_data['chunks'] = chunks or []
            
            context = ProcessingContext(**context_data)
            
            # Run processor
            result = await processor.process(context)
            
            return {
                'success': result.success if hasattr(result, 'success') else True,
                'data': result.data if hasattr(result, 'data') else result,
                'stage': stage.value,
                'processor': processor_key
            }
            
        except Exception as e:
            self.logger.error(f"Error running stage {stage.value} for document {document_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': stage.value
            }
    
    async def run_stages(self, document_id: str, stages: List) -> Dict[str, Any]:
        """
        Run multiple stages for a document
        
        Args:
            document_id: Document UUID
            stages: List of Stage enums or stage names
            
        Returns:
            Dict with processing results for all stages
        """
        results = {
            'document_id': document_id,
            'total_stages': len(stages),
            'successful': 0,
            'failed': 0,
            'stage_results': []
        }
        
        for stage in stages:
            stage_result = await self.run_single_stage(document_id, stage)
            results['stage_results'].append(stage_result)
            
            if stage_result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                
                # Stop on failure if not configured to continue
                if not self.force_continue_on_errors:
                    self.logger.error(f"Stopping pipeline due to stage failure: {stage}")
                    break
        
        results['success_rate'] = results['successful'] / results['total_stages'] * 100 if results['total_stages'] > 0 else 0
        
        return results
    
    def get_available_stages(self) -> List[str]:
        """
        Get list of all available stages
        
        Returns:
            List of stage names
        """
        from backend.core.base_processor import Stage
        return [stage.value for stage in Stage]
    
    async def get_stage_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get current stage status for a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            Dict with stage status information
        """
        try:
            result = await self.database_service.execute_query(
                "SELECT stage_status FROM krai_core.documents WHERE id = $1",
                [document_id]
            )
            
            if result and len(result) > 0:
                return {
                    'document_id': document_id,
                    'stage_status': result[0].get('stage_status', {}),
                    'found': True
                }
            
            return {
                'document_id': document_id,
                'stage_status': {},
                'found': False,
                'error': 'Document not found'
            }
            
        except Exception as e:
            return {
                'document_id': document_id,
                'stage_status': {},
                'found': False,
                'error': str(e)
            }

async def main():
    """Main function with menu system"""
    pipeline = KRMasterPipeline()
    await pipeline.initialize_services()
    logger = pipeline.logger

    logger.info("KRAI-ENGINE MASTER PIPELINE")
    
    while True:
        logger.info("")
        logger.info("MENU:")
        logger.info("1. Status Check - Zeige aktuelle Dokument-Status")
        logger.info("2. Smart Processing - Nur fehlende Stages verarbeiten")
        logger.info("3. Hardware Waker - Verarbeite neue Dokumente (CPU/GPU)")
        logger.info("4. Einzelnes Dokument verarbeiten")
        logger.info("5. Batch Processing - Alle Dokumente verarbeiten")
        logger.info("6. Debug - Zeige Pfad-Informationen")
        logger.info("7. Exit")
        logger.info("8. Quality Check - Prüfe Verarbeitungsqualität")
        logger.info("x/q. Exit")
        
        choice = input("\nWähle Option (1-8 oder x/q): ").strip().lower()
        if choice in ("x", "q", "0", "exit", "quit"):
            choice = "7"
        
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
                if not doc.get('id'):
                    logger.info("  %s. %s - local_only (no DB record yet)", i + 1, doc['filename'])
                    continue

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

                if not doc.get('id'):
                    result = await pipeline.process_single_document_full_pipeline(
                        doc['file_path'],
                        i + 1,
                        len(documents),
                    )
                else:
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
            
        elif choice == "4":
            # Single Document Processing
            logger.info("=== EINZELNES DOKUMENT ===")
            file_input = input("Vollen Dateipfad eingeben (oder nur Dateiname, wenn in service_documents): ").strip()
            if not file_input:
                logger.info("Kein Pfad eingegeben.")
                continue

            file_path = file_input
            if not os.path.isabs(file_path) and not os.path.exists(file_path):
                # Try to resolve relative name via service_documents
                pdf_directory = pipeline.find_service_documents_directory()
                if not pdf_directory:
                    logger.error("Kein service_documents-Verzeichnis gefunden – bitte vollen Pfad angeben.")
                    continue
                file_path = os.path.join(pdf_directory, file_input)

            if not os.path.exists(file_path):
                logger.error("Datei nicht gefunden: %s", file_path)
                continue

            response = input(f"\nVollständige Pipeline für {os.path.basename(file_path)} ausführen? (y/n): ").lower().strip()
            if response != "y":
                logger.info("Verarbeitung abgebrochen.")
                continue

            result = await pipeline.process_single_document_full_pipeline(file_path, 1, 1)
            if result.get("success"):
                logger.info("[SUCCESS] Erfolgreich verarbeitet: %s!", result.get("filename", os.path.basename(file_path)))
                logger.info("Images processed: %s", result.get("images", 0))
            else:
                logger.error(
                    "[FAILED] Fehler bei %s: %s",
                    result.get("filename", os.path.basename(file_path)),
                    result.get("error", "Unbekannter Fehler"),
                )
                
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
            
        elif choice == "7":
            logger.info("Exiting...")
            logger.info("Auf Wiedersehen! KR-AI-Engine Master Pipeline beendet.")
            break

        elif choice == "8":
            # Quality Check
            logger.info("=== QUALITY CHECK ===")
            logger.info("1. Check single document")
            logger.info("2. Check pipeline health")
            logger.info("3. Check all documents")
            
            qc_choice = input("\nWähle (1-3): ").strip()
            
            if qc_choice == "1":
                filename = input("Dateiname (wie in service_documents): ").strip()
                if not filename:
                    logger.info("Kein Dateiname eingegeben.")
                    continue

                doc_row = await pipeline._get_document_row_by_filename(filename)
                if not doc_row or not doc_row.get('id'):
                    logger.error("Kein DB-Eintrag für %s gefunden (bitte erst per Option 4/5 verarbeiten).", filename)
                    continue

                doc_id = doc_row['id']
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
        
        else:
            logger.warning("Ungültige Option. Bitte 1-8 oder x/q wählen.")

if __name__ == "__main__":
    asyncio.run(main())
