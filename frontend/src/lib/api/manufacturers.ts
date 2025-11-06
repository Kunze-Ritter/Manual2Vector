import { isAxiosError } from 'axios'
import apiClient from '@/lib/api-client'
import type {
  ApiError,
  ApiResponse,
  DocumentListResponse,
  Manufacturer,
  ManufacturerCreateInput,
  ManufacturerFilters,
  ManufacturerListResponse,
  ManufacturerStats,
  ManufacturerUpdateInput,
  ManufacturerWithStats,
  PaginationParams,
  ProductListResponse,
  ProductSeries,
  SortOrder,
} from '@/types/api'

type ManufacturerQueryParams = PaginationParams & {
  filters?: ManufacturerFilters
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

const mergeQueryParams = (params?: ManufacturerQueryParams): Record<string, unknown> | undefined => {
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

const manufacturersApi = {
  async getManufacturers(
    params?: ManufacturerQueryParams
  ): Promise<ApiResponse<ManufacturerListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<ManufacturerListResponse>>(
        `/api/v1/manufacturers${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getManufacturer(
    id: string,
    include_stats?: boolean
  ): Promise<ApiResponse<ManufacturerWithStats>> {
    try {
      const queryString = buildQueryString({ include_stats })
      const response = await apiClient.get<ApiResponse<ManufacturerWithStats>>(
        `/api/v1/manufacturers/${id}${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async createManufacturer(data: ManufacturerCreateInput): Promise<ApiResponse<Manufacturer>> {
    try {
      const response = await apiClient.post<ApiResponse<Manufacturer>>('/api/v1/manufacturers', data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async updateManufacturer(
    id: string,
    data: ManufacturerUpdateInput
  ): Promise<ApiResponse<Manufacturer>> {
    try {
      const response = await apiClient.put<ApiResponse<Manufacturer>>(`/api/v1/manufacturers/${id}`, data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async deleteManufacturer(id: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.delete<ApiResponse<{ message: string }>>(
        `/api/v1/manufacturers/${id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getManufacturerStats(): Promise<ApiResponse<ManufacturerStats>> {
    try {
      const response = await apiClient.get<ApiResponse<ManufacturerStats>>(
        '/api/v1/manufacturers/stats'
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getManufacturerProducts(
    id: string,
    params?: ManufacturerQueryParams
  ): Promise<ApiResponse<ProductListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<ProductListResponse>>(
        `/api/v1/manufacturers/${id}/products${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getManufacturerDocuments(
    id: string,
    params?: ManufacturerQueryParams
  ): Promise<ApiResponse<DocumentListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<DocumentListResponse>>(
        `/api/v1/manufacturers/${id}/documents${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getManufacturerSeries(id: string): Promise<ApiResponse<ProductSeries[]>> {
    try {
      const response = await apiClient.get<ApiResponse<ProductSeries[]>>(
        `/api/v1/products/series/by-manufacturer/${id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },
}

export default manufacturersApi
