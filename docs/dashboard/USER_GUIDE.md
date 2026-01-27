# Dashboard User Guide

This guide walks you through using the KRAI Dashboard, covering navigation, role‑based access, and common workflows.

## Getting Started

1. **Login** – Open `http://localhost:9100/login` (Laravel/Filament dashboard). Use the credentials defined in your environment (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, etc.).
2. **Dashboard Home** – After login you are redirected to `/dashboard`. The home page shows quick stats for recent documents, pipeline status, and alerts.

## Navigation

- **Products** – Manage product catalog. Create, edit, delete products. Permissions required: `products:create`, `products:update`, `products:delete`.
- **Documents** – View, upload, and edit documents. Permissions: `documents:*`.
- **Monitoring** – Real‑time view of pipeline stages, queue length, hardware utilization, and alerts. WebSocket connection is established automatically.
- **Admin Settings** – Only visible to users with the `admin` role. Manage users, roles, and system configuration.

## Role‑Based Views

| Role | Visible Sections | Capabilities |
|------|------------------|--------------|
| **Admin** | All pages | Full CRUD, user management, system settings |
| **Editor** | Products, Documents, Monitoring (read‑only) | Create/edit documents and products, view monitoring |
| **Viewer** | Dashboard, Monitoring (read‑only) | Read‑only access to overview data |

## Common Workflows

### Creating a New Document

1. Navigate to **Documents**.
2. Click **"Create Document"** (button with `data-testid="create-document-button"`).
3. Fill the form fields (`title`, `content`, select product/manufacturer).
4. Click **Save**. The document appears in the list and is indexed for search.

### Handling Alerts

1. Alerts appear in the top‑right corner (`data-testid="alert-item"`).
2. Click the **Acknowledge** button (`data-testid="acknowledge-button"`).
3. The alert disappears; the backend records the acknowledgement.

### Monitoring Reconnection

- The dashboard automatically attempts reconnection with exponential back‑off if the WebSocket drops. You can manually reload the page to force a new connection.

---

*For detailed API endpoint reference see `docs/api/DASHBOARD_API.md`.*
