"""
PRODUCTION MODE - Process Document with ALL Features

This script processes a document in FULL PRODUCTION MODE:
- All stages enabled
- R2 Storage activated (images uploaded to Cloudflare)
- Embeddings generated (semantic search ready)
- Live Supabase connection
- No mocks, all real processing
- OEM sync via standard Supabase API (no psycopg2)
- Interactive confirmation with dynamic yes/no defaults
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from multiple .env files
# Priority: Later files override earlier ones
project_root = Path(__file__).parent.parent.parent

# Load all .env files in priority order
env_files = [
    '.env',           # Base config (lowest priority)
    '.env.database',  # Database credentials
    '.env.storage',   # R2/Storage config
    '.env.external',  # External APIs (YouTube, etc.)
    '.env.pipeline',  # Pipeline settings
    '.env.ai',        # AI settings (LLM_MAX_PAGES, OLLAMA models, highest priority)
]

for env_file in env_files:
    env_path = project_root / env_file
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✅ Loaded: {env_file}")
    else:
        print(f"⚠️  Not found: {env_file}")

# Add project root and backend directory to path for absolute imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

# Change to backend directory for imports to work
original_dir = os.getcwd()
os.chdir(backend_dir)

# Now import with relative paths (we're in backend dir)
from processors.imports import get_supabase_client, get_logger
from processors.master_pipeline import MasterPipeline
from processors.__version__ import __version__, __commit__, __date__
from supabase import create_client

# Import GPU utils from API directory
sys.path.insert(0, str(backend_dir / 'api'))
try:
    from gpu_utils import GPUManager
    gpu_manager = GPUManager()
except ImportError:
    print("⚠️  GPU Utils not available")
    gpu_manager = None

# Change back
os.chdir(original_dir)


def print_section(title: str) -> None:
    """Print a divider section with a centered title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_banner() -> None:
    """Show unified processor banner using shared version metadata."""
    print_section(f"🚀 PRODUCTION PROCESSOR v{__version__}")
    print(f"  Commit: {__commit__} | Date: {__date__}")
    print("  📋 OEM Sync: Standard Supabase API (no psycopg2)")
    print(f"\n🔍 DEBUG: LLM_MAX_PAGES = {os.getenv('LLM_MAX_PAGES', 'NOT SET')}")

    if gpu_manager:
        gpu_info = gpu_manager.get_info()
        print("\n🖥️  GPU Status:")
        print(f"  • USE_GPU: {gpu_info.get('use_gpu')}")
        print(f"  • Device backend: {gpu_info.get('device')} (OpenCV: {gpu_info.get('opencv_backend')})")

        if gpu_info.get('gpu_available'):
            print(f"  • Active CUDA device: {gpu_info.get('cuda_device_index')} -> {gpu_info.get('cuda_device_name')}")
            print(f"  • Visible devices: {gpu_info.get('cuda_visible_devices')}")
            print(f"  • Compute capability: {gpu_info.get('cuda_compute_capability')}")
            print(f"  • Total memory: {gpu_info.get('cuda_memory_total_gb')} GB")
            if not gpu_info.get('opencv_cuda_available'):
                print("  • OpenCV CUDA: NOT available, using CPU fallback")
        else:
            print("  • CUDA not available – using CPU pipelines")


def confirm(prompt: str, default: bool = False) -> bool:
    """Interactive yes/no confirmation with sensible defaults."""
    choices = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{choices}]: ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please enter 'y' or 'n'.")


