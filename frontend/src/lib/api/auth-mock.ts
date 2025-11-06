/**
 * Mock Authentication API for development/testing
 * Use this when backend is not available
 * 
 * To enable: Set VITE_USE_MOCK_AUTH=true in .env.local
 */

import type { LoginRequest, RegisterRequest, LoginResponse, RegisterResponse, GetCurrentUserResponse, User } from './auth'

// Mock users database
const mockUsers: Record<string, any> = {
  'admin': {
    id: 'user-001',
    email: 'admin@example.com',
    username: 'admin',
    first_name: 'Admin',
    last_name: 'User',
    role: 'admin',
    status: 'active',
    is_active: true,
    is_verified: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
}

// Mock token generator
function generateMockToken(userId: string): string {
  return `mock_token_${userId}_${Date.now()}`
}

// Mock delay to simulate network
async function mockDelay(ms: number = 500): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export const mockAuthApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    await mockDelay()
    
    const user = mockUsers[data.username]
    if (!user) {
      throw new Error('Invalid credentials')
    }
    
    return {
      success: true,
      message: 'Login successful',
      data: {
        access_token: generateMockToken(user.id),
        refresh_token: generateMockToken(`refresh_${user.id}`),
        token_type: 'bearer',
        expires_in: 3600,
        user,
      }
    }
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    await mockDelay()
    
    // Check if user exists
    if (mockUsers[data.username]) {
      throw new Error('Username already exists')
    }
    
    // Create new mock user
    const newUser: User = {
      id: `user-${Date.now()}`,
      email: data.email,
      username: data.username,
      first_name: data.first_name,
      last_name: data.last_name,
      role: 'viewer',
      status: 'active',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    
    // Store in mock database
    mockUsers[data.username] = newUser
    
    return {
      success: true,
      message: 'Registration successful',
      data: {
        access_token: generateMockToken(newUser.id),
        refresh_token: generateMockToken(`refresh_${newUser.id}`),
        token_type: 'bearer',
        expires_in: 3600,
        user: newUser,
      }
    }
  },

  async logout(): Promise<void> {
    await mockDelay(200)
  },

  async getCurrentUser(): Promise<GetCurrentUserResponse> {
    await mockDelay()
    
    // Return mock admin user
    return {
      success: true,
      data: {
        user: mockUsers['admin']
      }
    }
  },
}

export default mockAuthApi
