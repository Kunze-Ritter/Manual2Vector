# Interaction Patterns - Master Guide

This is the master documentation for all interaction patterns in the KRAI Dashboard. Use this as your starting point for understanding and implementing consistent UI patterns.

## Table of Contents

- [Overview](#overview)
- [Pattern Documentation](#pattern-documentation)
- [Decision Tree](#decision-tree)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)
- [Anti-Patterns](#anti-patterns)

---

## Overview

The KRAI Dashboard follows consistent interaction patterns across all features. This ensures:

- **Predictable UX** - Users know what to expect
- **Faster Development** - Reuse proven patterns
- **Easier Maintenance** - Changes propagate consistently
- **Better Quality** - Tested patterns reduce bugs

### Core Principles

1. **Design Tokens Over Hardcoded Values** - Use theme tokens for colors, spacing, typography
2. **Server State with TanStack Query** - Centralized data fetching and caching
3. **Form State with react-hook-form + zod** - Type-safe validation
4. **Optimistic Updates** - Immediate feedback, background sync
5. **Consistent Error Handling** - try-catch + toast notifications
6. **Loading States** - Skeleton components for content, spinners for actions

---

## Pattern Documentation

### Core Patterns

- **[Navigation Patterns](./NAVIGATION_PATTERNS.md)** - Sidebar, Header, role-based access
- **[Form Patterns](./FORM_PATTERNS.md)** - Form architecture, validation, submission
- **[Table Patterns](./TABLE_PATTERNS.md)** - DataTable, sorting, pagination, row selection
- **[Modal Patterns](./MODAL_PATTERNS.md)** - CrudModal, AlertDialog, confirmations
- **[Error Handling](./ERROR_HANDLING.md)** - try-catch, toast notifications, error boundaries
- **[Loading States](./LOADING_STATES.md)** - Skeletons, spinners, loading indicators

### Component Reference

- **[Component Library](./COMPONENT_LIBRARY.md)** - Complete UI component reference
- **[Testing Patterns](./TESTING_PATTERNS.md)** - Testing strategies and conventions

### Contribution

- **[Quick Start Guide](./QUICK_START.md)** - Step-by-step for new features
- **[Contributing Guidelines](../CONTRIBUTING.md)** - Code style and workflow
- **[Code Review Checklist](../CODE_REVIEW_CHECKLIST.md)** - Review criteria

---

## Decision Tree

### I need to create a new feature...

```
What type of feature?
├─ CRUD Page (List + Create + Edit + Delete)
│  ├─ 1. Create API hooks with TanStack Query
│  ├─ 2. Create form component with react-hook-form + zod
│  ├─ 3. Create page with FilterBar + DataTable + CrudModal
│  ├─ 4. Add navigation item to Sidebar
│  └─ 5. Add tests with data-testid attributes
│
├─ Form Only
│  ├─ 1. Define zod schema
│  ├─ 2. Create form component with forwardRef
│  ├─ 3. Use FormFieldTemplates for consistent fields
│  ├─ 4. Implement error handling with toast
│  └─ 5. Add loading states to submit button
│
├─ Data Display (Read-Only)
│  ├─ 1. Create API hook with useQuery
│  ├─ 2. Create DataTable with columns
│  ├─ 3. Add FilterBar if needed
│  ├─ 4. Implement loading state with skeleton
│  └─ 5. Handle errors with Alert component
│
└─ Batch Operation
   ├─ 1. Enable row selection in DataTable
   ├─ 2. Add BatchActionsToolbar
   ├─ 3. Create batch mutation hook
   ├─ 4. Add ConfirmDialog for destructive actions
   └─ 5. Show toast on success/error
```

### I need to handle...

```
What needs handling?
├─ User Input
│  └─ Use react-hook-form + zod validation
│
├─ Data Fetching
│  └─ Use TanStack Query (useQuery)
│
├─ Data Mutation
│  └─ Use TanStack Query (useMutation) + try-catch + toast
│
├─ Loading State
│  ├─ Content: Skeleton components
│  └─ Actions: Button with Loader2 icon
│
├─ Error State
│  ├─ Query: Alert component
│  └─ Mutation: toast.error()
│
└─ Confirmation
   └─ Use ConfirmDialog or AlertDialog
```

---

## Common Patterns

### CRUD Page Template

```tsx
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { DataTable } from '@/components/shared/DataTable'
import { FilterBar } from '@/components/shared/FilterBar'
import { CrudModal } from '@/components/shared/CrudModal'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

type ModalState = {
  open: boolean
  mode: 'create' | 'edit'
  data?: Item | null
}

export function ItemsPage() {
  const queryClient = useQueryClient()
  const formRef = useRef<FormHandle>(null)
  
  // State
  const [modalState, setModalState] = useState<ModalState>({ open: false, mode: 'create' })
  const [deleteConfirm, setDeleteConfirm] = useState({ open: false, id: null, name: '' })
  const [filters, setFilters] = useState({})
  
  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['items', filters],
    queryFn: () => fetchItems(filters)
  })
  
  // Mutations
  const createMutation = useMutation({
    mutationFn: createItem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
  })
  
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateItem(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
  })
  
  const deleteMutation = useMutation({
    mutationFn: deleteItem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
  })
  
  // Handlers
  const handleCreate = () => setModalState({ open: true, mode: 'create', data: null })
  const handleEdit = (item: Item) => setModalState({ open: true, mode: 'edit', data: item })
  const handleDeleteClick = (item: Item) => setDeleteConfirm({ open: true, id: item.id, name: item.name })
  
  const handleFormSubmit = async (data: FormData) => {
    try {
      const response = modalState.mode === 'create'
        ? await createMutation.mutateAsync(data)
        : await updateMutation.mutateAsync({ id: modalState.data.id, data })
      
      if (!response.success) throw new Error(response.message)
      
      toast.success(modalState.mode === 'create' ? 'Item created' : 'Item updated')
      setModalState({ open: false, mode: 'create', data: null })
    } catch (error) {
      toast.error('Operation failed', { description: error.message })
    }
  }
  
  const handleDeleteConfirm = async () => {
    try {
      await deleteMutation.mutateAsync(deleteConfirm.id)
      toast.success('Item deleted')
      setDeleteConfirm({ open: false, id: null, name: '' })
    } catch (error) {
      toast.error('Delete failed', { description: error.message })
    }
  }
  
  // Columns
  const columns = [
    { accessorKey: 'name', header: 'Name' },
    { accessorKey: 'status', header: 'Status', cell: ({ row }) => <Badge>{row.original.status}</Badge> },
    {
      id: '_actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreHorizontal /></Button></DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={() => handleEdit(row.original)}>Edit</DropdownMenuItem>
            <DropdownMenuItem className="text-destructive" onSelect={() => handleDeleteClick(row.original)}>Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    }
  ]
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Items</h1>
        <Button onClick={handleCreate}><Plus className="mr-2 h-4 w-4" />Create Item</Button>
      </div>
      
      <FilterBar filters={filters} onFiltersChange={setFilters} />
      
      <DataTable columns={columns} data={data?.items ?? []} isLoading={isLoading} />
      
      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalState.mode === 'create' ? 'Create Item' : 'Edit Item'}
        onSubmit={() => formRef.current?.submit()}
        onCancel={() => setModalState({ open: false, mode: 'create', data: null })}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      >
        <ItemForm ref={formRef} mode={modalState.mode} initialData={modalState.data} onSubmit={handleFormSubmit} />
      </CrudModal>
      
      <ConfirmDialog
        open={deleteConfirm.open}
        title="Delete Item?"
        description={`This will permanently delete "${deleteConfirm.name}".`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteConfirm({ open: false, id: null, name: '' })}
      />
    </div>
  )
}
```

---

## Best Practices

### 1. Design Tokens

✅ **DO:**
```tsx
<div className="p-md gap-sm bg-background text-foreground">
```

❌ **DON'T:**
```tsx
<div style={{ padding: '16px', gap: '8px', background: '#ffffff', color: '#000000' }}>
```

### 2. Server State

✅ **DO:**
```tsx
const { data, isLoading } = useQuery({ queryKey: ['items'], queryFn: fetchItems })
```

❌ **DON'T:**
```tsx
const [data, setData] = useState([])
useEffect(() => { fetchItems().then(setData) }, [])
```

### 3. Form Validation

✅ **DO:**
```tsx
const schema = z.object({ name: z.string().min(1, 'Name is required') })
const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) })
```

❌ **DON'T:**
```tsx
const [errors, setErrors] = useState({})
const validate = () => { if (!name) setErrors({ name: 'Required' }) }
```

### 4. Error Handling

✅ **DO:**
```tsx
try {
  const response = await mutation.mutateAsync(data)
  if (!response.success) throw new Error(response.message)
  toast.success('Success')
} catch (error) {
  toast.error('Failed', { description: error.message })
}
```

❌ **DON'T:**
```tsx
mutation.mutateAsync(data).then(response => {
  alert('Success')
}).catch(error => {
  console.log(error)
})
```

### 5. Loading States

✅ **DO:**
```tsx
{isLoading ? <SkeletonTable rows={10} cols={5} /> : <DataTable data={data} />}
```

❌ **DON'T:**
```tsx
{isLoading ? <div>Loading...</div> : <DataTable data={data} />}
```

---

## Anti-Patterns

### ❌ Inline Styles

Never use inline styles - always use Tailwind classes or design tokens.

### ❌ Hardcoded Colors/Spacing

Never hardcode colors or spacing values - use theme tokens.

### ❌ Unhandled Promises

Always handle promise rejections with try-catch or .catch().

### ❌ Uncontrolled Forms

Always use react-hook-form for form state management.

### ❌ Direct DOM Manipulation

Never use document.querySelector or direct DOM manipulation - use React state.

### ❌ Prop Drilling

Avoid passing props through multiple levels - use Context or state management.

### ❌ Missing data-testid

Always add data-testid attributes for testing.

### ❌ Console.log in Production

Remove console.log statements before committing.

---

## Related Documentation

- [Quick Start Guide](./QUICK_START.md) - Step-by-step for new features
- [Component Library](./COMPONENT_LIBRARY.md) - Complete component reference
- [Contributing Guidelines](../CONTRIBUTING.md) - Code style and workflow
