# Content Management API

API endpoints for video enrichment and link checking.

## 🎯 **Endpoints**

### Base URL: `/content`

---

## 📹 **Video Enrichment**

### `POST /content/videos/enrich`
Enrich video links with metadata (async, returns immediately)

**Request:**
```json
{
  "limit": 100,
  "force": false
}
```

**Response:**
```json
{
  "status": "queued",
  "message": "Video enrichment started in background",
  "enriched_count": 0,
  "error_count": 0,
  "started_at": "2025-10-05T20:30:00.000Z",
  "task_id": "video_enrich_1728158400.123"
}
```

---

### `POST /content/videos/enrich/sync`
Enrich video links synchronously (waits for completion)

**Request:**
```json
{
  "limit": 10,
  "force": false
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Enriched 10 videos",
  "enriched_count": 10,
  "error_count": 0,
  "started_at": "2025-10-05T20:30:00.000Z"
}
```

**Parameters:**
- `limit` (optional): Maximum number of videos to process
- `force` (optional): Re-process already enriched videos (default: `false`)

**Supported Platforms:**
- ✅ YouTube (full metadata, views, likes, etc.)
- ✅ Vimeo (title, description, thumbnails)
- ✅ Brightcove (full metadata via Playback API)

---

## 🔗 **Link Checking**

### `POST /content/links/check`
Check links for validity (async, returns immediately)

**Request:**
```json
{
  "limit": 100,
  "check_only": true,
  "check_inactive": false
}
```

**Response:**
```json
{
  "status": "queued",
  "message": "Link checking started in background",
  "checked_count": 0,
  "working_count": 0,
  "broken_count": 0,
  "fixed_count": 0,
  "error_count": 0,
  "started_at": "2025-10-05T20:30:00.000Z",
  "task_id": "link_check_1728158400.123"
}
```

---

### `POST /content/links/check/sync`
Check links synchronously (waits for completion)

**Request:**
```json
{
  "limit": 10,
  "check_only": false,
  "check_inactive": false
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Checked 10 links",
  "checked_count": 10,
  "working_count": 8,
  "broken_count": 1,
  "fixed_count": 1,
  "error_count": 0,
  "started_at": "2025-10-05T20:30:00.000Z"
}
```

**Parameters:**
- `limit` (optional): Maximum number of links to check
- `check_only` (optional): Only check without fixing (default: `true`)
- `check_inactive` (optional): Also check inactive links (default: `false`)

**Features:**
- ✅ Auto-clean trailing punctuation (PDF extraction artifacts)
- ✅ Follow redirects (301/302/307/308)
- ✅ GET fallback for servers that reject HEAD
- ✅ Auto-fix common issues (http→https, www, etc.)

---

## 📊 **Task Status**

### `GET /content/tasks/{task_id}`
Get status of a background task

**Response:**
```json
{
  "task_id": "video_enrich_1728158400.123",
  "status": "running",
  "progress": {
    "current": 50,
    "total": 100
  },
  "result": null,
  "error": null
}
```

**Statuses:**
- `queued`: Task is waiting to start
- `running`: Task is currently executing
- `completed`: Task finished successfully
- `failed`: Task encountered an error

---

### `GET /content/tasks`
List all background tasks

**Response:**
```json
{
  "tasks": {
    "video_enrich_1728158400.123": {
      "status": "completed",
      "type": "video_enrichment",
      "started_at": "2025-10-05T20:30:00.000Z",
      "completed_at": "2025-10-05T20:32:00.000Z",
      "result": {
        "enriched": 100,
        "errors": 0
      }
    }
  },
  "count": 1
}
```

---

## 🧪 **Examples**

### cURL Examples

**Enrich Videos (Async):**
```bash
curl -X POST http://localhost:8000/content/videos/enrich \
  -H "Content-Type: application/json" \
  -d '{"limit": 50, "force": false}'
```

**Check Links (Sync, Small Batch):**
```bash
curl -X POST http://localhost:8000/content/links/check/sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "check_only": true}'
```

**Get Task Status:**
```bash
curl http://localhost:8000/content/tasks/video_enrich_1728158400.123
```

---

### Python Examples

```python
import requests

# Enrich videos asynchronously
response = requests.post(
    "http://localhost:8000/content/videos/enrich",
    json={"limit": 100, "force": False}
)
task_id = response.json()["task_id"]

# Check task status
status = requests.get(f"http://localhost:8000/content/tasks/{task_id}")
print(status.json())

# Check links synchronously (small batch)
response = requests.post(
    "http://localhost:8000/content/links/check/sync",
    json={"limit": 10, "check_only": False}
)
print(response.json())
```

---

## 📝 **Notes**

**When to use Async vs Sync:**
- **Async** (`/enrich`, `/check`): For large batches (100+ items), long-running tasks
- **Sync** (`/enrich/sync`, `/check/sync`): For small batches (< 20 items), testing

**API Keys:**
- YouTube API key required for YouTube video enrichment
- Set in `.env`: `YOUTUBE_API_KEY=your_key_here`
- Get key at: https://console.cloud.google.com/apis/credentials

**Rate Limits:**
- Video enrichment: ~10,000 YouTube videos/day (free tier)
- Link checking: 0.5s delay between requests (respect servers)

---

## 🚀 **Testing in Swagger UI**

Visit `http://localhost:8000/docs` to test endpoints interactively!
