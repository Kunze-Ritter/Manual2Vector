import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import documentsApi from '@/lib/api/documents'
import type {
  Document,
  DocumentCreateInput,
  DocumentFilters,
  DocumentListResponse,
  DocumentStats,
  DocumentUpdateInput,
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
    queryFn: async () => {
      const response = await documentsApi.getDocuments(params)
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
