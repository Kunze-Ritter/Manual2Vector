"""Check whether the YouTube API key is configured."""

import os

from scripts._env import load_env

load_env()
key = os.getenv('YOUTUBE_API_KEY')
print(f'YouTube API Key: {"SET ✅" if key else "NOT SET ❌"}')
if key:
    print(f'Key preview: {key[:10]}...')