def main():
    """Process document in FULL PRODUCTION MODE"""
    
    print_banner()
    print_section("PRODUCTION MODE - FULL PROCESSING")
    
    print("\n🔧 Configuration:")
    print("   - Supabase: LIVE")
    print("   - R2 Storage: ENABLED (Images will be uploaded)")
    print("   - Embeddings: ENABLED (Semantic search ready)")
    print("   - OCR: ENABLED (Tesseract)")
    print("   - Vision AI: ENABLED (LLaVA)")
    print("   - All stages: ACTIVE")
    
    # Initialize GPU if enabled
    if gpu_manager:
        print("\n🎮 GPU Configuration:")
        use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'
        if use_gpu:
            print("   - GPU Acceleration: ENABLED")
            gpu_info = gpu_manager.get_info()
            if gpu_info.get('gpu_available'):
                print(f"   - CUDA Available: YES")
                if 'cuda_device_name' in gpu_info:
                    print(f"   - Device: {gpu_info['cuda_device_name']}")
                if gpu_manager.is_opencv_cuda_available():
                    print("   - OpenCV CUDA: Available")
                    gpu_manager.configure_opencv()
                else:
                    print("   - OpenCV CUDA: Not available (using CPU)")
            else:
                print("   - CUDA: Not available (using CPU)")
        else:
            print("   - GPU Acceleration: DISABLED (USE_GPU=false)")
    
    # Initialize Supabase
    print("\n📊 Step 1/4: Connecting to Supabase...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase connected")
    # Check Ollama
    print("\n📊 Step 3/4: Checking Ollama...")
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    embedding_model = os.getenv('OLLAMA_MODEL_EMBEDDING', 'nomic-embed-text:latest')
    vision_model = os.getenv('OLLAMA_MODEL_VISION', 'llava:7b')
    print(f"   Ollama URL: {ollama_url}")
    
    try:
        import requests
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            # Extract base model name (remove :tag)
            embedding_base = embedding_model.split(':')[0]
            vision_base = vision_model.split(':')[0]
            
            has_embedding = any(embedding_base in m.get('name', '') for m in models)
            has_vision = any(vision_base in m.get('name', '') for m in models)
            
            print(f"✅ Ollama available")
            print(f"   Embedding model: {'✅' if has_embedding else '❌'} {embedding_model}")
            print(f"   Vision model: {'✅' if has_vision else '❌'} {vision_model}")
            
            if not has_embedding:
                print(f"\n⚠️  WARNING: {embedding_model} not found!")
                print(f"   Run: ollama pull {embedding_model}")
            if not has_vision:
                print(f"\n⚠️  WARNING: {vision_model} not found!")
                print(f"   Run: ollama pull {vision_model}")
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
    print_section("READY TO PROCESS IN PRODUCTION MODE")
    print(f"\n⚠️  This will process {len(pdf_files)} PDF(s):")
    print("   1. Process each complete PDF")
    print("   2. Extract all text, products, error codes, versions, links")
    print("   3. Process all images with OCR + Vision AI")
    if enable_r2:
        print("   4. Upload images to object storage")
    else:
        print("   4. Skip object storage upload (disabled)")
    print("   5. Generate 768-dim embeddings for all chunks")
    print("   6. Store everything in Supabase")
    print("   7. Move processed PDFs to processed/ folder")
    
    # Ask for confirmation
    if not confirm("Continue with FULL PRODUCTION processing?", default=False):
        print("\n❌ Aborted by user")
        return
    
    # Initialize Pipeline with ALL FEATURES
    print_section("🚀 STARTING PRODUCTION PROCESSING")
    
    # Read R2 upload settings from .env
    upload_images = os.getenv('UPLOAD_IMAGES_TO_STORAGE', 'false').lower() == 'true'
    upload_documents = os.getenv('UPLOAD_DOCUMENTS_TO_STORAGE', 'false').lower() == 'true'
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')  # Load YouTube API key from .env.external
    
    pipeline = MasterPipeline(
        supabase_client=supabase,
        manufacturer="AUTO",  # Auto-detect manufacturer
        enable_images=True,          # Extract images
        enable_ocr=True,              # OCR on images
        enable_vision=True,           # Vision AI analysis
        upload_images_to_r2=upload_images,      # Upload images to object storage (from .env)
        upload_documents_to_r2=upload_documents,  # Upload PDFs to object storage (from .env)
        enable_embeddings=True,       # Generate embeddings
        max_retries=2,
        youtube_api_key=youtube_api_key  # Pass YouTube API key for video metadata
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


