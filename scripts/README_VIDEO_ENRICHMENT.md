# Video Enrichment & Link Checking Scripts

## 📹 Video Metadata Enricher

Enriches video links with metadata from YouTube, Vimeo, and other sources.

### Setup

1. **Get YouTube API Key:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create a new project or select existing
   - Enable "YouTube Data API v3"
   - Create credentials (API Key)
   - Copy the API key

2. **Add to .env file:**
   ```bash
   YOUTUBE_API_KEY=your_actual_api_key_here
   ```

3. **Install dependencies:**
   ```bash
   pip install httpx
   ```

### Usage

```bash
# Enrich all unenriched video links
python scripts/enrich_video_metadata.py

# Process only 10 videos (for testing)
python scripts/enrich_video_metadata.py --limit 10

# Re-process already enriched videos
python scripts/enrich_video_metadata.py --force

# Help
python scripts/enrich_video_metadata.py --help
```

### What it does

- ✅ Fetches YouTube video metadata (title, description, duration, views, etc.)
- ✅ Fetches Vimeo video metadata via oEmbed API
- ✅ Fetches Brightcove video metadata via Playback API
- ✅ Extracts thumbnails
- ✅ Updates `videos` table with enriched data
- ✅ Links back to original `links` table
- ✅ Rate limiting (10,000 quota/day for YouTube)
- ✅ **Full Deduplication:** Same video from different links = single record

### Deduplication Strategy

**Smart deduplication prevents duplicate video metadata:**

- **YouTube:** Checks by `youtube_id` first (e.g., `ABC123` from `youtube.com/watch?v=ABC123` or `youtu.be/ABC123`)
- **Vimeo:** Checks by `vimeo_id` in metadata JSON
- **Brightcove:** Checks by `brightcove_id` in metadata JSON

**Example:**
```
Link A: https://youtube.com/watch?v=ABC123
Link B: https://youtu.be/ABC123
→ Creates only 1 video record
→ Both links point to the same video
```

**Benefits:**
- 💾 Saves storage space
- 📊 Better analytics (views counted once)
- 🔗 Multiple links can share same video metadata

### YouTube API Quota

- **Free tier:** 10,000 units/day
- **Cost per video:** 1 unit
- **You can enrich:** ~10,000 videos/day


## 🔗 Link Checker & Fixer

Checks links for validity and attempts to fix broken ones.

### **Features:**
- ✅ Auto-clean trailing punctuation (PDF extraction artifacts)
- ✅ Follow redirects (301/302/307/308) with extended timeout (30s)
- ✅ GET fallback for servers that reject HEAD or timeout
- ✅ Auto-fix common issues (http→https, www, etc.)
- ✅ Retry mechanism for slow servers (e.g., HP support)
- ✅ Redirect following
- ✅ Auto-deactivate broken links (404)
- ✅ Auto-update database with fixed links

### Usage
{{ ... }}

```bash
# Check and fix all links
python scripts/check_and_fix_links.py

# Check only (no fixes)
python scripts/check_and_fix_links.py --check-only

# Check only 10 links (for testing)
python scripts/check_and_fix_links.py --limit 10

# Also check inactive links
python scripts/check_and_fix_links.py --inactive

# Help
python scripts/check_and_fix_links.py --help
```

### What it does

1. **Checks each link:**
   - HTTP HEAD request to verify accessibility
   - Returns status code (200, 404, etc.)

2. **Attempts to fix broken links:**
   - Try https vs http
   - Remove/add www
   - Fix URL encoding
   - Follow redirects
   - Try common variations

3. **Updates database:**
   - Updates `url` field with fixed URL
   - Stores original URL in `metadata`
   - Marks 404 links as `is_active = false`

### Common Fixes

| Problem | Fix |
|---------|-----|
| `https://example.com.` (trailing dot from PDF) | Remove trailing `.` |
| `https://example.com,` (trailing comma) | Remove trailing `,;:!?)]}` |
| `http://example.com` → 404 | Try `https://example.com` |
| `example.com/page ` (trailing space) | Remove whitespace |
| `example.com/page` (no protocol) | Add `https://` |
| Missing `www.` | Try with/without `www.` |
| Redirects | Follow to final URL |
| URL with spaces | Encode as `%20` |

