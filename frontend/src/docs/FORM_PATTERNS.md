# Form Patterns

This document describes the form patterns used throughout the KRAI Dashboard, including architecture, layout, validation, and submission flows.

## Table of Contents

- [Form Architecture](#form-architecture)
- [Grid Layout Patterns](#grid-layout-patterns)
- [Field Types](#field-types)
- [Error Display](#error-display)
- [Optional Field Handling](#optional-field-handling)
- [Payload Building](#payload-building)
- [Form Submission Flow](#form-submission-flow)
- [Validation Patterns](#validation-patterns)
- [Best Practices](#best-practices)

---

## Form Architecture

All forms follow a consistent architecture using **react-hook-form** and **zod** for validation.

### Standard Form Structure

```tsx
import { forwardRef, useImperativeHandle } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// 1. Define Zod schema
const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Must be a valid email'),
  description: z.string().optional()
})

type FormData = z.infer<typeof formSchema>

// 2. Define form props
type FormProps = {
  mode: 'create' | 'edit'
  initialData?: FormData | null
  onSubmit: (data: FormData) => void | Promise<void>
}

// 3. Define imperative handle for external submission
export type FormHandle = {
  submit: () => void
}

// 4. Implement form with forwardRef
export const MyForm = forwardRef<FormHandle, FormProps>(
  ({ mode, initialData, onSubmit }, ref) => {
    const {
      register,
      handleSubmit,
      formState: { errors },
      control
    } = useForm<FormData>({
      resolver: zodResolver(formSchema),
      defaultValues: initialData ?? {}
    })

    // 5. Expose submit method via ref
    useImperativeHandle(ref, () => ({
      submit: () => {
        handleSubmit(onSubmit)()
      }
    }))

    return (
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Form fields */}
      </form>
    )
  }
)

MyForm.displayName = 'MyForm'
```

### Why This Pattern?

- **forwardRef + useImperativeHandle**: Allows parent components (e.g., CrudModal) to trigger submission
- **react-hook-form**: Efficient form state management with minimal re-renders
- **zod**: Type-safe schema validation with TypeScript inference
- **zodResolver**: Seamless integration between zod and react-hook-form

---

## Grid Layout Patterns

Forms use CSS Grid for responsive layouts.

### Two-Column Layout

```tsx
<form className="space-y-4">
  {/* Full-width field */}
  <div className="space-y-2">
    <Label htmlFor="name">Name *</Label>
    <Input id="name" {...register('name')} />
    {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
  </div>

  {/* Two-column grid */}
  <div className="grid gap-4 md:grid-cols-2">
    <div className="space-y-2">
      <Label htmlFor="email">Email *</Label>
      <Input id="email" type="email" {...register('email')} />
      {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
    </div>

    <div className="space-y-2">
      <Label htmlFor="phone">Phone</Label>
      <Input id="phone" {...register('phone')} />
      {errors.phone && <p className="text-sm text-destructive">{errors.phone.message}</p>}
    </div>
  </div>

  {/* Full-width textarea */}
  <div className="space-y-2">
    <Label htmlFor="description">Description</Label>
    <Textarea id="description" {...register('description')} rows={4} />
    {errors.description && <p className="text-sm text-destructive">{errors.description.message}</p>}
  </div>
</form>
```

### Three-Column Layout

```tsx
<div className="grid gap-4 md:grid-cols-3">
  <div className="space-y-2">
    <Label htmlFor="field1">Field 1</Label>
    <Input id="field1" {...register('field1')} />
  </div>
  <div className="space-y-2">
    <Label htmlFor="field2">Field 2</Label>
    <Input id="field2" {...register('field2')} />
  </div>
  <div className="space-y-2">
    <Label htmlFor="field3">Field 3</Label>
    <Input id="field3" {...register('field3')} />
  </div>
</div>
```

---

## Field Types

### Text Input

```tsx
<div className="space-y-2">
  <Label htmlFor="field_name">Field Label *</Label>
  <Input 
    id="field_name" 
    placeholder="Enter value..."
    {...register('field_name')} 
  />
  {errors.field_name && (
    <p className="text-sm text-destructive">{errors.field_name.message}</p>
  )}
</div>
```

### Select Dropdown

```tsx
import { Controller } from 'react-hook-form'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

<Controller
  control={control}
  name="field_name"
  render={({ field }) => (
    <div className="space-y-2">
      <Label>Field Label *</Label>
      <Select value={field.value} onValueChange={field.onChange}>
        <SelectTrigger>
          <SelectValue placeholder="Select an option..." />
        </SelectTrigger>
        <SelectContent>
          {options.map(option => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {errors.field_name && (
        <p className="text-sm text-destructive">{errors.field_name.message}</p>
      )}
    </div>
  )}
/>
```

### Textarea

```tsx
<div className="space-y-2">
  <Label htmlFor="description">Description</Label>
  <Textarea 
    id="description" 
    placeholder="Enter description..."
    rows={4}
    {...register('description')} 
  />
  {errors.description && (
    <p className="text-sm text-destructive">{errors.description.message}</p>
  )}
</div>
```

### Switch (Boolean)

```tsx
import { Controller } from 'react-hook-form'
import { Switch } from '@/components/ui/switch'

<Controller
  control={control}
  name="is_active"
  render={({ field }) => (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <Label>Active Status</Label>
        <p className="text-sm text-muted-foreground">
          Enable or disable this item
        </p>
      </div>
      <Switch 
        checked={field.value} 
        onCheckedChange={field.onChange} 
      />
    </div>
  )}
/>
```

### Number Input

```tsx
<div className="space-y-2">
  <Label htmlFor="quantity">Quantity *</Label>
  <Input 
    id="quantity" 
    type="number"
    min={0}
    step={1}
    {...register('quantity', { valueAsNumber: true })} 
  />
  {errors.quantity && (
    <p className="text-sm text-destructive">{errors.quantity.message}</p>
  )}
</div>
```

---

## Error Display

### Standard Error Pattern

```tsx
{errors.field_name && (
  <p className="text-sm text-destructive">{errors.field_name.message}</p>
)}
```

### Error Styling

- **Text Size:** `text-sm` (14px)
- **Color:** `text-destructive` (theme-based red)
- **Spacing:** Appears below input with `space-y-2` parent

### Field-Level Errors

Display errors immediately below the relevant field for clear association.

### Form-Level Errors

For errors not tied to specific fields (e.g., API errors):

```tsx
{formError && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>{formError}</AlertDescription>
  </Alert>
)}
```

---

## Optional Field Handling

Use utility functions to handle optional fields consistently.

### Utility Functions

```tsx
// Convert empty string to null for optional fields
export function toOptionalString(value: string | undefined | null): string | null {
  if (!value || value.trim() === '') return null
  return value.trim()
}

// Convert empty/invalid number to null
export function toOptionalNumber(value: number | string | undefined | null): number | null {
  if (value === undefined || value === null || value === '') return null
  const num = typeof value === 'string' ? parseFloat(value) : value
  return isNaN(num) ? null : num
}
```

### Usage in Payload Building

```tsx
const buildPayload = (data: FormData) => ({
  name: data.name,
  email: data.email,
  phone: toOptionalString(data.phone),
  quantity: toOptionalNumber(data.quantity),
  description: toOptionalString(data.description)
})
```

---

## Payload Building

### Create vs. Edit Payloads

```tsx
const buildPayload = (data: FormData, mode: 'create' | 'edit') => {
  const basePayload = {
    name: data.name,
    email: data.email,
    description: toOptionalString(data.description)
  }

  if (mode === 'create') {
    return {
      ...basePayload,
      created_at: new Date().toISOString()
    }
  }

  // Edit mode: include ID and updated timestamp
  return {
    ...basePayload,
    id: data.id,
    updated_at: new Date().toISOString()
  }
}
```

### Nested Objects

```tsx
const buildPayload = (data: FormData) => ({
  name: data.name,
  metadata: {
    category: data.category,
    tags: data.tags,
    custom_fields: data.custom_fields
  }
})
```

---

## Form Submission Flow

### Standard Submission Pattern

```tsx
const handleFormSubmit = async (data: FormData) => {
  try {
    // 1. Build payload
    const payload = buildPayload(data, mode)

    // 2. Call mutation
    const response = mode === 'create'
      ? await createMutation.mutateAsync(payload)
      : await updateMutation.mutateAsync(payload)

    // 3. Validate response
    if (!response.success || !response.data) {
      throw new Error(response.message ?? 'Operation failed')
    }

    // 4. Show success toast
    toast.success(
      mode === 'create' ? 'Item created' : 'Item updated',
      { description: 'Changes saved successfully.' }
    )

    // 5. Reset modal/form state
    resetModal()

  } catch (error) {
    // 6. Handle errors
    const message = error instanceof Error ? error.message : 'Unexpected error'
    toast.error('Operation failed', { description: message })
  }
}
```

### With Loading State

```tsx
const [isSubmitting, setIsSubmitting] = useState(false)

const handleFormSubmit = async (data: FormData) => {
  setIsSubmitting(true)
  try {
    // ... submission logic
  } catch (error) {
    // ... error handling
  } finally {
    setIsSubmitting(false)
  }
}
```

---

## Validation Patterns

### Zod Schema Examples

#### Required Fields

```tsx
const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Must be a valid email'),
  age: z.number().min(18, 'Must be at least 18')
})
```

#### Optional Fields

```tsx
const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  website: z.string().url('Must be a valid URL').optional().or(z.literal(''))
})
```

#### Custom Refinements

```tsx
const schema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string()
}).refine(data => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword']
})
```

#### Async Validation

```tsx
const schema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters')
}).refine(
  async (data) => {
    const response = await checkUsernameAvailability(data.username)
    return response.available
  },
  { message: 'Username is already taken', path: ['username'] }
)
```

### Error Message Standardization

Use consistent error messages across forms:

- **Required:** `"Field name is required"`
- **Email:** `"Must be a valid email"`
- **URL:** `"Must be a valid URL"`
- **Min Length:** `"Must be at least X characters"`
- **Max Length:** `"Must be at most X characters"`
- **Min Value:** `"Must be at least X"`
- **Max Value:** `"Must be at most X"`
- **Pattern:** `"Invalid format"`

---

## Best Practices

1. **Always use zod schemas** - Type-safe validation with TypeScript inference
2. **Mark required fields** - Use asterisk (*) in labels
3. **Provide helpful placeholders** - Guide users on expected input
4. **Show errors inline** - Display errors below relevant fields
5. **Handle optional fields consistently** - Use `toOptionalString`/`toOptionalNumber`
6. **Disable submit during loading** - Prevent duplicate submissions
7. **Reset form after success** - Clear state for next operation
8. **Use Controller for complex inputs** - Select, Switch, custom components
9. **Test validation rules** - Ensure error messages are clear and helpful
10. **Accessibility** - Use proper labels, ARIA attributes, keyboard navigation

---

## Related Documentation

- [Modal Patterns](./MODAL_PATTERNS.md) - Form integration with modals
- [Error Handling](./ERROR_HANDLING.md) - Error handling patterns
- [Component Library](./COMPONENT_LIBRARY.md) - UI component reference
- [Form Field Templates](../components/forms/FormFieldTemplates.tsx) - Reusable field components
