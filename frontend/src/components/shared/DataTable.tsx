import { useMemo, useState } from 'react'
import type {
  Cell,
  ColumnDef,
  Header,
  HeaderGroup,
  Row,
  RowSelectionState,
  SortingState,
  Table as TableType,
  Updater,
} from '@tanstack/react-table'
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronsLeft,
  ChevronsRight,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export interface DataTablePagination {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface DataTableSorting {
  sort_by: string
  sort_order: 'asc' | 'desc'
}

export interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  isLoading?: boolean
  pagination?: DataTablePagination
  onPaginationChange?: (page: number, pageSize: number) => void
  sorting?: DataTableSorting
  sortingState?: SortingState
  onSortingChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void
  onSortingStateChange?: (sortingState: SortingState) => void
  onClearSorting?: () => void
  multiSort?: boolean
  rowSelection?: Record<string, boolean>
  onRowSelectionChange?: (event: RowSelectionChangeEvent<TData>) => void
  enableRowSelection?: boolean
  getRowId?: (originalRow: TData, index: number, parent?: Row<TData>) => string
  emptyMessage?: string
  tableCaption?: string
  dataTestId?: string
}

export interface RowSelectionChangeEvent<TData> {
  state: Record<string, boolean>
  selectedRows: TData[]
  selectedIds: string[]
  selectedRowModel: ReturnType<TableType<TData>['getSelectedRowModel']>
}

const PAGE_SIZE_OPTIONS = ['10', '20', '50', '100']

function getSortingState(sorting?: DataTableSorting): SortingState {
  if (!sorting?.sort_by) {
    return []
  }
  return [
    {
      id: sorting.sort_by,
      desc: sorting.sort_order === 'desc',
    },
  ]
}

interface ApplySortingOptions<TData> {
  onSortingChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void
  onSortingStateChange?: (sortingState: SortingState) => void
  onClearSorting?: () => void
  multiSort?: boolean
  table: TableType<TData>
}

function applySortingChange<TData>(updater: Updater<SortingState>, options: ApplySortingOptions<TData>): void {
  const { onSortingChange, onSortingStateChange, onClearSorting, multiSort, table } = options
  const nextSorting =
    typeof updater === 'function' ? updater(table.getState().sorting) : (updater as SortingState)
  onSortingStateChange?.(nextSorting)

  const primary = nextSorting[0]

  if (primary) {
    onSortingChange?.(primary.id, primary.desc ? 'desc' : 'asc')
    return
  }

  if (!multiSort) {
    onSortingChange?.('', 'asc')
  }

  onClearSorting?.()
}

function renderSortingIndicator<TData>(columnId: string, table: TableType<TData>) {
  const sorting = table.getState().sorting
  const current = sorting.find((item: SortingState[number]) => item.id === columnId)

  if (!current) {
    return <ArrowUpDown className="ml-2 h-4 w-4 text-muted-foreground" />
  }

  return current.desc ? (
    <ArrowDown className="ml-2 h-4 w-4" />
  ) : (
    <ArrowUp className="ml-2 h-4 w-4" />
  )
}

function renderSkeletonRows(columnCount: number, rowCount = 10) {
  return Array.from({ length: rowCount }).map((_, index) => (
    <TableRow key={`skeleton-${index}`}>
      {Array.from({ length: columnCount }).map((__, colIndex) => (
        <TableCell key={`skeleton-cell-${index}-${colIndex}`}>
          <Skeleton className="h-6 w-full" />
        </TableCell>
      ))}
    </TableRow>
  ))
}

