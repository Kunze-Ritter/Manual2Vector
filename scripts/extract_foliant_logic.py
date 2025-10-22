import PyPDF2
import json
import re

pdf_path = r"C:\Users\haast\Downloads\Foliant bizhub C257i v1.10 R1.pdf"

with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    
    print(f"Analyzing Foliant PDF: {pdf.metadata.get('/Title', 'N/A')}")
    print("=" * 80)
    
    catalog = pdf.trailer["/Root"]
    if hasattr(catalog, 'get_object'):
        catalog = catalog.get_object()
    
    acroform = catalog["/AcroForm"]
    if hasattr(acroform, 'get_object'):
        acroform = acroform.get_object()
    
    fields = acroform["/Fields"]
    print(f"\nTotal fields: {len(fields)}")
    
    # Extract all JavaScript
    all_js = []
    field_info = {}
    
    for i, field_ref in enumerate(fields):
        field = field_ref.get_object()
        field_name = field.get("/T", f"Field_{i}")
        
        # Get field type and value
        field_type = field.get("/FT", "Unknown")
        field_value = field.get("/V", None)
        
        field_info[field_name] = {
            'type': str(field_type),
            'value': str(field_value) if field_value else None,
            'actions': []
        }
        
        # Check for actions
        if "/AA" in field:
            aa = field["/AA"]
            if hasattr(aa, 'get_object'):
                aa = aa.get_object()
            
            for action_type in ["/K", "/F", "/V", "/C"]:  # Keystroke, Format, Validate, Calculate
                if action_type in aa:
                    action = aa[action_type]
                    if hasattr(action, 'get_object'):
                        action = action.get_object()
                    
                    if "/JS" in action:
                        js = action["/JS"]
                        if hasattr(js, 'get_data'):
                            js_code = js.get_data().decode('utf-8', errors='ignore')
                        else:
                            js_code = str(js)
                        
                        all_js.append({
                            'field': field_name,
                            'action': action_type,
                            'code': js_code
                        })
                        
                        field_info[field_name]['actions'].append(action_type)
    
    print(f"\nFound JavaScript in {len(all_js)} actions")
    print("\n" + "=" * 80)
    
    # Look for compatibility logic
    print("\nSearching for compatibility/dependency logic...")
    print("=" * 80)
    
    compatibility_patterns = [
        r'(if|when|require|depend|compatible|incompatible)',
        r'(option|accessory|finisher|feeder|tray)',
        r'(enable|disable|show|hide)',
    ]
    
    relevant_js = []
    for item in all_js:
        code_lower = item['code'].lower()
        if any(re.search(pattern, code_lower) for pattern in compatibility_patterns):
            relevant_js.append(item)
    
    print(f"\nFound {len(relevant_js)} potentially relevant JavaScript blocks")
    
    # Show first few
    for i, item in enumerate(relevant_js[:5]):
        print(f"\n--- Field: {item['field']} ({item['action']}) ---")
        print(item['code'][:500])
        if len(item['code']) > 500:
            print("... (truncated)")
    
    # Save all to file
    output_file = "foliant_javascript_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump({
            'field_info': field_info,
            'javascript_actions': all_js
        }, out, indent=2, ensure_ascii=False)
    
    print(f"\n\nFull analysis saved to: {output_file}")
    print(f"Total fields: {len(field_info)}")
    print(f"Fields with JavaScript: {len([f for f in field_info.values() if f['actions']])}")
