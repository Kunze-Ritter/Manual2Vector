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

export function Sidebar() {
  const { user, logout } = useAuth()

  const navigationItems = [
    { label: 'Home', icon: Home, href: '/' },
    { label: 'Documents', icon: FileText, href: '/documents' },
    { label: 'Products', icon: Package, href: '/products' },
    { label: 'Manufacturers', icon: Building2, href: '/manufacturers' },
    { label: 'Error Codes', icon: AlertCircle, href: '/error-codes' },
    { label: 'Videos', icon: Video, href: '/videos' },
    { label: 'Images', icon: Image, href: '/images' },
    { label: 'Monitoring', icon: Activity, href: '/monitoring' },
  ]

  const settingsItems = [{ label: 'Settings', icon: Settings, href: '/settings' }]

  const getInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    }
    return user?.username?.[0]?.toUpperCase() || 'U'
  }

  const isAdmin = user?.role === 'admin'
  const isEditor = user?.role === 'editor'
  const isViewer = user?.role === 'viewer'

  const visibleItems = navigationItems.filter((item) => {
    if (isAdmin) return true
    if (isEditor) return true
    if (isViewer) return true
    return false
  })

  const visibleSettingsItems = settingsItems.filter(() => {
    if (isAdmin) return true
    if (isEditor) return false
    if (isViewer) return false
    return false
  })

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-card border-r border-border overflow-y-auto" data-testid="sidebar">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <a href="/" className="block" data-testid="logo">
          <h1 className="text-xl font-bold text-foreground">KRAI</h1>
          <p className="text-xs text-muted-foreground mt-1">Dashboard</p>
        </a>
      </div>

      {/* User Info */}
      {user && (
        <div className="p-4 border-b border-border" data-testid="user-info">
          <div className="flex items-center gap-3">
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

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {visibleItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.href}
              to={item.href}
              data-testid={`nav-link-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
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
          <Separator className="my-2" />
          <nav className="p-4 space-y-2">
            {visibleSettingsItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  data-testid={`nav-link-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
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

      {/* Logout Button */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border bg-card">
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
