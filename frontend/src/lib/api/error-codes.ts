import { isAxiosError } from 'axios'
import apiClient from '@/lib/api-client'
import type {
  ApiError,
  ApiResponse,
  ErrorCode,
  ErrorCodeCreateInput,
  ErrorCodeFilters,
  ErrorCodeListResponse,
  ErrorCodeSearchRequest,
  ErrorCodeSearchResponse,
  ErrorCodeUpdateInput,
  ErrorCodeWithRelations,
  PaginationParams,
  SortOrder,
} from '@/types/api'

type ErrorCodeQueryParams = PaginationParams & {
  filters?: ErrorCodeFilters
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

const mergeQueryParams = (params?: ErrorCodeQueryParams): Record<string, unknown> | undefined => {
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

const errorCodesApi = {
  async getErrorCodes(params?: ErrorCodeQueryParams): Promise<ApiResponse<ErrorCodeListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<ErrorCodeListResponse>>(
        `/api/v1/error_codes${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getErrorCode(
    id: string,
    include_relations?: boolean
  ): Promise<ApiResponse<ErrorCodeWithRelations>> {
    try {
      const queryString = buildQueryString({ include_relations })
      const response = await apiClient.get<ApiResponse<ErrorCodeWithRelations>>(
        `/api/v1/error_codes/${id}${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async createErrorCode(data: ErrorCodeCreateInput): Promise<ApiResponse<ErrorCode>> {
    try {
      const response = await apiClient.post<ApiResponse<ErrorCode>>('/api/v1/error_codes', data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async updateErrorCode(
    id: string,
    data: ErrorCodeUpdateInput
  ): Promise<ApiResponse<ErrorCode>> {
    try {
      const response = await apiClient.put<ApiResponse<ErrorCode>>(`/api/v1/error_codes/${id}`, data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async deleteErrorCode(id: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.delete<ApiResponse<{ message: string }>>(
        `/api/v1/error_codes/${id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async searchErrorCodes(
    request: ErrorCodeSearchRequest
  ): Promise<ApiResponse<ErrorCodeSearchResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<ErrorCodeSearchResponse>>(
        '/api/v1/error_codes/search',
        request
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getErrorCodesByDocument(
    document_id: string,
    params?: ErrorCodeQueryParams
  ): Promise<ApiResponse<ErrorCodeListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<ErrorCodeListResponse>>(
        `/api/v1/error_codes/by-document/${document_id}${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getErrorCodesByManufacturer(
    manufacturer_id: string,
    params?: ErrorCodeQueryParams
  ): Promise<ApiResponse<ErrorCodeListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<ErrorCodeListResponse>>(
        `/api/v1/error_codes/by-manufacturer/${manufacturer_id}${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },
}

export default errorCodesApi
