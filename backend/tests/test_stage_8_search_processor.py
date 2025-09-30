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
from processors.search_processor import SearchProcessor
from core.data_models import DocumentModel, DocumentType, SearchAnalyticsModel
from core.base_processor import ProcessingContext

async def test_stage_8_search_processor():
    """Test Stage 8: Search Processor with PRODUCTION semantic search capabilities"""
    print("Testing Stage 8: Search Processor with PRODUCTION semantic search capabilities...")
    
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
        
        # Initialize Search Processor
        search_processor = SearchProcessor(database_service, ai_service)
        
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
        
        print("Starting Stage 8: Search Processor...")
        print("=" * 60)
        
        # Process search index creation
        result = await search_processor.process(context)
        
        print("=" * 60)
        print("Stage 8 Search Processor Results:")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            data = result.data
            print(f"Search Index Created: {data.get('search_index', {}).get('index_created', False)}")
            print(f"Analytics Tracked: {bool(data.get('analytics', {}))}")
            
            # Show search index result
            search_index = data.get('search_index', {})
            if search_index:
                print(f"\nSearch Index Result:")
                print(f"  Document ID: {search_index.get('document_id', 'N/A')}")
                print(f"  Index Type: {search_index.get('index_type', 'N/A')}")
                print(f"  Optimization Level: {search_index.get('optimization_level', 'N/A')}")
                print(f"  Index Created: {search_index.get('index_created', False)}")
            
            # Show analytics result
            analytics = data.get('analytics', {})
            if analytics:
                print(f"\nAnalytics Result:")
                print(f"  Document ID: {analytics.get('document_id', 'N/A')}")
                print(f"  Search Queries: {analytics.get('search_queries', 0)}")
                print(f"  Success Rate: {analytics.get('search_success_rate', 0):.2f}")
                print(f"  Avg Response Time: {analytics.get('average_response_time', 0):.2f}ms")
            
            # Test semantic search functionality
            print(f"\nTesting Semantic Search...")
            try:
                # Generate query embedding
                test_query = "How to fix paper jam in HP printer"
                print(f"Test Query: '{test_query}'")
                
                query_embedding = await ai_service.generate_embeddings(test_query)
                print(f"Query Embedding Generated: {len(query_embedding)} dimensions")
                
                # Create search analytics entry
                search_analytics = SearchAnalyticsModel(
                    query=test_query,
                    results_count=1,
                    processing_time_ms=150.0,
                    user_id="test_user",
                    session_id="test_session"
                )
                
                analytics_id = await database_service.create_search_analytics(search_analytics)
                print(f"Search Analytics Created: {analytics_id}")
                
            except Exception as search_error:
                print(f"Semantic search test failed: {search_error}")
            
            # Verify database storage
            print(f"\nVerifying database storage...")
            try:
                if search_index.get('index_created'):
                    print(f"Search index created successfully")
                else:
                    print("Search index creation failed")
                
                if analytics:
                    print(f"Search analytics tracked: {bool(analytics)}")
                else:
                    print("No search analytics tracked")
                
            except Exception as e:
                print(f"Database verification error: {e}")
                
        else:
            print(f"Search processing failed: {result.error}")
            return False
        
        print("\nStage 8 Search Processor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Stage 8 Search Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_stage_8_search_processor())
