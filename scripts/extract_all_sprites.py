"""
Extract all Sprite fields from Foliant PDF
These represent all available options
"""
import PyPDF2
import json

def extract_sprites(pdf_path):
    """Extract all Sprite_ fields from PDF"""
    
    print(f"Extracting sprites from: {pdf_path}")
    print("=" * 80)
    
    sprites = []
    
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        
        # Get catalog and AcroForm
        catalog = pdf.trailer["/Root"]
        if hasattr(catalog, 'get_object'):
            catalog = catalog.get_object()
        
        acroform = catalog["/AcroForm"]
        if hasattr(acroform, 'get_object'):
            acroform = acroform.get_object()
        
        fields = acroform["/Fields"]
        
        print(f"\nScanning {len(fields)} form fields...")
        
        for field_ref in fields:
            field = field_ref.get_object()
            field_name = field.get("/T", "")
            
            if field_name.startswith("Sprite_"):
                option_name = field_name.replace("Sprite_", "")
                sprites.append(option_name)
    
    # Sort and categorize
    sprites.sort()
    
    print(f"\n{'=' * 80}")
    print(f"FOUND {len(sprites)} SPRITES (OPTIONS)")
    print("=" * 80)
    
    # Categorize by prefix
    categories = {}
    for sprite in sprites:
        # Get prefix (first 2-3 chars before dash)
        if '-' in sprite:
            prefix = sprite.split('-')[0]
        elif sprite.startswith('C') and len(sprite) > 3:
            prefix = 'MAIN'
        else:
            prefix = 'OTHER'
        
        if prefix not in categories:
            categories[prefix] = []
        categories[prefix].append(sprite)
    
    # Print by category
    for category in sorted(categories.keys()):
        items = categories[category]
        print(f"\n{category}: ({len(items)} items)")
        for item in items:
            print(f"  - {item}")
    
    # Save to JSON
    output = {
        'total': len(sprites),
        'sprites': sprites,
        'categories': categories
    }
    
    with open('foliant_all_sprites.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 80}")
    print(f"✅ Saved to: foliant_all_sprites.json")
    print("=" * 80)
    
    return sprites

if __name__ == "__main__":
    pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_foliant\processed\Foliant bizhub C257i v1.10 R1.pdf"
    sprites = extract_sprites(pdf_path)
    
    print(f"\n\nAll sprites represent AVAILABLE OPTIONS in this PDF!")
    print(f"This is the COMPLETE list of what can be configured.")
