#!/usr/bin/env python3
"""
KRAI Multimodal Search Test
===========================

Comprehensive test for multimodal search functionality across all content types.
This script validates the MultimodalSearchService's ability to perform unified search
across text, images, videos, tables, and links with context-aware embeddings.

Features Tested:
- Unified multimodal search across all content types
- Modality filtering (text-only, image-only, etc.)
- Context-aware image search using context embeddings
- Two-stage image retrieval with LLM expansion
- RPC function validation (match_multimodal, match_images_by_context)
- Performance testing and latency measurement
- Threshold and limit parameter testing

Usage:
    python scripts/test_multimodal_search.py
    python scripts/test_multimodal_search.py --verbose
    python scripts/test_multimodal_search.py --performance
    python scripts/test_multimodal_search.py --query "test query"
"""

import os
import sys
import asyncio
import argparse
import json
import time
import uuid
import logging
import numpy as np
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
from backend.services.multimodal_search_service import MultimodalSearchService

@dataclass
class SearchTestResult:
    """Test result for multimodal search"""
    query: str
    total_results: int
    results_by_modality: Dict[str, int]
    avg_similarity: float
    processing_time_ms: float
    errors: List[str]
    warnings: List[str]

class MultimodalSearchTester:
    """Test runner for multimodal search functionality"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.multimodal_search_test")
        
        # Test configuration
        self.test_queries = [
            "error 900.01 paper jam",
            "fuser unit diagram",
            "C4080 specifications",
            "maintenance procedures",
            "technical troubleshooting"
        ]
        
        # Performance benchmarks
        self.performance_targets = {
            'multimodal_search_ms': 100,
            'context_aware_search_ms': 50,
            'two_stage_retrieval_ms': 500
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
                'search': 'orange'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪',
                'search': '🔍'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            self.print_status("Setting up Multimodal Search Tester", 'test')
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Initialize database service with local PostgreSQL
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
            
            self.print_status("Initializing multimodal search service...", 'info')
            self.search_service = MultimodalSearchService(
                database_service=self.database_service,
                ai_service=self.ai_service,
                default_threshold=0.5,
                default_limit=10
            )
            
            # Check if RPC functions are available
            await self._check_rpc_functions()
            
            self.print_status("Setup completed successfully", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def _check_rpc_functions(self):
        """Check if required RPC functions are available"""
        try:
            # Test match_multimodal function
            test_embedding = np.random.rand(768).tolist()
            
            try:
                results = await self.database_service.match_multimodal(
                    query_embedding=test_embedding,
                    match_threshold=0.5,
                    match_count=1
                )
                self.print_status("✅ match_multimodal RPC function available", 'success')
            except Exception as e:
                self.print_status(f"❌ match_multimodal RPC function not available: {e}", 'error')
                raise
            
            # Test match_images_by_context function
            try:
                results = await self.database_service.match_images_by_context(
                    query_embedding=test_embedding,
                    match_threshold=0.5,
                    match_count=1
                )
                self.print_status("✅ match_images_by_context RPC function available", 'success')
            except Exception as e:
                self.print_status(f"❌ match_images_by_context RPC function not available: {e}", 'error')
                raise
            
        except Exception as e:
            self.print_status("RPC functions not available - make sure migrations 116-118 are applied", 'warning')
            raise
    
    async def test_unified_multimodal_search(self) -> Dict[str, Any]:
        """Test unified multimodal search across all content types"""
        self.print_status("Testing unified multimodal search...", 'test')
        
        try:
            test_results = []
            
            for query in self.test_queries:
                self.print_status(f"Searching: '{query}'", 'search')
                
                start_time = time.time()
                
                # Perform unified search
                search_results = await self.search_service.search_multimodal(
                    query=query,
                    modalities=['text', 'image', 'video', 'table', 'link'],
                    threshold=0.5,
                    limit=10
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                if search_results and search_results.get('results'):
                    results = search_results['results']
                    
                    # Analyze results by modality
                    results_by_modality = {}
                    similarities = []
                    
                    for result in results:
                        modality = result.get('source_type', 'unknown')
                        if modality not in results_by_modality:
                            results_by_modality[modality] = 0
                        results_by_modality[modality] += 1
                        
                        similarity = result.get('similarity', 0)
                        if similarity > 0:
                            similarities.append(similarity)
                    
                    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                    
                    test_result = SearchTestResult(
                        query=query,
                        total_results=len(results),
                        results_by_modality=results_by_modality,
                        avg_similarity=avg_similarity,
                        processing_time_ms=processing_time,
                        errors=[],
                        warnings=[]
                    )
                    
                    test_results.append(test_result)
                    
                    self.print_status(f"  Found {len(results)} results in {processing_time:.2f}ms", 'success')
                    self.print_status(f"  Modalities: {dict(results_by_modality)}", 'info')
                else:
                    test_results.append(SearchTestResult(
                        query=query,
                        total_results=0,
                        results_by_modality={},
                        avg_similarity=0,
                        processing_time_ms=processing_time,
                        errors=['No results returned'],
                        warnings=[]
                    ))
                    self.print_status(f"  No results found", 'warning')
            
            # Calculate overall metrics
            total_queries = len(test_results)
            successful_queries = sum(1 for r in test_results if r.total_results > 0)
            avg_processing_time = sum(r.processing_time_ms for r in test_results) / total_queries
            
            return {
                'success': True,
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': (successful_queries / total_queries) * 100,
                'avg_processing_time_ms': avg_processing_time,
                'test_results': [vars(r) for r in test_results]
            }
            
        except Exception as e:
            self.print_status(f"Unified multimodal search test failed: {e}", 'error')
            self.logger.error("Unified multimodal search test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_modality_filtering(self) -> Dict[str, Any]:
        """Test modality filtering functionality"""
        self.print_status("Testing modality filtering...", 'test')
        
        try:
            query = "C4080 specifications"
            modality_combinations = [
                (['text'], "Text only"),
                (['text', 'table'], "Text + Table"),
                (['image', 'video'], "Image + Video"),
                (['text', 'image', 'table'], "Text + Image + Table"),
                (['text', 'image', 'video', 'table', 'link'], "All modalities")
            ]
            
            test_results = []
            
            for modalities, description in modality_combinations:
                self.print_status(f"Testing: {description}", 'search')
                
                start_time = time.time()
                
                # Perform filtered search
                search_results = await self.search_service.search_multimodal(
                    query=query,
                    modalities=modalities,
                    threshold=0.5,
                    limit=10
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                if search_results and search_results.get('results'):
                    results = search_results['results']
                    
                    # Verify all results match requested modalities
                    unexpected_modalities = set()
                    results_by_modality = {}
                    
                    for result in results:
                        modality = result.get('source_type', 'unknown')
                        if modality not in modalities:
                            unexpected_modalities.add(modality)
                        
                        if modality not in results_by_modality:
                            results_by_modality[modality] = 0
                        results_by_modality[modality] += 1
                    
                    test_result = {
                        'modalities': modalities,
                        'description': description,
                        'total_results': len(results),
                        'results_by_modality': results_by_modality,
                        'processing_time_ms': processing_time,
                        'filtering_correct': len(unexpected_modalities) == 0,
                        'unexpected_modalities': list(unexpected_modalities)
                    }
                    
                    test_results.append(test_result)
                    
                    status = "✅" if test_result['filtering_correct'] else "❌"
                    self.print_status(f"  {status} {len(results)} results, {dict(results_by_modality)}", 'success' if test_result['filtering_correct'] else 'error')
                else:
                    test_results.append({
                        'modalities': modalities,
                        'description': description,
                        'total_results': 0,
                        'results_by_modality': {},
                        'processing_time_ms': processing_time,
                        'filtering_correct': True,
                        'unexpected_modalities': []
                    })
                    self.print_status(f"  No results found", 'warning')
            
            # Calculate filtering accuracy
            correctly_filtered = sum(1 for r in test_results if r['filtering_correct'])
            filtering_accuracy = (correctly_filtered / len(test_results)) * 100
            
            return {
                'success': True,
                'total_tests': len(test_results),
                'correctly_filtered': correctly_filtered,
                'filtering_accuracy': filtering_accuracy,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Modality filtering test failed: {e}", 'error')
            self.logger.error("Modality filtering test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_context_aware_image_search(self) -> Dict[str, Any]:
        """Test context-aware image search"""
        self.print_status("Testing context-aware image search...", 'test')
        
        try:
            # Test queries that should find images with context
            image_queries = [
                "fuser unit diagram",
                "paper jam removal",
                "maintenance procedures",
                "technical specifications"
            ]
            
            test_results = []
            
            for query in image_queries:
                self.print_status(f"Context-aware image search: '{query}'", 'search')
                
                start_time = time.time()
                
                # Perform context-aware image search
                image_results = await self.search_service.search_images_by_context(
                    query=query,
                    threshold=0.5,
                    limit=5
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                if image_results:
                    # Analyze image results
                    results_with_context = 0
                    avg_similarity = 0
                    
                    for result in image_results:
                        if result.get('context_caption'):
                            results_with_context += 1
                        
                        similarity = result.get('similarity', 0)
                        if similarity > 0:
                            avg_similarity += similarity
                    
                    avg_similarity = avg_similarity / len(image_results) if image_results else 0
                    
                    test_result = {
                        'query': query,
                        'total_results': len(image_results),
                        'results_with_context': results_with_context,
                        'context_percentage': (results_with_context / len(image_results)) * 100 if image_results else 0,
                        'avg_similarity': avg_similarity,
                        'processing_time_ms': processing_time
                    }
                    
                    test_results.append(test_result)
                    
                    self.print_status(f"  Found {len(image_results)} images in {processing_time:.2f}ms", 'success')
                    self.print_status(f"  {results_with_context} have context ({test_result['context_percentage']:.1f}%)", 'info')
                else:
                    test_results.append({
                        'query': query,
                        'total_results': 0,
                        'results_with_context': 0,
                        'context_percentage': 0,
                        'avg_similarity': 0,
                        'processing_time_ms': processing_time
                    })
                    self.print_status(f"  No images found", 'warning')
            
            # Calculate overall metrics
            total_images = sum(r['total_results'] for r in test_results)
            total_with_context = sum(r['results_with_context'] for r in test_results)
            avg_processing_time = sum(r['processing_time_ms'] for r in test_results) / len(test_results)
            
            return {
                'success': True,
                'total_queries': len(test_results),
                'total_images_found': total_images,
                'total_with_context': total_with_context,
                'context_coverage': (total_with_context / total_images * 100) if total_images > 0 else 0,
                'avg_processing_time_ms': avg_processing_time,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Context-aware image search test failed: {e}", 'error')
            self.logger.error("Context-aware image search test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_two_stage_retrieval(self) -> Dict[str, Any]:
        """Test two-stage image retrieval with LLM expansion"""
        self.print_status("Testing two-stage image retrieval...", 'test')
        
        try:
            # Test queries suitable for two-stage retrieval
            test_queries = [
                "error 900.01",
                "paper jam",
                "fuser unit"
            ]
            
            test_results = []
            
            for query in test_queries:
                self.print_status(f"Two-stage retrieval: '{query}'", 'search')
                
                start_time = time.time()
                
                # Perform two-stage retrieval
                two_stage_results = await self.search_service.search_two_stage(
                    query=query,
                    max_chunks=5,
                    image_threshold=0.5,
                    image_limit=5
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                if two_stage_results:
                    # Analyze two-stage results
                    stage1_results = two_stage_results.get('stage1_results', [])
                    stage2_results = two_stage_results.get('stage2_results', [])
                    llm_answer = two_stage_results.get('llm_answer', '')
                    
                    test_result = {
                        'query': query,
                        'stage1_text_results': len(stage1_results),
                        'stage2_image_results': len(stage2_results),
                        'llm_answer_length': len(llm_answer),
                        'llm_answer_preview': llm_answer[:100] + "..." if len(llm_answer) > 100 else llm_answer,
                        'processing_time_ms': processing_time,
                        'improvement_detected': len(stage2_results) > 0
                    }
                    
                    test_results.append(test_result)
                    
                    self.print_status(f"  Stage 1: {len(stage1_results)} text results", 'info')
                    self.print_status(f"  Stage 2: {len(stage2_results)} image results", 'info')
                    self.print_status(f"  LLM answer: {len(llm_answer)} characters", 'info')
                    self.print_status(f"  Total time: {processing_time:.2f}ms", 'success')
                else:
                    test_results.append({
                        'query': query,
                        'stage1_text_results': 0,
                        'stage2_image_results': 0,
                        'llm_answer_length': 0,
                        'llm_answer_preview': '',
                        'processing_time_ms': processing_time,
                        'improvement_detected': False
                    })
                    self.print_status(f"  Two-stage retrieval failed", 'error')
            
            # Calculate overall metrics
            successful_retrievals = sum(1 for r in test_results if r['improvement_detected'])
            avg_processing_time = sum(r['processing_time_ms'] for r in test_results) / len(test_results)
            
            return {
                'success': True,
                'total_queries': len(test_results),
                'successful_retrievals': successful_retrievals,
                'improvement_rate': (successful_retrievals / len(test_results)) * 100,
                'avg_processing_time_ms': avg_processing_time,
                'test_results': test_results
            }
            
        except Exception as e:
            self.print_status(f"Two-stage retrieval test failed: {e}", 'error')
            self.logger.error("Two-stage retrieval test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance against benchmarks"""
        self.print_status("Testing performance benchmarks...", 'test')
        
        try:
            performance_results = {}
            
            # Test 1: Multimodal search performance
            self.print_status("Testing multimodal search performance...", 'info')
            query_times = []
            
            for _ in range(5):  # Run 5 times for average
                start_time = time.time()
                await self.search_service.search_multimodal(
                    query="performance test",
                    threshold=0.5,
                    limit=10
                )
                query_times.append((time.time() - start_time) * 1000)
            
            avg_multimodal_time = sum(query_times) / len(query_times)
            multimodal_within_target = avg_multimodal_time <= self.performance_targets['multimodal_search_ms']
            
            performance_results['multimodal_search'] = {
                'avg_time_ms': avg_multimodal_time,
                'target_ms': self.performance_targets['multimodal_search_ms'],
                'within_target': multimodal_within_target,
                'measurements': query_times
            }
            
            # Test 2: Context-aware image search performance
            self.print_status("Testing context-aware search performance...", 'info')
            context_times = []
            
            for _ in range(5):
                start_time = time.time()
                await self.search_service.search_images_by_context(
                    query="performance test",
                    threshold=0.5,
                    limit=5
                )
                context_times.append((time.time() - start_time) * 1000)
            
            avg_context_time = sum(context_times) / len(context_times)
            context_within_target = avg_context_time <= self.performance_targets['context_aware_search_ms']
            
            performance_results['context_aware_search'] = {
                'avg_time_ms': avg_context_time,
                'target_ms': self.performance_targets['context_aware_search_ms'],
                'within_target': context_within_target,
                'measurements': context_times
            }
            
            # Test 3: Two-stage retrieval performance
            self.print_status("Testing two-stage retrieval performance...", 'info')
            two_stage_times = []
            
            for _ in range(3):  # Fewer runs due to LLM overhead
                start_time = time.time()
                await self.search_service.search_two_stage(
                    query="performance test",
                    max_chunks=3,
                    image_threshold=0.5,
                    image_limit=3
                )
                two_stage_times.append((time.time() - start_time) * 1000)
            
            avg_two_stage_time = sum(two_stage_times) / len(two_stage_times)
            two_stage_within_target = avg_two_stage_time <= self.performance_targets['two_stage_retrieval_ms']
            
            performance_results['two_stage_retrieval'] = {
                'avg_time_ms': avg_two_stage_time,
                'target_ms': self.performance_targets['two_stage_retrieval_ms'],
                'within_target': two_stage_within_target,
                'measurements': two_stage_times
            }
            
            # Calculate overall performance score
            passed_benchmarks = sum(1 for result in performance_results.values() if result['within_target'])
            performance_score = (passed_benchmarks / len(performance_results)) * 100
            
            return {
                'success': True,
                'performance_score': performance_score,
                'passed_benchmarks': passed_benchmarks,
                'total_benchmarks': len(performance_results),
                'performance_results': performance_results
            }
            
        except Exception as e:
            self.print_status(f"Performance benchmark test failed: {e}", 'error')
            self.logger.error("Performance benchmark test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def display_search_results_table(self, results: List[Dict[str, Any]]):
        """Display search results in a formatted table"""
        if not self.console:
            return
        
        table = Table(title="Search Results by Query", box=box.ROUNDED)
        table.add_column("Query", style="cyan")
        table.add_column("Results", style="green")
        table.add_column("Modalities", style="yellow")
        table.add_column("Avg Similarity", style="blue")
        table.add_column("Time", style="red")
        
        for result in results:
            modalities_str = ", ".join([f"{k}: {v}" for k, v in result['results_by_modality'].items()])
            
            table.add_row(
                result['query'],
                str(result['total_results']),
                modalities_str,
                f"{result['avg_similarity']:.3f}",
                f"{result['processing_time_ms']:.2f}ms"
            )
        
        self.console.print(table)
    
    def display_performance_table(self, performance_results: Dict[str, Any]):
        """Display performance benchmark results"""
        if not self.console:
            return
        
        table = Table(title="Performance Benchmarks", box=box.ROUNDED)
        table.add_column("Test", style="cyan")
        table.add_column("Avg Time", style="green")
        table.add_column("Target", style="yellow")
        table.add_column("Status", style="blue")
        
        for test_name, result in performance_results.items():
            status = "✅ PASS" if result['within_target'] else "❌ FAIL"
            status_style = "green" if result['within_target'] else "red"
            
            table.add_row(
                test_name.replace('_', ' ').title(),
                f"{result['avg_time_ms']:.2f}ms",
                f"{result['target_ms']}ms",
                status,
                style=status_style
            )
        
        self.console.print(table)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all multimodal search tests"""
        self.print_status("Starting Multimodal Search Test Suite", 'test')
        
        if not await self.setup():
            return {'success': False, 'error': 'Setup failed'}
        
        # Run tests
        test_results = {}
        
        # Test 1: Unified multimodal search
        self.print_status("Running unified multimodal search test...", 'test')
        test_results['unified_search'] = await self.test_unified_multimodal_search()
        
        # Test 2: Modality filtering
        self.print_status("Running modality filtering test...", 'test')
        test_results['modality_filtering'] = await self.test_modality_filtering()
        
        # Test 3: Context-aware image search
        self.print_status("Running context-aware image search test...", 'test')
        test_results['context_aware_search'] = await self.test_context_aware_image_search()
        
        # Test 4: Two-stage retrieval
        self.print_status("Running two-stage retrieval test...", 'test')
        test_results['two_stage_retrieval'] = await self.test_two_stage_retrieval()
        
        # Test 5: Performance benchmarks
        self.print_status("Running performance benchmarks...", 'test')
        test_results['performance'] = await self.test_performance_benchmarks()
        
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
        
        self.console.print(Panel(summary_text, title="🔍 Multimodal Search Test Results", border_style="yellow"))
        
        # Unified Search Results
        if 'unified_search' in test_results:
            result = test_results['unified_search']
            if result['success']:
                self.console.print("\n🔍 Unified Multimodal Search", style="cyan bold")
                
                search_table = Table(title="Search Performance", box=box.ROUNDED)
                search_table.add_column("Metric", style="white")
                search_table.add_column("Value", style="green")
                
                search_table.add_row("Total Queries", str(result['total_queries']))
                search_table.add_row("Successful Queries", str(result['successful_queries']))
                search_table.add_row("Success Rate", f"{result['success_rate']:.1f}%")
                search_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                
                self.console.print(search_table)
                
                # Display detailed results
                self.display_search_results_table(result['test_results'])
        
        # Modality Filtering Results
        if 'modality_filtering' in test_results:
            result = test_results['modality_filtering']
            if result['success']:
                self.console.print("\n🎯 Modality Filtering", style="cyan bold")
                
                filtering_table = Table(title="Filtering Accuracy", box=box.ROUNDED)
                filtering_table.add_column("Metric", style="white")
                filtering_table.add_column("Value", style="green")
                
                filtering_table.add_row("Total Tests", str(result['total_tests']))
                filtering_table.add_row("Correctly Filtered", str(result['correctly_filtered']))
                filtering_table.add_row("Filtering Accuracy", f"{result['filtering_accuracy']:.1f}%")
                
                self.console.print(filtering_table)
        
        # Context-Aware Search Results
        if 'context_aware_search' in test_results:
            result = test_results['context_aware_search']
            if result['success']:
                self.console.print("\n🖼️ Context-Aware Image Search", style="cyan bold")
                
                context_table = Table(title="Context Coverage", box=box.ROUNDED)
                context_table.add_column("Metric", style="white")
                context_table.add_column("Value", style="green")
                
                context_table.add_row("Total Queries", str(result['total_queries']))
                context_table.add_row("Images Found", str(result['total_images_found']))
                context_table.add_row("With Context", str(result['total_with_context']))
                context_table.add_row("Context Coverage", f"{result['context_coverage']:.1f}%")
                context_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                
                self.console.print(context_table)
        
        # Two-Stage Retrieval Results
        if 'two_stage_retrieval' in test_results:
            result = test_results['two_stage_retrieval']
            if result['success']:
                self.console.print("\n🔄 Two-Stage Retrieval", style="cyan bold")
                
                two_stage_table = Table(title="Retrieval Improvement", box=box.ROUNDED)
                two_stage_table.add_column("Metric", style="white")
                two_stage_table.add_column("Value", style="green")
                
                two_stage_table.add_row("Total Queries", str(result['total_queries']))
                two_stage_table.add_row("Successful Retrievals", str(result['successful_retrievals']))
                two_stage_table.add_row("Improvement Rate", f"{result['improvement_rate']:.1f}%")
                two_stage_table.add_row("Avg Processing Time", f"{result['avg_processing_time_ms']:.2f}ms")
                
                self.console.print(two_stage_table)
        
        # Performance Results
        if 'performance' in test_results:
            result = test_results['performance']
            if result['success']:
                self.console.print("\n⚡ Performance Benchmarks", style="cyan bold")
                
                performance_table = Table(title="Performance Score", box=box.ROUNDED)
                performance_table.add_column("Metric", style="white")
                performance_table.add_column("Value", style="green")
                
                performance_table.add_row("Performance Score", f"{result['performance_score']:.1f}%")
                performance_table.add_row("Passed Benchmarks", f"{result['passed_benchmarks']}/{result['total_benchmarks']}")
                
                self.console.print(performance_table)
                
                # Display detailed performance results
                self.display_performance_table(result['performance_results'])
        
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
        
        print(f"\n🔍 Multimodal Search Test Results")
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
                if 'success_rate' in result:
                    print(f"  Success rate: {result['success_rate']:.1f}%")
                if 'avg_processing_time_ms' in result:
                    print(f"  Avg processing time: {result['avg_processing_time_ms']:.2f}ms")
                if 'performance_score' in result:
                    print(f"  Performance score: {result['performance_score']:.1f}%")
            else:
                print(f"  ❌ {result.get('error', 'Unknown error')}")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='KRAI Multimodal Search Test')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--query', type=str, help='Test specific query')
    
    args = parser.parse_args()
    
    tester = MultimodalSearchTester(verbose=args.verbose)
    
    if args.performance:
        # Run only performance tests
        await tester.setup()
        performance_result = await tester.test_performance_benchmarks()
        
        tester.generate_test_report({'performance': performance_result})
    elif args.query:
        # Test specific query
        await tester.setup()
        search_results = await tester.search_service.search_multimodal(
            query=args.query,
            threshold=0.5,
            limit=10
        )
        
        if search_results and search_results.get('results'):
            print(f"Query: '{args.query}'")
            print(f"Results: {len(search_results['results'])}")
            for result in search_results['results']:
                print(f"  {result['source_type']}: {result.get('similarity', 0):.3f} - {result.get('content', '')[:100]}...")
        else:
            print(f"No results found for query: '{args.query}'")
    else:
        # Run all tests
        results = await tester.run_all_tests()
        
        if results['success']:
            total_tests = len(results['test_results'])
            passed_tests = sum(1 for result in results['test_results'].values() if result.get('success', False))
            success_rate = passed_tests / total_tests * 100
            
            print(f"\n🎉 Multimodal search test completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            sys.exit(0 if passed_tests == total_tests else 1)
        else:
            print(f"❌ Multimodal search test failed: {results.get('error', 'Unknown error')}")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
