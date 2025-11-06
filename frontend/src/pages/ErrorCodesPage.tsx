import { useCallback, useMemo, useRef, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { format } from 'date-fns'
import { AlertTriangle, MoreHorizontal, Plus, Trash2 } from 'lucide-react'

import { BatchActionsToolbar } from '@/components/shared/BatchActionsToolbar'
import { CrudModal } from '@/components/shared/CrudModal'
import { DataTable } from '@/components/shared/DataTable'
import { FilterBar, type FilterDefinition, type FilterValue } from '@/components/shared/FilterBar'
import {
  ErrorCodeForm,
  type ErrorCodeFormHandle,
  type ErrorCodeFormSubmit,
} from '@/components/forms/ErrorCodeForm'
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
  useCreateErrorCode,
  useDeleteErrorCode,
  useErrorCodes,
  useUpdateErrorCode,
} from '@/hooks/use-error-codes'
import { useDocuments } from '@/hooks/use-documents'
import { useManufacturers } from '@/hooks/use-manufacturers'
import { usePermissions } from '@/lib/permissions'
import type {
  ErrorCode,
  ErrorCodeCreateInput,
  ErrorCodeFilters,
  ErrorCodeUpdateInput,
} from '@/types/api'
import { SeverityLevel } from '@/types/api'

