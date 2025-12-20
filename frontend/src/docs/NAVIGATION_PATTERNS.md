# Navigation Patterns

This document describes the navigation patterns used throughout the KRAI Dashboard, including Sidebar and Header components.

## Table of Contents

- [Sidebar Structure](#sidebar-structure)
- [Role-Based Navigation](#role-based-navigation)
- [Active State Patterns](#active-state-patterns)
- [Icon Usage](#icon-usage)
- [Design Token Usage](#design-token-usage)
- [Header Structure](#header-structure)
- [Responsive Breakpoints](#responsive-breakpoints)

---

## Sidebar Structure

The Sidebar follows a consistent vertical layout with the following sections:

1. **Logo Area** - Brand identity at the top
2. **User Info** - Current user display with avatar
3. **Navigation Items** - Main navigation links
4. **Settings** - Configuration access
5. **Logout** - Session termination

### Layout Pattern

```tsx
<aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-background">
  {/* Logo */}
  <div className="flex h-16 items-center border-b px-md">
    <Logo />
  </div>

  {/* User Info */}
  <div className="border-b p-md">
    <UserInfo user={user} />
  </div>

  {/* Navigation */}
  <nav className="flex-1 space-y-sm p-md">
    {visibleNavigationItems.map(item => (
      <NavigationItem key={item.href} item={item} />
    ))}
  </nav>

  {/* Footer Actions */}
  <div className="border-t p-md space-y-sm">
    <SettingsLink />
    <LogoutButton />
  </div>
</aside>
```

---

## Role-Based Navigation

Navigation items are filtered based on user roles to ensure users only see authorized sections.

### Navigation Item Structure

```tsx
type NavigationItem = {
  label: string
  icon: LucideIcon
  href: string
  roles: string[]  // Allowed roles
}

const navigationItems: NavigationItem[] = [
  { 
    label: 'Dashboard', 
    icon: Home, 
    href: '/', 
    roles: ['admin', 'editor', 'viewer'] 
  },
  { 
    label: 'Documents', 
    icon: FileText, 
    href: '/documents', 
    roles: ['admin', 'editor', 'viewer'] 
  },
  { 
    label: 'Products', 
    icon: Package, 
    href: '/products', 
    roles: ['admin', 'editor'] 
  },
  { 
    label: 'Users', 
    icon: Users, 
    href: '/users', 
    roles: ['admin'] 
  },
  { 
    label: 'Settings', 
    icon: Settings, 
    href: '/settings', 
    roles: ['admin'] 
  }
]
```

### Helper Function

Use the `getVisibleNavigationItems` helper to filter navigation based on user role:

```tsx
import { getVisibleNavigationItems } from '@/lib/navigation'

// In Sidebar component
const visibleItems = getVisibleNavigationItems(user, navigationItems)
```

**Implementation:** See `frontend/src/lib/navigation.ts`

---

## Active State Patterns

Use React Router's `NavLink` component with the `isActive` callback for dynamic styling.

### Standard NavLink Pattern

```tsx
import { NavLink } from 'react-router-dom'

<NavLink
  to={item.href}
  className={({ isActive }) =>
    `flex items-center gap-sm px-sm py-sm rounded-lg text-sm font-medium transition-colors duration-base ${
      isActive 
        ? 'bg-accent text-accent-foreground' 
        : 'text-muted-foreground hover:bg-accent/50'
    }`
  }
>
  <item.icon className="h-5 w-5" />
  <span>{item.label}</span>
</NavLink>
```

### Active State Indicators

- **Background:** `bg-accent` for active items
- **Text Color:** `text-accent-foreground` for active, `text-muted-foreground` for inactive
- **Hover:** `hover:bg-accent/50` for inactive items
- **Transition:** `transition-colors duration-base` for smooth state changes

---

## Icon Usage

All navigation icons use **Lucide React** icons with consistent sizing.

### Icon Standards

- **Size:** `h-5 w-5` (20x20px)
- **Stroke Width:** Default (2px)
- **Color:** Inherits from parent text color
- **Spacing:** `gap-sm` between icon and label

### Common Navigation Icons

```tsx
import { 
  Home,           // Dashboard
  FileText,       // Documents
  Package,        // Products
  Users,          // Users
  Settings,       // Settings
  LogOut,         // Logout
  Bell,           // Notifications
  Search,         // Search
  Menu,           // Mobile menu toggle
  X               // Close/Cancel
} from 'lucide-react'
```

---

## Design Token Usage

Navigation components use design tokens from the theme system for consistent spacing and styling.

### Spacing Tokens

```tsx
// Padding
px-md      // Horizontal padding (medium)
py-sm      // Vertical padding (small)
p-md       // All-around padding (medium)

// Gaps
gap-sm     // Small gap between elements
space-y-sm // Vertical spacing between stacked elements

// Sizing
h-16       // Header height
w-64       // Sidebar width
```

### Color Tokens

```tsx
bg-background           // Main background
bg-accent              // Active state background
bg-accent/50           // Hover state (50% opacity)
text-accent-foreground // Active text
text-muted-foreground  // Inactive text
border-r               // Right border
border-b               // Bottom border
```

### Transition Tokens

```tsx
transition-colors  // Color transitions
duration-base      // Standard duration (150ms)
```

---

## Header Structure

The Header provides global actions and user context.

### Header Layout

```tsx
<header className="fixed top-0 right-0 left-64 z-30 h-16 border-b bg-background">
  <div className="flex h-full items-center justify-between px-md">
    {/* Left: Page Title */}
    <h1 className="text-xl font-semibold">{pageTitle}</h1>

    {/* Right: Actions */}
    <div className="flex items-center gap-md">
      <SearchButton />
      <NotificationDropdown />
      <ThemeToggle />
      <UserMenu />
    </div>
  </div>
</header>
```

### User Menu Pattern

```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon">
      <Avatar>
        <AvatarImage src={user.avatar_url} />
        <AvatarFallback>{user.initials}</AvatarFallback>
      </Avatar>
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end" className="w-56">
    <DropdownMenuLabel>
      <div className="flex flex-col space-y-1">
        <p className="text-sm font-medium">{user.name}</p>
        <p className="text-xs text-muted-foreground">{user.email}</p>
      </div>
    </DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem asChild>
      <Link to="/profile">
        <User className="mr-2 h-4 w-4" />
        Profile
      </Link>
    </DropdownMenuItem>
    <DropdownMenuItem asChild>
      <Link to="/settings">
        <Settings className="mr-2 h-4 w-4" />
        Settings
      </Link>
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem onClick={handleLogout}>
      <LogOut className="mr-2 h-4 w-4" />
      Logout
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Notification Badge Pattern

```tsx
<Button variant="ghost" size="icon" className="relative">
  <Bell className="h-5 w-5" />
  {unreadCount > 0 && (
    <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground">
      {unreadCount}
    </span>
  )}
</Button>
```

### Theme Toggle Integration

```tsx
import { useTheme } from '@/contexts/ThemeContext'

const ThemeToggle = () => {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
    >
      {theme === 'light' ? (
        <Moon className="h-5 w-5" />
      ) : (
        <Sun className="h-5 w-5" />
      )}
    </Button>
  )
}
```

---

## Responsive Breakpoints

Navigation adapts to different screen sizes using responsive utilities.

### Desktop (≥1024px)

```tsx
// Sidebar: Fixed left sidebar
<aside className="fixed left-0 top-0 z-40 h-screen w-64">
  {/* Sidebar content */}
</aside>

// Header: Offset by sidebar width
<header className="fixed top-0 left-64 right-0">
  {/* Header content */}
</header>

// Main: Offset by sidebar and header
<main className="ml-64 mt-16 p-md">
  {/* Page content */}
</main>
```

### Mobile (<1024px)

```tsx
// Sidebar: Slide-in overlay
<aside className={`fixed left-0 top-0 z-50 h-screen w-64 transform transition-transform ${
  isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
} lg:translate-x-0`}>
  {/* Sidebar content */}
</aside>

// Overlay: Dark backdrop when menu open
{isMobileMenuOpen && (
  <div 
    className="fixed inset-0 z-40 bg-black/50 lg:hidden"
    onClick={() => setIsMobileMenuOpen(false)}
  />
)}

// Header: Full width with menu toggle
<header className="fixed top-0 left-0 right-0 lg:left-64">
  <Button 
    variant="ghost" 
    size="icon"
    className="lg:hidden"
    onClick={() => setIsMobileMenuOpen(true)}
  >
    <Menu className="h-5 w-5" />
  </Button>
  {/* Rest of header */}
</header>

// Main: No left margin
<main className="mt-16 p-md lg:ml-64">
  {/* Page content */}
</main>
```

### Z-Index Hierarchy

```tsx
z-50  // Mobile sidebar (highest)
z-40  // Mobile overlay / Desktop sidebar
z-30  // Header
z-20  // Modals
z-10  // Dropdowns
```

---

## Best Practices

1. **Always use role-based filtering** - Never show unauthorized navigation items
2. **Consistent icon sizing** - Use `h-5 w-5` for all navigation icons
3. **Design tokens over hardcoded values** - Use theme tokens for colors and spacing
4. **Active state feedback** - Always indicate the current page clearly
5. **Keyboard navigation** - Ensure all navigation items are keyboard accessible
6. **Mobile-first responsive** - Test navigation on mobile devices
7. **Loading states** - Show skeleton or spinner during navigation transitions

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
- [Design Tokens](../config/design-tokens.ts) - Theme configuration
- [Interaction Patterns](./INTERACTION_PATTERNS.md) - Overall pattern guide
