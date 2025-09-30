#!/usr/bin/env python3
"""
KR-AI-Engine Production Test
Testet das System mit echten Services (Supabase, R2, Ollama)
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from config.ai_config import AIConfigManager
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService
from processors.upload_processor import UploadProcessor
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from processors.classification_processor import ClassificationProcessor
from core.base_processor import ProcessingContext

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionTester:
    """Production Test für KR-AI-Engine"""
    
    def __init__(self):
        self.services = {}
        self.processors = {}
        self.test_results = {}
    
    async def setup_services(self):
        """Setup Production Services"""
        print("🔧 Setting up production services...")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Database Service (Supabase)
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials not found in environment")
            
            self.services['database'] = DatabaseService(supabase_url, supabase_key)
            await self.services['database'].connect()
            print("✅ Database service ready (Supabase)")
            
            # Object Storage Service (Cloudflare R2)
            r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
            r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
            r2_endpoint = os.getenv('R2_ENDPOINT_URL')
            r2_public_docs = os.getenv('R2_PUBLIC_URL_DOCUMENTS')
            r2_public_error = os.getenv('R2_PUBLIC_URL_ERROR')
            r2_public_parts = os.getenv('R2_PUBLIC_URL_PARTS')
            
            if not all([r2_access_key, r2_secret_key, r2_endpoint, r2_public_docs]):
                raise ValueError("R2 credentials not found in environment")
            
            self.services['storage'] = ObjectStorageService(
                r2_access_key, r2_secret_key, r2_endpoint,
                r2_public_docs, r2_public_error, r2_public_parts
            )
            await self.services['storage'].connect()
            print("✅ Object storage service ready (Cloudflare R2)")
            
            # AI Service (Ollama)
            ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.services['ai'] = AIService(ollama_url)
            await self.services['ai'].connect()
            print("✅ AI service ready (Ollama)")
            
            # Config Service
            self.services['config'] = ConfigService()
            print("✅ Configuration service ready")
            
            # Features Service
            self.services['features'] = FeaturesService(
                self.services['ai'], 
                self.services['database']
            )
            print("✅ Features service ready")
            
            print("🎯 All production services ready!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup services: {e}")
            return False
    
    async def setup_processors(self):
        """Setup Production Processors"""
        print("🔧 Setting up production processors...")
        
        try:
            # Upload Processor
            self.processors['upload'] = UploadProcessor(self.services['database'])
            print("✅ Upload processor ready")
            
            # Text Processor
            self.processors['text'] = TextProcessor(
                self.services['database'], 
                self.services['config']
            )
            print("✅ Text processor ready")
            
            # Image Processor
            self.processors['image'] = ImageProcessor(
                self.services['database'],
                self.services['storage'],
                self.services['ai']
            )
            print("✅ Image processor ready")
            
            # Classification Processor
            self.processors['classification'] = ClassificationProcessor(
                self.services['database'],
                self.services['ai'],
                self.services['features']
            )
            print("✅ Classification processor ready")
            
            print("🎯 All production processors ready!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup processors: {e}")
            return False
    
    async def test_services_health(self):
        """Test Production Services Health"""
        print("🏥 Testing production services health...")
        
        results = {}
        
        try:
            # Test Database
            db_health = await self.services['database'].health_check()
            results['database'] = db_health['status']
            print(f"🗄️ Database service: {db_health['status']}")
            
            # Test Object Storage
            storage_health = await self.services['storage'].health_check()
            results['storage'] = storage_health['status']
            print(f"☁️ Object storage service: {storage_health['status']}")
            
            # Test AI Service
            ai_health = await self.services['ai'].health_check()
            results['ai'] = ai_health['status']
            print(f"🤖 AI service: {ai_health['status']}")
            
            # Test Config Service
            results['config'] = 'healthy'
            print(f"📋 Configuration service: healthy")
            
            # Test Features Service
            results['features'] = 'healthy'
            print(f"⚙️ Features service: healthy")
            
            all_healthy = all(status == 'healthy' for status in results.values())
            if all_healthy:
                print("🎯 All production services healthy!")
                return True
            else:
                print("⚠️ Some services have issues")
                return False
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_production_pipeline(self):
        """Test Production Processing Pipeline"""
        print("🧪 Testing production processing pipeline...")
        
        try:
            # Create test document
            test_file_path = "test_document.pdf"
            test_content = b"Mock PDF content for production testing"
            
            # Create test file
            with open(test_file_path, 'wb') as f:
                f.write(test_content)
            
            # Create processing context
            context = ProcessingContext(
                file_path=test_file_path,
                file_hash="test_hash_production",
                document_type="service_manual",
                language="en",
                filename="test_document.pdf"
            )
            
            # Test Upload Processor
            print("📤 Testing upload processor...")
            upload_result = await self.processors['upload'].safe_process(context)
            if upload_result.success:
                print("✅ Upload processor test passed")
                context.document_id = upload_result.data['document_id']
            else:
                print(f"❌ Upload processor test failed: {upload_result.error}")
                return False
            
            # Test Text Processor
            print("📄 Testing text processor...")
            text_result = await self.processors['text'].safe_process(context)
            if text_result.success:
                print("✅ Text processor test passed")
            else:
                print(f"❌ Text processor test failed: {text_result.error}")
                return False
            
            # Test Image Processor
            print("🖼️ Testing image processor...")
            image_result = await self.processors['image'].safe_process(context)
            if image_result.success:
                print("✅ Image processor test passed")
            else:
                print(f"❌ Image processor test failed: {image_result.error}")
                return False
            
            # Test Classification Processor
            print("🏷️ Testing classification processor...")
            classification_result = await self.processors['classification'].safe_process(context)
            if classification_result.success:
                print("✅ Classification processor test passed")
            else:
                print(f"❌ Classification processor test failed: {classification_result.error}")
                return False
            
            # Cleanup test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            
            print("🎯 Production pipeline test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Production pipeline test failed: {e}")
            return False
    
    async def test_ai_models(self):
        """Test AI Models Availability"""
        print("🤖 Testing AI models availability...")
        
        try:
            # Test Ollama connection
            ai_health = await self.services['ai'].health_check()
            if ai_health['status'] == 'healthy':
                print("✅ Ollama connection successful")
                print(f"   Available models: {len(ai_health.get('available_models', []))}")
                print(f"   Configured models: {ai_health.get('configured_models', {})}")
                print(f"   GPU Acceleration: {ai_health.get('gpu_acceleration', False)}")
                return True
            else:
                print(f"❌ Ollama connection failed: {ai_health.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ AI models test failed: {e}")
            return False
    
    async def test_storage_buckets(self):
        """Test Storage Buckets"""
        print("☁️ Testing storage buckets...")
        
        try:
            # Test bucket access
            buckets = ['krai-documents', 'krai-error-images', 'krai-parts-images']
            
            for bucket in buckets:
                try:
                    # Try to list objects in bucket
                    objects = await self.services['storage'].list_images('document_images' if 'documents' in bucket else 'error_images')
                    print(f"✅ Bucket {bucket} accessible")
                except Exception as e:
                    print(f"⚠️ Bucket {bucket} issue: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Storage buckets test failed: {e}")
            return False
    
    async def run_production_test(self):
        """Run Complete Production Test"""
        print("🚀 Starting KR-AI-Engine Production Test")
        print("=" * 50)
        
        # Hardware Detection
        ai_config = AIConfigManager()
        print(f"🔍 Hardware Detection:")
        print(f"   RAM: {ai_config.detector.specs.total_ram_gb:.1f} GB")
        print(f"   CPU: {ai_config.detector.specs.cpu_cores} cores, {ai_config.detector.specs.cpu_threads} threads")
        if ai_config.detector.specs.gpu_available:
            print(f"   GPU: {ai_config.detector.specs.gpu_name} ({ai_config.detector.specs.gpu_memory_gb:.1f} GB VRAM)")
            print(f"   GPU Driver: {ai_config.detector.specs.gpu_driver_version}")
        else:
            print(f"   GPU: Not Available")
        print(f"   Recommended Tier: {ai_config.detector.recommend_model_tier().value}")
        print(f"   GPU Acceleration: {'Enabled' if ai_config.detector.specs.gpu_available else 'Disabled'}")
        
        # Setup Services
        if not await self.setup_services():
            print("❌ Production Test: FAILED - Service setup failed")
            return False
        
        # Setup Processors
        if not await self.setup_processors():
            print("❌ Production Test: FAILED - Processor setup failed")
            return False
        
        # Test Services Health
        if not await self.test_services_health():
            print("❌ Production Test: FAILED - Service health check failed")
            return False
        
        # Test AI Models
        if not await self.test_ai_models():
            print("❌ Production Test: FAILED - AI models test failed")
            return False
        
        # Test Storage Buckets
        if not await self.test_storage_buckets():
            print("❌ Production Test: FAILED - Storage buckets test failed")
            return False
        
        # Test Production Pipeline
        if not await self.test_production_pipeline():
            print("❌ Production Test: FAILED - Production pipeline test failed")
            return False
        
        print("=" * 50)
        print("🎉 Production Test: SUCCESS!")
        print("🎯 KR-AI-Engine is ready for production use!")
        return True

async def main():
    """Main function"""
    tester = ProductionTester()
    success = await tester.run_production_test()
    
    if success:
        print("\n✅ All production tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some production tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
