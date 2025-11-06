#!/usr/bin/env python3
"""
Phase 6 Integration Test Suite

Comprehensive integration tests for all Phase 6 features working together.
Tests the complete system with hierarchical chunking, SVG processing, 
multimodal search, and context extraction.

Author: KRAI Development Team
Date: 2025-12-08
Version: 1.0
"""

import asyncio
import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Using basic output.")
    Console = None

# Import backend services
try:
    from backend.services.database_service import DatabaseService
    from backend.services.ai_service import AIService
    from backend.services.storage_service import StorageService
    from backend.services.multimodal_search_service import MultimodalSearchService
    from backend.processors.svg_processor import SVGProcessor
    from backend.processors.chunker import SmartChunker
    from backend.config.ai_config import AIConfig
    from backend.config.database_config import DatabaseConfig
    from backend.config.storage_config import StorageConfig
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Backend services not available: {e}")
    SERVICES_AVAILABLE = False

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

class Phase6IntegrationTester:
    """Phase 6 Integration Test Suite"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.results: List[TestResult] = []
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="krai_phase6_test_"))
        self.services: Dict[str, Any] = {}
        self.start_time = time.time()
        
        # Test configuration
        self.config = {
            "test_document_count": 3,
            "test_queries": [
                "printer error code",
                "hierarchical document structure",
                "vector graphics processing",
                "multimodal search capabilities",
                "context extraction features"
            ],
            "performance_thresholds": {
                "svg_processing": 30.0,  # seconds
                "context_extraction": 60.0,
                "multimodal_search": 5.0,
                "hierarchical_chunking": 20.0
            }
        }
        
    def log(self, message: str, level: str = "info"):
        """Log message with rich formatting if available"""
        if self.console:
            if level == "error":
                self.console.print(f"[red]ERROR: {message}[/red]")
            elif level == "warning":
                self.console.print(f"[yellow]WARNING: {message}[/yellow]")
            elif level == "success":
                self.console.print(f"[green]SUCCESS: {message}[/green]")
            else:
                self.console.print(f"[blue]{message}[/blue]")
        else:
            print(f"{level.upper()}: {message}")
    
    def add_result(self, test_name: str, success: bool, duration: float, 
                   details: Dict[str, Any], error_message: Optional[str] = None):
        """Add test result to results list"""
        result = TestResult(
            test_name=test_name,
            success=success,
            duration=duration,
            details=details,
            error_message=error_message
        )
        self.results.append(result)
    
    async def setup_services(self) -> bool:
        """Initialize all required services"""
        self.log("Setting up services for Phase 6 integration tests...")
        
        try:
            # Initialize database service
            db_config = DatabaseConfig()
            self.services["database"] = DatabaseService(db_config)
            await self.services["database"].connect()
            
            # Initialize AI service
            ai_config = AIConfig()
            self.services["ai"] = AIService(ai_config)
            await self.services["ai"].initialize()
            
            # Initialize storage service
            storage_config = StorageConfig()
            self.services["storage"] = StorageService(storage_config)
            await self.services["storage"].initialize()
            
            # Initialize multimodal search service
            self.services["search"] = MultimodalSearchService(
                database_service=self.services["database"],
                ai_service=self.services["ai"]
            )
            
            # Initialize processors
            self.services["svg_processor"] = SVGProcessor(
                ai_service=self.services["ai"],
                storage_service=self.services["storage"]
            )
            
            self.services["chunker"] = SmartChunker(
                ai_service=self.services["ai"]
            )
            
            self.log("All services initialized successfully", "success")
            return True
            
        except Exception as e:
            self.log(f"Failed to initialize services: {e}", "error")
            return False
    
    async def test_hierarchical_chunking_integration(self) -> TestResult:
        """Test hierarchical chunking with database integration"""
        test_name = "Hierarchical Chunking Integration"
        start_time = time.time()
        
        try:
            self.log(f"Testing {test_name}...")
            
            # Create test document with hierarchical structure
            test_content = """
            # Document Title
            
            ## Chapter 1: Introduction
            This is the introduction section with some basic content.
            
            ### Section 1.1: Overview
            Detailed overview content here.
            
            ### Section 1.2: Background
            Background information and context.
            
            ## Chapter 2: Technical Details
            
            ### Section 2.1: Error Codes
            Error Code 001: General failure
            Error Code 002: Specific issue
            
            ### Section 2.2: Solutions
            Solution for Error Code 001
            Solution for Error Code 002
            
            ## Conclusion
            Final thoughts and summary.
            """
            
            # Process with hierarchical chunking
            chunks = await self.services["chunker"].chunk_document(
                content=test_content,
                document_id="test_hierarchical_doc",
                enable_hierarchical=True,
                detect_error_codes=True,
                link_chunks=True
            )
            
            # Verify hierarchical structure
            hierarchical_chunks = [c for c in chunks if c.get("section_hierarchy")]
            linked_chunks = [c for c in chunks if c.get("previous_chunk_id") or c.get("next_chunk_id")]
            error_code_chunks = [c for c in chunks if c.get("error_code")]
            
            # Store chunks in database
            stored_chunks = []
            for chunk in chunks:
                stored_chunk = await self.services["database"].store_chunk(chunk)
                stored_chunks.append(stored_chunk)
            
            duration = time.time() - start_time
            
            details = {
                "total_chunks": len(chunks),
                "hierarchical_chunks": len(hierarchical_chunks),
                "linked_chunks": len(linked_chunks),
                "error_code_chunks": len(error_code_chunks),
                "stored_chunks": len(stored_chunks),
                "performance_threshold": self.config["performance_thresholds"]["hierarchical_chunking"],
                "within_threshold": duration <= self.config["performance_thresholds"]["hierarchical_chunking"]
            }
            
            success = (
                len(chunks) > 0 and
                len(hierarchical_chunks) > 0 and
                len(stored_chunks) == len(chunks)
            )
            
            self.add_result(test_name, success, duration, details)
            
            if success:
                self.log(f"{test_name} completed successfully in {duration:.2f}s", "success")
            else:
                self.log(f"{test_name} failed", "error")
                
            return TestResult(test_name, success, duration, details)
            
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(test_name, False, duration, {}, str(e))
            self.log(f"{test_name} failed with exception: {e}", "error")
            return TestResult(test_name, False, duration, {}, str(e))
    
    async def test_svg_processing_integration(self) -> TestResult:
        """Test SVG processing with Vision AI integration"""
        test_name = "SVG Processing Integration"
        start_time = time.time()
        
        try:
            self.log(f"Testing {test_name}...")
            
            # Create test SVG content
            test_svg = """
            <svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
                <rect width="200" height="100" fill="blue" />
                <text x="100" y="50" text-anchor="middle" fill="white">Test SVG</text>
                <circle cx="50" cy="50" r="20" fill="red" />
            </svg>
            """
            
            # Process SVG with Vision AI
            svg_result = await self.services["svg_processor"].process_svg_content(
                svg_content=test_svg,
                document_id="test_svg_doc",
                page_number=1
            )
            
            # Verify SVG processing results
            png_converted = svg_result.get("png_converted", False)
            vision_analysis = svg_result.get("vision_analysis")
            png_url = svg_result.get("png_url")
            
            # Store SVG result in database
            if png_converted:
                stored_image = await self.services["database"].store_image(svg_result)
                svg_result["stored_image_id"] = stored_image.get("id")
            
            duration = time.time() - start_time
            
            details = {
                "svg_processed": True,
                "png_converted": png_converted,
                "vision_analysis_completed": vision_analysis is not None,
                "png_url_generated": png_url is not None,
                "stored_in_database": "stored_image_id" in svg_result,
                "performance_threshold": self.config["performance_thresholds"]["svg_processing"],
                "within_threshold": duration <= self.config["performance_thresholds"]["svg_processing"]
            }
            
            success = (
                png_converted and
                vision_analysis is not None and
                png_url is not None
            )
            
            self.add_result(test_name, success, duration, details)
            
            if success:
                self.log(f"{test_name} completed successfully in {duration:.2f}s", "success")
            else:
                self.log(f"{test_name} failed", "error")
                
            return TestResult(test_name, success, duration, details)
            
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(test_name, False, duration, {}, str(e))
            self.log(f"{test_name} failed with exception: {e}", "error")
            return TestResult(test_name, False, duration, {}, str(e))
    
    async def test_multimodal_search_integration(self) -> TestResult:
        """Test multimodal search across all content types"""
        test_name = "Multimodal Search Integration"
        start_time = time.time()
        
        try:
            self.log(f"Testing {test_name}...")
            
            search_results = {}
            
            # Test different query types
            for query in self.config["test_queries"][:3]:  # Test first 3 queries
                query_start = time.time()
                
                # Perform multimodal search
                result = await self.services["search"].search_multimodal(
                    query=query,
                    modalities=['text', 'image', 'video', 'table', 'link'],
                    threshold=0.5,
                    limit=10
                )
                
                query_duration = time.time() - query_start
                search_results[query] = {
                    "results": result,
                    "duration": query_duration,
                    "total_results": len(result.get("results", [])),
                    "modalities_found": list(set(
                        r.get("source_type") for r in result.get("results", [])
                    ))
                }
            
            # Verify search functionality
            total_searches = len(search_results)
            successful_searches = sum(1 for r in search_results.values() if r["total_results"] >= 0)
            
            duration = time.time() - start_time
            
            details = {
                "total_queries_tested": total_searches,
                "successful_searches": successful_searches,
                "average_duration": sum(r["duration"] for r in search_results.values()) / total_searches,
                "performance_threshold": self.config["performance_thresholds"]["multimodal_search"],
                "within_threshold": all(r["duration"] <= self.config["performance_thresholds"]["multimodal_search"] for r in search_results.values()),
                "search_results": search_results
            }
            
            success = successful_searches == total_searches
            
            self.add_result(test_name, success, duration, details)
            
            if success:
                self.log(f"{test_name} completed successfully in {duration:.2f}s", "success")
            else:
                self.log(f"{test_name} failed", "error")
                
            return TestResult(test_name, success, duration, details)
            
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(test_name, False, duration, {}, str(e))
            self.log(f"{test_name} failed with exception: {e}", "error")
            return TestResult(test_name, False, duration, {}, str(e))
    
    async def test_context_extraction_integration(self) -> TestResult:
        """Test context extraction for all media types"""
        test_name = "Context Extraction Integration"
        start_time = time.time()
        
        try:
            self.log(f"Testing {test_name}...")
            
            # Test context extraction for different media types
            test_media = {
                "image": {
                    "url": "test://image/sample.jpg",
                    "type": "diagram",
                    "description": "Technical diagram showing printer components"
                },
                "video": {
                    "url": "test://video/tutorial.mp4",
                    "title": "Printer Maintenance Tutorial",
                    "duration": 300
                },
                "table": {
                    "content": "Error Code | Description | Solution\n001 | Paper Jam | Open cover\n002 | Toner Low | Replace cartridge",
                    "headers": ["Error Code", "Description", "Solution"]
                },
                "link": {
                    "url": "https://example.com/printer-manual",
                    "title": "Printer Manual",
                    "type": "documentation"
                }
            }
            
            context_results = {}
            
            for media_type, media_data in test_media.items():
                media_start = time.time()
                
                # Extract context using AI service
                context = await self.services["ai"].extract_context(
                    media_type=media_type,
                    media_data=media_data,
                    max_length=1000
                )
                
                media_duration = time.time() - media_start
                
                # Generate embedding for context
                if context:
                    embedding = await self.services["ai"].generate_embeddings(context)
                else:
                    embedding = None
                
                context_results[media_type] = {
                    "context": context,
                    "embedding_generated": embedding is not None,
                    "duration": media_duration,
                    "context_length": len(context) if context else 0
                }
            
            # Store context results in database
            stored_contexts = []
            for media_type, result in context_results.items():
                if result["context"]:
                    context_data = {
                        "media_type": media_type,
                        "context": result["context"],
                        "embedding": result.get("embedding"),
                        "source_data": test_media[media_type]
                    }
                    stored = await self.services["database"].store_context(context_data)
                    stored_contexts.append(stored)
            
            duration = time.time() - start_time
            
            details = {
                "media_types_tested": len(test_media),
                "contexts_extracted": sum(1 for r in context_results.values() if r["context"]),
                "embeddings_generated": sum(1 for r in context_results.values() if r["embedding_generated"]),
                "contexts_stored": len(stored_contexts),
                "average_duration": sum(r["duration"] for r in context_results.values()) / len(test_media),
                "performance_threshold": self.config["performance_thresholds"]["context_extraction"],
                "within_threshold": duration <= self.config["performance_thresholds"]["context_extraction"],
                "context_results": context_results
            }
            
            success = (
                details["contexts_extracted"] > 0 and
                details["embeddings_generated"] > 0 and
                details["contexts_stored"] > 0
            )
            
            self.add_result(test_name, success, duration, details)
            
            if success:
                self.log(f"{test_name} completed successfully in {duration:.2f}s", "success")
            else:
                self.log(f"{test_name} failed", "error")
                
            return TestResult(test_name, success, duration, details)
            
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(test_name, False, duration, {}, str(e))
            self.log(f"{test_name} failed with exception: {e}", "error")
            return TestResult(test_name, False, duration, {}, str(e))
    
    async def test_end_to_end_pipeline(self) -> TestResult:
        """Test complete end-to-end pipeline with all Phase 6 features"""
        test_name = "End-to-End Pipeline Integration"
        start_time = time.time()
        
        try:
            self.log(f"Testing {test_name}...")
            
            # Create comprehensive test document
            test_document = {
                "content": """
                # Advanced Printer Manual
                
                ## Chapter 1: Device Overview
                
                ### Section 1.1: Product Specifications
                The HP LaserJet Pro M404n is a monochrome laser printer designed for small offices.
                
                ### Section 1.2: Technical Diagrams
                [SVG: Printer components diagram showing paper path, toner cartridge, fuser unit]
                
                ## Chapter 2: Error Handling
                
                ### Section 2.1: Common Error Codes
                Error Code 49.XXXX: Firmware error
                Error Code 50.XX: Fuser error
                Error Code 13.XX: Paper jam early
                
                ### Section 2.2: Troubleshooting Tables
                | Error Code | Description | Solution |
                |------------|-------------|----------|
                | 49.XXXX | Firmware error | Power cycle, update firmware |
                | 50.XX | Fuser error | Check fuser, replace if needed |
                | 13.XX | Paper jam | Clear paper path, check sensors |
                
                ## Chapter 3: Maintenance Procedures
                
                ### Section 3.1: Video Tutorials
                Link: https://example.com/toner-replacement-tutorial
                Title: How to Replace Toner Cartridge
                
                ### Section 3.2: Step-by-Step Guide
                1. Open printer cover
                2. Remove old toner cartridge
                3. Insert new cartridge
                4. Close cover and test
                """,
                "metadata": {
                    "title": "Advanced Printer Manual",
                    "manufacturer": "HP",
                    "model": "LaserJet Pro M404n",
                    "document_type": "technical_manual"
                }
            }
            
            # Step 1: Process with hierarchical chunking
            chunks = await self.services["chunker"].chunk_document(
                content=test_document["content"],
                document_id="test_e2e_doc",
                enable_hierarchical=True,
                detect_error_codes=True,
                link_chunks=True
            )
            
            # Step 2: Extract and process SVG content
            svg_content = """
            <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
                <rect width="400" height="300" fill="#f0f0f0" />
                <text x="200" y="30" text-anchor="middle" font-size="16">Printer Components</text>
                <rect x="50" y="60" width="80" height="120" fill="#333" />
                <text x="90" y="130" text-anchor="middle" fill="white">Toner</text>
                <rect x="200" y="100" width="100" height="60" fill="#666" />
                <text x="250" y="135" text-anchor="middle" fill="white">Fuser</text>
                <path d="M 130 120 L 200 120" stroke="blue" stroke-width="3" />
                <text x="165" y="110" text-anchor="middle" fill="blue">Paper Path</text>
            </svg>
            """
            
            svg_result = await self.services["svg_processor"].process_svg_content(
                svg_content=svg_content,
                document_id="test_e2e_doc",
                page_number=1
            )
            
            # Step 3: Extract context for all media types
            context_tasks = []
            
            # Context for SVG image
            if svg_result.get("png_url"):
                image_context = await self.services["ai"].extract_context(
                    media_type="image",
                    media_data={"url": svg_result["png_url"], "type": "technical_diagram"},
                    max_length=500
                )
                context_tasks.append(("image", image_context))
            
            # Context for table data
            table_data = test_document["content"].split("### Section 2.2: Troubleshooting Tables")[1].split("## Chapter 3")[0].strip()
            table_context = await self.services["ai"].extract_context(
                media_type="table",
                media_data={"content": table_data, "type": "troubleshooting_table"},
                max_length=500
            )
            context_tasks.append(("table", table_context))
            
            # Context for video link
            video_context = await self.services["ai"].extract_context(
                media_type="video",
                media_data={
                    "url": "https://example.com/toner-replacement-tutorial",
                    "title": "How to Replace Toner Cartridge",
                    "type": "tutorial"
                },
                max_length=300
            )
            context_tasks.append(("video", video_context))
            
            # Step 4: Store all processed data
            stored_data = {
                "chunks": [],
                "images": [],
                "contexts": []
            }
            
            # Store chunks
            for chunk in chunks:
                stored_chunk = await self.services["database"].store_chunk(chunk)
                stored_data["chunks"].append(stored_chunk)
            
            # Store SVG image
            if svg_result.get("png_converted"):
                stored_image = await self.services["database"].store_image(svg_result)
                stored_data["images"].append(stored_image)
            
            # Store contexts
            for media_type, context in context_tasks:
                if context:
                    embedding = await self.services["ai"].generate_embeddings(context)
                    context_data = {
                        "media_type": media_type,
                        "context": context,
                        "embedding": embedding,
                        "document_id": "test_e2e_doc"
                    }
                    stored_context = await self.services["database"].store_context(context_data)
                    stored_data["contexts"].append(stored_context)
            
            # Step 5: Test multimodal search on processed data
            search_results = await self.services["search"].search_multimodal(
                query="HP LaserJet error code 49 firmware",
                modalities=['text', 'image', 'video', 'table'],
                threshold=0.5,
                limit=10
            )
            
            duration = time.time() - start_time
            
            details = {
                "chunks_processed": len(chunks),
                "chunks_stored": len(stored_data["chunks"]),
                "svg_processed": svg_result.get("png_converted", False),
                "images_stored": len(stored_data["images"]),
                "contexts_extracted": len(context_tasks),
                "contexts_stored": len(stored_data["contexts"]),
                "search_results_count": len(search_results.get("results", [])),
                "pipeline_stages_completed": 5,
                "all_stages_successful": (
                    len(stored_data["chunks"]) > 0 and
                    svg_result.get("png_converted", False) and
                    len(stored_data["contexts"]) > 0 and
                    len(search_results.get("results", [])) >= 0
                )
            }
            
            success = details["all_stages_successful"]
            
            self.add_result(test_name, success, duration, details)
            
            if success:
                self.log(f"{test_name} completed successfully in {duration:.2f}s", "success")
            else:
                self.log(f"{test_name} failed", "error")
                
            return TestResult(test_name, success, duration, details)
            
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(test_name, False, duration, {}, str(e))
            self.log(f"{test_name} failed with exception: {e}", "error")
            return TestResult(test_name, False, duration, {}, str(e))
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        if self.console:
            # Create summary panel
            summary_text = f"""
