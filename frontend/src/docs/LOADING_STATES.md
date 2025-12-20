# Loading States Patterns

This document describes loading state patterns used throughout the KRAI Dashboard, including skeleton components, spinners, and loading indicators.

## Table of Contents

- [Skeleton Component Usage](#skeleton-component-usage)
- [DataTable Loading Pattern](#datatable-loading-pattern)
- [Query Loading States](#query-loading-states)
- [Button Loading States](#button-loading-states)
- [Page Loading Pattern](#page-loading-pattern)
- [Skeleton Variants](#skeleton-variants)
- [Spinner Pattern](#spinner-pattern)
- [Best Practices](#best-practices)

---

## Skeleton Component Usage

The Skeleton component provides a placeholder during content loading.

### Basic Skeleton

```tsx
import { Skeleton } from '@/components/ui/skeleton'

<Skeleton className="h-6 w-full" />
```

### Multiple Skeletons

```tsx
<div className="space-y-2">
  <Skeleton className="h-6 w-full" />
  <Skeleton className="h-6 w-3/4" />
  <Skeleton className="h-6 w-1/2" />
</div>
```

### Skeleton Sizes

```tsx
// Small
<Skeleton className="h-4 w-24" />

// Medium
<Skeleton className="h-6 w-32" />

// Large
<Skeleton className="h-8 w-48" />

// Full width
<Skeleton className="h-10 w-full" />
```

### Skeleton Shapes

```tsx
// Rectangle (default)
<Skeleton className="h-20 w-full" />

// Square
<Skeleton className="h-12 w-12" />

// Circle
<Skeleton className="h-12 w-12 rounded-full" />

// Rounded
<Skeleton className="h-10 w-32 rounded-lg" />
```

---

## DataTable Loading Pattern

### Automatic Skeleton Rows

```tsx
<DataTable
  columns={columns}
  data={data}
  isLoading={isLoading}  // Automatically renders skeleton rows
/>
```

### Custom Skeleton Rows

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

// Usage
{isLoading ? (
  <TableBody>{renderSkeletonRows(10)}</TableBody>
) : (
  <TableBody>
    {data.map(row => <TableRow key={row.id}>...</TableRow>)}
  </TableBody>
)}
```

---

## Query Loading States

### Basic Query Loading

```tsx
const { data, isLoading } = useQuery({
  queryKey: ['documents'],
  queryFn: fetchDocuments
})

if (isLoading) {
  return <SkeletonTable rows={10} cols={5} />
}

return <DataTable columns={columns} data={data} />
```

### Loading with Skeleton

```tsx
const { data, isLoading } = useQuery({
  queryKey: ['document', id],
  queryFn: () => fetchDocument(id)
})

if (isLoading) {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  )
}

return <DocumentDetails document={data} />
```

### Fetching Indicator

```tsx
const { data, isLoading, isFetching } = useQuery({
  queryKey: ['documents'],
  queryFn: fetchDocuments
})

return (
  <div>
    {isFetching && !isLoading && (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Updating...
      </div>
    )}
    <DataTable columns={columns} data={data} />
  </div>
)
```

---

## Button Loading States

### Standard Button Loading

```tsx
<Button disabled={isLoading}>
  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
  {isLoading ? 'Saving...' : 'Save'}
</Button>
```

### Submit Button Loading

```tsx
<Button type="submit" disabled={isSubmitting}>
  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
  {isSubmitting ? 'Creating...' : 'Create'}
</Button>
```

### Icon Button Loading

```tsx
<Button variant="ghost" size="icon" disabled={isLoading}>
  {isLoading ? (
    <Loader2 className="h-4 w-4 animate-spin" />
  ) : (
    <Trash className="h-4 w-4" />
  )}
</Button>
```

### Button with Progress

```tsx
const [progress, setProgress] = useState(0)

<Button disabled={isUploading}>
  {isUploading ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Uploading {progress}%
    </>
  ) : (
    'Upload'
  )}
</Button>
```

---

## Page Loading Pattern

### Full Page Loading

```tsx
if (isLoading) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  )
}
```

### Page Content Loading

```tsx
if (isLoading) {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-1/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>

      {/* Content skeleton */}
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  )
}
```

### Section Loading

```tsx
<div className="space-y-4">
  <h2 className="text-xl font-semibold">Recent Documents</h2>
  {isLoading ? (
    <SkeletonTable rows={5} cols={4} />
  ) : (
    <DataTable columns={columns} data={documents} />
  )}
</div>
```

---

## Skeleton Variants

Use pre-built skeleton variants for common patterns.

### SkeletonText

```tsx
import { SkeletonText } from '@/components/ui/skeleton-variants'

<SkeletonText lines={3} />
```

### SkeletonCard

```tsx
import { SkeletonCard } from '@/components/ui/skeleton-variants'

<SkeletonCard />
```

### SkeletonTable

```tsx
import { SkeletonTable } from '@/components/ui/skeleton-variants'

<SkeletonTable rows={10} cols={5} />
```

### SkeletonList

```tsx
import { SkeletonList } from '@/components/ui/skeleton-variants'

<SkeletonList items={5} />
```

### SkeletonForm

```tsx
import { SkeletonForm } from '@/components/ui/skeleton-variants'

<SkeletonForm fields={6} />
```

---

## Spinner Pattern

### Inline Spinner

```tsx
import { Loader2 } from 'lucide-react'

<div className="flex items-center gap-2">
  <Loader2 className="h-4 w-4 animate-spin" />
  <span>Loading...</span>
</div>
```

### Centered Spinner

```tsx
<div className="flex items-center justify-center py-12">
  <Loader2 className="h-8 w-8 animate-spin text-primary" />
</div>
```

### Spinner with Message

```tsx
<div className="flex flex-col items-center justify-center py-12 gap-4">
  <Loader2 className="h-8 w-8 animate-spin text-primary" />
  <p className="text-sm text-muted-foreground">Loading documents...</p>
</div>
```

### Spinner Sizes

```tsx
// Small
<Loader2 className="h-3 w-3 animate-spin" />

// Medium
<Loader2 className="h-4 w-4 animate-spin" />

// Large
<Loader2 className="h-6 w-6 animate-spin" />

// Extra Large
<Loader2 className="h-8 w-8 animate-spin" />
```

---

## Best Practices

1. **Use skeletons for content loading** - Better UX than spinners alone
2. **Match skeleton dimensions to actual content** - Prevents layout shift
3. **Show loading state immediately** - Don't wait for slow queries
4. **Disable interactive elements during loading** - Prevent duplicate actions
5. **Use appropriate loading indicators** - Skeleton for content, spinner for actions
6. **Provide loading feedback for long operations** - Show progress when possible
7. **Keep loading states consistent** - Use same patterns across the app
8. **Test loading states** - Ensure they display correctly
9. **Handle loading errors** - Show error state if loading fails
10. **Optimize loading performance** - Use suspense and lazy loading where appropriate

---

## Loading State Decision Tree

```
Is the loading for...
├─ Page content?
│  └─ Use full page skeleton or SkeletonTable/SkeletonCard
├─ Table data?
│  └─ Use DataTable with isLoading prop
├─ Form submission?
│  └─ Use Button with Loader2 icon and disabled state
├─ Background fetch?
│  └─ Use inline spinner with "Updating..." text
├─ File upload?
│  └─ Use Button with progress percentage
└─ Modal content?
   └─ Use Skeleton components inside modal
```

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
- [DataTable Patterns](./TABLE_PATTERNS.md) - Table loading states
- [Skeleton Variants](../components/ui/skeleton-variants.tsx) - Pre-built skeleton components
- [Interaction Patterns](./INTERACTION_PATTERNS.md) - Overall pattern guide
