import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { setTokens, clearTokens } from '@/lib/api-client'
import authApi from '@/lib/api/auth'
import type { User, LoginRequest, RegisterRequest } from '@/lib/api/auth'

interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
  clearAuth: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setUser: (user) => {
        set({
          user,
          isAuthenticated: !!user,
        })
      },

      setLoading: (loading) => {
        set({ isLoading: loading })
      },

      login: async (credentials) => {
        set({ isLoading: true })
        try {
          const response = await authApi.login(credentials)
          const authData = response?.data

          if (!response?.success || !authData?.access_token || !authData?.user) {
            throw new Error(response?.message || 'Authentication failed. Please try again.')
          }

          setTokens(authData.access_token, authData.refresh_token)
          set({
            user: authData.user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      register: async (data) => {
        set({ isLoading: true })
        try {
          const response = await authApi.register(data)
          const authData = response?.data

          if (!response?.success || !authData?.access_token || !authData?.user) {
            throw new Error(response?.message || 'Registration failed. Please try again.')
          }

          setTokens(authData.access_token, authData.refresh_token)
          set({
            user: authData.user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: async () => {
        try {
          set({ isLoading: true })
          await authApi.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          clearTokens()
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      loadUser: async () => {
        try {
          set({ isLoading: true })
          const response = await authApi.getCurrentUser()
          set({
            user: response.data.user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      clearAuth: () => {
        clearTokens()
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },
    }),
    {
      name: 'krai-auth-storage',
      partialize: (state) => ({ user: state.user }),
    }
  )
)
