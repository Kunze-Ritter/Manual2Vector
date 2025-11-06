import apiClient from '@/lib/api-client'
import { mockAuthApi } from './auth-mock'

// Use mock API if VITE_USE_MOCK_AUTH is true
const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH === 'true'

// Types
export type UserRole = 'admin' | 'editor' | 'viewer' | 'api_user'
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending'

export interface User {
  id: string
  email: string
  username: string
  first_name?: string
  last_name?: string
  role: UserRole
  status: UserStatus
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

export interface LoginResponse {
  success: boolean
  message: string
  data: {
    access_token: string
    refresh_token?: string
    token_type: string
    expires_in: number
    user: User
  }
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  confirm_password: string
  first_name?: string
  last_name?: string
}

export interface RegisterResponse {
  success: boolean
  message: string
  data: {
    access_token: string
    refresh_token?: string
    token_type: string
    expires_in: number
    user: User
  }
}

export interface GetCurrentUserResponse {
  success: boolean
  data: {
    user: User
  }
}

// API functions
const realAuthApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', data)
    return response.data
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', data)
    return response.data
  },

  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  },

  async getCurrentUser(): Promise<GetCurrentUserResponse> {
    const response = await apiClient.get<GetCurrentUserResponse>('/api/v1/auth/me')
    return response.data
  },
}

// Export either mock or real API based on environment
export const authApi = USE_MOCK_AUTH ? mockAuthApi : realAuthApi

export default authApi
