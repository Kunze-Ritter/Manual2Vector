# KRAI Dashboard Frontend

Modern React dashboard for KRAI document processing system.

Built with React 19, TypeScript, Tailwind CSS, and Shadcn/ui.

## Tech Stack

- **React** 19.1.1 - UI framework
- **TypeScript** 5.9 - Type safety
- **Vite** 7.1 - Build tool
- **Tailwind CSS** 4.1 - Styling
- **Shadcn/ui** - Component library (Radix UI + Tailwind)
- **React Router** 7.1 - Routing
- **TanStack Query** 5.62 - Server state management
- **Zustand** 5.0 - Client state management
- **Axios** 1.7 - HTTP client
- **React Hook Form** 7.54 - Form management
- **Zod** 3.24 - Schema validation

## Getting Started

### Prerequisites

- Node.js 18+
- npm/yarn/pnpm

### Installation

1. Clone the repository and navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Create a `.env.local` file from `.env.example`:

```bash
cp .env.example .env.local
```

4. Update `.env.local` with your configuration:

```env
# API Configuration
VITE_API_BASE_URL=/api
VITE_API_TIMEOUT=30000

# Authentication Storage Keys
VITE_TOKEN_STORAGE_KEY=krai_auth_token
VITE_REFRESH_TOKEN_STORAGE_KEY=krai_refresh_token

# Feature Flags
VITE_ENABLE_DEVTOOLS=true
```

## Development

### Running the Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### Building for Production

#### Production Build with Environment Variables

The production build uses `.env.production` for environment configuration:

```bash
# Build for production (uses .env.production)
npm run build:production

# Preview production build locally
npm run preview:production
```

**Important:** Environment variables are baked into the build at compile time. Changing `.env.production` requires rebuilding.

#### General Build

```bash
# Standard build (development mode)
npm run build

# Preview standard build
npm run preview
```

**Build scripts:**
- `build` - Standard build with TypeScript compilation
- `build:production` - Production build with `.env.production` (cross-platform compatible)
- `build:production:verbose` - Production build with verbose output (no bundle analysis tooling)
- `preview:production` - Preview production build on port 3000

**Note:** All build scripts use `cross-env` for cross-platform compatibility, ensuring they work correctly on both Windows and Unix-like systems.

## Production Deployment

### Docker-Based Deployment

The frontend is deployed using Docker with a multi-stage build:

**Build process:**
1. Node.js builder stage compiles the application with `.env.production`
2. Nginx production stage serves static files and proxies API requests

**Deploy commands:**
```bash
# Build frontend Docker image
docker-compose -f docker-compose.production.yml build krai-frontend

# Run full stack
docker-compose -f docker-compose.production.yml up -d
```

> **Note:** `docker-compose.production-final.yml` has been consolidated into `docker-compose.production.yml`. The new production file includes Firecrawl services and uses uvicorn instead of gunicorn.

**Key differences from development:**
- Uses nginx for serving (not Vite dev server)
- Environment variables baked into build
- API requests proxied through nginx (`/api` → `http://krai-engine:8000`)
- DevTools disabled for performance and security

**For detailed deployment information, see:**
- [Frontend Production Deployment Guide](../docs/setup/FRONTEND_PRODUCTION_DEPLOYMENT.md)
- [Main Deployment Guide](../DEPLOYMENT.md)

## Project Structure

```
src/
├── components/
│   ├── auth/              # Authentication components (ProtectedRoute, etc.)
│   ├── layout/            # Layout components (Header, Sidebar, Footer, AppLayout)
│   └── ui/                # Shadcn/ui components
├── contexts/              # React Context (AuthContext)
├── hooks/                 # Custom React hooks
├── lib/
│   ├── api/               # API client and endpoints
│   ├── api-client.ts      # Axios instance with interceptors
│   └── utils.ts           # Utility functions
├── pages/
│   ├── auth/              # Login and Register pages
│   └── HomePage.tsx       # Dashboard home page
├── stores/                # Zustand state management
├── App.tsx                # Main app component with routing
└── main.tsx               # Entry point
```

