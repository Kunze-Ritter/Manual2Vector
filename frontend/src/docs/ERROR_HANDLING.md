# Error Handling Patterns

This document describes error handling patterns used throughout the KRAI Dashboard, including try-catch patterns, toast notifications, and error boundaries.

## Table of Contents

- [Try-Catch Pattern in Mutations](#try-catch-pattern-in-mutations)
- [Error Message Extraction](#error-message-extraction)
- [Toast Notification Pattern](#toast-notification-pattern)
- [API Response Handling](#api-response-handling)
- [Query Error Handling](#query-error-handling)
- [Form Validation Errors](#form-validation-errors)
- [Error Boundaries](#error-boundaries)
- [Best Practices](#best-practices)

---

## Try-Catch Pattern in Mutations

All mutations should follow a consistent try-catch pattern for error handling.

### Standard Mutation Pattern

```tsx
const handleCreate = async (data: CreateInput) => {
  try {
    // 1. Call mutation
    const response = await createMutation.mutateAsync(data)

    // 2. Validate response
    if (!response.success || !response.data) {
      throw new Error(response.message ?? 'Failed to create item')
    }

    // 3. Show success toast
    toast.success('Item created', {
      description: 'The item has been added successfully.'
    })

    // 4. Perform cleanup/navigation
    resetModal()

  } catch (error) {
    // 5. Extract error message
    const message = error instanceof Error ? error.message : 'Unexpected error'

    // 6. Show error toast
    toast.error('Creation failed', {
      description: message
    })
  }
}
```

### Update Pattern

```tsx
const handleUpdate = async (id: string, data: UpdateInput) => {
  try {
    const response = await updateMutation.mutateAsync({ id, data })

    if (!response.success || !response.data) {
      throw new Error(response.message ?? 'Failed to update item')
    }

    toast.success('Item updated', {
      description: 'Changes saved successfully.'
    })

    resetModal()

  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unexpected error'
    toast.error('Update failed', { description: message })
  }
}
```

### Delete Pattern

```tsx
const handleDelete = async (id: string) => {
  try {
    const response = await deleteMutation.mutateAsync(id)

    if (!response.success) {
      throw new Error(response.message ?? 'Failed to delete item')
    }

    toast.success('Item deleted', {
      description: 'The item has been removed.'
    })

  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unexpected error'
    toast.error('Delete failed', { description: message })
  }
}
```

---

## Error Message Extraction

Always extract error messages safely to avoid displaying raw error objects.

### Standard Extraction

```tsx
const message = error instanceof Error ? error.message : 'Unexpected error'
```

### With Fallback Message

```tsx
const getErrorMessage = (error: unknown, fallback: string = 'An error occurred'): string => {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return fallback
}

// Usage
const message = getErrorMessage(error, 'Failed to create item')
```

### API Error Extraction

```tsx
const getApiErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    // Check for API response in error
    const apiError = (error as any).response?.data?.message
    if (apiError) return apiError

    return error.message
  }
  return 'An unexpected error occurred'
}
```

---

## Toast Notification Pattern

Use Sonner toast for consistent user feedback.

### Success Toast

```tsx
import { toast } from 'sonner'

toast.success('Operation successful', {
  description: 'Your changes have been saved.'
})
```

### Error Toast

```tsx
toast.error('Operation failed', {
  description: 'An error occurred. Please try again.'
})
```

### Info Toast

```tsx
toast.info('Processing', {
  description: 'Your request is being processed.'
})
```

### Warning Toast

```tsx
toast.warning('Warning', {
  description: 'This action may have unintended consequences.'
})
```

### Toast with Action

```tsx
toast.error('Delete failed', {
  description: 'Could not delete the item.',
  action: {
    label: 'Retry',
    onClick: () => handleDelete(id)
  }
})
```

### Loading Toast

```tsx
const toastId = toast.loading('Processing...', {
  description: 'Please wait while we process your request.'
})

// Later, update the toast
toast.success('Complete', {
  id: toastId,
  description: 'Operation completed successfully.'
})
```

---

## API Response Handling

### Standard Response Validation

```tsx
type ApiResponse<T> = {
  success: boolean
  data?: T
  message?: string
}

const handleApiCall = async <T,>(apiCall: () => Promise<ApiResponse<T>>) => {
  try {
    const response = await apiCall()

    // Validate response structure
    if (!response.success || !response.data) {
      throw new Error(response.message ?? 'API call failed')
    }

    return response.data

  } catch (error) {
    const message = getErrorMessage(error)
    toast.error('Request failed', { description: message })
    throw error
  }
}
```

### Network Error Handling

```tsx
const handleNetworkError = (error: unknown) => {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    toast.error('Network error', {
      description: 'Could not connect to the server. Please check your internet connection.'
    })
    return
  }

  const message = getErrorMessage(error)
  toast.error('Request failed', { description: message })
}
```

### Timeout Handling

```tsx
const fetchWithTimeout = async (url: string, timeout: number = 30000) => {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, { signal: controller.signal })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout. Please try again.')
    }
    throw error
  }
}
```

---

## Query Error Handling

### TanStack Query Error Display

```tsx
const { data, error, isError, isLoading } = useQuery({
  queryKey: ['documents'],
  queryFn: fetchDocuments
})

if (isError) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>
        {error instanceof Error ? error.message : 'Failed to load documents'}
      </AlertDescription>
    </Alert>
  )
}
```

### Query Error with Retry

```tsx
const { data, error, isError, refetch } = useQuery({
  queryKey: ['documents'],
  queryFn: fetchDocuments,
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
})

if (isError) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error loading documents</AlertTitle>
      <AlertDescription>
        {error instanceof Error ? error.message : 'An error occurred'}
      </AlertDescription>
      <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2">
        Retry
      </Button>
    </Alert>
  )
}
```

### Global Query Error Handler

```tsx
import { QueryClient } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      onError: (error) => {
        const message = getErrorMessage(error, 'Failed to fetch data')
        toast.error('Query failed', { description: message })
      }
    },
    mutations: {
      onError: (error) => {
        const message = getErrorMessage(error, 'Operation failed')
        toast.error('Mutation failed', { description: message })
      }
    }
  }
})
```

---

## Form Validation Errors

### Field-Level Errors

```tsx
{errors.field_name && (
  <p className="text-sm text-destructive">{errors.field_name.message}</p>
)}
```

### Form-Level Errors

```tsx
const [formError, setFormError] = useState<string | null>(null)

const handleSubmit = async (data: FormData) => {
  setFormError(null)
  try {
    // ... submission logic
  } catch (error) {
    const message = getErrorMessage(error)
    setFormError(message)
  }
}

// Display form error
{formError && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>{formError}</AlertDescription>
  </Alert>
)}
```

### Server Validation Errors

```tsx
type ServerValidationError = {
  field: string
  message: string
}

const handleServerValidationErrors = (
  errors: ServerValidationError[],
  setError: UseFormSetError<FormData>
) => {
  errors.forEach(({ field, message }) => {
    setError(field as any, {
      type: 'server',
      message
    })
  })
}

// Usage
try {
  const response = await createMutation.mutateAsync(data)
  if (response.validationErrors) {
    handleServerValidationErrors(response.validationErrors, setError)
    return
  }
} catch (error) {
  // Handle other errors
}
```

---

## Error Boundaries

### React Error Boundary

```tsx
import { Component, ReactNode } from 'react'

type ErrorBoundaryProps = {
  children: ReactNode
  fallback?: ReactNode
}

type ErrorBoundaryState = {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Optional: Log to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex flex-col items-center justify-center min-h-screen p-4">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h1 className="text-2xl font-bold mb-2">Something went wrong</h1>
          <p className="text-muted-foreground mb-4">
            {this.state.error?.message ?? 'An unexpected error occurred'}
          </p>
          <Button onClick={() => window.location.reload()}>
            Reload Page
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
```

### Usage

```tsx
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

---

## Best Practices

1. **Always use try-catch in mutations** - Never let errors go unhandled
2. **Extract error messages safely** - Use `instanceof Error` checks
3. **Provide context in error messages** - Tell users what failed
4. **Show actionable errors** - Include retry buttons when appropriate
5. **Log errors for debugging** - Console.error or error tracking service
6. **Validate API responses** - Check `success` and `data` fields
7. **Handle network errors specifically** - Different message for connectivity issues
8. **Use error boundaries for React errors** - Catch rendering errors
9. **Don't expose sensitive information** - Sanitize error messages
10. **Test error scenarios** - Ensure error handling works as expected

---

## Related Documentation

- [Toast Messages](../lib/toast-messages.ts) - Standardized toast messages
- [Form Patterns](./FORM_PATTERNS.md) - Form validation errors
- [Modal Patterns](./MODAL_PATTERNS.md) - Modal error handling
- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
