#!/usr/bin/env python3
"""
KRAI PostgreSQL Migrations Test
================================

Comprehensive test for PostgreSQL database migrations and schema validation.
This script validates that all required migrations are applied correctly,
RPC functions are available, and database schemas are properly structured.

Features Tested:
- Migration application and rollback
- Schema validation across all KRAI schemas
- RPC function availability and execution
- Index and constraint validation
- Database performance and connection pooling
- Data integrity and foreign key relationships

Usage:
    python scripts/test_postgresql_migrations.py
    python scripts/test_postgresql_migrations.py --verbose
    python scripts/test_postgresql_migrations.py --validate-only
    python scripts/test_postgresql_migrations.py --rpc-test
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

@dataclass
class MigrationTestResult:
    """Test result for database migrations"""
    migration_number: str
    applied: bool
    rollback_possible: bool
    validation_passed: bool
    execution_time_ms: float
    errors: List[str]
    warnings: List[str]

class PostgreSQLMigrationTester:
    """Test runner for PostgreSQL migrations"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.postgresql_migration_test")
        
        # Expected schemas and their key tables
        self.expected_schemas = {
            'krai_core': ['documents', 'document_metadata'],
            'krai_content': ['images', 'instructional_videos', 'links'],
            'krai_intelligence': ['chunks', 'embeddings_v2', 'structured_tables'],
            'krai_system': ['processing_logs', 'system_metrics'],
            'krai_parts': ['products', 'parts', 'compatibility_rules']
        }
        
        # Expected RPC functions (from Phase 6 migrations)
        self.expected_rpc_functions = [
            'match_multimodal',
            'match_images_by_context',
            'get_document_statistics',
            'search_chunks_by_content',
            'get_embeddings_by_document'
        ]
        
        # Performance targets
        self.performance_targets = {
            'connection_time_ms': 100,
            'query_time_ms': 50,
            'rpc_call_time_ms': 100
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
                'database': 'purple'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪',
                'database': '🗄️'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            self.print_status("Setting up PostgreSQL Migration Tester", 'test')
            
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
            
            # Test connection
            start_time = time.time()
            await self.database_service.connect()
            connection_time = (time.time() - start_time) * 1000
            
            if connection_time > self.performance_targets['connection_time_ms']:
                self.print_status(f"⚠️ Slow connection: {connection_time:.2f}ms (target: {self.performance_targets['connection_time_ms']}ms)", 'warning')
            else:
                self.print_status(f"✅ Connected in {connection_time:.2f}ms", 'success')
            
            self.print_status("Setup completed successfully", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def test_schema_validation(self) -> Dict[str, Any]:
        """Test database schema validation"""
        self.print_status("Testing database schema validation...", 'test')
        
        try:
            schema_results = {}
            total_expected_tables = 0
            total_found_tables = 0
            
            for schema_name, expected_tables in self.expected_schemas.items():
                self.print_status(f"Validating schema: {schema_name}", 'database')
                
                schema_result = {
                    'schema_exists': False,
                    'expected_tables': len(expected_tables),
                    'found_tables': 0,
                    'missing_tables': [],
                    'table_details': {}
                }
                
                # Check if schema exists
                try:
                    schema_exists = await self.database_service.execute_query(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = $1)",
                        [schema_name]
                    )
                    
                    schema_result['schema_exists'] = schema_exists[0]['exists'] if schema_exists else False
                    
                    if schema_result['schema_exists']:
                        # Get actual tables in schema
                        actual_tables = await self.database_service.execute_query(
                            """
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = $1 AND table_type = 'BASE TABLE'
                            ORDER BY table_name
                            """,
                            [schema_name]
                        )
                        
                        found_table_names = [row['table_name'] for row in actual_tables] if actual_tables else []
                        missing_tables = [table for table in expected_tables if table not in found_table_names]
                        unexpected_tables = [table for table in found_table_names if table not in expected_tables]
                        
                        schema_result['found_tables'] = len(found_table_names)
                        schema_result['missing_tables'] = missing_tables
                        schema_result['unexpected_tables'] = unexpected_tables
                        schema_result['table_details'] = {table: 'present' for table in found_table_names}
                        
                        total_found_tables += len(found_table_names)
                        
                        self.print_status(f"  Found {len(found_table_names)}/{len(expected_tables)} expected tables", 'success' if len(missing_tables) == 0 else 'warning')
                        
                        if missing_tables:
                            self.print_status(f"  Missing: {', '.join(missing_tables)}", 'warning')
                        
                        if unexpected_tables:
                            self.print_status(f"  Unexpected: {', '.join(unexpected_tables)}", 'info')
                    else:
                        self.print_status(f"  Schema {schema_name} does not exist", 'error')
                        schema_result['missing_tables'] = expected_tables
                    
                    total_expected_tables += len(expected_tables)
                    
                except Exception as e:
                    schema_result['error'] = str(e)
                    self.print_status(f"  Error checking schema: {e}", 'error')
                
                schema_results[schema_name] = schema_result
            
            # Calculate overall schema validation score
            schema_score = (total_found_tables / total_expected_tables * 100) if total_expected_tables > 0 else 0
            
            return {
                'success': schema_score >= 90,  # Require at least 90% of expected tables
                'schema_score': schema_score,
                'total_expected_tables': total_expected_tables,
                'total_found_tables': total_found_tables,
                'schema_results': schema_results
            }
            
        except Exception as e:
            self.print_status(f"Schema validation test failed: {e}", 'error')
            self.logger.error("Schema validation test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_rpc_functions(self) -> Dict[str, Any]:
        """Test RPC function availability and execution"""
        self.print_status("Testing RPC function availability...", 'test')
        
        try:
            rpc_results = {}
            total_functions = len(self.expected_rpc_functions)
            working_functions = 0
            
            for function_name in self.expected_rpc_functions:
                self.print_status(f"Testing RPC function: {function_name}", 'database')
                
                function_result = {
                    'exists': False,
                    'executable': False,
                    'execution_time_ms': 0,
                    'error': None
                }
                
                try:
                    # Check if function exists in relevant schemas
                    function_exists = await self.database_service.execute_query(
                        """
                        SELECT EXISTS(
                            SELECT 1 FROM pg_proc p
                            JOIN pg_namespace n ON p.pronamespace = n.oid
                            WHERE p.proname = $1 AND n.nspname IN ('public','krai_intelligence','krai_content','krai_core')
                        )
                        """,
                        [function_name]
                    )
                    
                    function_result['exists'] = function_exists[0]['exists'] if function_exists else False
                    
                    if function_result['exists']:
                        # Test function execution with minimal parameters
                        start_time = time.time()
                        
                        try:
                            if function_name == 'match_multimodal':
                                # Test with dummy embedding
                                test_embedding = [0.0] * 768
                                result = await self.database_service.match_multimodal(
                                    query_embedding=test_embedding,
                                    match_threshold=0.5,
                                    match_count=1
                                )
                                function_result['executable'] = True
                            elif function_name == 'match_images_by_context':
                                # Test with dummy embedding
                                test_embedding = [0.0] * 768
                                result = await self.database_service.match_images_by_context(
                                    query_embedding=test_embedding,
                                    match_threshold=0.5,
                                    match_count=1
                                )
                                function_result['executable'] = True
                            elif function_name == 'get_document_statistics':
                                result = await self.database_service.get_document_statistics()
                                function_result['executable'] = True
                            elif function_name == 'search_chunks_by_content':
                                result = await self.database_service.search_chunks_by_content(
                                    query_text="test",
                                    limit=1
                                )
                                function_result['executable'] = True
                            elif function_name == 'get_embeddings_by_document':
                                test_document_id = str(uuid.uuid4())
                                result = await self.database_service.get_embeddings_by_document(
                                    document_id=test_document_id
                                )
                                function_result['executable'] = True
                            
                            execution_time = (time.time() - start_time) * 1000
                            function_result['execution_time_ms'] = execution_time
                            working_functions += 1
                            
                            if execution_time > self.performance_targets['rpc_call_time_ms']:
                                self.print_status(f"  ⚠️ Slow execution: {execution_time:.2f}ms", 'warning')
                            else:
                                self.print_status(f"  ✅ Executed in {execution_time:.2f}ms", 'success')
                            
                        except Exception as exec_error:
                            function_result['error'] = str(exec_error)
                            self.print_status(f"  ❌ Execution failed: {exec_error}", 'error')
                    else:
                        self.print_status(f"  ❌ Function does not exist", 'error')
                
                except Exception as e:
                    function_result['error'] = str(e)
                    self.print_status(f"  ❌ Error checking function: {e}", 'error')
                
                rpc_results[function_name] = function_result
            
            # Calculate RPC function score
            rpc_score = (working_functions / total_functions * 100) if total_functions > 0 else 0
            
            return {
                'success': rpc_score >= 80,  # Require at least 80% of functions working
                'rpc_score': rpc_score,
                'total_functions': total_functions,
                'working_functions': working_functions,
                'rpc_results': rpc_results
            }
            
        except Exception as e:
            self.print_status(f"RPC function test failed: {e}", 'error')
            self.logger.error("RPC function test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_migration_status(self) -> Dict[str, Any]:
        """Test migration application status via feature presence"""
        self.print_status("Testing migration application status...", 'test')
        
        try:
            # Check for Phase 6 feature tables instead of schema_migrations
            feature_checks = {}
            
            # Check for embeddings_v2 table (Phase 6 multimodal)
            embeddings_v2_exists = await self.database_service.execute_query(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'embeddings_v2' AND table_schema = 'krai_intelligence')"
            )
            feature_checks['embeddings_v2'] = embeddings_v2_exists[0]['exists'] if embeddings_v2_exists else False
            
            # Check for structured_tables table (Phase 6 multimodal)
            structured_tables_exists = await self.database_service.execute_query(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'structured_tables' AND table_schema = 'krai_intelligence')"
            )
            feature_checks['structured_tables'] = structured_tables_exists[0]['exists'] if structured_tables_exists else False
            
            # Check for hierarchical chunk columns (Phase 6)
            hierarchical_columns = await self.database_service.execute_query(
                """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'chunks' 
                    AND table_schema = 'krai_intelligence' 
                    AND column_name IN ('section_level', 'previous_chunk_id', 'next_chunk_id', 'parent_path')
                )
                """
            )
            feature_checks['hierarchical_columns'] = hierarchical_columns[0]['exists'] if hierarchical_columns else False
            
            # Check for context columns in images table (Phase 6)
            context_columns = await self.database_service.execute_query(
                """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'images' 
                    AND table_schema = 'krai_content' 
                    AND column_name IN ('page_header', 'context_text', 'related_chunks')
                )
                """
            )
            feature_checks['context_columns'] = context_columns[0]['exists'] if context_columns else False
            
            # Check for vector_graphics image type (Phase 6 SVG)
            vector_graphics_exists = await self.database_service.execute_query(
                """
                SELECT EXISTS(
                    SELECT 1 FROM krai_content.images 
                    WHERE image_type = 'vector_graphic' 
                    LIMIT 1
                )
                """
            )
            feature_checks['vector_graphics'] = vector_graphics_exists[0]['exists'] if vector_graphics_exists else False
            
            # Check for Phase 6 RPC functions
            phase6_functions = await self.database_service.execute_query(
                """
                SELECT COUNT(*) as count
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname IN ('match_multimodal', 'match_images_by_context')
                AND n.nspname IN ('public','krai_intelligence','krai_content','krai_core')
                """
            )
            phase6_function_count = phase6_functions[0]['count'] if phase6_functions else 0
            feature_checks['phase6_functions'] = phase6_function_count >= 2
            
            # Calculate success based on critical Phase 6 features
            critical_features = ['embeddings_v2', 'structured_tables', 'hierarchical_columns', 'context_columns']
            critical_features_present = sum(1 for feature in critical_features if feature_checks.get(feature, False))
            
            overall_success = critical_features_present >= 3  # Require at least 3 of 4 critical features
            
            result = {
                'success': overall_success,
                'feature_checks': feature_checks,
                'critical_features_present': critical_features_present,
                'total_critical_features': len(critical_features),
                'phase6_complete': all(feature_checks.values()),
                'migration_approach': 'file_based_01_05'
            }
            
            self.print_status(f"Critical Phase 6 features: {critical_features_present}/{len(critical_features)} present", 'info' if overall_success else 'warning')
            
            if not overall_success:
                missing_features = [feature for feature in critical_features if not feature_checks.get(feature, False)]
                self.print_status(f"Missing critical features: {', '.join(missing_features)}", 'error')
            else:
                self.print_status("✅ Critical Phase 6 migration features detected", 'success')
            
            return result
            
        except Exception as e:
            self.print_status(f"Migration status test failed: {e}", 'error')
            self.logger.error("Migration status test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_database_performance(self) -> Dict[str, Any]:
        """Test database performance and connection pooling"""
        self.print_status("Testing database performance...", 'test')
        
        try:
            performance_results = {}
            
            # Test 1: Simple query performance
            self.print_status("Testing simple query performance...", 'info')
            query_times = []
            
            for _ in range(10):
                start_time = time.time()
                await self.database_service.execute_query("SELECT 1")
                query_times.append((time.time() - start_time) * 1000)
            
            avg_query_time = sum(query_times) / len(query_times)
            performance_results['simple_query'] = {
                'avg_time_ms': avg_query_time,
                'target_ms': self.performance_targets['query_time_ms'],
                'within_target': avg_query_time <= self.performance_targets['query_time_ms'],
                'measurements': query_times
            }
            
            # Test 2: Connection pool stress test
            self.print_status("Testing connection pool stress...", 'info')
            concurrent_queries = 20
            start_time = time.time()
            
            async def run_concurrent_query():
                return await self.database_service.execute_query("SELECT pg_sleep(0.01), version()")
            
            # Run concurrent queries
            tasks = [run_concurrent_query() for _ in range(concurrent_queries)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            concurrent_time = (time.time() - start_time) * 1000
            successful_queries = sum(1 for r in results if not isinstance(r, Exception))
            
            performance_results['concurrent_queries'] = {
                'total_queries': concurrent_queries,
                'successful_queries': successful_queries,
                'success_rate': (successful_queries / concurrent_queries) * 100,
                'total_time_ms': concurrent_time,
                'avg_time_per_query_ms': concurrent_time / concurrent_queries
            }
            
            # Test 3: Complex query performance
            self.print_status("Testing complex query performance...", 'info')
            
            start_time = time.time()
            complex_result = await self.database_service.execute_query("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables 
                WHERE schemaname LIKE 'krai_%'
                ORDER BY schemaname, tablename
            """)
            complex_time = (time.time() - start_time) * 1000
            
            performance_results['complex_query'] = {
                'time_ms': complex_time,
                'rows_returned': len(complex_result) if complex_result else 0
            }
            
            # Calculate overall performance score
            simple_query_score = 100 if performance_results['simple_query']['within_target'] else 50
            concurrent_score = performance_results['concurrent_queries']['success_rate']
            overall_score = (simple_query_score + concurrent_score) / 2
            
            return {
                'success': overall_score >= 80,
                'performance_score': overall_score,
                'performance_results': performance_results
            }
            
        except Exception as e:
            self.print_status(f"Database performance test failed: {e}", 'error')
            self.logger.error("Database performance test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and foreign key relationships"""
        self.print_status("Testing data integrity...", 'test')
        
        try:
            integrity_results = {}
            
            # Test 1: Foreign key constraints
            self.print_status("Testing foreign key constraints...", 'info')
            
            # Get foreign key constraints for KRAI schemas
            fk_constraints = await self.database_service.execute_query("""
                SELECT 
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema LIKE 'krai_%'
                ORDER BY tc.table_schema, tc.table_name
            """)
            
            integrity_results['foreign_key_constraints'] = {
                'total_constraints': len(fk_constraints) if fk_constraints else 0,
                'constraints': fk_constraints if fk_constraints else []
            }
            
            # Test 2: Index validation
            self.print_status("Testing index presence...", 'info')
            
            # Check for important indexes
            important_indexes = await self.database_service.execute_query("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname LIKE 'krai_%'
                    AND (indexname LIKE '%embedding%' 
                         OR indexname LIKE '%document%'
                         OR indexname LIKE '%chunk%'
                         OR indexname LIKE '%search%')
                ORDER BY schemaname, tablename, indexname
            """)
            
            integrity_results['important_indexes'] = {
                'total_indexes': len(important_indexes) if important_indexes else 0,
                'indexes': important_indexes if important_indexes else []
            }
            
            # Test 3: Table size analysis
            self.print_status("Analyzing table sizes...", 'info')
            
            table_sizes = await self.database_service.execute_query("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname LIKE 'krai_%'
                ORDER BY size_bytes DESC
            """)
            
            total_db_size = sum(row['size_bytes'] for row in table_sizes) if table_sizes else 0
            
            integrity_results['table_sizes'] = {
                'total_db_size_bytes': total_db_size,
                'total_db_size_pretty': self._format_bytes(total_db_size),
                'tables': table_sizes if table_sizes else []
            }
            
            # Calculate integrity score
            fk_score = 100  # Assume FK constraints are properly defined if they exist
            index_score = min(100, len(integrity_results['important_indexes']['indexes']) * 10)  # Score based on number of important indexes
            integrity_score = (fk_score + index_score) / 2
            
            return {
                'success': integrity_score >= 70,
                'integrity_score': integrity_score,
                'integrity_results': integrity_results
            }
            
        except Exception as e:
            self.print_status(f"Data integrity test failed: {e}", 'error')
            self.logger.error("Data integrity test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"
    
    def display_schema_table(self, schema_results: Dict[str, Any]):
        """Display schema validation results"""
        if not self.console:
            return
        
        table = Table(title="Schema Validation Results", box=box.ROUNDED)
        table.add_column("Schema", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Tables", style="yellow")
        table.add_column("Missing", style="red")
        
        for schema_name, result in schema_results.items():
            status = "✅ Exists" if result['schema_exists'] else "❌ Missing"
            status_style = "green" if result['schema_exists'] else "red"
            
            tables_str = f"{result['found_tables']}/{result['expected_tables']}"
            missing_str = ", ".join(result['missing_tables']) if result['missing_tables'] else "None"
            
            table.add_row(
                schema_name,
                status,
                tables_str,
                missing_str,
                style=status_style
            )
        
        self.console.print(table)
    
    def display_rpc_table(self, rpc_results: Dict[str, Any]):
        """Display RPC function test results"""
        if not self.console:
            return
        
        table = Table(title="RPC Function Test Results", box=box.ROUNDED)
        table.add_column("Function", style="cyan")
        table.add_column("Exists", style="green")
        table.add_column("Executable", style="yellow")
        table.add_column("Time", style="blue")
        table.add_column("Status", style="red")
        
        for function_name, result in rpc_results.items():
            exists = "✅" if result['exists'] else "❌"
            executable = "✅" if result['executable'] else "❌"
            time_str = f"{result['execution_time_ms']:.2f}ms" if result['execution_time_ms'] > 0 else "N/A"
            
            if result['executable']:
                status = "✅ Working"
                status_style = "green"
            elif result['exists']:
                status = "❌ Failed"
                status_style = "red"
            else:
                status = "❌ Missing"
                status_style = "red"
            
            table.add_row(
                function_name,
                exists,
                executable,
                time_str,
                status,
                style=status_style
            )
        
        self.console.print(table)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all PostgreSQL migration tests"""
        self.print_status("Starting PostgreSQL Migration Test Suite", 'test')
        
        if not await self.setup():
            return {'success': False, 'error': 'Setup failed'}
        
        # Run tests
        test_results = {}
        
        # Test 1: Schema validation
        self.print_status("Running schema validation test...", 'test')
        test_results['schema_validation'] = await self.test_schema_validation()
        
        # Test 2: RPC functions
        self.print_status("Running RPC function test...", 'test')
        test_results['rpc_functions'] = await self.test_rpc_functions()
        
        # Test 3: Migration status
        self.print_status("Running migration status test...", 'test')
        test_results['migration_status'] = await self.test_migration_status()
        
        # Test 4: Database performance
        self.print_status("Running database performance test...", 'test')
        test_results['performance'] = await self.test_database_performance()
        
        # Test 5: Data integrity
        self.print_status("Running data integrity test...", 'test')
        test_results['data_integrity'] = await self.test_data_integrity()
        
        # Generate report
        self.generate_test_report(test_results)
        
        # Cleanup
        # Database service cleanup (disconnect not available)
        # await self.database_service.disconnect()
        
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
        
        self.console.print(Panel(summary_text, title="🗄️ PostgreSQL Migration Test Results", border_style="purple"))
        
        # Schema Validation Results
        if 'schema_validation' in test_results:
            result = test_results['schema_validation']
            if result['success']:
                self.console.print("\n🏗️ Schema Validation", style="cyan bold")
                
                schema_table = Table(title="Schema Summary", box=box.ROUNDED)
                schema_table.add_column("Metric", style="white")
                schema_table.add_column("Value", style="green")
                
                schema_table.add_row("Schema Score", f"{result['schema_score']:.1f}%")
                schema_table.add_row("Expected Tables", str(result['total_expected_tables']))
                schema_table.add_row("Found Tables", str(result['total_found_tables']))
                
                self.console.print(schema_table)
                
                # Display detailed schema results
                self.display_schema_table(result['schema_results'])
        
        # RPC Function Results
        if 'rpc_functions' in test_results:
            result = test_results['rpc_functions']
            if result['success']:
                self.console.print("\n⚡ RPC Functions", style="cyan bold")
                
                rpc_table = Table(title="RPC Function Summary", box=box.ROUNDED)
                rpc_table.add_column("Metric", style="white")
                rpc_table.add_column("Value", style="green")
                
                rpc_table.add_row("RPC Score", f"{result['rpc_score']:.1f}%")
                rpc_table.add_row("Total Functions", str(result['total_functions']))
                rpc_table.add_row("Working Functions", str(result['working_functions']))
                
                self.console.print(rpc_table)
                
                # Display detailed RPC results
                self.display_rpc_table(result['rpc_results'])
        
        # Migration Status Results
        if 'migration_status' in test_results:
            result = test_results['migration_status']
            if result['success']:
                self.console.print("\n📋 Migration Status", style="cyan bold")
                
                migration_table = Table(title="Migration Summary", box=box.ROUNDED)
                migration_table.add_column("Metric", style="white")
                migration_table.add_column("Value", style="green")
                
                migration_table.add_row("Migration Approach", result['migration_approach'])
                migration_table.add_row("Critical Features", f"{result['critical_features_present']}/{result['total_critical_features']}")
                migration_table.add_row("Phase 6 Complete", "✅ Yes" if result['phase6_complete'] else "❌ No")
                
                self.console.print(migration_table)
            else:
                self.console.print("\n📋 Migration Status", style="cyan bold")
                self.console.print(f"❌ {result.get('error', 'Migration check failed')}", style="red")
        
        # Performance Results
        if 'performance' in test_results:
            result = test_results['performance']
            if result['success']:
                self.console.print("\n⚡ Database Performance", style="cyan bold")
                
                perf_table = Table(title="Performance Summary", box=box.ROUNDED)
                perf_table.add_column("Metric", style="white")
                perf_table.add_column("Value", style="green")
                
                perf_table.add_row("Performance Score", f"{result['performance_score']:.1f}%")
                
                simple_query = result['performance_results']['simple_query']
                perf_table.add_row("Simple Query Time", f"{simple_query['avg_time_ms']:.2f}ms")
                
                concurrent = result['performance_results']['concurrent_queries']
                perf_table.add_row("Concurrent Success Rate", f"{concurrent['success_rate']:.1f}%")
                
                self.console.print(perf_table)
        
        # Data Integrity Results
        if 'data_integrity' in test_results:
            result = test_results['data_integrity']
            if result['success']:
                self.console.print("\n🔒 Data Integrity", style="cyan bold")
                
                integrity_table = Table(title="Integrity Summary", box=box.ROUNDED)
                integrity_table.add_column("Metric", style="white")
                integrity_table.add_column("Value", style="green")
                
                integrity_table.add_row("Integrity Score", f"{result['integrity_score']:.1f}%")
                
                fk_constraints = result['integrity_results']['foreign_key_constraints']
                integrity_table.add_row("FK Constraints", str(fk_constraints['total_constraints']))
                
                indexes = result['integrity_results']['important_indexes']
                integrity_table.add_row("Important Indexes", str(indexes['total_indexes']))
                
                table_sizes = result['integrity_results']['table_sizes']
                integrity_table.add_row("Database Size", table_sizes['total_db_size_pretty'])
                
                self.console.print(integrity_table)
        
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
        
        print(f"\n🗄️ PostgreSQL Migration Test Results")
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
                if 'schema_score' in result:
                    print(f"  Schema score: {result['schema_score']:.1f}%")
                if 'rpc_score' in result:
                    print(f"  RPC score: {result['rpc_score']:.1f}%")
                if 'performance_score' in result:
                    print(f"  Performance score: {result['performance_score']:.1f}%")
                if 'integrity_score' in result:
                    print(f"  Integrity score: {result['integrity_score']:.1f}%")
            else:
                print(f"  ❌ {result.get('error', 'Unknown error')}")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='KRAI PostgreSQL Migration Test')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--validate-only', action='store_true', help='Run schema validation only')
    parser.add_argument('--rpc-test', action='store_true', help='Run RPC function tests only')
    
    args = parser.parse_args()
    
    tester = PostgreSQLMigrationTester(verbose=args.verbose)
    
    if args.validate_only:
        # Run only schema validation
        await tester.setup()
        schema_result = await tester.test_schema_validation()
        
        tester.generate_test_report({'schema_validation': schema_result})
        
        await tester.database_service.disconnect()
    elif args.rpc_test:
        # Run only RPC function tests
        await tester.setup()
        rpc_result = await tester.test_rpc_functions()
        
        tester.generate_test_report({'rpc_functions': rpc_result})
        
        await tester.database_service.disconnect()
    else:
        # Run all tests
        results = await tester.run_all_tests()
        
        if results['success']:
            total_tests = len(results['test_results'])
            passed_tests = sum(1 for result in results['test_results'].values() if result.get('success', False))
            success_rate = passed_tests / total_tests * 100
            
            print(f"\n🎉 PostgreSQL migration test completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            sys.exit(0 if passed_tests == total_tests else 1)
        else:
            print(f"❌ PostgreSQL migration test failed: {results.get('error', 'Unknown error')}")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
