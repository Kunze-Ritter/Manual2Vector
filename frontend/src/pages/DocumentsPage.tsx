import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { format } from 'date-fns'
import { FileText, MoreHorizontal, Plus, Trash2 } from 'lucide-react'

import { BatchActionsToolbar } from '@/components/shared/BatchActionsToolbar'
import { CrudModal } from '@/components/shared/CrudModal'
import { DataTable } from '@/components/shared/DataTable'
import { FilterBar, type FilterDefinition, type FilterValue } from '@/components/shared/FilterBar'
import {
  DocumentForm,
  type DocumentFormHandle,
  type DocumentFormSubmit,
} from '@/components/forms/DocumentForm'
import { FileUploadDialog } from '@/components/upload/FileUploadDialog'
import { DocumentProcessingTimeline } from '@/components/documents/DocumentProcessingTimeline'
import { DocumentStageDetailsModal } from '@/components/documents/DocumentStageDetailsModal'
import { DocumentStageProgressCell } from '@/components/documents/DocumentStageProgressCell'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'
import {
  useBatchDeleteDocuments,
  useCreateDocument,
  useDeleteDocument,
  useDocuments,
  useUpdateDocument,
} from '@/hooks/use-documents'
import { useDocumentStages } from '@/hooks/use-document-stages'
import type { Document, DocumentCreateInput, DocumentFilters, DocumentUpdateInput } from '@/types/api'
import { DocumentType, ProcessingStatus } from '@/types/api'
import { usePermissions } from '@/lib/permissions'

