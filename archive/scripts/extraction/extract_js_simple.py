import PyPDF2
import sys

pdf_path = r"C:\Users\haast\Downloads\Foliant bizhub C257i v1.10 R1.pdf"

with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    
    print(f"Pages: {len(pdf.pages)}")
    print(f"Title: {pdf.metadata.get('/Title', 'N/A')}")
    print()
    
    # Get catalog
    catalog = pdf.trailer["/Root"]
    if hasattr(catalog, 'get_object'):
        catalog = catalog.get_object()
    
    # Check AcroForm
    if "/AcroForm" in catalog:
        acroform = catalog["/AcroForm"]
        if hasattr(acroform, 'get_object'):
            acroform = acroform.get_object()
        
        print("Found AcroForm!")
        
        if "/Fields" in acroform:
            fields = acroform["/Fields"]
            print(f"Fields: {len(fields)}")
            
            # Check first few fields for JavaScript
            for i, field_ref in enumerate(fields[:10]):
                field = field_ref.get_object()
                field_name = field.get("/T", f"Field_{i}")
                print(f"\nField {i}: {field_name}")
                
                # Check for actions
                if "/AA" in field:
                    aa = field["/AA"]
                    if hasattr(aa, 'get_object'):
                        aa = aa.get_object()
                    print(f"  Has actions: {list(aa.keys())}")
                    
                    # Try to get Calculate action
                    if "/C" in aa:
                        calc = aa["/C"]
                        if hasattr(calc, 'get_object'):
                            calc = calc.get_object()
                        if "/JS" in calc:
                            js = calc["/JS"]
                            if hasattr(js, 'get_data'):
                                js_code = js.get_data().decode('utf-8', errors='ignore')
                            else:
                                js_code = str(js)
                            print(f"  JavaScript (first 200 chars):")
                            print(f"  {js_code[:200]}")
