"""
Quick test: What does search_parts return for 41X5345?
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
print("TESTING: search_parts('41X5345')")
print("="*60)

result = tools.search_parts("41X5345")
print("\nRaw JSON result:")
print(result)

print("\n" + "="*60)
print("Parsed result:")
print("="*60)

data = json.loads(result)
print(json.dumps(data, indent=2, ensure_ascii=False))
