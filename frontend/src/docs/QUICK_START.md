# Quick Start Guide

This guide provides step-by-step instructions for implementing common features in the KRAI Dashboard.

## Table of Contents

- [Creating a New CRUD Page](#creating-a-new-crud-page)
- [Adding a New Form](#adding-a-new-form)
- [Implementing Batch Operations](#implementing-batch-operations)
- [Adding Navigation Items](#adding-navigation-items)
- [Code Review Checklist](#code-review-checklist)

---

## Creating a New CRUD Page

Follow these steps to create a complete CRUD (Create, Read, Update, Delete) page.

### Step 1: Create API Hooks

Create a new file: `frontend/src/api/items.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export type Item = {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

export type CreateItemInput = Omit<Item, 'id' | 'created_at' | 'updated_at'>
export type UpdateItemInput = Partial<CreateItemInput>

// Fetch all items
export function useItems(filters?: any) {
  return useQuery({
    queryKey: ['items', filters],
    queryFn: () => apiClient.get('/items', { params: filters })
  })
}

// Fetch single item
export function useItem(id: string) {
  return useQuery({
    queryKey: ['items', id],
    queryFn: () => apiClient.get(`/items/${id}`),
    enabled: !!id
  })
}

// Create item
export function useCreateItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateItemInput) => apiClient.post('/items', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
  })
}

// Update item
export function useUpdateItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateItemInput }) =>
      apiClient.patch(`/items/${id}`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
  })
}

// Delete item
export function useDeleteItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/items/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
  })
}
```

### Step 2: Create Form Component

Create a new file: `frontend/src/components/forms/ItemForm.tsx`

```typescript
import { forwardRef, useImperativeHandle } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { TextFieldTemplate, SelectFieldTemplate } from '@/components/forms/FormFieldTemplates'

const itemSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  status: z.enum(['active', 'inactive'])
})

type ItemFormData = z.infer<typeof itemSchema>

type ItemFormProps = {
  mode: 'create' | 'edit'
  initialData?: ItemFormData | null
  onSubmit: (data: ItemFormData) => void | Promise<void>
}

export type ItemFormHandle = {
  submit: () => void
}

export const ItemForm = forwardRef<ItemFormHandle, ItemFormProps>(
  ({ mode, initialData, onSubmit }, ref) => {
    const {
      register,
      handleSubmit,
      control,
      formState: { errors }
    } = useForm<ItemFormData>({
      resolver: zodResolver(itemSchema),
      defaultValues: initialData ?? { status: 'active' }
    })

    useImperativeHandle(ref, () => ({
      submit: () => {
        handleSubmit(onSubmit)()
      }
    }))

    return (
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <TextFieldTemplate
          id="name"
          label="Name"
          required
          error={errors.name}
          register={register('name')}
        />

        <TextFieldTemplate
          id="description"
          label="Description"
          error={errors.description}
          register={register('description')}
        />

        <SelectFieldTemplate
          label="Status"
          required
          error={errors.status}
          value={control._formValues.status}
          onValueChange={(value) => control._formState.isDirty && control._subjects.state.next()}
          options={[
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' }
          ]}
        />
      </form>
    )
  }
)

ItemForm.displayName = 'ItemForm'
```

### Step 3: Create Page Component

Create a new file: `frontend/src/pages/ItemsPage.tsx`

```typescript
import { useState, useRef } from 'react'
import { toast } from 'sonner'
import { ColumnDef } from '@tanstack/react-table'
import { MoreHorizontal, Plus, Edit, Trash } from 'lucide-react'
import { DataTable } from '@/components/shared/DataTable'
import { CrudModal } from '@/components/shared/CrudModal'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useItems, useCreateItem, useUpdateItem, useDeleteItem, Item } from '@/api/items'
import { ItemForm, ItemFormHandle } from '@/components/forms/ItemForm'
import { TOAST_MESSAGES } from '@/lib/toast-messages'

type ModalState = {
  open: boolean
  mode: 'create' | 'edit'
  data?: Item | null
}

export function ItemsPage() {
  const formRef = useRef<ItemFormHandle>(null)
  const [modalState, setModalState] = useState<ModalState>({ open: false, mode: 'create' })
  const [deleteConfirm, setDeleteConfirm] = useState({ open: false, id: '', name: '' })

  const { data, isLoading } = useItems()
  const createMutation = useCreateItem()
  const updateMutation = useUpdateItem()
  const deleteMutation = useDeleteItem()

  const handleCreate = () => setModalState({ open: true, mode: 'create', data: null })
  
  const handleEdit = (item: Item) => setModalState({ open: true, mode: 'edit', data: item })
  
  const handleDeleteClick = (item: Item) =>
    setDeleteConfirm({ open: true, id: item.id, name: item.name })

  const handleFormSubmit = async (formData: any) => {
    try {
      const response = modalState.mode === 'create'
        ? await createMutation.mutateAsync(formData)
        : await updateMutation.mutateAsync({ id: modalState.data!.id, data: formData })

      if (!response.success) throw new Error(response.message)

      const message = TOAST_MESSAGES[modalState.mode === 'create' ? 'CREATE_SUCCESS' : 'UPDATE_SUCCESS']('Item')
      toast.success(message.title, { description: message.description })
      setModalState({ open: false, mode: 'create', data: null })
    } catch (error) {
      const message = TOAST_MESSAGES[modalState.mode === 'create' ? 'CREATE_FAILED' : 'UPDATE_FAILED']('Item')
      toast.error(message.title, { description: message.description })
    }
  }

  const handleDeleteConfirm = async () => {
    try {
      await deleteMutation.mutateAsync(deleteConfirm.id)
      const message = TOAST_MESSAGES.DELETE_SUCCESS('Item')
      toast.success(message.title, { description: message.description })
      setDeleteConfirm({ open: false, id: '', name: '' })
    } catch (error) {
      const message = TOAST_MESSAGES.DELETE_FAILED('Item')
      toast.error(message.title, { description: message.description })
    }
  }

  const columns: ColumnDef<Item>[] = [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => <span className="font-medium">{row.original.name}</span>
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge variant={row.original.status === 'active' ? 'default' : 'secondary'}>
          {row.original.status}
        </Badge>
      )
    },
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
            <DropdownMenuItem onSelect={() => handleEdit(row.original)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive"
              onSelect={() => handleDeleteClick(row.original)}
            >
              <Trash className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    }
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Items</h1>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Create Item
        </Button>
      </div>

      <DataTable columns={columns} data={data?.items ?? []} isLoading={isLoading} />

      <CrudModal
        open={modalState.open}
        mode={modalState.mode}
        title={modalState.mode === 'create' ? 'Create Item' : 'Edit Item'}
        description="Fill in the details below."
        onSubmit={() => formRef.current?.submit()}
        onCancel={() => setModalState({ open: false, mode: 'create', data: null })}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      >
        <ItemForm
          ref={formRef}
          mode={modalState.mode}
          initialData={modalState.data}
          onSubmit={handleFormSubmit}
        />
      </CrudModal>

      <ConfirmDialog
        open={deleteConfirm.open}
        title="Delete Item?"
        description={`This will permanently delete "${deleteConfirm.name}". This action cannot be undone.`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteConfirm({ open: false, id: '', name: '' })}
      />
    </div>
  )
}
```

### Step 4: Add Route

Update `frontend/src/App.tsx`:

```typescript
import { ItemsPage } from '@/pages/ItemsPage'

// In your routes
<Route path="/items" element={<ItemsPage />} />
```

### Step 5: Add Navigation

Update `frontend/src/components/layout/Sidebar.tsx`:

```typescript
import { Package } from 'lucide-react'

const navigationItems = [
  // ... existing items
  { label: 'Items', icon: Package, href: '/items', roles: ['admin', 'editor'] }
]
```

---

## Adding a New Form

For standalone forms (not part of a CRUD page):

1. Define zod schema
2. Create form component with `forwardRef`
3. Use `FormFieldTemplates` for fields
4. Implement error handling
5. Add loading states

See [Form Patterns](./FORM_PATTERNS.md) for detailed examples.

---

## Implementing Batch Operations

### Step 1: Enable Row Selection

```typescript
const [selectedRows, setSelectedRows] = useState<Item[]>([])

<DataTable
  columns={columns}
  data={data}
  enableRowSelection
  onRowSelectionChange={setSelectedRows}
/>
```

### Step 2: Add Batch Actions Toolbar

```typescript
import { BatchActionsToolbar } from '@/components/shared/BatchActionsToolbar'

{selectedRows.length > 0 && (
  <BatchActionsToolbar
    selectedCount={selectedRows.length}
    onDelete={handleBatchDelete}
    onClearSelection={() => setSelectedRows([])}
  />
)}
```

### Step 3: Implement Batch Mutation

```typescript
const batchDeleteMutation = useMutation({
  mutationFn: (ids: string[]) => apiClient.post('/items/batch-delete', { ids }),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] })
})

const handleBatchDelete = async () => {
  try {
    const ids = selectedRows.map(row => row.id)
    await batchDeleteMutation.mutateAsync(ids)
    toast.success(`${ids.length} items deleted`)
    setSelectedRows([])
  } catch (error) {
    toast.error('Batch delete failed')
  }
}
```

---

## Adding Navigation Items

### Step 1: Define Navigation Item

```typescript
import { Package } from 'lucide-react'

const newItem = {
  label: 'Items',
  icon: Package,
  href: '/items',
  roles: ['admin', 'editor', 'viewer']
}
```

### Step 2: Add to Sidebar

Update `frontend/src/components/layout/Sidebar.tsx`:

```typescript
const navigationItems = [
  // ... existing items
  newItem
]
```

### Step 3: Verify Role-Based Access

The `getVisibleNavigationItems` helper will automatically filter based on user role.

---

## Code Review Checklist

Before submitting your code for review:

- [ ] Design tokens used (no hardcoded colors/spacing)
- [ ] TanStack Query for server state
- [ ] react-hook-form + zod for forms
- [ ] Error handling with try-catch + toast
- [ ] Loading states with skeletons/spinners
- [ ] data-testid attributes added
- [ ] TypeScript types defined
- [ ] No ESLint warnings
- [ ] Tests written and passing
- [ ] Documentation updated

See [Code Review Checklist](../CODE_REVIEW_CHECKLIST.md) for complete list.

---

## Related Documentation

- [Interaction Patterns](./INTERACTION_PATTERNS.md) - Master pattern guide
- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
- [Contributing Guidelines](../CONTRIBUTING.md) - Code style and workflow
