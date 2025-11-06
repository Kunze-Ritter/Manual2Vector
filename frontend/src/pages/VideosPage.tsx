import { useCallback, useMemo, useRef, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { format } from 'date-fns'
import { ImageOff, MoreHorizontal, PlayCircle, Plus, Trash2 } from 'lucide-react'

import { BatchActionsToolbar } from '@/components/shared/BatchActionsToolbar'
import { CrudModal } from '@/components/shared/CrudModal'
import { DataTable } from '@/components/shared/DataTable'
import { FilterBar, type FilterDefinition, type FilterValue } from '@/components/shared/FilterBar'
import {
  VideoForm,
  type VideoFormHandle,
  type VideoFormSubmit,
} from '@/components/forms/VideoForm'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'
import { useDocuments } from '@/hooks/use-documents'
import { useManufacturers, useManufacturerSeries } from '@/hooks/use-manufacturers'
import {
  useCreateVideo,
  useDeleteVideo,
  useUpdateVideo,
  useVideos,
} from '@/hooks/use-videos'
import { usePermissions } from '@/lib/permissions'
import type { Video, VideoCreateInput, VideoFilters, VideoUpdateInput } from '@/types/api'
import { VideoPlatform } from '@/types/api'

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
  video?: Video | null
}

const INITIAL_MODAL_STATE: ModalState = {
  open: false,
  mode: 'create',
  video: null,
}

const toTitleCase = (value: string) =>
  value
    .split('_')
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')

const videoPlatformOptions = Object.values(VideoPlatform).map((platform) => ({
  value: platform,
  label: toTitleCase(platform),
}))

const getSelectedCount = (selection: Record<string, boolean>) =>
  Object.values(selection).filter(Boolean).length

const formatDuration = (seconds?: number | null) => {
  if (seconds == null || Number.isNaN(seconds)) return '—'

  const totalSeconds = Math.max(0, Math.floor(seconds))
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const remainingSeconds = totalSeconds % 60

  const segments = [minutes.toString().padStart(hours ? 2 : 1, '0'), remainingSeconds.toString().padStart(2, '0')]
  if (hours) {
    segments.unshift(hours.toString())
  }
  return segments.join(':')
}

const formatNumber = (value?: number | null) => (value != null ? value.toLocaleString() : '—')

const formatDate = (value?: string | null) => (value ? format(new Date(value), 'PP') : '—')

