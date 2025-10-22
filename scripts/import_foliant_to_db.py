"""
Import Konica Minolta Foliant PDF data into KRAI database
Extracts product compatibility information from interactive PDFs
"""

import PyPDF2
import re
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

def extract_foliant_data(pdf_path):
    """Extract compatibility data from Foliant PDF"""
    
    print(f"Extracting data from: {Path(pdf_path).name}")
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
        
        # Find Pandora field (contains compatibility data)
        for field_ref in fields:
            field = field_ref.get_object()
            field_name = field.get("/T", "")
            
            if field_name == "Pandora":
                # Get value
                value = field.get("/V")
                if hasattr(value, 'get_object'):
                    value = value.get_object()
                
                # Parse the data
                data_str = str(value)
                
                # Extract article codes (products and accessories)
                article_match = re.search(r'name;code\r(.*?)\r</', data_str, re.DOTALL)
                if article_match:
                    articles_text = article_match.group(1)
                    articles = []
                    
                    for line in articles_text.split('\r'):
                        if ';' in line:
                            parts = line.split(';')
                            if len(parts) >= 2:
                                name = parts[0].strip()
                                code = parts[1].strip()
                                if name and code and code != 't.b.d.' and code != '-':
                                    articles.append({
                                        'name': name,
                                        'code': code
                                    })
                    
                    print(f"\nFound {len(articles)} products/accessories:")
                    for article in articles[:10]:
                        print(f"  {article['name']:20} -> {article['code']}")
                    if len(articles) > 10:
                        print(f"  ... and {len(articles) - 10} more")
                    
                    return articles
    
    return []

def import_to_database(articles, manufacturer_name="Konica Minolta"):
    """Import articles to KRAI database"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not found in .env")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    print(f"\n{'=' * 80}")
    print("Importing to database...")
    print("=" * 80)
    
    # Get manufacturer_id
    mfr_result = supabase.table('vw_manufacturers').select('id').eq('name', manufacturer_name).execute()
    if not mfr_result.data:
        print(f"ERROR: Manufacturer '{manufacturer_name}' not found in database")
        return
    
    manufacturer_id = mfr_result.data[0]['id']
    print(f"Manufacturer: {manufacturer_name} ({manufacturer_id})")
    
    # Classify products vs accessories
    main_products = []
    accessories = []
    
    for article in articles:
        name = article['name']
        
        # Main products: C###i, C###e pattern
        if re.match(r'C\d{3}[ie]', name):
            main_products.append(article)
        else:
            accessories.append(article)
    
    print(f"\nClassified:")
    print(f"  Main products: {len(main_products)}")
    print(f"  Accessories: {len(accessories)}")
    
    # Import main products
    print(f"\n{'=' * 80}")
    print("Importing main products...")
    print("=" * 80)
    
    imported_products = 0
    updated_products = 0
    
    for product in main_products:
        model_number = product['name']
        article_code = product['code']
        
        # Check if exists
        existing = supabase.table('vw_products').select('id').eq('model_number', model_number).execute()
        
        if existing.data:
            # Update with article code in specifications
            product_id = existing.data[0]['id']
            supabase.table('vw_products').update({
                'specifications': {'article_code': article_code}
            }).eq('id', product_id).execute()
            updated_products += 1
            print(f"  Updated: {model_number} (article_code: {article_code})")
        else:
            # Insert new product
            supabase.table('vw_products').insert({
                'model_number': model_number,
                'manufacturer_id': manufacturer_id,
                'product_type': 'laser_multifunction',  # Default for bizhub
                'specifications': {'article_code': article_code}
            }).execute()
            imported_products += 1
            print(f"  Imported: {model_number} (article_code: {article_code})")
    
    print(f"\nMain products: {imported_products} new, {updated_products} updated")
    
    # Import accessories
    print(f"\n{'=' * 80}")
    print("Importing accessories...")
    print("=" * 80)
    
    imported_accessories = 0
    updated_accessories = 0
    
    # Detect accessory type from name
    def detect_accessory_type(name):
        name_lower = name.lower()
        if 'finisher' in name_lower or 'fs-' in name_lower:
            return 'finisher'
        elif 'feeder' in name_lower or 'df-' in name_lower:
            return 'feeder'
        elif 'tray' in name_lower or 'pk-' in name_lower:
            return 'output_tray'
        elif 'cabinet' in name_lower or 'pc-' in name_lower:
            return 'cabinet'
        elif 'desk' in name_lower or 'dk-' in name_lower:
            return 'cabinet'
        elif 'unit' in name_lower or 'au-' in name_lower or 'cu-' in name_lower:
            return 'accessory'
        else:
            return 'accessory'
    
    for accessory in accessories:
        model_number = accessory['name']
        article_code = accessory['code']
        product_type = detect_accessory_type(model_number)
        
        # Check if exists
        existing = supabase.table('vw_products').select('id').eq('model_number', model_number).execute()
        
        if existing.data:
            # Update
            product_id = existing.data[0]['id']
            supabase.table('vw_products').update({
                'product_type': product_type,
                'specifications': {'article_code': article_code}
            }).eq('id', product_id).execute()
            updated_accessories += 1
            print(f"  Updated: {model_number:15} ({product_type:15}) -> {article_code}")
        else:
            # Insert
            supabase.table('vw_products').insert({
                'model_number': model_number,
                'manufacturer_id': manufacturer_id,
                'product_type': product_type,
                'specifications': {'article_code': article_code}
            }).execute()
            imported_accessories += 1
            print(f"  Imported: {model_number:15} ({product_type:15}) -> {article_code}")
    
    print(f"\nAccessories: {imported_accessories} new, {updated_accessories} updated")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)
    print(f"Total imported: {imported_products + imported_accessories}")
    print(f"Total updated: {updated_products + updated_accessories}")
    print(f"Total processed: {len(articles)}")

if __name__ == "__main__":
    import sys
    from glob import glob
    
    # Check for input_foliant directory
    input_dir = Path(__file__).parent.parent / "input_foliant"
    
    if len(sys.argv) > 1:
        # Single file mode
        pdf_path = sys.argv[1]
        pdf_files = [pdf_path]
    elif input_dir.exists():
        # Batch mode - process all PDFs in input_foliant/
        pdf_files = list(input_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in: {input_dir}")
            print("\nPlace Foliant PDFs in the input_foliant/ directory")
            sys.exit(1)
        
        print(f"Found {len(pdf_files)} PDF(s) in {input_dir}")
        print("=" * 80)
    else:
        print("Usage: python import_foliant_to_db.py [path_to_foliant_pdf]")
        print("\nBatch mode:")
        print(f"  Place Foliant PDFs in: {input_dir}")
        print("  Then run: python import_foliant_to_db.py")
        print("\nSingle file mode:")
        print('  python import_foliant_to_db.py "C:\\Downloads\\Foliant.pdf"')
        sys.exit(1)
    
    # Process all PDFs
    total_articles = 0
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        try:
            print(f"\n{'=' * 80}")
            print(f"Processing: {Path(pdf_file).name}")
            print("=" * 80)
            
            # Extract data
            articles = extract_foliant_data(pdf_file)
            
            if articles:
                # Import to database
                import_to_database(articles)
                total_articles += len(articles)
                successful += 1
            else:
                print("No data extracted!")
                failed += 1
        
        except Exception as e:
            print(f"ERROR processing {Path(pdf_file).name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print("BATCH SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(pdf_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"Total articles imported: {total_articles}")
