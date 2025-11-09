"""Debug PostgreSQL connection URL"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts._env import load_env

# Load environment
load_env(extra_files=['.env.database'])

print("="*70)
print("DATABASE CONNECTION DEBUG")
print("="*70)

# Check environment variables
db_type = os.getenv('DATABASE_TYPE')
db_url = os.getenv('DATABASE_CONNECTION_URL')

print(f"\nDATABASE_TYPE: {repr(db_type)}")
print(f"DATABASE_CONNECTION_URL: {repr(db_url)}")

if db_url:
    print(f"\nURL Length: {len(db_url)}")
    print(f"URL bytes: {db_url.encode('utf-8')}")
    print(f"Contains [: {('[' in db_url)}")
    print(f"Contains ]: {(']' in db_url)}")
    
    # Try parsing with urllib
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(db_url)
        print(f"\n✅ urllib.parse succeeded:")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Netloc: {parsed.netloc}")
        print(f"   Hostname: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Path: {parsed.path}")
    except Exception as e:
        print(f"\n❌ urllib.parse failed: {e}")
        print(f"   This is why asyncpg fails!")
        
        # Check for common issues
        if '[' in db_url or ']' in db_url:
            print("\n⚠️  Found brackets in URL - this suggests IPv6 notation")
            print("   For IPv4, use: postgresql://user:pass@127.0.0.1:5432/db")
        
        # Show character by character
        print("\nCharacter analysis:")
        for i, char in enumerate(db_url):
            if not char.isprintable() or char in '[]':
                print(f"   Position {i}: {repr(char)} (ord={ord(char)})")

print("\n" + "="*70)
