# 📦 KRAI Storage Buckets - Setup Guide

## ⚠️ Wichtiger Hinweis

Storage Buckets können **NICHT über SQL-Migrationen** erstellt werden, da dies Owner-Rechte auf der `storage.buckets` Tabelle erfordert. Sie müssen über das **Supabase Dashboard** oder die **Management API** erstellt werden.

---

## 🎯 Erforderliche Storage Buckets

Das KRAI-System benötigt **3 Storage Buckets** für verschiedene Bildtypen:

| Bucket Name | Zweck | Public | Max Size | Allowed Types |
|-------------|-------|--------|----------|---------------|
| `krai-document-images` | Bilder aus Service Manuals | No | 50 MB | image/jpeg, image/png, image/gif, image/webp |
| `krai-error-images` | Defekt-Bilder von Technikern | No | 50 MB | image/jpeg, image/png, image/gif, image/webp |
| `krai-parts-images` | Ersatzteil-Katalog Bilder | No | 50 MB | image/jpeg, image/png, image/gif, image/webp |

---

## 📋 Methode 1: Supabase Dashboard (Empfohlen)

### Schritt 1: Zum Storage Dashboard navigieren

1. Öffne dein Supabase Projekt: https://supabase.com/dashboard
2. Wähle dein Projekt aus
3. Navigiere zu **Storage** im linken Menü

### Schritt 2: Buckets erstellen

Für **jeden** der 3 Buckets:

1. Klicke auf **"New bucket"**
2. Fülle die Felder aus:

#### Bucket 1: krai-document-images

```
Name: krai-document-images
Public bucket: ☐ (NICHT öffentlich)
File size limit: 50 MB
Allowed MIME types: image/jpeg, image/png, image/gif, image/webp, image/svg+xml
```

#### Bucket 2: krai-error-images

```
Name: krai-error-images
Public bucket: ☐ (NICHT öffentlich)
File size limit: 50 MB
Allowed MIME types: image/jpeg, image/png, image/gif, image/webp, image/svg+xml
```

#### Bucket 3: krai-parts-images

```
Name: krai-parts-images
Public bucket: ☐ (NICHT öffentlich)
File size limit: 50 MB
Allowed MIME types: image/jpeg, image/png, image/gif, image/webp, image/svg+xml
```

3. Klicke auf **"Create bucket"**

### Schritt 3: Storage Policies konfigurieren

Für **jeden Bucket** → **Policies** Tab:

#### Policy 1: Service Role Access (ALLE Buckets)

```
Policy Name: service_role_all_access
Allowed operation: ALL
Target roles: service_role
Using expression: true
```

#### Policy 2: Authenticated Read (ALLE Buckets)

```
Policy Name: authenticated_read_krai
Allowed operation: SELECT
Target roles: authenticated
Using expression: bucket_id LIKE 'krai-%'
```

#### Policy 3: Technician Upload (nur krai-error-images)

```
Policy Name: technician_upload_errors
Allowed operation: INSERT
Target roles: authenticated
Using expression: bucket_id = 'krai-error-images'
```

---

## 📋 Methode 2: Supabase Management API

### Voraussetzungen

- **Management API Token** von Supabase
- **Project Reference ID** (zu finden im Dashboard unter Settings → General)

### Bucket erstellen via cURL

```bash
# Set your credentials
PROJECT_REF="your-project-ref"
MANAGEMENT_TOKEN="your-management-api-token"

# Create krai-document-images bucket
curl -X POST "https://api.supabase.com/v1/projects/${PROJECT_REF}/storage/buckets" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "krai-document-images",
    "public": false,
    "file_size_limit": 52428800,
    "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
  }'

# Create krai-error-images bucket
curl -X POST "https://api.supabase.com/v1/projects/${PROJECT_REF}/storage/buckets" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "krai-error-images",
    "public": false,
    "file_size_limit": 52428800,
    "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
  }'

# Create krai-parts-images bucket
curl -X POST "https://api.supabase.com/v1/projects/${PROJECT_REF}/storage/buckets" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "krai-parts-images",
    "public": false,
    "file_size_limit": 52428800,
    "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
  }'
```

---

## 📋 Methode 3: Python Script

```python
import requests
import os

# Configuration
PROJECT_REF = os.getenv('SUPABASE_PROJECT_REF')
MANAGEMENT_TOKEN = os.getenv('SUPABASE_MANAGEMENT_TOKEN')
API_URL = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/storage/buckets"

headers = {
    'Authorization': f'Bearer {MANAGEMENT_TOKEN}',
    'Content-Type': 'application/json'
}

buckets = [
    {
        'name': 'krai-document-images',
        'public': False,
        'file_size_limit': 52428800,  # 50 MB
        'allowed_mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
    },
    {
        'name': 'krai-error-images',
        'public': False,
        'file_size_limit': 52428800,
        'allowed_mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
    },
    {
        'name': 'krai-parts-images',
        'public': False,
        'file_size_limit': 52428800,
        'allowed_mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
    }
]

# Create buckets
for bucket in buckets:
    response = requests.post(API_URL, headers=headers, json=bucket)
    if response.status_code == 201:
        print(f"✅ Created bucket: {bucket['name']}")
    elif response.status_code == 409:
        print(f"⚠️  Bucket already exists: {bucket['name']}")
    else:
        print(f"❌ Error creating {bucket['name']}: {response.text}")
```

