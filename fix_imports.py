#!/usr/bin/env python3
"""
Fix backend imports in service files
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix backend imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace backend imports with relative imports
        original_content = content
        content = re.sub(r'from backend\.', 'from ', content)
        content = re.sub(r'import backend\.', 'import ', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all Python files in backend directory"""
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("Backend directory not found")
        return
    
    fixed_count = 0
    total_count = 0
    
    for py_file in backend_dir.rglob("*.py"):
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"Fixed imports in {fixed_count}/{total_count} files")

if __name__ == "__main__":
    main()
