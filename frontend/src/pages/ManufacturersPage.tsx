import { useCallback, useMemo, useRef, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { format } from 'date-fns'
import { Building2, MoreHorizontal, Plus, Trash2 } from 'lucide-react'

import { BatchActionsToolbar } from '@/components/shared/BatchActionsToolbar'
import { CrudModal } from '@/components/shared/CrudModal'
import { DataTable } from '@/components/shared/DataTable'
import { FilterBar, type FilterDefinition, type FilterValue } from '@/components/shared/FilterBar'
import {
  ManufacturerForm,
  type ManufacturerFormHandle,
  type ManufacturerFormSubmit,
} from '@/components/forms/ManufacturerForm'
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
  useCreateManufacturer,
  useDeleteManufacturer,
  useManufacturers,
  useUpdateManufacturer,
} from '@/hooks/use-manufacturers'
import type {
  Manufacturer,
  ManufacturerCreateInput,
  ManufacturerFilters,
  ManufacturerUpdateInput,
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
  manufacturer?: Manufacturer | null
}

const INITIAL_MODAL_STATE: ModalState = {
  open: false,
  mode: 'create',
  manufacturer: null,
}

const getSelectedCount = (selection: Record<string, boolean>) =>
  Object.values(selection).filter(Boolean).length

const formatBoolean = (value: boolean | null | undefined) => (value ? 'Yes' : 'No')

