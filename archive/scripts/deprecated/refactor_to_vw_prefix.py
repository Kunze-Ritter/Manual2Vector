"""
Refactor all .table() calls to use vw_ prefix
"""

import os
import re
from pathlib import Path

# Mapping: old table name → new vw_ name
TABLE_MAPPINGS = {
    "table('documents')": "table('vw_documents')",
    'table("documents")': 'table("vw_documents")',
    
    "table('manufacturers')": "table('vw_manufacturers')",
    'table("manufacturers")': 'table("vw_manufacturers")',
    
    "table('products')": "table('vw_products')",
    'table("products")': 'table("vw_products")',
    
    "table('error_codes')": "table('vw_error_codes')",
    'table("error_codes")': 'table("vw_error_codes")',
    
    "table('chunks')": "table('vw_chunks')",
    'table("chunks")': 'table("vw_chunks")',
    
    "table('links')": "table('vw_links')",
    'table("links")': 'table("vw_links")',
    
    "table('videos')": "table('vw_videos')",
    'table("videos")': 'table("vw_videos")',
    
    "table('images')": "table('vw_images')",
    'table("images")': 'table("vw_images")',
    
    "table('parts_catalog')": "table('vw_parts')",
    'table("parts_catalog")': 'table("vw_parts")',
    
    "table('embeddings')": "table('vw_embeddings')",
    'table("embeddings")': 'table("vw_embeddings")',
    
    "table('product_series')": "table('vw_product_series')",
    'table("product_series")': 'table("vw_product_series")',
    
    "table('document_products')": "table('vw_document_products')",
    'table("document_products")': 'table("vw_document_products")',
    
    "table('video_products')": "table('vw_video_products')",
    'table("video_products")': 'table("vw_video_products")',
    
    "table('system_metrics')": "table('vw_system_metrics')",
    'table("system_metrics")': 'table("vw_system_metrics")',
    
    "table('intelligence_chunks')": "table('vw_intelligence_chunks')",
    'table("intelligence_chunks")': 'table("vw_intelligence_chunks")',
}

# Tables that should NOT be changed (already correct or special cases)
SKIP_TABLES = [
    'product_series',
    'document_products',
    'oem_relationships',
    'video_products',
    'processing_queue',
    'system_metrics',
    'audit_log',
    'webhook_logs',
]

def refactor_file(file_path: Path) -> tuple[int, list[str]]:
    """Refactor a single Python file"""
    
    # Try UTF-8 first, fallback to Latin-1
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to Latin-1 (Windows-1252)
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  Skipping {file_path.name} (encoding error: {e})")
            return 0, []
    
    original_content = content
    changes = []
    
    # Apply replacements
    for old, new in TABLE_MAPPINGS.items():
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            changes.append(f"  {old} → {new} ({count}x)")
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return len(changes), changes
    
    return 0, []

def main():
    """Refactor all Python files in backend/"""
    
    backend_dir = Path(__file__).parent.parent / 'backend'
    
    print("="*60)
    print("REFACTORING: .table() calls to vw_ prefix")
    print("="*60)
    
    total_files = 0
    total_changes = 0
    
    # Find all Python files
    for py_file in backend_dir.rglob('*.py'):
        # Skip __pycache__ and .venv
        if '__pycache__' in str(py_file) or '.venv' in str(py_file):
            continue
        
        change_count, changes = refactor_file(py_file)
        
        if change_count > 0:
            total_files += 1
            total_changes += change_count
            
            rel_path = py_file.relative_to(backend_dir)
            print(f"\n✅ {rel_path}")
            for change in changes:
                print(change)
    
    print("\n" + "="*60)
    print(f"✅ REFACTORED {total_files} files with {total_changes} changes")
    print("="*60)
    
    if total_changes == 0:
        print("\n⚠️  No changes needed - all files already use vw_ prefix!")

if __name__ == '__main__':
    main()
