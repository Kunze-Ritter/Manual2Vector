import { useState, useCallback, useEffect } from 'react'
import { Upload } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FileUploadZone } from './FileUploadZone'
import { FileUploadQueue } from './FileUploadQueue'
import { useUploadQueue } from '@/hooks/use-documents'
import { DocumentType } from '@/types/api'
import { useToast } from '@/hooks/use-toast'
import { useWebSocket } from '@/hooks/use-websocket'
import { WebSocketEvent } from '@/types/api'

/**
 * File Upload Dialog Component
 * 
 * Provides a modal interface for uploading documents with real-time progress tracking.
 * 
 * UPLOAD HISTORY SCOPE:
 * The upload queue shown in this dialog is in-memory and per-session only.
 * It provides immediate feedback during upload but is NOT a durable history.
 * 
 * For persistent upload history and document processing status:
 * - Navigate to the Documents page (/documents)
 * - Use the document list API with status filters
 * - Processing status is tracked in the database via subsequent pipeline phases
 * 
 * This dialog is optimized for the upload experience, while long-term document
 * management and status tracking happens in the main Documents interface.
 */
interface FileUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const documentTypeOptions = Object.values(DocumentType).map((value) => ({
  value,
  label: value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' '),
}))

export function FileUploadDialog({ open, onOpenChange }: FileUploadDialogProps) {
  const [documentType, setDocumentType] = useState<DocumentType>(DocumentType.SERVICE_MANUAL)
  const { queue, addToQueue, uploadFile, retryUpload, removeFromQueue, clearCompleted } = useUploadQueue()
  const { success: toastSuccess, error: toastError } = useToast()

  // WebSocket für Echtzeit-Updates
  useWebSocket({
    enabled: open && queue.length > 0,
    onMessage: (message) => {
      if (message.type === WebSocketEvent.STAGE_COMPLETED) {
        const { document_id, stage } = message.data as { document_id: string; stage: string }
        const item = queue.find((q) => q.document_id === document_id)
        if (item && stage === 'search_indexing') {
          // Final stage completed
          toastSuccess('Processing complete', {
            description: `Document ${item.file.name} is now searchable`,
          })
        }
      } else if (message.type === WebSocketEvent.STAGE_FAILED) {
        const { document_id, stage, error } = message.data as { 
          document_id: string
          stage: string
          error: string 
        }
        const item = queue.find((q) => q.document_id === document_id)
        if (item) {
          toastError('Processing failed', {
            description: `Stage ${stage} failed: ${error}`,
          })
        }
      }
    },
  })

  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      const items = addToQueue(files, documentType)
      toastSuccess('Files added', {
        description: `${files.length} file(s) added to upload queue`,
      })

      // Start uploading immediately
      for (const item of items) {
        try {
          await uploadFile(item.id, documentType)
        } catch (error) {
          toastError('Upload failed', {
            description: error instanceof Error ? error.message : 'Unknown error',
          })
        }
      }
    },
    [addToQueue, uploadFile, documentType, toastSuccess, toastError]
  )

  // Auto-close dialog when all uploads are completed
  useEffect(() => {
    if (queue.length > 0) {
      const allCompleted = queue.every((item) => 
        item.status === 'completed' || item.status === 'failed'
      )
      if (allCompleted) {
        const successCount = queue.filter((item) => item.status === 'completed').length
        if (successCount > 0) {
          toastSuccess('Upload complete', {
            description: `${successCount} document(s) uploaded successfully`,
          })
        }
      }
    }
  }, [queue, toastSuccess])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Documents
          </DialogTitle>
          <DialogDescription>
            Upload PDF documents for processing. <strong>Currently only PDF and PDFZ formats are supported.</strong> Files will be validated, deduplicated, and processed through the pipeline.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="document-type">Document Type</Label>
            <Select
              value={documentType}
              onValueChange={(value) => setDocumentType(value as DocumentType)}
            >
              <SelectTrigger id="document-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {documentTypeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <FileUploadZone
            onFilesSelected={handleFilesSelected}
            accept=".pdf,.pdfz"
            maxFiles={10}
            maxSizeMB={500}
          />

          <FileUploadQueue
            queue={queue}
            onRetry={(item) => retryUpload(item, documentType)}
            onRemove={removeFromQueue}
            onClearCompleted={clearCompleted}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
