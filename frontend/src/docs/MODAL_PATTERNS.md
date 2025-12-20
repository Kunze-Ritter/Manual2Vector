# Modal Patterns

This document describes the modal patterns used throughout the KRAI Dashboard, including CrudModal for form operations and AlertDialog for confirmations.

## Table of Contents

- [CrudModal Pattern](#crudmodal-pattern)
- [Modal State Management](#modal-state-management)
- [Form Integration](#form-integration)
- [Submit Flow](#submit-flow)
- [Loading States](#loading-states)
- [Cancel Handling](#cancel-handling)
- [AlertDialog Pattern](#alertdialog-pattern)
- [ConfirmDialog Component](#confirmdialog-component)
- [Best Practices](#best-practices)

---

## CrudModal Pattern

The CrudModal component provides a consistent interface for create and edit operations.

### CrudModal Props

```tsx
type CrudModalProps = {
  open: boolean
  mode: 'create' | 'edit'
  title: string
  description?: string
  children: ReactNode
  onSubmit: () => void
  onCancel: () => void
  isSubmitting?: boolean
  submitLabel?: string
  cancelLabel?: string
}
```

### Basic Usage

```tsx
<CrudModal
  open={modalState.open}
  mode={modalState.mode}
  title={modalState.mode === 'create' ? 'Create Document' : 'Edit Document'}
  description="Fill in the details below."
  onSubmit={() => formRef.current?.submit()}
  onCancel={handleCancel}
  isSubmitting={mutation.isPending}
>
  <DocumentForm
    ref={formRef}
    mode={modalState.mode}
    initialData={modalState.data}
    onSubmit={handleFormSubmit}
  />
</CrudModal>
```

---

## Modal State Management

Use a structured state object to manage modal visibility and data.

### Modal State Type

```tsx
type ModalState<T = any> = {
  open: boolean
  mode: 'create' | 'edit'
  data?: T | null
}
```

### State Management Pattern

```tsx
const [modalState, setModalState] = useState<ModalState<Document>>({
  open: false,
  mode: 'create',
  data: null
})

// Open for create
const handleCreate = () => {
  setModalState({
    open: true,
    mode: 'create',
    data: null
  })
}

// Open for edit
const handleEdit = (document: Document) => {
  setModalState({
    open: true,
    mode: 'edit',
    data: document
  })
}

// Close modal
const handleCancel = () => {
  setModalState({
    open: false,
    mode: 'create',
    data: null
  })
}

// Reset after successful operation
const resetModal = () => {
  setModalState({
    open: false,
    mode: 'create',
    data: null
  })
}
```

---

## Form Integration

Forms are integrated with modals using `forwardRef` and `useImperativeHandle`.

### Form Handle Type

```tsx
export type FormHandle = {
  submit: () => void
}
```

### Form Component with Ref

```tsx
export const DocumentForm = forwardRef<FormHandle, DocumentFormProps>(
  ({ mode, initialData, onSubmit }, ref) => {
    const { handleSubmit, ...formMethods } = useForm<FormData>({
      defaultValues: initialData ?? {}
    })

    useImperativeHandle(ref, () => ({
      submit: () => {
        handleSubmit(onSubmit)()
      }
    }))

    return (
      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Form fields */}
      </form>
    )
  }
)
```

### Using Form Ref in Modal

```tsx
const formRef = useRef<FormHandle>(null)

<CrudModal
  open={modalState.open}
  mode={modalState.mode}
  title="Create Document"
  onSubmit={() => formRef.current?.submit()}
  onCancel={handleCancel}
>
  <DocumentForm
    ref={formRef}
    mode={modalState.mode}
    initialData={modalState.data}
    onSubmit={handleFormSubmit}
  />
</CrudModal>
```

---

## Submit Flow

### Complete Submit Flow

```tsx
const handleFormSubmit = async (data: FormData) => {
  try {
    // 1. Build payload
    const payload = buildPayload(data, modalState.mode)

    // 2. Call mutation
    const response = modalState.mode === 'create'
      ? await createMutation.mutateAsync(payload)
      : await updateMutation.mutateAsync(payload)

    // 3. Validate response
    if (!response.success || !response.data) {
      throw new Error(response.message ?? 'Operation failed')
    }

    // 4. Show success toast
    toast.success(
      modalState.mode === 'create' ? 'Document created' : 'Document updated',
      { description: 'Changes saved successfully.' }
    )

    // 5. Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: ['documents'] })

    // 6. Reset modal state
    resetModal()

  } catch (error) {
    // 7. Handle errors
    const message = error instanceof Error ? error.message : 'Unexpected error'
    toast.error('Operation failed', { description: message })
  }
}
```

---

## Loading States

### Disable Submit During Loading

```tsx
<CrudModal
  open={modalState.open}
  mode={modalState.mode}
  title="Create Document"
  onSubmit={() => formRef.current?.submit()}
  onCancel={handleCancel}
  isSubmitting={mutation.isPending}  // Disables submit button
>
  <DocumentForm ref={formRef} {...formProps} />
</CrudModal>
```

### Loading Indicator in Submit Button

```tsx
<Button disabled={isSubmitting}>
  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
  {isSubmitting ? 'Saving...' : 'Save'}
</Button>
```

---

## Cancel Handling

### Simple Cancel

```tsx
const handleCancel = () => {
  setModalState({ open: false, mode: 'create', data: null })
}

<CrudModal
  open={modalState.open}
  onCancel={handleCancel}
  onOpenChange={(open) => !open && handleCancel()}  // Handle ESC/backdrop click
>
  {/* Modal content */}
</CrudModal>
```

### Cancel with Unsaved Changes Warning

```tsx
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

const handleCancel = () => {
  if (hasUnsavedChanges) {
    if (confirm('You have unsaved changes. Are you sure you want to close?')) {
      resetModal()
    }
  } else {
    resetModal()
  }
}
```

---

## AlertDialog Pattern

Use AlertDialog for destructive actions that require confirmation.

### Delete Confirmation Pattern

```tsx
type DeleteConfirmState = {
  open: boolean
  id: string | null
  name?: string
}

const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmState>({
  open: false,
  id: null,
  name: undefined
})

const handleDeleteClick = (item: Document) => {
  setDeleteConfirm({
    open: true,
    id: item.id,
    name: item.name
  })
}

const handleDeleteConfirm = async () => {
  if (!deleteConfirm.id) return

  try {
    await deleteMutation.mutateAsync(deleteConfirm.id)
    toast.success('Document deleted', { description: 'The document has been removed.' })
    setDeleteConfirm({ open: false, id: null, name: undefined })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unexpected error'
    toast.error('Delete failed', { description: message })
  }
}

<AlertDialog open={deleteConfirm.open} onOpenChange={(open) => !open && setDeleteConfirm({ open: false, id: null })}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Are you sure?</AlertDialogTitle>
      <AlertDialogDescription>
        This will permanently delete "{deleteConfirm.name}". This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        onClick={handleDeleteConfirm}
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
      >
        Delete
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

### Batch Delete Pattern

```tsx
const [batchDeleteConfirm, setBatchDeleteConfirm] = useState({
  open: false,
  count: 0
})

const handleBatchDeleteClick = () => {
  setBatchDeleteConfirm({
    open: true,
    count: selectedRows.length
  })
}

const handleBatchDeleteConfirm = async () => {
  try {
    const ids = selectedRows.map(row => row.id)
    await batchDeleteMutation.mutateAsync(ids)
    toast.success('Documents deleted', { description: `${ids.length} documents removed.` })
    setBatchDeleteConfirm({ open: false, count: 0 })
    setSelectedRows([])
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unexpected error'
    toast.error('Batch delete failed', { description: message })
  }
}

<AlertDialog open={batchDeleteConfirm.open} onOpenChange={(open) => !open && setBatchDeleteConfirm({ open: false, count: 0 })}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete {batchDeleteConfirm.count} items?</AlertDialogTitle>
      <AlertDialogDescription>
        This will permanently delete {batchDeleteConfirm.count} selected items. This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        onClick={handleBatchDeleteConfirm}
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
      >
        Delete All
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

---

## ConfirmDialog Component

Use the reusable ConfirmDialog component for consistent confirmation dialogs.

### ConfirmDialog Usage

```tsx
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'

<ConfirmDialog
  open={deleteConfirm.open}
  title="Delete Document?"
  description={`This will permanently delete "${deleteConfirm.name}". This action cannot be undone.`}
  confirmLabel="Delete"
  variant="destructive"
  onConfirm={handleDeleteConfirm}
  onCancel={() => setDeleteConfirm({ open: false, id: null, name: undefined })}
/>
```

### ConfirmDialog Props

```tsx
type ConfirmDialogProps = {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'default' | 'destructive'
  onConfirm: () => void | Promise<void>
  onCancel: () => void
}
```

---

## Best Practices

1. **Use structured modal state** - `{ open, mode, data }` pattern
2. **Implement form refs** - Allow external submission via `useImperativeHandle`
3. **Show loading states** - Disable submit button during operations
4. **Validate responses** - Check `response.success` before proceeding
5. **Reset modal after success** - Clear state for next operation
6. **Handle errors gracefully** - Show toast notifications with details
7. **Confirm destructive actions** - Use AlertDialog for delete operations
8. **Provide context in confirmations** - Show item name/count in messages
9. **Invalidate queries after mutations** - Keep data fresh
10. **Handle ESC/backdrop clicks** - Use `onOpenChange` for proper cleanup

---

## Related Documentation

- [Form Patterns](./FORM_PATTERNS.md) - Form integration details
- [Error Handling](./ERROR_HANDLING.md) - Error handling patterns
- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
- [ConfirmDialog Component](../components/shared/ConfirmDialog.tsx) - Reusable confirmation dialog
