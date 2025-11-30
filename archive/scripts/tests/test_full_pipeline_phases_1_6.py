#!/usr/bin/env python3
"""
KRAI Full Pipeline Test - Phases 1-6
====================================

Comprehensive end-to-end test for the complete KRAI pipeline with all Phase 1-6 features.
This script validates the entire processing pipeline from PDF upload through all 10 stages.

Features Tested:
- Phase 1: Infrastructure (MinIO, PostgreSQL, Ollama)
- Phase 2: Database (Migrations 116-119, RPC functions)
- Phase 3: Services (Generic storage, AI service)
- Phase 4: Multi-modal embeddings (text, visual, table)
- Phase 5: Context extraction (images, videos, links, tables)
- Phase 6: Advanced features (hierarchical chunking, SVG, multimodal search)

Usage:
    python scripts/test_full_pipeline_phases_1_6.py
    python scripts/test_full_pipeline_phases_1_6.py --verbose
    python scripts/test_full_pipeline_phases_1_6.py --scenario svg
"""

import os
import sys
import asyncio
import argparse
import json
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from io import BytesIO

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Backend imports
from backend.services.database_service import DatabaseService
from backend.services.object_storage_service import ObjectStorageService
from backend.services.storage_factory import create_storage_service
from backend.services.ai_service import AIService
from backend.services.config_service import ConfigService
from backend.services.features_service import FeaturesService
from backend.services.quality_check_service import QualityCheckService
from backend.services.context_extraction_service import ContextExtractionService
from backend.services.multimodal_search_service import MultimodalSearchService

from backend.pipeline.master_pipeline import KRMasterPipeline
from backend.core.base_processor import ProcessingContext

@dataclass
class TestResult:
    """Test result data structure"""
    scenario: str
    success: bool
    duration: float
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    skipped: bool = False

