import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import errorCodesApi from '@/lib/api/error-codes'
import type {
  ApiResponse,
  ErrorCodeCreateInput,
  ErrorCodeFilters,
  ErrorCodeListResponse,
  ErrorCodeSearchRequest,
  ErrorCodeSearchResponse,
  ErrorCodeUpdateInput,
  ErrorCodeWithRelations,
} from '@/types/api'

type UseErrorCodesParams = {
  page?: number
  page_size?: number
  filters?: ErrorCodeFilters
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type UpdateErrorCodeVariables = {
  id: string
  data: ErrorCodeUpdateInput
}

type RelatedQueryParams = UseErrorCodesParams

type SearchVariables = ErrorCodeSearchRequest

export const useErrorCodes = (params: UseErrorCodesParams = {}) =>
  useQuery<ErrorCodeListResponse, Error>({
    queryKey: ['error_codes', params],
    queryFn: async () => {
      const response = await errorCodesApi.getErrorCodes(params)
      return response.data
    },
    placeholderData: keepPreviousData,
  })

export const useErrorCode = (id?: string, include_relations = false) =>
  useQuery<ErrorCodeWithRelations, Error>({
    queryKey: ['error_codes', id, { include_relations }],
    queryFn: async () => {
      if (!id) throw new Error('Error code ID is required')
      const response = await errorCodesApi.getErrorCode(id, include_relations)
      return response.data
    },
    enabled: Boolean(id),
  })

export const useCreateErrorCode = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ErrorCodeCreateInput) => errorCodesApi.createErrorCode(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['error_codes'] })
    },
  })
}

export const useUpdateErrorCode = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: UpdateErrorCodeVariables) => errorCodesApi.updateErrorCode(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['error_codes'] })
      queryClient.invalidateQueries({ queryKey: ['error_codes', variables.id] })
    },
  })
}

export const useDeleteErrorCode = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => errorCodesApi.deleteErrorCode(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['error_codes'] })
    },
  })
}

export const useErrorCodeSearch = () =>
  useMutation<ApiResponse<ErrorCodeSearchResponse>, Error, SearchVariables>({
    mutationFn: (request) => errorCodesApi.searchErrorCodes(request),
  })

export const useErrorCodesByDocument = (
  document_id?: string,
  params: RelatedQueryParams = {}
) =>
  useQuery<ErrorCodeListResponse, Error>({
    queryKey: ['error_codes', 'by-document', document_id, params],
    queryFn: async () => {
      if (!document_id) throw new Error('Document ID is required')
      const response = await errorCodesApi.getErrorCodesByDocument(document_id, params)
      return response.data
    },
    enabled: Boolean(document_id),
    placeholderData: keepPreviousData,
  })

export const useErrorCodesByManufacturer = (
  manufacturer_id?: string,
  params: RelatedQueryParams = {}
) =>
  useQuery<ErrorCodeListResponse, Error>({
    queryKey: ['error_codes', 'by-manufacturer', manufacturer_id, params],
    queryFn: async () => {
      if (!manufacturer_id) throw new Error('Manufacturer ID is required')
      const response = await errorCodesApi.getErrorCodesByManufacturer(manufacturer_id, params)
      return response.data
    },
    enabled: Boolean(manufacturer_id),
    placeholderData: keepPreviousData,
  })
