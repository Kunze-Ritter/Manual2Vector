"""
Check what's actually stored in the database for C9402
"""

import os
import sys
from pathlib import Path

from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files

# Load environment
load_all_env_files(PROJECT_ROOT)

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*60)
print("CHECKING ERROR CODE C9402 IN DATABASE")
print("="*60)

# Query error codes
result = supabase.table('vw_error_codes') \
    .select('error_code, error_description, solution_text, page_number, document_id') \
    .ilike('error_code', '%C9402%') \
    .limit(3) \
    .execute()

if result.data:
    print(f"\nFound {len(result.data)} entries for C9402\n")
    
    for i, error in enumerate(result.data, 1):
        print(f"--- Entry {i} ---")
        print(f"Error Code: {error['error_code']}")
        print(f"Description: {error['error_description']}")
        print(f"Page: {error['page_number']}")
        print(f"Document ID: {error['document_id']}")
        print(f"\nSolution Text:")
        print(f"Length: {len(error['solution_text'])} characters")
        print(f"Content: {error['solution_text'][:500]}")
        print(f"\n{'='*60}\n")
else:
    print("\n❌ No entries found for C9402")
