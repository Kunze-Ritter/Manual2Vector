#!/usr/bin/env python3
"""
KRAI Context Extraction Integration Test
=========================================

Comprehensive test for context extraction across all media types.
This script validates the ContextExtractionService's ability to extract and store
context for images, videos, links, and tables using Vision AI and LLM analysis.

Features Tested:
- Image context extraction using Vision AI
- Video link processing and context generation
- YouTube link metadata extraction and context
- Table structure analysis and context generation
- Context embedding generation for multimodal search
- Database storage and retrieval of context data

Usage:
    python scripts/test_context_extraction_integration.py
    python scripts/test_context_extraction_integration.py --verbose
    python scripts/test_context_extraction_integration.py --media-type image
    python scripts/test_context_extraction_integration.py --performance
"""

import os
import sys
import asyncio
import argparse
import json
import time
import uuid
import base64
import io
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich import box
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Backend imports
from backend.services.database_service import DatabaseService
from backend.services.ai_service import AIService
from backend.services.context_extraction_service import ContextExtractionService

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

@dataclass
class ContextExtractionTestResult:
    """Test result for context extraction"""
    media_type: str
    items_processed: int
    contexts_extracted: int
    embeddings_generated: int
    avg_processing_time_ms: float
    success_rate: float
    errors: List[str]
    warnings: List[str]

