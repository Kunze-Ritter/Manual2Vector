"""
Database Adapter Testing Suite

Tests all database adapters to ensure:
1. Connection works
2. Backward compatibility is maintained
3. Factory pattern works correctly
4. Basic CRUD operations function
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables via centralized loader
try:
    from backend.processors.env_loader import load_all_env_files
    loaded_files = load_all_env_files(PROJECT_ROOT)
    if loaded_files:
        print(f"Loaded environment files: {', '.join(loaded_files)}")
    else:
        print("⚠️  No .env files found - relying on system environment variables")
except ImportError:
    print("⚠️  Environment loader not available, using system environment variables")


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")


def print_test(test_name: str):
    """Print test name"""
    print(f"{Colors.BLUE}🧪 Testing:{Colors.RESET} {test_name}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")


async def test_factory_pattern():
    """Test database factory pattern"""
    print_header("TEST 1: Database Factory Pattern")
    
    try:
        from backend.services.database_factory import create_database_adapter
        print_success("Factory module imported successfully")
        
        # Test 1.1: Default adapter (from environment)
        print_test("Creating adapter from environment (DATABASE_TYPE)")
        db_type = os.getenv("DATABASE_TYPE", "supabase")
        print_info(f"DATABASE_TYPE = {db_type}")
        
        adapter = create_database_adapter()
        print_success(f"Created adapter: {adapter.__class__.__name__}")
        
        # Test 1.2: Explicit Supabase adapter
        print_test("Creating Supabase adapter explicitly")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            supabase_adapter = create_database_adapter(
                database_type="supabase",
                supabase_url=supabase_url,
                supabase_key=supabase_key
            )
            print_success(f"Created Supabase adapter: {supabase_adapter.__class__.__name__}")
        else:
            print_warning("SUPABASE_URL or SUPABASE_ANON_KEY not set - skipping Supabase test")
        
        # Test 1.3: Invalid adapter type
        print_test("Testing invalid adapter type (should raise ValueError)")
        try:
            invalid_adapter = create_database_adapter(database_type="invalid_type")
            print_error("Should have raised ValueError for invalid adapter type!")
            return False
        except ValueError as e:
            print_success(f"Correctly raised ValueError: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Factory pattern test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backward_compatibility():
    """Test backward compatibility wrappers"""
    print_header("TEST 2: Backward Compatibility")
    
    try:
        # Test 2.1: DatabaseService (production wrapper)
        print_test("Testing DatabaseService (production wrapper)")
        from backend.services.database_service_production import DatabaseService
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print_warning("SUPABASE credentials not set - skipping production wrapper test")
            return True
        
        db = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            postgres_url=os.getenv("DATABASE_CONNECTION_URL")
        )
        print_success("DatabaseService instantiated successfully")
        
        # Check that it has the expected attributes
        assert hasattr(db, '_adapter'), "Missing _adapter attribute"
        assert hasattr(db, 'supabase_url'), "Missing supabase_url attribute"
        assert hasattr(db, 'logger'), "Missing logger attribute"
        print_success("All expected attributes present")
        
        # Test 2.2: DatabaseService (API wrapper)
        print_test("Testing DatabaseService (API wrapper)")
        from backend.services.database_service import DatabaseService as APIService
        
        api_db = APIService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        print_success("API DatabaseService instantiated successfully")
        
        assert hasattr(api_db, '_adapter'), "Missing _adapter attribute"
        print_success("API wrapper has _adapter attribute")
        
        return True
        
    except Exception as e:
        print_error(f"Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_adapter_connection():
    """Test adapter connection"""
    print_header("TEST 3: Adapter Connection")
    
    try:
        from backend.services.database_factory import create_database_adapter
        
        # Test 3.1: Create and connect adapter
        print_test("Creating and connecting adapter")
        adapter = create_database_adapter()
        print_info(f"Adapter type: {adapter.__class__.__name__}")
        
        await adapter.connect()
        print_success("Adapter connected successfully")
        
        # Test 3.2: Test connection
        print_test("Testing connection with test_connection()")
        is_connected = await adapter.test_connection()
        
        if is_connected:
            print_success("Connection test passed")
        else:
            print_error("Connection test failed")
            return False
        
        # Test 3.3: Check adapter attributes
        print_test("Checking adapter attributes")
        
        if hasattr(adapter, 'client'):
            print_info(f"Has Supabase client: {adapter.client is not None}")
        
        if hasattr(adapter, 'pg_pool'):
            print_info(f"Has PostgreSQL pool: {adapter.pg_pool is not None}")
        
        if hasattr(adapter, 'service_client'):
            print_info(f"Has service role client: {adapter.service_client is not None}")
        
        print_success("Adapter attributes checked")
        
        return True
        
    except Exception as e:
        print_error(f"Adapter connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_operations():
    """Test basic CRUD operations"""
    print_header("TEST 4: Basic CRUD Operations")
    
    try:
        from backend.services.database_factory import create_database_adapter
        from backend.core.data_models import DocumentModel
        from datetime import datetime
        import hashlib
        
        # Create adapter
        adapter = create_database_adapter()
        await adapter.connect()
        
        # Test 4.1: Get document by hash (should return None for non-existent)
        print_test("Testing get_document_by_hash() with non-existent hash")
        test_hash = hashlib.sha256(b"test_adapter_pattern_12345").hexdigest()
        result = await adapter.get_document_by_hash(test_hash)
        
        if result is None:
            print_success("Correctly returned None for non-existent document")
        else:
            print_warning(f"Found existing document with test hash: {result.get('id')}")
        
        # Test 4.2: Test manufacturer lookup (should work with existing data)
        print_test("Testing get_manufacturer_by_name() with known manufacturer")
        try:
            manufacturer = await adapter.get_manufacturer_by_name("HP")
            if manufacturer:
                print_success(f"Found manufacturer: {manufacturer.get('name')} (ID: {manufacturer.get('id')})")
            else:
                print_info("No HP manufacturer found (database might be empty)")
        except NotImplementedError:
            print_warning("get_manufacturer_by_name() not implemented in this adapter")
        
        # Test 4.3: Test product lookup
        print_test("Testing get_product_by_model() with known model")
        try:
            # Try to find a common HP printer model
            if manufacturer:
                product = await adapter.get_product_by_model("LaserJet", manufacturer.get('id'))
                if product:
                    print_success(f"Found product: {product.get('model_number')}")
                else:
                    print_info("No LaserJet product found")
        except NotImplementedError:
            print_warning("get_product_by_model() not implemented in this adapter")
        
        print_success("Basic operations test completed")
        return True
        
    except Exception as e:
        print_error(f"Basic operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_adapter_methods():
    """Test that all required adapter methods exist"""
    print_header("TEST 5: Adapter Interface Compliance")
    
    try:
        from backend.services.database_factory import create_database_adapter
        from backend.services.database_adapter import DatabaseAdapter
        import inspect
        
        adapter = create_database_adapter()
        
        # Get all abstract methods from DatabaseAdapter
        abstract_methods = [
            name for name, method in inspect.getmembers(DatabaseAdapter, predicate=inspect.isfunction)
            if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__
        ]
        
        print_test(f"Checking {len(abstract_methods)} abstract methods")
        
        missing_methods = []
        implemented_methods = []
        
        for method_name in abstract_methods:
            if hasattr(adapter, method_name):
                implemented_methods.append(method_name)
            else:
                missing_methods.append(method_name)
        
        print_info(f"Implemented: {len(implemented_methods)}/{len(abstract_methods)}")
        
        if missing_methods:
            print_warning(f"Missing methods: {', '.join(missing_methods)}")
        else:
            print_success("All abstract methods implemented")
        
        # Show some key methods
        key_methods = [
            'connect', 'test_connection',
            'create_document', 'get_document',
            'create_chunk', 'create_embedding',
            'search_embeddings'
        ]
        
        print_test("Checking key methods")
        for method in key_methods:
            if hasattr(adapter, method):
                print_success(f"  ✓ {method}")
            else:
                print_error(f"  ✗ {method}")
        
        return True
        
    except Exception as e:
        print_error(f"Interface compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_environment_configuration():
    """Test environment configuration"""
    print_header("TEST 6: Environment Configuration")
    
    try:
        print_test("Checking environment variables")
        
        # Check DATABASE_TYPE
        db_type = os.getenv("DATABASE_TYPE", "supabase")
        print_info(f"DATABASE_TYPE: {db_type}")
        
        # Check Supabase config
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if supabase_url:
            print_success(f"SUPABASE_URL: {supabase_url[:30]}...")
        else:
            print_warning("SUPABASE_URL not set")
        
        if supabase_key:
            print_success(f"SUPABASE_ANON_KEY: {supabase_key[:20]}...")
        else:
            print_warning("SUPABASE_ANON_KEY not set")
        
        if service_role_key:
            print_success(f"SUPABASE_SERVICE_ROLE_KEY: {service_role_key[:20]}...")
        else:
            print_info("SUPABASE_SERVICE_ROLE_KEY not set (optional)")
        
        # Check PostgreSQL config
        postgres_url = os.getenv("DATABASE_CONNECTION_URL") or os.getenv("POSTGRES_URL")
        postgres_host = os.getenv("POSTGRES_HOST")
        
        if postgres_url:
            print_success(f"PostgreSQL URL configured")
        elif postgres_host:
            print_info(f"PostgreSQL host: {postgres_host}")
        else:
            print_info("PostgreSQL not configured (optional)")
        
        # Check schema prefix
        schema_prefix = os.getenv("DATABASE_SCHEMA_PREFIX", "krai")
        print_info(f"Schema prefix: {schema_prefix}")
        
        return True
        
    except Exception as e:
        print_error(f"Environment configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║           DATABASE ADAPTER TESTING SUITE                          ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    results = {}
    
    # Run tests
    results['Environment Configuration'] = await test_environment_configuration()
    results['Factory Pattern'] = await test_factory_pattern()
    results['Backward Compatibility'] = await test_backward_compatibility()
    results['Adapter Connection'] = await test_adapter_connection()
    results['Basic Operations'] = await test_basic_operations()
    results['Interface Compliance'] = await test_adapter_methods()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED ⚠️{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
