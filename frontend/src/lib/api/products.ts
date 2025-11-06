import { isAxiosError } from 'axios'
import apiClient from '@/lib/api-client'
import type {
  ApiError,
  ApiResponse,
  PaginationParams,
  Product,
  ProductBatchResponse,
  ProductCreateInput,
  ProductFilters,
  ProductListResponse,
  ProductStats,
  ProductTypesResponse,
  ProductUpdateInput,
  ProductWithRelations,
  SortOrder,
} from '@/types/api'

type ProductQueryParams = PaginationParams & {
  filters?: ProductFilters
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

const mergeQueryParams = (params?: ProductQueryParams): Record<string, unknown> | undefined => {
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

const productsApi = {
  async getProducts(params?: ProductQueryParams): Promise<ApiResponse<ProductListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<ProductListResponse>>(
        `/api/v1/products${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getProduct(id: string, include_relations?: boolean): Promise<ApiResponse<ProductWithRelations>> {
    try {
      const queryString = buildQueryString({ include_relations })
      const response = await apiClient.get<ApiResponse<ProductWithRelations>>(
        `/api/v1/products/${id}${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async createProduct(data: ProductCreateInput): Promise<ApiResponse<Product>> {
    try {
      const response = await apiClient.post<ApiResponse<Product>>('/api/v1/products', data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async updateProduct(id: string, data: ProductUpdateInput): Promise<ApiResponse<Product>> {
    try {
      const response = await apiClient.put<ApiResponse<Product>>(`/api/v1/products/${id}`, data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async deleteProduct(id: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.delete<ApiResponse<{ message: string }>>(
        `/api/v1/products/${id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getProductStats(): Promise<ApiResponse<ProductStats>> {
    try {
      const response = await apiClient.get<ApiResponse<ProductStats>>('/api/v1/products/stats')
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async batchCreateProducts(products: ProductCreateInput[]): Promise<ApiResponse<ProductBatchResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<ProductBatchResponse>>(
        '/api/v1/products/batch/create',
        { products }
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async batchUpdateProducts(
    updates: { id: string; update_data: ProductUpdateInput }[]
  ): Promise<ApiResponse<ProductBatchResponse>> {
    try {
      const response = await apiClient.put<ApiResponse<ProductBatchResponse>>(
        '/api/v1/products/batch/update',
        { updates }
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async batchDeleteProducts(product_ids: string[]): Promise<ApiResponse<ProductBatchResponse>> {
    try {
      const response = await apiClient.delete<ApiResponse<ProductBatchResponse>>(
        '/api/v1/products/batch/delete',
        { data: { product_ids } }
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getProductTypes(): Promise<ApiResponse<ProductTypesResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<ProductTypesResponse>>('/api/v1/products/types')
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },
}

export default productsApi
