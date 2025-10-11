import fitz
import sys

# Get PDF path from command line argument or use default
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]
else:
    pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\processed\UTAX_P4531MFP-iMFP_P4536MFP-iMFP_P5536iMFP_P6036iMFP.pdf"

print(f"Opening: {pdf_path}\n")
pdf = fitz.open(pdf_path)

print("="*80)
print("PDF METADATA")
print("="*80)

meta = pdf.metadata

print(f"Title:             {meta.get('title', '(none)')}")
print(f"Author:            {meta.get('author', '(none)')}")
print(f"Subject:           {meta.get('subject', '(none)')}")
print(f"Keywords:          {meta.get('keywords', '(none)')}")
print(f"Creator:           {meta.get('creator', '(none)')}")
print(f"Producer:          {meta.get('producer', '(none)')}")
print(f"Creation Date:     {meta.get('creationDate', '(none)')}")
print(f"Modification Date: {meta.get('modDate', '(none)')}")

print("\n" + "="*80)
print("PDF PROPERTIES")
print("="*80)
print(f"Total Pages:       {len(pdf)}")
print(f"Encrypted:         {pdf.is_encrypted}")
print(f"Format:            {meta.get('format', '(none)')}")

print("\n" + "="*80)
print("ALL METADATA KEYS")
print("="*80)
for key, value in meta.items():
    if value:  # Only show non-empty values
        print(f"{key:20s} = {value}")

pdf.close()
