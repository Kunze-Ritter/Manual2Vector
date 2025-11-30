# 🔧 Fixes Directory Documentation

## Overview

The `fixes/` subdirectory contains one-time fix scripts for data corrections and consistency improvements. These scripts are designed to address specific data issues that may arise during normal operations or data migration.

## Active Fix Scripts

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `fix_document_metadata.py` | Correct faulty document metadata | `python scripts/fixes/fix_document_metadata.py --dry-run` | Active |
| `fix_parts_catalog_products.py` | Fix parts catalog product associations | `python scripts/fixes/fix_parts_catalog_products.py --dry-run` | Active |
| `link_videos_to_products.py` | Link videos to products based on metadata | `python scripts/fixes/link_videos_to_products.py --limit 100` | Active |

## Historical/Deprecated Fix Scripts

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `update_video_manufacturers.py` | Update manufacturer assignments for videos | `python scripts/fixes/update_video_manufacturers.py --dry-run` | Removed from active scripts list (2025-11-29) |

## Usage Guidelines

### When to Use Fix Scripts

Fix scripts should be used when:
- Data inconsistencies are detected in the database
- Migration or processing errors cause data corruption
- Manual data entry errors need correction
- System upgrades require data format updates

### Best Practices

1. **Always Use Dry-Run First**: Most scripts support `--dry-run` flag to preview changes
2. **Backup Data**: Create database backups before running fix scripts
3. **Test on Small Subset**: Use `--limit` parameter to test on small data subsets
4. **Review Logs**: Check script output for any unexpected behavior
5. **Monitor Performance**: Large fixes may impact database performance

### Creating New Fix Scripts

When creating new fix scripts:

1. **Naming Convention**: Use `fix_<issue>.py` format
2. **Include Dry-Run**: Always implement `--dry-run` functionality
3. **Add Logging**: Use proper logging for tracking changes
4. **Rollback Strategy**: Document how to undo changes if needed
5. **Update Documentation**: Add script to this README with description

### Script Template

```python
#!/usr/bin/env python3
"""
Fix Script Template

Description of what this script fixes.
"""

import argparse
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts._env import load_env
from backend.processors.logger import get_logger

def main():
    parser = argparse.ArgumentParser(description="Fix specific data issue")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--limit", type=int, help="Limit number of records to process")
    
    args = parser.parse_args()
    
    logger = get_logger()
    logger.info("=" * 80)
    logger.info("FIX SCRIPT: <Issue Name>")
    logger.info("=" * 80)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
    
    # Implementation here
    
    logger.info("=" * 80)
    logger.info("FIX COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
```

## Usage Examples

### Dry-Run (Recommended First)

```bash
# Preview changes for document metadata fix
python scripts/fixes/fix_document_metadata.py --dry-run

# Preview changes for parts catalog fix with limit
python scripts/fixes/fix_parts_catalog_products.py --dry-run --limit 50
```

### Actual Execution

```bash
# Fix document metadata
python scripts/fixes/fix_document_metadata.py

# Link videos to products with limit
python scripts/fixes/link_videos_to_products.py --limit 100

# Update video manufacturers (Historical - removed from active scripts)
# python scripts/fixes/update_video_manufacturers.py
```

### Advanced Usage
```bash
# Fix with specific parameters
python scripts/fixes/fix_parts_catalog_products.py --manufacturer "Konica Minolta" --dry-run

# Process large datasets in batches
python scripts/fixes/link_videos_to_products.py --limit 1000 --batch-size 100
```

## Historical Fixes

### Completed Fixes

| Fix | Date | Records Affected | Status |
|-----|------|------------------|--------|
| Video Platform Fix | 2025-11-XX | 13 videos | ✅ Completed |
| Video manufacturer_id Update | 2025-11-XX | 217 videos | ✅ Completed |

### Migration History

Previous SQL-based fixes have been moved to `database/migrations/`:
- `100_update_rpc_function_add_chunk_id.sql` - RPC function update
- `101_fix_links_manufacturer_id.sql` - Links manufacturer_id fix

## Important Notes

⚠️ **CRITICAL**: Always test fix scripts in a development environment before running on production data.

⚠️ **BACKUP**: Create database backups before executing any fix scripts.

⚠️ **PERFORMANCE**: Large fix operations may impact database performance. Consider running during maintenance windows.

⚠️ **MONITORING**: Monitor database performance during fix execution.

## Related Documentation

- `scripts/README.md` - Main scripts documentation
- `archive/scripts/README.md` - Archived scripts documentation
- `docs/PROJECT_CLEANUP_LOG.md` - Cleanup history
- `DATABASE_SCHEMA.md` - Database schema reference
- `DB_FIXES_CHECKLIST.md` - Database fixes checklist

## Support

For questions about fix scripts:
1. Check script logs for detailed error messages
2. Review this documentation for usage guidelines
3. Consult the database schema documentation
4. Contact the development team for complex issues

## Rollback Procedures

If a fix script causes issues:

1. **Stop the script** immediately if running
2. **Restore from backup** if available
3. **Review logs** to identify affected records
4. **Create reverse script** if manual rollback needed
5. **Test thoroughly** before re-running
