"""
Extract article codes for slot sprites to see if they're different products
"""
import PyPDF2
import re
import json

def extract_articles_from_pdf(pdf_path):
    """Extract Articles table from Pandora field"""
    
    print(f"Analyzing: {pdf_path}")
    print("=" * 80)
    
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        catalog = pdf.trailer["/Root"]
        if hasattr(catalog, 'get_object'):
            catalog = catalog.get_object()
        
        acroform = catalog["/AcroForm"]
        if hasattr(acroform, 'get_object'):
            acroform = acroform.get_object()
        
        fields = acroform["/Fields"]
        
        # Find Pandora field
        for field_ref in fields:
            field = field_ref.get_object()
            field_name = field.get("/T", "")
            
            if field_name == "Pandora":
                # Get value
                if "/V" in field:
                    value = field["/V"]
                    if hasattr(value, 'get_object'):
                        value = value.get_object()
                    
                    pandora_value = str(value)
                    
                    # Extract Articles table
                    articles_match = re.search(r'<Articles>(.*?)</Articles>', pandora_value, re.DOTALL)
                    if not articles_match:
                        print("No Articles table found")
                        return {}
                    
                    articles_text = articles_match.group(1)
                    
                    # Parse CSV-like format
                    lines = re.split(r'\\r|\\n|\r\n|\n|\r', articles_text)
                    lines = [line for line in lines if line.strip()]
                    
                    if not lines:
                        return {}
                    
                    # First line is header
                    header = lines[0].split(';')
                    
                    # Parse articles
                    articles = {}
                    for line in lines[1:]:
                        parts = line.split(';')
                        if len(parts) >= 2:
                            sprite_name = parts[0].strip()
                            article_code = parts[1].strip() if len(parts) > 1 else ""
                            articles[sprite_name] = article_code
                    
                    return articles
    
    return {}

def analyze_slot_articles():
    """Analyze article codes for slot sprites"""
    
    # Try multiple PDFs
    pdf_paths = [
        r"input_foliant\processed\Foliant bizhub C257i v1.10 R1.pdf",
        r"input_foliant\processed\Foliant bizhub C251i-C361i-C451i-C551i-C651i-C751i v1.10 R3.pdf",
        r"input_foliant\Foliant AccurioPress 6272P v1.10 R8 DE.pdf"
    ]
    
    articles = None
    pdf_path = None
    
    for path in pdf_paths:
        try:
            articles = extract_articles_from_pdf(path)
            if articles:
                pdf_path = path
                break
        except:
            continue
    
    articles = extract_articles_from_pdf(pdf_path)
    
    if not articles:
        print("❌ No articles found")
        return
    
    print(f"\n✅ Found {len(articles)} articles")
    
    # Check WT-511 slots
    print(f"\n{'=' * 80}")
    print("WT-511 (Working Table) - Article Codes:")
    print("=" * 80)
    
    wt_articles = {k: v for k, v in articles.items() if 'WT-511' in k}
    for sprite, article in sorted(wt_articles.items()):
        print(f"  {sprite:20} → {article}")
    
    # Check if they're the same
    unique_articles = set(wt_articles.values())
    if len(unique_articles) == 1:
        print(f"\n  ✅ ALL SAME ARTICLE CODE: {list(unique_articles)[0]}")
        print(f"  → This is ONE product with 7 different installation positions!")
    else:
        print(f"\n  ⚠️ DIFFERENT ARTICLE CODES: {len(unique_articles)} variations")
        print(f"  → These are DIFFERENT products!")
    
    # Check RU-518 slots
    print(f"\n{'=' * 80}")
    print("RU-518 (Relay Unit) - Article Codes:")
    print("=" * 80)
    
    ru_articles = {k: v for k, v in articles.items() if 'RU-518' in k}
    for sprite, article in sorted(ru_articles.items()):
        print(f"  {sprite:20} → {article}")
    
    # Check if they're the same
    unique_articles = set(ru_articles.values())
    if len(unique_articles) == 1:
        print(f"\n  ✅ ALL SAME ARTICLE CODE: {list(unique_articles)[0]}")
        print(f"  → This is ONE product with multiple installation positions!")
    else:
        print(f"\n  ⚠️ DIFFERENT ARTICLE CODES: {len(unique_articles)} variations")
        print(f"  → These are DIFFERENT products!")
    
    # Check FK-513 (we know this one)
    print(f"\n{'=' * 80}")
    print("FK-513 (Fax Kit) - Article Codes (for comparison):")
    print("=" * 80)
    
    fk_articles = {k: v for k, v in articles.items() if 'FK-513' in k}
    for sprite, article in sorted(fk_articles.items()):
        print(f"  {sprite:20} → {article}")
    
    # Check FK-514
    print(f"\n{'=' * 80}")
    print("FK-514 (Fax Kit) - Article Codes:")
    print("=" * 80)
    
    fk514_articles = {k: v for k, v in articles.items() if 'FK-514' in k}
    for sprite, article in sorted(fk514_articles.items()):
        print(f"  {sprite:20} → {article}")
    
    unique_articles = set(fk514_articles.values())
    if len(unique_articles) == 1:
        print(f"\n  ✅ ALL SAME ARTICLE CODE: {list(unique_articles)[0]}")
    else:
        print(f"\n  ⚠️ DIFFERENT ARTICLE CODES: {len(unique_articles)} variations")
    
    # Summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)
    print("""
If article codes are THE SAME:
  → It's ONE product that can be installed in multiple positions
  → Use slot_number in database (1, 2, 3, etc.)
  → Example: FK-513 can go in slot 1 OR slot 2

If article codes are DIFFERENT:
  → They are DIFFERENT products (variations)
  → Create separate product entries
  → Example: WT-511-A, WT-511-B, WT-511-C (different heights?)
""")

if __name__ == "__main__":
    analyze_slot_articles()
