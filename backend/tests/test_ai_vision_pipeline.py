import asyncio
import os
import sys
import hashlib
import fitz  # PyMuPDF
import base64
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.ai_service import AIService
from services.object_storage_service import ObjectStorageService
from core.data_models import DocumentModel, DocumentType, ImageModel, ImageType

async def test_ai_vision_pipeline():
    """Test AI Vision Pipeline for image processing"""
    print("Testing AI Vision Pipeline...")
    
    try:
        # Initialize services
        print("Initializing services...")
        config_service = ConfigService()
        
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        
        ai_service = AIService()
        # storage_service = ObjectStorageService()  # Temporarily disabled
        
        # PDF file path
        pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        print(f"PDF file found: {pdf_path}")
        file_size = os.path.getsize(pdf_path)
        print(f"File size: {file_size} bytes")
        
        # Extract images from PDF
        print("Extracting images from PDF...")
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(min(doc.page_count, 10)):  # Test first 10 pages
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
                        
                        # Create image info
                        image_info = {
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'data': img_data,
                            'hash': img_hash,
                            'size': len(img_data),
                            'format': 'png'
                        }
                        images.append(image_info)
                        
                        print(f"Extracted image from page {page_num + 1}, index {img_index}, size: {len(img_data)} bytes")
                        
                    pix = None
                    
                except Exception as e:
                    print(f"Error extracting image from page {page_num + 1}, index {img_index}: {e}")
                    continue
        
        doc.close()
        
        print(f"Extracted {len(images)} images from PDF")
        
        if not images:
            print("No images found in PDF")
            return False
        
        # Test AI Vision with first image
        print("Testing AI Vision with first image...")
        first_image = images[0]
        
        # Convert image to base64 for Ollama
        img_base64 = base64.b64encode(first_image['data']).decode('utf-8')
        
        # Test Ollama Vision API
        print("Testing Ollama Vision API...")
        try:
            ollama_url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": "llava:latest",
                "prompt": "Describe this image in detail. What do you see? What type of document is this?",
                "images": [img_base64],
                "stream": False
            }
            
            response = requests.post(ollama_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                ai_description = result.get('response', 'No description generated')
                print(f"AI Vision Analysis:")
                print(f"   Description: {ai_description[:200]}...")
                
                # Test image classification
                print("Testing image classification...")
                classification_payload = {
                    "model": "llava:latest",
                    "prompt": "Classify this image. Is it a diagram, photo, chart, or technical drawing? What is the main subject?",
                    "images": [img_base64],
                    "stream": False
                }
                
                classification_response = requests.post(ollama_url, json=classification_payload, timeout=30)
                
                if classification_response.status_code == 200:
                    classification_result = classification_response.json()
                    classification = classification_result.get('response', 'No classification')
                    print(f"   Classification: {classification[:200]}...")
                else:
                    print(f"Classification failed: {classification_response.status_code}")
                    classification = "Unknown"
                
            else:
                print(f"Vision API failed: {response.status_code}")
                ai_description = "Vision analysis failed"
                classification = "Unknown"
                
        except Exception as e:
            print(f"Vision API error: {e}")
            ai_description = "Vision analysis error"
            classification = "Unknown"
        
        # Create document for images
        print("Creating document for images...")
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
        
        # Process and save images
        print("Processing and saving images...")
        saved_images = 0
        
        for i, img_info in enumerate(images[:5]):  # Test first 5 images
            try:
                # Create image model
                image_model = ImageModel(
                    document_id=created_doc.id if hasattr(created_doc, 'id') else created_doc,
                    filename=f"page_{img_info['page_number']}_img_{img_info['image_index']}.png",
                    original_filename=f"page_{img_info['page_number']}_img_{img_info['image_index']}.png",
                    storage_path=f"images/page_{img_info['page_number']}_img_{img_info['image_index']}.png",
                    storage_url=f"https://mock-storage.com/images/page_{img_info['page_number']}_img_{img_info['image_index']}.png",
                    file_size=img_info['size'],
                    image_format="png",
                    width_px=100,  # Mock dimensions
                    height_px=100,
                    page_number=img_info['page_number'],
                    image_index=img_info['image_index'],
                    image_type=ImageType.DIAGRAM,  # Default to diagram
                    ai_description=ai_description if i == 0 else None,  # Only first image gets AI description
                    file_hash=img_info['hash']
                )
                
                # Save to database
                await database_service.create_image(image_model)
                saved_images += 1
                
                print(f"Saved image {i+1}/5: page {img_info['page_number']}, size {img_info['size']} bytes")
                
            except Exception as e:
                print(f"Error saving image {i+1}: {e}")
                continue
        
        print(f"\nVision Pipeline Results:")
        print(f"   Total images extracted: {len(images)}")
        print(f"   Images saved to database: {saved_images}")
        print(f"   AI Vision analysis: {'Success' if ai_description != 'Vision analysis failed' else 'Failed'}")
        print(f"   Image classification: {'Success' if classification != 'Unknown' else 'Failed'}")
        
        # Test image retrieval
        print("Testing image retrieval from database...")
        try:
            # Get images for our document
            result = database_service.client.table("images").select("*").eq("document_id", created_doc.id if hasattr(created_doc, 'id') else created_doc).execute()
            retrieved_images = result.data
            print(f"Retrieved {len(retrieved_images)} images from database")
            
            if retrieved_images:
                first_retrieved = retrieved_images[0]
                print(f"First image: {first_retrieved['filename']}, page {first_retrieved['page_number']}")
                if first_retrieved.get('ai_description'):
                    print(f"AI Description: {first_retrieved['ai_description'][:100]}...")
                
        except Exception as e:
            print(f"Image retrieval test failed: {e}")
        
        print("\nAI Vision Pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"AI Vision Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_ai_vision_pipeline())
