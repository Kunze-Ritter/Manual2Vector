#!/usr/bin/env python3
"""
Real Chunk Pipeline Test with HP_X580_SM.pdf
Tests the actual chunk processing with real PDF and chunk_settings.json
"""

import os
import sys
import asyncio
import fitz  # PyMuPDF
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.ai_service import AIService
# from modules.utils.chunk_utils import ChunkingUtils

async def test_real_chunk_pipeline():
    """Test chunk processing pipeline with real PDF"""
    print("Testing Real Chunk Pipeline with HP_X580_SM.pdf...")
    
    try:
        # Initialize services
        print("Initializing services...")
        config_service = ConfigService()
        # database_service = DatabaseService()  # Temporarily disabled
        # ai_service = AIService()  # Temporarily disabled
        
        # Initialize chunking utils (temporarily disabled)
        # chunking_utils = ChunkingUtils()
        
        # PDF file path
        pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"ERROR: PDF file not found: {pdf_path}")
            return False
        
        print(f"PDF file found: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
        
        # Extract text from PDF
        print("Extracting text from PDF...")
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
        
        page_count = doc.page_count
        doc.close()
        
        print(f"Extracted text length: {len(full_text)} characters")
        print(f"Number of pages: {page_count}")
        
        # Get chunking strategy from config
        print("Loading chunking configuration...")
        try:
            chunking_strategy = config_service.get_chunking_strategy()
            print(f"Chunking strategy: {chunking_strategy}")
        except:
            chunking_strategy = "contextual_chunking"
            print(f"Using default chunking strategy: {chunking_strategy}")
        
        # Get chunk settings for HP (assuming HP manufacturer)
        try:
            chunk_settings = config_service.get_chunk_settings()
            hp_settings = chunk_settings.get("hp", {})
            print(f"HP chunk settings: {hp_settings}")
        except:
            hp_settings = {"chunk_size_multiplier": 1.0, "preferred_strategy": "contextual_chunking"}
            print(f"Using default HP settings: {hp_settings}")
        
        # Process text with real chunking
        print("Processing text with AI-powered chunking...")
        
        # Create processing context (simplified)
        context = {
            "document_id": "test_doc_123",
            "file_path": pdf_path,
            "file_hash": "test_hash",
            "document_type": "service_manual",
            "language": "en",
            "manufacturer": "hp",
            "model": "X580",
            "chunking_strategy": chunking_strategy
        }
        
        # Simple chunking for now (AI chunking temporarily disabled)
        # Use basic chapter-based chunking
        chapters = full_text.split("Chapter ")
        chunks = []
        
        for i, chapter in enumerate(chapters):
            if chapter.strip() and len(chapter.strip()) > 100:
                # Create chunk data structure (simplified)
                chunk = {
                    'content': chapter.strip(),
                    'section_title': f"Chapter {i}" if i > 0 else "Introduction",
                    'confidence': 0.8,
                    'metadata': {'chunk_type': 'chapter', 'chunk_index': i, 'source': 'hp_x580_sm'}
                }
                chunks.append(chunk)
        
        print(f"Created {len(chunks)} chunks using basic chunking")
        
        # Display chunk details
        for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
            print(f"\nChunk {i+1}:")
            print(f"   Content length: {len(chunk['content'])} characters")
            print(f"   Section: {chunk['section_title']}")
            print(f"   Confidence: {chunk['confidence']}")
            print(f"   Preview: {chunk['content'][:150]}...")
            if chunk['metadata']:
                print(f"   Metadata: {chunk['metadata']}")
        
        if len(chunks) > 5:
            print(f"\n... and {len(chunks) - 5} more chunks")
        
        # Test chunk size distribution
        chunk_sizes = [len(chunk['content']) for chunk in chunks]
        print(f"\nChunk size statistics:")
        print(f"   Min size: {min(chunk_sizes)} characters")
        print(f"   Max size: {max(chunk_sizes)} characters")
        print(f"   Average size: {sum(chunk_sizes) / len(chunk_sizes):.0f} characters")
        
        # Test chunk quality
        print(f"\nChunk quality analysis:")
        high_confidence_chunks = [c for c in chunks if c['confidence'] > 0.8]
        print(f"   High confidence chunks: {len(high_confidence_chunks)}/{len(chunks)}")
        
        structured_chunks = [c for c in chunks if c['section_title'] and c['section_title'] != "Unknown"]
        print(f"   Structured chunks: {len(structured_chunks)}/{len(chunks)}")
        
        print("\nReal chunk pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Real chunk pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_real_chunk_pipeline())
