import { useCallback, useState } from 'react'
import { Upload, FileText, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void
  accept?: string
  maxFiles?: number
  maxSizeMB?: number
  disabled?: boolean
  className?: string
}

export function FileUploadZone({
  onFilesSelected,
  accept = '.pdf,.pdfz',
  maxFiles = 10,
  maxSizeMB = 500,
  disabled = false,
  className,
}: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFiles = useCallback((files: File[]): File[] => {
    setError(null)

    if (files.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`)
      return []
    }

    const validFiles: File[] = []
    const maxSizeBytes = maxSizeMB * 1024 * 1024

    for (const file of files) {
      // Check file size
      if (file.size > maxSizeBytes) {
        setError(`File "${file.name}" exceeds ${maxSizeMB}MB limit`)
        continue
      }

      // Check file extension
      const extension = `.${file.name.split('.').pop()?.toLowerCase()}` 
      const acceptedExtensions = accept.split(',').map((ext) => ext.trim())
      if (!acceptedExtensions.includes(extension)) {
        setError(`File "${file.name}" has invalid type. Allowed: ${accept}`)
        continue
      }

      validFiles.push(file)
    }

    return validFiles
  }, [accept, maxFiles, maxSizeMB])

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    const validFiles = validateFiles(files)
    if (validFiles.length > 0) {
      onFilesSelected(validFiles)
    }
  }, [disabled, validateFiles, onFilesSelected])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return

    const files = Array.from(e.target.files || [])
    const validFiles = validateFiles(files)
    if (validFiles.length > 0) {
      onFilesSelected(validFiles)
    }
    // Reset input
    e.target.value = ''
  }, [disabled, validateFiles, onFilesSelected])

  return (
    <div className={cn('space-y-4', className)}>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors',
          isDragging && !disabled && 'border-primary bg-primary/5',
          !isDragging && !disabled && 'border-border hover:border-primary/50',
          disabled && 'cursor-not-allowed opacity-50'
        )}
      >
        <input
          type="file"
          multiple
          accept={accept}
          onChange={handleFileInput}
          disabled={disabled}
          className="absolute inset-0 cursor-pointer opacity-0"
          data-testid="file-input"
        />
        <Upload className={cn('h-12 w-12 mb-4', isDragging ? 'text-primary' : 'text-muted-foreground')} />
        <p className="text-lg font-medium mb-2">
          {isDragging ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="text-sm text-muted-foreground mb-4">or click to browse</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileText className="h-4 w-4" />
          <span>Supported: {accept} • Max {maxSizeMB}MB per file • Up to {maxFiles} files</span>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
