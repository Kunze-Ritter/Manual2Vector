#!/usr/bin/env python3
"""
Test Page Label Extraction from PDFs
Shows the difference between PDF index and document page numbers
"""

import fitz  # PyMuPDF
from pathlib import Path

# Test with multiple PDFs
test_pdfs = [
    Path(r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\A93E.pdfz"),  # Konica
]

# Try to find HP PDFs
input_dir = Path(r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs")
if input_dir.exists():
    # Look for HP PDFs
    hp_pdfs = list(input_dir.glob("*HP*.pdf*")) + list(input_dir.glob("*hp*.pdf*"))
    if hp_pdfs:
        print(f"Found {len(hp_pdfs)} HP PDFs:")
        for pdf in hp_pdfs[:3]:  # Test first 3
            print(f"  - {pdf.name}")
            test_pdfs.append(pdf)
    else:
        print("No HP PDFs found, testing with available PDFs...")

for pdf_path in test_pdfs:
    if not pdf_path.exists():
        print(f"⚠️  Not found: {pdf_path.name}")
        continue
    
    print(f"\n{'='*60}")
    print(f"📄 {pdf_path.name}")
    print(f"{'='*60}\n")
    
    doc = fitz.open(pdf_path)
    
    print(f"Total pages: {len(doc)}")
    
    # Check if PDF has page labels
    has_labels = False
    try:
        # Get page labels (if defined)
        labels = doc.get_page_labels()
        if labels:
            has_labels = True
            print(f"\n✅ PDF has page labels defined!")
            print(f"\nPage Label Rules: {len(labels)}")
            for i, label in enumerate(labels):
                print(f"  {i+1}. {label}")
    except:
        pass
    
    if not has_labels:
        print(f"\n⚠️  No page labels defined in PDF")
        print(f"   Using default numbering (1, 2, 3, ...)")
    
    # Show first 20 pages with their labels
    print(f"\n📊 First 20 pages:")
    print(f"{'PDF Index':<12} {'Page Label':<15} {'Sample Text'}")
    print(f"{'-'*60}")
    
    # Helper function to convert page number to label based on style
    def format_page_label(page_num, rules):
        """Convert page number to label based on PDF page label rules"""
        # Find applicable rule
        applicable_rule = rules[0]
        for rule in rules:
            if rule['startpage'] <= page_num:
                applicable_rule = rule
            else:
                break
        
        # Calculate page number within this rule
        offset = page_num - applicable_rule['startpage']
        page_in_section = applicable_rule['firstpagenum'] + offset
        prefix = applicable_rule.get('prefix', '')
        style = applicable_rule.get('style', 'D')
        
        # Format based on style
        if style == 'D':  # Decimal
            label = str(page_in_section)
        elif style == 'r':  # Lowercase roman
            label = int_to_roman(page_in_section).lower()
        elif style == 'R':  # Uppercase roman
            label = int_to_roman(page_in_section)
        elif style == 'a':  # Lowercase letters
            label = int_to_letter(page_in_section).lower()
        elif style == 'A':  # Uppercase letters
            label = int_to_letter(page_in_section)
        else:
            label = str(page_in_section)
        
        return prefix + label
    
    def int_to_roman(num):
        """Convert integer to Roman numeral"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        roman = ''
        for i in range(len(val)):
            count = int(num / val[i])
            if count:
                roman += syms[i] * count
                num -= val[i] * count
        return roman
    
    def int_to_letter(num):
        """Convert integer to letter (1=A, 2=B, etc.)"""
        if num <= 26:
            return chr(64 + num)
        else:
            return chr(64 + ((num-1) % 26) + 1) + str((num-1) // 26)
    
    for page_num in range(min(20, len(doc))):
        page = doc[page_num]
        
        # Get page label using our custom formatter
        if has_labels and labels:
            page_label = format_page_label(page_num, labels)
        else:
            page_label = str(page_num + 1)
        
        # Get sample text
        text = page.get_text()[:50].replace('\n', ' ').strip()
        
        print(f"{page_num:<12} {page_label:<15} {text[:30]}...")
    
    doc.close()

print(f"\n{'='*60}")
print("✅ Page label analysis complete!")
print(f"{'='*60}")
