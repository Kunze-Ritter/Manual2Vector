# R2 Storage Cleanup Guide

## Prerequisites

**Install boto3:**
```bash
pip install boto3 python-dotenv
```

**Get R2 Credentials:**
1. Go to Cloudflare Dashboard → R2
2. Click "Manage R2 API Tokens"
3. Create new API Token with:
   - Permissions: Read & Write
   - Apply to: All buckets (or specific ones)
4. Copy: Account ID, Access Key ID, Secret Access Key

---

## Setup

**1. Create `.env` file in scripts directory:**
```bash
# scripts/.env
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
```

**OR set environment variables:**
```bash
export R2_ACCOUNT_ID=your_account_id
export R2_ACCESS_KEY_ID=your_access_key
export R2_SECRET_ACCESS_KEY=your_secret_key
```

**2. Update bucket names in script:**
Edit `cleanup_r2_storage.py` line ~18:
```python
BUCKETS = [
    'krai-documents',       # Your actual bucket names
    'krai-processed',
    # ... add your bucket names here
]
```

---

## Usage

### List all buckets (safe - no deletion):
```bash
python scripts/cleanup_r2_storage.py --list
```

### Dry run (show what would be deleted):
```bash
# All configured buckets
python scripts/cleanup_r2_storage.py --all --dry-run

# Specific bucket
python scripts/cleanup_r2_storage.py --bucket krai-documents --dry-run
```

### Delete objects from all buckets:
```bash
python scripts/cleanup_r2_storage.py --all
```

### Delete objects from specific bucket:
```bash
python scripts/cleanup_r2_storage.py --bucket krai-documents
```

### Delete objects AND buckets:
```bash
python scripts/cleanup_r2_storage.py --all --delete-buckets
```

---

## Examples

**1. Check what's in storage:**
```bash
python scripts/cleanup_r2_storage.py --list

# Output:
# 📋 Listing all buckets:
#    - krai-documents: 150 objects
#    - krai-processed: 423 objects
#    - krai-embeddings: 150 objects
#    Total: 723 objects across 3 buckets
```

**2. Safe test (dry run):**
```bash
python scripts/cleanup_r2_storage.py --all --dry-run

# Shows what would be deleted without actually deleting
```

**3. Delete everything (with confirmation):**
```bash
python scripts/cleanup_r2_storage.py --all

# ⚠️  WARNING: This will DELETE ALL objects from:
#    - krai-documents (150 objects)
#    - krai-processed (423 objects)
#    - krai-embeddings (150 objects)
# 
# ❓ Are you sure? Type 'yes' to continue: yes
# 
# 🗑️  Processing bucket: krai-documents
#    Found 150 objects in this page...
#    ✅ Deleted 150 objects
# ...
```

**4. Delete specific bucket only:**
```bash
python scripts/cleanup_r2_storage.py --bucket krai-documents
```

**5. Complete wipe (delete objects AND buckets):**
```bash
python scripts/cleanup_r2_storage.py --all --delete-buckets

# ⚠️  This will delete EVERYTHING including buckets themselves!
# Buckets will need to be recreated
```

---

## Safety Features

✅ **Dry run mode** - Test before deleting
✅ **Confirmation prompt** - Must type 'yes' to proceed
✅ **List mode** - Check what's there first
✅ **Progress output** - See what's happening
✅ **Error handling** - Shows what failed

---

## Notes

- R2 doesn't support bulk delete of buckets, only objects
- Objects are deleted in batches (faster than one-by-one)
- Empty buckets can be deleted with `--delete-buckets`
- Deleted objects cannot be recovered!
- Buckets will be auto-created again when you upload new files

---

## Troubleshooting

**"Missing R2 credentials" error:**
- Make sure `.env` file exists in scripts directory
- Or set environment variables
- Check credentials are correct

**"NoSuchBucket" error:**
- Bucket doesn't exist (maybe already deleted)
- Check bucket names in script match your actual buckets
- Use `--list` to see what buckets exist

**"AccessDenied" error:**
- API token doesn't have sufficient permissions
- Create new token with Read & Write permissions
- Make sure token is applied to correct buckets

---

## After Cleanup

**1. Verify cleanup:**
```bash
python scripts/cleanup_r2_storage.py --list
# Should show 0 objects in all buckets
```

**2. Database cleanup:**
```sql
-- In Supabase SQL Editor:
TRUNCATE krai_intelligence.chunks CASCADE;
TRUNCATE krai_intelligence.embeddings CASCADE;
TRUNCATE krai_intelligence.error_codes CASCADE;
TRUNCATE krai_core.products CASCADE;
TRUNCATE krai_core.documents CASCADE;
```

**3. Ready for fresh start!**
- Upload new PDFs
- Process with improved processor
- Monitor quality