## Features

- ✅ Authentication (Login/Register)
- ✅ Protected routes with role-based access
- ✅ Responsive layout with sidebar navigation
- ✅ Light/Dark theme toggle with persistence
- ✅ Form validation with Zod + React Hook Form
- ✅ Server state management with TanStack Query
- ✅ Client state management with Zustand
- ✅ API client with automatic token refresh
- ✅ Comprehensive error handling
- ✅ Development tools (React Query DevTools)

## Environment Variables

### Configuration Files

- `.env.example` - Example configuration (template)
- `.env.local` - Local development (not committed to git)
- `.env.production` - Production configuration (committed to git)

### Available Variables

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `VITE_API_BASE_URL` | `/api` | `/api` | API base URL (proxied in both environments) |
| `VITE_API_TIMEOUT` | `30000` | `30000` | API request timeout in milliseconds |
| `VITE_TOKEN_STORAGE_KEY` | `krai_auth_token` | `krai_auth_token` | LocalStorage key for access token |
| `VITE_REFRESH_TOKEN_STORAGE_KEY` | `krai_refresh_token` | `krai_refresh_token` | LocalStorage key for refresh token |
| `VITE_ENABLE_DEVTOOLS` | `true` | `false` | Enable React Query DevTools (disable in production) |
| `VITE_USE_MOCK_AUTH` | `false` | `false` | Use mock authentication API (for testing only) |

**Note:** All variables prefixed with `VITE_` are exposed to the client and baked into the build at compile time.

## API Integration

The frontend communicates with the backend via Axios with automatic token refresh:

- **Base URL**: `/api` (proxied in both development and production)
- **Authentication**: Bearer token in `Authorization` header
- **Refresh**: Automatic 401 handling with token refresh
- **Timeout**: 30 seconds (configurable)

### Production API Configuration

In production, nginx handles API proxying:

- Frontend requests: `http://localhost:3000/api/documents`
- Nginx proxies to: `http://krai-engine:8000/documents`
- Configuration: `nginx/nginx-simple.conf`

**Benefits:**
- No CORS issues (same origin)
- Simplified frontend configuration
- Centralized request routing
- Security headers and compression

### Development API Configuration

In development, Vite dev server proxies API requests:

- Frontend requests: `http://localhost:3000/api/documents`
- Vite proxies to: `http://localhost:8000/documents`
- Configuration: `vite.config.ts`

**Alternative:** Use absolute URL (`http://localhost:8000`) for direct backend access

## Docker Deployment

### Quick Reference

```bash
# Build frontend Docker image
docker-compose -f docker-compose.production.yml build krai-frontend

# Start frontend container
docker-compose -f docker-compose.production.yml up -d krai-frontend

# View logs
docker-compose -f docker-compose.production.yml logs -f krai-frontend

# Restart container
docker-compose -f docker-compose.production.yml restart krai-frontend
```

### When to Rebuild

Rebuild the Docker image when:
- Environment variables in `.env.production` change
- Frontend source code changes
- Dependencies in `package.json` change
- Nginx configuration changes

**Important:** Environment variables are baked into the build, not read at runtime!

### References

- **Dockerfile:** `frontend/Dockerfile`
- **Docker Compose:** `docker-compose.production.yml`
- **Nginx Config:** `nginx/nginx-simple.conf`
- **Deployment Guide:** [docs/setup/FRONTEND_PRODUCTION_DEPLOYMENT.md](../docs/setup/FRONTEND_PRODUCTION_DEPLOYMENT.md)
- **Main Deployment:** [DEPLOYMENT.md](../DEPLOYMENT.md)

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Add tests for new features
4. Keep components small and focused
5. Use Shadcn/ui components for UI consistency

## License

MIT
