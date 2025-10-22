import json
import xml.etree.ElementTree as ET
import csv

# Load the extracted data
with open('foliant_javascript_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get Pandora field value (contains XML)
pandora_value = data['field_info']['Pandora']['value']

# Parse XML
try:
    root = ET.fromstring(pandora_value)
    
    print("Foliant Configuration Data")
    print("=" * 80)
    
    # Extract Article Codes
    article_codes = root.find(".//ArticleCodes")
    if article_codes:
        print(f"\nArticle Codes ({article_codes.get('name')}):")
        print("-" * 80)
        
        # Parse CSV-like data
        lines = article_codes.text.strip().split('\r')
        header = lines[0].split(';')
        print(f"Columns: {header}")
        print()
        
        products = []
        for line in lines[1:]:
            if line.strip():
                parts = line.split(';')
                if len(parts) >= 2:
                    product_name = parts[0].strip()
                    product_code = parts[1].strip()
                    if product_name and product_code:
                        products.append({'name': product_name, 'code': product_code})
                        print(f"  {product_name:20} -> {product_code}")
        
        print(f"\nTotal products: {len(products)}")
    
    # Extract Consumables
    consumables = root.find(".//ConsumableCodes")
    if consumables:
        print(f"\n\nConsumables ({consumables.get('name')}):")
        print("-" * 80)
        
        lines = consumables.text.strip().split('\r')
        header = lines[0].split(';')
        print(f"Columns: {header}")
        print()
        
        consumable_list = []
        for line in lines[1:]:
            if line.strip():
                parts = line.split(';')
                if len(parts) >= 2:
                    consumable_name = parts[0].strip()
                    consumable_code = parts[1].strip()
                    if consumable_name and consumable_code:
                        consumable_list.append({'name': consumable_name, 'code': consumable_code})
                        print(f"  {consumable_name:20} -> {consumable_code}")
        
        print(f"\nTotal consumables: {len(consumable_list)}")
    
    # Extract Physicals (compatibility matrix!)
    physicals = root.find(".//Physicals")
    if physicals:
        print(f"\n\nPhysical Properties & Compatibility Matrix:")
        print("-" * 80)
        
        lines = physicals.text.strip().split('\r')
        header_line = lines[0]
        headers = header_line.split(';')
        
        print(f"Products in matrix: {len(headers) - 1}")
        print(f"Products: {', '.join(headers[1:10])}...")  # Show first few
        
        print(f"\nProperties:")
        for line in lines[1:6]:  # Show first few properties
            parts = line.split(';')
            if parts:
                prop_name = parts[0]
                print(f"  {prop_name:15} - {len([p for p in parts[1:] if p.strip()])} values")
        
        # Save to CSV for analysis
        with open('foliant_compatibility_matrix.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for line in lines:
                writer.writerow(line.split(';'))
        
        print(f"\nFull matrix saved to: foliant_compatibility_matrix.csv")
    
except Exception as e:
    print(f"Error parsing XML: {e}")
    import traceback
    traceback.print_exc()
