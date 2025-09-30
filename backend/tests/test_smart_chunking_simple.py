"""
Simple Smart Chunking Test - Focus on intelligence without PyMuPDF issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizations.smart_chunking_optimization import SmartChunkingOptimizer

def test_smart_chunking_intelligence():
    """Test the intelligence features of smart chunking"""
    print("SMART CHUNKING INTELLIGENCE TEST")
    print("=" * 40)
    
    # Initialize smart chunker
    smart_chunker = SmartChunkingOptimizer(chunk_size=500, overlap=50)
    
    # Test content samples
    test_contents = [
        "Error 1234: Paper jam detected. Please clear the paper path and try again.",
        "Step 1: Turn off the printer. Step 2: Open the front panel. Step 3: Remove any paper.",
        "Table 1: Print Specifications\nSpeed: 25 ppm\nResolution: 1200 dpi",
        "```\nfunction printDocument() {\n  console.log('Printing...');\n}\n```",
        "Chapter 3: Maintenance\nThis chapter covers regular maintenance procedures.",
        "Section 2.1: Troubleshooting\nCommon issues and solutions are listed below."
    ]
    
    print("Testing chunk type detection:")
    print("-" * 30)
    
    for i, content in enumerate(test_contents, 1):
        chunk_type = smart_chunker._detect_chunk_type(content)
        confidence = smart_chunker._calculate_confidence(content, chunk_type)
        metadata = smart_chunker._extract_chunk_metadata(content)
        
        print(f"Test {i}:")
        print(f"  Content: {content[:50]}...")
        print(f"  Detected Type: {chunk_type}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Metadata: {metadata}")
        print()
    
    print("Testing section title detection:")
    print("-" * 35)
    
    test_pages = [
        "Chapter 1: Introduction\nThis document covers...",
        "## Installation Guide\nFollow these steps...",
        "1. Getting Started\nFirst, you need to...",
        "TROUBLESHOOTING\nIf you encounter problems...",
        "Error Codes\nCommon error codes are listed below."
    ]
    
    for i, page_text in enumerate(test_pages, 1):
        section = smart_chunker._detect_section_title(page_text)
        print(f"Page {i}:")
        print(f"  Text: {page_text[:40]}...")
        print(f"  Detected Section: {section}")
        print()
    
    print("Testing smart break points:")
    print("-" * 28)
    
    long_text = "This is a long sentence. This is another sentence! And here's a question? Finally, some more text with commas, and periods."
    break_point = smart_chunker._find_smart_break_point(long_text, 50)
    
    print(f"Original: {long_text}")
    print(f"Break point at position: {break_point}")
    print(f"First chunk: {long_text[:break_point]}")
    print(f"Second chunk: {long_text[break_point:]}")
    
    print("\nSmart chunking intelligence test completed!")

if __name__ == "__main__":
    test_smart_chunking_intelligence()
