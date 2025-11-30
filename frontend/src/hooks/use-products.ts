import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import productsApi from '@/lib/api/products'
import type {
  ProductCreateInput,
  ProductFilters,
  ProductListResponse,
  ProductStats,
  ProductUpdateInput,
  ProductWithRelations,
} from '@/types/api'

type UseProductsParams = {
  page?: number
  page_size?: number
  filters?: ProductFilters
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type UpdateProductVariables = {
  id: string
  data: ProductUpdateInput
}

type BatchUpdateProductVariables = Array<{
  id: string
  update_data: ProductUpdateInput
}>

export const useProducts = (params: UseProductsParams = {}) =>
  useQuery<ProductListResponse, Error>({
    queryKey: ['products', params],
    queryFn: async () => {
      const response = await productsApi.getProducts(params)
      return response.data
    },
    placeholderData: keepPreviousData,
    // Avoid aggressive retry/refetch loops while the products API is returning 500s
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })

export const useProduct = (id?: string, include_relations = false) =>
  useQuery<ProductWithRelations, Error>({
    queryKey: ['products', id, { include_relations }],
    queryFn: async () => {
      if (!id) throw new Error('Product ID is required')
      const response = await productsApi.getProduct(id, include_relations)
      return response.data
    },
    enabled: Boolean(id),
  })

export const useProductStats = () =>
  useQuery<ProductStats, Error>({
    queryKey: ['products', 'stats'],
    queryFn: async () => {
      const response = await productsApi.getProductStats()
      return response.data
    },
    staleTime: 60_000,
  })

export const useCreateProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProductCreateInput) => productsApi.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export const useUpdateProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: UpdateProductVariables) => productsApi.updateProduct(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['products', variables.id] })
    },
  })
}

export const useDeleteProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => productsApi.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export const useBatchCreateProducts = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (products: ProductCreateInput[]) => productsApi.batchCreateProducts(products),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export const useBatchUpdateProducts = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (updates: BatchUpdateProductVariables) => productsApi.batchUpdateProducts(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export const useBatchDeleteProducts = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (product_ids: string[]) => productsApi.batchDeleteProducts(product_ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export const useProductTypes = () =>
  useQuery<string[], Error>({
    queryKey: ['products', 'types'],
    queryFn: async () => {
      const response = await productsApi.getProductTypes()
      return response.data.product_types
    },
    staleTime: 10 * 60 * 1000,
  })