type TableSorting = {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

type ModalState = {
  open: boolean
  mode: 'create' | 'edit'
  document?: Document | null
}

type DeleteConfirmState = {
  open: boolean
  documentId?: string
  isBatch: boolean
  selectedIds?: string[]
}

const initialModalState: ModalState = {
  open: false,
  mode: 'create',
  document: null,
}

const initialDeleteConfirmState: DeleteConfirmState = {
  open: false,
  isBatch: false,
}

const defaultPagination = {
  page: 1,
  page_size: 20,
}

const formatLabel = (value: string) =>
  value
    .toLowerCase()
    .split('_')
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')

const documentTypeOptions = Object.values(DocumentType).map((value) => ({
  value,
  label: formatLabel(value),
}))

const processingStatusOptions = Object.values(ProcessingStatus).map((value) => ({
  value,
  label: formatLabel(value),
}))

const getSelectedCount = (selection: Record<string, boolean>) =>
  Object.values(selection).filter(Boolean).length

export default function DocumentsPage() {
  const [pagination, setPagination] = useState(defaultPagination)
  const [sorting, setSorting] = useState<TableSorting>({ sort_by: 'created_at', sort_order: 'desc' })
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<DocumentFilters>({})
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({})
  const [modalState, setModalState] = useState<ModalState>(initialModalState)
  const [deleteConfirmState, setDeleteConfirmState] = useState<DeleteConfirmState>(initialDeleteConfirmState)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [stageModalState, setStageModalState] = useState<{
    open: boolean
    documentId?: string
    stageName?: string
  }>({ open: false })
  const formRef = useRef<DocumentFormHandle | null>(null)

  const { canWrite, canDelete } = usePermissions()
  const { notify, success: toastSuccess, error: toastError } = useToast()

  // Check URL parameter for upload dialog
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('dialog') === 'upload') {
      setUploadDialogOpen(true)
      // Remove query param
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

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

  const documentsQuery = useDocuments(queryParams)
  const createDocument = useCreateDocument()
  const updateDocument = useUpdateDocument()
  const deleteDocument = useDeleteDocument()
  const batchDeleteDocuments = useBatchDeleteDocuments()

  const isLoading = documentsQuery.isLoading || documentsQuery.isFetching
  const documents = documentsQuery.data?.documents ?? []
  const paginationMeta = useMemo(
    () => ({
      page: documentsQuery.data?.page ?? pagination.page,
      page_size: documentsQuery.data?.page_size ?? pagination.page_size,
      total: documentsQuery.data?.total ?? 0,
      total_pages: documentsQuery.data?.total_pages ?? 1,
    }),
    [documentsQuery.data, pagination.page, pagination.page_size],
  )

  const handlePaginationChange = useCallback((page: number, pageSize: number) => {
    setPagination({ page, page_size: pageSize })
  }, [])

  const handleSortingChange = useCallback((sort_by: string, sort_order: 'asc' | 'desc') => {
    setSorting({ sort_by: sort_by || undefined, sort_order })
  }, [])

  const handleRowSelectionChange = useCallback(
    ({ state }: { state: Record<string, boolean> }) => {
      setRowSelection(state)
    },
    [],
  )

  const resetModal = useCallback(() => setModalState(initialModalState), [])

  const resetDeleteConfirm = useCallback(() => setDeleteConfirmState(initialDeleteConfirmState), [])

  const openCreateModal = useCallback(() => {
    setModalState({ open: true, mode: 'create', document: null })
  }, [])

  const openEditModal = useCallback((document: Document) => {
    setModalState({ open: true, mode: 'edit', document })
  }, [])

  const openDeleteConfirm = useCallback((documentId: string) => {
    setDeleteConfirmState({ open: true, documentId, isBatch: false })
  }, [])

  const openBatchDeleteConfirm = useCallback(() => {
    const selectedIds = Object.entries(rowSelection)
      .filter(([, selected]) => selected)
      .map(([id]) => id)
    
    if (selectedIds.length > 0) {
      setDeleteConfirmState({ open: true, isBatch: true, selectedIds })
    }
  }, [rowSelection])

  const handleDelete = useCallback(
    async (id: string) => {
      if (!canDelete('documents')) return

      try {
        const response = await deleteDocument.mutateAsync(id)
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to delete document')
        }
        toastSuccess('Document deleted', { description: 'The document has been removed.' })
        resetDeleteConfirm()
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Deletion failed', { description: message })
        resetDeleteConfirm()
      }
    },
    [canDelete, deleteDocument, toastError, toastSuccess, resetDeleteConfirm],
  )

  const handleBatchDelete = useCallback(async () => {
    if (!canDelete('documents')) return

    const selectedIds = deleteConfirmState.selectedIds ?? []

    if (!selectedIds.length) return

    try {
      const response = await batchDeleteDocuments.mutateAsync(selectedIds)
      if (!response.success || !response.data) {
        throw new Error(response.message ?? 'Batch delete failed')
      }

      const { successful, failed } = response.data
      notify('Batch delete completed', {
        description: `${successful} deleted, ${failed} failed.`,
      })
      setRowSelection({})
      resetDeleteConfirm()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unexpected error'
      toastError('Batch delete failed', { description: message })
      resetDeleteConfirm()
    }
  }, [batchDeleteDocuments, canDelete, deleteConfirmState.selectedIds, notify, toastError, resetDeleteConfirm])

  const handleFilterChange = useCallback((key: string, value: FilterValue) => {
    setPagination(defaultPagination)
    setFilters((prev) => {
      const next = { ...prev }
      const isEmpty =
        value === undefined ||
        value === null ||
        (typeof value === 'string' && value.trim() === '')

      switch (key) {
        case 'document_type':
          if (isEmpty) {
            delete next.document_type
          } else {
            next.document_type = value as DocumentType
          }
          break
        case 'processing_status':
          if (isEmpty) {
            delete next.processing_status
          } else {
            next.processing_status = value as ProcessingStatus
          }
          break
        case 'manual_review_required':
          if (typeof value === 'boolean') {
            next.manual_review_required = value
          } else {
            delete next.manual_review_required
          }
          break
        case 'language':
          if (isEmpty) {
            delete next.language
          } else {
            next.language = String(value)
          }
          break
        case 'has_failed_stages':
          if (typeof value === 'boolean') {
            next.has_failed_stages = value
          } else {
            delete next.has_failed_stages
          }
          break
        case 'has_incomplete_stages':
          if (typeof value === 'boolean') {
            next.has_incomplete_stages = value
          } else {
            delete next.has_incomplete_stages
          }
          break
        case 'stage_name':
          if (isEmpty) {
            delete next.stage_name
          } else {
            next.stage_name = String(value)
          }
          break
        default:
          break
      }

      return next
    })
  }, [])

  const handleResetFilters = useCallback(() => {
    setPagination(defaultPagination)
    setFilters({})
    setSearch('')
  }, [])

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value)
    setPagination(defaultPagination)
  }, [])

  const filterDefinitions: FilterDefinition[] = useMemo(
    () => [
      {
        key: 'document_type',
        label: 'Type',
        type: 'select',
        options: documentTypeOptions,
      },
      {
        key: 'processing_status',
        label: 'Status',
        type: 'select',
        options: processingStatusOptions,
      },
      {
        key: 'manual_review_required',
        label: 'Needs review',
        type: 'switch',
      },
      {
        key: 'has_failed_stages',
        label: 'Has failed stages',
        type: 'switch',
      },
      {
        key: 'has_incomplete_stages',
        label: 'Has incomplete stages',
        type: 'switch',
      },
      {
        key: 'language',
        label: 'Language',
        type: 'text',
        placeholder: 'e.g. en-US',
      },
    ],
    [],
  )

  const actionColumn = useMemo<ColumnDef<Document>>(
    () => ({
      id: '_actions',
      header: '',
      enableSorting: false,
      cell: ({ row }) => {
        const document = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="action-menu-button">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Open actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canWrite('documents') && <DropdownMenuItem onSelect={() => openEditModal(document)} data-testid="edit-document-menu-item">Edit</DropdownMenuItem>}
              {canDelete('documents') && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onSelect={() => openDeleteConfirm(document.id)}
                  data-testid="delete-document-menu-item"
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

  const columns = useMemo<ColumnDef<Document>[]>(
    () => [
      {
        accessorKey: 'filename',
        header: 'Filename',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium text-sm text-foreground">{row.original.filename}</span>
          </div>
        ),
      },
      {
        accessorKey: 'document_type',
        header: 'Type',
        cell: ({ row }) => <Badge variant="outline">{formatLabel(row.original.document_type)}</Badge>,
      },
      {
        accessorKey: 'processing_status',
        header: 'Status',
        cell: ({ row }) => {
          const status = row.original.processing_status
          const variant =
            status === ProcessingStatus.COMPLETED
              ? 'default'
              : status === ProcessingStatus.FAILED
              ? 'destructive'
              : 'secondary'
          return <Badge variant={variant}>{formatLabel(status)}</Badge>
        },
      },
      {
        accessorKey: 'stage_progress',
        header: 'Pipeline Progress',
        cell: ({ row }) => (
          <DocumentStageProgressCell
            documentId={row.original.id}
            onViewClick={() => setStageModalState({ open: true, documentId: row.original.id })}
          />
        ),
      },
      {
        accessorKey: 'manual_review_required',
        header: 'Needs review',
        cell: ({ row }) => (
          <Badge variant={row.original.manual_review_required ? 'destructive' : 'secondary'}>
            {row.original.manual_review_required ? 'Yes' : 'No'}
          </Badge>
        ),
      },
      {
        accessorKey: 'publish_date',
        header: 'Published',
        cell: ({ row }) =>
          row.original.publish_date ? (
            <span>{format(new Date(row.original.publish_date), 'PP')}</span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: 'created_at',
        header: 'Uploaded',
        cell: ({ row }) => <span>{format(new Date(row.original.created_at), 'PPp')}</span>,
      },
      actionColumn,
    ],
    [actionColumn],
  )

  const selectedCount = getSelectedCount(rowSelection)
  const canCreate = canWrite('documents')
  const canShowBatchToolbar = canDelete('documents') && selectedCount > 0

  const modalTitle = modalState.mode === 'create' ? 'Create document' : 'Edit document'
  const modalDescription =
    modalState.mode === 'create'
      ? 'Add a new document to the catalog.'
      : 'Update metadata for the selected document.'

  const handleSubmitForm = useCallback(
    async (payload: DocumentFormSubmit) => {
      try {
        if (payload.mode === 'create') {
          const response = await createDocument.mutateAsync(payload.data as DocumentCreateInput)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to create document')
          }
          toastSuccess('Document created', {
            description: 'The document has been added successfully.',
          })
          resetModal()
          return
        }

        if (!modalState.document) {
          throw new Error('No document selected for update')
        }

        const response = await updateDocument.mutateAsync({
          id: modalState.document.id,
          data: payload.data as DocumentUpdateInput,
        })
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to update document')
        }

        toastSuccess('Document updated', { description: 'Changes saved successfully.' })
        resetModal()
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Operation failed', { description: message })
      }
    },
    [createDocument, modalState.document, resetModal, toastError, toastSuccess, updateDocument],
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
            <p className="text-sm text-muted-foreground">
              Manage uploaded manuals, bulletins, and technical resources for the knowledge base.
            </p>
          </div>
          {canCreate && (
            <div className="flex gap-2">
              <Button 
                onClick={() => setUploadDialogOpen(true)} 
                className="self-start md:self-auto" 
                data-testid="upload-document-button"
              >
                <Plus className="mr-2 h-4 w-4" />
                Upload documents
              </Button>
              <Button 
                onClick={openCreateModal} 
                variant="outline"
                className="self-start md:self-auto" 
                data-testid="create-document-button"
              >
                New document
              </Button>
            </div>
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
          isProcessing={batchDeleteDocuments.isPending}
          actions={[
            {
              key: 'delete',
              label: 'Delete selected',
              icon: <Trash2 className="h-4 w-4" />,
              onAction: openBatchDeleteConfirm,
              destructive: true,
            },
          ]}
        />
      )}

      <DataTable<Document, unknown>
        dataTestId="documents-table"
        columns={columns}
        data={documents}
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
        enableRowSelection={canDelete('documents')}
        rowSelection={rowSelection}
        onRowSelectionChange={handleRowSelectionChange}
        emptyMessage="No documents found"
      />

      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalTitle}
        description={modalDescription}
        onCancel={resetModal}
        onSubmit={() => formRef.current?.submit()}
        disableSubmit={createDocument.isPending || updateDocument.isPending}
        isSubmitting={createDocument.isPending || updateDocument.isPending}
      >
        <DocumentForm
          ref={formRef}
          mode={modalState.mode}
          initialData={modalState.document ?? undefined}
          onSubmit={handleSubmitForm}
        />
      </CrudModal>

      <AlertDialog open={deleteConfirmState.open} onOpenChange={(open) => !open && resetDeleteConfirm()}>
        <AlertDialogContent data-testid={deleteConfirmState.isBatch ? "confirm-batch-delete-dialog" : "confirm-delete-dialog"}>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {deleteConfirmState.isBatch ? 'Delete Multiple Documents' : 'Delete Document'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {deleteConfirmState.isBatch
                ? `Are you sure you want to delete ${deleteConfirmState.selectedIds?.length || 0} documents? This action cannot be undone.`
                : 'Are you sure you want to delete this document? This action cannot be undone.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteConfirmState.isBatch) {
                  handleBatchDelete()
                } else if (deleteConfirmState.documentId) {
                  handleDelete(deleteConfirmState.documentId)
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              data-testid={deleteConfirmState.isBatch ? "confirm-batch-delete-button" : "confirm-delete-button"}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <FileUploadDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
      />

      {/* Stage Timeline Modal */}
      {stageModalState.documentId && !stageModalState.stageName && (
        <Dialog open={stageModalState.open} onOpenChange={(open) => setStageModalState({ ...stageModalState, open })}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>Processing Pipeline</DialogTitle>
            </DialogHeader>
            <DocumentProcessingTimeline
              documentId={stageModalState.documentId}
              onStageClick={(stageName) => setStageModalState({ ...stageModalState, stageName })}
            />
          </DialogContent>
        </Dialog>
      )}

      {/* Stage Details Modal */}
      {stageModalState.documentId && stageModalState.stageName && (
        <DocumentStageDetailsModal
          documentId={stageModalState.documentId}
          stageName={stageModalState.stageName}
          open={Boolean(stageModalState.stageName)}
          onOpenChange={(open) => !open && setStageModalState({ ...stageModalState, stageName: undefined })}
        />
      )}
    </div>
  )
}
