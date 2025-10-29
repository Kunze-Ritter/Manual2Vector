import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path('.env.database'))
key = os.getenv('YOUTUBE_API_KEY')
print(f'YouTube API Key: {"SET ✅" if key else "NOT SET ❌"}')
if key:
    print(f'Key preview: {key[:10]}...')
