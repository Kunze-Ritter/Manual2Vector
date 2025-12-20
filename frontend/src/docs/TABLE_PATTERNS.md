# DataTable Patterns

This document describes the DataTable patterns used throughout the KRAI Dashboard, including column definitions, sorting, pagination, row selection, and custom cell renderers.

## Table of Contents

- [DataTable Props Overview](#datatable-props-overview)
- [Column Definition Patterns](#column-definition-patterns)
- [Sorting Pattern](#sorting-pattern)
- [Pagination Pattern](#pagination-pattern)
- [Row Selection Pattern](#row-selection-pattern)
- [Loading States](#loading-states)
- [Empty States](#empty-states)
- [Action Column Pattern](#action-column-pattern)
- [Custom Cell Patterns](#custom-cell-patterns)
- [Best Practices](#best-practices)

---

## DataTable Props Overview

The DataTable component accepts the following key props:

```tsx
type DataTableProps<TData> = {
  // Required
  columns: ColumnDef<TData>[]
  data: TData[]

  // Optional
  isLoading?: boolean
  pagination?: DataTablePagination
  onPaginationChange?: (page: number, pageSize: number) => void
  enableRowSelection?: boolean
  onRowSelectionChange?: (selectedRows: TData[]) => void
  emptyMessage?: string
}
```

### Standard Usage

```tsx
<DataTable
  columns={columns}
  data={documents}
  isLoading={isLoading}
  pagination={paginationMeta}
  onPaginationChange={handlePaginationChange}
  enableRowSelection
  onRowSelectionChange={handleRowSelectionChange}
  emptyMessage="No documents found"
/>
```

---

## Column Definition Patterns

Columns are defined using TanStack Table's `ColumnDef` type.

### Basic Column

```tsx
import { ColumnDef } from '@tanstack/react-table'

const columns: ColumnDef<Document>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => <span className="font-medium">{row.original.name}</span>
  }
]
```

### Column with Sorting

```tsx
{
  accessorKey: 'created_at',
  header: 'Created',
  enableSorting: true,
  cell: ({ row }) => format(new Date(row.original.created_at), 'PPP')
}
```

### Column with Custom Header

```tsx
{
  accessorKey: 'status',
  header: ({ column }) => (
    <Button
      variant="ghost"
      onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
    >
      Status
      <ArrowUpDown className="ml-2 h-4 w-4" />
    </Button>
  ),
  cell: ({ row }) => <StatusBadge status={row.original.status} />
}
```

### Column without Sorting

```tsx
{
  id: '_actions',
  header: '',
  enableSorting: false,
  cell: ({ row }) => <ActionMenu item={row.original} />
}
```

---

## Sorting Pattern

### Server-Side Sorting

```tsx
const [sorting, setSorting] = useState<SortingState>([])

const { data, isLoading } = useQuery({
  queryKey: ['documents', sorting],
  queryFn: () => fetchDocuments({
    sortBy: sorting[0]?.id,
    sortOrder: sorting[0]?.desc ? 'desc' : 'asc'
  })
})

<DataTable
  columns={columns}
  data={data}
  sorting={sorting}
  onSortingChange={setSorting}
/>
```

### Client-Side Sorting

```tsx
const columns: ColumnDef<Document>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    enableSorting: true,
    sortingFn: 'alphanumeric'  // Built-in sorting function
  },
  {
    accessorKey: 'created_at',
    header: 'Created',
    enableSorting: true,
    sortingFn: (rowA, rowB) => {
      const dateA = new Date(rowA.original.created_at).getTime()
      const dateB = new Date(rowB.original.created_at).getTime()
      return dateA - dateB
    }
  }
]
```

---

## Pagination Pattern

### Server-Side Pagination

```tsx
const [pagination, setPagination] = useState({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE
})

const { data, isLoading } = useQuery({
  queryKey: ['documents', pagination],
  queryFn: () => fetchDocuments({
    page: pagination.page,
    pageSize: pagination.pageSize
  })
})

const handlePaginationChange = (page: number, pageSize: number) => {
  setPagination({ page, pageSize })
}

<DataTable
  columns={columns}
  data={data?.items ?? []}
  pagination={{
    page: data?.page ?? 1,
    pageSize: data?.pageSize ?? DEFAULT_PAGE_SIZE,
    totalPages: data?.totalPages ?? 1,
    totalItems: data?.totalItems ?? 0
  }}
  onPaginationChange={handlePaginationChange}
/>
```

### Pagination Defaults

Use the standardized defaults from `DataTableDefaults.ts`:

```tsx
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from '@/components/shared/DataTableDefaults'

// Default page size: 20
// Page size options: [10, 20, 50, 100]
```

---

## Row Selection Pattern

### Enable Row Selection

```tsx
const [selectedRows, setSelectedRows] = useState<Document[]>([])

<DataTable
  columns={columns}
  data={documents}
  enableRowSelection
  onRowSelectionChange={setSelectedRows}
/>
```

### Checkbox Column

The DataTable automatically adds a checkbox column when `enableRowSelection` is true:

```tsx
{
  id: 'select',
  header: ({ table }) => (
    <Checkbox
      checked={table.getIsAllPageRowsSelected()}
      onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
    />
  ),
  cell: ({ row }) => (
    <Checkbox
      checked={row.getIsSelected()}
      onCheckedChange={(value) => row.toggleSelected(!!value)}
    />
  ),
  enableSorting: false
}
```

### Using Selected Rows

```tsx
const handleBatchDelete = async () => {
  const ids = selectedRows.map(row => row.id)
  await deleteMutation.mutateAsync(ids)
  setSelectedRows([])
}

<BatchActionsToolbar
  selectedCount={selectedRows.length}
  onDelete={handleBatchDelete}
  onClearSelection={() => setSelectedRows([])}
/>
```

---

## Loading States

### Skeleton Rows

When `isLoading` is true, the DataTable renders skeleton rows:

```tsx
<DataTable
  columns={columns}
  data={data}
  isLoading={isLoading}  // Shows skeleton rows
/>
```

### Custom Skeleton Count

```tsx
const renderSkeletonRows = (count: number = 10) => (
  Array.from({ length: count }).map((_, i) => (
    <TableRow key={i}>
      {columns.map((col, j) => (
        <TableCell key={j}>
          <Skeleton className="h-6 w-full" />
        </TableCell>
      ))}
    </TableRow>
  ))
)
```

---

## Empty States

### Default Empty State

```tsx
<DataTable
  columns={columns}
  data={[]}
  emptyMessage="No data available"
/>
```

### Custom Empty State

```tsx
{data.length === 0 && !isLoading && (
  <div className="flex flex-col items-center justify-center py-12">
    <FileText className="h-12 w-12 text-muted-foreground mb-4" />
    <p className="text-lg font-medium">No documents found</p>
    <p className="text-sm text-muted-foreground">
      Get started by creating your first document
    </p>
    <Button className="mt-4" onClick={handleCreate}>
      Create Document
    </Button>
  </div>
)}
```

---

## Action Column Pattern

### Dropdown Menu Actions

```tsx
import { MoreHorizontal, Edit, Trash } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'

{
  id: '_actions',
  header: '',
  enableSorting: false,
  cell: ({ row }) => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onSelect={() => onEdit(row.original)}>
          <Edit className="mr-2 h-4 w-4" />
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem 
          className="text-destructive" 
          onSelect={() => onDelete(row.original.id)}
        >
          <Trash className="mr-2 h-4 w-4" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

### Icon Button Actions

```tsx
{
  id: '_actions',
  header: '',
  enableSorting: false,
  cell: ({ row }) => (
    <div className="flex items-center gap-2">
      <Button 
        variant="ghost" 
        size="icon"
        onClick={() => onEdit(row.original)}
      >
        <Edit className="h-4 w-4" />
      </Button>
      <Button 
        variant="ghost" 
        size="icon"
        onClick={() => onDelete(row.original.id)}
      >
        <Trash className="h-4 w-4 text-destructive" />
      </Button>
    </div>
  )
}
```

---

## Custom Cell Patterns

### Badge Cell

```tsx
import { Badge } from '@/components/ui/badge'

{
  accessorKey: 'status',
  header: 'Status',
  cell: ({ row }) => {
    const status = row.original.status
    const variant = {
      active: 'default',
      inactive: 'secondary',
      pending: 'outline',
      error: 'destructive'
    }[status] as any

    return <Badge variant={variant}>{status}</Badge>
  }
}
```

### Icon Cell

```tsx
import { FileText, Package, Users } from 'lucide-react'

{
  accessorKey: 'type',
  header: 'Type',
  cell: ({ row }) => {
    const icons = {
      document: FileText,
      product: Package,
      user: Users
    }
    const Icon = icons[row.original.type as keyof typeof icons]
    
    return (
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span>{row.original.type}</span>
      </div>
    )
  }
}
```

### Date Cell

```tsx
import { format } from 'date-fns'

{
  accessorKey: 'created_at',
  header: 'Created',
  cell: ({ row }) => format(new Date(row.original.created_at), 'PPP')
}
```

### Progress Cell

```tsx
import { Progress } from '@/components/ui/progress'

{
  accessorKey: 'progress',
  header: 'Progress',
  cell: ({ row }) => (
    <div className="flex items-center gap-2">
      <Progress value={row.original.progress} className="w-24" />
      <span className="text-sm text-muted-foreground">
        {row.original.progress}%
      </span>
    </div>
  )
}
```

### Link Cell

```tsx
import { Link } from 'react-router-dom'

{
  accessorKey: 'name',
  header: 'Name',
  cell: ({ row }) => (
    <Link 
      to={`/documents/${row.original.id}`}
      className="font-medium hover:underline"
    >
      {row.original.name}
    </Link>
  )
}
```

### Truncated Text Cell

```tsx
{
  accessorKey: 'description',
  header: 'Description',
  cell: ({ row }) => (
    <span className="max-w-xs truncate block">
      {row.original.description}
    </span>
  )
}
```

---

## Best Practices

1. **Use accessorKey for simple columns** - Automatic data access
2. **Use id for custom columns** - Actions, checkboxes, etc.
3. **Disable sorting for action columns** - `enableSorting: false`
4. **Consistent icon sizing** - Use `h-4 w-4` for cell icons
5. **Server-side pagination for large datasets** - Better performance
6. **Show loading skeletons** - Better UX during data fetching
7. **Provide meaningful empty states** - Guide users on next actions
8. **Use Badge components for status** - Consistent visual language
9. **Format dates consistently** - Use date-fns format functions
10. **Truncate long text** - Prevent layout issues

---

## Related Documentation

- [Loading States](./LOADING_STATES.md) - Skeleton patterns
- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
- [Interaction Patterns](./INTERACTION_PATTERNS.md) - Overall pattern guide
- [DataTable Defaults](../components/shared/DataTableDefaults.ts) - Default values
