"""
Check what's in the database for C9402
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env.database')

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Import tools
from agent_api import KRAITools

tools = KRAITools(supabase)

print("="*60)
print("TESTING: search_error_codes('C9402')")
print("="*60)

result = tools.search_error_codes("C9402")
data = json.loads(result)

print(f"\nFound: {data.get('found')}")
print(f"Count: {data.get('count')}")

if data.get('found'):
    print("\n" + "="*60)
    print("FIRST RESULT:")
    print("="*60)
    
    first = data['error_codes'][0]
    
    print(f"\nError Code: {first.get('error_code')}")
    print(f"Description: {first.get('error_description')}")
    print(f"Manufacturer: {first.get('manufacturer_name')}")
    print(f"Document: {first.get('document_filename')}")
    print(f"Page: {first.get('page_number')}")
    
    print(f"\n{'='*60}")
    print("SOLUTION TEXT (FULL):")
    print("="*60)
    solution = first.get('solution_text', '')
    print(solution)
    print(f"\n{'='*60}")
    print(f"Solution length: {len(solution)} characters")
    print("="*60)
