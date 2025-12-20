import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import documentsApi from '@/lib/api/documents'
import type {
  Document,
  DocumentCreateInput,
  DocumentFilters,
  DocumentListResponse,
  DocumentStats,
  DocumentType,
  DocumentUpdateInput,
  DocumentUploadInput,
  UploadQueueItem,
} from '@/types/api'

type UseDocumentsParams = {
  page?: number
  page_size?: number
  filters?: DocumentFilters
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type UpdateDocumentVariables = {
  id: string
  data: DocumentUpdateInput
}

export const useDocuments = (params: UseDocumentsParams = {}) =>
  useQuery<DocumentListResponse, Error>({
    queryKey: ['documents', params],
    queryFn: async ({ signal }) => {
      const response = await documentsApi.getDocuments(params, signal)
      return response.data
    },
    placeholderData: keepPreviousData,
  })

export const useDocument = (id?: string) =>
  useQuery<Document, Error>({
    queryKey: ['documents', id],
    queryFn: async () => {
      if (!id) throw new Error('Document ID is required')
      const response = await documentsApi.getDocument(id)
      return response.data
    },
    enabled: Boolean(id),
  })

export const useDocumentStats = () =>
  useQuery<DocumentStats, Error>({
    queryKey: ['documents', 'stats'],
    queryFn: async () => {
      const response = await documentsApi.getDocumentStats()
      return response.data
    },
    staleTime: 60_000,
  })

export const useCreateDocument = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: DocumentCreateInput) => documentsApi.createDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export const useUpdateDocument = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: UpdateDocumentVariables) =>
      documentsApi.updateDocument(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['documents', variables.id] })
    },
  })
}

export const useDeleteDocument = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => documentsApi.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export const useBatchDeleteDocuments = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (document_ids: string[]) => documentsApi.batchDeleteDocuments(document_ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const mutation = useMutation({
    mutationFn: async ({ 
      input, 
      fileId 
    }: { 
      input: DocumentUploadInput
      fileId: string 
    }) => {
      return documentsApi.uploadDocument(input, (progress) => {
        setUploadProgress((prev) => ({ ...prev, [fileId]: progress }))
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
    onSettled: (_, __, variables) => {
      // Cleanup progress after 2 seconds
      setTimeout(() => {
        setUploadProgress((prev) => {
          const { [variables.fileId]: _, ...rest } = prev
          return rest
        })
      }, 2000)
    },
  })

  return {
    ...mutation,
    uploadProgress,
  }
}

/**
 * Upload Queue Hook
 * 
 * Manages an in-memory, per-session upload queue for tracking file uploads.
 * 
 * SCOPE: This queue is ephemeral and exists only for the current browser session.
 * It is NOT persisted to the database and will be lost on page refresh.
 * 
 * For durable upload history and processing status tracking, use the document
 * list endpoints and processing status fields managed by subsequent pipeline phases.
 * 
 * The queue provides:
 * - Real-time upload progress tracking
 * - Retry logic for failed uploads (max 3 attempts)
 * - Visual feedback during upload and initial processing
 * 
 * Once a document enters the processing pipeline (status: 'processing'),
 * its long-term status should be tracked via the documents API, not this queue.
 */
export const useUploadQueue = () => {
  const [queue, setQueue] = useState<UploadQueueItem[]>([])
  const { uploadProgress, ...uploadMutation } = useUploadDocument()

  // Sync uploadProgress into queue items
  useEffect(() => {
    Object.entries(uploadProgress).forEach(([fileId, progress]) => {
      setQueue((prev) =>
        prev.map((item) =>
          item.id === fileId && item.status === 'uploading'
            ? { ...item, progress }
            : item
        )
      )
    })
  }, [uploadProgress])

  const addToQueue = useCallback((files: File[], documentType?: DocumentType) => {
    const newItems: UploadQueueItem[] = files.map((file) => ({
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      file,
      progress: 0,
      status: 'pending',
      retry_count: 0,
      can_retry: true,
    }))
    setQueue((prev) => [...prev, ...newItems])
    return newItems
  }, [])

  const removeFromQueue = useCallback((id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id))
  }, [])

  const updateQueueItem = useCallback((id: string, updates: Partial<UploadQueueItem>) => {
    setQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...updates } : item))
    )
  }, [])

  const uploadFile = useCallback(async (itemId: string, documentType?: DocumentType, onProgress?: (progress: number) => void) => {
    // Read fresh item from state to get current retry_count
    const currentItem = queue.find(item => item.id === itemId)
    if (!currentItem) {
      console.error(`Upload item ${itemId} not found in queue`)
      return
    }

    updateQueueItem(itemId, { status: 'uploading', progress: 0 })

    try {
      const result = await uploadMutation.mutateAsync({
        input: {
          file: currentItem.file,
          document_type: documentType,
          language: 'en',
        },
        fileId: itemId,
      })

      if (result.success) {
        updateQueueItem(itemId, {
          status: 'processing',
          progress: 100,
          document_id: result.data.document_id,
          uploaded_at: new Date().toISOString(),
        })
      } else {
        throw new Error(result.message || 'Upload failed')
      }
    } catch (error) {
      // Re-read item to get latest retry_count after any updates
      const latestItem = queue.find(item => item.id === itemId)
      const retryCount = latestItem?.retry_count ?? currentItem.retry_count
      
      updateQueueItem(itemId, {
        status: 'failed',
        error: error instanceof Error ? error.message : 'Upload failed',
        can_retry: retryCount < 3,
      })
    }
  }, [uploadMutation, updateQueueItem, queue])

  const retryUpload = useCallback((item: UploadQueueItem, documentType?: DocumentType) => {
    // Read fresh retry_count from state
    const currentItem = queue.find(q => q.id === item.id)
    const currentRetryCount = currentItem?.retry_count ?? item.retry_count
    
    updateQueueItem(item.id, {
      retry_count: currentRetryCount + 1,
      error: undefined,
    })
    uploadFile(item.id, documentType)
  }, [uploadFile, updateQueueItem, queue])

  const clearCompleted = useCallback(() => {
    setQueue((prev) => prev.filter((item) => item.status !== 'completed'))
  }, [])

  return {
    queue,
    addToQueue,
    removeFromQueue,
    updateQueueItem,
    uploadFile,
    retryUpload,
    clearCompleted,
    isUploading: uploadMutation.isPending,
  }
}
