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

# Load environment first
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Use centralized imports
from .imports import get_supabase_client, get_logger

try:
    from processors.master_pipeline import MasterPipeline
    from processors.__version__ import __version__, __commit__, __date__
except ImportError:
    # Fallback if these don't exist
    MasterPipeline = None
    __version__ = "2.0"
    __commit__ = "unknown"
    __date__ = "2025-10-08"


def main():
    """Process document in FULL PRODUCTION MODE"""
    
    # Show version info
    print("\n" + "=" * 80)
    print(f"  KRAI PROCESSING PIPELINE v{__version__}")
    print(f"  Commit: {__commit__} | Date: {__date__}")
    print("=" * 80 + "\n")
    
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
    
    # Find PDFs in input folder
    print("\n📊 Step 4/4: Finding PDFs to process...")
    
    input_folder = Path(__file__).parent.parent.parent / "input_pdfs"
    processed_folder = input_folder / "processed"
    
    # Create folders if they don't exist
    input_folder.mkdir(exist_ok=True)
    processed_folder.mkdir(exist_ok=True)
    
    # Find all PDFs (including .pdfz compressed)
    pdf_files = list(input_folder.glob("*.pdf")) + list(input_folder.glob("*.pdfz"))
    
    if not pdf_files:
        print(f"\n❌ No PDFs found in: {input_folder}")
        print("\n💡 Place your PDF files in:")
        print(f"   {input_folder.absolute()}")
        print("\n   Supported formats:")
        print("   - *.pdf (normal PDFs)")
        print("   - *.pdfz (compressed PDFs - will be auto-decompressed)")
        return
    
    print(f"✅ Found {len(pdf_files)} PDF(s):")
    for i, pdf in enumerate(pdf_files, 1):
        size_mb = pdf.stat().st_size / 1024 / 1024
        print(f"   {i}. {pdf.name} ({size_mb:.1f} MB)")
    
    # Confirm production mode
    print("\n" + "="*80)
    print("  READY TO PROCESS IN PRODUCTION MODE")
    print("="*80)
    print(f"\n⚠️  This will process {len(pdf_files)} PDF(s):")
    print("   1. Process each complete PDF")
    print("   2. Extract all text, products, error codes, versions, links")
    print("   3. Process all images with OCR + Vision AI")
    if enable_r2:
        print("   4. Upload images to Cloudflare R2 (costs money!)")
    else:
        print("   4. Skip R2 upload (disabled)")
    print("   5. Generate 768-dim embeddings for all chunks")
    print("   6. Store everything in Supabase")
    print("   7. Move processed PDFs to processed/ folder")
    
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
        manufacturer="AUTO",  # Auto-detect manufacturer
        enable_images=True,          # Extract images
        enable_ocr=True,              # OCR on images
        enable_vision=True,           # Vision AI analysis
        enable_r2_storage=enable_r2,  # Upload to R2 (if configured)
        enable_embeddings=True,       # Generate embeddings
        max_retries=2
    )
    
    # Process each PDF
    import shutil
    import gzip
    
    total_success = 0
    total_failed = 0
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*80}")
        print(f"  📄 PROCESSING [{idx}/{len(pdf_files)}]: {pdf_file.name}")
        print(f"{'='*80}\n")
        
        # Handle .pdfz (compressed) files
        working_pdf = pdf_file
        temp_decompressed = None
        
        if pdf_file.suffix.lower() == '.pdfz':
            print(f"🗜️  Decompressing .pdfz file...")
            temp_decompressed = pdf_file.with_suffix('.pdf')
            try:
                with gzip.open(pdf_file, 'rb') as f_in:
                    with open(temp_decompressed, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                working_pdf = temp_decompressed
                print(f"✅ Decompressed to: {working_pdf.name}\n")
            except Exception as e:
                # Check if it's actually a normal PDF (not compressed)
                try:
                    with open(pdf_file, 'rb') as f:
                        header = f.read(4)
                        if header.startswith(b'%PDF'):
                            print(f"⚠️  Not gzipped - treating as normal PDF")
                            # Just rename to .pdf for processing
                            shutil.copy(pdf_file, temp_decompressed)
                            working_pdf = temp_decompressed
                            print(f"✅ Ready to process: {working_pdf.name}\n")
                        else:
                            print(f"❌ Failed to decompress: {e}")
                            total_failed += 1
                            continue
                except Exception as e2:
                    print(f"❌ Failed to decompress: {e}")
                    total_failed += 1
                    continue
        
        print("⏳ Processing... This may take several minutes...\n")
        
        # Process!
        result = pipeline.process_document(
            file_path=working_pdf,
            document_type="service_manual",
            manufacturer="AUTO"  # Auto-detect
        )
    
        # Results for this PDF
        print("\n" + "="*80)
        if result['success']:
            print(f"  ✅ SUCCESS [{idx}/{len(pdf_files)}]")
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
                links = processing.get('links', [])
                videos = processing.get('videos', [])
                images = processing.get('images', [])
                chunks = processing.get('chunks', [])
                
                print(f"\n📦 Extracted:")
                print(f"   Products: {len(products)}")
                print(f"   Error Codes: {len(error_codes)}")
                print(f"   Versions: {len(versions)}")
                print(f"   Links: {len(links)}")
                print(f"   Videos: {len(videos)}")
                print(f"   Images: {len(images)}")
                print(f"   Chunks: {len(chunks)}")
                
                # R2 Upload Results
                if enable_r2 and 'r2_storage' in result['results']:
                    r2_result = result['results']['r2_storage']
                    if r2_result.get('success'):
                        print(f"\n☁️  R2 Storage:")
                        print(f"   Uploaded: {r2_result.get('uploaded_count', 0)} images")
                
                # Embeddings
                if 'embeddings' in result['results']:
                    emb_result = result['results']['embeddings']
                    if emb_result.get('success'):
                        print(f"\n🔮 Embeddings:")
                        print(f"   Created: {emb_result.get('embeddings_created', 0):,}")
                        print(f"   Time: {emb_result.get('processing_time', 0):.1f}s")
            
            # Move to processed folder
            try:
                dest = processed_folder / pdf_file.name
                shutil.move(str(pdf_file), str(dest))
                print(f"\n✅ Moved to processed/")
                total_success += 1
            except Exception as e:
                print(f"\n⚠️  Could not move file: {e}")
            
            # Cleanup temp file
            if temp_decompressed and temp_decompressed.exists():
                temp_decompressed.unlink()
            
        else:
            print(f"  ❌ FAILED [{idx}/{len(pdf_files)}]")
            print("="*80)
            print(f"\n💥 Error: {result.get('error')}")
            total_failed += 1
            
            # Cleanup temp file even on failure
            if temp_decompressed and temp_decompressed.exists():
                temp_decompressed.unlink()
    
    # Final Summary
    print("\n" + "="*80)
    print("  🎉 BATCH PROCESSING COMPLETE!")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   Total PDFs: {len(pdf_files)}")
    print(f"   ✅ Successful: {total_success}")
    print(f"   ❌ Failed: {total_failed}")
    print(f"\n💡 Processed files moved to:")
    print(f"   {processed_folder.absolute()}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
