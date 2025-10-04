# 🗑️ R2 Bucket Bulk Delete

**Purpose:** Delete ALL objects from any R2 bucket (even with 4000+ files!)

---

## 🎯 Problem:

Cloudflare UI only allows deleting **25 objects at a time**.  
For 4000 objects: **160 manual clicks!** 😰

**This script:** Deletes **1000 per batch** = Only **4 API calls!** ⚡

---

## 🚀 Quick Start:

### **Option 1: Use .env credentials (EU buckets)**

```bash
# Preview
python delete_r2_bucket_contents.py --bucket ai-technik-agent --dry-run

# Delete
python delete_r2_bucket_contents.py --bucket ai-technik-agent --delete
```

### **Option 2: Different Account/Region (USA bucket)**

```bash
# With custom credentials
python delete_r2_bucket_contents.py --bucket ai-technik-agent --delete \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --endpoint https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
```

---

## 🔑 How to Get USA Account Credentials:

1. **Go to Cloudflare Dashboard:**
   - https://dash.cloudflare.com/

2. **Select the USA Account** (where `ai-technik-agent` bucket is)

3. **Navigate to R2:**
   - Sidebar → R2

4. **Get Account ID:**
   - Look at the URL or bucket settings
   - Should be something like: `https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com`

5. **Create API Token:**
   - Click "Manage R2 API Tokens"
   - Create new token
   - Permissions: **Object Read & Write**
   - Copy: Access Key ID & Secret Access Key

6. **Run Script:**
   ```bash
   python delete_r2_bucket_contents.py \
     --bucket ai-technik-agent \
     --delete \
     --access-key YOUR_KEY_HERE \
     --secret-key YOUR_SECRET_HERE \
     --endpoint https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
   ```

---

## 🔐 Safety Features:

1. **Dry-run by default** - Always preview first!
2. **Double confirmation:**
   - Must type bucket name
   - Must type "DELETE ALL"
3. **Shows total objects & size** before deletion
4. **Cannot be undone warning**

---

## 📊 Example Output:

```
================================================================================
  R2 BUCKET BULK DELETE
================================================================================

Bucket: ai-technik-agent
Mode: DELETE MODE
Endpoint: https://a88f92c913c232559845adb9001a5d14.r2.cloudflarestorage.com

📋 Listing all objects...
   Found 500 objects so far...
   Found 1000 objects so far...
   ...
   Found 4000 objects so far...
✅ Found 4000 objects
   Total Size: 1234.56 MB

⚠️  WARNING: DESTRUCTIVE OPERATION
⚠️  THIS CANNOT BE UNDONE!

To confirm, type the bucket name: ai-technik-agent
   Bucket name: ai-technik-agent

Type 'DELETE ALL' to proceed:
   Confirmation: DELETE ALL

🗑️  Deleting 4000 objects in batches of 1000...

[Batch 1/4] Deleting 1000 objects...
   ✅ Deleted 1000/1000 objects

[Batch 2/4] Deleting 1000 objects...
   ✅ Deleted 1000/1000 objects

[Batch 3/4] Deleting 1000 objects...
   ✅ Deleted 1000/1000 objects

[Batch 4/4] Deleting 1000 objects...
   ✅ Deleted 1000/1000 objects

================================================================================
  CLEANUP SUMMARY
================================================================================

📊 Statistics:
   Bucket: ai-technik-agent
   Total Objects: 4000
   Deleted: 4000
   Failed: 0
   Batches: 4

✅ CLEANUP COMPLETE!
   Bucket 'ai-technik-agent' is now empty
   You can now delete the bucket via Cloudflare dashboard
```

---

## ⏱️ Performance:

| Method | Time | Effort |
|--------|------|--------|
| Cloudflare UI (25 per click) | ~30 minutes | 160 clicks 😰 |
| This Script (1000 per batch) | **~10 seconds** | 1 command ⚡ |

---

## 📝 After Script Completes:

1. ✅ Bucket is empty
2. ✅ Go to Cloudflare Dashboard
3. ✅ Delete the empty bucket (instant!)

---

**Last Updated:** 2025-10-04