**🔍 Smart URL Cleaning:**
The link checker automatically removes trailing punctuation that often comes from PDF text extraction (e.g., URLs at the end of sentences).

**📊 Contextual Metadata:**
Videos are automatically linked to manufacturers, product series, and error codes based on the source document:
- `manufacturer_id`: Which manufacturer this video relates to (e.g., HP, Canon)
- `series_id`: Which product series (e.g., LaserJet Pro, OfficeJet)
- `related_error_codes`: Array of error codes mentioned in the source document

This enables powerful filtering like "Show me all HP LaserJet videos about error 49.4C02".

---

## 🔄 Automated Workflow (N8N)

You can automate these scripts with N8N:

### Daily Video Enrichment

```json
{
  "schedule": "0 2 * * *",  // 2 AM daily
  "action": "Execute Command",
  "command": "python /path/to/scripts/enrich_video_metadata.py --limit 100"
}
```

### Weekly Link Check

```json
{
  "schedule": "0 3 * * 0",  // 3 AM every Sunday
  "action": "Execute Command",
  "command": "python /path/to/scripts/check_and_fix_links.py"
}
```

---

## 📊 Monitoring

### Check enrichment status

```sql
-- How many videos are enriched?
SELECT 
    COUNT(*) as total_video_links,
    COUNT(video_id) as enriched,
    COUNT(*) - COUNT(video_id) as pending
FROM krai_content.links
WHERE link_type IN ('video', 'youtube', 'vimeo');
```

### Check link health

```sql
-- Link status overview
SELECT 
    is_active,
    link_type,
    COUNT(*) as count
FROM krai_content.links
GROUP BY is_active, link_type
ORDER BY link_type, is_active DESC;
```

### Find broken links

```sql
-- Recently deactivated links
SELECT 
    url,
    link_type,
    metadata->>'deactivated_at' as deactivated_at,
    metadata->>'reason' as reason
FROM krai_content.links
WHERE is_active = false
AND metadata->>'deactivated_at' IS NOT NULL
ORDER BY metadata->>'deactivated_at' DESC
LIMIT 20;
```

---

## 🚀 Best Practices

### Video Enrichment

1. **Run daily** for new links
2. **Start with `--limit 10`** to test
3. **Monitor API quota** (check Google Cloud Console)
4. **Re-run with `--force`** quarterly to refresh old data

### Link Checking

1. **Run `--check-only`** first to see what's broken
2. **Review broken links** before auto-fixing
3. **Run weekly** to catch new broken links
4. **Monitor deactivated links** - some might be temporary outages

---

## 🐛 Troubleshooting

### YouTube API Errors

**"quotaExceeded" (403)**
- You've hit the 10,000 units/day limit
- Wait until next day (resets at midnight Pacific Time)
- Or request quota increase

**"Invalid API Key" (403)**
- Check your API key in .env
- Make sure YouTube Data API v3 is enabled
- Regenerate API key if needed

**"Video not found" (404)**
- Video was deleted or made private
- Link will be marked as broken

### Link Checker Issues

**"Connection timeout"**
- Site might be slow or down
- Script will retry common fixes
- Check manually if important

**"Too many requests" (429)**
- You're being rate-limited
- Script includes delays, but some sites are strict
- Run with `--limit` to reduce load

**SSL/Certificate errors**
- Some sites have invalid certificates
- Script will try http:// fallback
- Consider manually fixing these

---

## 📝 Logs

Scripts create detailed logs showing:
- ✅ Successfully enriched/fixed
- ❌ Errors encountered
- 🔀 Redirects followed
- 💾 Database updates

Example output:
```
🔍 Finding video links to enrich...
📹 Found 42 video links to process

[1/42] Processing: https://youtube.com/watch?v=abc123
   ✅ Enriched YouTube video: How to fix error S800...
   💾 Database updated

[2/42] Processing: https://vimeo.com/123456
   ✅ Enriched Vimeo video: Maintenance tutorial...
   💾 Database updated

✅ Processing complete!
   Enriched: 40
   Errors: 2
```