---

## ✅ Verifizierung

### Über Supabase Client prüfen

```python
from supabase import create_client

supabase = create_client(supabase_url, supabase_key)

# Liste alle Buckets
buckets = supabase.storage.list_buckets()
print("Available buckets:")
for bucket in buckets:
    print(f"  - {bucket.name}")

# Test Upload
with open('test_image.png', 'rb') as f:
    result = supabase.storage\
        .from_('krai-document-images')\
        .upload('test/test.png', f)
    print(f"Upload successful: {result}")

# Test Download
url = supabase.storage\
    .from_('krai-document-images')\
    .get_public_url('test/test.png')
print(f"Public URL: {url}")
```

### Über SQL prüfen

```sql
-- Prüfen ob Buckets existieren
SELECT id, name, public, file_size_limit, created_at 
FROM storage.buckets 
WHERE name LIKE 'krai-%'
ORDER BY name;

-- Erwartete Ausgabe:
-- krai-document-images | false | 52428800 | ...
-- krai-error-images    | false | 52428800 | ...
-- krai-parts-images    | false | 52428800 | ...
```

---

## 🎨 Use Cases

### krai-document-images
**Zweck:** Bilder aus Service Manuals für Agent Context

**Beispiel:**
```python
# Bild aus PDF extrahieren und hochladen
image_data = extract_image_from_pdf(page=42)
filename = f"doc_{doc_id}/page_42_diagram.png"

supabase.storage\
    .from_('krai-document-images')\
    .upload(filename, image_data)
```

### krai-error-images
**Zweck:** Defekt-Bilder von Technikern für AI/ML Training

**Beispiel:**
```python
# Techniker lädt Fehler-Bild hoch
defect_image = upload_from_mobile()
filename = f"defect_{error_code}_{timestamp}.jpg"

supabase.storage\
    .from_('krai-error-images')\
    .upload(filename, defect_image)
```

### krai-parts-images
**Zweck:** Technische Zeichnungen für Ersatzteil-Katalog

**Beispiel:**
```python
# Ersatzteil-Bild hochladen
part_image = get_technical_drawing('CF259A')
filename = f"parts/CF259A_toner_cartridge.png"

supabase.storage\
    .from_('krai-parts-images')\
    .upload(filename, part_image)
```

---

## 🔐 Sicherheitshinweise

1. **Alle Buckets sind PRIVATE** (nicht öffentlich zugänglich)
2. **Service Role Key** wird für Backend-Operationen benötigt
3. **Authenticated Users** können nur lesen (außer Error-Images)
4. **Dateigröße** ist auf 50 MB begrenzt
5. **MIME Types** sind auf Bilder beschränkt

---

## 🆘 Troubleshooting

### Problem: "Bucket already exists"
```
✅ Das ist OK! Bucket wurde bereits erstellt.
```

### Problem: "Permission denied"
```
❌ Prüfe ob du den richtigen Management API Token verwendest
❌ Prüfe ob der Token noch gültig ist
```

### Problem: "Invalid MIME type"
```
❌ Stelle sicher, dass du nur Bilder hochlädst
❌ Akzeptierte Typen: jpeg, png, gif, webp, svg
```

### Problem: "File too large"
```
❌ Dateien größer als 50 MB werden abgelehnt
❌ Komprimiere das Bild oder erhöhe das Limit im Dashboard
```

---

## 📊 Storage Monitoring

```python
# Storage Usage prüfen
def check_storage_usage():
    buckets = ['krai-document-images', 'krai-error-images', 'krai-parts-images']
    
    for bucket_name in buckets:
        files = supabase.storage.from_(bucket_name).list()
        total_size = sum(f.get('metadata', {}).get('size', 0) for f in files)
        
        print(f"{bucket_name}:")
        print(f"  Files: {len(files)}")
        print(f"  Total Size: {total_size / 1024 / 1024:.2f} MB")
```

---

## ✅ Checkliste

Nach Abschluss solltest du haben:

- [ ] 3 Storage Buckets erstellt (krai-document-images, krai-error-images, krai-parts-images)
- [ ] Alle Buckets sind NICHT öffentlich
- [ ] File Size Limit ist 50 MB
- [ ] MIME Types sind konfiguriert
- [ ] Storage Policies sind aktiv
- [ ] Test-Upload erfolgreich

---

**Bei Fragen:** Siehe KRAI Development Team Lead

