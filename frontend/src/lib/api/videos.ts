import { isAxiosError } from 'axios'
import apiClient from '@/lib/api-client'
import type {
  ApiError,
  ApiResponse,
  PaginationParams,
  ProductListResponse,
  SortOrder,
  Video,
  VideoCreateInput,
  VideoEnrichmentRequest,
  VideoEnrichmentResponse,
  VideoFilters,
  VideoListResponse,
  VideoProductLinkRequest,
  VideoUpdateInput,
  VideoWithRelations,
} from '@/types/api'

type VideoQueryParams = PaginationParams & {
  filters?: VideoFilters
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

const mergeQueryParams = (params?: VideoQueryParams): Record<string, unknown> | undefined => {
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

const videosApi = {
  async getVideos(params?: VideoQueryParams): Promise<ApiResponse<VideoListResponse>> {
    try {
      const queryObject = mergeQueryParams(params)
      const queryString = buildQueryString(queryObject)
      const response = await apiClient.get<ApiResponse<VideoListResponse>>(
        `/api/v1/videos${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getVideo(id: string, include_relations?: boolean): Promise<ApiResponse<VideoWithRelations>> {
    try {
      const queryString = buildQueryString({ include_relations })
      const response = await apiClient.get<ApiResponse<VideoWithRelations>>(
        `/api/v1/videos/${id}${queryString}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async createVideo(data: VideoCreateInput): Promise<ApiResponse<Video>> {
    try {
      const response = await apiClient.post<ApiResponse<Video>>('/api/v1/videos', data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async updateVideo(id: string, data: VideoUpdateInput): Promise<ApiResponse<Video>> {
    try {
      const response = await apiClient.put<ApiResponse<Video>>(`/api/v1/videos/${id}`, data)
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async deleteVideo(id: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.delete<ApiResponse<{ message: string }>>(
        `/api/v1/videos/${id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async enrichVideo(request: VideoEnrichmentRequest): Promise<ApiResponse<VideoEnrichmentResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<VideoEnrichmentResponse>>(
        '/api/v1/videos/enrich',
        request
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async linkVideoToProducts(
    video_id: string,
    product_ids: VideoProductLinkRequest['product_ids']
  ): Promise<ApiResponse<{ success: boolean; linked_count: number }>> {
    try {
      const response = await apiClient.post<ApiResponse<{ success: boolean; linked_count: number }>>(
        `/api/v1/videos/${video_id}/link-products`,
        { product_ids }
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async unlinkVideoFromProduct(
    video_id: string,
    product_id: string
  ): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.delete<ApiResponse<{ message: string }>>(
        `/api/v1/videos/${video_id}/unlink-products/${product_id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getVideoProducts(video_id: string): Promise<ApiResponse<ProductListResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<ProductListResponse>>(
        `/api/v1/videos/${video_id}/products`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },

  async getVideosByProduct(product_id: string): Promise<ApiResponse<VideoListResponse>> {
    try {
      const response = await apiClient.get<ApiResponse<VideoListResponse>>(
        `/api/v1/videos/by-product/${product_id}`
      )
      return response.data
    } catch (error) {
      return handleRequestError(error)
    }
  },
}

export default videosApi
