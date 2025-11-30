import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Activity, Building2, FileText, Image, Package, RefreshCw, Settings, Video } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useDashboardOverview } from '@/hooks/use-dashboard'

const statusStyles: Record<string, string> = {
  completed: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  pending: 'bg-amber-50 text-amber-700 border-amber-100',
  failed: 'bg-rose-50 text-rose-700 border-rose-100',
  in_progress: 'bg-blue-50 text-blue-700 border-blue-100',
}

const navigationItems = [
  { label: 'Documents', icon: FileText, href: '/documents', description: 'Manage uploads & processing states' },
  { label: 'Products', icon: Package, href: '/products', description: 'Product catalogue & specs' },
  { label: 'Manufacturers', icon: Building2, href: '/manufacturers', description: 'Vendors & OEM partners' },
  { label: 'Error Codes', icon: AlertCircle, href: '/error-codes', description: 'Troubleshooting knowledge' },
  { label: 'Videos', icon: Video, href: '/videos', description: 'Training & service videos' },
  { label: 'Images', icon: Image, href: '/images', description: 'Media assets & diagrams' },
  { label: 'Monitoring', icon: Activity, href: '/monitoring', description: 'Pipeline health & alerts' },
  { label: 'Settings', icon: Settings, href: '/settings', description: 'Platform configuration' },
]

const quickActions = [
  { label: 'Upload Document', icon: FileText, href: '/documents?dialog=upload' },
  { label: 'Create Product', icon: Package, href: '/products?dialog=create' },
  { label: 'Create Manufacturer', icon: Building2, href: '/manufacturers?dialog=create' },
  { label: 'Open Monitoring', icon: Activity, href: '/monitoring' },
]

function formatNumber(value: number | undefined) {
  if (value === undefined || value === null) return '—'
  return Intl.NumberFormat('en-US').format(value)
}