type TableSorting = {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type ModalState = {
  open: boolean
  mode: 'create' | 'edit'
  errorCode?: ErrorCode | null
}

const DEFAULT_PAGINATION = {
  page: 1,
  page_size: 20,
}

const INITIAL_MODAL_STATE: ModalState = {
  open: false,
  mode: 'create',
  errorCode: null,
}

const severityOptions = Object.values(SeverityLevel).map((severity) => ({
  value: severity,
  label:
    severity
      .split('_')
      .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
      .join(' ') ?? severity,
}))

const getSelectedCount = (selection: Record<string, boolean>) =>
  Object.values(selection).filter(Boolean).length

const formatBoolean = (value?: boolean | null) => (value ? 'Yes' : 'No')

const formatMinutes = (value?: number | null) =>
  value != null && !Number.isNaN(value) ? `${value} min` : '—'

const truncateText = (value?: string | null, length = 120) => {
  if (!value) return '—'
  if (value.length <= length) return value
  return `${value.slice(0, length)}…`
}

export default function ErrorCodesPage() {
  const [pagination, setPagination] = useState(DEFAULT_PAGINATION)
  const [sorting, setSorting] = useState<TableSorting>({ sort_by: 'created_at', sort_order: 'desc' })
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<ErrorCodeFilters>({})
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({})
  const [modalState, setModalState] = useState<ModalState>(INITIAL_MODAL_STATE)
  const [isBatchDeleting, setIsBatchDeleting] = useState(false)
  const formRef = useRef<ErrorCodeFormHandle | null>(null)

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

  const documentsQuery = useDocuments({ page_size: 100, sort_by: 'original_filename', sort_order: 'asc' })
  const documentOptions = useMemo(
    () =>
      (documentsQuery.data?.documents ?? []).map((document) => ({
        value: document.id,
        label: document.original_filename ?? document.filename ?? document.id,
      })),
    [documentsQuery.data?.documents],
  )

  const documentLabelMap = useMemo(
    () =>
      documentOptions.reduce<Record<string, string>>((acc, option) => {
        acc[option.value] = option.label
        return acc
      }, {} as Record<string, string>),
    [documentOptions],
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

  const errorCodesQuery = useErrorCodes(queryParams)
  const createErrorCode = useCreateErrorCode()
  const updateErrorCode = useUpdateErrorCode()
  const deleteErrorCode = useDeleteErrorCode()

  const isLoading = errorCodesQuery.isLoading || errorCodesQuery.isFetching
  const errorCodes = errorCodesQuery.data?.error_codes ?? []

  const paginationMeta = useMemo(
    () => ({
      page: errorCodesQuery.data?.page ?? pagination.page,
      page_size: errorCodesQuery.data?.page_size ?? pagination.page_size,
      total: errorCodesQuery.data?.total ?? 0,
      total_pages: errorCodesQuery.data?.total_pages ?? 1,
    }),
    [errorCodesQuery.data, pagination.page, pagination.page_size],
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
    setModalState({ open: true, mode: 'create', errorCode: null })
  }, [])

  const openEditModal = useCallback((errorCode: ErrorCode) => {
    setModalState({ open: true, mode: 'edit', errorCode })
  }, [])

  const handleDelete = useCallback(
    async (id: string) => {
      if (!canDelete('error_codes')) return

      try {
        const response = await deleteErrorCode.mutateAsync(id)
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to delete error code')
        }
        toastSuccess('Error code deleted', { description: 'The error code has been removed.' })
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Deletion failed', { description: message })
      }
    },
    [canDelete, deleteErrorCode, toastError, toastSuccess],
  )

  const handleBatchDelete = useCallback(async () => {
    if (!canDelete('error_codes')) return

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
          const response = await deleteErrorCode.mutateAsync(id)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to delete error code')
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
  }, [canDelete, deleteErrorCode, notify, rowSelection, toastError])

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
          } else {
            next.manufacturer_id = String(value)
          }
          break
        case 'document_id':
          if (isEmpty) {
            delete next.document_id
          } else {
            next.document_id = String(value)
          }
          break
        case 'chunk_id':
          if (isEmpty) {
            delete next.chunk_id
          } else {
            next.chunk_id = String(value)
          }
          break
        case 'error_code':
          if (isEmpty) {
            delete next.error_code
          } else {
            next.error_code = String(value)
          }
          break
        case 'severity_level':
          if (isEmpty) {
            delete next.severity_level
          } else {
            next.severity_level = value as SeverityLevel
          }
          break
        case 'requires_technician':
          if (typeof value === 'boolean') {
            next.requires_technician = value
          } else {
            delete next.requires_technician
          }
          break
        case 'requires_parts':
          if (typeof value === 'boolean') {
            next.requires_parts = value
          } else {
            delete next.requires_parts
          }
          break
        default:
          break
      }

      return next
    })
  }, [])

  const handleResetFilters = useCallback(() => {
    setFilters({})
    setSearch('')
    setPagination(DEFAULT_PAGINATION)
  }, [])

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value)
    setPagination(DEFAULT_PAGINATION)
  }, [])

  const filterDefinitions: FilterDefinition[] = useMemo(
    () => [
      {
        key: 'manufacturer_id',
        label: 'Manufacturer',
        type: 'select',
        options: manufacturerOptions,
        placeholder: 'All manufacturers',
      },
      {
        key: 'document_id',
        label: 'Document',
        type: 'select',
        options: documentOptions,
        placeholder: 'All documents',
      },
      {
        key: 'severity_level',
        label: 'Severity',
        type: 'select',
        options: severityOptions,
        placeholder: 'Any severity',
      },
      {
        key: 'requires_technician',
        label: 'Technician required',
        type: 'switch',
      },
      {
        key: 'requires_parts',
        label: 'Parts required',
        type: 'switch',
      },
      {
        key: 'error_code',
        label: 'Error code',
        type: 'text',
        placeholder: 'e.g. 1234-AB',
      },
      {
        key: 'chunk_id',
        label: 'Chunk ID',
        type: 'text',
        placeholder: 'Optional chunk ID',
      },
    ],
    [documentOptions, manufacturerOptions],
  )

  const actionColumn = useMemo<ColumnDef<ErrorCode>>(
    () => ({
      id: '_actions',
      header: '',
      enableSorting: false,
      size: 64,
      cell: ({ row }) => {
        const errorCode = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="action-menu-button">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Open actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canWrite('error_codes') && (
                <DropdownMenuItem onSelect={() => openEditModal(errorCode)} data-testid="edit-error-code-menu-item">Edit</DropdownMenuItem>
              )}
              {canDelete('error_codes') && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onSelect={() => handleDelete(errorCode.id)}
                  data-testid="delete-error-code-menu-item"
                >
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    }),
    [canDelete, canWrite, handleDelete, openEditModal],
  )

  const columns = useMemo<ColumnDef<ErrorCode>[]>(
    () => [
      {
        accessorKey: 'error_code',
        header: 'Error code',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <span className="font-medium text-sm text-foreground">{row.original.error_code}</span>
          </div>
        ),
      },
      {
        accessorKey: 'error_description',
        header: 'Description',
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">{truncateText(row.original.error_description)}</span>
        ),
      },
      {
        accessorKey: 'severity_level',
        header: 'Severity',
        cell: ({ row }) => <Badge variant="secondary">{row.original.severity_level}</Badge>,
      },
      {
        accessorKey: 'manufacturer_id',
        header: 'Manufacturer',
        cell: ({ row }) =>
          manufacturerLabelMap[row.original.manufacturer_id ?? ''] ?? row.original.manufacturer_id ?? '—',
      },
      {
        accessorKey: 'document_id',
        header: 'Document',
        cell: ({ row }) =>
          documentLabelMap[row.original.document_id ?? ''] ?? row.original.document_id ?? '—',
      },
      {
        accessorKey: 'requires_technician',
        header: 'Technician',
        cell: ({ row }) => formatBoolean(row.original.requires_technician),
      },
      {
        accessorKey: 'requires_parts',
        header: 'Parts',
        cell: ({ row }) => formatBoolean(row.original.requires_parts),
      },
      {
        accessorKey: 'estimated_fix_time_minutes',
        header: 'Fix time',
        cell: ({ row }) => formatMinutes(row.original.estimated_fix_time_minutes),
      },
      {
        accessorKey: 'updated_at',
        header: 'Updated',
        cell: ({ row }) => (row.original.updated_at ? format(new Date(row.original.updated_at), 'PPp') : '—'),
      },
      actionColumn,
    ],
    [actionColumn, documentLabelMap, manufacturerLabelMap],
  )

  const selectedCount = getSelectedCount(rowSelection)
  const canCreate = canWrite('error_codes')
  const canShowBatchToolbar = canDelete('error_codes') && selectedCount > 0

  const modalTitle = modalState.mode === 'create' ? 'Create error code' : 'Edit error code'
  const modalDescription =
    modalState.mode === 'create'
      ? 'Add a new error code to the knowledge base.'
      : 'Update the selected error code details.'

  const handleSubmitForm = useCallback(
    async (payload: ErrorCodeFormSubmit) => {
      try {
        if (payload.mode === 'create') {
          const response = await createErrorCode.mutateAsync(payload.data as ErrorCodeCreateInput)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to create error code')
          }
          toastSuccess('Error code created', {
            description: 'The error code has been added successfully.',
          })
          resetModal()
          return
        }

        if (!modalState.errorCode) {
          throw new Error('No error code selected for update')
        }

        const response = await updateErrorCode.mutateAsync({
          id: modalState.errorCode.id,
          data: payload.data as ErrorCodeUpdateInput,
        })
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to update error code')
        }

        toastSuccess('Error code updated', { description: 'Changes saved successfully.' })
        resetModal()
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Operation failed', { description: message })
      }
    },
    [createErrorCode, modalState.errorCode, resetModal, toastError, toastSuccess, updateErrorCode],
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Error codes</h1>
            <p className="text-sm text-muted-foreground">
              Manage troubleshooting error codes, severity, and remediation guidance.
            </p>
          </div>
          {canCreate && (
            <Button onClick={openCreateModal} className="self-start md:self-auto">
              <Plus className="mr-2 h-4 w-4" />
              New error code
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

      <DataTable<ErrorCode, unknown>
        columns={columns}
        data={errorCodes}
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
        enableRowSelection={canDelete('error_codes')}
        rowSelection={rowSelection}
        onRowSelectionChange={handleRowSelectionChange}
        emptyMessage="No error codes found"
      />

      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalTitle}
        description={modalDescription}
        onCancel={resetModal}
        onSubmit={() => formRef.current?.submit()}
        disableSubmit={createErrorCode.isPending || updateErrorCode.isPending}
        isSubmitting={createErrorCode.isPending || updateErrorCode.isPending}
      >
        <ErrorCodeForm
          ref={formRef}
          mode={modalState.mode}
          initialData={modalState.errorCode ?? undefined}
          onSubmit={handleSubmitForm}
        />
      </CrudModal>
    </div>
  )
}
