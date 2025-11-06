import { isAxiosError } from 'axios'
import apiClient from '@/lib/api-client'
import type {
  ApiError,
  ApiResponse,
  Document,
  DocumentBatchResponse,
  DocumentCreateInput,
  DocumentFilters,
  DocumentListResponse,
  DocumentStats,
  DocumentUpdateInput,
  PaginationParams,
  SortOrder,
} from '@/types/api'

type DocumentQueryParams = PaginationParams & {
  filters?: DocumentFilters
  sort_by?: string
  sort_order?: SortOrder | 'asc' | 'desc'
}

interface ApiClientError extends Error {
  status: number
  data?: ApiError
}

const buildQueryString = (params?: Record<string, unknown>): string => {
  if (!params) return ''

  const searchParams = new URLSearchParams()

  const appendParam = (key: string, value: unknown) => {
    if (value === undefined || value === null || value === '') return

    if (Array.isArray(value)) {
      value.forEach((item) => appendParam(key, item))
      return
    }

    const stringValue = value instanceof Date ? value.toISOString() : String(value)
    searchParams.append(key, stringValue)
  }

  Object.entries(params).forEach(([key, value]) => {
    appendParam(key, value)
  })

  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

const mergeQueryParams = (params?: DocumentQueryParams): Record<string, unknown> | undefined => {
  if (!params) return undefined

  const { filters, ...rest } = params
  const queryObject: Record<string, unknown> = { ...rest }

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      queryObject[key] = value
    })
  }

  return queryObject
}

const handleRequestError = (error: unknown): never => {
  if (isAxiosError<ApiError>(error)) {
    const status = error.response?.status ?? 500
    const data = error.response?.data
    const message = data?.detail || data?.error || error.message || 'Request failed'

    const formattedError = new Error(message) as ApiClientError
    formattedError.status = status
    if (data) {
      formattedError.data = data
    }
    throw formattedError
  }

  const fallbackError = new Error('Unexpected error') as ApiClientError
  fallbackError.status = 500
  throw fallbackError
}

const documentsApi = {
  async getDocuments(params?: DocumentQueryParams): Promise<ApiResponse<DocumentListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<DocumentListResponse>>(
        `/api/v1/documents${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getDocument(id: string): Promise<ApiResponse<Document>> {
    try {
      const response = await apiClient.get<ApiResponse<Document>>(`/api/v1/documents/${id}`)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async createDocument(data: DocumentCreateInput): Promise<ApiResponse<Document>> {
    try {
      const response = await apiClient.post<ApiResponse<Document>>('/api/v1/documents', data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async updateDocument(id: string, data: DocumentUpdateInput): Promise<ApiResponse<Document>> {
    try {
      const response = await apiClient.put<ApiResponse<Document>>(`/api/v1/documents/${id}`, data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async deleteDocument(id: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.delete<ApiResponse<{ message: string }>>(
        `/api/v1/documents/${id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async batchDeleteDocuments(document_ids: string[]): Promise<ApiResponse<DocumentBatchResponse>> {
    try {
      const response = await apiClient.delete<ApiResponse<DocumentBatchResponse>>(
        '/api/v1/documents/batch/delete',
        {
          data: { document_ids },
        },
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getDocumentStats(): Promise<ApiResponse<DocumentStats>> {
    try {
      const response = await apiClient.get<ApiResponse<DocumentStats>>('/api/v1/documents/stats')
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },
}

export default documentsApi
