"""
Test Storage Processor

Tests R2 upload, download, presigned URLs, and storage organization.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.processors.storage_processor import StorageProcessor


def test_configuration():
    """Test 1: Check R2 configuration"""
    print("="*80)
    print("TEST 1: R2 Configuration")
    print("="*80)
    
    storage = StorageProcessor()
    
    if storage.is_configured():
        print("\n✅ R2 is configured")
        print(f"   Bucket: {storage.bucket_name}")
        print(f"   Endpoint: {storage.endpoint_url[:50]}...")
        return True
    else:
        print("\n❌ R2 is NOT configured")
        print("\n   Set these environment variables:")
        print("   - R2_ENDPOINT_URL")
        print("   - R2_ACCESS_KEY_ID")
        print("   - R2_SECRET_ACCESS_KEY")
        print("   - R2_BUCKET_NAME (optional, defaults to 'krai-documents')")
        return False


def test_storage_statistics():
    """Test 2: Get storage statistics"""
    print("\n" + "="*80)
    print("TEST 2: Storage Statistics")
    print("="*80)
    
    storage = StorageProcessor()
    
    if not storage.is_configured():
        print("\n⚠️  Skipped: R2 not configured")
        return False
    
    try:
        stats = storage.get_storage_statistics()
        
        print("\n✅ Statistics retrieved")
        print(f"\n   📊 Storage Stats:")
        print(f"      Total Documents: {stats.get('total_documents', 0)}")
        print(f"      Total Size: {stats.get('total_size_mb', 0)} MB")
        
        if 'by_type' in stats and stats['by_type']:
            print(f"\n   📁 By Type:")
            for doc_type, info in stats['by_type'].items():
                print(f"      {doc_type}: {info['count']} documents ({info['size'] / (1024*1024):.1f} MB)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False


def test_upload_document():
    """Test 3: Upload document to R2"""
    print("\n" + "="*80)
    print("TEST 3: Document Upload")
    print("="*80)
    
    storage = StorageProcessor()
    
    if not storage.is_configured():
        print("\n⚠️  Skipped: R2 not configured")
        return False
    
    # Find test PDF
    test_pdf = Path("../../CX833 CX961 CX962 CX963 XC8355 XC9635 XC9645 SM.pdf")
    
    if not test_pdf.exists():
        test_pdf = Path("C:/Users/haast/Docker/KRAI-minimal/CX833 CX961 CX962 CX963 XC8355 XC9635 XC9645 SM.pdf")
    
    if not test_pdf.exists():
        print("\n⚠️  Skipped: Test PDF not found")
        return False
    
    print(f"\n📄 Uploading: {test_pdf.name}")
    print(f"   Size: {test_pdf.stat().st_size / (1024*1024):.1f} MB")
    
    # Upload
    document_id = uuid4()
    
    try:
        result = storage.upload_document(
            document_id=document_id,
            file_path=test_pdf,
            manufacturer="Lexmark",
            document_type="service_manual",
            metadata={'test': True}
        )
        
        if result['success']:
            print(f"\n✅ Upload successful!")
            print(f"   Storage Path: {result['storage_path']}")
            print(f"   Storage URL: {result['storage_url'][:60]}...")
            print(f"   Bucket: {result['bucket']}")
            
            # Store for next tests
            global uploaded_path
            uploaded_path = result['storage_path']
            
            return True
        else:
            print(f"\n❌ Upload failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_presigned_url():
    """Test 4: Generate presigned URL"""
    print("\n" + "="*80)
    print("TEST 4: Presigned URL")
    print("="*80)
    
    storage = StorageProcessor()
    
    if not storage.is_configured():
        print("\n⚠️  Skipped: R2 not configured")
        return False
    
    if 'uploaded_path' not in globals():
        print("\n⚠️  Skipped: No uploaded document")
        return False
    
    try:
        # Generate URL (1 hour expiration)
        url = storage.generate_presigned_url(
            storage_path=uploaded_path,
            expiration=3600
        )
        
        if url:
            print(f"\n✅ Presigned URL generated!")
            print(f"   URL: {url[:80]}...")
            print(f"   Expires in: 1 hour")
            
            # Test if URL is accessible
            import requests
            response = requests.head(url, timeout=10)
            
            if response.status_code == 200:
                print(f"\n✅ URL is accessible!")
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                print(f"   Content-Length: {int(response.headers.get('Content-Length', 0)) / (1024*1024):.1f} MB")
            else:
                print(f"\n⚠️  URL returned status: {response.status_code}")
            
            return True
        else:
            print(f"\n❌ Failed to generate URL")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_download_document():
    """Test 5: Download document from R2"""
    print("\n" + "="*80)
    print("TEST 5: Document Download")
    print("="*80)
    
    storage = StorageProcessor()
    
    if not storage.is_configured():
        print("\n⚠️  Skipped: R2 not configured")
        return False
    
    if 'uploaded_path' not in globals():
        print("\n⚠️  Skipped: No uploaded document")
        return False
    
    # Download to temp location
    download_path = Path("../../temp_download.pdf")
    
    print(f"\n📥 Downloading: {uploaded_path}")
    print(f"   To: {download_path}")
    
    try:
        success = storage.download_document(
            storage_path=uploaded_path,
            local_path=download_path
        )
        
        if success and download_path.exists():
            print(f"\n✅ Download successful!")
            print(f"   File size: {download_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Cleanup
            download_path.unlink()
            print(f"   ✓ Temp file cleaned up")
            
            return True
        else:
            print(f"\n❌ Download failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_list_documents():
    """Test 6: List documents in R2"""
    print("\n" + "="*80)
    print("TEST 6: List Documents")
    print("="*80)
    
    storage = StorageProcessor()
    
    if not storage.is_configured():
        print("\n⚠️  Skipped: R2 not configured")
        return False
    
    try:
        # List all documents
        print("\n📋 Listing all documents...")
        documents = storage.list_documents(max_keys=10)
        
        if documents:
            print(f"\n✅ Found {len(documents)} documents")
            
            for i, doc in enumerate(documents[:5], 1):
                print(f"\n   {i}. {doc['key']}")
                print(f"      Size: {doc['size'] / (1024*1024):.1f} MB")
                print(f"      Modified: {doc['last_modified']}")
            
            if len(documents) > 5:
                print(f"\n   ... and {len(documents) - 5} more")
            
            return True
        else:
            print(f"\n⚠️  No documents found")
            return True  # Not an error, just empty
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Run all storage tests"""
    
    print("\n" + "🧪"*40)
    print("\n   STORAGE PROCESSOR - TEST SUITE")
    print("   Cloudflare R2 Integration")
    print("\n" + "🧪"*40)
    
    results = {}
    
    # Test 1: Configuration
    results['configuration'] = test_configuration()
    
    if not results['configuration']:
        print("\n" + "="*80)
        print("⚠️  R2 not configured - cannot run further tests")
        print("="*80)
        return
    
    # Test 2: Statistics
    results['statistics'] = test_storage_statistics()
    
    # Test 3: Upload
    results['upload'] = test_upload_document()
    
    # Test 4: Presigned URL
    results['presigned_url'] = test_presigned_url()
    
    # Test 5: Download
    results['download'] = test_download_document()
    
    # Test 6: List
    results['list'] = test_list_documents()
    
    # Summary
    print("\n" + "="*80)
    print("  📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n  Results: {passed}/{total} passed")
    
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"    {status} {test_name}")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print("\n  ⚠️  SOME TESTS FAILED")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
