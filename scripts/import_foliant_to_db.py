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

# Load environment variables from multiple .env files
load_dotenv()  # Load .env
load_dotenv('.env.database')  # Load .env.database
load_dotenv('.env.ai')  # Load .env.ai if exists

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
                articles = []
                article_match = re.search(r'name;code\r(.*?)\r</', data_str, re.DOTALL)
                if article_match:
                    articles_text = article_match.group(1)
                    
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
                
                # Extract Physicals matrix (compatibility + specs)
                compatibility_matrix = {}
                phys_match = re.search(r'<Physicals>(.*?)</Physicals>', data_str, re.DOTALL)
                if phys_match:
                    phys_text = phys_match.group(1)
                    # Split on various line endings (\r\n, \n, \r, or escaped \r)
                    lines = re.split(r'\\r|\\n|\r\n|\n|\r', phys_text)
                    lines = [line for line in lines if line.strip()]  # Remove empty lines
                    
                    if lines:
                        # Parse header (product/option names)
                        header = lines[0].split(';')
                        print(f"\nFound compatibility matrix:")
                        print(f"  Products/Options: {len(header) - 1}")
                        print(f"  Properties: {len(lines) - 1}")
                        
                        # Parse each property row
                        for line in lines[1:]:
                            if line.strip():
                                parts = line.split(';')
                                if parts:
                                    prop_name = parts[0]
                                    # Store values for each product/option
                                    for i, value in enumerate(parts[1:], 1):
                                        if i < len(header):
                                            product_name = header[i]
                                            if product_name not in compatibility_matrix:
                                                compatibility_matrix[product_name] = {}
                                            if value.strip():
                                                compatibility_matrix[product_name][prop_name] = value.strip()
                        
                        print(f"  Parsed specs for {len(compatibility_matrix)} items")
                
                # Log summary
                print(f"\n{'=' * 80}")
                print("EXTRACTION SUMMARY")
                print("=" * 80)
                print(f"Articles: {len(articles)}")
                print(f"Compatibility Matrix Items: {len(compatibility_matrix)}")
                if compatibility_matrix:
                    # Count items with specs
                    items_with_specs = sum(1 for specs in compatibility_matrix.values() if specs)
                    print(f"Items with physical specs: {items_with_specs}")
                
                return {
                    'articles': articles,
                    'compatibility_matrix': compatibility_matrix
                }
    
    return {'articles': [], 'compatibility_matrix': {}}

def import_compatibility_links(compatibility_matrix, supabase, manufacturer_id):
    """Import compatibility links from Physicals matrix"""
    
    print(f"\n{'=' * 80}")
    print("Importing compatibility links...")
    print("=" * 80)
    
    # Get all products from DB
    products_result = supabase.table('vw_products').select('id, model_number').eq('manufacturer_id', manufacturer_id).execute()
    product_map = {p['model_number']: p['id'] for p in products_result.data}
    
    print(f"Found {len(product_map)} products in database")
    
    links_created = 0
    links_updated = 0
    
    # Parse compatibility from matrix
    # Look for properties that indicate compatibility
    for product_name, specs in compatibility_matrix.items():
        if product_name not in product_map:
            continue
        
        product_id = product_map[product_name]
        
        # Check for quantity limits (maxQty, minQty, etc.)
        quantity_max = 1
        quantity_min = 0
        
        for prop_name, value in specs.items():
            prop_lower = prop_name.lower()
            
            # Look for max quantity
            if 'maxqty' in prop_lower or 'max_qty' in prop_lower:
                try:
                    quantity_max = int(value)
                except:
                    pass
            
            # Look for min quantity
            if 'minqty' in prop_lower or 'min_qty' in prop_lower:
                try:
                    quantity_min = int(value)
                except:
                    pass
        
        # Update product specifications with physical specs
        physical_specs = {}
        for prop_name, value in specs.items():
            prop_lower = prop_name.lower()
            
            # Store physical properties
            if prop_lower in ['width', 'depth', 'height', 'weight']:
                try:
                    physical_specs[prop_lower] = float(value)
                except:
                    physical_specs[prop_lower] = value
            elif 'power' in prop_lower:
                physical_specs[prop_name] = value
        
        if physical_specs:
            # Update product with physical specs
            current = supabase.table('vw_products').select('specifications').eq('id', product_id).single().execute()
            current_specs = current.data.get('specifications', {}) if current.data else {}
            current_specs.update(physical_specs)
            
            supabase.table('vw_products').update({
                'specifications': current_specs
            }).eq('id', product_id).execute()
    
    print(f"\nCompatibility links: {links_created} created, {links_updated} updated")
    print(f"Physical specs updated for products")
    
    return {
        'links_created': links_created,
        'links_updated': links_updated
    }

