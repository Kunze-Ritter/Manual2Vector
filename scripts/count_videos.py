"""Count videos in Supabase"""

import os

from supabase import create_client

from scripts._env import load_env

load_env()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
result = client.table('vw_videos').select('id, title, manufacturer_id').limit(10).execute()
print(f'Videos in DB: {len(result.data)}')
for v in result.data[:5]:
    print(f"  - {v.get('title', 'N/A')[:60]}")
