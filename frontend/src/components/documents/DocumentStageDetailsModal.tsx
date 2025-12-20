import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { RefreshCw } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { DocumentStageDetail } from '@/types/api'
import { useDocumentStages, useRetryDocumentStage } from '@/hooks/use-document-stages'
import { useToast } from '@/hooks/use-toast'

interface DocumentStageDetailsModalProps {
  documentId: string
  stageName: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DocumentStageDetailsModal({
  documentId,
  stageName,
  open,
  onOpenChange,
}: DocumentStageDetailsModalProps) {
  const { data: stageStatus, isLoading } = useDocumentStages(documentId)
  const retryStage = useRetryDocumentStage()
  const { success, error: toastError } = useToast()

  const handleRetry = async () => {
    try {
      await retryStage.mutateAsync({ documentId, stageName })
      success('Stage retry triggered', { description: `${stageName} will be reprocessed.` })
      onOpenChange(false)
    } catch (error) {
      toastError('Retry failed', { 
        description: error instanceof Error ? error.message : 'Unknown error' 
      })
    }
  }

  const stageDetail = stageStatus?.stages[stageName] || null

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl">
          <div className="flex items-center justify-center p-8">
            <div className="text-sm text-muted-foreground">Loading stage details...</div>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!stageDetail) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Stage: {stageName}
            <Badge variant={stageDetail.status === 'completed' ? 'default' : stageDetail.status === 'failed' ? 'destructive' : 'secondary'}>
              {stageDetail.status}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Timing Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Started</p>
              <p className="font-medium">
                {stageDetail.started_at ? formatDistanceToNow(new Date(stageDetail.started_at), { addSuffix: true }) : 'Not started'}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="font-medium">
                {stageDetail.completed_at ? formatDistanceToNow(new Date(stageDetail.completed_at), { addSuffix: true }) : 'In progress'}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Duration</p>
              <p className="font-medium">
                {stageDetail.duration_seconds ? `${stageDetail.duration_seconds.toFixed(2)}s` : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Progress</p>
              <p className="font-medium">{stageDetail.progress}%</p>
            </div>
          </div>

          {/* Error Display */}
          {stageDetail.error && (
            <Alert variant="destructive">
              <AlertDescription>{stageDetail.error}</AlertDescription>
            </Alert>
          )}

          {/* Metadata */}
          {Object.keys(stageDetail.metadata).length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Metadata</p>
              <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40">
                {JSON.stringify(stageDetail.metadata, null, 2)}
              </pre>
            </div>
          )}

          {/* Retry Button */}
          {stageDetail.status === 'failed' && (
            <Button onClick={handleRetry} disabled={retryStage.isPending} className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry Stage
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
