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

// Resolve base URL. If the configured base starts with '/', leverage Vite proxy by
// leaving axios baseURL empty so request paths (e.g. '/api/v1/...') are sent verbatim.
const envBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const resolvedBaseUrl = envBaseUrl.startsWith('/') ? '' : envBaseUrl

// Create axios instance
const apiClient = axios.create({
  baseURL: resolvedBaseUrl,
  timeout: import.meta.env.VITE_API_TIMEOUT ? parseInt(import.meta.env.VITE_API_TIMEOUT) : 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

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