export function DataTable<TData, TValue>({
  columns,
  data,
  isLoading = false,
  pagination,
  onPaginationChange,
  sorting,
  sortingState,
  onSortingChange,
  onSortingStateChange,
  onClearSorting,
  multiSort = false,
  rowSelection,
  onRowSelectionChange,
  enableRowSelection = false,
  getRowId,
  emptyMessage = 'No data available',
  tableCaption,
  dataTestId,
}: DataTableProps<TData, TValue>) {
  const [internalRowSelection, setInternalRowSelection] = useState<RowSelectionState>({})

  const selectionState = rowSelection ?? internalRowSelection

  const tableSortingState = sortingState ?? getSortingState(sorting)

  const selectionColumn: ColumnDef<TData, TValue> = useMemo(
    () => ({
      id: '_select',
      header: ({ table }: { table: TableType<TData> }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && 'indeterminate')}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
          data-testid="select-all-checkbox"
        />
      ),
      cell: ({ row }: { row: Row<TData> }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
          data-testid="row-checkbox"
        />
      ),
      enableSorting: false,
      enableHiding: false,
      size: 40,
    }),
    [],
  )

  const tableColumns = useMemo(
    () => (enableRowSelection ? [selectionColumn, ...columns] : columns),
    [enableRowSelection, selectionColumn, columns],
  )

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: {
      sorting: tableSortingState,
      rowSelection: selectionState,
    },
    enableSortingRemoval: false,
    enableRowSelection,
    enableMultiSort: multiSort,
    onSortingChange: (updater) =>
      applySortingChange(updater, {
        table,
        onSortingChange,
        onSortingStateChange,
        onClearSorting,
        multiSort,
      }),
    onRowSelectionChange: (updater) => {
      const nextState =
        typeof updater === 'function' ? updater(selectionState) : (updater as RowSelectionState)
      
      // Update internal state if uncontrolled
      if (!rowSelection) {
        setInternalRowSelection(nextState)
      }
      
      // Always propagate to external consumer if provided
      if (onRowSelectionChange) {
        const selectedRowModel = table.getSelectedRowModel()
        const selectedRows = selectedRowModel.rows.map((row) => row.original as TData)
        const selectedIds = selectedRowModel.rows.map((row) => row.id)
        
        onRowSelectionChange({
          state: nextState,
          selectedRows,
          selectedIds,
          selectedRowModel,
        })
      }
    },
    getRowId: (originalRow, index, parent) => {
      if (getRowId) {
        return getRowId(originalRow, index, parent)
      }
      const candidate = (originalRow as { id?: string | number } | undefined)?.id
      if (typeof candidate === 'string' && candidate) {
        return candidate
      }
      if (typeof candidate === 'number') {
        return String(candidate)
      }
      return String(index)
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  })


  const currentPage = pagination?.page ?? 1
  const currentPageSize = pagination?.page_size ?? Number(PAGE_SIZE_OPTIONS[0])
  const totalPages = pagination?.total_pages ?? 1
  const totalItems = pagination?.total ?? data.length

  const handlePageChange = (page: number) => {
    if (!onPaginationChange) return
    const nextPage = Math.min(Math.max(page, 1), totalPages)
    if (nextPage !== currentPage) {
      onPaginationChange(nextPage, currentPageSize)
    }
  }

  const handlePageSizeChange = (pageSize: number) => {
    onPaginationChange?.(1, pageSize)
  }

  const columnCount = table.getVisibleLeafColumns().length

  return (
    <div className="space-y-4" data-testid={dataTestId || "data-table"}>
      <div className="rounded-md border">
        <Table data-testid="table">
          {tableCaption && <TableCaption>{tableCaption}</TableCaption>}
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup: HeaderGroup<TData>) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header: Header<TData, unknown>) => {
                  if (!header.isPlaceholder) {
                    const canSort = header.column.getCanSort()
                    const sortState = header.column.getIsSorted()
                    const ariaSort = sortState === 'asc' ? 'ascending' : sortState === 'desc' ? 'descending' : undefined
                    
                    return (
                      <TableHead 
                        key={header.id} 
                        style={{ width: header.getSize() }} 
                        data-testid={`column-${header.column.id}`}
                        aria-sort={ariaSort}
                      >
                        {canSort ? (
                          <button
                            type="button"
                            className="flex items-center"
                            onClick={() => header.column.toggleSorting(header.column.getIsSorted() === 'asc')}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {renderSortingIndicator(header.column.id, table)}
                          </button>
                        ) : (
                          flexRender(header.column.columnDef.header, header.getContext())
                        )}
                      </TableHead>
                    )
                  }
                  return <TableHead key={header.id} />
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              renderSkeletonRows(columnCount)
            ) : table.getRowModel().rows?.length ? (
              table
                .getRowModel()
                .rows.map((row: Row<TData>) => (
                  <TableRow key={row.id} data-state={row.getIsSelected() ? 'selected' : undefined} data-testid="table-row">
                    {row.getVisibleCells().map((cell: Cell<TData, unknown>) => (
                      <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                    ))}
                  </TableRow>
                ))
            ) : (
              <TableRow data-testid="table-empty-state">
                <TableCell colSpan={columnCount} className="h-24 text-center">
                  <Badge variant="secondary">{emptyMessage}</Badge>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground" data-testid="pagination-info">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <Badge variant="outline">{totalItems} items</Badge>
        </div>

        <div className="flex flex-col items-center gap-3 md:flex-row">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Rows per page</span>
            <Select value={String(currentPageSize)} onValueChange={(value) => handlePageSizeChange(Number(value))}>
              <SelectTrigger className="h-9 w-[90px]" data-testid="page-size-select">
                <SelectValue placeholder={currentPageSize} />
              </SelectTrigger>
              <SelectContent>
                {PAGE_SIZE_OPTIONS.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => handlePageChange(1)}
              disabled={currentPage <= 1}
              data-testid="first-page-button"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              data-testid="prev-page-button"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              data-testid="next-page-button"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage >= totalPages}
              data-testid="last-page-button"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
