/**
 * Navigation utilities for role-based access control
 */

import type { LucideIcon } from 'lucide-react'

export type NavigationItem = {
  label: string
  icon: LucideIcon
  href: string
  roles: string[]
}

export type User = {
  role: string
  [key: string]: any
}

/**
 * Filters navigation items based on user role
 * 
 * @param user - Current user object with role property
 * @param navigationItems - Array of navigation items with role restrictions
 * @returns Filtered array of navigation items visible to the user
 * 
 * @example
 * ```tsx
 * const visibleItems = getVisibleNavigationItems(user, navigationItems)
 * ```
 */
export function getVisibleNavigationItems(
  user: User | null,
  navigationItems: NavigationItem[]
): NavigationItem[] {
  if (!user) {
    return []
  }

  return navigationItems.filter(item => 
    item.roles.includes(user.role)
  )
}

/**
 * Checks if a user has access to a specific route
 * 
 * @param user - Current user object with role property
 * @param requiredRoles - Array of roles that can access the route
 * @returns True if user has access, false otherwise
 * 
 * @example
 * ```tsx
 * if (!hasAccess(user, ['admin', 'editor'])) {
 *   return <Navigate to="/unauthorized" />
 * }
 * ```
 */
export function hasAccess(
  user: User | null,
  requiredRoles: string[]
): boolean {
  if (!user) {
    return false
  }

  return requiredRoles.includes(user.role)
}