export default function VideosPage() {
  const [pagination, setPagination] = useState(DEFAULT_PAGINATION)
  const [sorting, setSorting] = useState<TableSorting>({ sort_by: 'created_at', sort_order: 'desc' })
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<VideoFilters>({})
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({})
  const [modalState, setModalState] = useState<ModalState>(INITIAL_MODAL_STATE)
  const [isBatchDeleting, setIsBatchDeleting] = useState(false)
  const formRef = useRef<VideoFormHandle | null>(null)

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
  const seriesQuery = useManufacturerSeries(selectedManufacturerId)
  const seriesOptions = useMemo(
    () =>
      (seriesQuery.data ?? []).map((series) => ({
        value: series.id,
        label: series.name,
      })),
    [seriesQuery.data],
  )

  const seriesLabelMap = useMemo(
    () =>
      seriesOptions.reduce<Record<string, string>>((acc, option) => {
        acc[option.value] = option.label
        return acc
      }, {} as Record<string, string>),
    [seriesOptions],
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

  const videosQuery = useVideos(queryParams)
  const createVideo = useCreateVideo()
  const updateVideo = useUpdateVideo()
  const deleteVideo = useDeleteVideo()

  const isLoading = videosQuery.isLoading || videosQuery.isFetching
  const videos = videosQuery.data?.videos ?? []

  const paginationMeta = useMemo(
    () => ({
      page: videosQuery.data?.page ?? pagination.page,
      page_size: videosQuery.data?.page_size ?? pagination.page_size,
      total: videosQuery.data?.total ?? 0,
      total_pages: videosQuery.data?.total_pages ?? 1,
    }),
    [videosQuery.data, pagination.page, pagination.page_size],
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
    setModalState({ open: true, mode: 'create', video: null })
  }, [])

  const openEditModal = useCallback((video: Video) => {
    setModalState({ open: true, mode: 'edit', video })
  }, [])

  const handleDelete = useCallback(
    async (id: string) => {
      if (!canDelete('videos')) return

      try {
        const response = await deleteVideo.mutateAsync(id)
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to delete video')
        }
        toastSuccess('Video deleted', { description: 'The video has been removed.' })
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Deletion failed', { description: message })
      }
    },
    [canDelete, deleteVideo, toastError, toastSuccess],
  )

  const handleBatchDelete = useCallback(async () => {
    if (!canDelete('videos')) return

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
          const response = await deleteVideo.mutateAsync(id)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to delete video')
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
  }, [canDelete, deleteVideo, notify, rowSelection, toastError])

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
        case 'document_id':
          if (isEmpty) {
            delete next.document_id
          } else {
            next.document_id = String(value)
          }
          break
        case 'platform':
          if (isEmpty) {
            delete next.platform
          } else {
            next.platform = value as VideoPlatform
          }
          break
        case 'youtube_id':
          if (isEmpty) {
            delete next.youtube_id
          } else {
            next.youtube_id = String(value)
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
        key: 'series_id',
        label: 'Series',
        type: 'select',
        options: seriesOptions,
        placeholder: selectedManufacturerId ? 'All series' : 'Select manufacturer first',
      },
      {
        key: 'document_id',
        label: 'Document',
        type: 'select',
        options: documentOptions,
        placeholder: 'All documents',
      },
      {
        key: 'platform',
        label: 'Platform',
        type: 'select',
        options: videoPlatformOptions,
        placeholder: 'Any platform',
      },
      {
        key: 'youtube_id',
        label: 'YouTube ID',
        type: 'text',
        placeholder: 'e.g. dQw4w9WgXcQ',
      },
    ],
    [documentOptions, manufacturerOptions, selectedManufacturerId, seriesOptions],
  )

  const actionColumn = useMemo<ColumnDef<Video>>(
    () => ({
      id: '_actions',
      header: '',
      enableSorting: false,
      size: 64,
      cell: ({ row }) => {
        const video = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="action-menu-button">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Open actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canWrite('videos') && <DropdownMenuItem onSelect={() => openEditModal(video)} data-testid="edit-video-menu-item">Edit</DropdownMenuItem>}
              {canDelete('videos') && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onSelect={() => handleDelete(video.id)}
                  data-testid="delete-video-menu-item"
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

  const columns = useMemo<ColumnDef<Video>[]>(
    () => [
      {
        accessorKey: 'thumbnail_url',
        header: 'Preview',
        enableSorting: false,
        cell: ({ row }) => {
          const thumbnail = row.original.thumbnail_url
          if (!thumbnail) {
            return (
              <div className="flex h-12 w-20 items-center justify-center rounded border border-dashed border-border bg-muted">
                <ImageOff className="h-4 w-4 text-muted-foreground" />
              </div>
            )
          }

          return (
            <div className="h-12 w-20 overflow-hidden rounded border border-border">
              <img src={thumbnail} alt={row.original.title} className="h-full w-full object-cover" />
            </div>
          )
        },
      },
      {
        accessorKey: 'title',
        header: 'Title',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <PlayCircle className="h-4 w-4 text-primary" />
            <span className="font-medium text-sm text-foreground">{row.original.title}</span>
          </div>
        ),
      },
      {
        accessorKey: 'platform',
        header: 'Platform',
        cell: ({ row }) => <Badge variant="outline">{toTitleCase(row.original.platform)}</Badge>,
      },
      {
        accessorKey: 'duration_seconds',
        header: 'Duration',
        cell: ({ row }) => formatDuration(row.original.duration_seconds),
      },
      {
        accessorKey: 'view_count',
        header: 'Views',
        cell: ({ row }) => formatNumber(row.original.view_count),
      },
      {
        accessorKey: 'manufacturer_id',
        header: 'Manufacturer',
        cell: ({ row }) =>
          manufacturerLabelMap[row.original.manufacturer_id ?? ''] ?? row.original.manufacturer_id ?? '—',
      },
      {
        accessorKey: 'series_id',
        header: 'Series',
        cell: ({ row }) => seriesLabelMap[row.original.series_id ?? ''] ?? row.original.series_id ?? '—',
      },
      {
        accessorKey: 'document_id',
        header: 'Document',
        cell: ({ row }) =>
          documentLabelMap[row.original.document_id ?? ''] ?? row.original.document_id ?? '—',
      },
      {
        accessorKey: 'published_at',
        header: 'Published',
        cell: ({ row }) => formatDate(row.original.published_at),
      },
      actionColumn,
    ],
    [actionColumn, documentLabelMap, manufacturerLabelMap, seriesLabelMap],
  )

  const selectedCount = getSelectedCount(rowSelection)
  const canCreate = canWrite('videos')
  const canShowBatchToolbar = canDelete('videos') && selectedCount > 0

  const modalTitle = modalState.mode === 'create' ? 'Create video' : 'Edit video'
  const modalDescription =
    modalState.mode === 'create'
      ? 'Add a new video reference to the content library.'
      : 'Update the selected video details.'

  const handleSubmitForm = useCallback(
    async (payload: VideoFormSubmit) => {
      try {
        if (payload.mode === 'create') {
          const response = await createVideo.mutateAsync(payload.data as VideoCreateInput)
          if (!response.success || !response.data) {
            throw new Error(response.message ?? 'Failed to create video')
          }
          toastSuccess('Video created', { description: 'The video has been added successfully.' })
          resetModal()
          return
        }

        if (!modalState.video) {
          throw new Error('No video selected for update')
        }

        const response = await updateVideo.mutateAsync({
          id: modalState.video.id,
          data: payload.data as VideoUpdateInput,
        })
        if (!response.success || !response.data) {
          throw new Error(response.message ?? 'Failed to update video')
        }

        toastSuccess('Video updated', { description: 'Changes saved successfully.' })
        resetModal()
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unexpected error'
        toastError('Operation failed', { description: message })
      }
    },
    [createVideo, modalState.video, resetModal, toastError, toastSuccess, updateVideo],
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Videos</h1>
            <p className="text-sm text-muted-foreground">
              Manage training and troubleshooting videos, their metadata, and relationships.
            </p>
          </div>
          {canCreate && (
            <Button onClick={openCreateModal} className="self-start md:self-auto">
              <Plus className="mr-2 h-4 w-4" />
              New video
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

      <DataTable<Video, unknown>
        columns={columns}
        data={videos}
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
        enableRowSelection={canDelete('videos')}
        rowSelection={rowSelection}
        onRowSelectionChange={handleRowSelectionChange}
        emptyMessage="No videos found"
      />

      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalTitle}
        description={modalDescription}
        onCancel={resetModal}
        onSubmit={() => formRef.current?.submit()}
        disableSubmit={createVideo.isPending || updateVideo.isPending}
        isSubmitting={createVideo.isPending || updateVideo.isPending}
      >
        <VideoForm
          ref={formRef}
          mode={modalState.mode}
          initialData={modalState.video ?? undefined}
          onSubmit={handleSubmitForm}
        />
      </CrudModal>
    </div>
  )
}
