/**
 * Reusable form field templates for consistent form layouts
 */

import { ReactNode } from 'react'
import { FieldError } from 'react-hook-form'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// ============================================================================
// Types
// ============================================================================

type BaseFieldProps = {
  label: string
  error?: FieldError
  required?: boolean
  description?: string
}

type TextFieldProps = BaseFieldProps & {
  id: string
  type?: 'text' | 'email' | 'password' | 'url' | 'tel' | 'number'
  placeholder?: string
  register: any
}

type TextareaFieldProps = BaseFieldProps & {
  id: string
  placeholder?: string
  rows?: number
  register: any
}

type SelectFieldProps = BaseFieldProps & {
  placeholder?: string
  value: string
  onValueChange: (value: string) => void
  options: Array<{ value: string; label: string }>
}

type SwitchFieldProps = BaseFieldProps & {
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}

// ============================================================================
// Text Field Template
// ============================================================================

export function TextFieldTemplate({
  id,
  label,
  type = 'text',
  placeholder,
  required = false,
  error,
  description,
  register
}: TextFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <Input
        id={id}
        type={type}
        placeholder={placeholder}
        {...register}
      />
      {description && !error && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {error && (
        <p className="text-sm text-destructive">{error.message}</p>
      )}
    </div>
  )
}

// ============================================================================
// Textarea Field Template
// ============================================================================

export function TextareaFieldTemplate({
  id,
  label,
  placeholder,
  rows = 4,
  required = false,
  error,
  description,
  register
}: TextareaFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <Textarea
        id={id}
        placeholder={placeholder}
        rows={rows}
        {...register}
      />
      {description && !error && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {error && (
        <p className="text-sm text-destructive">{error.message}</p>
      )}
    </div>
  )
}

// ============================================================================
// Select Field Template
// ============================================================================

export function SelectFieldTemplate({
  label,
  placeholder = 'Select an option...',
  required = false,
  error,
  description,
  value,
  onValueChange,
  options
}: SelectFieldProps) {
  return (
    <div className="space-y-2">
      <Label>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map(option => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {description && !error && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {error && (
        <p className="text-sm text-destructive">{error.message}</p>
      )}
    </div>
  )
}

// ============================================================================
// Switch Field Template
// ============================================================================

export function SwitchFieldTemplate({
  label,
  description,
  checked,
  onCheckedChange
}: SwitchFieldProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <Label>{label}</Label>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  )
}

// ============================================================================
// Field Group Template (for grid layouts)
// ============================================================================

type FieldGroupProps = {
  children: ReactNode
  columns?: 1 | 2 | 3 | 4
}

export function FieldGroup({ children, columns = 2 }: FieldGroupProps) {
  const gridClass = {
    1: '',
    2: 'md:grid-cols-2',
    3: 'md:grid-cols-3',
    4: 'md:grid-cols-4'
  }[columns]

  return (
    <div className={`grid gap-4 ${gridClass}`}>
      {children}
    </div>
  )
}

// ============================================================================
// Form Section Template (for grouped fields)
// ============================================================================

type FormSectionProps = {
  title: string
  description?: string
  children: ReactNode
}

export function FormSection({ title, description, children }: FormSectionProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-lg font-medium">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  )
}
