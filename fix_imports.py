"""
Fix all relative imports to absolute imports with backend. prefix
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Fix patterns
        patterns = [
            (r'^from services\.', 'from backend.services.'),
            (r'^from api\.', 'from backend.api.'),
            (r'^from processors\.', 'from backend.processors.'),
            (r'^from core\.', 'from backend.core.'),
            (r'^from utils\.', 'from backend.utils.'),
            (r'^from config\.', 'from backend.config.'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Only write if changed
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path.relative_to(Path.cwd())}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error in {file_path}: {e}")
        return False

def main():
    """Fix all Python files in backend/"""
    backend_dir = Path(__file__).parent / 'backend'
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return
    
    print("🔧 Fixing imports in backend/...")
    print()
    
    fixed_count = 0
    total_count = 0
    
    # Process all .py files
    for py_file in backend_dir.rglob('*.py'):
        # Skip __pycache__
        if '__pycache__' in str(py_file):
            continue
        
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print()
    print(f"✅ Fixed {fixed_count}/{total_count} files")

if __name__ == '__main__':
    main()
