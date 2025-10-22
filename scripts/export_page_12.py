#!/usr/bin/env python3
"""
Export Page 12 from A93E.pdf (Technical Drawings)
"""

import fitz  # PyMuPDF
from pathlib import Path

# Path to PDF
pdfz_path = Path(r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\A93E.pdfz")

print(f"📦 Opening: {pdfz_path.name}\n")

# Open PDF (pdfz is just renamed PDF)
doc = fitz.open(pdfz_path)

print(f"📊 Total pages: {len(doc)}")

# Get page 12 (index 11)
page_num = 11  # 0-indexed
page = doc[page_num]

print(f"\n{'='*60}")
print(f"Page {page_num + 1} (Technical Drawings)")
print(f"{'='*60}\n")

# 1. Extract images (raster)
images = page.get_images()
print(f"🖼️  Raster Images: {len(images)}")

# 2. Extract drawings (vector paths)
drawings = page.get_drawings()
print(f"✏️  Vector Drawings: {len(drawings)}")

if drawings:
    print(f"\n   Drawing details:")
    print(f"   - Total paths: {len(drawings)}")
    
    # Count by type
    types = {}
    for d in drawings:
        dtype = d.get('type', 'unknown')
        types[dtype] = types.get(dtype, 0) + 1
    
    print(f"   - Types: {types}")

# 3. Extract text
text = page.get_text()
text_lines = [line.strip() for line in text.split('\n') if line.strip()]
print(f"\n📝 Text Lines: {len(text_lines)}")

# Show first 20 text lines (part numbers, labels)
print(f"\n   First 20 text lines:")
for i, line in enumerate(text_lines[:20], 1):
    print(f"   {i:2d}. {line}")

# 4. Export as SVG
try:
    svg = page.get_svg_image()
    if svg:
        svg_size = len(svg)
        print(f"\n🎨 SVG Export: {svg_size:,} bytes")
        
        # Save SVG
        output_path = Path("page_12_technical_drawing.svg")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"   ✅ Saved to: {output_path}")
        
        # Also save as PNG for preview
        try:
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            png_path = Path("page_12_technical_drawing.png")
            pix.save(png_path)
            print(f"   ✅ PNG preview: {png_path}")
        except Exception as e:
            print(f"   ⚠️  PNG export failed: {e}")
            
except Exception as e:
    print(f"   ⚠️  SVG export failed: {e}")

# 5. Extract text with positions (for OCR-like output)
text_dict = page.get_text("dict")
blocks = text_dict.get("blocks", [])

print(f"\n📍 Text Blocks with Positions:")
for i, block in enumerate(blocks[:10], 1):  # First 10 blocks
    if block.get("type") == 0:  # Text block
        bbox = block.get("bbox", [0,0,0,0])
        lines = block.get("lines", [])
        if lines:
            first_line = lines[0]
            spans = first_line.get("spans", [])
            if spans:
                text_content = " ".join(s.get("text", "") for s in spans)
                print(f"   {i}. [{bbox[0]:.0f},{bbox[1]:.0f}] {text_content[:60]}")

doc.close()

print(f"\n{'='*60}")
print("✅ Page 12 exported!")
print(f"{'='*60}")
print("\nFiles created:")
print("  - page_12_technical_drawing.svg (vector graphics)")
print("  - page_12_technical_drawing.png (preview)")
