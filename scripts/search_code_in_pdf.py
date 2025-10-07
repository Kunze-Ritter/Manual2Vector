#!/usr/bin/env python3
"""Search for error code in PDF"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

import pymupdf

pdf_path = Path('input_pdfs/HP_X580_CPMD.pdf')
search_code = "30.03.30"

print(f"\n{'='*100}")
print(f"SEARCHING FOR: {search_code} in {pdf_path.name}")
print(f"{'='*100}\n")

doc = pymupdf.open(pdf_path)

found_count = 0
for page_num, page in enumerate(doc, 1):
    text = page.get_text()
    
    # Search for code
    if search_code in text:
        found_count += 1
        print(f"📄 PAGE {page_num}: FOUND!\n")
        
        # Extract context
        matches = re.finditer(re.escape(search_code), text)
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            print(f"Context:")
            print(f"{context}\n")
            print("-" * 100)

if found_count == 0:
    print(f"❌ Code '{search_code}' NOT FOUND in PDF!")
else:
    print(f"\n✅ Found '{search_code}' on {found_count} page(s)")

print(f"\n{'='*100}\n")
