import { createContext, useContext, useEffect, useRef, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth-store'
import { getAccessToken } from '@/lib/api-client'
import authApi, { type User, type LoginRequest, type RegisterRequest } from '@/lib/api/auth'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const authStore = useAuthStore()

  // Load user from database if token exists
  const { data: currentUserData, isLoading: isUserLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: () => authApi.getCurrentUser(),
    enabled: !!getAccessToken(),
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Update store when user data is loaded
  useEffect(() => {
    const isMounted = useRef(true)
    
    if (currentUserData?.data?.user && isMounted.current) {
      authStore.setUser(currentUserData.data.user)
    }
    
    return () => {
      isMounted.current = false
    }
  }, [currentUserData, authStore])

  // Handle query error (401 means token is invalid)
  useEffect(() => {
    if (isUserLoading === false && !currentUserData && getAccessToken()) {
      authStore.clearAuth()
    }
  }, [isUserLoading, currentUserData, authStore])

  const login = async (credentials: LoginRequest) => {
    try {
      await authStore.login(credentials)
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
      navigate('/')
    } catch (error) {
      throw error
    }
  }

  const register = async (data: RegisterRequest) => {
    try {
      await authStore.register(data)
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
      navigate('/')
    } catch (error) {
      throw error
    }
  }

  const logout = async () => {
    try {
      await authStore.logout()
      queryClient.clear()
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
      authStore.clearAuth()
      queryClient.clear()
      navigate('/login')
    }
  }

  const value: AuthContextType = {
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    isLoading: isUserLoading || authStore.isLoading,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
