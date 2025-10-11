import fitz

pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_pdfs\7566-69x_sm.pdf"
pdf = fitz.open(pdf_path)

# Get first 3 pages
text = ''.join([pdf[i].get_text() for i in range(min(3, len(pdf)))]).lower()

print(f"Lexmark mentions in first 3 pages: {text.count('lexmark')}")
print(f"\nFirst 500 chars:")
print(text[:500])

pdf.close()
