"""Check video link types in database"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path(__file__).parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Count by link_type
result = client.schema('krai_content').table('links').select(
    'link_type'
).in_('link_type', ['video', 'youtube', 'vimeo', 'brightcove']).execute()

from collections import Counter
counts = Counter([r['link_type'] for r in result.data])

print("Video Links by Type:")
for link_type, count in counts.items():
    print(f"  {link_type}: {count}")

# Check which have video_id
enriched = client.schema('krai_content').table('links').select(
    'link_type, video_id'
).in_('link_type', ['video', 'youtube', 'vimeo', 'brightcove']).not_.is_('video_id', 'null').execute()

enriched_counts = Counter([r['link_type'] for r in enriched.data])

print("\nEnriched (with video_id):")
for link_type, count in enriched_counts.items():
    print(f"  {link_type}: {count}")

print("\nNot enriched:")
for link_type in counts.keys():
    not_enriched = counts[link_type] - enriched_counts.get(link_type, 0)
    if not_enriched > 0:
        print(f"  {link_type}: {not_enriched}")
