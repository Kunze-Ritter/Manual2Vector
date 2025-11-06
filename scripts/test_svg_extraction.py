#!/usr/bin/env python3
"""
KRAI SVG Extraction Test
========================

Focused test for SVG vector graphics processing from PDFs.
This script validates the SVGProcessor's ability to extract vector graphics,
convert them to PNG, and prepare them for Vision AI analysis.

Features Tested:
- SVG extraction from PDF pages using PyMuPDF
- SVG to PNG conversion quality and performance
- Vision AI integration with converted PNGs
- Storage queue integration for processed images
- Error handling for malformed SVG content
- Large SVG file handling and optimization

Usage:
    python scripts/test_svg_extraction.py
    python scripts/test_svg_extraction.py --verbose
    python scripts/test_svg_extraction.py --document <filename>
    python scripts/test_svg_extraction.py --quality-check
"""

import os
import sys
import asyncio
import argparse
import json
import time
import uuid
import logging
import base64
import io
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
from backend.services.object_storage_service import ObjectStorageService
from backend.services.storage_factory import create_storage_service
from backend.services.ai_service import AIService
from backend.processors.svg_processor import SVGProcessor
from backend.core.base_processor import ProcessingContext

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    SVG_PROCESSING_AVAILABLE = True
except ImportError:
    SVG_PROCESSING_AVAILABLE = False

@dataclass
class SVGTestResult:
    """Test result for SVG processing"""
    svgs_extracted: int
    svgs_converted: int
    png_conversions_successful: int
    vision_ai_analyses: int
    images_queued: int
    conversion_quality_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    sample_files: Dict[str, str]  # Paths to sample files for inspection

