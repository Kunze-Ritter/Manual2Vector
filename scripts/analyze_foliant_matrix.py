"""
Analyze Foliant compatibility matrix in detail
Shows what data is available for quantity limits, dependencies, etc.
"""

import PyPDF2
import re
from pathlib import Path

def analyze_foliant_matrix(pdf_path):
    """Analyze the full Physicals matrix"""
    
    print(f"Analyzing: {Path(pdf_path).name}")
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
        
        for field_ref in fields:
            field = field_ref.get_object()
            field_name = field.get("/T", "")
            
            if field_name == "Pandora":
                value = field.get("/V")
                if hasattr(value, 'get_object'):
                    value = value.get_object()
                
                data_str = str(value)
                
                # Extract Physicals table
                phys_match = re.search(r'<Physicals>(.*?)</Physicals>', data_str, re.DOTALL)
                if phys_match:
                    phys_text = phys_match.group(1)
                    lines = phys_text.split('\\r')
                    
                    print("\nPhysicals Matrix:")
                    print("=" * 80)
                    
                    # Parse header (product/option names)
                    if lines:
                        header = lines[0].split(';')
                        print(f"\nColumns ({len(header)}):")
                        print(f"  {', '.join(header[:15])}")
                        if len(header) > 15:
                            print(f"  ... and {len(header) - 15} more")
                        
                        # Parse properties
                        print(f"\nProperties ({len(lines) - 1}):")
                        for line in lines[1:]:
                            if line.strip():
                                parts = line.split(';')
                                if parts:
                                    prop_name = parts[0]
                                    # Count non-empty values
                                    values = [p for p in parts[1:] if p.strip()]
                                    print(f"  {prop_name:20} - {len(values):3} values")
                        
                        # Show sample data for first product
                        print(f"\nSample data for '{header[1]}' (first product):")
                        print("-" * 80)
                        for line in lines[1:20]:  # First 20 properties
                            if line.strip():
                                parts = line.split(';')
                                if len(parts) > 1:
                                    prop_name = parts[0]
                                    value = parts[1] if len(parts) > 1 else ""
                                    if value.strip():
                                        print(f"  {prop_name:20} = {value}")
                        
                        # Look for quantity/limit properties
                        print(f"\nSearching for quantity/limit properties:")
                        print("-" * 80)
                        for line in lines[1:]:
                            if line.strip():
                                parts = line.split(';')
                                if parts:
                                    prop_name = parts[0].lower()
                                    if any(keyword in prop_name for keyword in ['max', 'min', 'qty', 'quantity', 'limit', 'count', 'number']):
                                        values = [p for p in parts[1:] if p.strip()]
                                        print(f"  {parts[0]:30} - {len(values)} values")
                                        # Show first few values
                                        if values:
                                            print(f"    Sample: {', '.join(values[:5])}")
                        
                        # Save full matrix to CSV
                        output_file = "foliant_full_matrix.csv"
                        with open(output_file, 'w', encoding='utf-8') as out:
                            for line in lines:
                                out.write(line.replace(';', ',') + '\n')
                        
                        print(f"\nFull matrix saved to: {output_file}")
                        print(f"  Rows: {len(lines)}")
                        print(f"  Columns: {len(header)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Try to find a Foliant PDF in input_foliant/
        input_dir = Path(__file__).parent.parent / "input_foliant"
        pdf_files = list(input_dir.glob("*.pdf"))
        if pdf_files:
            pdf_path = pdf_files[0]
            print(f"Using: {pdf_path}")
        else:
            print("Usage: python analyze_foliant_matrix.py <foliant_pdf>")
            print("\nOr place a Foliant PDF in input_foliant/ directory")
            sys.exit(1)
    
    analyze_foliant_matrix(pdf_path)
