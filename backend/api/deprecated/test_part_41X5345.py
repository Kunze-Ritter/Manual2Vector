"""
Quick test: What does search_parts return for 41X5345?
"""

import json
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
