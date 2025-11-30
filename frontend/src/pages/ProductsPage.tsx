import { useCallback, useMemo, useRef, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { format } from 'date-fns'
import { Factory, MoreHorizontal, Plus, Trash2 } from 'lucide-react'

import { BatchActionsToolbar } from '@/components/shared/BatchActionsToolbar'
import { CrudModal } from '@/components/shared/CrudModal'
import { DataTable } from '@/components/shared/DataTable'
import { FilterBar, type FilterDefinition, type FilterValue } from '@/components/shared/FilterBar'
import {
  ProductForm,
  type ProductFormHandle,
  type ProductFormSubmit,
} from '@/components/forms/ProductForm'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'
import {
  useBatchDeleteProducts,
  useCreateProduct,
  useDeleteProduct,
  useProductTypes,
  useProducts,
  useUpdateProduct,
} from '@/hooks/use-products'
import {
  useManufacturers,
  useManufacturerSeries,
} from '@/hooks/use-manufacturers'
import type {
  Product,
  ProductCreateInput,
  ProductFilters,
  ProductUpdateInput,
} from '@/types/api'
import { usePermissions } from '@/lib/permissions'

const DEFAULT_PAGINATION = {
  page: 1,
  page_size: 20,
}

type TableSorting = {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type ModalState = {
  open: boolean
  mode: 'create' | 'edit'
  product?: Product | null
}

const INITIAL_MODAL_STATE: ModalState = {
  open: false,
  mode: 'create',
  product: null,
}

const getSelectedCount = (selection: Record<string, boolean>) =>
  Object.values(selection).filter(Boolean).length

const toTitleCase = (value: string) =>
  value
    .split('_')
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')

const formatDate = (value?: string | null) =>
  value ? format(new Date(value), 'PP') : '—'

const formatCurrency = (value?: number | null) =>
  value != null ? `$${value.toLocaleString()}` : '—'

const formatBoolean = (value: boolean | null | undefined) => (value ? 'Yes' : 'No')

export default function ProductsPage() {
  const [pagination, setPagination] = useState(DEFAULT_PAGINATION)
  const [sorting, setSorting] = useState<TableSorting>({ sort_by: 'created_at', sort_order: 'desc' })
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<ProductFilters>({})
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({})
  const [modalState, setModalState] = useState<ModalState>(INITIAL_MODAL_STATE)
  const formRef = useRef<ProductFormHandle | null>(null)

  const { canWrite, canDelete } = usePermissions()
  const { notify, success: toastSuccess, error: toastError } = useToast()

  const manufacturersQuery = useManufacturers({ page_size: 200 })
  const manufacturerOptions = useMemo(
    () =>
      (manufacturersQuery.data?.manufacturers ?? []).map((manufacturer) => ({
        value: manufacturer.id,
        label: manufacturer.name,
      })),
    [manufacturersQuery.data?.manufacturers],
  )

  const manufacturerLabelMap = useMemo(
    () =>
      manufacturerOptions.reduce<Record<string, string>>((acc, option) => {
        acc[option.value] = option.label
        return acc
      }, {} as Record<string, string>),
    [manufacturerOptions],
  )

  const selectedManufacturerId = filters.manufacturer_id
  const { data: seriesData } = useManufacturerSeries(selectedManufacturerId)
  const seriesOptions = useMemo(
    () =>
      (seriesData ?? []).map((series) => ({
        value: series.id,
        label: series.name,
      })),
    [seriesData],
  )

  const productTypesQuery = useProductTypes()
  const productTypeOptions = useMemo(
    () =>
      (productTypesQuery.data ?? []).map((type: string) => ({
        value: type,
        label: toTitleCase(type),
      })),
    [productTypesQuery.data],
  )

  const queryParams = useMemo(
    () => ({
      page: pagination.page,
      page_size: pagination.page_size,
      sort_by: sorting.sort_by,
      sort_order: sorting.sort_order,
      filters: {
        ...filters,
        search,
      },
    }),
    [filters, pagination.page, pagination.page_size, search, sorting.sort_by, sorting.sort_order],
  )

  const productsQuery = useProducts(queryParams)
  const createProduct = useCreateProduct()
  const updateProduct = useUpdateProduct()
  const deleteProduct = useDeleteProduct()
  const batchDeleteProducts = useBatchDeleteProducts()

  const filterDefinitions: FilterDefinition[] = useMemo(
    () => [
      {
        key: 'manufacturer_id',
        label: 'Manufacturer',
        type: 'select',
        options: manufacturerOptions,
      },
      {
        key: 'series_id',
        label: 'Series',
        type: 'select',
        options: seriesOptions,
      },
      {
        key: 'product_type',
        label: 'Product type',
        type: 'select',
        options: productTypeOptions,
      },
      {
        key: 'launch_date_from',
        label: 'Launch from',
        type: 'date',
      },
      {
        key: 'launch_date_to',
        label: 'Launch to',
        type: 'date',
      },
      {
        key: 'min_price',
        label: 'Min price',
        type: 'number',
      },
      {
        key: 'max_price',
        label: 'Max price',
        type: 'number',
      },
      {
        key: 'print_technology',
        label: 'Print technology',
        type: 'text',
        placeholder: 'Laser, Inkjet…',
      },
      {
        key: 'network_capable',
        label: 'Network capable',
        type: 'switch',
      },
    ],
    [manufacturerOptions, seriesOptions],
  )

  const isLoading = productsQuery.isLoading || productsQuery.isFetching
  const products = productsQuery.data?.products ?? []
  const paginationMeta = useMemo(
    () => ({
      page: productsQuery.data?.page ?? pagination.page,
      page_size: productsQuery.data?.page_size ?? pagination.page_size,
      total: productsQuery.data?.total ?? 0,
      total_pages: productsQuery.data?.total_pages ?? 1,
    }),
    [productsQuery.data, pagination.page, pagination.page_size],
  )

  const handlePaginationChange = useCallback((page: number, pageSize: number) => {
    setPagination({ page, page_size: pageSize })
  }, [])

  const handleSortingChange = useCallback((sort_by: string, sort_order: 'asc' | 'desc') => {
    setSorting({ sort_by: sort_by || undefined, sort_order })
  }, [])

  const handleRowSelectionChange = useCallback(({ state }: { state: Record<string, boolean> }) => {
    setRowSelection(state)
  }, [])

  const resetModal = useCallback(() => setModalState(INITIAL_MODAL_STATE), [])

  const openCreateModal = useCallback(() => {
    setModalState({ open: true, mode: 'create', product: null })
  }, [])

  const openEditModal = useCallback((product: Product) => {
    setModalState({ open: true, mode: 'edit', product })
  }, [])

  const handleDelete = useCallback(
    async (id: string) => {
      if (!canDelete('products')) return

      try {
        const response = await deleteProduct.mutateAsync(id)
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to delete product')
        }
        toastSuccess('Product deleted', { description: 'The product has been removed.' })
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Deletion failed', { description: message })
      }
    },
    [canDelete, deleteProduct, toastError, toastSuccess],
  )

  const handleBatchDelete = useCallback(async () => {
    if (!canDelete('products')) return

    const selectedIds = Object.entries(rowSelection)
      .filter(([, selected]) => selected)
      .map(([id]) => id)

    if (!selectedIds.length) return

    try {
      const response = await batchDeleteProducts.mutateAsync(selectedIds)
      if (!response.success || !response.data) {
        throw new Error(response.message ?? 'Batch delete failed')
      }

      const { successful, failed } = response.data
      notify('Batch delete completed', {
        description: `${successful} deleted, ${failed} failed.`,
      })
      setRowSelection({})
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unexpected error'
      toastError('Batch delete failed', { description: message })
    }
  }, [batchDeleteProducts, canDelete, notify, rowSelection, toastError])

  const handleFilterChange = useCallback((key: string, value: FilterValue) => {
    setPagination(DEFAULT_PAGINATION)
    setFilters((prev) => {
      const next = { ...prev }
      const isEmpty =
        value === undefined ||
        value === null ||
        (typeof value === 'string' && value.trim() === '')

      switch (key) {
        case 'manufacturer_id':
          if (isEmpty) {
            delete next.manufacturer_id
            delete next.series_id
          } else {
            next.manufacturer_id = String(value)
            delete next.series_id
          }
          break
        case 'series_id':
          if (isEmpty) {
            delete next.series_id
          } else {
            next.series_id = String(value)
          }
          break
        case 'product_type':
          if (isEmpty) {
            delete next.product_type
          } else {
            next.product_type = String(value)
          }
          break
        case 'launch_date_from':
          if (isEmpty) {
            delete next.launch_date_from
          } else {
            next.launch_date_from = String(value)
          }
          break
        case 'launch_date_to':
          if (isEmpty) {
            delete next.launch_date_to
          } else {
            next.launch_date_to = String(value)
          }
          break
        case 'min_price':
          if (typeof value === 'number') {
            next.min_price = value
          } else {
            delete next.min_price
          }
          break
        case 'max_price':
          if (typeof value === 'number') {
            next.max_price = value
          } else {
            delete next.max_price
          }
          break
        case 'print_technology':
          if (isEmpty) {
            delete next.print_technology
          } else {
            next.print_technology = String(value)
          }
          break
        case 'network_capable':
          if (typeof value === 'boolean') {
            next.network_capable = value
          } else {
            delete next.network_capable
          }
          break
        default:
          break
      }

      return next
    })
  }, [])

  const handleResetFilters = useCallback(() => {
    setPagination(DEFAULT_PAGINATION)
    setFilters({})
    setSearch('')
  }, [])

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value)
    setPagination(DEFAULT_PAGINATION)
  }, [])

  const actionColumn = useMemo<ColumnDef<Product>>(
    () => ({
      id: '_actions',
      header: '',
      enableSorting: false,
      cell: ({ row }) => {
        const product = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="action-menu-button">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Open actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canWrite('products') && <DropdownMenuItem onSelect={() => openEditModal(product)} data-testid="edit-product-menu-item">Edit</DropdownMenuItem>}
              {canDelete('products') && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onSelect={() => handleDelete(product.id)}
                  data-testid="delete-product-menu-item"
                >
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
      size: 64,
    }),
    [canDelete, canWrite, handleDelete, openEditModal],
  )

  const columns = useMemo<ColumnDef<Product>[]>(
    () => [
      {
        accessorKey: 'model_number',
        header: 'Model number',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <Factory className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium text-sm text-foreground">{row.original.model_number}</span>
          </div>
        ),
      },
      {
        accessorKey: 'model_name',
        header: 'Model name',
      },
      {
        accessorKey: 'product_type',
        header: 'Product type',
        cell: ({ row }) => <Badge variant="outline">{row.original.product_type}</Badge>,
      },
      {
        accessorKey: 'manufacturer_id',
        header: 'Manufacturer',
        cell: ({ row }) =>
          manufacturerLabelMap[row.original.manufacturer_id] ?? row.original.manufacturer_id ?? '—',
      },
      {
        accessorKey: 'series_id',
        header: 'Series',
        cell: ({ row }) => row.original.series_id ?? '—',
      },
      {
        accessorKey: 'print_technology',
        header: 'Technology',
        cell: ({ row }) => row.original.print_technology ?? '—',
      },
      {
        accessorKey: 'network_capable',
        header: 'Network',
        cell: ({ row }) => formatBoolean(row.original.network_capable),
      },
      {
        accessorKey: 'launch_date',
        header: 'Launch date',
        cell: ({ row }) => formatDate(row.original.launch_date),
      },
      {
        accessorKey: 'msrp_usd',
        header: 'MSRP',
        cell: ({ row }) => formatCurrency(row.original.msrp_usd ?? undefined),
      },
      {
        accessorKey: 'updated_at',
        header: 'Updated',
        cell: ({ row }) => format(new Date(row.original.updated_at), 'PPp'),
      },
      actionColumn,
    ],
    [actionColumn],
  )

  const selectedCount = getSelectedCount(rowSelection)
  const canCreate = canWrite('products')
  const canShowBatchToolbar = canDelete('products') && selectedCount > 0

  const modalTitle = modalState.mode === 'create' ? 'Create product' : 'Edit product'
  const modalDescription =
    modalState.mode === 'create'
      ? 'Add a new product to the catalog.'
      : 'Update metadata for the selected product.'

  const handleSubmitForm = useCallback(
    async (payload: ProductFormSubmit) => {
      try {
        if (payload.mode === 'create') {
          const response = await createProduct.mutateAsync(payload.data as ProductCreateInput)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to create product')
          }
          toastSuccess('Product created', {
            description: 'The product has been added successfully.',
          })
          resetModal()
          return
        }

        if (!modalState.product) {
          throw new Error('No product selected for update')
        }

        const response = await updateProduct.mutateAsync({
          id: modalState.product.id,
          data: payload.data as ProductUpdateInput,
        })
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to update product')
        }

        toastSuccess('Product updated', { description: 'Changes saved successfully.' })
        resetModal()
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Operation failed', { description: message })
      }
    },
    [createProduct, modalState.product, resetModal, toastError, toastSuccess, updateProduct],
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Products</h1>
            <p className="text-sm text-muted-foreground">
              Manage product definitions, pricing, and capabilities for the catalog.
            </p>
          </div>
          {canCreate && (
            <Button
              onClick={openCreateModal}
              className="self-start md:self-auto"
              data-testid="create-product-button"
            >
              <Plus className="mr-2 h-4 w-4" />
              New product
            </Button>
          )}
        </div>

        <FilterBar
          searchValue={search}
          onSearchChange={handleSearchChange}
          filters={filterDefinitions}
          filterValues={filters as Record<string, FilterValue>}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
          isLoading={isLoading}
        />
      </div>

      {canShowBatchToolbar && (
        <BatchActionsToolbar
          selectedCount={selectedCount}
          onClearSelection={() => setRowSelection({})}
          isProcessing={batchDeleteProducts.isPending}
          actions={[
            {
              key: 'delete',
              label: 'Delete selected',
              icon: <Trash2 className="h-4 w-4" />,
              onAction: handleBatchDelete,
              destructive: true,
            },
          ]}
        />
      )}

      <DataTable<Product, unknown>
        dataTestId="products-table"
        columns={columns}
        data={products}
        isLoading={isLoading}
        pagination={{
          page: paginationMeta.page,
          page_size: paginationMeta.page_size,
          total: paginationMeta.total,
          total_pages: paginationMeta.total_pages,
        }}
        onPaginationChange={handlePaginationChange}
        sorting={{ sort_by: sorting.sort_by ?? '', sort_order: sorting.sort_order ?? 'asc' }}
        onSortingChange={handleSortingChange}
        enableRowSelection={canDelete('products')}
        rowSelection={rowSelection}
        onRowSelectionChange={handleRowSelectionChange}
        emptyMessage="No products found"
      />

      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalTitle}
        description={modalDescription}
        onCancel={resetModal}
        onSubmit={() => formRef.current?.submit()}
        disableSubmit={createProduct.isPending || updateProduct.isPending}
        isSubmitting={createProduct.isPending || updateProduct.isPending}
      >
        <ProductForm
          ref={formRef}
          mode={modalState.mode}
          initialData={modalState.product ?? undefined}
          onSubmit={handleSubmitForm}
        />
      </CrudModal>
    </div>
  )
}
