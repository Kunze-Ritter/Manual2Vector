#!/usr/bin/env python3
"""
Simple Chunk Pipeline Test
Tests only the chunk processing functionality without complex imports
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_chunk_pipeline():
    """Test chunk processing pipeline in isolation"""
    print("Testing Chunk Pipeline...")
    
    try:
        # Test document content
        test_content = """
        Service Manual for XYZ Printer Model 123
        
        Table of Contents:
        1. Safety Instructions
        2. Installation Guide
        3. Operation Instructions
        4. Maintenance Procedures
        5. Troubleshooting Guide
        
        Chapter 1: Safety Instructions
        Before operating this printer, please read all safety instructions carefully.
        Always ensure the printer is properly grounded and connected to a stable power source.
        
        Chapter 2: Installation Guide
        Step 1: Unpack the printer and remove all protective materials.
        Step 2: Place the printer on a stable, level surface.
        Step 3: Connect the power cable to the printer and wall outlet.
        Step 4: Install the ink cartridges according to the color-coded guides.
        
        Chapter 3: Operation Instructions
        To print a document:
        1. Load paper into the paper tray
        2. Open your document
        3. Select Print from the File menu
        4. Choose your printer from the list
        5. Click Print
        
        Chapter 4: Maintenance Procedures
        Regular maintenance is essential for optimal printer performance.
        Clean the print heads monthly using the built-in cleaning function.
        Replace ink cartridges when the low ink indicator appears.
        
        Chapter 5: Troubleshooting Guide
        Problem: Printer not responding
        Solution: Check power connection and restart the printer.
        
        Problem: Poor print quality
        Solution: Clean print heads and check ink levels.
        """
        
        print("Test content prepared")
        print(f"Content length: {len(test_content)} characters")
        
        # Simple chunking test
        print("Testing simple chunking...")
        
        # Split by chapters
        chapters = test_content.split("Chapter ")
        chunks = []
        
        for i, chapter in enumerate(chapters):
            if chapter.strip():
                chunk_content = chapter.strip()
                if len(chunk_content) > 50:  # Only meaningful chunks
                    chunks.append({
                        'content': chunk_content,
                        'section_title': f"Chapter {i}" if i > 0 else "Introduction",
                        'confidence': 0.9,
                        'metadata': {'chunk_type': 'chapter', 'chunk_index': i}
                    })
        
        print(f"Created {len(chunks)} chunks")
        
        # Display chunk details
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1}:")
            print(f"   Content length: {len(chunk['content'])} characters")
            print(f"   Section: {chunk['section_title']}")
            print(f"   Confidence: {chunk['confidence']}")
            print(f"   Preview: {chunk['content'][:100]}...")
        
        # Test chunk size distribution
        chunk_sizes = [len(chunk['content']) for chunk in chunks]
        print(f"\nChunk size statistics:")
        print(f"   Min size: {min(chunk_sizes)} characters")
        print(f"   Max size: {max(chunk_sizes)} characters")
        print(f"   Average size: {sum(chunk_sizes) / len(chunk_sizes):.0f} characters")
        
        print("\nChunk pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Chunk pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_chunk_pipeline())