def detect_series_name(main_products):
    """Detect series name from product list"""
    if not main_products:
        return None
    
    # Check for bizhub patterns
    first_product = main_products[0]['name']
    
    if re.match(r'C[2-7]\d{2}i', first_product):
        # bizhub C-Series (C227i, C257i, C287i, C251i, etc.)
        return 'bizhub C-Series'
    elif first_product.startswith('AP'):
        # AccurioPress
        return 'AccurioPress'
    elif re.match(r'\d{3}i', first_product):
        # bizhub monochrome (301i, 361i, etc.)
        return 'bizhub'
    
    return 'bizhub'  # Default

def categorize_by_mounting_position(sprite_name):
    """Categorize accessory by mounting position"""
    if sprite_name.startswith('DF-'):
        return 'top'
    elif sprite_name.startswith(('FS-', 'LU-', 'JS-', 'RU-', 'SD-')):
        return 'side'
    elif sprite_name.startswith(('PC-', 'DK-', 'WT-')):
        return 'bottom'
    elif sprite_name.startswith(('CU-', 'EK-', 'IC-', 'AU-', 'UK-', 'FK-', 'SX-', 'IQ-', 'MIC-')):
        return 'internal'
    else:
        return 'accessory'

def extract_slot_number(sprite_name):
    """Extract slot number from sprite name (e.g., FK-513_1 -> 1)"""
    if '_' in sprite_name and sprite_name[-1].isdigit():
        parts = sprite_name.rsplit('_', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
    return None

def get_base_model(sprite_name):
    """Get base model without slot suffix (e.g., FK-513_1 -> FK-513)"""
    if '_' in sprite_name and sprite_name[-1].isdigit():
        return sprite_name.rsplit('_', 1)[0]
    return sprite_name

def import_to_database(data, manufacturer_name="Konica Minolta", pdf_filename=None):
    """Import articles and compatibility to KRAI database"""
    
    articles = data.get('articles', [])
    compatibility_matrix = data.get('compatibility_matrix', {})
    
    if not articles:
        print("No articles to import")
        return False
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase credentials not found in .env")
        print("Please configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env file")
        return False
    
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
    
    # Check if article_code column exists (Migration 112)
    has_article_code_column = False
    try:
        test_query = supabase.table('vw_products').select('article_code').limit(1).execute()
        has_article_code_column = True
        print("✅ article_code column available (Migration 112 applied)")
    except:
        print("⚠️ article_code column not found - will store in specifications JSON")
        print("   Run Migration 112 to add dedicated article_code column")
    
    # Classify products vs accessories
    main_products = []
    accessories = []
    
    for article in articles:
        name = article['name']
        
        # Main products: C###i, C###e, AP#### pattern
        if re.match(r'C\d{3}[ie]', name) or name.startswith('AP'):
            main_products.append(article)
        else:
            accessories.append(article)
    
    print(f"\nClassified:")
    print(f"  Main products: {len(main_products)}")
    print(f"  Accessories: {len(accessories)}")
    
    # Detect and create/get series
    series_name = detect_series_name(main_products)
    series_id = None
    
    if series_name:
        print(f"\nDetected series: {series_name}")
        
        # Check if series exists
        series_result = supabase.table('vw_product_series').select('id').eq('series_name', series_name).eq('manufacturer_id', manufacturer_id).execute()
        
        if series_result.data:
            series_id = series_result.data[0]['id']
            print(f"  Series exists: {series_id}")
        else:
            # Create series
            series_insert = supabase.table('vw_product_series').insert({
                'series_name': series_name,
                'manufacturer_id': manufacturer_id
            }).execute()
            series_id = series_insert.data[0]['id']
            print(f"  Created series: {series_id}")
    
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
            # Update with article code and series
            product_id = existing.data[0]['id']
            update_data = {}
            if has_article_code_column:
                update_data['article_code'] = article_code
            else:
                update_data['specifications'] = {'article_code': article_code}
            if series_id:
                update_data['series_id'] = series_id
            supabase.table('vw_products').update(update_data).eq('id', product_id).execute()
            updated_products += 1
            print(f"  Updated: {model_number} (article_code: {article_code}, series: {series_name})")
        else:
            # Insert new product
            insert_data = {
                'model_number': model_number,
                'manufacturer_id': manufacturer_id,
                'product_type': 'laser_multifunction'  # Default for bizhub
            }
            if has_article_code_column:
                insert_data['article_code'] = article_code
            else:
                insert_data['specifications'] = {'article_code': article_code}
            if series_id:
                insert_data['series_id'] = series_id
            supabase.table('vw_products').insert(insert_data).execute()
            imported_products += 1
            print(f"  Imported: {model_number} (article_code: {article_code}, series: {series_name})")
    
    print(f"\nMain products: {imported_products} new, {updated_products} updated")
    
    # Import accessories
    print(f"\n{'=' * 80}")
    print("Importing accessories...")
    print("=" * 80)
    
    imported_accessories = 0
    updated_accessories = 0
    
    # Detect accessory type from name
    # Based on Migration 107 & 110 product_type_check constraint
    def detect_accessory_type(name):
        name_lower = name.lower()
        name_upper = name.upper()
        
        # Finishers (Migration 107)
        if 'finisher' in name_lower or name_upper.startswith('FS-'):
            return 'finisher'
        
        # Saddle Finishers (Migration 107: SD-*)
        elif name_upper.startswith('SD-'):
            return 'saddle_finisher'
        
        # Staplers (Migration 110: JS-* standalone staplers)
        elif name_upper.startswith('JS-'):
            return 'stapler'
        
        # Finisher Accessories (Migration 107: RU, PK, SK, TR)
        elif name_upper.startswith(('PK-', 'SK-', 'TR-')):
            return 'finisher_accessory'
        
        # Relay Units (Migration 110: RU-*)
        elif name_upper.startswith('RU-'):
            return 'relay_unit'
        
        # Feeders (Migration 107)
        elif 'feeder' in name_lower or name_upper.startswith('DF-'):
            return 'document_feeder'
        
        # Paper Feeders (Migration 107: PF-*)
        elif name_upper.startswith('PF-'):
            return 'paper_feeder'
        
        # Large Capacity Units (Migration 110: LU-*, LK-*)
        elif name_upper.startswith(('LU-', 'LK-')):
            return 'large_capacity_unit'
        
        # Output Trays (Migration 107: OT-*)
        elif name_upper.startswith('OT-'):
            return 'output_tray'
        
        # Cabinets/Desks (Migration 107: PC-*, DK-*)
        elif 'cabinet' in name_lower or 'desk' in name_lower or name_upper.startswith(('PC-', 'DK-')):
            return 'cabinet'
        
        # Hole Punch Units (Migration 110: HT-*)
        elif name_upper.startswith('HT-'):
            return 'punch_unit'
        
        # Fold/Crease Units (Migration 110: CR-*, FD-*)
        elif name_upper.startswith(('CR-', 'FD-')):
            return 'fold_unit'
        
        # Post Inserters (Migration 107: PI-*)
        elif name_upper.startswith('PI-'):
            return 'post_inserter'
        
        # Z-Fold Units (Migration 107: ZU-*)
        elif name_upper.startswith('ZU-'):
            return 'z_fold_unit'
        
        # Image Controllers (Migration 107: IC-*, MIC-*)
        elif name_upper.startswith(('IC-', 'MIC-')):
            return 'image_controller'
        
        # Controller Accessories (Migration 107: VI-*)
        elif name_upper.startswith('VI-'):
            return 'controller_accessory'
        
        # Controller Units (Migration 110: CU-*, EK-*, IQ-*)
        elif name_upper.startswith(('CU-', 'EK-', 'IQ-')):
            return 'controller_unit'
        
        # Authentication Units (Migration 110: AU-*, UK-*)
        elif name_upper.startswith(('AU-', 'UK-')):
            return 'authentication_unit'
        
        # Waste Toner (Migration 107)
        elif name_upper.startswith('WT-'):
            return 'waste_toner_box'
        
        # Mount Kits (Migration 107: MK-*)
        elif name_upper.startswith('MK-'):
            return 'mount_kit'
        
        # Generic units
        elif 'unit' in name_lower:
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
                'article_code': article_code
            }).eq('id', product_id).execute()
            updated_accessories += 1
            print(f"  Updated: {model_number:15} ({product_type:15}) -> {article_code}")
        else:
            # Insert
            supabase.table('vw_products').insert({
                'model_number': model_number,
                'manufacturer_id': manufacturer_id,
                'product_type': product_type,
                'article_code': article_code
            }).execute()
            imported_accessories += 1
            print(f"  Imported: {model_number:15} ({product_type:15}) -> {article_code}")
    
    print(f"\nAccessories: {imported_accessories} new, {updated_accessories} updated")
    
    # Import product_accessories links (compatibility)
    print(f"\n{'=' * 80}")
    print("Creating product_accessories links...")
    print("=" * 80)
    
    # Get all products from DB
    all_products_result = supabase.table('vw_products').select('id, model_number').eq('manufacturer_id', manufacturer_id).execute()
    product_map = {p['model_number']: p['id'] for p in all_products_result.data}
    
    links_created = 0
    links_skipped = 0
    
    # For each main product, link all accessories
    for main_product in main_products:
        main_model = main_product['name']
        if main_model not in product_map:
            continue
        
        main_product_id = product_map[main_model]
        
        for accessory in accessories:
            accessory_model = get_base_model(accessory['name'])  # Remove _1, _2 suffix
            
            if accessory_model not in product_map:
                continue
            
            accessory_id = product_map[accessory_model]
            
            # Get mounting position and slot number
            mounting_position = categorize_by_mounting_position(accessory['name'])
            slot_number = extract_slot_number(accessory['name'])
            
            # Check if link already exists
            try:
                existing_link = supabase.schema('krai_core').table('product_accessories').select('id').eq('product_id', main_product_id).eq('accessory_id', accessory_id)
                if slot_number:
                    existing_link = existing_link.eq('slot_number', slot_number)
                existing_link = existing_link.execute()
                
                if not existing_link.data:
                    # Create link
                    link_data = {
                        'product_id': main_product_id,
                        'accessory_id': accessory_id,
                        'mounting_position': mounting_position,
                        'compatibility_type': 'compatible'  # Default compatibility type
                    }
                    if slot_number:
                        link_data['slot_number'] = slot_number
                    
                    supabase.schema('krai_core').table('product_accessories').insert(link_data).execute()
                    links_created += 1
                else:
                    links_skipped += 1
            except Exception as e:
                # Skip if table doesn't exist or other error
                print(f"    ⚠️ Could not create link for {accessory_model}: {e}")
                links_skipped += 1
    
    print(f"\nProduct_accessories links: {links_created} created, {links_skipped} already existed")
    
    # Import compatibility matrix (physical specs)
    if compatibility_matrix:
        compat_stats = import_compatibility_links(compatibility_matrix, supabase, manufacturer_id)
    else:
        print("\nNo compatibility matrix found - skipping physical specs")
        compat_stats = {'links_created': 0, 'links_updated': 0}
    
    print(f"\n{'=' * 80}")
    print("IMPORT SUMMARY")
    print("=" * 80)
    if series_name:
        print(f"📚 Series: {series_name} ({'created' if series_id else 'existing'})")
    print(f"📦 Products: {imported_products} new, {updated_products} updated")
    print(f"🔧 Accessories: {imported_accessories} new, {updated_accessories} updated")
    print(f"🔗 Product_accessories links: {links_created} created, {links_skipped} skipped")
    print(f"📏 Physical specs: {compat_stats['links_created']} created, {compat_stats['links_updated']} updated")
    print(f"📊 Total articles processed: {len(articles)}")
    
    # Log what was saved to DB
    print(f"\n{'=' * 80}")
    print("DATABASE CHANGES")
    print("=" * 80)
    if imported_products > 0:
        print(f"✅ {imported_products} new products added to database")
    if updated_products > 0:
        print(f"🔄 {updated_products} products updated (article codes, types)")
    if imported_accessories > 0:
        print(f"✅ {imported_accessories} new accessories added to database")
    if updated_accessories > 0:
        print(f"🔄 {updated_accessories} accessories updated (article codes, types)")
    if compatibility_matrix:
        specs_count = sum(1 for specs in compatibility_matrix.values() if specs)
        print(f"📏 Physical specs updated for {specs_count} items")
    
    return True  # Success!

if __name__ == "__main__":
    import sys
    from glob import glob
    import shutil
    
    # Check for input_foliant directory
    input_dir = Path(__file__).parent.parent / "input_foliant"
    processed_dir = input_dir / "processed"
    
    # Create processed directory if it doesn't exist
    processed_dir.mkdir(exist_ok=True)
    
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
            data = extract_foliant_data(pdf_file)
            
            if data and data.get('articles'):
                # Import to database
                success = import_to_database(data)
                
                if success:
                    total_articles += len(data['articles'])
                    successful += 1
                    
                    # Move to processed directory
                    dest_path = processed_dir / Path(pdf_file).name
                    shutil.move(str(pdf_file), str(dest_path))
                    print(f"\n✅ Moved to: {dest_path.relative_to(input_dir.parent)}")
                else:
                    print("\n❌ Import failed - PDF not moved")
                    failed += 1
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
