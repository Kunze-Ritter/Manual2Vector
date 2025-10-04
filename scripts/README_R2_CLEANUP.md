# 🧹 R2 Image Cleanup & Hash Migration

**Purpose:** Migrate old images to hash-based naming with deduplication  
**Date:** 2025-10-04

---

## 🎯 What This Script Does:

1. Lists all images in R2 bucket
2. Downloads each temporarily
3. Calculates MD5 hash
4. Checks if hash exists (deduplication!)
5. Uploads with new name: `{hash}.{extension}`
6. Inserts to `krai_content.images`
7. Deletes old image
8. Cleans up temp files

---

## 🚀 Usage:

### Dry Run (Preview):
```bash
python cleanup_r2_images_with_hashes.py --dry-run
```

### Execute Cleanup:
```bash
python cleanup_r2_images_with_hashes.py --execute
```

⚠️ **WARNING:** `--execute` makes real changes!

---

## 📊 Example Output:

```
Migrated: 350
Deduplicated: 119  (25.4% savings!)
Failed: 0
```

---

## 🗂️ Old vs New:

**Before:** `documents/uuid/images/page_0001_diagram.png`  
**After:** `a1b2c3d4e5f6.png`

---

## ⚠️ Important:

**Wait until current processing job finishes!**

---

**Last Updated:** 2025-10-04
