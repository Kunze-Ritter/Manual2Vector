"""
Example: Using the Master Pipeline

This script demonstrates how to use the complete document processing pipeline.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from backend.pipeline.master_pipeline import KRMasterPipeline
from supabase import create_client


def main():
    """Main example"""
    
    print("\n" + "="*80)
    print("  MASTER PIPELINE - EXAMPLE USAGE")
    print("="*80)
    
    # ==========================================
    # 1. Initialize Supabase
    # ==========================================
    print("\n1️⃣  Initializing Supabase...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found in environment")
        print("\nPlease set:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_SERVICE_KEY=your-service-key")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase connected")
    
    # ==========================================
    # 2. Initialize Pipeline
    # ==========================================
    print("\n2️⃣  Initializing Master Pipeline...")
    
    pipeline = KRMasterPipeline(
        supabase_client=supabase,
        manufacturer="AUTO",          # Auto-detect manufacturer
        enable_images=True,            # Extract images
        enable_ocr=True,               # OCR on images
        enable_vision=True,            # Vision AI analysis
        enable_r2_storage=False,       # Skip R2 upload (optional)
        enable_embeddings=True,        # Generate embeddings for search
        max_retries=2                  # Retry failed stages twice
    )
    
    print("✅ Pipeline ready")
    
    # ==========================================
    # 3. Process Document
    # ==========================================
    print("\n3️⃣  Processing Document...")
    
    # Find test PDF
    test_pdf = Path(__file__).parent.parent.parent / "AccurioPress_C4080_C4070_C84hc_C74hc_AccurioPrint_C4065_C4065P_SM_EN_20250127.pdf"
    
    if not test_pdf.exists():
        print(f"❌ Test PDF not found at: {test_pdf}")
        print("\nPlease provide a PDF file path")
        return
    
    print(f"📄 File: {test_pdf.name}")
    print(f"📦 Size: {test_pdf.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Process!
    result = pipeline.process_document(
        file_path=test_pdf,
        document_type="service_manual",
        manufacturer="Konica Minolta"
    )
    
    # ==========================================
    # 4. Check Results
    # ==========================================
    print("\n4️⃣  Results...")
    
    if result['success']:
        print("\n✅ SUCCESS!")
        print(f"\n📊 Processing Summary:")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Total Time: {result['processing_time']:.1f}s")
        
        # Get details from results
        processing = result['results'].get('processing', {})
        
        if processing:
            metadata = processing.get('metadata', {})
            print(f"\n📄 Document Details:")
            print(f"   Pages: {metadata.get('page_count', 0)}")
            print(f"   Words: {metadata.get('word_count', 0):,}")
            print(f"   Characters: {metadata.get('char_count', 0):,}")
            
            print(f"\n📦 Extracted Entities:")
            print(f"   Products: {len(processing.get('products', []))}")
            print(f"   Error Codes: {len(processing.get('error_codes', []))}")
            print(f"   Versions: {len(processing.get('versions', []))}")
            print(f"   Images: {len(processing.get('images', []))}")
            print(f"   Chunks: {len(processing.get('chunks', []))}")
            
            # Embeddings
            embeddings = result['results'].get('embeddings', {})
            if embeddings and embeddings.get('success'):
                print(f"\n🔮 Embeddings:")
                print(f"   Created: {embeddings.get('embeddings_created', 0)}")
                print(f"   Time: {embeddings.get('processing_time', 0):.1f}s")
                print(f"   Speed: {embeddings.get('embeddings_created', 0) / embeddings.get('processing_time', 1):.1f} emb/s")
        
        print("\n✅ Document ready for semantic search!")
        
    else:
        print(f"\n❌ FAILED: {result['error']}")
    
    print("\n" + "="*80)


def example_batch_processing():
    """Example: Batch processing multiple documents"""
    
    print("\n" + "="*80)
    print("  BATCH PROCESSING EXAMPLE")
    print("="*80)
    
    # Initialize
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    pipeline = KRMasterPipeline(
        supabase_client=supabase,
        enable_embeddings=True
    )
    
    # Process multiple files
    file_paths = [
        Path("manual1.pdf"),
        Path("manual2.pdf"),
        Path("manual3.pdf")
    ]
    
    result = pipeline.process_batch(
        file_paths=file_paths,
        document_type="service_manual"
    )
    
    print(f"\n✅ Batch Complete!")
    print(f"   Successful: {result['successful']}/{result['total']}")
    print(f"   Failed: {result['failed']}/{result['total']}")
    print(f"   Total Time: {result['processing_time']:.1f}s")


def example_semantic_search():
    """Example: Using semantic search after processing"""
    
    print("\n" + "="*80)
    print("  SEMANTIC SEARCH EXAMPLE")
    print("="*80)
    
    from processors.embedding_processor import EmbeddingProcessor
    
    # Initialize
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    embedding_processor = EmbeddingProcessor(
        supabase_client=supabase
    )
    
    # Search for similar content
    query = "How to fix paper jam error?"
    
    results = embedding_processor.search_similar(
        query_text=query,
        limit=5,
        similarity_threshold=0.7
    )
    
    print(f"\n🔍 Query: \"{query}\"")
    print(f"\n📊 Found {len(results)} results:")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Similarity: {result['similarity']:.2%}")
        print(f"   {result['text'][:100]}...")


if __name__ == "__main__":
    # Run main example
    main()
    
    # Uncomment to run other examples:
    # example_batch_processing()
    # example_semantic_search()
