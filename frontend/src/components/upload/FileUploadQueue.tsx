import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Trash2 } from 'lucide-react'
import { FileUploadItem } from './FileUploadItem'
import type { UploadQueueItem } from '@/types/api'

/**
 * File Upload Queue Component
 * 
 * Displays the current session's upload queue with real-time status updates.
 * 
 * NOTE: This is an ephemeral, in-memory queue for the current upload session only.
 * It is not a persistent upload history. For durable document tracking, users should
 * navigate to the Documents page where all uploaded documents are listed with their
 * processing status from the database.
 */
interface FileUploadQueueProps {
  queue: UploadQueueItem[]
  onRetry: (item: UploadQueueItem) => void
  onRemove: (id: string) => void
  onClearCompleted: () => void
}

export function FileUploadQueue({
  queue,
  onRetry,
  onRemove,
  onClearCompleted,
}: FileUploadQueueProps) {
  const completedCount = queue.filter((item) => item.status === 'completed').length
  const failedCount = queue.filter((item) => item.status === 'failed').length
  const uploadingCount = queue.filter((item) => 
    item.status === 'uploading' || item.status === 'processing'
  ).length

  if (queue.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Upload Queue</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {uploadingCount > 0 && `${uploadingCount} uploading • `}
              {completedCount} completed
              {failedCount > 0 && ` • ${failedCount} failed`}
            </span>
            {completedCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearCompleted}
                className="h-8"
                data-testid="clear-completed-button"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear completed
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {queue.map((item) => (
          <FileUploadItem
            key={item.id}
            item={item}
            onRetry={() => onRetry(item)}
            onRemove={() => onRemove(item.id)}
          />
        ))}
      </CardContent>
    </Card>
  )
}
