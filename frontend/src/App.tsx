import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy } from 'react'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Lazy load devtools for development only
const ReactQueryDevtools = lazy(() =>
  import('@tanstack/react-query-devtools').then((module) => ({
    default: module.ReactQueryDevtools,
  }))
)
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { HomePage } from '@/pages/HomePage'
import DocumentsPage from '@/pages/DocumentsPage'
import ProductsPage from '@/pages/ProductsPage'
import ManufacturersPage from '@/pages/ManufacturersPage'
import ErrorCodesPage from '@/pages/ErrorCodesPage'
import VideosPage from '@/pages/VideosPage'
import MonitoringPage from '@/pages/MonitoringPage'

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/unauthorized"
              element={
                <div className="flex items-center justify-center min-h-screen bg-background">
                  <div className="text-center">
                    <h1 className="text-4xl font-bold text-destructive mb-4">403</h1>
                    <h2 className="text-2xl font-semibold mb-2">Unauthorized</h2>
                    <p className="text-muted-foreground mb-6">You do not have permission to access this resource.</p>
                    <Navigate to="/login" replace />
                  </div>
                </div>
              }
            />

            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <DocumentsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            {/* Dashboard */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <HomePage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            {/* Entity Routes */}
            <Route
              path="/documents"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <DocumentsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/products"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ProductsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/manufacturers"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ManufacturersPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/error-codes"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ErrorCodesPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/videos"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <VideosPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/images"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <div className="text-center py-12">
                      <h1 className="text-2xl font-bold">Images</h1>
                      <p className="text-muted-foreground mt-2">Coming Soon</p>
                    </div>
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/monitoring"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <MonitoringPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <div className="text-center py-12">
                      <h1 className="text-2xl font-bold">Settings</h1>
                      <p className="text-muted-foreground mt-2">Coming Soon</p>
                    </div>
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            {/* Catch All */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>

      <Toaster richColors closeButton />
      </ThemeProvider>

      {/* DevTools */}
      {import.meta.env.VITE_ENABLE_DEVTOOLS === 'true' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  )
}

export default App
