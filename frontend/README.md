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

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

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

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `/api` | API base URL (use `/api` for proxy, absolute URL for production) |
| `VITE_API_TIMEOUT` | `30000` | API request timeout in milliseconds |
| `VITE_TOKEN_STORAGE_KEY` | `krai_auth_token` | LocalStorage key for access token |
| `VITE_REFRESH_TOKEN_STORAGE_KEY` | `krai_refresh_token` | LocalStorage key for refresh token |
| `VITE_ENABLE_DEVTOOLS` | `true` | Enable React Query DevTools in development |

## API Integration

The frontend communicates with the backend via Axios with automatic token refresh:

- **Base URL**: `/api` (proxied to `http://localhost:8000` in development)
- **Authentication**: Bearer token in `Authorization` header
- **Refresh**: Automatic 401 handling with token refresh
- **Timeout**: 30 seconds (configurable)

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Add tests for new features
4. Keep components small and focused
5. Use Shadcn/ui components for UI consistency

## License

MIT
