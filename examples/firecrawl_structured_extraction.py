#!/usr/bin/env python3
"""
Structured data extraction example using Firecrawl's LLM-based extraction.

Purpose: Demonstrate schema-based extraction of product specs, error codes, and service manuals

Usage Examples:
    # Extract product specs
    python examples/firecrawl_structured_extraction.py --url https://example.com/product --type product_specs
    
    # Extract error codes
    python examples/firecrawl_structured_extraction.py --url https://example.com/support --type error_codes
    
    # Custom schema extraction
    python examples/firecrawl_structured_extraction.py --url https://example.com --schema custom_schema.json
    
    # Batch extraction
    python examples/firecrawl_structured_extraction.py --batch urls.txt --type product_specs --export results.json
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.web_scraping_service import (
    WebScrapingService,
    create_web_scraping_service,
    FirecrawlUnavailableError
)
from backend.services.structured_extraction_service import StructuredExtractionService

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.json import JSON
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Install with: pip install rich")
    print("Falling back to basic console output")

console = Console() if RICH_AVAILABLE else None


def print_with_rich(content):
    """Print using rich if available, otherwise regular print."""
    if RICH_AVAILABLE and console:
        console.print(content)
    else:
        print(content)


def load_extraction_configuration() -> Dict[str, str]:
    """Load extraction configuration from environment variables."""
    config = {
        'backend': os.getenv('SCRAPING_BACKEND', 'firecrawl'),  # Firecrawl required for extraction
        'firecrawl_api_url': os.getenv('FIRECRAWL_API_URL', 'http://localhost:3002'),
        'firecrawl_llm_provider': os.getenv('FIRECRAWL_LLM_PROVIDER', 'ollama'),
        'firecrawl_model_name': os.getenv('FIRECRAWL_MODEL_NAME', 'llama3.1:8b'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'confidence_threshold': float(os.getenv('EXTRACTION_CONFIDENCE_THRESHOLD', '0.7')),
    }
    
    # Display configuration summary
    if RICH_AVAILABLE and console:
        config_table = Table(title="🔧 Structured Extraction Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        for key, value in config.items():
            if key == 'openai_api_key' and value:
                value = f"***{value[-4:]}"  # Show last 4 chars only
            config_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(config_table)
    else:
        print("=== Structured Extraction Configuration ===")
        for key, value in config.items():
            if key == 'openai_api_key' and value:
                value = f"***{value[-4:]}"
            print(f"{key.replace('_', ' ').title()}: {value}")
        print()
    
    return config


def load_extraction_schemas() -> Dict[str, Any]:
    """Load extraction schemas from the backend schemas directory."""
    schema_path = Path(__file__).parent.parent / 'backend' / 'schemas' / 'extraction_schemas.json'
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schemas_data = json.load(f)
        
        schemas = schemas_data.get('schemas', {})
        
        # Display available schemas
        if RICH_AVAILABLE and console:
            schema_table = Table(title="📋 Available Extraction Schemas")
            schema_table.add_column("Schema Name", style="cyan")
            schema_table.add_column("Description", style="white")
            
            for name, schema_info in schemas.items():
                schema_table.add_row(
                    name,
                    schema_info.get('description', 'No description')
                )
            
            console.print(schema_table)
        else:
            print("=== Available Extraction Schemas ===")
            for name, schema_info in schemas.items():
                print(f"{name}: {schema_info.get('description', 'No description')}")
            print()
        
        return schemas
        
    except FileNotFoundError:
        print_with_rich("❌ Extraction schemas file not found")
        return {}
    except json.JSONDecodeError as e:
        print_with_rich(f"❌ Invalid JSON in schemas file: {e}")
        return {}


async def extract_product_specs(url: str, llm_provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract product specifications from a URL.
    
    Args:
        url: URL to extract product specs from
        llm_provider: Force specific LLM provider (ollama, openai)
    
    Returns:
        Dictionary with extraction results
    """
    start_time = time.time()
    
    try:
        # Create services
        scraping_service = create_web_scraping_service(backend='firecrawl')
        
        # Mock database service for this example
        class MockDatabaseService:
            async def insert_structured_extraction(self, data):
                return True
        
        db_service = MockDatabaseService()
        extraction_service = StructuredExtractionService(
            web_scraping_service=scraping_service,
            database_service=db_service
        )
        
        print_with_rich(f"🏭 Extracting product specs from: {url}")
        if llm_provider:
            print_with_rich(f"🤖 Using LLM provider: {llm_provider}")
        
        # Perform extraction
        result = await extraction_service.extract_product_specs(url)
        duration = time.time() - start_time
        
        if result.get('success', False):
            extracted_data = result.get('extracted_data', {})
            confidence = result.get('confidence', 0.0)
            
            # Get additional fields from result if available
            extraction_type = result.get('extraction_type', 'unknown')
            schema_version = result.get('schema_version', 'unknown')
            record_id = result.get('record_id', 'unknown')
            llm_used = result.get('llm_provider', 'unknown')
            
            # Display extraction results
            if RICH_AVAILABLE and console:
                success_panel = Panel(
                    f"✅ **Product Specs Extracted**\n"
                    f"🏭 Model: {extracted_data.get('model_number', 'Unknown')}\n"
                    f"📊 Series: {extracted_data.get('series_name', 'Unknown')}\n"
                    f"🖨️ Type: {extracted_data.get('product_type', 'Unknown')}\n"
                    f"⚡ Speed Mono: {extracted_data.get('speed_mono', 'N/A')} ppm\n"
                    f"🌈 Speed Color: {extracted_data.get('speed_color', 'N/A')} ppm\n"
                    f"📏 Resolution: {extracted_data.get('resolution', 'N/A')}\n"
                    f"📊 Confidence: {confidence:.2f}\n"
                    f"🤖 LLM Provider: {llm_used}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="green"
                )
                console.print(success_panel)
                
                # Display full extracted data as JSON
                if extracted_data:
                    json_panel = Panel(
                        JSON.from_data(extracted_data, indent=2),
                        title="Extracted Data (JSON)",
                        border_style="blue"
                    )
                    console.print(json_panel)
            else:
                print(f"✅ Product Specs Extracted!")
                print(f"🏭 Model: {extracted_data.get('model_number', 'Unknown')}")
                print(f"📊 Series: {extracted_data.get('series_name', 'Unknown')}")
                print(f"🖨️ Type: {extracted_data.get('product_type', 'Unknown')}")
                print(f"⚡ Speed Mono: {extracted_data.get('speed_mono', 'N/A')} ppm")
                print(f"🌈 Speed Color: {extracted_data.get('speed_color', 'N/A')} ppm")
                print(f"📏 Resolution: {extracted_data.get('resolution', 'N/A')}")
                print(f"📊 Confidence: {confidence:.2f}")
                print(f"🤖 LLM Provider: {llm_used}")
                print(f"⏱️ Duration: {duration:.2f}s")
                
                print(f"\n--- Extracted Data (JSON) ---")
                print(json.dumps(extracted_data, indent=2))
            
            # Validate confidence
            validate_extraction_confidence({'confidence': confidence}, confidence_threshold=0.7)
            
            return {
                'success': True,
                'data': extracted_data,
                'duration': duration,
                'confidence': confidence,
                'llm_provider': llm_used,
                'extraction_type': extraction_type,
                'schema_version': schema_version,
                'record_id': record_id
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            
            if RICH_AVAILABLE and console:
                error_panel = Panel(
                    f"❌ **Extraction Failed**\n"
                    f"🚨 Error: {error_msg}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="red"
                )
                console.print(error_panel)
            else:
                print(f"❌ Extraction Failed!")
                print(f"🚨 Error: {error_msg}")
                print(f"⏱️ Duration: {duration:.2f}s")
            
            return {
                'success': False,
                'error': error_msg,
                'duration': duration
            }
            
    except FirecrawlUnavailableError as e:
        if RICH_AVAILABLE and console:
            error_panel = Panel(
                f"⚠️ **Firecrawl Unavailable**\n"
                f"💡 Structured extraction requires Firecrawl with LLM support\n"
                f"🔧 Try: docker-compose up -d krai-redis krai-playwright krai-firecrawl-api krai-firecrawl-worker",
                title="Backend Error",
                border_style="yellow"
            )
            console.print(error_panel)
        else:
            print("⚠️ Firecrawl Unavailable")
            print("💡 Structured extraction requires Firecrawl with LLM support")
            print("🔧 Try: docker-compose up -d krai-redis krai-playwright krai-firecrawl-api krai-firecrawl-worker")
        
        return {
            'success': False,
            'error': str(e),
            'suggestion': 'Firecrawl with LLM support is required for structured extraction'
        }
        
    except Exception as e:
        if RICH_AVAILABLE and console:
            error_panel = Panel(
                f"❌ **Unexpected Error**\n"
                f"🚨 {str(e)}\n"
                f"💡 Check URL, LLM configuration, and Firecrawl services",
                title="Error",
                border_style="red"
            )
            console.print(error_panel)
        else:
            print(f"❌ Unexpected Error: {str(e)}")
            print("💡 Check URL, LLM configuration, and Firecrawl services")
        
        return {
            'success': False,
            'error': str(e)
        }


async def extract_error_codes(url: str, llm_provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract error codes from a URL.
    
    Args:
        url: URL to extract error codes from
        llm_provider: Force specific LLM provider
    
    Returns:
        Dictionary with extraction results
    """
    start_time = time.time()
    
    try:
        # Create services
        scraping_service = create_web_scraping_service(backend='firecrawl')
        
        class MockDatabaseService:
            async def insert_structured_extraction(self, data):
                return True
        
        db_service = MockDatabaseService()
        extraction_service = StructuredExtractionService(
            web_scraping_service=scraping_service,
            database_service=db_service
        )
        
        print_with_rich(f"⚠️ Extracting error codes from: {url}")
        
        # Perform extraction
        result = await extraction_service.extract_error_codes(url)
        duration = time.time() - start_time
        
        if result.get('success', False):
            extracted_data = result.get('extracted_data', {})
            confidence = result.get('confidence', 0.0)
            
            # Get additional fields from result if available
            extraction_type = result.get('extraction_type', 'unknown')
            schema_version = result.get('schema_version', 'unknown')
            record_id = result.get('record_id', 'unknown')
            llm_used = result.get('llm_provider', 'unknown')
            
            error_codes = extracted_data.get('error_codes', [])
            
            # Display extraction results
            if RICH_AVAILABLE and console:
                success_panel = Panel(
                    f"✅ **Error Codes Extracted**\n"
                    f"📊 Total Codes: {len(error_codes)}\n"
                    f"📊 Confidence: {confidence:.2f}\n"
                    f"🤖 LLM Provider: {llm_used}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="green"
                )
                console.print(success_panel)
                
                # Display error codes table
                if error_codes:
                    error_table = Table(title="🚨 Extracted Error Codes")
                    error_table.add_column("Code", style="cyan")
                    error_table.add_column("Description", style="white")
                    error_table.add_column("Severity", style="yellow")
                    error_table.add_column("Requires Tech", style="red")
                    
                    for error in error_codes[:10]:  # Show first 10
                        error_table.add_row(
                            error.get('code', 'N/A'),
                            error.get('description', 'N/A')[:50] + ('...' if len(error.get('description', '')) > 50 else ''),
                            error.get('severity', 'N/A'),
                            'Yes' if error.get('requires_technician') else 'No'
                        )
                    
                    if len(error_codes) > 10:
                        error_table.add_row("...", f"and {len(error_codes) - 10} more", "", "")
                    
                    console.print(error_table)
            else:
                print(f"✅ Error Codes Extracted!")
                print(f"📊 Total Codes: {len(error_codes)}")
                print(f"📊 Confidence: {confidence:.2f}")
                print(f"🤖 LLM Provider: {llm_used}")
                print(f"⏱️ Duration: {duration:.2f}s")
                
                if error_codes:
                    print(f"\n--- Extracted Error Codes ---")
                    for i, error in enumerate(error_codes[:5], 1):
                        print(f"{i}. {error.get('code', 'N/A')}: {error.get('description', 'N/A')}")
                    if len(error_codes) > 5:
                        print(f"... and {len(error_codes) - 5} more")
            
            # Validate confidence
            validate_extraction_confidence({'confidence': confidence}, confidence_threshold=0.7)
            
            return {
                'success': True,
                'data': extracted_data,
                'duration': duration,
                'confidence': confidence,
                'llm_provider': llm_used,
                'extraction_type': extraction_type,
                'schema_version': schema_version,
                'record_id': record_id,
                'error_codes_count': len(error_codes)
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            
            if RICH_AVAILABLE and console:
                error_panel = Panel(
                    f"❌ **Extraction Failed**\n"
                    f"🚨 Error: {error_msg}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="red"
                )
                console.print(error_panel)
            else:
                print(f"❌ Extraction Failed!")
                print(f"🚨 Error: {error_msg}")
                print(f"⏱️ Duration: {duration:.2f}s")
            
            return {
                'success': False,
                'error': error_msg,
                'duration': duration
            }
            
    except Exception as e:
        print_with_rich(f"❌ Error extracting error codes: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


async def extract_service_manual_metadata(url: str, llm_provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract service manual metadata from a URL.
    
    Args:
        url: URL to extract manual metadata from
        llm_provider: Force specific LLM provider
    
    Returns:
        Dictionary with extraction results
    """
    start_time = time.time()
    
    try:
        # Create services
        scraping_service = create_web_scraping_service(backend='firecrawl')
        
        class MockDatabaseService:
            async def insert_structured_extraction(self, data):
                return True
        
        db_service = MockDatabaseService()
        extraction_service = StructuredExtractionService(
            web_scraping_service=scraping_service,
            database_service=db_service
        )
        
        print_with_rich(f"📚 Extracting manual metadata from: {url}")
        
        # Perform extraction
        result = await extraction_service.extract_service_manual_metadata(url)
        duration = time.time() - start_time
        
        if result.get('success', False):
            extracted_data = result.get('extracted_data', {})
            confidence = result.get('confidence', 0.0)
            
            # Get additional fields from result if available
            extraction_type = result.get('extraction_type', 'unknown')
            schema_version = result.get('schema_version', 'unknown')
            record_id = result.get('record_id', 'unknown')
            llm_used = result.get('llm_provider', 'unknown')
            
            # Display extraction results
            if RICH_AVAILABLE and console:
                success_panel = Panel(
                    f"✅ **Manual Metadata Extracted**\n"
                    f"📚 Type: {extracted_data.get('manual_type', 'Unknown')}\n"
                    f"🏭 Products: {', '.join(extracted_data.get('product_models', []))}\n"
                    f"📄 Pages: {extracted_data.get('page_count', 'N/A')}\n"
                    f"📅 Published: {extracted_data.get('publication_date', 'N/A')}\n"
                    f"📊 Confidence: {confidence:.2f}\n"
                    f"🤖 LLM Provider: {llm_used}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="green"
                )
                console.print(success_panel)
                
                # Display full extracted data
                json_panel = Panel(
                    JSON.from_data(extracted_data, indent=2),
                    title="Manual Metadata (JSON)",
                    border_style="blue"
                )
                console.print(json_panel)
            else:
                print(f"✅ Manual Metadata Extracted!")
                print(f"📚 Type: {extracted_data.get('manual_type', 'Unknown')}")
                print(f"🏭 Products: {', '.join(extracted_data.get('product_models', []))}")
                print(f"📄 Pages: {extracted_data.get('page_count', 'N/A')}")
                print(f"📅 Published: {extracted_data.get('publication_date', 'N/A')}")
                print(f"📊 Confidence: {confidence:.2f}")
                print(f"🤖 LLM Provider: {llm_used}")
                print(f"⏱️ Duration: {duration:.2f}s")
                
                print(f"\n--- Manual Metadata (JSON) ---")
                print(json.dumps(extracted_data, indent=2))
            
            return {
                'success': True,
                'data': extracted_data,
                'duration': duration,
                'confidence': confidence,
                'llm_provider': llm_used,
                'extraction_type': extraction_type,
                'schema_version': schema_version,
                'record_id': record_id
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            
            if RICH_AVAILABLE and console:
                error_panel = Panel(
                    f"❌ **Extraction Failed**\n"
                    f"🚨 Error: {error_msg}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="red"
                )
                console.print(error_panel)
            else:
                print(f"❌ Extraction Failed!")
                print(f"🚨 Error: {error_msg}")
                print(f"⏱️ Duration: {duration:.2f}s")
            
            return {
                'success': False,
                'error': error_msg,
                'duration': duration
            }
            
    except Exception as e:
        print_with_rich(f"❌ Error extracting manual metadata: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


async def extract_with_custom_schema(url: str, schema: Dict[str, Any], llm_provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract data using a custom JSON schema.
    
    Args:
        url: URL to extract from
        schema: Custom JSON schema
        llm_provider: Force specific LLM provider
    
    Returns:
        Dictionary with extraction results
    """
    start_time = time.time()
    
    try:
        # Create scraping service
        scraping_service = create_web_scraping_service(backend='firecrawl')
        
        print_with_rich(f"🔧 Extracting with custom schema from: {url}")
        
        # Perform extraction
        result = await scraping_service.extract_structured_data(url, schema)
        duration = time.time() - start_time
        
        if result.get('success', False):
            extracted_data = result.get('data', {})
            metadata = result.get('metadata', {})
            confidence = metadata.get('confidence', 0.0)
            llm_used = metadata.get('llm_provider', 'unknown')
            
            # Display extraction results
            if RICH_AVAILABLE and console:
                success_panel = Panel(
                    f"✅ **Custom Schema Extraction Successful**\n"
                    f"📊 Confidence: {confidence:.2f}\n"
                    f"🤖 LLM Provider: {llm_used}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="green"
                )
                console.print(success_panel)
                
                # Display extracted data
                json_panel = Panel(
                    JSON.from_data(extracted_data, indent=2),
                    title="Custom Extracted Data (JSON)",
                    border_style="blue"
                )
                console.print(json_panel)
            else:
                print(f"✅ Custom Schema Extraction Successful!")
                print(f"📊 Confidence: {confidence:.2f}")
                print(f"🤖 LLM Provider: {llm_used}")
                print(f"⏱️ Duration: {duration:.2f}s")
                
                print(f"\n--- Custom Extracted Data (JSON) ---")
                print(json.dumps(extracted_data, indent=2))
            
            return {
                'success': True,
                'data': extracted_data,
                'metadata': metadata,
                'duration': duration,
                'confidence': confidence,
                'llm_provider': llm_used
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            
            if RICH_AVAILABLE and console:
                error_panel = Panel(
                    f"❌ **Custom Extraction Failed**\n"
                    f"🚨 Error: {error_msg}\n"
                    f"⏱️ Duration: {duration:.2f}s",
                    title="Extraction Results",
                    border_style="red"
                )
                console.print(error_panel)
            else:
                print(f"❌ Custom Extraction Failed!")
                print(f"🚨 Error: {error_msg}")
                print(f"⏱️ Duration: {duration:.2f}s")
            
            return {
                'success': False,
                'error': error_msg,
                'duration': duration
            }
            
    except Exception as e:
        print_with_rich(f"❌ Error with custom schema extraction: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


async def batch_extract_from_urls(urls: List[str], extraction_type: str, llm_provider: Optional[str] = None, max_concurrent: int = 2) -> Dict[str, Any]:
    """
    Process multiple URLs concurrently for batch extraction.
    
    Args:
        urls: List of URLs to extract from
        extraction_type: Type of extraction (product_specs, error_codes, service_manual)
        llm_provider: Force specific LLM provider
        max_concurrent: Maximum concurrent extractions (LLM is slow)
    
    Returns:
        Dictionary with batch extraction results
    """
    print_with_rich(f"🚀 Starting batch extraction for {len(urls)} URLs")
    print_with_rich(f"📊 Type: {extraction_type}, Max Concurrent: {max_concurrent}")
    
    # Extraction function mapping
    extraction_functions = {
        'product_specs': extract_product_specs,
        'error_codes': extract_error_codes,
        'service_manual': extract_service_manual_metadata
    }
    
    if extraction_type not in extraction_functions:
        return {
            'success': False,
            'error': f"Unknown extraction type: {extraction_type}. Available: {list(extraction_functions.keys())}"
        }
    
    extract_func = extraction_functions[extraction_type]
    
    # Create semaphore to limit concurrent extractions
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_with_semaphore(url: str):
        async with semaphore:
            return await extract_func(url, llm_provider)
    
    # Process URLs with progress tracking
    start_time = time.time()
    
    if RICH_AVAILABLE and console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Extracting from URLs...", total=len(urls))
            
            # Create tasks for all URLs
            tasks = []
            for url in urls:
                task_coro = extract_with_semaphore(url)
                task_future = asyncio.create_task(task_coro)
                tasks.append((url, task_future))
            
            # Process results as they complete
            results = []
            for url, task_future in tasks:
                try:
                    result = await task_future
                    results.append((url, result))
                    progress.advance(task, 1)
                except Exception as e:
                    results.append((url, {'success': False, 'error': str(e)}))
                    progress.advance(task, 1)
    else:
        print("🚀 Extracting from URLs...")
        results = []
        for url in urls:
            try:
                result = await extract_with_semaphore(url)
                results.append((url, result))
                print(f"  ✅ Processed: {url}")
            except Exception as e:
                results.append((url, {'success': False, 'error': str(e)}))
                print(f"  ❌ Failed: {url} - {str(e)}")
    
    duration = time.time() - start_time
    
    # Analyze results
    successful = sum(1 for _, result in results if result.get('success', False))
    failed = len(results) - successful
    avg_confidence = 0.0
    
    if successful > 0:
        confidences = [result.get('confidence', 0.0) for _, result in results if result.get('success', False)]
        avg_confidence = sum(confidences) / len(confidences)
    
    # Display batch results
    if RICH_AVAILABLE and console:
        batch_panel = Panel(
            f"✅ **Batch Extraction Complete**\n"
            f"📊 Total URLs: {len(urls)}\n"
            f"✅ Successful: {successful}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Average Confidence: {avg_confidence:.2f}\n"
            f"⏱️ Total Duration: {duration:.2f}s\n"
            f"📊 Average per URL: {duration/len(urls):.2f}s",
            title="Batch Results",
            border_style="green" if successful == len(urls) else "yellow"
        )
        console.print(batch_panel)
    else:
        print(f"\n✅ Batch Extraction Complete!")
        print(f"📊 Total URLs: {len(urls)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Average Confidence: {avg_confidence:.2f}")
        print(f"⏱️ Total Duration: {duration:.2f}s")
        print(f"📊 Average per URL: {duration/len(urls):.2f}s")
    
    return {
        'success': True,
        'total_urls': len(urls),
        'successful': successful,
        'failed': failed,
        'average_confidence': avg_confidence,
        'duration': duration,
        'results': results
    }


def validate_extraction_confidence(result: Dict[str, Any], threshold: float = 0.7) -> bool:
    """
    Validate if extraction confidence meets threshold.
    
    Args:
        result: Extraction result
        threshold: Minimum confidence threshold
    
    Returns:
        True if confidence is acceptable, False otherwise
    """
    confidence = result.get('confidence', 0.0)
    
    if confidence < threshold:
        if RICH_AVAILABLE and console:
            warning_panel = Panel(
                f"⚠️ **Low Confidence Extraction**\n"
                f"📊 Confidence: {confidence:.2f} (threshold: {threshold:.2f})\n"
                f"💡 Suggestion: Manual verification recommended\n"
                f"🔧 Try: Use OpenAI LLM provider for better quality",
                title="Confidence Warning",
                border_style="yellow"
            )
            console.print(warning_panel)
        else:
            print(f"⚠️ Low Confidence Extraction: {confidence:.2f} (threshold: {threshold:.2f})")
            print("💡 Suggestion: Manual verification recommended")
            print("🔧 Try: Use OpenAI LLM provider for better quality")
        
        return False
    else:
        if RICH_AVAILABLE and console:
            success_panel = Panel(
                f"✅ **High Confidence Extraction**\n"
                f"📊 Confidence: {confidence:.2f} (threshold: {threshold:.2f})",
                title="Confidence OK",
                border_style="green"
            )
            console.print(success_panel)
        else:
            print(f"✅ High Confidence Extraction: {confidence:.2f} (threshold: {threshold:.2f})")
        
        return True


def load_custom_schema(schema_path: str) -> Dict[str, Any]:
    """Load custom JSON schema from file."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate schema format
        if not isinstance(schema, dict) or 'type' not in schema:
            raise ValueError("Invalid schema format: must be a JSON Schema object")
        
        return schema
        
    except FileNotFoundError:
        print_with_rich(f"❌ Schema file not found: {schema_path}")
        return {}
    except json.JSONDecodeError as e:
        print_with_rich(f"❌ Invalid JSON in schema file: {e}")
        return {}
    except Exception as e:
        print_with_rich(f"❌ Error loading schema: {e}")
        return {}


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Structured data extraction example using Firecrawl's LLM-based extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url https://example.com/product --type product_specs
  %(prog)s --url https://example.com/support --type error_codes
  %(prog)s --url https://example.com --schema custom_schema.json
  %(prog)s --batch urls.txt --type product_specs --export results.json
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--url',
        type=str,
        help='URL to extract from'
    )
    input_group.add_argument(
        '--batch',
        type=str,
        help='File with list of URLs for batch processing'
    )
    
    # Extraction options
    parser.add_argument(
        '--type',
        choices=['product_specs', 'error_codes', 'service_manual'],
        help='Type of extraction to perform'
    )
    
    parser.add_argument(
        '--schema',
        type=str,
        help='Path to custom JSON schema file'
    )
    
    parser.add_argument(
        '--llm-provider',
        choices=['ollama', 'openai'],
        help='Force specific LLM provider'
    )
    
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.7,
        help='Minimum confidence threshold (default: 0.7)'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Export results to file'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.url and not args.type and not args.schema:
        parser.error("--type or --schema is required when using --url")
    
    if args.batch and not args.type:
        parser.error("--type is required when using --batch")
    
    if args.type and args.schema:
        parser.error("--type and --schema are mutually exclusive")
    
    # Load configuration
    config = load_extraction_configuration()
    
    # Run the extraction operation
    async def run_extraction():
        if args.url:
            # Single URL extraction
            if args.schema:
                # Custom schema extraction
                schema = load_custom_schema(args.schema)
                if not schema:
                    return {'success': False, 'error': 'Failed to load custom schema'}
                
                result = await extract_with_custom_schema(
                    args.url, 
                    schema, 
                    args.llm_provider
                )
            else:
                # Predefined schema extraction
                extraction_functions = {
                    'product_specs': extract_product_specs,
                    'error_codes': extract_error_codes,
                    'service_manual': extract_service_manual_metadata
                }
                
                extract_func = extraction_functions[args.type]
                result = await extract_func(args.url, args.llm_provider)
        
        elif args.batch:
            # Batch extraction
            try:
                with open(args.batch, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except FileNotFoundError:
                return {'success': False, 'error': f'Batch file not found: {args.batch}'}
            
            if not urls:
                return {'success': False, 'error': 'No URLs found in batch file'}
            
            result = await batch_extract_from_urls(
                urls, 
                args.type, 
                args.llm_provider
            )
        
        # Validate confidence
        if result.get('success') and 'confidence' in result:
            validate_extraction_confidence(result, args.confidence_threshold)
        
        # Export results
        if args.export and result.get('success'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = args.export if args.export.endswith('.json') else f"{args.export}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print_with_rich(f"💾 Results exported to: {filename}")
            result['export_filename'] = filename
        
        return result
    
    # Execute operation
    try:
        result = asyncio.run(run_extraction())
        return result
        
    except KeyboardInterrupt:
        print_with_rich("\n⚠️ Extraction cancelled by user")
        return None
    except Exception as e:
        print_with_rich(f"❌ Fatal error: {str(e)}")
        return None


if __name__ == '__main__':
    main()
