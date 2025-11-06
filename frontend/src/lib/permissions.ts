import { useMemo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import type { User, UserRole } from '@/lib/api/auth'

export const RESOURCES = [
  'documents',
  'products',
  'manufacturers',
  'error_codes',
  'videos',
  'images',
  'monitoring',
  'batch',
] as const

type Resource = (typeof RESOURCES)[number]

type Permission = `${Resource}:${'read' | 'write' | 'delete'}` | '*'

const buildPermissions = (actions: Array<'read' | 'write' | 'delete'>): Permission[] =>
  RESOURCES.flatMap((resource) => actions.map((action) => `${resource}:${action}` as Permission))

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: ['*'],
  editor: buildPermissions(['read', 'write']),
  viewer: buildPermissions(['read']),
  api_user: ['documents:read', 'products:read', 'error_codes:read'],
}

const hasWildcard = (permissions: Permission[]): boolean => permissions.includes('*')

export const hasPermission = (user: User | null, permission: Permission): boolean => {
  if (!user) return false
  const rolePermissions = ROLE_PERMISSIONS[user.role] ?? []
  if (hasWildcard(rolePermissions)) return true
  return rolePermissions.includes(permission)
}

export const canRead = (user: User | null, resource: Resource): boolean =>
  hasPermission(user, `${resource}:read`)

export const canWrite = (user: User | null, resource: Resource): boolean =>
  hasPermission(user, `${resource}:write`)

export const canDelete = (user: User | null, resource: Resource): boolean =>
  hasPermission(user, `${resource}:delete`)

export const isAdmin = (user: User | null): boolean => user?.role === 'admin'

export const isEditor = (user: User | null): boolean => user?.role === 'editor'

export const isViewer = (user: User | null): boolean => user?.role === 'viewer'

interface UsePermissionsResult {
  canRead: (resource: Resource) => boolean
  canWrite: (resource: Resource) => boolean
  canDelete: (resource: Resource) => boolean
  isAdmin: boolean
  isEditor: boolean
  isViewer: boolean
}

export const usePermissions = (): UsePermissionsResult => {
  const { user } = useAuth()

  return useMemo(
    () => ({
      canRead: (resource: Resource) => canRead(user, resource),
      canWrite: (resource: Resource) => canWrite(user, resource),
      canDelete: (resource: Resource) => canDelete(user, resource),
      isAdmin: isAdmin(user),
      isEditor: isEditor(user),
      isViewer: isViewer(user),
    }),
    [user],
  )
}
