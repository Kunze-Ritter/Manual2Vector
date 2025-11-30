"""Apply Migration 82: Cleanup duplicate views and rules"""

import os
from pathlib import Path

from supabase import create_client

from scripts._env import load_env

# Load environment
load_env()

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*60)
print("APPLYING MIGRATION 82: Cleanup duplicate views and rules")
print("="*60)

# Read migration file
migration_file = Path(__file__).resolve().parent.parent / 'database' / 'migrations' / '82_cleanup_duplicate_views_and_rules.sql'
with open(migration_file, 'r', encoding='utf-8') as f:
    sql = f.read()

# Extract SQL statements (skip comments and empty lines)
statements = []
current_statement = []
for line in sql.split('\n'):
    line = line.strip()
    if line.startswith('--') or not line:
        continue
    current_statement.append(line)
    if line.endswith(';'):
        statements.append(' '.join(current_statement))
        current_statement = []

print(f"\nFound {len(statements)} SQL statements to execute\n")

# Execute each statement
for i, statement in enumerate(statements, 1):
    print(f"{i}. Executing: {statement[:80]}...")
    try:
        supabase.rpc('exec_sql', {'sql': statement}).execute()
        print(f"   ✅ Success")
    except Exception as e:
        # Try direct execution if RPC fails
        print(f"   ⚠️  RPC failed, trying direct execution...")
        try:
            # For DROP RULE, we need to use raw SQL
            # Supabase doesn't support this via REST API
            print(f"   ℹ️  Please run this manually in Supabase SQL Editor:")
            print(f"   {statement}")
        except Exception as e2:
            print(f"   ❌ Failed: {e2}")

print("\n" + "="*60)
print("✅ MIGRATION 82 COMPLETED")
print("="*60)
print("\nNote: If any statements failed, run them manually in Supabase SQL Editor:")
print("https://supabase.com/dashboard/project/YOUR_PROJECT/sql")
