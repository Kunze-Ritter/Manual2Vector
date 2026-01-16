"""
Check database schema for solution_text column
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
print("CHECKING DB SCHEMA FOR solution_text")
print("="*60)

# Query schema
result = supabase.rpc('exec_sql', {
    'query': """
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_schema = 'krai_intelligence' 
    AND table_name = 'error_codes' 
    AND column_name = 'solution_text';
    """
}).execute()

print("\nSchema:")
print(result.data)

print("\n" + "="*60)
print("CHECKING ACTUAL DATA FOR C9402")
print("="*60)

# Get actual data
result2 = supabase.table('vw_error_codes').select('error_code, solution_text, LENGTH(solution_text) as len').eq('error_code', 'C9402').limit(1).execute()

if result2.data:
    print(f"\nError Code: {result2.data[0]['error_code']}")
    print(f"Solution Length: {result2.data[0].get('len', 'N/A')} characters")
    print(f"Solution Text: {result2.data[0]['solution_text']}")
else:
    print("\nNo data found for C9402")
