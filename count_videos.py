import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path('.env.database'))
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
result = client.table('vw_videos').select('id, title, manufacturer_id').limit(10).execute()
print(f'Videos in DB: {len(result.data)}')
for v in result.data[:5]:
    print(f"  - {v.get('title', 'N/A')[:60]}")
