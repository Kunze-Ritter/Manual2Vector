import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import {
  Home,
  FileText,
  Package,
  Building2,
  AlertCircle,
  Video,
  Image,
  Activity,
  Settings,
  LogOut,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

type UserRole = 'admin' | 'editor' | 'viewer'

interface NavigationItem {
  label: string
  icon: typeof Home
  href: string
  roles?: UserRole[]
}

/**
 * Helper function to filter navigation items based on user role.
 * If an item has no roles defined, it's visible to all users.
 * If an item has roles defined, it's only visible to users with matching roles.
 */
function filterVisibleItems(items: NavigationItem[], userRole?: string): NavigationItem[] {
  return items.filter((item) => {
    // If no roles specified, item is visible to all
    if (!item.roles || item.roles.length === 0) {
      return true
    }
    // Otherwise, check if user's role is in the allowed roles
    return item.roles.includes(userRole as UserRole)
  })
}

export function Sidebar() {
  const { user, logout } = useAuth()

  const navigationItems: NavigationItem[] = [
    { label: 'Home', icon: Home, href: '/', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Documents', icon: FileText, href: '/documents', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Products', icon: Package, href: '/products', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Manufacturers', icon: Building2, href: '/manufacturers', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Error Codes', icon: AlertCircle, href: '/error-codes', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Videos', icon: Video, href: '/videos', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Images', icon: Image, href: '/images', roles: ['admin', 'editor', 'viewer'] },
    { label: 'Monitoring', icon: Activity, href: '/monitoring', roles: ['admin', 'editor', 'viewer'] },
  ]

  const settingsItems: NavigationItem[] = [
    { label: 'Settings', icon: Settings, href: '/settings', roles: ['admin'] },
  ]

  const getInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    }
    return user?.username?.[0]?.toUpperCase() || 'U'
  }

  const visibleItems = filterVisibleItems(navigationItems, user?.role)
  const visibleSettingsItems = filterVisibleItems(settingsItems, user?.role)

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-card border-r border-border overflow-y-auto z-fixed shadow-sm" data-testid="sidebar">
      {/* Header - Using spacing tokens */}
      <div className="p-lg border-b border-border">
        <a href="/" className="block" data-testid="logo">
          <h1 className="text-xl font-bold text-foreground">KRAI</h1>
          <p className="text-xs text-muted-foreground mt-1">Dashboard</p>
        </a>
      </div>

      {/* User Info - Using spacing tokens */}
      {user && (
        <div className="p-md border-b border-border" data-testid="user-info">
          <div className="flex items-center gap-sm">
            <Avatar className="h-10 w-10">
              <AvatarImage src={`https://avatar.vercel.sh/${user.username}`} />
              <AvatarFallback>{getInitials()}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {user.first_name || user.username}
              </p>
              <p className="text-xs text-muted-foreground capitalize" data-testid="user-role">{user.role}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation - Using spacing tokens */}
      <nav className="p-md space-y-sm">
        {visibleItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.href}
              to={item.href}
              data-testid={`nav-link-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-sm px-sm py-sm rounded-lg text-sm font-medium transition-colors duration-base ${
                  isActive
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Settings Section */}
      {visibleSettingsItems.length > 0 && (
        <>
          <Separator className="my-sm" />
          <nav className="p-md space-y-sm">
            {visibleSettingsItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  data-testid={`nav-link-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  className={({ isActive }) =>
                    `flex items-center gap-sm px-sm py-sm rounded-lg text-sm font-medium transition-colors duration-base ${
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
                    }`
                  }
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>
        </>
      )}

      {/* Logout Button - Using spacing tokens */}
      <div className="absolute bottom-0 left-0 right-0 p-md border-t border-border bg-card shadow-sm">
        <Button
          variant="outline"
          className="w-full justify-start gap-2"
          onClick={() => logout()}
          data-testid="logout-button"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
      </div>
    </aside>
  )
}
