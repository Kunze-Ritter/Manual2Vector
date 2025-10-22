"""
Extract JavaScript from interactive PDFs (e.g., Konica Minolta Foliant configurators)
"""

import PyPDF2
import json
import sys
from pathlib import Path

def extract_javascript_from_pdf(pdf_path):
    """Extract all JavaScript from a PDF file"""
    
    print(f"Analyzing: {Path(pdf_path).name}")
    print("=" * 80)
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            print(f"📊 Pages: {len(pdf.pages)}")
            print(f"📋 Metadata: {pdf.metadata}")
            print()
            
            # Check for JavaScript in catalog
            catalog = pdf.trailer.get("/Root")
            if not catalog:
                print("❌ No catalog found")
                return
            
            # Dereference if it's an indirect object
            if hasattr(catalog, 'get_object'):
                catalog = catalog.get_object()
            
            # Look for JavaScript in Names dictionary
            names = catalog.get("/Names")
            if names:
                print("✅ Found /Names dictionary")
                # Dereference if needed
                if hasattr(names, 'get_object'):
                    names = names.get_object()
                js_dict = names.get("/JavaScript")
                if js_dict:
                    print("✅ Found /JavaScript dictionary")
                    print()
                    
                    # Extract JavaScript code
                    if isinstance(js_dict, PyPDF2.generic.ArrayObject):
                        for i, item in enumerate(js_dict):
                            if isinstance(item, PyPDF2.generic.DictionaryObject):
                                js_code = item.get("/JS")
                                if js_code:
                                    print(f"📜 JavaScript Block {i+1}:")
                                    print("-" * 80)
                                    if hasattr(js_code, 'get_data'):
                                        print(js_code.get_data().decode('utf-8', errors='ignore'))
                                    else:
                                        print(js_code)
                                    print("-" * 80)
                                    print()
                else:
                    print("❌ No /JavaScript found in /Names")
            else:
                print("❌ No /Names dictionary found")
            
            # Check for JavaScript in AcroForm
            acroform = catalog.get("/AcroForm")
            if acroform:
                print("✅ Found /AcroForm")
                js = acroform.get("/JS")
                if js:
                    print("✅ Found JavaScript in AcroForm")
                    print()
                    print("📜 AcroForm JavaScript:")
                    print("-" * 80)
                    if hasattr(js, 'get_data'):
                        print(js.get_data().decode('utf-8', errors='ignore'))
                    else:
                        print(js)
                    print("-" * 80)
                else:
                    print("❌ No JavaScript in AcroForm")
            
            # Check for JavaScript in OpenAction
            open_action = catalog.get("/OpenAction")
            if open_action:
                print("✅ Found /OpenAction")
                if isinstance(open_action, PyPDF2.generic.DictionaryObject):
                    js = open_action.get("/JS")
                    if js:
                        print("✅ Found JavaScript in OpenAction")
                        print()
                        print("📜 OpenAction JavaScript:")
                        print("-" * 80)
                        if hasattr(js, 'get_data'):
                            print(js.get_data().decode('utf-8', errors='ignore'))
                        else:
                            print(js)
                        print("-" * 80)
            
            # Check form fields for JavaScript
            if acroform and "/Fields" in acroform:
                fields = acroform["/Fields"]
                print(f"\n📋 Found {len(fields)} form fields")
                
                js_fields = []
                for i, field_ref in enumerate(fields):
                    field = field_ref.get_object()
                    field_name = field.get("/T", f"Field_{i}")
                    
                    # Check for JavaScript actions
                    aa = field.get("/AA")  # Additional Actions
                    if aa:
                        for action_type in ["/K", "/F", "/V", "/C"]:  # Keystroke, Format, Validate, Calculate
                            action = aa.get(action_type)
                            if action:
                                js = action.get("/JS")
                                if js:
                                    js_fields.append({
                                        'field': field_name,
                                        'action': action_type,
                                        'js': js
                                    })
                
                if js_fields:
                    print(f"✅ Found JavaScript in {len(js_fields)} fields")
                    for item in js_fields[:5]:  # Show first 5
                        print(f"\n📌 Field: {item['field']} ({item['action']})")
                        print("-" * 80)
                        js_code = item['js']
                        if hasattr(js_code, 'get_data'):
                            print(js_code.get_data().decode('utf-8', errors='ignore')[:500])
                        else:
                            print(str(js_code)[:500])
                        print("...")
                else:
                    print("❌ No JavaScript in form fields")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = r"C:\Users\haast\Downloads\Foliant bizhub C257i v1.10 R1.pdf"
    
    extract_javascript_from_pdf(pdf_path)
