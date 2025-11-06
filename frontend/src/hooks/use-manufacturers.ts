import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import manufacturersApi from '@/lib/api/manufacturers'
import type {
  DocumentListResponse,
  ManufacturerCreateInput,
  ManufacturerFilters,
  ManufacturerListResponse,
  ManufacturerStats,
  ManufacturerUpdateInput,
  ManufacturerWithStats,
  ProductListResponse,
  ProductSeries,
} from '@/types/api'

type UseManufacturersParams = {
  page?: number
  page_size?: number
  filters?: ManufacturerFilters
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type UpdateManufacturerVariables = {
  id: string
  data: ManufacturerUpdateInput
}

type RelatedQueryParams = UseManufacturersParams

export const useManufacturers = (params: UseManufacturersParams = {}) =>
  useQuery<ManufacturerListResponse, Error>({
    queryKey: ['manufacturers', params],
    queryFn: async () => {
      const response = await manufacturersApi.getManufacturers(params)
      return response.data
    },
    placeholderData: keepPreviousData,
  })

export const useManufacturer = (id?: string, include_stats = false) =>
  useQuery<ManufacturerWithStats, Error>({
    queryKey: ['manufacturers', id, { include_stats }],
    queryFn: async () => {
      if (!id) throw new Error('Manufacturer ID is required')
      const response = await manufacturersApi.getManufacturer(id, include_stats)
      return response.data
    },
    enabled: Boolean(id),
  })

export const useManufacturerStats = () =>
  useQuery<ManufacturerStats, Error>({
    queryKey: ['manufacturers', 'stats'],
    queryFn: async () => {
      const response = await manufacturersApi.getManufacturerStats()
      return response.data
    },
    staleTime: 60_000,
  })

export const useCreateManufacturer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ManufacturerCreateInput) => manufacturersApi.createManufacturer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manufacturers'] })
    },
  })
}

export const useUpdateManufacturer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: UpdateManufacturerVariables) =>
      manufacturersApi.updateManufacturer(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['manufacturers'] })
      queryClient.invalidateQueries({ queryKey: ['manufacturers', variables.id] })
    },
  })
}

export const useDeleteManufacturer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => manufacturersApi.deleteManufacturer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manufacturers'] })
    },
  })
}

export const useManufacturerProducts = (manufacturer_id?: string, params: RelatedQueryParams = {}) =>
  useQuery<ProductListResponse, Error>({
    queryKey: ['manufacturers', manufacturer_id, 'products', params],
    queryFn: async () => {
      if (!manufacturer_id) throw new Error('Manufacturer ID is required')
      const response = await manufacturersApi.getManufacturerProducts(manufacturer_id, params)
      return response.data
    },
    enabled: Boolean(manufacturer_id),
    placeholderData: keepPreviousData,
  })

export const useManufacturerDocuments = (
  manufacturer_id?: string,
  params: RelatedQueryParams = {}
) =>
  useQuery<DocumentListResponse, Error>({
    queryKey: ['manufacturers', manufacturer_id, 'documents', params],
    queryFn: async () => {
      if (!manufacturer_id) throw new Error('Manufacturer ID is required')
      const response = await manufacturersApi.getManufacturerDocuments(manufacturer_id, params)
      return response.data
    },
    enabled: Boolean(manufacturer_id),
    placeholderData: keepPreviousData,
  })

export const useManufacturerSeries = (manufacturer_id?: string) =>
  useQuery<ProductSeries[], Error>({
    queryKey: ['manufacturers', manufacturer_id, 'series'],
    queryFn: async () => {
      if (!manufacturer_id) throw new Error('Manufacturer ID is required')
      const response = await manufacturersApi.getManufacturerSeries(manufacturer_id)
      return response.data
    },
    enabled: Boolean(manufacturer_id),
    placeholderData: keepPreviousData,
  })