class SVGExtractionTester:
    """Test runner for SVG extraction functionality"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.svg_extraction_test")
        
        # Test configuration
        self.test_documents = []
        self.output_dir = Path("test_output/svg_extraction")
        self.results: SVGTestResult = None
        
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
                'svg': 'purple'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪',
                'svg': '🎨'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            self.print_status("Setting up SVG Extraction Tester", 'test')
            
            # Check dependencies
            if not PYMUPDF_AVAILABLE:
                self.print_status("PyMuPDF not available - install with: pip install PyMuPDF", 'error')
                return False
            
            if not SVG_PROCESSING_AVAILABLE:
                self.print_status("SVG processing libraries not available - install with: pip install Pillow svglib reportlab", 'error')
                return False
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Find test documents
            await self._find_test_documents()
            
            if not self.test_documents:
                self.print_status("No test documents found", 'warning')
                # Create synthetic test document
                await self._create_synthetic_test_document()
            
            self.print_status(f"Setup completed with {len(self.test_documents)} test documents", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def _find_test_documents(self):
        """Find test PDF documents in service_documents directory"""
        service_docs_dir = Path("service_documents")
        
        if not service_docs_dir.exists():
            return
        
        # Find PDF files
        pdf_files = list(service_docs_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            self.test_documents.append({
                'filename': pdf_file.name,
                'file_path': str(pdf_file),
                'file_size': pdf_file.stat().st_size
            })
    
    async def _create_synthetic_test_document(self):
        """Create a synthetic PDF with SVG content for testing"""
        try:
            # This would require creating a PDF with vector graphics
            # For now, we'll just note that no test documents are available
            self.print_status("Synthetic test document creation not implemented", 'warning')
        except Exception as e:
            self.print_status(f"Failed to create synthetic test document: {e}", 'error')
    
    def _create_test_svg_content(self) -> str:
        """Create test SVG content for conversion testing"""
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="50" width="100" height="100" fill="blue" stroke="black" stroke-width="2"/>
  <circle cx="100" cy="100" r="30" fill="red" stroke="black" stroke-width="2"/>
  <text x="100" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="black">Test SVG</text>
</svg>'''
        return test_svg
    
    async def test_svg_extraction(self) -> Dict[str, Any]:
        """Test SVG extraction from PDF documents"""
        self.print_status("Testing SVG extraction from PDFs...", 'test')
        
        try:
            # Initialize services
            database_service = DatabaseService(
                supabase_url=None,
                supabase_key=None,
                postgres_url=os.getenv('DATABASE_URL'),
                database_type='postgresql'
            )
            await database_service.connect()
            
            storage_service = create_storage_service()
            await storage_service.connect()
            
            ai_service = AIService()
            await ai_service.connect()
            
            # Initialize SVG processor
            svg_processor = SVGProcessor(
                database_service=database_service,
                storage_service=storage_service,
                ai_service=ai_service,
                dpi=300,
                max_dimension=2048
            )
            
            results = []
            
            for test_doc in self.test_documents[:2]:  # Test first 2 documents
                self.print_status(f"Processing document: {test_doc['filename']}", 'info')
                
                # Create processing context
                context = ProcessingContext(
                    file_path=test_doc['file_path'],
                    document_id=str(uuid.uuid4()),
                    file_hash="test-hash",
                    document_type="service_manual",
                    processing_config={'filename': test_doc['filename']},
                    file_size=test_doc['file_size'],
                    pdf_path=test_doc['file_path']  # SVG processor needs pdf_path
                )
                
                # Process SVG extraction
                start_time = time.time()
                svg_result = await svg_processor.process(context)
                processing_time = time.time() - start_time
                
                if svg_result.success:
                    result_data = {
                        'filename': test_doc['filename'],
                        'success': True,
                        'processing_time': processing_time,
                        'svgs_extracted': svg_result.data.get('svgs_extracted', 0),
                        'svgs_converted': svg_result.data.get('svgs_converted', 0),
                        'images_queued': svg_result.data.get('images_queued', 0),
                        'errors': [],
                        'warnings': []
                    }
                    
                    # Query database for vector graphics
                    if hasattr(database_service, 'pg_pool') and database_service.pg_pool:
                        async with database_service.pg_pool.acquire() as conn:
                            vector_count = await conn.fetchval(
                                "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1 AND image_type = 'vector_graphic'",
                                context.document_id
                            )
                            result_data['vector_graphics_stored'] = vector_count
                    
                    results.append(result_data)
                    self.print_status(f"SVG extraction completed: {result_data['svgs_extracted']} SVGs", 'success')
                else:
                    results.append({
                        'filename': test_doc['filename'],
                        'success': False,
                        'error': svg_result.message,
                        'processing_time': processing_time
                    })
                    self.print_status(f"SVG extraction failed: {svg_result.message}", 'error')
                
                # Cleanup test document
                try:
                    await database_service.delete_document(context.document_id)
                except:
                    pass
            
            # Close services
            # Database service cleanup (disconnect not available)
            # await database_service.disconnect()
            # await storage_service.disconnect()
            # await ai_service.disconnect()
            
            return {
                'success': True,
                'documents_processed': len(results),
                'results': results
            }
            
        except Exception as e:
            self.print_status(f"SVG extraction test failed: {e}", 'error')
            self.logger.error("SVG extraction test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_svg_to_png_conversion(self) -> Dict[str, Any]:
        """Test SVG to PNG conversion quality and performance"""
        self.print_status("Testing SVG to PNG conversion...", 'test')
        
        try:
            # Initialize AI service for conversion
            ai_service = AIService()
            await ai_service.connect()
            
            # Test conversions with different SVG content
            test_svgs = [
                self._create_test_svg_content(),
                '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
    </linearGradient>
  </defs>
  <ellipse cx="200" cy="150" rx="150" ry="100" fill="url(#grad1)" />
  <text x="200" y="250" text-anchor="middle" font-family="Arial" font-size="16" fill="black">Gradient Test</text>
</svg>''',
                '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
  <path d="M10,10 L50,90 L90,10 L130,90 L170,10 L210,90 L250,10" 
        stroke="blue" stroke-width="3" fill="none"/>
  <text x="130" y="180" text-anchor="middle" font-family="Arial" font-size="14" fill="black">Path Test</text>
</svg>'''
            ]
            
            conversion_results = []
            
            for i, svg_content in enumerate(test_svgs):
                self.print_status(f"Converting SVG {i+1}/3...", 'info')
                
                try:
                    # Test conversion with different settings
                    for dpi in [150, 300, 600]:
                        start_time = time.time()
                        
                        png_bytes = ai_service.convert_svg_to_png(
                            svg_content=svg_content,
                            dpi=dpi,
                            max_dimension=2048
                        )
                        
                        conversion_time = time.time() - start_time
                        
                        if png_bytes:
                            # Analyze PNG quality
                            png_image = Image.open(io.BytesIO(png_bytes))
                            
                            # Save sample for inspection
                            sample_path = self.output_dir / f"test_svg_{i+1}_dpi_{dpi}.png"
                            png_image.save(sample_path)
                            
                            conversion_results.append({
                                'svg_index': i,
                                'dpi': dpi,
                                'success': True,
                                'conversion_time': conversion_time,
                                'png_size': len(png_bytes),
                                'width': png_image.width,
                                'height': png_image.height,
                                'sample_path': str(sample_path)
                            })
                            
                            self.print_status(f"  DPI {dpi}: {png_image.width}x{png_image.height}, {len(png_bytes)} bytes", 'success')
                        else:
                            conversion_results.append({
                                'svg_index': i,
                                'dpi': dpi,
                                'success': False,
                                'error': 'Conversion returned None'
                            })
                            self.print_status(f"  DPI {dpi}: Conversion failed", 'error')
                
                except Exception as e:
                    conversion_results.append({
                        'svg_index': i,
                        'success': False,
                        'error': str(e)
                    })
                    self.print_status(f"  SVG {i+1}: {e}", 'error')
            
            # Calculate performance metrics
            successful_conversions = [r for r in conversion_results if r.get('success', False)]
            avg_conversion_time = sum(r['conversion_time'] for r in successful_conversions) / len(successful_conversions) if successful_conversions else 0
            avg_png_size = sum(r['png_size'] for r in successful_conversions) / len(successful_conversions) if successful_conversions else 0
            
            await ai_service.disconnect()
            
            return {
                'success': True,
                'total_conversions': len(conversion_results),
                'successful_conversions': len(successful_conversions),
                'avg_conversion_time': avg_conversion_time,
                'avg_png_size': avg_png_size,
                'conversion_results': conversion_results
            }
            
        except Exception as e:
            self.print_status(f"SVG to PNG conversion test failed: {e}", 'error')
            self.logger.error("SVG to PNG conversion test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_vision_ai_integration(self) -> Dict[str, Any]:
        """Test Vision AI analysis of converted SVGs"""
        self.print_status("Testing Vision AI integration with converted SVGs...", 'test')
        
        try:
            # Initialize AI service
            ai_service = AIService()
            await ai_service.connect()
            
            # Create test SVG with recognizable content
            test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="50" width="200" height="100" fill="lightblue" stroke="black" stroke-width="2"/>
  <circle cx="150" cy="100" r="30" fill="orange" stroke="black" stroke-width="2"/>
  <text x="150" y="180" text-anchor="middle" font-family="Arial" font-size="14" fill="black">Technical Diagram</text>
</svg>'''
            
            # Convert SVG to PNG
            png_bytes = ai_service.convert_svg_to_png(test_svg, dpi=300, max_dimension=2048)
            
            if not png_bytes:
                return {'success': False, 'error': 'SVG to PNG conversion failed'}
            
            # Save sample for inspection
            sample_path = self.output_dir / "vision_ai_test.png"
            png_image = Image.open(io.BytesIO(png_bytes))
            png_image.save(sample_path)
            
            # Analyze with Vision AI
            vision_prompt = "Describe this technical diagram. What shapes and text do you see?"
            
            start_time = time.time()
            vision_result = await ai_service.analyze_image_base64(
                base64.b64encode(png_bytes).decode(),
                prompt=vision_prompt
            )
            analysis_time = time.time() - start_time
            
            if vision_result:
                self.print_status("Vision AI analysis completed", 'success')
                self.print_status(f"Analysis: {vision_result[:100]}...", 'info')
                
                return {
                    'success': True,
                    'analysis_time': analysis_time,
                    'vision_result': vision_result,
                    'sample_path': str(sample_path),
                    'png_size': len(png_bytes),
                    'image_dimensions': (png_image.width, png_image.height)
                }
            else:
                return {'success': False, 'error': 'Vision AI analysis returned no result'}
            
        except Exception as e:
            self.print_status(f"Vision AI integration test failed: {e}", 'error')
            self.logger.error("Vision AI integration test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling for malformed SVG content"""
        self.print_status("Testing error handling for malformed SVG content...", 'test')
        
        try:
            # Initialize AI service
            ai_service = AIService()
            await ai_service.connect()
            
            # Test cases with malformed SVG content
            test_cases = [
                {
                    'name': 'Malformed XML',
                    'content': '<svg><rect x="10" y="10" width="100" height="100"</svg>',  # Missing closing tag
                    'should_fail': True
                },
                {
                    'name': 'Empty SVG',
                    'content': '',
                    'should_fail': True
                },
                {
                    'name': 'Very Large SVG',
                    'content': '<svg width="10000" height="10000" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="10000" height="10000" fill="red"/></svg>',
                    'should_fail': False  # Should succeed but be scaled down
                },
                {
                    'name': 'SVG with External Reference',
                    'content': '<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><image href="http://example.com/image.jpg" x="0" y="0" width="100" height="100"/></svg>',
                    'should_fail': False  # Should handle gracefully
                }
            ]
            
            error_handling_results = []
            
            for test_case in test_cases:
                self.print_status(f"Testing: {test_case['name']}", 'info')
                
                try:
                    start_time = time.time()
                    png_bytes = ai_service.convert_svg_to_png(
                        svg_content=test_case['content'],
                        dpi=300,
                        max_dimension=2048
                    )
                    conversion_time = time.time() - start_time
                    
                    if test_case['should_fail']:
                        if png_bytes is None:
                            error_handling_results.append({
                                'name': test_case['name'],
                                'success': True,  # Expected failure
                                'result': 'correctly_failed',
                                'conversion_time': conversion_time
                            })
                            self.print_status(f"  Correctly failed as expected", 'success')
                        else:
                            error_handling_results.append({
                                'name': test_case['name'],
                                'success': False,  # Unexpected success
                                'result': 'unexpectedly_succeeded',
                                'conversion_time': conversion_time,
                                'png_size': len(png_bytes)
                            })
                            self.print_status(f"  Unexpectedly succeeded", 'warning')
                    else:
                        if png_bytes is not None:
                            error_handling_results.append({
                                'name': test_case['name'],
                                'success': True,
                                'result': 'succeeded',
                                'conversion_time': conversion_time,
                                'png_size': len(png_bytes)
                            })
                            self.print_status(f"  Succeeded as expected", 'success')
                        else:
                            error_handling_results.append({
                                'name': test_case['name'],
                                'success': False,
                                'result': 'unexpectedly_failed',
                                'conversion_time': conversion_time
                            })
                            self.print_status(f"  Unexpectedly failed", 'error')
                
                except Exception as e:
                    error_handling_results.append({
                        'name': test_case['name'],
                        'success': False,
                        'result': 'exception',
                        'error': str(e)
                    })
                    self.print_status(f"  Exception: {e}", 'error')
            
            await ai_service.disconnect()
            
            # Calculate error handling score
            correctly_handled = sum(1 for r in error_handling_results if r['success'])
            error_handling_score = (correctly_handled / len(test_cases)) * 100
            
            return {
                'success': True,
                'total_tests': len(test_cases),
                'correctly_handled': correctly_handled,
                'error_handling_score': error_handling_score,
                'results': error_handling_results
            }
            
        except Exception as e:
            self.print_status(f"Error handling test failed: {e}", 'error')
            self.logger.error("Error handling test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def display_conversion_results(self, results: Dict[str, Any]):
        """Display conversion results in a formatted table"""
        if not self.console or not results.get('conversion_results'):
            return
        
        table = Table(title="SVG to PNG Conversion Results", box=box.ROUNDED)
        table.add_column("SVG", style="cyan")
        table.add_column("DPI", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Size", style="blue")
        table.add_column("Dimensions", style="magenta")
        table.add_column("Time", style="red")
        
        for result in results['conversion_results']:
            status = "✅ Success" if result.get('success', False) else "❌ Failed"
            size = f"{result.get('png_size', 0)} bytes" if result.get('success', False) else "N/A"
            dimensions = f"{result.get('width', 0)}x{result.get('height', 0)}" if result.get('success', False) else "N/A"
            time_taken = f"{result.get('conversion_time', 0):.3f}s"
            
            table.add_row(
                f"SVG {result.get('svg_index', 0) + 1}",
                str(result.get('dpi', 0)),
                status,
                size,
                dimensions,
                time_taken
            )
        
        self.console.print(table)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all SVG extraction tests"""
        self.print_status("Starting SVG Extraction Test Suite", 'test')
        
        if not await self.setup():
            return {'success': False, 'error': 'Setup failed'}
        
        # Run tests
        test_results = {}
        
        # Test 1: SVG extraction from PDFs
        self.print_status("Running SVG extraction test...", 'test')
        test_results['svg_extraction'] = await self.test_svg_extraction()
        
        # Test 2: SVG to PNG conversion
        self.print_status("Running SVG to PNG conversion test...", 'test')
        test_results['conversion'] = await self.test_svg_to_png_conversion()
        
        # Test 3: Vision AI integration
        self.print_status("Running Vision AI integration test...", 'test')
        test_results['vision_ai'] = await self.test_vision_ai_integration()
        
        # Test 4: Error handling
        self.print_status("Running error handling test...", 'test')
        test_results['error_handling'] = await self.test_error_handling()
        
        # Generate report
        self.generate_test_report(test_results)
        
        return {
            'success': True,
            'test_results': test_results,
            'output_directory': str(self.output_dir)
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
📁 Output: {self.output_dir}
        """.strip()
        
        self.console.print(Panel(summary_text, title="🎨 SVG Extraction Test Results", border_style="purple"))
        
        # SVG Extraction Results
        if 'svg_extraction' in test_results:
            result = test_results['svg_extraction']
            if result['success']:
                self.console.print("\n📄 SVG Extraction from PDFs", style="cyan bold")
                
                extraction_table = Table(title="Extraction Results", box=box.ROUNDED)
                extraction_table.add_column("Document", style="white")
                extraction_table.add_column("SVGs", style="green")
                extraction_table.add_column("Converted", style="yellow")
                extraction_table.add_column("Queued", style="blue")
                extraction_table.add_column("Time", style="red")
                
                for doc_result in result.get('results', []):
                    if doc_result['success']:
                        extraction_table.add_row(
                            doc_result['filename'],
                            str(doc_result['svgs_extracted']),
                            str(doc_result['svgs_converted']),
                            str(doc_result['images_queued']),
                            f"{doc_result['processing_time']:.2f}s"
                        )
                
                self.console.print(extraction_table)
        
        # Conversion Results
        if 'conversion' in test_results:
            result = test_results['conversion']
            if result['success']:
                self.console.print("\n🔄 SVG to PNG Conversion", style="cyan bold")
                
                conversion_table = Table(title="Conversion Performance", box=box.ROUNDED)
                conversion_table.add_column("Metric", style="white")
                conversion_table.add_column("Value", style="green")
                
                conversion_table.add_row("Total Conversions", str(result['total_conversions']))
                conversion_table.add_row("Successful", str(result['successful_conversions']))
                conversion_table.add_row("Success Rate", f"{(result['successful_conversions']/result['total_conversions']*100):.1f}%")
                conversion_table.add_row("Avg Conversion Time", f"{result['avg_conversion_time']:.3f}s")
                conversion_table.add_row("Avg PNG Size", f"{result['avg_png_size']:.0f} bytes")
                
                self.console.print(conversion_table)
                
                # Display detailed conversion results
                self.display_conversion_results(result)
        
        # Vision AI Results
        if 'vision_ai' in test_results:
            result = test_results['vision_ai']
            if result['success']:
                self.console.print("\n👁️ Vision AI Integration", style="cyan bold")
                
                vision_table = Table(title="Vision AI Results", box=box.ROUNDED)
                vision_table.add_column("Metric", style="white")
                vision_table.add_column("Value", style="green")
                
                vision_table.add_row("Analysis Time", f"{result['analysis_time']:.2f}s")
                vision_table.add_row("PNG Size", f"{result['png_size']} bytes")
                vision_table.add_row("Dimensions", f"{result['image_dimensions'][0]}x{result['image_dimensions'][1]}")
                vision_table.add_row("Sample File", result['sample_path'])
                
                self.console.print(vision_table)
                
                # Display vision analysis
                vision_panel = Panel(
                    result['vision_result'][:500] + "..." if len(result['vision_result']) > 500 else result['vision_result'],
                    title="🤖 Vision AI Analysis",
                    border_style="blue"
                )
                self.console.print(vision_panel)
        
        # Error Handling Results
        if 'error_handling' in test_results:
            result = test_results['error_handling']
            if result['success']:
                self.console.print("\n🛡️ Error Handling", style="cyan bold")
                
                error_table = Table(title="Error Handling Results", box=box.ROUNDED)
                error_table.add_column("Test Case", style="white")
                error_table.add_column("Result", style="green")
                error_table.add_column("Time", style="yellow")
                
                for test_result in result['results']:
                    status_color = "green" if test_result['success'] else "red"
                    error_table.add_row(
                        test_result['name'],
                        test_result['result'],
                        f"{test_result.get('conversion_time', 0):.3f}s",
                        style=status_color
                    )
                
                self.console.print(error_table)
                self.console.print(f"📊 Error Handling Score: {result['error_handling_score']:.1f}%")
        
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
        
        print(f"\n🎨 SVG Extraction Test Results")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"📁 Output: {self.output_dir}")
        print()
        
        for test_name, result in test_results.items():
            status = "PASS" if result.get('success', False) else "FAIL"
            print(f"{test_name}: {status}")
            
            if result.get('success', False):
                if 'svgs_extracted' in result:
                    print(f"  SVGs extracted from documents")
                if 'successful_conversions' in result:
                    print(f"  Conversions: {result['successful_conversions']}/{result['total_conversions']}")
                    print(f"  Avg time: {result['avg_conversion_time']:.3f}s")
                if 'analysis_time' in result:
                    print(f"  Vision AI analysis: {result['analysis_time']:.2f}s")
                if 'error_handling_score' in result:
                    print(f"  Error handling score: {result['error_handling_score']:.1f}%")
            else:
                print(f"  ❌ {result.get('error', 'Unknown error')}")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='KRAI SVG Extraction Test')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--document', type=str, help='Test specific document (filename)')
    parser.add_argument('--quality-check', action='store_true', help='Run quality checks only')
    
    args = parser.parse_args()
    
    tester = SVGExtractionTester(verbose=args.verbose)
    
    if args.quality_check:
        # Run only quality-related tests
        await tester.setup()
        conversion_result = await tester.test_svg_to_png_conversion()
        vision_result = await tester.test_vision_ai_integration()
        
        tester.generate_test_report({
            'conversion': conversion_result,
            'vision_ai': vision_result
        })
    else:
        # Run all tests
        results = await tester.run_all_tests()
        
        if results['success']:
            total_tests = len(results['test_results'])
            passed_tests = sum(1 for result in results['test_results'].values() if result.get('success', False))
            success_rate = passed_tests / total_tests * 100
            
            print(f"\n🎉 SVG extraction test completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            print(f"📁 Check output files in: {results.get('output_directory', 'test_output/svg_extraction')}")
            sys.exit(0 if passed_tests == total_tests else 1)
        else:
            print(f"❌ SVG extraction test failed: {results.get('error', 'Unknown error')}")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
