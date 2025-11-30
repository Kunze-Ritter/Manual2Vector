"""
Extract ALL JavaScript from Foliant PDF
Including document-level scripts and field actions
"""
import PyPDF2
import json
import re

def extract_all_javascript(pdf_path):
    """Extract all JavaScript from PDF"""
    
    print(f"Extracting JavaScript from: {pdf_path}")
    print("=" * 80)
    
    all_scripts = []
    
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        
        # Get catalog
        catalog = pdf.trailer["/Root"]
        if hasattr(catalog, 'get_object'):
            catalog = catalog.get_object()
        
        # Check for document-level JavaScript
        if "/Names" in catalog:
            names = catalog["/Names"]
            if hasattr(names, 'get_object'):
                names = names.get_object()
            
            if "/JavaScript" in names:
                js_names = names["/JavaScript"]
                if hasattr(js_names, 'get_object'):
                    js_names = js_names.get_object()
                
                print("\n📜 DOCUMENT-LEVEL JAVASCRIPT FOUND!")
                print("=" * 80)
                
                if "/Names" in js_names:
                    js_array = js_names["/Names"]
                    
                    # Names array is [name1, script1, name2, script2, ...]
                    for i in range(0, len(js_array), 2):
                        script_name = str(js_array[i])
                        script_ref = js_array[i + 1]
                        
                        if hasattr(script_ref, 'get_object'):
                            script_obj = script_ref.get_object()
                            
                            if "/JS" in script_obj:
                                js_code = script_obj["/JS"]
                                if hasattr(js_code, 'get_object'):
                                    js_code = js_code.get_object()
                                
                                # Check if it's a stream (compressed)
                                if hasattr(js_code, 'get_data'):
                                    js_code_str = js_code.get_data().decode('utf-8', errors='ignore')
                                else:
                                    js_code_str = str(js_code)
                                
                                print(f"\nScript: {script_name}")
                                print(f"Length: {len(js_code_str)} chars")
                                
                                all_scripts.append({
                                    'type': 'document',
                                    'name': script_name,
                                    'code': js_code_str
                                })
                                
                                # Search for compatibility keywords
                                keywords = ['compatible', 'conflict', 'require', 'depend', 
                                           'mutual', 'exclusive', 'allow', 'forbid', 'enable', 
                                           'disable', 'check', 'validate']
                                
                                found_keywords = []
                                for keyword in keywords:
                                    if keyword.lower() in js_code_str.lower():
                                        found_keywords.append(keyword)
                                
                                if found_keywords:
                                    print(f"  🔍 Keywords found: {', '.join(found_keywords)}")
        
        # Check AcroForm field actions
        if "/AcroForm" in catalog:
            acroform = catalog["/AcroForm"]
            if hasattr(acroform, 'get_object'):
                acroform = acroform.get_object()
            
            if "/Fields" in acroform:
                fields = acroform["/Fields"]
                
                print(f"\n\n📋 CHECKING {len(fields)} FORM FIELDS FOR ACTIONS...")
                print("=" * 80)
                
                for field_ref in fields:
                    field = field_ref.get_object()
                    field_name = field.get("/T", "")
                    
                    # Check for actions
                    if "/AA" in field:  # Additional Actions
                        aa = field["/AA"]
                        if hasattr(aa, 'get_object'):
                            aa = aa.get_object()
                        
                        for action_type in ["/F", "/K", "/V", "/C"]:  # Format, Keystroke, Validate, Calculate
                            if action_type in aa:
                                action = aa[action_type]
                                if hasattr(action, 'get_object'):
                                    action = action.get_object()
                                
                                if "/JS" in action:
                                    js_code = action["/JS"]
                                    if hasattr(js_code, 'get_object'):
                                        js_code = js_code.get_object()
                                    
                                    js_code_str = str(js_code)
                                    
                                    if len(js_code_str) > 100:  # Only show substantial scripts
                                        print(f"\n  Field: {field_name}")
                                        print(f"  Action: {action_type}")
                                        print(f"  Length: {len(js_code_str)} chars")
                                        
                                        all_scripts.append({
                                            'type': 'field_action',
                                            'field': field_name,
                                            'action': action_type,
                                            'code': js_code_str
                                        })
    
    # Save all scripts
    with open('foliant_all_javascript.json', 'w', encoding='utf-8') as f:
        json.dump(all_scripts, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'=' * 80}")
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Total scripts found: {len(all_scripts)}")
    print(f"  Document-level: {sum(1 for s in all_scripts if s['type'] == 'document')}")
    print(f"  Field actions: {sum(1 for s in all_scripts if s['type'] == 'field_action')}")
    print(f"\nSaved to: foliant_all_javascript.json")
    
    return all_scripts

if __name__ == "__main__":
    pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_foliant\processed\Foliant bizhub C257i v1.10 R1.pdf"
    scripts = extract_all_javascript(pdf_path)
    
    # Show preview of longest script
    if scripts:
        longest = max(scripts, key=lambda s: len(s['code']))
        print(f"\n\n{'=' * 80}")
        print(f"LONGEST SCRIPT PREVIEW")
        print("=" * 80)
        print(f"Type: {longest['type']}")
        if longest['type'] == 'document':
            print(f"Name: {longest['name']}")
        else:
            print(f"Field: {longest['field']}")
        print(f"Length: {len(longest['code'])} chars")
        print(f"\nFirst 1000 chars:")
        print(longest['code'][:1000])
