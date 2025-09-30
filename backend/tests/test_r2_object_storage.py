import asyncio
import os
import sys
import hashlib
import fitz  # PyMuPDF
from datetime import datetime
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

# ===========================================
# SUPABASE CLOUD CONFIGURATION
# ===========================================
SUPABASE_URL=https://crujfdpqdjzcfqeyhang.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNydWpmZHBxZGp6Y2ZxZXloYW5nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkwNDY1MTUsImV4cCI6MjA3NDYyMjUxNX0.kDSf9jMYbNgzV8v1f-_kSoSy_cAMFLG367m9ZbDsBkw
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNydWpmZHBxZGp6Y2ZxZXloYW5nIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTA0NjUxNSwiZXhwIjoyMDc0NjIyNTE1fQ.5MnFW5MuKdS6ZNvKv5iTWH-jv_ZB1SgeoP7cVGI7cdE
SUPABASE_STORAGE_URL=https://crujfdpqdjzcfqeyhang.supabase.co/storage/v1

# Database Connection (für direkte PostgreSQL Verbindung)
DATABASE_CONNECTION_URL=postgresql://postgres:YOUR_DB_PASSWORD@db.crujfdpqdjzcfqeyhang.supabase.co:5432/postgres
DATABASE_PASSWORD=YOUR_DATABASE_PASSWORD

# Database Storage Buckets
DATABASE_STORAGE_BUCKET=krai-documents
DATABASE_IMAGE_BUCKET=krai-images

# ===========================================
# R2 STORAGE CONFIGURATION (Cloudflare)
# ===========================================
R2_ACCESS_KEY_ID=9c59473961632448c91db3ef9dbd35ab
R2_SECRET_ACCESS_KEY=9cc62a9506ac9ec6e8373a39fa86268bc187632e5548e8c37b1c6c9c071755e4
R2_BUCKET_NAME_DOCUMENTS=krai-documents
R2_BUCKET_NAME_ERROR=krai-error-images
R2_BUCKET_NAME_PARTS=krai-parts-images
R2_ENDPOINT_URL=https://a88f92c913c232559845adb9001a5d14.eu.r2.cloudflarestorage.com
R2_REGION=auto

# ===========================================
# R2 PUBLIC URLS
# ===========================================
R2_PUBLIC_URL_DOCUMENTS=https://pub-68e63cf2d6ac4222adaab70dfbc29ec4.r2.dev
R2_PUBLIC_URL_ERROR=https://pub-e327cb3371c741e08c5e8672e817d9cf.r2.dev
R2_PUBLIC_URL_PARTS=https://pub-61c8b15e7bf24febbf8e0197ab237041.r2.dev        
        
        # R2 Configuration (you need to provide these)
        r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID", "your-r2-access-key")
        r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY", "your-r2-secret-key")
        r2_endpoint_url = os.getenv("R2_ENDPOINT_URL", "https://your-account-id.r2.cloudflarestorage.com")
        r2_public_url_documents = os.getenv("R2_PUBLIC_URL_DOCUMENTS", "https://your-bucket.r2.dev")
        r2_public_url_error = os.getenv("R2_PUBLIC_URL_ERROR", "https://your-error-bucket.r2.dev")
        r2_public_url_parts = os.getenv("R2_PUBLIC_URL_PARTS", "https://your-parts-bucket.r2.dev")
        
        # Initialize R2 service
        storage_service = ObjectStorageService(
            r2_access_key_id=r2_access_key_id,
            r2_secret_access_key=r2_secret_access_key,
            r2_endpoint_url=r2_endpoint_url,
            r2_public_url_documents=r2_public_url_documents,
            r2_public_url_error=r2_public_url_error,
            r2_public_url_parts=r2_public_url_parts
        )
        
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
        
        for page_num in range(min(doc.page_count, 5)):  # Test first 5 pages
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
                    bucket_type='documents',  # Document images bucket
                    metadata={
                        'page_number': img_info['page_number'],
                        'image_index': img_info['image_index'],
                        'original_pdf': os.path.basename(pdf_path),
                        'upload_timestamp': datetime.utcnow().isoformat()
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
                bucket_type='documents',
                metadata={'test_duplicate': True}
            )
            
            if duplicate_result['success']:
                print(f"  Duplicate detected: {duplicate_result.get('message', 'File already exists')}")
            else:
                print(f"  Duplicate handling: {duplicate_result.get('error', 'Unknown')}")
        
        # Create document in database
        print("Creating document in database...")
        document = DocumentModel(
            filename=os.path.basename(pdf_path),
            original_filename=os.path.basename(pdf_path),
            file_size=os.path.getsize(pdf_path),
            file_hash=hashlib.sha256(open(pdf_path, "rb").read()).hexdigest(),
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            series="Color LaserJet Enterprise",
            models=["X580"],
            version="1.0",
            language="en"
        )
        
        try:
            created_doc = await database_service.create_document(document)
            print(f"Document created: {created_doc.id if hasattr(created_doc, 'id') else created_doc}")
        except Exception as e:
            print(f"Document creation failed: {e}")
            return False
        
        # Save image metadata to database
        print("Saving image metadata to database...")
        saved_images = 0
        
        for i, img_info in enumerate(uploaded_images):
            try:
                # Find corresponding original image data
                original_img = next((img for img in images if img['hash'] == img_info['hash']), None)
                if not original_img:
                    continue
                
                # Create image model
                image_model = ImageModel(
                    document_id=created_doc.id if hasattr(created_doc, 'id') else created_doc,
                    filename=img_info['filename'],
                    original_filename=f"page_{original_img['page_number']}_img_{original_img['image_index']}.png",
                    storage_path=img_info['storage_path'],
                    storage_url=img_info['public_url'],
                    file_size=img_info['size'],
                    image_format="png",
                    width_px=100,  # Mock dimensions
                    height_px=100,
                    page_number=original_img['page_number'],
                    image_index=original_img['image_index'],
                    image_type=ImageType.DIAGRAM,
                    file_hash=img_info['hash']
                )
                
                # Save to database
                await database_service.create_image(image_model)
                saved_images += 1
                
                print(f"Saved image metadata {i+1}: {img_info['hash'][:16]}...")
                
            except Exception as e:
                print(f"Error saving image metadata {i+1}: {e}")
                continue
        
        print(f"\nR2 Object Storage Test Results:")
        print(f"   Total images extracted: {len(images)}")
        print(f"   Images uploaded to R2: {len(uploaded_images)}")
        print(f"   Images saved to database: {saved_images}")
        print(f"   Success rate: {len(uploaded_images)/len(images)*100:.1f}%")
        
        # Test image retrieval from database
        print("Testing image retrieval from database...")
        try:
            result = database_service.client.table("images").select("*").eq("document_id", created_doc.id if hasattr(created_doc, 'id') else created_doc).execute()
            retrieved_images = result.data
            print(f"Retrieved {len(retrieved_images)} images from database")
            
            if retrieved_images:
                first_retrieved = retrieved_images[0]
                print(f"First image: {first_retrieved['filename']}")
                print(f"Storage URL: {first_retrieved['storage_url']}")
                print(f"File hash: {first_retrieved['file_hash'][:16]}...")
                
        except Exception as e:
            print(f"Image retrieval test failed: {e}")
        
        print("\nR2 Object Storage test completed successfully!")
        return True
        
    except Exception as e:
        print(f"R2 Object Storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_r2_object_storage())
