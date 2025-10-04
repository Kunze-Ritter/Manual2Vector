"""
PRODUCTION MODE - Process Document with ALL Features

This script processes a document in FULL PRODUCTION MODE:
- All stages enabled
- R2 Storage activated (images uploaded to Cloudflare)
- Embeddings generated (semantic search ready)
- Live Supabase connection
- No mocks, all real processing
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from processors_v2.master_pipeline import MasterPipeline
from supabase import create_client


def main():
    """Process document in FULL PRODUCTION MODE"""
    
    print("\n" + "="*80)
    print("  PRODUCTION MODE - FULL PROCESSING")
    print("="*80)
    
    print("\n🔧 Configuration:")
    print("   - Supabase: LIVE")
    print("   - R2 Storage: ENABLED (Images will be uploaded)")
    print("   - Embeddings: ENABLED (Semantic search ready)")
    print("   - OCR: ENABLED (Tesseract)")
    print("   - Vision AI: ENABLED (LLaVA)")
    print("   - All stages: ACTIVE")
    
    # Initialize Supabase
    print("\n📊 Step 1/4: Connecting to Supabase...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase connected")
    
    # Check R2 Configuration
    print("\n📊 Step 2/4: Checking R2 Storage...")
    r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
    r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
    r2_bucket = os.getenv('R2_BUCKET_NAME_DOCUMENTS')
    r2_endpoint = os.getenv('R2_ENDPOINT_URL')
    
    if not all([r2_access_key, r2_secret_key, r2_bucket, r2_endpoint]):
        print("⚠️  Warning: R2 credentials incomplete")
        print("    R2 Storage will be DISABLED")
        enable_r2 = False
    else:
        print("✅ R2 Storage configured")
        print(f"   Bucket: {r2_bucket}")
        print(f"   Endpoint: {r2_endpoint}")
        enable_r2 = True
    
    # Check Ollama
    print("\n📊 Step 3/4: Checking Ollama...")
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    print(f"   Ollama URL: {ollama_url}")
    
    try:
        import requests
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            has_embedding = any('embeddinggemma' in m.get('name', '') for m in models)
            has_vision = any('llava' in m.get('name', '') for m in models)
            
            print(f"✅ Ollama available")
            print(f"   Embedding model: {'✅' if has_embedding else '❌'} embeddinggemma")
            print(f"   Vision model: {'✅' if has_vision else '❌'} llava")
            
            if not has_embedding:
                print("\n⚠️  WARNING: embeddinggemma not found!")
                print("   Run: ollama pull embeddinggemma")
            if not has_vision:
                print("\n⚠️  WARNING: llava not found!")
                print("   Run: ollama pull llava-phi3")
        else:
            print("⚠️  Warning: Ollama not responding")
    except Exception as e:
        print(f"⚠️  Warning: Cannot connect to Ollama: {e}")
        print("   Embeddings will be DISABLED")
    
    # Find PDF
    print("\n📊 Step 4/4: Finding PDF to process...")
    
    # Try to find AccurioPress manual
    possible_paths = [
        Path("C:/Users/haast/Docker/KRAI-minimal/AccurioPress_C4080_C4070_C84hc_C74hc_AccurioPrint_C4065_C4065P_SM_EN_20250127.pdf"),
        Path(__file__).parent.parent.parent / "AccurioPress_C4080_C4070_C84hc_C74hc_AccurioPrint_C4065_C4065P_SM_EN_20250127.pdf",
    ]
    
    pdf_path = None
    for path in possible_paths:
        if path.exists():
            pdf_path = path
            break
    
    if not pdf_path:
        print("\n❌ Error: No PDF found")
        print("\nTried:")
        for path in possible_paths:
            print(f"   - {path}")
        return
    
    print(f"✅ PDF found: {pdf_path.name}")
    print(f"   Size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Confirm production mode
    print("\n" + "="*80)
    print("  READY TO PROCESS IN PRODUCTION MODE")
    print("="*80)
    print("\n⚠️  This will:")
    print("   1. Process the complete PDF")
    print("   2. Extract all text, products, error codes, versions")
    print("   3. Process all images with OCR + Vision AI")
    if enable_r2:
        print("   4. Upload images to Cloudflare R2 (costs money!)")
    else:
        print("   4. Skip R2 upload (disabled)")
    print("   5. Generate 768-dim embeddings for all chunks")
    print("   6. Store everything in Supabase")
    
    # Ask for confirmation
    print("\n❓ Continue with FULL PRODUCTION processing?")
    response = input("   Type 'YES' to proceed: ").strip()
    
    if response != 'YES':
        print("\n❌ Aborted by user")
        return
    
    # Initialize Pipeline with ALL FEATURES
    print("\n" + "="*80)
    print("  🚀 STARTING PRODUCTION PROCESSING")
    print("="*80)
    
    pipeline = MasterPipeline(
        supabase_client=supabase,
        manufacturer="Konica Minolta",
        enable_images=True,          # Extract images
        enable_ocr=True,              # OCR on images
        enable_vision=True,           # Vision AI analysis
        enable_r2_storage=enable_r2,  # Upload to R2 (if configured)
        enable_embeddings=True,       # Generate embeddings
        max_retries=2
    )
    
    print("\n⏳ Processing... This may take several minutes...\n")
    
    # Process!
    result = pipeline.process_document(
        file_path=pdf_path,
        document_type="service_manual",
        manufacturer="Konica Minolta"
    )
    
    # Results
    print("\n" + "="*80)
    if result['success']:
        print("  ✅ SUCCESS - PRODUCTION PROCESSING COMPLETE!")
        print("="*80)
        
        print(f"\n📊 Results:")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Processing Time: {result['processing_time']:.1f}s")
        
        processing = result['results'].get('processing', {})
        if processing:
            metadata = processing.get('metadata', {})
            print(f"\n📄 Document:")
            print(f"   Pages: {metadata.get('page_count', 0):,}")
            print(f"   Words: {metadata.get('word_count', 0):,}")
            
            products = processing.get('products', [])
            error_codes = processing.get('error_codes', [])
            versions = processing.get('versions', [])
            images = processing.get('images', [])
            chunks = processing.get('chunks', [])
            
            print(f"\n📦 Extracted:")
            print(f"   Products: {len(products)}")
            print(f"   Error Codes: {len(error_codes)}")
            print(f"   Versions: {len(versions)}")
            print(f"   Images: {len(images)}")
            print(f"   Chunks: {len(chunks)}")
            
            # R2 Upload Results
            if enable_r2 and 'r2_storage' in result['results']:
                r2_result = result['results']['r2_storage']
                if r2_result.get('success'):
                    print(f"\n☁️  R2 Storage:")
                    print(f"   Uploaded: {r2_result.get('uploaded_count', 0)} images")
                    print(f"   URLs: {len(r2_result.get('urls', []))}")
            
            # Embeddings
            if 'embeddings' in result['results']:
                emb_result = result['results']['embeddings']
                if emb_result.get('success'):
                    print(f"\n🔮 Embeddings:")
                    print(f"   Created: {emb_result.get('embeddings_created', 0):,}")
                    print(f"   Time: {emb_result.get('processing_time', 0):.1f}s")
                    rate = emb_result.get('embeddings_created', 0) / max(emb_result.get('processing_time', 1), 1)
                    print(f"   Speed: {rate:.1f} embeddings/second")
        
        print("\n✅ Document is now:")
        print("   - Fully indexed in Supabase")
        print("   - Searchable semantically")
        print("   - Ready for AI queries")
        if enable_r2:
            print("   - Images available on R2")
        
        print("\n🎉 PRODUCTION PROCESSING SUCCESSFUL!")
        
    else:
        print("  ❌ FAILED")
        print("="*80)
        print(f"\n💥 Error: {result.get('error')}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