const formatCurrency = (value?: number | null) =>
  value != null ? `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '—'

const formatPercentage = (value?: number | null) =>
  value != null ? `${value.toFixed(1)}%` : '—'

export default function ManufacturersPage() {
  const [pagination, setPagination] = useState(DEFAULT_PAGINATION)
  const [sorting, setSorting] = useState<TableSorting>({ sort_by: 'created_at', sort_order: 'desc' })
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<ManufacturerFilters>({})
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({})
  const [modalState, setModalState] = useState<ModalState>(INITIAL_MODAL_STATE)
  const [isBatchDeleting, setIsBatchDeleting] = useState(false)
  const formRef = useRef<ManufacturerFormHandle | null>(null)

  const { canWrite, canDelete } = usePermissions()
  const { notify, success: toastSuccess, error: toastError } = useToast()

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

  const manufacturersQuery = useManufacturers(queryParams)
  const createManufacturer = useCreateManufacturer()
  const updateManufacturer = useUpdateManufacturer()
  const deleteManufacturer = useDeleteManufacturer()

  const filterDefinitions: FilterDefinition[] = useMemo(
    () => [
      {
        key: 'country',
        label: 'Country',
        type: 'text',
        placeholder: 'e.g. Germany',
      },
      {
        key: 'is_competitor',
        label: 'Competitor',
        type: 'switch',
      },
      {
        key: 'founded_year_from',
        label: 'Founded (from)',
        type: 'number',
      },
      {
        key: 'founded_year_to',
        label: 'Founded (to)',
        type: 'number',
      },
    ],
    [],
  )

  const isLoading = manufacturersQuery.isLoading || manufacturersQuery.isFetching
  const manufacturers = manufacturersQuery.data?.manufacturers ?? []
  const paginationMeta = useMemo(
    () => ({
      page: manufacturersQuery.data?.page ?? pagination.page,
      page_size: manufacturersQuery.data?.page_size ?? pagination.page_size,
      total: manufacturersQuery.data?.total ?? 0,
      total_pages: manufacturersQuery.data?.total_pages ?? 1,
    }),
    [manufacturersQuery.data, pagination.page, pagination.page_size],
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
    setModalState({ open: true, mode: 'create', manufacturer: null })
  }, [])

  const openEditModal = useCallback((manufacturer: Manufacturer) => {
    setModalState({ open: true, mode: 'edit', manufacturer })
  }, [])

  const handleDelete = useCallback(
    async (id: string) => {
      if (!canDelete('manufacturers')) return

      try {
        const response = await deleteManufacturer.mutateAsync(id)
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to delete manufacturer')
        }
        toastSuccess('Manufacturer deleted', { description: 'The manufacturer has been removed.' })
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Deletion failed', { description: message })
      }
    },
    [canDelete, deleteManufacturer, toastError, toastSuccess],
  )

  const handleBatchDelete = useCallback(async () => {
    if (!canDelete('manufacturers')) return

    const selectedIds = Object.entries(rowSelection)
      .filter(([, selected]) => selected)
      .map(([id]) => id)

    if (!selectedIds.length) return

    setIsBatchDeleting(true)
    let successful = 0
    let failed = 0

    try {
      for (const id of selectedIds) {
        try {
          const response = await deleteManufacturer.mutateAsync(id)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to delete manufacturer')
          }
          successful += 1
        } catch (error) {
          failed += 1
        }
      }

      notify('Batch delete completed', {
        description: `${successful} deleted${failed ? `, ${failed} failed` : ''}.`,
      })
      setRowSelection({})

      if (failed) {
        toastError('Some deletions failed', {
          description: 'Review logs for details and retry if necessary.',
        })
      }
    } finally {
      setIsBatchDeleting(false)
    }
  }, [canDelete, deleteManufacturer, notify, rowSelection, toastError])

  const handleFilterChange = useCallback((key: string, value: FilterValue) => {
    setPagination(DEFAULT_PAGINATION)
    setFilters((prev) => {
      const next = { ...prev }
      const isEmpty =
        value === undefined ||
        value === null ||
        (typeof value === 'string' && value.trim() === '')

      switch (key) {
        case 'country':
          if (isEmpty) {
            delete next.country
          } else {
            next.country = String(value)
          }
          break
        case 'is_competitor':
          if (typeof value === 'boolean') {
            next.is_competitor = value
          } else {
            delete next.is_competitor
          }
          break
        case 'founded_year_from':
          if (typeof value === 'number') {
            next.founded_year_from = value
          } else {
            delete next.founded_year_from
          }
          break
        case 'founded_year_to':
          if (typeof value === 'number') {
            next.founded_year_to = value
          } else {
            delete next.founded_year_to
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

  const actionColumn = useMemo<ColumnDef<Manufacturer>>(
    () => ({
      id: '_actions',
      header: '',
      enableSorting: false,
      cell: ({ row }) => {
        const manufacturer = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="action-menu-button">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Open actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canWrite('manufacturers') && (
                <DropdownMenuItem onSelect={() => openEditModal(manufacturer)} data-testid="edit-manufacturer-menu-item">Edit</DropdownMenuItem>
              )}
              {canDelete('manufacturers') && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onSelect={() => handleDelete(manufacturer.id)}
                  data-testid="delete-manufacturer-menu-item"
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

  const columns = useMemo<ColumnDef<Manufacturer>[]>(
    () => [
      {
        accessorKey: 'name',
        header: 'Name',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium text-sm text-foreground">{row.original.name}</span>
          </div>
        ),
      },
      {
        accessorKey: 'country',
        header: 'Country',
        cell: ({ row }) => row.original.country ?? '—',
      },
      {
        accessorKey: 'founded_year',
        header: 'Founded',
        cell: ({ row }) => row.original.founded_year ?? '—',
      },
      {
        accessorKey: 'is_competitor',
        header: 'Competitor',
        cell: ({ row }) => (
          <Badge variant={row.original.is_competitor ? 'destructive' : 'secondary'}>
            {formatBoolean(row.original.is_competitor)}
          </Badge>
        ),
      },
      {
        accessorKey: 'market_share_percent',
        header: 'Market share',
        cell: ({ row }) => formatPercentage(row.original.market_share_percent),
      },
      {
        accessorKey: 'annual_revenue_usd',
        header: 'Revenue (USD)',
        cell: ({ row }) => formatCurrency(row.original.annual_revenue_usd),
      },
      {
        accessorKey: 'employee_count',
        header: 'Employees',
        cell: ({ row }) => row.original.employee_count?.toLocaleString() ?? '—',
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
  const canCreate = canWrite('manufacturers')
  const canShowBatchToolbar = canDelete('manufacturers') && selectedCount > 0

  const modalTitle = modalState.mode === 'create' ? 'Create manufacturer' : 'Edit manufacturer'
  const modalDescription =
    modalState.mode === 'create'
      ? 'Add a new manufacturer to the catalog.'
      : 'Update details for the selected manufacturer.'

  const handleSubmitForm = useCallback(
    async (payload: ManufacturerFormSubmit) => {
      try {
        if (payload.mode === 'create') {
          const response = await createManufacturer.mutateAsync(payload.data as ManufacturerCreateInput)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to create manufacturer')
          }
          toastSuccess('Manufacturer created', {
            description: 'The manufacturer has been added successfully.',
          })
          resetModal()
          return
        }

        if (!modalState.manufacturer) {
          throw new Error('No manufacturer selected for update')
        }

        const response = await updateManufacturer.mutateAsync({
          id: modalState.manufacturer.id,
          data: payload.data as ManufacturerUpdateInput,
        })
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to update manufacturer')
        }

        toastSuccess('Manufacturer updated', { description: 'Changes saved successfully.' })
        resetModal()
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Operation failed', { description: message })
      }
    },
    [createManufacturer, modalState.manufacturer, resetModal, toastError, toastSuccess, updateManufacturer],
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Manufacturers</h1>
            <p className="text-sm text-muted-foreground">
              Manage manufacturer profiles, market data, and contact information.
            </p>
          </div>
          {canCreate && (
            <Button onClick={openCreateModal} className="self-start md:self-auto">
              <Plus className="mr-2 h-4 w-4" />
              New manufacturer
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
          isProcessing={isBatchDeleting}
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

      <DataTable<Manufacturer, unknown>
        columns={columns}
        data={manufacturers}
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
        enableRowSelection={canDelete('manufacturers')}
        rowSelection={rowSelection}
        onRowSelectionChange={handleRowSelectionChange}
        emptyMessage="No manufacturers found"
      />

      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalTitle}
        description={modalDescription}
        onCancel={resetModal}
        onSubmit={() => formRef.current?.submit()}
        disableSubmit={createManufacturer.isPending || updateManufacturer.isPending}
        isSubmitting={createManufacturer.isPending || updateManufacturer.isPending}
      >
        <ManufacturerForm
          ref={formRef}
          mode={modalState.mode}
          initialData={modalState.manufacturer ?? undefined}
          onSubmit={handleSubmitForm}
        />
      </CrudModal>
    </div>
  )
}
