# Component Library

Complete reference for all UI components in the KRAI Dashboard.

## Table of Contents

- [UI Components (shadcn/ui)](#ui-components-shadcnui)
- [Shared Components](#shared-components)
- [Form Components](#form-components)
- [Layout Components](#layout-components)

---

## UI Components (shadcn/ui)

### Button

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | 'default' \| 'destructive' \| 'outline' \| 'ghost' | 'default' | Visual style |
| size | 'sm' \| 'md' \| 'lg' | 'md' | Button size |
| disabled | boolean | false | Disabled state |

**Example:**
```tsx
<Button variant="default" size="md">Click me</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline" size="sm">Cancel</Button>
```

### Input

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| type | string | 'text' | Input type |
| placeholder | string | - | Placeholder text |
| disabled | boolean | false | Disabled state |

**Example:**
```tsx
<Input type="text" placeholder="Enter name..." />
<Input type="email" placeholder="email@example.com" />
```

### Select

**Example:**
```tsx
<Select value={value} onValueChange={setValue}>
  <SelectTrigger>
    <SelectValue placeholder="Select..." />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

### Badge

**Variants:** `default`, `secondary`, `destructive`, `outline`

**Example:**
```tsx
<Badge variant="default">Active</Badge>
<Badge variant="destructive">Error</Badge>
```

### Alert

**Example:**
```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>Something went wrong</AlertDescription>
</Alert>
```

---

## Shared Components

### DataTable

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| columns | ColumnDef[] | Yes | Column definitions |
| data | TData[] | Yes | Table data |
| isLoading | boolean | No | Show skeleton rows |
| pagination | DataTablePagination | No | Pagination config |
| enableRowSelection | boolean | No | Enable row selection |

**Example:**
```tsx
<DataTable
  columns={columns}
  data={documents}
  isLoading={isLoading}
  pagination={paginationMeta}
  onPaginationChange={handlePaginationChange}
/>
```

See [Table Patterns](./TABLE_PATTERNS.md) for detailed usage.

### CrudModal

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| open | boolean | Yes | Modal visibility |
| mode | 'create' \| 'edit' | Yes | Operation mode |
| title | string | Yes | Modal title |
| onSubmit | () => void | Yes | Submit handler |
| onCancel | () => void | Yes | Cancel handler |
| isSubmitting | boolean | No | Loading state |

**Example:**
```tsx
<CrudModal
  open={modalState.open}
  mode={modalState.mode}
  title="Create Document"
  onSubmit={() => formRef.current?.submit()}
  onCancel={handleCancel}
  isSubmitting={mutation.isPending}
>
  <DocumentForm ref={formRef} onSubmit={handleSubmit} />
</CrudModal>
```

See [Modal Patterns](./MODAL_PATTERNS.md) for detailed usage.

### ConfirmDialog

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| open | boolean | Yes | Dialog visibility |
| title | string | Yes | Dialog title |
| description | string | Yes | Dialog description |
| variant | 'default' \| 'destructive' | No | Visual style |
| onConfirm | () => void | Yes | Confirm handler |
| onCancel | () => void | Yes | Cancel handler |

**Example:**
```tsx
<ConfirmDialog
  open={deleteConfirm.open}
  title="Delete Document?"
  description="This action cannot be undone."
  variant="destructive"
  onConfirm={handleDelete}
  onCancel={handleCancel}
/>
```

### FilterBar

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| filters | object | Yes | Current filters |
| onFiltersChange | (filters) => void | Yes | Filter change handler |

**Example:**
```tsx
<FilterBar
  filters={filters}
  onFiltersChange={setFilters}
/>
```

### BatchActionsToolbar

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| selectedCount | number | Yes | Number of selected items |
| onDelete | () => void | Yes | Delete handler |
| onClearSelection | () => void | Yes | Clear selection handler |

**Example:**
```tsx
<BatchActionsToolbar
  selectedCount={selectedRows.length}
  onDelete={handleBatchDelete}
  onClearSelection={() => setSelectedRows([])}
/>
```

---

## Form Components

### FormFieldTemplates

Reusable field templates for consistent form layouts.

**TextFieldTemplate:**
```tsx
<TextFieldTemplate
  id="name"
  label="Name"
  required
  error={errors.name}
  register={register('name')}
/>
```

**SelectFieldTemplate:**
```tsx
<SelectFieldTemplate
  label="Status"
  required
  value={value}
  onValueChange={setValue}
  options={[
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' }
  ]}
/>
```

**SwitchFieldTemplate:**
```tsx
<SwitchFieldTemplate
  label="Active"
  description="Enable or disable this item"
  checked={checked}
  onCheckedChange={setChecked}
/>
```

See [Form Patterns](./FORM_PATTERNS.md) for detailed usage.

---

## Layout Components

### Sidebar

Navigation sidebar with role-based access control.

**Features:**
- Logo area
- User info display
- Navigation items with icons
- Active state highlighting
- Role-based filtering
- Settings and logout

See [Navigation Patterns](./NAVIGATION_PATTERNS.md) for detailed usage.

### Header

Top header with global actions.

**Features:**
- Page title
- Search button
- Notification dropdown
- Theme toggle
- User menu

See [Navigation Patterns](./NAVIGATION_PATTERNS.md) for detailed usage.

---

## Loading Components

### Skeleton Variants

Pre-built skeleton components for common patterns.

**SkeletonText:**
```tsx
<SkeletonText lines={3} />
```

**SkeletonCard:**
```tsx
<SkeletonCard />
```

**SkeletonTable:**
```tsx
<SkeletonTable rows={10} cols={5} />
```

**SkeletonList:**
```tsx
<SkeletonList items={5} />
```

See [Loading States](./LOADING_STATES.md) for detailed usage.

---

## Best Practices

1. **Use design tokens** - Never hardcode colors or spacing
2. **Add data-testid** - For all interactive elements
3. **Document props** - Use JSDoc for complex components
4. **Export types** - Make component types reusable
5. **Follow patterns** - Use existing patterns for consistency

---

## Related Documentation

- [Interaction Patterns](./INTERACTION_PATTERNS.md) - Overall pattern guide
- [Form Patterns](./FORM_PATTERNS.md) - Form component usage
- [Table Patterns](./TABLE_PATTERNS.md) - DataTable usage
- [Modal Patterns](./MODAL_PATTERNS.md) - Modal component usage
- [Navigation Patterns](./NAVIGATION_PATTERNS.md) - Layout component usage
- [Loading States](./LOADING_STATES.md) - Loading component usage
