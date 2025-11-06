import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { FileText, Package, Building2, AlertCircle, Video, Image, Activity, Settings } from 'lucide-react'

export function HomePage() {
  const stats = [
    { label: 'Total Documents', value: '1,250', icon: FileText, color: 'bg-blue-100 text-blue-600' },
    { label: 'Total Products', value: '342', icon: Package, color: 'bg-green-100 text-green-600' },
    { label: 'Manufacturers', value: '28', icon: Building2, color: 'bg-purple-100 text-purple-600' },
    { label: 'Processing Queue', value: '12', icon: Activity, color: 'bg-orange-100 text-orange-600' },
  ]

  const quickActions = [
    { label: 'Upload Document', icon: FileText, href: '#' },
    { label: 'Add Product', icon: Package, href: '#' },
    { label: 'View Monitoring', icon: Activity, href: '/monitoring' },
  ]

  const navigationItems = [
    { label: 'Documents', icon: FileText, href: '/documents' },
    { label: 'Products', icon: Package, href: '/products' },
    { label: 'Manufacturers', icon: Building2, href: '/manufacturers' },
    { label: 'Error Codes', icon: AlertCircle, href: '/error-codes' },
    { label: 'Videos', icon: Video, href: '/videos' },
    { label: 'Images', icon: Image, href: '/images' },
    { label: 'Monitoring', icon: Activity, href: '/monitoring' },
    { label: 'Settings', icon: Settings, href: '/settings' },
  ]

  return (
    <div className="space-y-8" data-testid="dashboard">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Welcome to KRAI Dashboard</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label} data-testid={`stat-card-${stat.label.toLowerCase().replace(/\s+/g, '-')}`}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-2xl font-bold mt-2">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Quick Actions */}
      <Card data-testid="quick-actions">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Button key={action.label} variant="outline" asChild data-testid={`quick-action-${action.label.toLowerCase().replace(/\s+/g, '-')}`}>
                  <a href={action.href} className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    {action.label}
                  </a>
                </Button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Navigation Overview */}
      <Card data-testid="navigation-overview">
        <CardHeader>
          <CardTitle>Available Sections</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <a
                  key={item.label}
                  href={item.href}
                  className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-accent hover:text-accent-foreground transition-colors"
                  data-testid={`nav-item-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-sm font-medium">{item.label}</span>
                </a>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="pt-6">
          <p className="text-sm text-foreground">
            Welcome to the KRAI Dashboard! This is your central hub for managing documents, products, and monitoring the
            system. Use the navigation menu on the left to explore different sections.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