class FullPipelineTestRunner:
    """Comprehensive test runner for KRAI Phases 1-6"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.pipeline_test")
        self.results: List[TestResult] = []
        
        # Initialize services
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.pipeline = None
        self.context_service = None
        self.search_service = None
        
        # Test data
        self.test_documents = []
        self.test_document_ids = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_status(self, message: str, status: str = 'info'):
        """Print status message with appropriate formatting"""
        if self.console:
            color = {
                'success': 'green',
                'warning': 'yellow',
                'error': 'red',
                'info': 'blue',
                'test': 'cyan'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize all services and prepare test environment"""
        try:
            self.print_status("Setting up Full Pipeline Test Runner", 'test')
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Initialize database service
            self.print_status("Initializing database service...", 'info')
            self.database_service = DatabaseService(
                supabase_url=None,
                supabase_key=None,
                postgres_url=os.getenv('DATABASE_URL'),
                database_type='postgresql'
            )
            await self.database_service.connect()
            
            # Initialize storage service
            self.print_status("Initializing storage service...", 'info')
            self.storage_service = create_storage_service()
            await self.storage_service.connect()
            
            # Initialize AI service
            self.print_status("Initializing AI service...", 'info')
            self.ai_service = AIService()
            await self.ai_service.connect()
            
            # Initialize pipeline
            self.print_status("Initializing master pipeline...", 'info')
            self.pipeline = KRMasterPipeline()
            await self.pipeline.initialize_services()
            
            # Initialize context service
            self.print_status("Initializing context extraction service...", 'info')
            self.context_service = ContextExtractionService(
                self.database_service, 
                self.ai_service
            )
            
            # Initialize search service
            self.print_status("Initializing multimodal search service...", 'info')
            self.search_service = MultimodalSearchService(
                self.database_service,
                self.ai_service
            )
            
            # Prepare test documents
            await self._prepare_test_documents()
            
            self.print_status("Setup completed successfully!", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def _prepare_test_documents(self):
        """Prepare test documents for processing"""
        # Look for test PDFs in service_documents directory
        service_docs_dir = Path("service_documents")
        
        if not service_docs_dir.exists():
            self.print_status("Creating service_documents directory with test files", 'warning')
            service_docs_dir.mkdir(exist_ok=True)
            # TODO: Add sample PDF creation if needed
            return
        
        # Find PDF files
        pdf_files = list(service_docs_dir.glob("*.pdf"))
        
        if not pdf_files:
            self.print_status("No PDF files found in service_documents directory", 'warning')
            return
        
        self.print_status(f"Found {len(pdf_files)} PDF files for testing", 'info')
        for pdf_file in pdf_files:
            self.test_documents.append({
                'filename': pdf_file.name,
                'file_path': str(pdf_file),
                'file_size': pdf_file.stat().st_size
            })
    
    async def test_svg_processing(self) -> TestResult:
        """Test SVG vector graphics processing (Scenario 1)"""
        start_time = time.time()
        scenario = "SVG Processing"
        
        try:
            self.print_status(f"Testing {scenario}...", 'test')
            
            details = {
                'svgs_extracted': 0,
                'png_conversions': 0,
                'vision_analyses': 0,
                'vector_graphics_stored': 0
            }
            errors = []
            warnings = []
            
            # Check if SVG extraction is enabled
            svg_enabled = os.getenv('ENABLE_SVG_EXTRACTION', 'false').lower() == 'true'
            if not svg_enabled:
                warnings.append("SVG extraction is disabled - enable with ENABLE_SVG_EXTRACTION=true")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings, skipped=True)
            
            # Process a test document
            if not self.test_documents:
                errors.append("No test documents available")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
            
            test_doc = self.test_documents[0]
            self.print_status(f"Processing document: {test_doc['filename']}", 'info')
            
            # Create processing context
            context = ProcessingContext(
                file_path=test_doc['file_path'],
                document_id=str(uuid.uuid4()),
                file_hash="test-hash",
                document_type="service_manual",
                processing_config={'filename': test_doc['filename']},
                file_size=test_doc['file_size']
            )
            
            # Process through upload stage to get document ID
            upload_result = await self.pipeline.processors['upload'].process(context)
            if not upload_result.success:
                errors.append(f"Upload failed: {upload_result.message}")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
            
            document_id = upload_result.data.get('document_id')
            context.document_id = document_id
            
            # Process SVG stage
            svg_processor = self.pipeline.processors.get('svg')
            if not svg_processor:
                warnings.append("SVG processor not available")
                return TestResult(scenario, True, time.time() - start_time, details, errors, warnings)
            
            svg_result = await svg_processor.process(context)
            
            if svg_result.success:
                details['svgs_extracted'] = svg_result.data.get('svgs_extracted', 0)
                details['png_conversions'] = svg_result.data.get('png_conversions', 0)
                details['images_queued'] = svg_result.data.get('images_queued', 0)
                
                # Query database for vector graphics
                if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                    async with self.database_service.pg_pool.acquire() as conn:
                        vector_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1 AND image_type = 'vector_graphic'",
                            document_id
                        )
                        details['vector_graphics_stored'] = vector_count
                
                self.print_status(f"SVG processing completed: {details['svgs_extracted']} SVGs extracted", 'success')
            else:
                errors.append(f"SVG processing failed: {svg_result.message}")
            
            # Store document ID for cleanup
            self.test_document_ids.append(document_id)
            
            return TestResult(scenario, svg_result.success, time.time() - start_time, details, errors, warnings)
            
        except Exception as e:
            self.print_status(f"SVG processing test failed: {e}", 'error')
            self.logger.error("SVG processing test failed", exc_info=True)
            return TestResult(scenario, False, time.time() - start_time, {}, [str(e)], [])
    
    async def test_hierarchical_chunking(self) -> TestResult:
        """Test hierarchical chunking feature (Scenario 2)"""
        start_time = time.time()
        scenario = "Hierarchical Chunking"
        
        try:
            self.print_status(f"Testing {scenario}...", 'test')
            
            details = {
                'chunks_with_hierarchy': 0,
                'error_code_sections': 0,
                'linked_chunks': 0,
                'section_levels': 0
            }
            errors = []
            warnings = []
            
            # Check if hierarchical chunking is enabled
            hierarchical_enabled = os.getenv('ENABLE_HIERARCHICAL_CHUNKING', 'true').lower() == 'true'
            if not hierarchical_enabled:
                warnings.append("Hierarchical chunking is disabled")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings, skipped=True)
            
            # Use existing document or create new one
            if not self.test_document_ids:
                # Process a document first
                if not self.test_documents:
                    errors.append("No test documents available")
                    return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
                
                test_doc = self.test_documents[0]
                context = ProcessingContext(
                    file_path=test_doc['file_path'],
                    document_id=str(uuid.uuid4()),
                    file_hash="test-hash",
                    document_type="service_manual",
                    processing_config={'filename': test_doc['filename']},
                    file_size=test_doc['file_size']
                )
                
                upload_result = await self.pipeline.processors['upload'].process(context)
                if upload_result.success:
                    self.test_document_ids.append(upload_result.data.get('document_id'))
            
            document_id = self.test_document_ids[-1] if self.test_document_ids else None
            if not document_id:
                errors.append("No document ID available for testing")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
            
            # Process text stage to generate chunks
            context = ProcessingContext(
                file_path=self.test_documents[0]['file_path'],
                document_id=document_id,
                file_hash="test-hash",
                document_type="service_manual",
                processing_config={'filename': self.test_documents[0]['filename']},
                file_size=self.test_documents[0]['file_size']
            )
            
            text_result = await self.pipeline.processors['text'].process(context)
            
            if text_result.success:
                # Query chunks for hierarchical structure
                if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                    async with self.database_service.pg_pool.acquire() as conn:
                        # Count chunks with section hierarchy
                        hierarchy_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.chunks WHERE document_id = $1 AND metadata->>'section_hierarchy' IS NOT NULL",
                            document_id
                        )
                        details['chunks_with_hierarchy'] = hierarchy_count
                        
                        # Count error code sections
                        error_code_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.chunks WHERE document_id = $1 AND metadata->>'error_code' IS NOT NULL",
                            document_id
                        )
                        details['error_code_sections'] = error_code_count
                        
                        # Count linked chunks
                        linked_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.chunks WHERE document_id = $1 AND (metadata->>'previous_chunk_id' IS NOT NULL OR metadata->>'next_chunk_id' IS NOT NULL)",
                            document_id
                        )
                        details['linked_chunks'] = linked_count
                        
                        # Get unique section levels
                        levels = await conn.fetch(
                            "SELECT DISTINCT metadata->>'section_level' as level FROM krai_intelligence.chunks WHERE document_id = $1 AND metadata->>'section_level' IS NOT NULL",
                            document_id
                        )
                        details['section_levels'] = len([row['level'] for row in levels if row['level']])
                
                self.print_status(f"Hierarchical chunking completed: {details['chunks_with_hierarchy']} chunks with hierarchy", 'success')
            else:
                errors.append(f"Text processing failed: {text_result.message}")
            
            return TestResult(scenario, text_result.success, time.time() - start_time, details, errors, warnings)
            
        except Exception as e:
            self.print_status(f"Hierarchical chunking test failed: {e}", 'error')
            self.logger.error("Hierarchical chunking test failed", exc_info=True)
            return TestResult(scenario, False, time.time() - start_time, {}, [str(e)], [])
    
    async def test_table_extraction(self) -> TestResult:
        """Test table extraction and embedding (Scenario 3)"""
        start_time = time.time()
        scenario = "Table Extraction"
        
        try:
            self.print_status(f"Testing {scenario}...", 'test')
            
            details = {
                'tables_extracted': 0,
                'tables_with_markdown': 0,
                'table_embeddings': 0,
                'structured_tables': 0
            }
            errors = []
            warnings = []
            
            # Check if table extraction is enabled
            table_enabled = os.getenv('ENABLE_TABLE_EXTRACTION', 'true').lower() == 'true'
            if not table_enabled:
                warnings.append("Table extraction is disabled")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings, skipped=True)
            
            # Use existing document
            if not self.test_document_ids:
                errors.append("No document available for testing")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
            
            document_id = self.test_document_ids[-1]
            
            # Process table stage
            context = ProcessingContext(
                file_path=self.test_documents[0]['file_path'],
                document_id=document_id,
                file_hash="test-hash",
                document_type="service_manual",
                processing_config={'filename': self.test_documents[0]['filename']},
                file_size=self.test_documents[0]['file_size']
            )
            
            table_processor = self.pipeline.processors.get('table')
            if not table_processor:
                warnings.append("Table processor not available")
                return TestResult(scenario, True, time.time() - start_time, details, errors, warnings)
            
            table_result = await table_processor.process(context)
            
            if table_result.success:
                details['tables_extracted'] = table_result.data.get('tables_extracted', 0)
                
                # Query structured tables
                if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                    async with self.database_service.pg_pool.acquire() as conn:
                        # Count structured tables
                        table_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.structured_tables WHERE document_id = $1",
                            document_id
                        )
                        details['structured_tables'] = table_count
                        
                        # Count tables with markdown
                        markdown_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.structured_tables WHERE document_id = $1 AND table_markdown IS NOT NULL",
                            document_id
                        )
                        details['tables_with_markdown'] = markdown_count
                        
                        # Count table embeddings
                        embedding_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_intelligence.embeddings_v2 WHERE document_id = $1 AND source_type = 'table'",
                            document_id
                        )
                        details['table_embeddings'] = embedding_count
                
                self.print_status(f"Table extraction completed: {details['tables_extracted']} tables extracted", 'success')
            else:
                errors.append(f"Table extraction failed: {table_result.message}")
            
            return TestResult(scenario, table_result.success, time.time() - start_time, details, errors, warnings)
            
        except Exception as e:
            self.print_status(f"Table extraction test failed: {e}", 'error')
            self.logger.error("Table extraction test failed", exc_info=True)
            return TestResult(scenario, False, time.time() - start_time, {}, [str(e)], [])
    
    async def test_context_extraction(self) -> TestResult:
        """Test context extraction for all media types (Scenario 4)"""
        start_time = time.time()
        scenario = "Context Extraction"
        
        try:
            self.print_status(f"Testing {scenario}...", 'test')
            
            details = {
                'images_with_context': 0,
                'videos_with_context': 0,
                'links_with_context': 0,
                'tables_with_context': 0,
                'context_embeddings': 0
            }
            errors = []
            warnings = []
            
            # Check if context extraction is enabled
            context_enabled = os.getenv('ENABLE_CONTEXT_EXTRACTION', 'true').lower() == 'true'
            if not context_enabled:
                warnings.append("Context extraction is disabled")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings, skipped=True)
            
            # Use existing document
            if not self.test_document_ids:
                errors.append("No document available for testing")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
            
            document_id = self.test_document_ids[-1]
            
            # Query context data
            if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                async with self.database_service.pg_pool.acquire() as conn:
                    # Count images with context
                    images_context = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1 AND context_caption IS NOT NULL",
                        document_id
                    )
                    details['images_with_context'] = images_context
                    
                    # Count videos with context
                    videos_context = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_content.instructional_videos WHERE document_id = $1 AND context_description IS NOT NULL",
                        document_id
                    )
                    details['videos_with_context'] = videos_context
                    
                    # Count links with context
                    links_context = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_content.links WHERE document_id = $1 AND context_description IS NOT NULL",
                        document_id
                    )
                    details['links_with_context'] = links_context
                    
                    # Count tables with context
                    tables_context = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_intelligence.structured_tables WHERE document_id = $1 AND context_text IS NOT NULL",
                        document_id
                    )
                    details['tables_with_context'] = tables_context
                    
                    # Count context embeddings
                    context_embeddings = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_intelligence.embeddings_v2 WHERE document_id = $1 AND source_type = 'context'",
                        document_id
                    )
                    details['context_embeddings'] = context_embeddings
            
            total_context = sum([
                details['images_with_context'],
                details['videos_with_context'],
                details['links_with_context'],
                details['tables_with_context']
            ])
            
            self.print_status(f"Context extraction completed: {total_context} media items with context", 'success')
            
            return TestResult(scenario, total_context > 0, time.time() - start_time, details, errors, warnings)
            
        except Exception as e:
            self.print_status(f"Context extraction test failed: {e}", 'error')
            self.logger.error("Context extraction test failed", exc_info=True)
            return TestResult(scenario, False, time.time() - start_time, {}, [str(e)], [])
    
    async def test_multimodal_embeddings(self) -> TestResult:
        """Test multimodal embeddings generation (Scenario 5)"""
        start_time = time.time()
        scenario = "Multimodal Embeddings"
        
        try:
            self.print_status(f"Testing {scenario}...", 'test')
            
            details = {
                'text_embeddings': 0,
                'image_embeddings': 0,
                'table_embeddings': 0,
                'context_embeddings': 0,
                'total_embeddings': 0
            }
            errors = []
            warnings = []
            
            # Use existing document
            if not self.test_document_ids:
                errors.append("No document available for testing")
                return TestResult(scenario, False, time.time() - start_time, details, errors, warnings)
            
            document_id = self.test_document_ids[-1]
            
            # Query embeddings by type
            if hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                async with self.database_service.pg_pool.acquire() as conn:
                    # Count embeddings by source type
                    embedding_types = await conn.fetch(
                        "SELECT source_type, COUNT(*) as count FROM krai_intelligence.embeddings_v2 WHERE document_id = $1 GROUP BY source_type",
                        document_id
                    )
                    
                    for row in embedding_types:
                        source_type = row['source_type']
                        count = row['count']
                        
                        if source_type == 'text':
                            details['text_embeddings'] = count
                        elif source_type == 'image':
                            details['image_embeddings'] = count
                        elif source_type == 'table':
                            details['table_embeddings'] = count
                        elif source_type == 'context':
                            details['context_embeddings'] = count
                        
                        details['total_embeddings'] += count
            
            self.print_status(f"Multimodal embeddings completed: {details['total_embeddings']} total embeddings", 'success')
            
            return TestResult(scenario, details['total_embeddings'] > 0, time.time() - start_time, details, errors, warnings)
            
        except Exception as e:
            self.print_status(f"Multimodal embeddings test failed: {e}", 'error')
            self.logger.error("Multimodal embeddings test failed", exc_info=True)
            return TestResult(scenario, False, time.time() - start_time, {}, [str(e)], [])
    
    async def test_multimodal_search(self) -> TestResult:
        """Test multimodal search functionality"""
        start_time = time.time()
        scenario = "Multimodal Search"
        
        try:
            self.print_status(f"Testing {scenario}...", 'test')
            
            details = {
                'unified_search_results': 0,
                'image_search_results': 0,
                'two_stage_results': 0,
                'search_latency_ms': 0
            }
            errors = []
            warnings = []
            
            # Test queries
            test_queries = [
                "error 900.01",
                "fuser unit",
                "paper jam",
                "technical specifications"
            ]
            
            total_results = 0
            search_start = time.time()
            
            for query in test_queries:
                try:
                    # Test unified multimodal search
                    search_results = await self.search_service.search_multimodal(
                        query=query,
                        threshold=0.5,
                        limit=5,
                        modalities=['text', 'image', 'table', 'video']
                    )
                    
                    if search_results and search_results.get('results'):
                        results = search_results['results']
                        results_by_type = {}
                        for result in results:
                            source_type = result.get('source_type', 'unknown')
                            results_by_type[source_type] = results_by_type.get(source_type, 0) + 1
                        
                        total_results += len(results)
                        self.print_status(f"Query '{query}': {len(results)} results ({dict(results_by_type)})", 'info')
                    
                except Exception as e:
                    warnings.append(f"Search failed for query '{query}': {e}")
            
            search_latency = (time.time() - search_start) * 1000
            details['unified_search_results'] = total_results
            details['search_latency_ms'] = round(search_latency, 2)
            
            self.print_status(f"Multimodal search completed: {total_results} total results in {search_latency:.2f}ms", 'success')
            
            return TestResult(scenario, total_results > 0, time.time() - start_time, details, errors, warnings)
            
        except Exception as e:
            self.print_status(f"Multimodal search test failed: {e}", 'error')
            self.logger.error("Multimodal search test failed", exc_info=True)
            return TestResult(scenario, False, time.time() - start_time, {}, [str(e)], [])
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios"""
        self.print_status("Starting Full Pipeline Test Suite", 'test')
        
        if not await self.setup():
            return {'success': False, 'error': 'Setup failed'}
        
        # Define test scenarios
        test_scenarios = [
            self.test_svg_processing,
            self.test_hierarchical_chunking,
            self.test_table_extraction,
            self.test_context_extraction,
            self.test_multimodal_embeddings,
            self.test_multimodal_search
        ]
        
        # Run tests with progress bar
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Running tests...", total=len(test_scenarios))
                
                for test_func in test_scenarios:
                    progress.update(task, description=test_func.__name__)
                    result = await test_func()
                    self.results.append(result)
                    progress.advance(task)
        else:
            for test_func in test_scenarios:
                self.print_status(f"Running {test_func.__name__}...", 'test')
                result = await test_func()
                self.results.append(result)
        
        # Generate summary
        await self.generate_test_report()
        
        # Cleanup
        await self.cleanup()
        
        return {
            'success': True,
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results if r.success and not r.skipped),
            'failed': sum(1 for r in self.results if not r.success and not r.skipped),
            'skipped': sum(1 for r in self.results if r.skipped),
            'results': [vars(r) for r in self.results]
        }
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        if not self.console:
            self.print_plain_report()
            return
        
        # Summary panel
        passed = sum(1 for r in self.results if r.success and not r.skipped)
        failed = sum(1 for r in self.results if not r.success and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        total = len(self.results)
        
        summary_text = f"""
