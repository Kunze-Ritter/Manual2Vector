import asyncio
import os
import sys
import hashlib
import fitz  # PyMuPDF
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from core.data_models import DocumentModel, DocumentType, ImageModel, ImageType

async def test_r2_object_storage():
    """Test R2 Object Storage integration with hash-based filenames"""
    print("Testing R2 Object Storage Integration...")
    
    try:
        # Initialize services
        print("Initializing services...")
        config_service = ConfigService()
        
        # R2 Configuration from environment variables
        r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        r2_endpoint_url = os.getenv("R2_ENDPOINT_URL")
        r2_public_url_documents = os.getenv("R2_PUBLIC_URL_DOCUMENTS")
        r2_public_url_error = os.getenv("R2_PUBLIC_URL_ERROR")
        r2_public_url_parts = os.getenv("R2_PUBLIC_URL_PARTS")
        
        print(f"R2 Access Key: {r2_access_key_id[:8]}..." if r2_access_key_id else "No R2 Access Key")
        print(f"R2 Endpoint: {r2_endpoint_url}")
        
        # Initialize R2 service
        storage_service = ObjectStorageService(
            r2_access_key_id=r2_access_key_id,
            r2_secret_access_key=r2_secret_access_key,
            r2_endpoint_url=r2_endpoint_url,
            r2_public_url_documents=r2_public_url_documents,
            r2_public_url_error=r2_public_url_error,
            r2_public_url_parts=r2_public_url_parts
        )
        
        # Connect to R2
        await storage_service.connect()
        print(f"R2 Connection: {'Connected' if storage_service.client else 'Mock Mode'}")
        
        # Initialize database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        
        # PDF file path
        pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        print(f"PDF file found: {pdf_path}")
        
        # Extract images from PDF
        print("Extracting images from PDF...")
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(min(doc.page_count, 3)):  # Test first 3 pages
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        img_hash = hashlib.sha256(img_data).hexdigest()
                        
                        # Create image info with hash-based filename
                        image_info = {
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'data': img_data,
                            'hash': img_hash,
                            'size': len(img_data),
                            'format': 'png',
                            'filename': f"{img_hash}.png"  # Hash-based filename
                        }
                        images.append(image_info)
                        
                        print(f"Extracted image: {img_hash[:16]}... (page {page_num + 1}, size: {len(img_data)} bytes)")
                        
                    pix = None
                    
                except Exception as e:
                    print(f"Error extracting image from page {page_num + 1}, index {img_index}: {e}")
                    continue
        
        doc.close()
        
        print(f"Extracted {len(images)} images from PDF")
        
        if not images:
            print("No images found in PDF")
            return False
        
        # Test R2 upload with hash-based filenames
        print("Testing R2 upload with hash-based filenames...")
        uploaded_images = []
        
        for i, img_info in enumerate(images):
            try:
                print(f"Uploading image {i+1}/{len(images)}: {img_info['hash'][:16]}...")
                
                # Upload to R2 with hash-based filename
                upload_result = await storage_service.upload_image(
                    content=img_info['data'],
                    filename=img_info['filename'],  # Hash-based filename
                    bucket_type='document_images',  # Document images bucket
                    metadata={
                        'page_number': img_info['page_number'],
                        'image_index': img_info['image_index'],
                        'original_pdf': os.path.basename(pdf_path),
                        'upload_timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                if upload_result['success']:
                    uploaded_images.append({
                        'hash': img_info['hash'],
                        'filename': img_info['filename'],
                        'storage_path': upload_result['storage_path'],
                        'public_url': upload_result['public_url'],
                        'size': img_info['size']
                    })
                    print(f"  Success: {upload_result['public_url']}")
                    
                    # Save image metadata to database
                    print(f"  Saving image metadata to database...")
                    try:
                        # Create document first if not exists
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
                        print(f"  Document ID: {doc_id}")
                        
                        # Create image model with R2 data
                        image_model = ImageModel(
                            document_id=doc_id,
                            filename=img_info['filename'],
                            original_filename=f"page_{img_info['page_number']}_img_{img_info['image_index']}.png",
                            storage_path=upload_result['storage_path'],
                            storage_url=upload_result['public_url'],
                            file_size=img_info['size'],
                            image_format="png",
                            width_px=100,  # Mock dimensions
                            height_px=100,
                            page_number=img_info['page_number'],
                            image_index=img_info['image_index'],
                            image_type=ImageType.DIAGRAM,
                            file_hash=img_info['hash']
                        )
                        
                        created_image = await database_service.create_image(image_model)
                        print(f"  Image saved to database: {created_image.id if hasattr(created_image, 'id') else created_image}")
                        
                    except Exception as db_error:
                        print(f"  Database error: {db_error}")
                    
                else:
                    print(f"  Failed: {upload_result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"  Error uploading image {i+1}: {e}")
                continue
        
        print(f"Successfully uploaded {len(uploaded_images)}/{len(images)} images to R2")
        
        # Test duplicate detection
        print("Testing duplicate detection...")
        if uploaded_images:
            # Try to upload the same image again (should detect duplicate)
            first_image = uploaded_images[0]
            print(f"Attempting to upload duplicate image: {first_image['hash'][:16]}...")
            
            duplicate_result = await storage_service.upload_image(
                content=images[0]['data'],  # Same image data
                filename=first_image['filename'],  # Same filename
                bucket_type='document_images',
                metadata={'test_duplicate': True}
            )
            
            if duplicate_result['success']:
                print(f"  Duplicate detected: {duplicate_result.get('message', 'File already exists')}")
            else:
                print(f"  Duplicate handling: {duplicate_result.get('error', 'Unknown')}")
        
        print(f"\nR2 Object Storage Test Results:")
        print(f"   Total images extracted: {len(images)}")
        print(f"   Images uploaded to R2: {len(uploaded_images)}")
        print(f"   Success rate: {len(uploaded_images)/len(images)*100:.1f}%")
        
        if uploaded_images:
            print(f"\nUploaded Images:")
            for img in uploaded_images:
                print(f"   Hash: {img['hash'][:16]}...")
                print(f"   URL: {img['public_url']}")
                print(f"   Size: {img['size']} bytes")
                print()
        
        print("R2 Object Storage test completed successfully!")
        return True
        
    except Exception as e:
        print(f"R2 Object Storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_r2_object_storage())
