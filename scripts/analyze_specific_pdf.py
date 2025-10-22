"""
Analyze a specific Foliant PDF
"""
import PyPDF2
import json
import re
import sys

def analyze_pdf(pdf_path):
    """Analyze a specific PDF"""
    
    print(f"Analyzing: {pdf_path}")
    print("=" * 80)
    
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
        
        # Find Pandora field
        for field_ref in fields:
            field = field_ref.get_object()
            field_name = field.get("/T", "")
            
            if field_name == "Pandora":
                value = field.get("/V")
                if hasattr(value, 'get_object'):
                    value = value.get_object()
                
                pandora = str(value)
                
                # Extract DynamicData
                dynamic_match = re.search(r'<DynamicData>(.*?)</DynamicData>', pandora, re.DOTALL)
                if dynamic_match:
                    dynamic_data = dynamic_match.group(1)
                    
                    # Find all TABSUM calls
                    tabsum_pattern = r"TABSUM\(['\"](\w+)['\"],\s*\[(.*?)\]\s*\)"
                    matches = re.findall(tabsum_pattern, dynamic_data)
                    
                    print(f"\nFound {len(matches)} TABSUM configurations")
                    print("=" * 80)
                    
                    seen_configs = set()
                    
                    for i, (property_name, products_str) in enumerate(matches, 1):
                        # Extract product list
                        products = re.findall(r"['\"]([^'\"]+)['\"]", products_str)
                        
                        config_key = tuple(sorted(products))
                        if config_key not in seen_configs:
                            seen_configs.add(config_key)
                            
                            print(f"\nConfiguration {len(seen_configs)}:")
                            print(f"  Property: {property_name}")
                            print(f"  Products ({len(products)}):")
                            
                            # Categorize products
                            main_products = []
                            finishers = []
                            feeders = []
                            cabinets = []
                            other = []
                            
                            for p in products:
                                if re.match(r'C\d{3}[ie]', p):
                                    main_products.append(p)
                                elif p.startswith('FS-') or p.startswith('SD-'):
                                    finishers.append(p)
                                elif p.startswith('DF-') or p.startswith('PF-') or p.startswith('LU-'):
                                    feeders.append(p)
                                elif p.startswith('PC-') or p.startswith('DK-'):
                                    cabinets.append(p)
                                else:
                                    other.append(p)
                            
                            if main_products:
                                print(f"    📦 Main: {', '.join(main_products)}")
                            if finishers:
                                print(f"    🔧 Finishers: {', '.join(finishers)}")
                            if feeders:
                                print(f"    📥 Feeders: {', '.join(feeders)}")
                            if cabinets:
                                print(f"    🗄️ Cabinets: {', '.join(cabinets)}")
                            if other:
                                print(f"    ⚙️ Other: {', '.join(other)}")
                    
                    print(f"\n{'=' * 80}")
                    print(f"TOTAL: {len(seen_configs)} unique configurations found")
                    print("=" * 80)
                    
                    return True
    
    return False

if __name__ == "__main__":
    # Default to C251i PDF
    pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_foliant\processed\Foliant bizhub C251i-C361i-C451i-C551i-C651i-C751i v1.10 R3.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    analyze_pdf(pdf_path)
