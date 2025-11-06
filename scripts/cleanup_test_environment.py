#!/usr/bin/env python3
"""
KRAI Test Environment Cleanup Script

This script cleans up the test environment after testing is complete,
removing test data and resetting the environment for the next test run.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import shutil

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.database_service import DatabaseService
from services.storage_service import StorageService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestEnvironmentCleanup:
    """Cleanup and reset test environment"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        self.storage_service = StorageService()
        
        # Test buckets to clean
        self.test_buckets = [
            'test-documents',
            'test-images', 
            'test-videos',
            'test-tables',
            'test-temp'
        ]
        
        # Test directories to clean
        self.test_directories = [
            'test_logs',
            'test_temp',
            'tests/fixtures/documents',
            'tests/fixtures/images',
            'tests/fixtures/videos'
        ]
    
    async def initialize_services(self):
        """Initialize services for cleanup"""
        logger.info("🔧 Initializing cleanup services...")
        
        try:
            await self.database_service.initialize()
            await self.storage_service.initialize()
            logger.info("✅ Cleanup services initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return False
    
    async def cleanup_test_database(self):
        """Clean up test database data"""
        logger.info("📊 Cleaning up test database...")
        
        try:
            # Get all KRAI schemas
            schemas_query = """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'krai_%' OR schema_name = 'krai_test'
            """
            schemas = await self.database_service.fetch_query(schemas_query)
            
            cleaned_tables = 0
            
            for schema_record in schemas:
                schema_name = schema_record['schema_name']
                
                # Get all tables in schema
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """
                tables = await self.database_service.fetch_query(tables_query, [schema_name])
                
                for table_record in tables:
                    table_name = table_record['table_name']
                    
                    # Truncate table
                    truncate_query = f'TRUNCATE TABLE {schema_name}.{table_name} RESTART IDENTITY CASCADE'
                    await self.database_service.execute_query(truncate_query)
                    cleaned_tables += 1
                    logger.info(f"🗑️ Truncated table: {schema_name}.{table_name}")
            
            logger.info(f"✅ Cleaned up {cleaned_tables} database tables")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
            return False
    
    async def cleanup_test_storage(self):
        """Clean up test storage buckets"""
        logger.info("📦 Cleaning up test storage...")
        
        try:
            cleaned_objects = 0
            
            for bucket in self.test_buckets:
                try:
                    # List all objects in bucket
                    objects = await self.storage_service.list_objects(bucket)
                    
                    # Delete all objects
                    for obj in objects:
                        await self.storage_service.delete_object(bucket, obj['name'])
                        cleaned_objects += 1
                        logger.info(f"🗑️ Deleted object: {bucket}/{obj['name']}")
                    
                    logger.info(f"✅ Cleaned bucket: {bucket} ({len(objects)} objects)")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not clean bucket {bucket}: {e}")
            
            logger.info(f"✅ Cleaned up {cleaned_objects} storage objects")
            return True
            
        except Exception as e:
            logger.error(f"❌ Storage cleanup failed: {e}")
            return False
    
    async def cleanup_test_directories(self):
        """Clean up test directories"""
        logger.info("📁 Cleaning up test directories...")
        
        try:
            cleaned_dirs = 0
            
            for dir_path in self.test_directories:
                path = Path(dir_path)
                
                if path.exists():
                    # Remove all files in directory
                    for item in path.glob('*'):
                        if item.is_file():
                            item.unlink()
                            logger.info(f"🗑️ Deleted file: {item}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            logger.info(f"🗑️ Deleted directory: {item}")
                    
                    cleaned_dirs += 1
                    logger.info(f"✅ Cleaned directory: {dir_path}")
                else:
                    logger.info(f"ℹ️ Directory does not exist: {dir_path}")
            
            logger.info(f"✅ Cleaned up {cleaned_dirs} directories")
            return True
            
        except Exception as e:
            logger.error(f"❌ Directory cleanup failed: {e}")
            return False
    
    async def cleanup_test_logs(self):
        """Clean up test logs"""
        logger.info("📝 Cleaning up test logs...")
        
        try:
            log_files = list(Path('test_logs').glob('*.log')) if Path('test_logs').exists() else []
            
            for log_file in log_files:
                log_file.unlink()
                logger.info(f"🗑️ Deleted log file: {log_file}")
            
            logger.info(f"✅ Cleaned up {len(log_files)} log files")
            return True
            
        except Exception as e:
            logger.error(f"❌ Log cleanup failed: {e}")
            return False
    
    async def reset_test_environment(self):
        """Reset test environment to initial state"""
        logger.info("🔄 Resetting test environment...")
        
        try:
            # Reset sequences in database
            reset_sequences_query = """
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema LIKE 'krai_%' OR sequence_schema = 'krai_test'
            """
            sequences = await self.database_service.fetch_query(reset_sequences_query)
            
            for sequence_record in sequences:
                sequence_name = sequence_record['sequence_name']
                schema_name = sequence_name.split('.')[0]
                seq_name = sequence_name.split('.')[1]
                
                reset_query = f'ALTER SEQUENCE {sequence_name} RESTART WITH 1'
                await self.database_service.execute_query(reset_query)
                logger.info(f"🔄 Reset sequence: {sequence_name}")
            
            logger.info("✅ Test environment reset completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment reset failed: {e}")
            return False
    
    async def verify_cleanup(self):
        """Verify cleanup was successful"""
        logger.info("🔍 Verifying cleanup...")
        
        verification_results = {}
        
        try:
            # Check database tables are empty
            tables_query = """
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname LIKE 'krai_%' OR schemaname = 'krai_test'
            """
            tables = await self.database_service.fetch_query(tables_query)
            
            empty_tables = 0
            for table in tables:
                count_query = f"SELECT COUNT(*) as count FROM {table['schemaname']}.{table['tablename']}"
                result = await self.database_service.fetch_query(count_query)
                count = result[0]['count']
                
                if count == 0:
                    empty_tables += 1
                else:
                    logger.warning(f"⚠️ Table not empty: {table['schemaname']}.{table['tablename']} ({count} rows)")
            
            verification_results['database_tables_empty'] = empty_tables == len(tables)
            
            # Check storage buckets are empty
            empty_buckets = 0
            for bucket in self.test_buckets:
                try:
                    objects = await self.storage_service.list_objects(bucket)
                    if len(objects) == 0:
                        empty_buckets += 1
                    else:
                        logger.warning(f"⚠️ Bucket not empty: {bucket} ({len(objects)} objects)")
                except:
                    # Bucket doesn't exist, which is fine
                    empty_buckets += 1
            
            verification_results['storage_buckets_empty'] = empty_buckets == len(self.test_buckets)
            
            # Check test directories are empty
            empty_dirs = 0
            for dir_path in self.test_directories:
                path = Path(dir_path)
                if path.exists():
                    items = list(path.glob('*'))
                    if len(items) == 0:
                        empty_dirs += 1
                    else:
                        logger.warning(f"⚠️ Directory not empty: {dir_path} ({len(items)} items)")
                else:
                    empty_dirs += 1
            
            verification_results['test_directories_empty'] = empty_dirs == len(self.test_directories)
            
            # Overall verification
            all_clean = all(verification_results.values())
            verification_results['overall'] = all_clean
            
            if all_clean:
                logger.info("🎉 Cleanup verification successful!")
            else:
                logger.warning(f"⚠️ Cleanup verification found issues: {verification_results}")
            
            return verification_results
            
        except Exception as e:
            logger.error(f"❌ Cleanup verification failed: {e}")
            return {'overall': False, 'error': str(e)}
    
    async def run_full_cleanup(self):
        """Run complete test environment cleanup"""
        logger.info("🧹 Starting full test environment cleanup...")
        
        cleanup_steps = [
            ("Services", self.initialize_services),
            ("Database", self.cleanup_test_database),
            ("Storage", self.cleanup_test_storage),
            ("Directories", self.cleanup_test_directories),
            ("Logs", self.cleanup_test_logs),
            ("Reset", self.reset_test_environment),
            ("Verification", self.verify_cleanup)
        ]
        
        results = {}
        
        for step_name, step_func in cleanup_steps:
            logger.info(f"🔄 Running cleanup step: {step_name}")
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
        
        logger.info(f"📊 Cleanup Summary: {successful_steps}/{total_steps} steps completed")
        
        if successful_steps == total_steps:
            logger.info("🎉 Test environment cleanup completed successfully!")
            return True
        else:
            logger.error(f"❌ Test environment cleanup incomplete. Failed steps: {[k for k, v in results.items() if not v]}")
            return False

async def main():
    """Main cleanup function"""
    cleanup = TestEnvironmentCleanup()
    
    try:
        success = await cleanup.run_full_cleanup()
        
        if success:
            logger.info("🎉 Test environment is clean and ready for next test run!")
            sys.exit(0)
        else:
            logger.error("❌ Test environment cleanup failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
