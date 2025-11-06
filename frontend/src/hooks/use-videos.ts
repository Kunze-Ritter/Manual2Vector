import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import videosApi from '@/lib/api/videos'
import type {
  ProductListResponse,
  VideoCreateInput,
  VideoEnrichmentRequest,
  VideoFilters,
  VideoListResponse,
  VideoUpdateInput,
  VideoWithRelations,
} from '@/types/api'

type UseVideosParams = {
  page?: number
  page_size?: number
  filters?: VideoFilters
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type UpdateVideoVariables = {
  id: string
  data: VideoUpdateInput
}

type LinkVariables = {
  video_id: string
  product_ids: string[]
}

type UnlinkVariables = {
  video_id: string
  product_id: string
}

export const useVideos = (params: UseVideosParams = {}) =>
  useQuery<VideoListResponse, Error>({
    queryKey: ['videos', params],
    queryFn: async () => {
      const response = await videosApi.getVideos(params)
      return response.data
    },
    placeholderData: keepPreviousData,
  })

export const useVideo = (id?: string, include_relations = false) =>
  useQuery<VideoWithRelations, Error>({
    queryKey: ['videos', id, { include_relations }],
    queryFn: async () => {
      if (!id) throw new Error('Video ID is required')
      const response = await videosApi.getVideo(id, include_relations)
      return response.data
    },
    enabled: Boolean(id),
  })

export const useCreateVideo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: VideoCreateInput) => videosApi.createVideo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export const useUpdateVideo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: UpdateVideoVariables) => videosApi.updateVideo(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      queryClient.invalidateQueries({ queryKey: ['videos', variables.id] })
    },
  })
}

export const useDeleteVideo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => videosApi.deleteVideo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export const useEnrichVideo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: VideoEnrichmentRequest) => videosApi.enrichVideo(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export const useLinkVideoToProducts = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ video_id, product_ids }: LinkVariables) =>
      videosApi.linkVideoToProducts(video_id, product_ids),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['videos', variables.video_id] })
      queryClient.invalidateQueries({ queryKey: ['videos', variables.video_id, 'products'] })
    },
  })
}

export const useUnlinkVideoFromProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ video_id, product_id }: UnlinkVariables) =>
      videosApi.unlinkVideoFromProduct(video_id, product_id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['videos', variables.video_id] })
      queryClient.invalidateQueries({ queryKey: ['videos', 'by-product', variables.product_id] })
    },
  })
}

export const useVideoProducts = (video_id?: string) =>
  useQuery<ProductListResponse, Error>({
    queryKey: ['videos', video_id, 'products'],
    queryFn: async () => {
      if (!video_id) throw new Error('Video ID is required')
      const response = await videosApi.getVideoProducts(video_id)
      return response.data
    },
    enabled: Boolean(video_id),
    placeholderData: keepPreviousData,
  })

export const useVideosByProduct = (product_id?: string) =>
  useQuery<VideoListResponse, Error>({
    queryKey: ['videos', 'by-product', product_id],
    queryFn: async () => {
      if (!product_id) throw new Error('Product ID is required')
      const response = await videosApi.getVideosByProduct(product_id)
      return response.data
    },
    enabled: Boolean(product_id),
    placeholderData: keepPreviousData,
  })
