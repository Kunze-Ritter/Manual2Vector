"""
Show article code examples from Foliant PDFs
"""
import json
import re

# Load the extracted data
with open('foliant_javascript_analysis.json', encoding='utf-8') as f:
    data = json.load(f)

pandora = data['field_info']['Pandora']['value']

print("=" * 80)
print("ARTICLE CODE EXAMPLES FROM FOLIANT PDF")
print("=" * 80)

# Search for pattern: ProductName;ArticleCode
# Article codes are typically alphanumeric, 8-12 characters

# Find all semicolon-separated pairs
lines = pandora.split('\\r')

article_examples = []
for line in lines:
    if ';' in line:
        parts = line.split(';')
        if len(parts) >= 2:
            name = parts[0].strip()
            code = parts[1].strip()
            
            # Check if this looks like a product name and article code
            # Product names: C257i, DF-633, FS-539, etc.
            # Article codes: AAJ4WY2961, A9CEWY1, etc.
            if (name and code and 
                len(code) > 5 and 
                code.isalnum() and
                code != 't.b.d.' and
                '-' not in code):
                article_examples.append((name, code))

print(f"\nFound {len(article_examples)} product/article code pairs:\n")

# Show examples
for name, code in article_examples[:30]:
    print(f"  {name:20} → {code}")

if len(article_examples) > 30:
    print(f"\n  ... and {len(article_examples) - 30} more")

print(f"\n{'=' * 80}")
print("ARTICLE CODE FORMAT")
print("=" * 80)
print("""
Article Codes sind Hersteller-Artikelnummern von Konica Minolta.

Format:
  - Typischerweise 8-12 Zeichen
  - Alphanumerisch (Buchstaben + Zahlen)
  - Beispiele:
    • AAJ4WY2961 (für DK-518)
    • A9CEWY1 (für ein anderes Produkt)
    • AAPKWY1 (für ein anderes Produkt)

Diese Codes werden verwendet für:
  - Bestellungen
  - Ersatzteilsuche
  - Eindeutige Identifikation
  - Preislisten
""")

# Check specific examples
print(f"\n{'=' * 80}")
print("CHECKING YOUR EXAMPLES")
print("=" * 80)

test_codes = ['AAPKWY1', 'A9CEWY2', 'AAJ4WY2961']
for code in test_codes:
    if code in pandora:
        print(f"✅ {code} found in PDF!")
        # Find context
        for name, article in article_examples:
            if article == code:
                print(f"   → Product: {name}")
    else:
        print(f"❌ {code} not found in this PDF")
        print(f"   (Might be in a different PDF or a typo)")
