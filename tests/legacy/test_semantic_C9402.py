"""
Check if semantic search has better data for C9402
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
print("TESTING: semantic_search('C9402 Konica Minolta')")
print("="*60)

result = tools.semantic_search("C9402 Konica Minolta error solution", limit=5)
data = json.loads(result)

print(f"\nFound: {data.get('found')}")
print(f"Count: {data.get('count')}")

if data.get('found'):
    print("\n" + "="*60)
    print("TOP 3 RESULTS:")
    print("="*60)
    
    # Check what keys are available
    print(f"\nAvailable keys: {list(data.keys())}")
    
    # Try to find the results
    results_key = None
    for key in ['chunks', 'results', 'documents', 'matches']:
        if key in data:
            results_key = key
            break
    
    if results_key:
        for i, chunk in enumerate(data[results_key][:3], 1):
            print(f"\n--- Result {i} ---")
            print(f"Keys in result: {list(chunk.keys())}")
            print(f"Document: {chunk.get('document_filename', chunk.get('filename', 'Unknown'))}")
            print(f"Page: {chunk.get('page_number', 'Unknown')}")
            print(f"Similarity: {chunk.get('similarity_score', chunk.get('similarity', 'Unknown'))}")
            print(f"\nContent ({len(chunk.get('content', chunk.get('text', '')))} chars):")
            print("-" * 60)
            content = chunk.get('content', chunk.get('text', ''))
            print(content[:800])  # First 800 chars
            print("\n...")
            print("-" * 60)
    else:
        print("\nCould not find results in data!")
        print(f"Full data: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
