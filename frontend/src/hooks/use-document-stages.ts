import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import documentsApi from '@/lib/api/documents'
import type { DocumentStageStatusResponse } from '@/types/api'

export const useDocumentStages = (documentId?: string) =>
  useQuery<DocumentStageStatusResponse, Error>({
    queryKey: ['documents', documentId, 'stages'],
    queryFn: async () => {
      if (!documentId) throw new Error('Document ID is required')
      const response = await documentsApi.getDocumentStages(documentId)
      return response.data
    },
    enabled: Boolean(documentId),
    refetchInterval: 5000, // Poll every 5s for active processing
    refetchIntervalInBackground: false,
  })

export const useRetryDocumentStage = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ documentId, stageName }: { documentId: string; stageName: string }) =>
      documentsApi.retryDocumentStage(documentId, stageName),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', variables.documentId, 'stages'] })
      queryClient.invalidateQueries({ queryKey: ['documents', variables.documentId] })
    },
  })
}
