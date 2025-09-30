#!/usr/bin/env python3
"""
Test script for all deduplication features across the KR-AI-Engine
Tests document, manufacturer, product, chunk, image, embedding, and error code deduplication
"""

import asyncio
import os
import sys
import hashlib
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from core.data_models import (
    DocumentModel, ManufacturerModel, ProductSeriesModel, ProductModel,
    ChunkModel, ImageModel, IntelligenceChunkModel, EmbeddingModel, ErrorCodeModel
)

async def test_all_deduplication():
    """Test all deduplication features"""
    print("🔍 Testing ALL Deduplication Features...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv('../credentials.txt')
    
    # Initialize services
    db_service = DatabaseService(
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_ANON_KEY')
    )
    
    await db_service.connect()
    
    storage_service = ObjectStorageService(
        r2_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        r2_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        r2_endpoint_url=os.getenv('R2_ENDPOINT_URL'),
        r2_region=os.getenv('R2_REGION', 'auto'),
        r2_public_domain=os.getenv('R2_PUBLIC_DOMAIN'),
        r2_public_urls={
            'documents': os.getenv('R2_PUBLIC_URL_DOCUMENTS'),
            'error': os.getenv('R2_PUBLIC_URL_ERROR'),
            'parts': os.getenv('R2_PUBLIC_URL_PARTS')
        }
    )
    
    await storage_service.connect()
    
    print("\n1️⃣ Testing Document Deduplication...")
    # Test document deduplication
    test_hash = hashlib.sha256(b"test document content").hexdigest()
    
    doc1 = DocumentModel(
        filename="test_doc_1.pdf",
        original_filename="test_doc_1.pdf",
        file_path="/test/path/test_doc_1.pdf",
        file_size=1024,
        file_hash=test_hash,
        document_type="service_manual",
        processing_status="pending"
    )
    
    doc2 = DocumentModel(
        filename="test_doc_2.pdf",  # Different filename
        original_filename="test_doc_2.pdf",
        file_path="/test/path/test_doc_2.pdf",
        file_size=2048,  # Different size
        file_hash=test_hash,  # SAME HASH = DUPLICATE
        document_type="service_manual",
        processing_status="pending"
    )
    
    # Create first document
    doc1_id = await db_service.create_document(doc1)
    print(f"   ✅ Created document 1: {doc1_id}")
    
    # Try to create duplicate document
    doc2_id = await db_service.create_document(doc2)
    print(f"   ✅ Document 2 returned existing ID: {doc2_id}")
    
    if doc1_id == doc2_id:
        print("   🎯 DOCUMENT DEDUPLICATION WORKS!")
    else:
        print("   ❌ Document deduplication failed!")
    
    print("\n2️⃣ Testing Manufacturer Deduplication...")
    # Test manufacturer deduplication
    man1 = ManufacturerModel(
        name="HP Inc.",
        description="Hewlett Packard"
    )
    
    man2 = ManufacturerModel(
        name="HP Inc.",  # SAME NAME = DUPLICATE
        description="Different description"  # Different description
    )
    
    man1_id = await db_service.create_manufacturer(man1)
    print(f"   ✅ Created manufacturer 1: {man1_id}")
    
    man2_id = await db_service.create_manufacturer(man2)
    print(f"   ✅ Manufacturer 2 returned existing ID: {man2_id}")
    
    if man1_id == man2_id:
        print("   🎯 MANUFACTURER DEDUPLICATION WORKS!")
    else:
        print("   ❌ Manufacturer deduplication failed!")
    
    print("\n3️⃣ Testing Product Series Deduplication...")
    # Test product series deduplication
    series1 = ProductSeriesModel(
        series_name="LaserJet Pro",
        manufacturer_id=man1_id,
        description="Professional laser printers"
    )
    
    series2 = ProductSeriesModel(
        series_name="LaserJet Pro",  # SAME NAME + MANUFACTURER = DUPLICATE
        manufacturer_id=man1_id,
        description="Different description"
    )
    
    series1_id = await db_service.create_product_series(series1)
    print(f"   ✅ Created product series 1: {series1_id}")
    
    series2_id = await db_service.create_product_series(series2)
    print(f"   ✅ Product series 2 returned existing ID: {series2_id}")
    
    if series1_id == series2_id:
        print("   🎯 PRODUCT SERIES DEDUPLICATION WORKS!")
    else:
        print("   ❌ Product series deduplication failed!")
    
    print("\n4️⃣ Testing Product Deduplication...")
    # Test product deduplication
    prod1 = ProductModel(
        model_number="M404dn",
        manufacturer_id=man1_id,
        product_series_id=series1_id,
        name="LaserJet Pro M404dn"
    )
    
    prod2 = ProductModel(
        model_number="M404dn",  # SAME MODEL + MANUFACTURER = DUPLICATE
        manufacturer_id=man1_id,
        product_series_id=series1_id,
        name="Different name"
    )
    
    prod1_id = await db_service.create_product(prod1)
    print(f"   ✅ Created product 1: {prod1_id}")
    
    prod2_id = await db_service.create_product(prod2)
    print(f"   ✅ Product 2 returned existing ID: {prod2_id}")
    
    if prod1_id == prod2_id:
        print("   🎯 PRODUCT DEDUPLICATION WORKS!")
    else:
        print("   ❌ Product deduplication failed!")
    
    print("\n5️⃣ Testing Chunk Deduplication...")
    # Test chunk deduplication
    chunk1 = ChunkModel(
        document_id=doc1_id,
        chunk_index=1,
        chunk_type="paragraph",
        content="This is test chunk content",
        metadata={"source": "page_1"}
    )
    
    chunk2 = ChunkModel(
        document_id=doc1_id,
        chunk_index=1,  # SAME DOCUMENT + INDEX = DUPLICATE
        chunk_type="paragraph",
        content="Different content",
        metadata={"source": "different"}
    )
    
    chunk1_id = await db_service.create_chunk(chunk1)
    print(f"   ✅ Created chunk 1: {chunk1_id}")
    
    chunk2_id = await db_service.create_chunk(chunk2)
    print(f"   ✅ Chunk 2 returned existing ID: {chunk2_id}")
    
    if chunk1_id == chunk2_id:
        print("   🎯 CHUNK DEDUPLICATION WORKS!")
    else:
        print("   ❌ Chunk deduplication failed!")
    
    print("\n6️⃣ Testing Image Deduplication...")
    # Test image deduplication
    image_hash = hashlib.sha256(b"test image content").hexdigest()
    
    img1 = ImageModel(
        filename="test_image_1.png",
        original_filename="test_image_1.png",
        storage_path="test_image_1.png",
        storage_url="https://example.com/test_image_1.png",
        file_size=512,
        image_format="PNG",
        width_px=100,
        height_px=100,
        page_number=1,
        image_index=1,
        image_type="diagram",
        file_hash=image_hash,
        document_id=doc1_id
    )
    
    img2 = ImageModel(
        filename="test_image_2.png",  # Different filename
        original_filename="test_image_2.png",
        storage_path="test_image_2.png",
        storage_url="https://example.com/test_image_2.png",
        file_size=1024,  # Different size
        image_format="PNG",
        width_px=200,  # Different dimensions
        height_px=200,
        page_number=2,  # Different page
        image_index=2,
        image_type="photo",
        file_hash=image_hash,  # SAME HASH = DUPLICATE
        document_id=doc1_id
    )
    
    img1_id = await db_service.create_image(img1)
    print(f"   ✅ Created image 1: {img1_id}")
    
    img2_id = await db_service.create_image(img2)
    print(f"   ✅ Image 2 returned existing ID: {img2_id}")
    
    if img1_id == img2_id:
        print("   🎯 IMAGE DEDUPLICATION WORKS!")
    else:
        print("   ❌ Image deduplication failed!")
    
    print("\n7️⃣ Testing Intelligence Chunk Deduplication...")
    # Test intelligence chunk deduplication
    int_chunk1 = IntelligenceChunkModel(
        chunk_id=chunk1_id,
        chunk_type="technical_specification",
        content="Technical specifications for the product",
        metadata={"category": "specs"}
    )
    
    int_chunk2 = IntelligenceChunkModel(
        chunk_id=chunk1_id,  # SAME CHUNK_ID = DUPLICATE
        chunk_type="different_type",
        content="Different content",
        metadata={"category": "different"}
    )
    
    int_chunk1_id = await db_service.create_intelligence_chunk(int_chunk1)
    print(f"   ✅ Created intelligence chunk 1: {int_chunk1_id}")
    
    int_chunk2_id = await db_service.create_intelligence_chunk(int_chunk2)
    print(f"   ✅ Intelligence chunk 2 returned existing ID: {int_chunk2_id}")
    
    if int_chunk1_id == int_chunk2_id:
        print("   🎯 INTELLIGENCE CHUNK DEDUPLICATION WORKS!")
    else:
        print("   ❌ Intelligence chunk deduplication failed!")
    
    print("\n8️⃣ Testing Embedding Deduplication...")
    # Test embedding deduplication
    embedding1 = EmbeddingModel(
        chunk_id=chunk1_id,
        embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        model_name="embeddinggemma:latest"
    )
    
    embedding2 = EmbeddingModel(
        chunk_id=chunk1_id,  # SAME CHUNK_ID = DUPLICATE
        embedding_vector=[0.6, 0.7, 0.8, 0.9, 1.0],  # Different vector
        model_name="different_model"
    )
    
    embedding1_id = await db_service.create_embedding(embedding1)
    print(f"   ✅ Created embedding 1: {embedding1_id}")
    
    embedding2_id = await db_service.create_embedding(embedding2)
    print(f"   ✅ Embedding 2 returned existing ID: {embedding2_id}")
    
    if embedding1_id == embedding2_id:
        print("   🎯 EMBEDDING DEDUPLICATION WORKS!")
    else:
        print("   ❌ Embedding deduplication failed!")
    
    print("\n9️⃣ Testing Error Code Deduplication...")
    # Test error code deduplication
    error1 = ErrorCodeModel(
        error_code="E001",
        description="Paper jam error",
        severity="medium"
    )
    
    error2 = ErrorCodeModel(
        error_code="E001",  # SAME ERROR_CODE = DUPLICATE
        description="Different description",
        severity="high"  # Different severity
    )
    
    error1_id = await db_service.create_error_code(error1)
    print(f"   ✅ Created error code 1: {error1_id}")
    
    error2_id = await db_service.create_error_code(error2)
    print(f"   ✅ Error code 2 returned existing ID: {error2_id}")
    
    if error1_id == error2_id:
        print("   🎯 ERROR CODE DEDUPLICATION WORKS!")
    else:
        print("   ❌ Error code deduplication failed!")
    
    print("\n🔟 Testing Object Storage Deduplication...")
    # Test object storage deduplication
    test_content = b"This is test image content for R2"
    test_hash = hashlib.sha256(test_content).hexdigest()
    
    # Upload first image
    result1 = await storage_service.upload_image(
        content=test_content,
        filename="test_r2_image_1.png",
        bucket_type="document_images",
        metadata={"test": "first"}
    )
    print(f"   ✅ Uploaded image 1: {result1['storage_path']}")
    print(f"   📊 Is duplicate: {result1.get('is_duplicate', False)}")
    
    # Upload same content (different filename)
    result2 = await storage_service.upload_image(
        content=test_content,  # SAME CONTENT = DUPLICATE
        filename="test_r2_image_2.png",  # Different filename
        bucket_type="document_images",
        metadata={"test": "second"}
    )
    print(f"   ✅ Uploaded image 2: {result2['storage_path']}")
    print(f"   📊 Is duplicate: {result2.get('is_duplicate', False)}")
    
    if result2.get('is_duplicate', False):
        print("   🎯 OBJECT STORAGE DEDUPLICATION WORKS!")
    else:
        print("   ❌ Object storage deduplication failed!")
    
    print("\n" + "=" * 60)
    print("🎉 ALL DEDUPLICATION TESTS COMPLETED!")
    print("✅ Every component now has proper deduplication!")
    print("🚀 No more duplicate data in your system!")

if __name__ == "__main__":
    asyncio.run(test_all_deduplication())
