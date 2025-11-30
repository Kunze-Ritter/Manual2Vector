import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Token storage keys
const ACCESS_TOKEN_KEY = import.meta.env.VITE_TOKEN_STORAGE_KEY || 'krai_auth_token'
const REFRESH_TOKEN_KEY = import.meta.env.VITE_REFRESH_TOKEN_STORAGE_KEY || 'krai_refresh_token'

// Token storage utilities
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken?: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// Resolve base URL with preference order:
// 1. Explicit VITE_API_BASE_URL
// 2. krai-engine service hostname (in Docker networks)
// 3. localhost fallback for direct host access
const FALLBACK_HOSTS = ['http://krai-engine:8000', 'http://localhost:8000'] as const
const envBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
const allowHostFallback = !envBaseUrl

let currentBaseUrl = envBaseUrl || FALLBACK_HOSTS[0]

const normalizeBaseUrl = (value: string) => (value.startsWith('/') ? '' : value)

const createApiInstance = () =>
  axios.create({
    baseURL: normalizeBaseUrl(currentBaseUrl),
    timeout: import.meta.env.VITE_API_TIMEOUT ? parseInt(import.meta.env.VITE_API_TIMEOUT) : 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

const apiClient = createApiInstance()

const switchToFallbackHost = () => {
  if (!allowHostFallback || currentBaseUrl === FALLBACK_HOSTS[1]) {
    return false
  }

  currentBaseUrl = FALLBACK_HOSTS[1]
  apiClient.defaults.baseURL = normalizeBaseUrl(currentBaseUrl)
  console.warn('[api-client] Primary host unreachable, falling back to localhost backend')
  return true
}

// Refresh token logic
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  isRefreshing = false
  failedQueue = []
}

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
      _fallbackAttempted?: boolean
    }

    const requestUrl = originalRequest?.url || ''

    // For auth login/register endpoints, let the caller handle 401 errors
    if (requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register')) {
      return Promise.reject(error)
    }

    // Handle network errors (e.g., krai-engine unreachable) by switching to localhost
    if (!error.response && error.code === 'ERR_NETWORK' && !originalRequest?._fallbackAttempted) {
      const switched = switchToFallbackHost()
      if (switched) {
        originalRequest._fallbackAttempted = true
        return apiClient(originalRequest)
      }
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return apiClient(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        // Use absolute path to avoid double "/api" when baseURL is "/api"
        // The Vite proxy will forward "/api/v1/..." to the backend
        const response = await axios.post(
          '/api/v1/auth/refresh-token',
          { refresh_token: refreshToken }
        )

        const { access_token, refresh_token } = response.data.data
        setTokens(access_token, refresh_token)

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }

        processQueue(null, access_token)
        return apiClient(originalRequest)
      } catch (err) {
        clearTokens()
        window.location.href = '/login'
        processQueue(err, null)
        return Promise.reject(err)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
