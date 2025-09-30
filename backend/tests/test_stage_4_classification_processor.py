import asyncio
import os
import sys
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.ai_service import AIService
from services.features_service import FeaturesService
from processors.classification_processor import ClassificationProcessor
from core.data_models import DocumentModel, DocumentType
from core.base_processor import ProcessingContext

async def test_stage_4_classification_processor():
    """Test Stage 4: Classification Processor with AI-powered document classification"""
    print("Testing Stage 4: Classification Processor with AI-powered document classification...")
    
    try:
        # Initialize services
        print("Initializing services...")
        config_service = ConfigService()
        
        # Database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        
        # AI service with correct Ollama URL
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ai_service = AIService(ollama_url)
        await ai_service.connect()
        
        # Features service
        features_service = FeaturesService(ai_service, database_service)
        
        # Initialize Classification Processor
        classification_processor = ClassificationProcessor(database_service, ai_service, features_service)
        
        # PDF file path
        pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        print(f"PDF file found: {pdf_path}")
        
        # Create document first
        print("Creating document in database...")
        document = DocumentModel(
            filename=os.path.basename(pdf_path),
            original_filename=os.path.basename(pdf_path),
            file_size=os.path.getsize(pdf_path),
            file_hash=hashlib.sha256(open(pdf_path, 'rb').read()).hexdigest(),
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            series="Color LaserJet Enterprise",
            models=["X580"],
            version="1.0",
            language="en"
        )
        
        created_doc = await database_service.create_document(document)
        doc_id = created_doc.id if hasattr(created_doc, 'id') else created_doc
        print(f"Document created: {doc_id}")
        
        # Create processing context
        context = ProcessingContext(
            document_id=doc_id,
            file_path=pdf_path,
            file_hash=hashlib.sha256(open(pdf_path, 'rb').read()).hexdigest(),
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            model="X580",
            series="Color LaserJet Enterprise",
            version="1.0",
            language="en",
            processing_config={"filename": os.path.basename(pdf_path)},
            file_size=os.path.getsize(pdf_path)
        )
        
        print("Starting Stage 4: Classification Processor...")
        print("=" * 60)
        
        # Process classification with AI
        result = await classification_processor.process(context)
        
        print("=" * 60)
        print("Stage 4 Classification Processor Results:")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            data = result.data
            print(f"Manufacturer ID: {data.get('manufacturer_id', 'N/A')}")
            print(f"Series ID: {data.get('series_id', 'N/A')}")
            print(f"Product ID: {data.get('product_id', 'N/A')}")
            
            # Show classification result
            classification_result = data.get('classification_result', {})
            if classification_result:
                print(f"\nClassification Result:")
                print(f"  Manufacturer: {classification_result.get('manufacturer', 'N/A')}")
                print(f"  Series: {classification_result.get('series', 'N/A')}")
                print(f"  Models: {classification_result.get('models', [])}")
                print(f"  Document Type: {classification_result.get('document_type', 'N/A')}")
                print(f"  Confidence: {classification_result.get('confidence', 0):.2f}")
                print(f"  Language: {classification_result.get('language', 'N/A')}")
                print(f"  Version: {classification_result.get('version', 'N/A')}")
            
            # Show features result
            features_result = data.get('features_result', {})
            if features_result:
                print(f"\nFeatures Result:")
                series_features = features_result.get('series_features', {})
                product_features = features_result.get('product_features', {})
                print(f"  Series Features: {len(series_features)} items")
                print(f"  Product Features: {len(product_features)} items")
                
                if series_features:
                    print(f"  Key Series Features:")
                    for key, value in list(series_features.items())[:3]:
                        print(f"    {key}: {value}")
                
                if product_features:
                    print(f"  Key Product Features:")
                    for key, value in list(product_features.items())[:3]:
                        print(f"    {key}: {value}")
            
            # Verify database storage
            print(f"\nVerifying database storage...")
            try:
                # Check if manufacturer was created
                if data.get('manufacturer_id'):
                    print(f"Manufacturer created in database: {data['manufacturer_id']}")
                
                # Check if series was created
                if data.get('series_id'):
                    print(f"Product series created in database: {data['series_id']}")
                
                # Check if products were created
                if data.get('product_id'):
                    print(f"Product created in database: {data['product_id']}")
                
            except Exception as e:
                print(f"Database verification error: {e}")
                
        else:
            print(f"Classification processing failed: {result.error}")
            return False
        
        print("\nStage 4 Classification Processor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Stage 4 Classification Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_stage_4_classification_processor())