class ContextExtractionIntegrationTester:
    """Test runner for context extraction integration"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.context_extraction_test")
        
        # Test data
        self.test_images = []
        self.test_videos = []
        self.test_links = []
        self.test_tables = []
        
        # Performance targets
        self.performance_targets = {
            'image_context_ms': 500,
            'video_context_ms': 1000,
            'link_context_ms': 300,
            'table_context_ms': 200
        }
        
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
                'test': 'cyan',
                'context': 'orange'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪',
                'context': '📝'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            self.print_status("Setting up Context Extraction Integration Tester", 'test')
            
            # Check dependencies
            if not PIL_AVAILABLE:
                self.print_status("PIL not available - install with: pip install Pillow", 'error')
                return False
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Initialize services
            self.print_status("Initializing database service...", 'info')
            self.database_service = DatabaseService(
                supabase_url=None,
                supabase_key=None,
                postgres_url=os.getenv('DATABASE_URL'),
                database_type='postgresql'
            )
            await self.database_service.connect()
            
            self.print_status("Initializing AI service...", 'info')
            self.ai_service = AIService()
            await self.ai_service.connect()
            
            self.print_status("Initializing context extraction service...", 'info')
            self.context_service = ContextExtractionService(
                self.database_service,
                self.ai_service
            )
            
            # Prepare test data
            await self._prepare_test_data()
            
            self.print_status("Setup completed successfully", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def _prepare_test_data(self):
        """Prepare test data for context extraction"""
        self.print_status("Preparing test data...", 'info')
        
        # Create test images
        test_image = Image.new('RGB', (200, 100), color='blue')
        test_image_draw = Image.new('RGB', (300, 200), color='white')
        
        # Convert to base64 for testing
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        img_buffer2 = io.BytesIO()
        test_image_draw.save(img_buffer2, format='PNG')
        img_base642 = base64.b64encode(img_buffer2.getvalue()).decode()
        
        self.test_images = [
            {
                'id': str(uuid.uuid4()),
                'base64_data': img_base64,
                'filename': 'test_diagram_1.png',
                'expected_context': 'blue rectangular image'
            },
            {
                'id': str(uuid.uuid4()),
                'base64_data': img_base642,
                'filename': 'test_diagram_2.png',
                'expected_context': 'white rectangular image'
            }
        ]
        
        # Create test video data
        self.test_videos = [
            {
                'id': str(uuid.uuid4()),
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'title': 'Test Video 1',
                'expected_context': 'YouTube video content'
            },
            {
                'id': str(uuid.uuid4()),
                'url': 'https://www.youtube.com/watch?v=abc123def456',
                'title': 'Test Video 2',
                'expected_context': 'Another YouTube video'
            }
        ]
        
        # Create test links
        self.test_links = [
            {
                'id': str(uuid.uuid4()),
                'url': 'https://www.example.com/technical-specs',
                'title': 'Technical Specifications',
                'expected_context': 'Technical documentation link'
            },
            {
                'id': str(uuid.uuid4()),
                'url': 'https://www.manuals.com/troubleshooting',
                'title': 'Troubleshooting Guide',
                'expected_context': 'Troubleshooting documentation'
            }
        ]
        
        # Create test table data
        self.test_tables = [
            {
                'id': str(uuid.uuid4()),
                'markdown': '''
| Error Code | Description | Solution |
|------------|-------------|----------|
| 900.01 | Paper Jam | Open cover and remove paper |
| 900.02 | Toner Low | Replace toner cartridge |
| 900.03 | Fuser Error | Check fuser temperature |
                '''.strip(),
                'expected_context': 'Error code table with solutions'
            },
            {
                'id': str(uuid.uuid4()),
                'markdown': '''
| Part Number | Description | Compatible Models |
|-------------|-------------|-------------------|
| C4080-001 | Fuser Unit | C4080, C4085 |
| C4080-002 | Toner Cartridge | C4080 series |
| C4080-003 | Paper Tray | C4080, C4085, C4090 |
                '''.strip(),
                'expected_context': 'Parts compatibility table'
            }
        ]
        
        self.print_status(f"Prepared {len(self.test_images)} images, {len(self.test_videos)} videos, {len(self.test_links)} links, {len(self.test_tables)} tables", 'success')
    
    async def test_image_context_extraction(self) -> Dict[str, Any]:
        """Test image context extraction using Vision AI"""
        self.print_status("Testing image context extraction...", 'test')
        
        try:
            test_results = []
            
            for image_data in self.test_images:
                self.print_status(f"Processing image: {image_data['filename']}", 'context')
                
                start_time = time.time()
                
                try:
                    # Extract context using Vision AI
                    context_result = await self.context_service.extract_image_context(
                        image_base64=image_data['base64_data'],
                        image_filename=image_data['filename']
                    )
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if context_result:
                        # Generate embedding for context
                        embedding_result = await self.context_service.generate_context_embedding(
                            context_text=context_result
                        )
                        
                        test_result = {
                            'image_id': image_data['id'],
                            'filename': image_data['filename'],
                            'context_extracted': context_result is not None,
                            'context_length': len(context_result) if context_result else 0,
                            'embedding_generated': embedding_result is not None,
                            'embedding_length': len(embedding_result) if embedding_result else 0,
                            'processing_time_ms': processing_time,
                            'within_target': processing_time <= self.performance_targets['image_context_ms']
                        }
                        
                        test_results.append(test_result)
                        
                        status = "✅" if test_result['context_extracted'] and test_result['embedding_generated'] else "❌"
                        self.print_status(f"  {status} Context: {test_result['context_length']} chars, Embedding: {test_result['embedding_length']} dims", 'success' if test_result['context_extracted'] else 'error')
                        self.print_status(f"  ⏱️ Processing time: {processing_time:.2f}ms", 'info')
                    else:
                        test_results.append({
                            'image_id': image_data['id'],
                            'filename': image_data['filename'],
                            'context_extracted': False,
                            'context_length': 0,
                            'embedding_generated': False,
                            'embedding_length': 0,
                            'processing_time_ms': processing_time,
                            'within_target': False,
                            'error': 'Context extraction returned None'
                        })
                        self.print_status(f"  ❌ Context extraction failed", 'error')
                
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    test_results.append({
                        'image_id': image_data['id'],
                        'filename': image_data['filename'],
                        'context_extracted': False,
                        'context_length': 0,
                        'embedding_generated': False,
                        'embedding_length': 0,
                        'processing_time_ms': processing_time,
                        'within_target': False,
                        'error': str(e)
                    })
                    self.print_status(f"  ❌ Exception: {e}", 'error')
            
            # Calculate overall metrics
            successful_extractions = sum(1 for r in test_results if r['context_extracted'])
            successful_embeddings = sum(1 for r in test_results if r['embedding_generated'])
            avg_processing_time = sum(r['processing_time_ms'] for r in test_results) / len(test_results)
            within_target_count = sum(1 for r in test_results if r['within_target'])
            
            return {
                'success': successful_extractions > 0,
                'total_images': len(test_results),
                'successful_extractions': successful_extractions,
                'successful_embeddings': successful_embeddings,
                'extraction_success_rate': (successful_extractions / len(test_results)) * 100,
                'embedding_success_rate': (successful_embeddings / len(test_results)) * 100,
                'avg_processing_time_ms': avg_processing_time,
                'within_target_rate': (within_target_count / len(test_results)) * 100,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Image context extraction test failed: {e}", 'error')
            self.logger.error("Image context extraction test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_video_context_extraction(self) -> Dict[str, Any]:
        """Test video context extraction from YouTube links"""
        self.print_status("Testing video context extraction...", 'test')
        
        try:
            test_results = []
            
            for video_data in self.test_videos:
                self.print_status(f"Processing video: {video_data['title']}", 'context')
                
                start_time = time.time()
                
                try:
                    # Extract video context
                    context_result = await self.context_service.extract_video_context(
                        video_url=video_data['url'],
                        video_title=video_data['title']
                    )
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if context_result:
                        # Generate embedding for context
                        embedding_result = await self.context_service.generate_context_embedding(
                            context_text=context_result
                        )
                        
                        test_result = {
                            'video_id': video_data['id'],
                            'title': video_data['title'],
                            'url': video_data['url'],
                            'context_extracted': context_result is not None,
                            'context_length': len(context_result) if context_result else 0,
                            'embedding_generated': embedding_result is not None,
                            'embedding_length': len(embedding_result) if embedding_result else 0,
                            'processing_time_ms': processing_time,
                            'within_target': processing_time <= self.performance_targets['video_context_ms']
                        }
                        
                        test_results.append(test_result)
                        
                        status = "✅" if test_result['context_extracted'] and test_result['embedding_generated'] else "❌"
                        self.print_status(f"  {status} Context: {test_result['context_length']} chars, Embedding: {test_result['embedding_length']} dims", 'success' if test_result['context_extracted'] else 'error')
                        self.print_status(f"  ⏱️ Processing time: {processing_time:.2f}ms", 'info')
                    else:
                        test_results.append({
                            'video_id': video_data['id'],
                            'title': video_data['title'],
                            'url': video_data['url'],
                            'context_extracted': False,
                            'context_length': 0,
                            'embedding_generated': False,
                            'embedding_length': 0,
                            'processing_time_ms': processing_time,
                            'within_target': False,
                            'error': 'Video context extraction returned None'
                        })
                        self.print_status(f"  ❌ Video context extraction failed", 'error')
                
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    test_results.append({
                        'video_id': video_data['id'],
                        'title': video_data['title'],
                        'url': video_data['url'],
                        'context_extracted': False,
                        'context_length': 0,
                        'embedding_generated': False,
                        'embedding_length': 0,
                        'processing_time_ms': processing_time,
                        'within_target': False,
                        'error': str(e)
                    })
                    self.print_status(f"  ❌ Exception: {e}", 'error')
            
            # Calculate overall metrics
            successful_extractions = sum(1 for r in test_results if r['context_extracted'])
            successful_embeddings = sum(1 for r in test_results if r['embedding_generated'])
            avg_processing_time = sum(r['processing_time_ms'] for r in test_results) / len(test_results)
            within_target_count = sum(1 for r in test_results if r['within_target'])
            
            return {
                'success': successful_extractions > 0,
                'total_videos': len(test_results),
                'successful_extractions': successful_extractions,
                'successful_embeddings': successful_embeddings,
                'extraction_success_rate': (successful_extractions / len(test_results)) * 100,
                'embedding_success_rate': (successful_embeddings / len(test_results)) * 100,
                'avg_processing_time_ms': avg_processing_time,
                'within_target_rate': (within_target_count / len(test_results)) * 100,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Video context extraction test failed: {e}", 'error')
            self.logger.error("Video context extraction test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_link_context_extraction(self) -> Dict[str, Any]:
        """Test link context extraction"""
        self.print_status("Testing link context extraction...", 'test')
        
        try:
            test_results = []
            
            for link_data in self.test_links:
                self.print_status(f"Processing link: {link_data['title']}", 'context')
                
                start_time = time.time()
                
                try:
                    # Extract link context
                    context_result = await self.context_service.extract_link_context(
                        link_url=link_data['url'],
                        link_title=link_data['title']
                    )
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if context_result:
                        # Generate embedding for context
                        embedding_result = await self.context_service.generate_context_embedding(
                            context_text=context_result
                        )
                        
                        test_result = {
                            'link_id': link_data['id'],
                            'title': link_data['title'],
                            'url': link_data['url'],
                            'context_extracted': context_result is not None,
                            'context_length': len(context_result) if context_result else 0,
                            'embedding_generated': embedding_result is not None,
                            'embedding_length': len(embedding_result) if embedding_result else 0,
                            'processing_time_ms': processing_time,
                            'within_target': processing_time <= self.performance_targets['link_context_ms']
                        }
                        
                        test_results.append(test_result)
                        
                        status = "✅" if test_result['context_extracted'] and test_result['embedding_generated'] else "❌"
                        self.print_status(f"  {status} Context: {test_result['context_length']} chars, Embedding: {test_result['embedding_length']} dims", 'success' if test_result['context_extracted'] else 'error')
                        self.print_status(f"  ⏱️ Processing time: {processing_time:.2f}ms", 'info')
                    else:
                        test_results.append({
                            'link_id': link_data['id'],
                            'title': link_data['title'],
                            'url': link_data['url'],
                            'context_extracted': False,
                            'context_length': 0,
                            'embedding_generated': False,
                            'embedding_length': 0,
                            'processing_time_ms': processing_time,
                            'within_target': False,
                            'error': 'Link context extraction returned None'
                        })
                        self.print_status(f"  ❌ Link context extraction failed", 'error')
                
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    test_results.append({
                        'link_id': link_data['id'],
                        'title': link_data['title'],
                        'url': link_data['url'],
                        'context_extracted': False,
                        'context_length': 0,
                        'embedding_generated': False,
                        'embedding_length': 0,
                        'processing_time_ms': processing_time,
                        'within_target': False,
                        'error': str(e)
                    })
                    self.print_status(f"  ❌ Exception: {e}", 'error')
            
            # Calculate overall metrics
            successful_extractions = sum(1 for r in test_results if r['context_extracted'])
            successful_embeddings = sum(1 for r in test_results if r['embedding_generated'])
            avg_processing_time = sum(r['processing_time_ms'] for r in test_results) / len(test_results)
            within_target_count = sum(1 for r in test_results if r['within_target'])
            
            return {
                'success': successful_extractions > 0,
                'total_links': len(test_results),
                'successful_extractions': successful_extractions,
                'successful_embeddings': successful_embeddings,
                'extraction_success_rate': (successful_extractions / len(test_results)) * 100,
                'embedding_success_rate': (successful_embeddings / len(test_results)) * 100,
                'avg_processing_time_ms': avg_processing_time,
                'within_target_rate': (within_target_count / len(test_results)) * 100,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Link context extraction test failed: {e}", 'error')
            self.logger.error("Link context extraction test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_table_context_extraction(self) -> Dict[str, Any]:
        """Test table context extraction"""
        self.print_status("Testing table context extraction...", 'test')
        
        try:
            test_results = []
            
            for table_data in self.test_tables:
                self.print_status(f"Processing table {table_data['id']}", 'context')
                
                start_time = time.time()
                
                try:
                    # Extract table context
                    context_result = await self.context_service.extract_table_context(
                        table_markdown=table_data['markdown']
                    )
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if context_result:
                        # Generate embedding for context
                        embedding_result = await self.context_service.generate_context_embedding(
                            context_text=context_result
                        )
                        
                        test_result = {
                            'table_id': table_data['id'],
                            'context_extracted': context_result is not None,
                            'context_length': len(context_result) if context_result else 0,
                            'embedding_generated': embedding_result is not None,
                            'embedding_length': len(embedding_result) if embedding_result else 0,
                            'processing_time_ms': processing_time,
                            'within_target': processing_time <= self.performance_targets['table_context_ms']
                        }
                        
                        test_results.append(test_result)
                        
                        status = "✅" if test_result['context_extracted'] and test_result['embedding_generated'] else "❌"
                        self.print_status(f"  {status} Context: {test_result['context_length']} chars, Embedding: {test_result['embedding_length']} dims", 'success' if test_result['context_extracted'] else 'error')
                        self.print_status(f"  ⏱️ Processing time: {processing_time:.2f}ms", 'info')
                    else:
                        test_results.append({
                            'table_id': table_data['id'],
                            'context_extracted': False,
                            'context_length': 0,
                            'embedding_generated': False,
                            'embedding_length': 0,
                            'processing_time_ms': processing_time,
                            'within_target': False,
                            'error': 'Table context extraction returned None'
                        })
                        self.print_status(f"  ❌ Table context extraction failed", 'error')
                
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    test_results.append({
                        'table_id': table_data['id'],
                        'context_extracted': False,
                        'context_length': 0,
                        'embedding_generated': False,
                        'embedding_length': 0,
                        'processing_time_ms': processing_time,
                        'within_target': False,
                        'error': str(e)
                    })
                    self.print_status(f"  ❌ Exception: {e}", 'error')
            
            # Calculate overall metrics
            successful_extractions = sum(1 for r in test_results if r['context_extracted'])
            successful_embeddings = sum(1 for r in test_results if r['embedding_generated'])
            avg_processing_time = sum(r['processing_time_ms'] for r in test_results) / len(test_results)
            within_target_count = sum(1 for r in test_results if r['within_target'])
            
            return {
                'success': successful_extractions > 0,
                'total_tables': len(test_results),
                'successful_extractions': successful_extractions,
                'successful_embeddings': successful_embeddings,
                'extraction_success_rate': (successful_extractions / len(test_results)) * 100,
                'embedding_success_rate': (successful_embeddings / len(test_results)) * 100,
                'avg_processing_time_ms': avg_processing_time,
                'within_target_rate': (within_target_count / len(test_results)) * 100,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Table context extraction test failed: {e}", 'error')
            self.logger.error("Table context extraction test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_database_integration(self) -> Dict[str, Any]:
        """Test database integration for context storage and retrieval"""
        self.print_status("Testing database integration...", 'test')
        
        try:
            # Create a test document
            document_id = str(uuid.uuid4())
            
            # Store test context data
            test_contexts = [
                {
                    'document_id': document_id,
                    'media_type': 'image',
                    'media_id': str(uuid.uuid4()),
                    'context_text': 'Test image context for database integration',
                    'context_embedding': [0.1] * 768
                },
                {
                    'document_id': document_id,
                    'media_type': 'video',
                    'media_id': str(uuid.uuid4()),
                    'context_text': 'Test video context for database integration',
                    'context_embedding': [0.2] * 768
                },
                {
                    'document_id': document_id,
                    'media_type': 'link',
                    'media_id': str(uuid.uuid4()),
                    'context_text': 'Test link context for database integration',
                    'context_embedding': [0.3] * 768
                },
                {
                    'document_id': document_id,
                    'media_type': 'table',
                    'media_id': str(uuid.uuid4()),
                    'context_text': 'Test table context for database integration',
                    'context_embedding': [0.4] * 768
                }
            ]
            
            stored_contexts = 0
            
            for context_data in test_contexts:
                try:
                    # Store context in database
                    if context_data['media_type'] == 'image':
                        await self.database_service.store_image_context(
                            image_id=context_data['media_id'],
                            document_id=document_id,
                            context_caption=context_data['context_text'],
                            context_embedding=context_data['context_embedding']
                        )
                    elif context_data['media_type'] == 'video':
                        await self.database_service.store_video_context(
                            video_id=context_data['media_id'],
                            document_id=document_id,
                            context_description=context_data['context_text'],
                            context_embedding=context_data['context_embedding']
                        )
                    elif context_data['media_type'] == 'link':
                        await self.database_service.store_link_context(
                            link_id=context_data['media_id'],
                            document_id=document_id,
                            context_description=context_data['context_text'],
                            context_embedding=context_data['context_embedding']
                        )
                    elif context_data['media_type'] == 'table':
                        await self.database_service.store_table_context(
                            table_id=context_data['media_id'],
                            document_id=document_id,
                            context_text=context_data['context_text'],
                            context_embedding=context_data['context_embedding']
                        )
                    
                    stored_contexts += 1
                    self.print_status(f"  ✅ Stored {context_data['media_type']} context", 'success')
                
                except Exception as e:
                    self.print_status(f"  ❌ Failed to store {context_data['media_type']} context: {e}", 'error')
            
            # Retrieve and verify stored contexts
            retrieved_contexts = 0
            
            try:
                # Retrieve image contexts
                image_contexts = await self.database_service.get_image_contexts_by_document(document_id)
                retrieved_contexts += len(image_contexts) if image_contexts else 0
                
                # Retrieve video contexts
                video_contexts = await self.database_service.get_video_contexts_by_document(document_id)
                retrieved_contexts += len(video_contexts) if video_contexts else 0
                
                # Retrieve link contexts
                link_contexts = await self.database_service.get_link_contexts_by_document(document_id)
                retrieved_contexts += len(link_contexts) if link_contexts else 0
                
                # Retrieve table contexts
                table_contexts = await self.database_service.get_table_contexts_by_document(document_id)
                retrieved_contexts += len(table_contexts) if table_contexts else 0
                
                self.print_status(f"  📊 Retrieved {retrieved_contexts} contexts", 'info')
            
            except Exception as e:
                self.print_status(f"  ❌ Failed to retrieve contexts: {e}", 'error')
            
            # Cleanup test data
            try:
                await self.database_service.delete_document(document_id)
                self.print_status("  🧹 Cleaned up test document", 'info')
            except Exception as e:
                self.print_status(f"  ⚠️ Cleanup failed: {e}", 'warning')
            
            result = {
                'success': stored_contexts == len(test_contexts) and retrieved_contexts == stored_contexts,
                'total_contexts': len(test_contexts),
                'stored_contexts': stored_contexts,
                'retrieved_contexts': retrieved_contexts,
                'storage_success_rate': (stored_contexts / len(test_contexts)) * 100,
                'retrieval_success_rate': (retrieved_contexts / stored_contexts) * 100 if stored_contexts > 0 else 0
            }
            
            self.print_status(f"✅ Database integration test completed", 'success')
            self.print_status(f"  Storage: {stored_contexts}/{len(test_contexts)} contexts", 'info')
            self.print_status(f"  Retrieval: {retrieved_contexts}/{stored_contexts} contexts", 'info')
            
            return result
            
        except Exception as e:
            self.print_status(f"Database integration test failed: {e}", 'error')
            self.logger.error("Database integration test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def display_context_table(self, results: Dict[str, Any], media_type: str):
        """Display context extraction results"""
        if not self.console or not results.get('test_results'):
            return
        
        table = Table(title=f"{media_type.title()} Context Extraction Results", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Context", style="green")
        table.add_column("Embedding", style="yellow")
        table.add_column("Time", style="blue")
        table.add_column("Status", style="red")
        
        for result in results['test_results']:
            context_status = "✅" if result['context_extracted'] else "❌"
            embedding_status = "✅" if result['embedding_generated'] else "❌"
            
            status = "✅ Success" if result['context_extracted'] and result['embedding_generated'] else "❌ Failed"
            status_style = "green" if result['context_extracted'] and result['embedding_generated'] else "red"
            
            table.add_row(
                result.get('filename', result.get('title', result.get('link_id', result.get('table_id', 'Unknown')))),
                f"{result['context_length']} chars {context_status}",
                f"{result['embedding_length']} dims {embedding_status}",
                f"{result['processing_time_ms']:.2f}ms",
                status,
                style=status_style
            )
        
        self.console.print(table)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all context extraction integration tests"""
        self.print_status("Starting Context Extraction Integration Test Suite", 'test')
        
        if not await self.setup():
            return {'success': False, 'error': 'Setup failed'}
        
        # Run tests
        test_results = {}
        
        # Test 1: Image context extraction
        self.print_status("Running image context extraction test...", 'test')
        test_results['image_context'] = await self.test_image_context_extraction()
        
        # Test 2: Video context extraction
        self.print_status("Running video context extraction test...", 'test')
        test_results['video_context'] = await self.test_video_context_extraction()
        
        # Test 3: Link context extraction
        self.print_status("Running link context extraction test...", 'test')
        test_results['link_context'] = await self.test_link_context_extraction()
        
        # Test 4: Table context extraction
        self.print_status("Running table context extraction test...", 'test')
        test_results['table_context'] = await self.test_table_context_extraction()
        
        # Test 5: Database integration
        self.print_status("Running database integration test...", 'test')
        test_results['database_integration'] = await self.test_database_integration()
        
        # Generate report
        self.generate_test_report(test_results)
        
        # Cleanup
        # Database service cleanup (disconnect not available)
        # await self.database_service.disconnect()
        # await self.ai_service.disconnect()
        
        return {
            'success': True,
            'test_results': test_results
        }
    
    def generate_test_report(self, test_results: Dict[str, Any]):
        """Generate comprehensive test report"""
        if not self.console:
            self.print_plain_report(test_results)
            return
        
        # Summary panel
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get('success', False))
        
        summary_text = f"""
Total Tests: {total_tests}
✅ Passed: {passed_tests}
❌ Failed: {total_tests - passed_tests}
📊 Success Rate: {(passed_tests/total_tests*100):.1f}%
        """.strip()
        
        self.console.print(Panel(summary_text, title="📝 Context Extraction Integration Test Results", border_style="yellow"))
        
        # Image Context Results
        if 'image_context' in test_results:
            result = test_results['image_context']
            if result['success']:
                self.console.print("\n🖼️ Image Context Extraction", style="cyan bold")
                
                image_table = Table(title="Image Context Summary", box=box.ROUNDED)
                image_table.add_column("Metric", style="white")
                image_table.add_column("Value", style="green")
                
                image_table.add_row("Total Images", str(result['total_images']))
                image_table.add_row("Extraction Success Rate", f"{result['extraction_success_rate']:.1f}%")
                image_table.add_row("Embedding Success Rate", f"{result['embedding_success_rate']:.1f}%")
                image_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                image_table.add_row("Within Target Rate", f"{result['within_target_rate']:.1f}%")
                
                self.console.print(image_table)
                self.display_context_table(result, 'image')
        
        # Video Context Results
        if 'video_context' in test_results:
            result = test_results['video_context']
            if result['success']:
                self.console.print("\n🎥 Video Context Extraction", style="cyan bold")
                
                video_table = Table(title="Video Context Summary", box=box.ROUNDED)
                video_table.add_column("Metric", style="white")
                video_table.add_column("Value", style="green")
                
                video_table.add_row("Total Videos", str(result['total_videos']))
                video_table.add_row("Extraction Success Rate", f"{result['extraction_success_rate']:.1f}%")
                video_table.add_row("Embedding Success Rate", f"{result['embedding_success_rate']:.1f}%")
                video_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                video_table.add_row("Within Target Rate", f"{result['within_target_rate']:.1f}%")
                
                self.console.print(video_table)
                self.display_context_table(result, 'video')
        
        # Link Context Results
        if 'link_context' in test_results:
            result = test_results['link_context']
            if result['success']:
                self.console.print("\n🔗 Link Context Extraction", style="cyan bold")
                
                link_table = Table(title="Link Context Summary", box=box.ROUNDED)
                link_table.add_column("Metric", style="white")
                link_table.add_column("Value", style="green")
                
                link_table.add_row("Total Links", str(result['total_links']))
                link_table.add_row("Extraction Success Rate", f"{result['extraction_success_rate']:.1f}%")
                link_table.add_row("Embedding Success Rate", f"{result['embedding_success_rate']:.1f}%")
                link_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                link_table.add_row("Within Target Rate", f"{result['within_target_rate']:.1f}%")
                
                self.console.print(link_table)
                self.display_context_table(result, 'link')
        
        # Table Context Results
        if 'table_context' in test_results:
            result = test_results['table_context']
            if result['success']:
                self.console.print("\n📊 Table Context Extraction", style="cyan bold")
                
                table_table = Table(title="Table Context Summary", box=box.ROUNDED)
                table_table.add_column("Metric", style="white")
                table_table.add_column("Value", style="green")
                
                table_table.add_row("Total Tables", str(result['total_tables']))
                table_table.add_row("Extraction Success Rate", f"{result['extraction_success_rate']:.1f}%")
                table_table.add_row("Embedding Success Rate", f"{result['embedding_success_rate']:.1f}%")
                table_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                table_table.add_row("Within Target Rate", f"{result['within_target_rate']:.1f}%")
                
                self.console.print(table_table)
                self.display_context_table(result, 'table')
        
        # Database Integration Results
        if 'database_integration' in test_results:
            result = test_results['database_integration']
            if result['success']:
                self.console.print("\n🗄️ Database Integration", style="cyan bold")
                
                db_table = Table(title="Database Integration Summary", box=box.ROUNDED)
                db_table.add_column("Metric", style="white")
                db_table.add_column("Value", style="green")
                
                db_table.add_row("Total Contexts", str(result['total_contexts']))
                db_table.add_row("Stored Successfully", str(result['stored_contexts']))
                db_table.add_row("Retrieved Successfully", str(result['retrieved_contexts']))
                db_table.add_row("Storage Success Rate", f"{result['storage_success_rate']:.1f}%")
                db_table.add_row("Retrieval Success Rate", f"{result['retrieval_success_rate']:.1f}%")
                
                self.console.print(db_table)
        
        # Errors and warnings
        has_errors = any(not result.get('success', False) for result in test_results.values())
        if has_errors:
            errors_panel = []
            for test_name, result in test_results.items():
                if not result.get('success', False):
                    errors_panel.append(f"\n{test_name}:")
                    errors_panel.append(f"  ❌ {result.get('error', 'Unknown error')}")
            
            if errors_panel:
                self.console.print(Panel("".join(errors_panel), title="❌ Errors", border_style="red"))
    
    def print_plain_report(self, test_results: Dict[str, Any]):
        """Print report in plain text format"""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get('success', False))
        
        print(f"\n📝 Context Extraction Integration Test Results")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        for test_name, result in test_results.items():
            status = "PASS" if result.get('success', False) else "FAIL"
            print(f"{test_name}: {status}")
            
            if result.get('success', False):
                if 'extraction_success_rate' in result:
                    print(f"  Extraction success rate: {result['extraction_success_rate']:.1f}%")
                if 'embedding_success_rate' in result:
                    print(f"  Embedding success rate: {result['embedding_success_rate']:.1f}%")
                if 'avg_processing_time_ms' in result:
                    print(f"  Avg processing time: {result['avg_processing_time_ms']:.2f}ms")
                if 'storage_success_rate' in result:
                    print(f"  Storage success rate: {result['storage_success_rate']:.1f}%")
            else:
                print(f"  ❌ {result.get('error', 'Unknown error')}")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='KRAI Context Extraction Integration Test')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--media-type', type=str, choices=['image', 'video', 'link', 'table'], help='Test specific media type only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    
    args = parser.parse_args()
    
    tester = ContextExtractionIntegrationTester(verbose=args.verbose)
    
    if args.media_type:
        # Run specific media type test
        await tester.setup()
        
        if args.media_type == 'image':
            result = await tester.test_image_context_extraction()
            tester.generate_test_report({'image_context': result})
        elif args.media_type == 'video':
            result = await tester.test_video_context_extraction()
            tester.generate_test_report({'video_context': result})
        elif args.media_type == 'link':
            result = await tester.test_link_context_extraction()
            tester.generate_test_report({'link_context': result})
        elif args.media_type == 'table':
            result = await tester.test_table_context_extraction()
            tester.generate_test_report({'table_context': result})
        
        # Database service cleanup (disconnect not available)
        # await tester.database_service.disconnect()
        # await tester.ai_service.disconnect()
    else:
        # Run all tests
        results = await tester.run_all_tests()
        
        if results['success']:
            total_tests = len(results['test_results'])
            passed_tests = sum(1 for result in results['test_results'].values() if result.get('success', False))
            success_rate = passed_tests / total_tests * 100
            
            print(f"\n🎉 Context extraction integration test completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            sys.exit(0 if passed_tests == total_tests else 1)
        else:
            print(f"❌ Context extraction integration test failed: {results.get('error', 'Unknown error')}")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
