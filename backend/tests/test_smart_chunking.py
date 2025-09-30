"""
Test Smart Chunking - Intelligent analysis with memory efficiency
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from typing import Dict

# Import smart chunking
from optimizations.smart_chunking_optimization import SmartChunkingOptimizer
from services.database_service import DatabaseService

async def test_smart_chunking():
    """Test the smart chunking with intelligent analysis"""
    print("SMART CHUNKING TEST")
    print("=" * 50)
    
    # Load environment
    load_dotenv('../credentials.txt')
    
    # Initialize database
    database_service = DatabaseService(
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_ANON_KEY')
    )
    await database_service.connect()
    
    # Initialize smart chunker
    smart_chunker = SmartChunkingOptimizer(chunk_size=800, overlap=100)
    
    # Test with HP PDF
    test_file = "../HP_X580_SM.pdf"
    document_id = "test_smart_chunking_doc"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    print(f"Testing smart chunking on: {test_file}")
    print(f"Document ID: {document_id}")
    print()
    
    chunk_count = 0
    page_stats = {}
    section_stats = {}
    chunk_type_stats = {}
    
    try:
        # Extract smart chunks
        for chunk_data in smart_chunker.extract_smart_chunks_streaming(test_file, document_id):
            chunk_count += 1
            
            # Collect statistics
            page_num = chunk_data.get('page_number', 'Unknown')
            section = chunk_data.get('section_title', 'Unknown')
            chunk_type = chunk_data.get('chunk_type', 'text')
            
            page_stats[page_num] = page_stats.get(page_num, 0) + 1
            section_stats[section] = section_stats.get(section, 0) + 1
            chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
            
            # Show first few chunks with details
            if chunk_count <= 5:
                print(f"Chunk {chunk_count}:")
                print(f"  Page: {page_num}")
                print(f"  Section: {section}")
                print(f"  Type: {chunk_type}")
                print(f"  Confidence: {chunk_data.get('confidence_score', 0):.2f}")
                print(f"  Content preview: {chunk_data['content'][:100]}...")
                print(f"  Metadata: {chunk_data.get('metadata', {})}")
                print()
            
            # Save to database (first 10 chunks for testing)
            if chunk_count <= 10:
                try:
                    chunk_id = await database_service.create_chunk_async(chunk_data)
                    print(f"  Saved to DB: {chunk_id}")
                except Exception as e:
                    print(f"  DB save failed: {e}")
            
            # Limit for demo
            if chunk_count >= 50:
                print("... (stopping at 50 chunks for demo)")
                break
    
    except Exception as e:
        print(f"Error during smart chunking: {e}")
        import traceback
        traceback.print_exc()
    
    # Show statistics
    print("\nSMART CHUNKING STATISTICS:")
    print("=" * 30)
    print(f"Total chunks processed: {chunk_count}")
    print()
    
    print("Page distribution (top 10):")
    for page, count in sorted(page_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  Page {page}: {count} chunks")
    print()
    
    print("Section distribution (top 10):")
    for section, count in sorted(section_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {section}: {count} chunks")
    print()
    
    print("Chunk type distribution:")
    for chunk_type, count in sorted(chunk_type_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {chunk_type}: {count} chunks")
    print()
    
    print("Smart chunking test completed!")

if __name__ == "__main__":
    asyncio.run(test_smart_chunking())
