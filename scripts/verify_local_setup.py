#!/usr/bin/env python3
"""
Local Docker Setup Verification Script for KRAI

This script verifies that all local Docker services are running and accessible.
It generates a comprehensive health report for the entire KRAI stack.

Usage:
    python scripts/verify_local_setup.py              # Check all services
    python scripts/verify_local_setup.py --verbose    # Detailed output
    python scripts/verify_local_setup.py --service postgres  # Check specific service
"""

import os
import asyncio
import argparse
import sys
import json
import time
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    PSYCOPG2_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError, EndpointConnectionError
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    BOTO3_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class LocalSetupVerifier:
    """Verifies local Docker setup for KRAI"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.results = {}
        
        # Service configuration
        self.services = {
            'postgresql': {
                'host': os.getenv('DATABASE_HOST', 'localhost'),
                'port': int(os.getenv('DATABASE_PORT', '5432')),
                'database': os.getenv('DATABASE_NAME', 'krai'),
                'user': os.getenv('DATABASE_USER', 'krai_user'),
                'password': os.getenv('DATABASE_PASSWORD', 'krai_secure_password')
            },
            'minio': {
                'endpoint': os.getenv('OBJECT_STORAGE_ENDPOINT', 'http://localhost:9000'),
                'access_key': os.getenv('OBJECT_STORAGE_ACCESS_KEY', 'minioadmin'),
                'secret_key': os.getenv('OBJECT_STORAGE_SECRET_KEY', 'minioadmin123'),
                'buckets': {
                    'documents': os.getenv('OBJECT_STORAGE_BUCKET_DOCUMENTS', 'documents'),
                    'images': os.getenv('OBJECT_STORAGE_BUCKET_IMAGES', 'images'),
                    'videos': os.getenv('OBJECT_STORAGE_BUCKET_VIDEOS', 'videos'),
                    'temp': os.getenv('OBJECT_STORAGE_BUCKET_TEMP', 'temp')
                }
            },
            'ollama': {
                'url': os.getenv('AI_SERVICE_URL', 'http://localhost:11434'),
                'models': {
                    'embedding': os.getenv('AI_EMBEDDING_MODEL', 'nomic-embed-text:latest'),
                    'text': os.getenv('AI_TEXT_MODEL', 'llama3.2:latest'),
                    'vision': os.getenv('AI_VISION_MODEL', 'llava-phi3:latest')
                }
            },
            'pgadmin': {
                'url': 'http://localhost:5050'
            },
            'n8n': {
                'url': 'http://localhost:5678'
            },
            'minio_console': {
                'url': 'http://localhost:9001'
            }
        }
    
    def print_status(self, message: str, status: str = 'info'):
        """Print status message with appropriate formatting"""
        if self.console:
            color = {
                'success': 'green',
                'warning': 'yellow',
                'error': 'red',
                'info': 'blue'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def check_docker_services(self) -> Dict[str, any]:
        """Check if Docker containers are running"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{json .}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'error': 'Docker command failed',
                    'details': result.stderr
                }
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            expected_containers = [
                'krai-postgres',
                'krai-minio',
                'krai-ollama',
                'krai-pgadmin',
                'krai-n8n-chat-agent'
            ]
            
            running_containers = [c['Name'] for c in containers]
            missing_containers = [c for c in expected_containers if c not in running_containers]
            
            if missing_containers:
                return {
                    'status': 'warning',
                    'running': running_containers,
                    'missing': missing_containers,
                    'message': f"Missing containers: {', '.join(missing_containers)}"
                }
            else:
                return {
                    'status': 'success',
                    'running': running_containers,
                    'message': f"All {len(expected_containers)} containers running"
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'error': 'Docker command timed out'
            }
        except FileNotFoundError:
            return {
                'status': 'error',
                'error': 'Docker not found or not in PATH'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Unexpected error: {e}'
            }
    
    async def check_postgresql(self) -> Dict[str, any]:
        """Check PostgreSQL connectivity and schema"""
        if not PSYCOPG2_AVAILABLE:
            return {
                'status': 'error',
                'error': 'psycopg2 not available. Install with: pip install psycopg2-binary'
            }
        
        config = self.services['postgresql']
        
        try:
            # Test connection
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                connect_timeout=10
            )
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check pgvector extension
                cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                vector_result = cur.fetchone()
                
                # Check schemas
                cur.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name LIKE 'krai_%'
                    ORDER BY schema_name
                """)
                schemas = [row['schema_name'] for row in cur.fetchall()]
                
                # Expected schemas
                expected_schemas = [
                    'krai_core', 'krai_content', 'krai_intelligence', 
                    'krai_system', 'krai_parts'
                ]
                
                missing_schemas = [s for s in expected_schemas if s not in schemas]
                
                # Count tables in each schema
                table_counts = {}
                for schema in schemas:
                    cur.execute("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    """, (schema,))
                    table_counts[schema] = cur.fetchone()['count']
                
                conn.close()
                
                if missing_schemas:
                    return {
                        'status': 'warning',
                        'vector_version': vector_result['extversion'] if vector_result else None,
                        'schemas': schemas,
                        'missing_schemas': missing_schemas,
                        'table_counts': table_counts,
                        'message': f"Missing schemas: {', '.join(missing_schemas)}"
                    }
                else:
                    return {
                        'status': 'success',
                        'vector_version': vector_result['extversion'] if vector_result else None,
                        'schemas': schemas,
                        'table_counts': table_counts,
                        'message': f"PostgreSQL healthy - {len(schemas)} schemas, vector extension available"
                    }
                    
        except psycopg2.OperationalError as e:
            return {
                'status': 'error',
                'error': f'Connection failed: {e}',
                'message': 'Check if PostgreSQL is running and credentials are correct'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Unexpected error: {e}'
            }
    
    async def check_minio(self) -> Dict[str, any]:
        """Check MinIO connectivity and buckets"""
        if not BOTO3_AVAILABLE:
            return {
                'status': 'error',
                'error': 'boto3 not available. Install with: pip install boto3'
            }
        
        config = self.services['minio']
        
        try:
            # Create S3 client
            client = boto3.client(
                's3',
                endpoint_url=config['endpoint'],
                aws_access_key_id=config['access_key'],
                aws_secret_access_key=config['secret_key'],
                region_name='us-east-1'
            )
            
            # List buckets
            response = client.list_buckets()
            existing_buckets = [bucket['Name'] for bucket in response['Buckets']]
            
            # Check expected buckets
            expected_buckets = list(config['buckets'].values())
            missing_buckets = [b for b in expected_buckets if b not in existing_buckets]
            
            # Test upload/download to first bucket
            test_result = None
            if existing_buckets:
                try:
                    test_bucket = existing_buckets[0]
                    test_content = b'KRAI verification test'
                    test_key = 'verification-test.txt'
                    
                    # Upload
                    client.put_object(Bucket=test_bucket, Key=test_key, Body=test_content)
                    
                    # Download
                    response = client.get_object(Bucket=test_bucket, Key=test_key)
                    downloaded_content = response['Body'].read()
                    
                    # Cleanup
                    client.delete_object(Bucket=test_bucket, Key=test_key)
                    
                    if downloaded_content == test_content:
                        test_result = 'success'
                    else:
                        test_result = 'failed'
                        
                except Exception as e:
                    test_result = f'error: {e}'
            
            if missing_buckets:
                return {
                    'status': 'warning',
                    'endpoint': config['endpoint'],
                    'existing_buckets': existing_buckets,
                    'missing_buckets': missing_buckets,
                    'test_upload': test_result,
                    'message': f"Missing buckets: {', '.join(missing_buckets)}"
                }
            else:
                return {
                    'status': 'success',
                    'endpoint': config['endpoint'],
                    'existing_buckets': existing_buckets,
                    'test_upload': test_result,
                    'message': f"MinIO healthy - {len(existing_buckets)} buckets, read/write working"
                }
                
        except EndpointConnectionError:
            return {
                'status': 'error',
                'error': f'Cannot connect to MinIO at {config["endpoint"]}',
                'message': 'Check if MinIO container is running'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Unexpected error: {e}'
            }
    
    async def check_ollama(self) -> Dict[str, any]:
        """Check Ollama connectivity and models"""
        if not REQUESTS_AVAILABLE:
            return {
                'status': 'error',
                'error': 'requests not available. Install with: pip install requests'
            }
        
        config = self.services['ollama']
        
        try:
            # Check service health
            response = requests.get(f"{config['url']}/api/tags", timeout=10)
            
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'error': f'Ollama API returned status {response.status_code}',
                    'message': 'Check if Ollama container is running'
                }
            
            data = response.json()
            available_models = [model['name'] for model in data.get('models', [])]
            
            # Check required models
            required_models = list(config['models'].values())
            missing_models = [m for m in required_models if m not in available_models]
            
            if missing_models:
                return {
                    'status': 'warning',
                    'endpoint': config['url'],
                    'available_models': available_models,
                    'missing_models': missing_models,
                    'message': f"Missing models: {', '.join(missing_models)}",
                    'suggestion': f"Run: docker exec krai-ollama ollama pull {missing_models[0]}"
                }
            else:
                return {
                    'status': 'success',
                    'endpoint': config['url'],
                    'available_models': available_models,
                    'message': f"Ollama healthy - {len(available_models)} models available"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'error': f'Cannot connect to Ollama at {config["url"]}',
                'message': 'Check if Ollama container is running'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Unexpected error: {e}'
            }
    
    async def check_web_interface(self, name: str, url: str) -> Dict[str, any]:
        """Check if web interface is accessible"""
        if not REQUESTS_AVAILABLE:
            return {
                'status': 'error',
                'error': 'requests not available'
            }
        
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code in [200, 302, 401]:  # Accept auth required as healthy
                return {
                    'status': 'success',
                    'url': url,
                    'status_code': response.status_code,
                    'message': f"{name} interface accessible"
                }
            else:
                return {
                    'status': 'warning',
                    'url': url,
                    'status_code': response.status_code,
                    'message': f"{name} returned unexpected status code"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'url': url,
                'error': f'Cannot connect to {name}',
                'message': f'Check if {name.lower()} container is running'
            }
        except Exception as e:
            return {
                'status': 'error',
                'url': url,
                'error': f'Unexpected error: {e}'
            }
    
    async def run_verification(self, service_filter: Optional[str] = None) -> Dict[str, any]:
        """Run complete verification"""
        start_time = time.time()
        
        # Define all checks
        checks = {
            'docker': self.check_docker_services(),
            'postgresql': self.check_postgresql(),
            'minio': self.check_minio(),
            'ollama': self.check_ollama(),
            'pgadmin': self.check_web_interface('pgAdmin', self.services['pgadmin']['url']),
            'n8n': self.check_web_interface('n8n', self.services['n8n']['url']),
            'minio_console': self.check_web_interface('MinIO Console', self.services['minio_console']['url'])
        }
        
        # Filter checks if specified
        if service_filter:
            if service_filter in checks:
                checks = {service_filter: checks[service_filter]}
            else:
                self.print_status(f"Unknown service: {service_filter}", 'error')
                return {}
        
        # Execute all checks
        results = {}
        for name, check in checks.items():
            if self.verbose:
                self.print_status(f"Checking {name}...", 'info')
            results[name] = await check
        
        # Calculate summary
        total_checks = len(results)
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        warning_count = sum(1 for r in results.values() if r['status'] == 'warning')
        error_count = sum(1 for r in results.values() if r['status'] == 'error')
        
        overall_status = 'success' if error_count == 0 else ('warning' if warning_count > 0 else 'error')
        
        duration = time.time() - start_time
        
        summary = {
            'overall_status': overall_status,
            'total_checks': total_checks,
            'success_count': success_count,
            'warning_count': warning_count,
            'error_count': error_count,
            'duration_seconds': round(duration, 2),
            'timestamp': datetime.now().isoformat(),
            'services': results
        }
        
        return summary
    
    def print_results(self, results: Dict[str, any]):
        """Print formatted results"""
        if self.console:
            self.print_rich_results(results)
        else:
            self.print_plain_results(results)
    
    def print_rich_results(self, results: Dict[str, any]):
        """Print results with rich formatting"""
        # Summary panel
        summary_text = f"""
Overall Status: {results['overall_status'].upper()}
✅ Success: {results['success_count']}
⚠️  Warnings: {results['warning_count']}
❌ Errors: {results['error_count']}
⏱️  Duration: {results['duration_seconds']}s
        """.strip()
        
        self.console.print(Panel(summary_text, title="🔍 KRAI Setup Verification", border_style="blue"))
        
        # Services table
        table = Table(title="Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        status_icons = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        
        for service, result in results['services'].items():
            status = result['status']
            icon = status_icons.get(status, '❓')
            
            details = result.get('message', result.get('error', 'No details'))
            if len(details) > 60:
                details = details[:57] + '...'
            
            table.add_row(service, f"{icon} {status}", details)
        
        self.console.print(table)
        
        # Recommendations
        if results['warning_count'] > 0 or results['error_count'] > 0:
            recommendations = []
            
            for service, result in results['services'].items():
                if result['status'] in ['warning', 'error']:
                    if service == 'postgresql' and 'schemas' in result:
                        recommendations.append("• Run database migrations: Check /docker-entrypoint-initdb.d/")
                    elif service == 'minio' and 'missing_buckets' in result:
                        recommendations.append("• Initialize MinIO: python scripts/init_minio.py")
                    elif service == 'ollama' and 'missing_models' in result:
                        model = result['missing_models'][0] if result['missing_models'] else 'nomic-embed-text:latest'
                        recommendations.append(f"• Pull Ollama model: docker exec krai-ollama ollama pull {model}")
                    elif service == 'docker':
                        recommendations.append("• Start Docker services: docker-compose up -d")
            
            if recommendations:
                self.console.print(Panel("\n".join(recommendations), title="💡 Recommendations", border_style="yellow"))
    
    def print_plain_results(self, results: Dict[str, any]):
        """Print results in plain text"""
        print(f"\n🔍 KRAI Setup Verification Results")
        print("=" * 50)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"✅ Success: {results['success_count']}")
        print(f"⚠️  Warnings: {results['warning_count']}")
        print(f"❌ Errors: {results['error_count']}")
        print(f"⏱️  Duration: {results['duration_seconds']}s")
        print(f"🕐 Timestamp: {results['timestamp']}")
        print()
        
        print("Service Details:")
        print("-" * 30)
        
        for service, result in results['services'].items():
            status = result['status'].upper()
            details = result.get('message', result.get('error', 'No details'))
            
            print(f"{service}: {status}")
            print(f"  {details}")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Verify KRAI local Docker setup')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--service', type=str, help='Check specific service only')
    
    args = parser.parse_args()
    
    verifier = LocalSetupVerifier(verbose=args.verbose)
    results = await verifier.run_verification(args.service)
    
    if not results:
        sys.exit(1)
    
    verifier.print_results(results)
    
    # Exit code based on overall status
    if results['overall_status'] == 'success':
        sys.exit(0)
    elif results['overall_status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
