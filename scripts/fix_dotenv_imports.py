#!/usr/bin/env python3
"""
Fix dotenv imports in all scripts to be optional
"""

from pathlib import Path
import re

# Files to fix
files_to_fix = [
    'check_and_fix_links.py',
    'cleanup_production_db.py',
    'cleanup_r2_images_with_hashes.py',
    'cleanup_r2_storage.py',
    'delete_r2_bucket_contents.py',
    # enrich_video_metadata.py already fixed
]

old_pattern = r'from dotenv import load_dotenv\n(.*?)load_dotenv\(\)'
new_code = '''try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use system environment
    pass'''

for filename in files_to_fix:
    filepath = Path(__file__).parent / filename
    if not filepath.exists():
        print(f"⚠️  {filename} not found")
        continue
    
    content = filepath.read_text(encoding='utf-8')
    
    # Check if already fixed
    if 'except ImportError' in content and 'dotenv' in content:
        print(f"✅ {filename} already fixed")
        continue
    
    # Replace pattern
    if 'from dotenv import load_dotenv' in content:
        # Simple replacement
        content = content.replace(
            'from dotenv import load_dotenv',
            'try:\n    from dotenv import load_dotenv\nexcept ImportError:\n    load_dotenv = lambda: None  # Fallback'
        )
        
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Fixed {filename}")
    else:
        print(f"⚠️  {filename} doesn't use dotenv")

print("\n✅ Done!")
