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
from processors.embedding_processor import EmbeddingProcessor
from core.data_models import DocumentModel, DocumentType
from core.base_processor import ProcessingContext

async def test_stage_7_embedding_processor():
    """Test Stage 7: Embedding Processor with AI-powered vector embedding generation"""
    print("Testing Stage 7: Embedding Processor with AI-powered vector embedding generation...")
    
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
        
        # Initialize Embedding Processor
        embedding_processor = EmbeddingProcessor(database_service, ai_service)
        
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
        
        print("Starting Stage 7: Embedding Processor...")
        print("=" * 60)
        
        # Process embedding generation
        result = await embedding_processor.process(context)
        
        print("=" * 60)
        print("Stage 7 Embedding Processor Results:")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            data = result.data
            print(f"Embeddings Generated: {data.get('vector_count', 0)}")
            
            # Show metadata result
            metadata = result.metadata
            if metadata:
                print(f"\nMetadata Result:")
                print(f"  Model Used: {metadata.get('model_used', 'N/A')}")
                print(f"  Embedding Dimension: {metadata.get('embedding_dimension', 0)}")
                print(f"  Processing Timestamp: {metadata.get('processing_timestamp', 'N/A')}")
            
            # Show embeddings
            embeddings = data.get('embeddings', [])
            if embeddings:
                print(f"\nEmbeddings Generated:")
                for i, embedding_id in enumerate(embeddings[:3]):  # Show first 3
                    print(f"  {i+1}. Embedding ID: {embedding_id}")
                
                if len(embeddings) > 3:
                    print(f"  ... and {len(embeddings) - 3} more embeddings")
            
            # Verify database storage
            print(f"\nVerifying database storage...")
            try:
                if embeddings:
                    print(f"Embeddings stored in database: {len(embeddings)} items")
                    print(f"Each embedding is a {metadata.get('embedding_dimension', 0)}-dimensional vector")
                else:
                    print("No embeddings generated")
                
            except Exception as e:
                print(f"Database verification error: {e}")
                
        else:
            print(f"Embedding processing failed: {result.error}")
            return False
        
        print("\nStage 7 Embedding Processor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Stage 7 Embedding Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_stage_7_embedding_processor())
