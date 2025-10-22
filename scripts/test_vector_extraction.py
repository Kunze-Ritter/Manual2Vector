#!/usr/bin/env python3
"""
Test Vector Graphics Extraction from Parts Catalog
Extracts technical drawings (vector graphics) with text overlays
"""

import fitz  # PyMuPDF
from pathlib import Path
import json

# Path to test PDF - try both .pdf and .pdfz
pdf_path = Path(r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\A93E.pdf")
pdfz_path = Path(r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\A93E.pdfz")

if pdfz_path.exists():
    print(f"📦 Found .pdfz file: {pdfz_path.name}")
    # Check if it's actually gzipped or just renamed
    with open(pdfz_path, 'rb') as f:
        magic = f.read(2)
    
    if magic == b'\x1f\x8b':  # gzip magic bytes
        print(f"   → Gzip compressed, decompressing...")
        import gzip
        temp_pdf = Path("temp_A93E.pdf")
        with gzip.open(pdfz_path, 'rb') as f_in:
            with open(temp_pdf, 'wb') as f_out:
                f_out.write(f_in.read())
        pdf_path = temp_pdf
        print(f"   ✅ Decompressed to: {pdf_path}")
    elif magic == b'%P':  # PDF magic bytes
        print(f"   → Just a renamed PDF, using directly")
        pdf_path = pdfz_path
    else:
        print(f"   ❌ Unknown file format (magic: {magic})")
        exit(1)
elif pdf_path.exists():
    print(f"📄 Found PDF: {pdf_path.name}")
else:
    print(f"❌ PDF not found at:")
    print(f"   - {pdf_path}")
    print(f"   - {pdfz_path}")
    exit(1)

print(f"📄 Opening: {pdf_path.name}\n")

# Open PDF
doc = fitz.open(pdf_path)

print(f"📊 Total pages: {len(doc)}\n")

# Test first 5 pages
for page_num in range(min(5, len(doc))):
    page = doc[page_num]
    print(f"\n{'='*60}")
    print(f"Page {page_num + 1}")
    print(f"{'='*60}")
    
    # 1. Extract images (raster)
    images = page.get_images()
    print(f"\n🖼️  Raster Images: {len(images)}")
    
    # 2. Extract drawings (vector paths)
    drawings = page.get_drawings()
    print(f"✏️  Vector Drawings: {len(drawings)}")
    
    if drawings:
        # Show first drawing details
        first_drawing = drawings[0]
        print(f"\n   First drawing:")
        print(f"   - Type: {first_drawing.get('type', 'unknown')}")
        print(f"   - Items: {len(first_drawing.get('items', []))}")
        print(f"   - Rect: {first_drawing.get('rect', 'N/A')}")
    
    # 3. Extract text (including text on drawings)
    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])
    
    text_blocks = [b for b in blocks if b.get("type") == 0]  # Text blocks
    image_blocks = [b for b in blocks if b.get("type") == 1]  # Image blocks
    
    print(f"📝 Text Blocks: {len(text_blocks)}")
    print(f"🖼️  Image Blocks: {len(image_blocks)}")
    
    # 4. Extract SVG (vector graphics as SVG)
    try:
        svg = page.get_svg_image()
        if svg:
            svg_size = len(svg)
            print(f"\n🎨 SVG Export: {svg_size:,} bytes")
            
            # Save first page SVG as test
            if page_num == 0:
                output_path = Path("test_page1_vector.svg")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(svg)
                print(f"   ✅ Saved to: {output_path}")
    except Exception as e:
        print(f"   ⚠️  SVG export failed: {e}")
    
    # 5. Show sample text (first 200 chars)
    text = page.get_text()
    if text:
        sample = text[:200].replace('\n', ' ')
        print(f"\n📄 Text sample: {sample}...")

doc.close()

print(f"\n{'='*60}")
print("✅ Extraction complete!")
print(f"{'='*60}")
print("\nCheck 'test_page1_vector.svg' for the first page vector export!")
