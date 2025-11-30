#!/usr/bin/env python3
"""
KRAI Test Environment Setup Script

This script configures and initializes a dedicated test environment
with complete isolation from production systems.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.database_service import DatabaseService
from services.storage_service import StorageService
from services.ai_service import AIService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestEnvironmentSetup:
    """Setup and manage isolated test environment"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        self.storage_service = StorageService()
        self.ai_service = AIService()
        
        # Test configuration
        self.test_buckets = [
            'test-documents',
            'test-images', 
            'test-videos',
            'test-tables',
            'test-temp'
        ]
        
    async def initialize_services(self):
        """Initialize all test services"""
        logger.info("🚀 Initializing KRAI Test Environment...")
        
        try:
            # Initialize database
            logger.info("📊 Initializing test database...")
            await self.database_service.initialize()
            
            # Initialize storage
            logger.info("📦 Initializing test storage...")
            await self.storage_service.initialize()
            
            # Initialize AI service
            logger.info("🤖 Initializing test AI service...")
            await self.ai_service.initialize()
            
            logger.info("✅ All services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return False
    
    async def setup_test_database(self):
        """Setup test database with test schema"""
        logger.info("📊 Setting up test database...")
        
        try:
            # Apply migrations
            logger.info("🔄 Applying database migrations...")
            from scripts.apply_migrations import apply_migrations
            await apply_migrations()
            
            # Create test schema if needed
            await self.database_service.execute_query("""
                CREATE SCHEMA IF NOT EXISTS krai_test;
                SET search_path TO krai_test, public;
            """)
            
            logger.info("✅ Test database setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False
    
    async def setup_test_storage(self):
        """Setup test storage buckets"""
        logger.info("📦 Setting up test storage buckets...")
        
        try:
            # Create test buckets
            for bucket in self.test_buckets:
                logger.info(f"📁 Creating bucket: {bucket}")
                await self.storage_service.create_bucket(bucket)
            
            # Verify buckets exist
            buckets = await self.storage_service.list_buckets()
            test_buckets_found = [b for b in buckets if b.startswith('test-')]
            
            logger.info(f"✅ Created {len(test_buckets_found)} test buckets")
            return True
            
        except Exception as e:
            logger.error(f"❌ Storage setup failed: {e}")
            return False
    
    async def setup_test_ai_models(self):
        """Setup test AI models"""
        logger.info("🤖 Setting up test AI models...")
        
        try:
            # Check available models
            models = await self.ai_service.list_models()
            logger.info(f"📋 Available models: {models}")
            
            # Pull required models if not available
            required_models = ['nomic-embed-text:latest', 'llama3.2:latest']
            
            for model in required_models:
                if model not in models:
                    logger.info(f"⬇️ Pulling model: {model}")
                    await self.ai_service.pull_model(model)
                else:
                    logger.info(f"✅ Model already available: {model}")
            
            logger.info("✅ Test AI models setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ AI models setup failed: {e}")
            return False
    
    async def create_test_data_directories(self):
        """Create test data directories"""
        logger.info("📁 Creating test data directories...")
        
        try:
            test_dirs = [
                'tests/fixtures/documents',
                'tests/fixtures/images', 
                'tests/fixtures/videos',
                'tests/fixtures/tables',
                'test_logs',
                'test_temp'
            ]
            
            for dir_path in test_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Created directory: {dir_path}")
            
            logger.info("✅ Test data directories created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Directory creation failed: {e}")
            return False
    
    async def verify_test_environment(self):
        """Verify test environment is ready"""
        logger.info("🔍 Verifying test environment...")
        
        verification_results = {}
        
        try:
            # Test database connection
            logger.info("📊 Testing database connection...")
            db_health = await self.database_service.health_check()
            verification_results['database'] = db_health.get('status') == 'healthy'
            
            # Test storage connection
            logger.info("📦 Testing storage connection...")
            storage_health = await self.storage_service.health_check()
            verification_results['storage'] = storage_health.get('status') == 'healthy'
            
            # Test AI service connection
            logger.info("🤖 Testing AI service connection...")
            ai_health = await self.ai_service.health_check()
            verification_results['ai_service'] = ai_health.get('status') == 'healthy'
            
            # Test feature flags
            logger.info("🚩 Testing feature flags...")
            features = {
                'ENABLE_HIERARCHICAL_CHUNKING': os.getenv('ENABLE_HIERARCHICAL_CHUNKING', 'false'),
                'ENABLE_SVG_EXTRACTION': os.getenv('ENABLE_SVG_EXTRACTION', 'false'),
                'ENABLE_MULTIMODAL_SEARCH': os.getenv('ENABLE_MULTIMODAL_SEARCH', 'false'),
                'ENABLE_CONTEXT_EXTRACTION': os.getenv('ENABLE_CONTEXT_EXTRACTION', 'false')
            }
            verification_results['features'] = features
            
            # Overall status
            all_healthy = all(verification_results.values())
            verification_results['overall'] = all_healthy
            
            if all_healthy:
                logger.info("🎉 Test environment verification successful!")
            else:
                logger.warning(f"⚠️ Test environment has issues: {verification_results}")
            
            return verification_results
            
        except Exception as e:
            logger.error(f"❌ Environment verification failed: {e}")
            return {'overall': False, 'error': str(e)}
    
    async def run_full_setup(self):
        """Run complete test environment setup"""
        logger.info("🚀 Starting full test environment setup...")
        
        setup_steps = [
            ("Services", self.initialize_services),
            ("Database", self.setup_test_database),
            ("Storage", self.setup_test_storage),
            ("AI Models", self.setup_test_ai_models),
            ("Directories", self.create_test_data_directories),
            ("Verification", self.verify_test_environment)
        ]
        
        results = {}
        
        for step_name, step_func in setup_steps:
            logger.info(f"🔄 Running setup step: {step_name}")
            try:
                result = await step_func()
                results[step_name] = result
                if result:
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.error(f"❌ {step_name} failed")
            except Exception as e:
                logger.error(f"❌ {step_name} failed with exception: {e}")
                results[step_name] = False
        
        # Summary
        successful_steps = sum(1 for result in results.values() if result)
        total_steps = len(results)
        
        logger.info(f"📊 Setup Summary: {successful_steps}/{total_steps} steps completed")
        
        if successful_steps == total_steps:
            logger.info("🎉 Test environment setup completed successfully!")
            return True
        else:
            logger.error(f"❌ Test environment setup incomplete. Failed steps: {[k for k, v in results.items() if not v]}")
            return False

async def main():
    """Main setup function"""
    setup = TestEnvironmentSetup()
    
    try:
        success = await setup.run_full_setup()
        
        if success:
            logger.info("🎉 Test environment is ready for testing!")
            logger.info("📝 You can now run tests with:")
            logger.info("   python -m pytest tests/ -v")
            logger.info("   python scripts/test_full_pipeline_phases_1_6.py")
            sys.exit(0)
        else:
            logger.error("❌ Test environment setup failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