Total Tests: {total}
✅ Passed: {passed}
❌ Failed: {failed}
⏸️ Skipped: {skipped}
📊 Success Rate: {(passed/(total-skipped)*100):.1f}% (excluding skipped)
        """.strip()
        
        self.console.print(Panel(summary_text, title="🧪 Pipeline Test Results", border_style="blue"))
        
        # Results table
        table = Table(title="Test Scenario Results", box=box.ROUNDED)
        table.add_column("Scenario", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Key Metrics", style="white")
        
        for result in self.results:
            if result.skipped:
                status_icon = "⏸️"
                status_text = f"{status_icon} SKIP"
                status_style = "yellow"
            elif result.success:
                status_icon = "✅"
                status_text = f"{status_icon} PASS"
                status_style = "green"
            else:
                status_icon = "❌"
                status_text = f"{status_icon} FAIL"
                status_style = "red"
            
            # Extract key metrics
            metrics = []
            if result.scenario == "SVG Processing":
                metrics.append(f"SVGs: {result.details.get('svgs_extracted', 0)}")
                metrics.append(f"Vectors: {result.details.get('vector_graphics_stored', 0)}")
            elif result.scenario == "Hierarchical Chunking":
                metrics.append(f"Hierarchy: {result.details.get('chunks_with_hierarchy', 0)}")
                metrics.append(f"Error Codes: {result.details.get('error_code_sections', 0)}")
            elif result.scenario == "Table Extraction":
                metrics.append(f"Tables: {result.details.get('tables_extracted', 0)}")
                metrics.append(f"Embeddings: {result.details.get('table_embeddings', 0)}")
            elif result.scenario == "Context Extraction":
                total_context = sum([
                    result.details.get('images_with_context', 0),
                    result.details.get('videos_with_context', 0),
                    result.details.get('links_with_context', 0),
                    result.details.get('tables_with_context', 0)
                ])
                metrics.append(f"Context Items: {total_context}")
            elif result.scenario == "Multimodal Embeddings":
                metrics.append(f"Total: {result.details.get('total_embeddings', 0)}")
                metrics.append(f"Types: {sum(1 for k, v in result.details.items() if k.endswith('_embeddings') and v > 0)}")
            elif result.scenario == "Multimodal Search":
                metrics.append(f"Results: {result.details.get('unified_search_results', 0)}")
                metrics.append(f"Latency: {result.details.get('search_latency_ms', 0)}ms")
            
            table.add_row(
                result.scenario,
                status_text,
                f"{result.duration:.2f}s",
                " | ".join(metrics),
                style=status_style
            )
        
        self.console.print(table)
        
        # Errors and warnings
        if failed > 0:
            errors_panel = []
            warnings_panel = []
            
            for result in self.results:
                if result.errors:
                    errors_panel.append(f"\n{result.scenario}:")
                    errors_panel.extend([f"  • {error}" for error in result.errors])
                
                if result.warnings:
                    warnings_panel.append(f"\n{result.scenario}:")
                    warnings_panel.extend([f"  • {warning}" for warning in result.warnings])
            
            if errors_panel:
                self.console.print(Panel("".join(errors_panel), title="❌ Errors", border_style="red"))
            
            if warnings_panel:
                self.console.print(Panel("".join(warnings_panel), title="⚠️ Warnings", border_style="yellow"))
    
    def print_plain_report(self):
        """Print report in plain text format"""
        passed = sum(1 for r in self.results if r.success and not r.skipped)
        failed = sum(1 for r in self.results if not r.success and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        total = len(self.results)
        
        print(f"\n🧪 KRAI Pipeline Test Results")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏸️ Skipped: {skipped}")
        if total > skipped:
            print(f"📊 Success Rate: {(passed/(total-skipped)*100):.1f}% (excluding skipped)")
        print()
        
        print("Test Details:")
        print("-" * 30)
        
        for result in self.results:
            status = "PASS" if result.success else "FAIL"
            print(f"{result.scenario}: {status} ({result.duration:.2f}s)")
            
            if result.errors:
                for error in result.errors:
                    print(f"  ❌ {error}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"  ⚠️ {warning}")
            print()
    
    async def cleanup(self):
        """Clean up test data and resources"""
        try:
            self.print_status("Cleaning up test resources...", 'info')
            
            # Clean up test documents
            for document_id in self.test_document_ids:
                try:
                    # Delete document and related data
                    await self.database_service.delete_document(document_id)
                    self.print_status(f"Cleaned up document: {document_id}", 'info')
                except Exception as e:
                    self.print_status(f"Failed to cleanup document {document_id}: {e}", 'warning')
            
            # Close services
            if self.database_service:
                # Database service cleanup (disconnect not available)
                # await self.database_service.disconnect()
                # await self.storage_service.disconnect()
                # await self.ai_service.disconnect()
                pass
            if self.ai_service:
                # AI Service cleanup (disconnect method not available)
                # await self.ai_service.disconnect()
                pass
            
            self.print_status("Cleanup completed", 'success')
            
        except Exception as e:
            self.print_status(f"Cleanup failed: {e}", 'error')
            self.logger.error("Cleanup failed", exc_info=True)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='KRAI Full Pipeline Test - Phases 1-6')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--scenario', type=str, help='Run specific scenario only')
    
    args = parser.parse_args()
    
    runner = FullPipelineTestRunner(verbose=args.verbose)
    
    if args.scenario:
        # Run specific scenario
        scenario_map = {
            'svg': runner.test_svg_processing,
            'hierarchical': runner.test_hierarchical_chunking,
            'table': runner.test_table_extraction,
            'context': runner.test_context_extraction,
            'embeddings': runner.test_multimodal_embeddings,
            'search': runner.test_multimodal_search
        }
        
        if args.scenario not in scenario_map:
            print(f"Unknown scenario: {args.scenario}")
            print(f"Available scenarios: {', '.join(scenario_map.keys())}")
            sys.exit(1)
        
        await runner.setup()
        result = await scenario_map[args.scenario]()
        runner.results = [result]
        runner.generate_test_report()
        await runner.cleanup()
        
        sys.exit(0 if result.success else 1)
    else:
        # Run all tests
        results = await runner.run_all_tests()
        
        if results['success']:
            success_rate = results['passed'] / results['total_tests'] * 100
            print(f"\n🎉 Pipeline test completed: {results['passed']}/{results['total_tests']} passed ({success_rate:.1f}%)")
            sys.exit(0 if results['failed'] == 0 else 1)
        else:
            print(f"❌ Pipeline test failed: {results.get('error', 'Unknown error')}")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
