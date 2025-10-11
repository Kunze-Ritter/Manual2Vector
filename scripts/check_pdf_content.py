import fitz
import sys

pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\processed\UTAX_P4531MFP-iMFP_P4536MFP-iMFP_P5536iMFP_P6036iMFP.pdf"

print(f"Opening: {pdf_path}\n")
pdf = fitz.open(pdf_path)

print(f"Total pages: {len(pdf)}\n")

# First 5 pages
print("="*80)
print("FIRST 5 PAGES (first 2000 chars)")
print("="*80)
text = ''.join([pdf[i].get_text() for i in range(min(5, len(pdf)))])
print(text[:2000])

# Search for Konica
print("\n" + "="*80)
print("SEARCHING FOR 'KONICA'")
print("="*80)
konica_pages = []
for i in range(len(pdf)):
    page_text = pdf[i].get_text().lower()
    if 'konica' in page_text:
        konica_pages.append(i+1)  # 1-indexed
        
print(f"Pages with 'Konica': {len(konica_pages)}/{len(pdf)}")
if konica_pages:
    print(f"Page numbers: {konica_pages[:20]}")
    print("\nSample text from first match:")
    first_page = konica_pages[0] - 1
    page_text = pdf[first_page].get_text()
    # Find context around "konica"
    lower_text = page_text.lower()
    idx = lower_text.find('konica')
    if idx >= 0:
        start = max(0, idx - 100)
        end = min(len(page_text), idx + 100)
        print(f"...{page_text[start:end]}...")

# Search for UTAX
print("\n" + "="*80)
print("SEARCHING FOR 'UTAX'")
print("="*80)
utax_pages = []
for i in range(len(pdf)):
    page_text = pdf[i].get_text().lower()
    if 'utax' in page_text:
        utax_pages.append(i+1)  # 1-indexed
        
print(f"Pages with 'UTAX': {len(utax_pages)}/{len(pdf)}")
if utax_pages:
    print(f"Page numbers: {utax_pages[:20]}")

pdf.close()
