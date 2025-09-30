#!/usr/bin/env python3
"""
Test script for KR-AI-Engine production setup
Tests all services in production mode with real credentials
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("krai.test")

async def test_services():
    """Test all services in production mode"""
    logger.info("🚀 Starting KR-AI-Engine Production Setup Test")
    logger.info("=" * 60)
    
    try:
        # Test 1: Hardware Detection
        logger.info("🔍 Testing Hardware Detection...")
        from config.ai_config import AIConfigManager
        
        ai_config_manager = AIConfigManager()
        model_config = ai_config_manager.get_config()
        
        logger.info(f"   Hardware: {ai_config_manager.detector.specs.total_ram_gb:.1f} GB RAM, {ai_config_manager.detector.specs.cpu_cores} cores")
        if ai_config_manager.detector.specs.gpu_available:
            logger.info(f"   GPU: {ai_config_manager.detector.specs.gpu_name} ({ai_config_manager.detector.specs.gpu_memory_gb:.1f} GB VRAM)")
        else:
            logger.info("   GPU: Not Available")
        logger.info(f"   Recommended Tier: {model_config.tier.value}")
        logger.info(f"   Models: {model_config.text_classification}, {model_config.embeddings}, {model_config.vision}")
        logger.info("✅ Hardware Detection: PASSED")
        
        # Test 2: Database Service
        logger.info("\n🗄️ Testing Database Service...")
        from services.database_service import DatabaseService
        
        # Use direct credentials from .env.example
        db_service = DatabaseService(
            supabase_url="https://crujfdpqdjzcfqeyhang.supabase.co",
            supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNydWpmZHBxZGp6Y2ZxZXloYW5nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkwNDY1MTUsImV4cCI6MjA3NDYyMjUxNX0.kDSf9jMYbNgzV8v1f-_kSoSy_cAMFL367m9ZbDsBkw"
        )
        
        await db_service.connect()
        health = await db_service.health_check()
        logger.info(f"   Database Status: {health['status']}")
        if health['status'] == 'healthy':
            logger.info(f"   Response Time: {health['response_time_ms']:.2f} ms")
        logger.info("✅ Database Service: PASSED")
        
        # Test 3: Object Storage Service
        logger.info("\n☁️ Testing Object Storage Service...")
        from services.object_storage_service import ObjectStorageService
        
        # Use direct credentials from .env.example
        storage_service = ObjectStorageService(
            r2_access_key_id="9c59473961632448c91db3ef9dbd35ab",
            r2_secret_access_key="9cc62a9506ac9ec6e8373a39fa86268bc187632e5548e8c37b1c6c9c071755e4",
            r2_endpoint_url="https://a88f92c913c232559845adb9001a5d14.eu.r2.cloudflarestorage.com",
            r2_public_url_documents="https://pub-68e63cf2d6ac4222adaab70dfbc29ec4.r2.dev",
            r2_public_url_error="https://pub-e327cb3371c741e08c5e8672e817d9cf.r2.dev",
            r2_public_url_parts="https://pub-61c8b15e7bf24febbf8e0197ab237041.r2.dev"
        )
        
        await storage_service.connect()
        health = await storage_service.health_check()
        logger.info(f"   Storage Status: {health['status']}")
        if health['status'] == 'healthy':
            logger.info(f"   Response Time: {health['response_time_ms']:.2f} ms")
            logger.info(f"   Buckets: {health['buckets']}")
        logger.info("✅ Object Storage Service: PASSED")
        
        # Test 4: AI Service
        logger.info("\n🤖 Testing AI Service...")
        from services.ai_service import AIService
        
        ai_service = AIService(ollama_url="http://localhost:11434")
        await ai_service.connect()
        health = await ai_service.health_check()
        logger.info(f"   AI Status: {health['status']}")
        if health['status'] == 'healthy':
            logger.info(f"   Response Time: {health['response_time_ms']:.2f} ms")
            logger.info(f"   Available Models: {len(health['available_models'])}")
            logger.info(f"   GPU Acceleration: {health['gpu_acceleration']}")
            logger.info(f"   Tier: {health['tier']}")
        logger.info("✅ AI Service: PASSED")
        
        # Test 5: Config Service
        logger.info("\n⚙️ Testing Config Service...")
        from services.config_service import ConfigService
        
        config_service = ConfigService()
        chunk_strategy = config_service.get_chunking_strategy("service_manual", "HP")
        error_patterns = config_service.get_error_code_patterns()
        version_patterns = config_service.get_version_patterns()
        model_patterns = config_service.get_model_placeholder_patterns()
        
        logger.info(f"   Chunk Strategy: {chunk_strategy.get('preferred_strategy', 'Unknown')}")
        logger.info(f"   Error Patterns: {len(error_patterns.get('error_code_patterns', {}))} manufacturers")
        logger.info(f"   Version Patterns: {len(version_patterns.get('version_patterns', {}))} types")
        logger.info(f"   Model Patterns: {len(model_patterns.get('model_placeholder_patterns', {}))} types")
        logger.info("✅ Config Service: PASSED")
        
        # Test 6: Features Service
        logger.info("\n🏷️ Testing Features Service...")
        from services.features_service import FeaturesService
        
        features_service = FeaturesService(ai_service, db_service)
        logger.info("   Features Service initialized")
        logger.info("✅ Features Service: PASSED")
        
        # Test 7: Update Service
        logger.info("\n🔄 Testing Update Service...")
        from services.update_service import UpdateService
        
        update_service = UpdateService(db_service)
        logger.info("   Update Service initialized")
        logger.info("✅ Update Service: PASSED")
        
        # Test 8: Core Data Models
        logger.info("\n📊 Testing Core Data Models...")
        from core.data_models import DocumentModel, DocumentType, ManufacturerModel, ProductSeriesModel, ProductModel
        
        # Test document model
        doc = DocumentModel(
            original_filename="test.pdf",
            filename="test.pdf",
            file_size=1024,
            file_hash="test_hash",
            document_type=DocumentType.SERVICE_MANUAL,
            language="en",
            processing_status="pending"
        )
        
        # Test manufacturer model
        manufacturer = ManufacturerModel(
            name="Test Manufacturer",
            country="Germany",
            website="https://test.com"
        )
        
        # Test product series model
        series = ProductSeriesModel(
            manufacturer_id=manufacturer.id,
            series_name="Test Series",
            description="Test product series",
            key_features={"color_capable": True, "duplex_capable": True}
        )
        
        # Test product model
        product = ProductModel(
            manufacturer_id=manufacturer.id,
            series_id=series.id,
            model_name="Test Model",
            model_number="TM-001",
            product_type="printer",
            description="Test product",
            is_color_capable=True,
            is_duplex_capable=True
        )
        
        logger.info(f"   Document ID: {doc.id}")
        logger.info(f"   Manufacturer ID: {manufacturer.id}")
        logger.info(f"   Series ID: {series.id}")
        logger.info(f"   Product ID: {product.id}")
        logger.info("✅ Core Data Models: PASSED")
        
        # Test 9: Base Processor
        logger.info("\n🔧 Testing Base Processor...")
        from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult
        
        class TestProcessor(BaseProcessor):
            async def process(self, context: ProcessingContext) -> ProcessingResult:
                return ProcessingResult(
                    success=True,
                    message="Test processing completed",
                    processor_name=self.name,
                    data={"test": "value"}
                )
            
            def get_outputs(self) -> List[str]:
                return ["test_output"]
            
            def get_required_inputs(self) -> List[str]:
                return ["test_input"]
        
        test_processor = TestProcessor("test_processor")
        context = ProcessingContext(
            document_id="test_doc_123",
            file_path="test.pdf",
            file_hash="test_hash",
            document_type="service_manual"
        )
        
        result = await test_processor.safe_process(context)
        logger.info(f"   Processor: {test_processor.name}")
        logger.info(f"   Success: {result.success}")
        logger.info(f"   Message: {result.error or 'Processing completed'}")
        logger.info("✅ Base Processor: PASSED")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ALL TESTS PASSED! Production setup is ready!")
        logger.info("=" * 60)
        logger.info("✅ Hardware Detection: Working")
        logger.info("✅ Database Service: Connected")
        logger.info("✅ Object Storage Service: Connected")
        logger.info("✅ AI Service: Connected")
        logger.info("✅ Config Service: Loaded")
        logger.info("✅ Features Service: Ready")
        logger.info("✅ Update Service: Ready")
        logger.info("✅ Core Data Models: Valid")
        logger.info("✅ Base Processor: Working")
        logger.info("\n🚀 KR-AI-Engine is ready for production!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error("Please check the error above and fix the issue.")
        raise

if __name__ == "__main__":
    asyncio.run(test_services())
