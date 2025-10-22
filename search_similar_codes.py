"""Search for similar error codes"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path(__file__).parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Search for HP E877 or 66.60 codes
searches = [
    ("E877", "HP E877 Drucker"),
    ("66.60", "66.60.* Fehlercodes"),
    ("66.*", "66.* Fehlercodes")
]

for search_term, description in searches:
    print(f"\n{'='*60}")
    print(f"Suche: {description} ({search_term})")
    print('='*60)
    
    result = client.table('vw_error_codes').select(
        'error_code, error_description, chunk_id'
    ).ilike('error_code', f'*{search_term}*').limit(5).execute()
    
    print(f"Gefunden: {len(result.data)} Ergebnisse\n")
    
    for i, error in enumerate(result.data, 1):
        code = error.get('error_code')
        desc = error.get('error_description', 'N/A')
        chunk_id = error.get('chunk_id')
        has_image = "🖼️" if chunk_id else "  "
        print(f"{i}. {has_image} {code}: {desc[:80]}")