function formatRelative(dateString: string | null | undefined) {
  if (!dateString) return '—'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return '—'

  const diffMs = Date.now() - date.getTime()
  const diffMins = Math.round(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.round(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.round(diffHours / 24)
  return `${diffDays}d ago`
}

export function HomePage() {
  const { data, isLoading, error, refetch, isFetching } = useDashboardOverview()

  const statCards = useMemo(() => {
    if (!data) {
      return []
    }

    return [
      { label: 'Total Documents', value: data.documents.total, icon: FileText, accent: 'bg-blue-50 text-blue-700' },
      { label: 'Processed (24h)', value: data.documents.processed_last_24h, icon: Activity, accent: 'bg-emerald-50 text-emerald-700' },
      { label: 'Products', value: data.products.total, icon: Package, accent: 'bg-indigo-50 text-indigo-700' },
      { label: 'Manufacturers', value: data.products.manufacturers, icon: Building2, accent: 'bg-purple-50 text-purple-700' },
    ]
  }, [data])

  const queuePercentages = useMemo(() => {
    if (!data || data.queue.total === 0) {
      return { completed: 0, pending: 0, failed: 0 }
    }
    const { by_status } = data.queue
    const total = data.queue.total
    return {
      completed: Math.round(((by_status.completed || 0) / total) * 100),
      pending: Math.round((((by_status.pending || 0) + (by_status.in_progress || 0)) / total) * 100),
      failed: Math.round(((by_status.failed || 0) / total) * 100),
    }
  }, [data])

  return (
    <div className="space-y-8" data-testid="dashboard">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Production Dashboard</h1>
          <p className="text-muted-foreground mt-2">Live view of ingestion throughput, queue status, and content footprint.</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading || isFetching} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="border-destructive/20 bg-destructive/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <div>
                <p className="font-semibold">Unable to load dashboard data</p>
                <p className="text-sm opacity-80">{error.message || 'Please try again in a moment.'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading
          ? Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-32 rounded-xl" />)
          : statCards.map((stat) => {
              const Icon = stat.icon
              return (
                <Card key={stat.label} data-testid={`stat-card-${stat.label.toLowerCase().replace(/\s+/g, '-')}`}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                        <p className="text-3xl font-bold mt-2">{formatNumber(stat.value)}</p>
                      </div>
                      <div className={`p-3 rounded-xl border ${stat.accent}`}>
                        <Icon className="h-6 w-6" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2" data-testid="documents-breakdown">
          <CardHeader>
            <CardTitle>Document Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading || !data ? (
              <Skeleton className="h-40 rounded-lg" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Processing Status</p>
                  <div className="space-y-3">
                    {Object.entries(data.documents.by_status).map(([status, value]) => (
                      <div key={status} className="flex items-center justify-between">
                        <span className="capitalize text-sm">{status.replace('_', ' ')}</span>
                        <Badge className={`border ${statusStyles[status] || 'bg-muted text-foreground'}`}>
                          {formatNumber(value)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Document Types</p>
                  <div className="space-y-3">
                    {Object.entries(data.documents.by_type).map(([type, value]) => (
                      <div key={type} className="flex items-center justify-between">
                        <span className="capitalize text-sm">{type.replace('_', ' ')}</span>
                        <Badge variant="secondary">{formatNumber(value)}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Media Footprint</p>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Images</span>
                      <span className="font-semibold">{formatNumber(data.media.images)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Videos</span>
                      <span className="font-semibold">{formatNumber(data.media.videos)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Products Active</span>
                      <span className="font-semibold">{formatNumber(data.products.active)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Products EoL</span>
                      <span className="font-semibold">{formatNumber(data.products.discontinued)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card data-testid="queue-overview">
          <CardHeader>
            <CardTitle>Processing Queue</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading || !data ? (
              <Skeleton className="h-32 rounded-lg" />
            ) : (
              <div className="space-y-4">
                <div className="flex items-baseline justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Items</p>
                    <p className="text-2xl font-semibold mt-1">{formatNumber(data.queue.total)}</p>
                  </div>
                  <Badge variant="outline" className="text-xs uppercase tracking-wide">
                    {queuePercentages.completed}% done
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Completed</span>
                      <span>{queuePercentages.completed}%</span>
                    </div>
                    <Progress value={queuePercentages.completed} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Pending / In Progress</span>
                      <span>{queuePercentages.pending}%</span>
                    </div>
                    <Progress value={queuePercentages.pending} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Failed</span>
                      <span>{queuePercentages.failed}%</span>
                    </div>
                    <Progress value={queuePercentages.failed} className="h-2" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Revisit Monitoring &gt; Queue for detailed retry reasons and task-level visibility.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2" data-testid="recent-documents">
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading || !data ? (
              <Skeleton className="h-48 rounded-lg" />
            ) : data.documents.recent.length === 0 ? (
              <p className="text-sm text-muted-foreground">No documents processed yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Filename</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Manufacturer</TableHead>
                    <TableHead className="text-right">Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.documents.recent.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">{doc.filename || '—'}</TableCell>
                      <TableCell>
                        <Badge className={`border ${statusStyles[doc.status || ''] || 'bg-muted text-foreground'}`}>
                          {doc.status?.replace('_', ' ') || 'unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell>{doc.manufacturer || '—'}</TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {formatRelative(doc.updated_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card data-testid="quick-actions">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2">
                {quickActions.map((action) => {
                  const Icon = action.icon
                  return (
                    <Button
                      key={action.label}
                      variant="secondary"
                      asChild
                      data-testid={`quick-action-${action.label.toLowerCase().replace(/\s+/g, '-')}`}
                      className="justify-start gap-3"
                    >
                      <Link to={action.href}>
                        <Icon className="h-4 w-4" />
                        {action.label}
                      </Link>
                    </Button>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          <Card data-testid="navigation-overview">
            <CardHeader>
              <CardTitle>Explore Modules</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {navigationItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.label}
                    to={item.href}
                    className="flex items-start gap-3 rounded-lg border border-border p-3 transition hover:bg-accent"
                    data-testid={`nav-item-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <div className="mt-1">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium leading-none">{item.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
                    </div>
                  </Link>
                )
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
