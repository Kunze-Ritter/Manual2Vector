import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Bell, Sun, Moon, User, Settings, LogOut } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { NavLink } from 'react-router-dom'

export function Header() {
  const { user, logout } = useAuth()
  const { actualTheme, setTheme } = useTheme()

  const toggleTheme = () => {
    // Toggle between light and dark (not using 'system' for now)
    setTheme(actualTheme === 'light' ? 'dark' : 'light')
  }

  const getInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    }
    return user?.username?.[0]?.toUpperCase() || 'U'
  }

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-card border-b border-border z-fixed shadow-sm">
      <div className="flex items-center justify-between h-full px-lg">
        {/* Left Section */}
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-foreground">Dashboard</h2>
        </div>

        {/* Right Section - Using spacing tokens */}
        <div className="flex items-center gap-md">
          {/* Notifications */}
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
              3
            </Badge>
          </Button>

          {/* Theme Toggle */}
          <Button variant="ghost" size="icon" onClick={toggleTheme}>
            {actualTheme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2" data-testid="user-menu">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={`https://avatar.vercel.sh/${user?.username}`} />
                  <AvatarFallback>{getInitials()}</AvatarFallback>
                </Avatar>
                <span className="hidden sm:inline text-sm">{user?.username}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-2 py-1.5">
                <p className="text-sm font-medium">{user?.first_name || user?.username}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <NavLink to="/profile" className="flex items-center gap-2 cursor-pointer" data-testid="header-profile-link">
                  <User className="h-4 w-4" />
                  <span>Profile</span>
                </NavLink>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <NavLink to="/settings" className="flex items-center gap-2 cursor-pointer" data-testid="header-settings-link">
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                </NavLink>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => logout()}
                className="flex items-center gap-2 cursor-pointer text-destructive"
                data-testid="logout-button"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