Total Tests: {total_tests}
Passed: {passed_tests} ✅
Failed: {failed_tests} ❌
Success Rate: {(passed_tests/total_tests)*100:.1f}%
Total Duration: {total_duration:.2f}s
            """
            
            self.console.print(Panel(summary_text, title="Phase 6 Integration Test Summary", border_style="green" if failed_tests == 0 else "yellow"))
            
            # Create detailed results table
            table = Table(title="Detailed Test Results")
            table.add_column("Test Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Duration", style="blue")
            table.add_column("Key Metrics", style="yellow")
            
            for result in self.results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                metrics = []
                
                for key, value in result.details.items():
                    if isinstance(value, bool):
                        metrics.append(f"{key}: {'✅' if value else '❌'}")
                    elif isinstance(value, (int, float)):
                        metrics.append(f"{key}: {value}")
                
                metrics_text = "\n".join(metrics[:3])  # Show first 3 metrics
                table.add_row(
                    result.test_name,
                    status,
                    f"{result.duration:.2f}s",
                    metrics_text
                )
            
            self.console.print(table)
            
            # Performance analysis
            self.console.print("\n[bold]Performance Analysis:[/bold]")
            for result in self.results:
                if "within_threshold" in result.details:
                    threshold_status = "✅ Within" if result.details["within_threshold"] else "⚠️ Exceeded"
                    self.console.print(f"  {result.test_name}: {threshold_status} threshold")
            
        else:
            # Basic text output
            print(f"\nPhase 6 Integration Test Summary")
            print(f"=" * 40)
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            print(f"Total Duration: {total_duration:.2f}s")
            print("\nDetailed Results:")
            for result in self.results:
                status = "PASS" if result.success else "FAIL"
                print(f"  {result.test_name}: {status} ({result.duration:.2f}s)")
    
    async def cleanup(self):
        """Clean up test resources"""
        self.log("Cleaning up test resources...")
        
        try:
            # Clean up test data directory
            if self.test_data_dir.exists():
                shutil.rmtree(self.test_data_dir)
            
            # Disconnect services
            if "database" in self.services:
                await self.services["database"].disconnect()
            
            self.log("Cleanup completed successfully", "success")
            
        except Exception as e:
            self.log(f"Cleanup failed: {e}", "warning")
    
    async def run_all_tests(self):
        """Run all Phase 6 integration tests"""
        if not SERVICES_AVAILABLE:
            self.log("Backend services not available. Cannot run integration tests.", "error")
            return False
        
        self.log("Starting Phase 6 Integration Test Suite...")
        self.log(f"Test data directory: {self.test_data_dir}")
        
        # Setup services
        if not await self.setup_services():
            return False
        
        try:
            # Run all tests
            tests = [
                self.test_hierarchical_chunking_integration,
                self.test_svg_processing_integration,
                self.test_multimodal_search_integration,
                self.test_context_extraction_integration,
                self.test_end_to_end_pipeline
            ]
            
            for test_func in tests:
                try:
                    await test_func()
                except Exception as e:
                    self.log(f"Test {test_func.__name__} failed with exception: {e}", "error")
            
            # Generate report
            self.generate_report()
            
            # Return overall success
            passed_tests = sum(1 for r in self.results if r.success)
            total_tests = len(self.results)
            
            return passed_tests == total_tests
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    tester = Phase6IntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All Phase 6 integration tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some Phase 6 integration tests failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
