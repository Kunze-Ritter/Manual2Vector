import { FileText, CheckCircle2, XCircle, Loader2, RotateCw, X } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import type { UploadQueueItem } from '@/types/api'

interface FileUploadItemProps {
  item: UploadQueueItem
  onRetry?: () => void
  onRemove?: () => void
}

export function FileUploadItem({ item, onRetry, onRemove }: FileUploadItemProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B` 
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB` 
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB` 
  }

  const getStatusIcon = () => {
    switch (item.status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-5 w-5 text-primary animate-spin" />
      default:
        return <FileText className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getStatusBadge = () => {
    const variants = {
      pending: 'secondary',
      uploading: 'default',
      processing: 'default',
      completed: 'default',
      failed: 'destructive',
    } as const

    const labels = {
      pending: 'Pending',
      uploading: 'Uploading',
      processing: 'Processing',
      completed: 'Completed',
      failed: 'Failed',
    }

    return (
      <Badge variant={variants[item.status]} className="text-xs">
        {labels[item.status]}
      </Badge>
    )
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="mt-1">{getStatusIcon()}</div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1">
              <p className="text-sm font-medium truncate">{item.file.name}</p>
              {getStatusBadge()}
            </div>
            
            <p className="text-xs text-muted-foreground mb-2">
              {formatFileSize(item.file.size)}
              {item.uploaded_at && ` • ${formatDistanceToNow(new Date(item.uploaded_at), { addSuffix: true })}`}
            </p>

            {(item.status === 'uploading' || item.status === 'processing') && (
              <div className="space-y-1">
                <Progress value={item.progress} className="h-2" />
                <p className="text-xs text-muted-foreground">{item.progress}%</p>
              </div>
            )}

            {item.error && (
              <p className="text-xs text-destructive mt-2">{item.error}</p>
            )}

            {item.document_id && (
              <p className="text-xs text-muted-foreground mt-2">
                Document ID: <code className="text-xs">{item.document_id}</code>
              </p>
            )}
          </div>

          <div className="flex items-center gap-1">
            {item.status === 'failed' && item.can_retry && onRetry && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onRetry}
                className="h-8 w-8"
                data-testid="retry-upload-button"
              >
                <RotateCw className="h-4 w-4" />
              </Button>
            )}
            {onRemove && (item.status === 'completed' || item.status === 'failed') && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onRemove}
                className="h-8 w-8"
                data-testid="remove-upload-button"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
