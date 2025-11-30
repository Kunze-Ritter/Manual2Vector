"""
Import ALL Foliant PDFs from input_foliant directory
"""
from pathlib import Path
from import_foliant_to_db import extract_foliant_data, import_to_database
import time

def import_all_pdfs():
    """Process all PDFs in input_foliant directory"""
    
    input_dir = Path("input_foliant")
    processed_dir = input_dir / "processed"
    
    # Get all PDFs from both directories
    pdf_files = list(input_dir.glob("*.pdf"))
    pdf_files.extend(list(processed_dir.glob("*.pdf")))
    
    print("=" * 80)
    print(f"FOLIANT BATCH IMPORT")
    print("=" * 80)
    print(f"\nFound {len(pdf_files)} PDF files to process\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, pdf_file in enumerate(sorted(pdf_files), 1):
        print(f"\n{'=' * 80}")
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("=" * 80)
        
        try:
            # Extract data
            data = extract_foliant_data(str(pdf_file))
            
            if not data or not data.get('articles'):
                print(f"⚠️ No data extracted from {pdf_file.name} - skipping")
                skipped_count += 1
                continue
            
            # Import to database
            success = import_to_database(data, pdf_filename=pdf_file.name)
            
            if success:
                success_count += 1
                print(f"\n✅ Successfully imported {pdf_file.name}")
            else:
                error_count += 1
                print(f"\n❌ Failed to import {pdf_file.name}")
        
        except Exception as e:
            error_count += 1
            print(f"\n❌ Error processing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay between PDFs
        time.sleep(0.5)
    
    # Final summary
    print(f"\n\n{'=' * 80}")
    print("BATCH IMPORT COMPLETE")
    print("=" * 80)
    print(f"✅ Successfully imported: {success_count} PDFs")
    print(f"⚠️ Skipped (no data): {skipped_count} PDFs")
    print(f"❌ Errors: {error_count} PDFs")
    print(f"📊 Total processed: {len(pdf_files)} PDFs")
    
    if success_count > 0:
        print(f"\n🎉 Import successful! Check your database for:")
        print(f"   - Product series (bizhub C-Series, AccurioPress, etc.)")
        print(f"   - Products with article codes")
        print(f"   - Accessories with product types")
        print(f"   - Product_accessories compatibility links")

if __name__ == "__main__":
    import_all_pdfs()
