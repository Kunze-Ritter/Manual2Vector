import { forwardRef, useEffect, useImperativeHandle, useMemo } from 'react'
import { Controller, type Resolver, useForm, type UseFormReturn } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { useDocuments } from '@/hooks/use-documents'
import { useManufacturers } from '@/hooks/use-manufacturers'
import {
  ExtractionMethod,
  SeverityLevel,
  type Document,
  type ErrorCode,
  type ErrorCodeCreateInput,
  type ErrorCodeUpdateInput,
  type Manufacturer,
} from '@/types/api'

export interface ErrorCodeFormHandle {
  submit: () => void
  reset: (values?: ErrorCodeFormValues) => void
  getValues: () => ErrorCodeFormValues
  getForm: () => UseFormReturn<ErrorCodeFormValues>
}

export interface ErrorCodeFormSubmit {
  mode: 'create' | 'edit'
  data: ErrorCodeCreateInput | ErrorCodeUpdateInput
}

export interface ErrorCodeFormProps {
  mode: 'create' | 'edit'
  initialData?: Partial<ErrorCode>
  onSubmit: (payload: ErrorCodeFormSubmit) => void | Promise<void>
  onChange?: (values: ErrorCodeFormValues, form: UseFormReturn<ErrorCodeFormValues>) => void
  formId?: string
  className?: string
}

type NullableString = string | null

const errorCodeSchemaBase = z
  .object({
    error_code: z.string().trim().min(1, 'Error code is required'),
    error_description: z.string().trim().min(1, 'Description is required'),
    solution_text: z.string().trim().optional().default(''),
    severity_level: z.nativeEnum(SeverityLevel),
    extraction_method: z.union([z.nativeEnum(ExtractionMethod), z.literal('')]).optional().default(''),
    requires_technician: z.boolean().default(false),
    requires_parts: z.boolean().default(false),
    confidence_score: z
      .string()
      .trim()
      .optional()
      .default('')
      .refine((value) => {
        if (value === '') return true
        const parsed = Number(value)
        return !Number.isNaN(parsed) && parsed >= 0 && parsed <= 1
      }, 'Confidence must be a number between 0 and 1'),
    estimated_fix_time_minutes: z
      .string()
      .trim()
      .optional()
      .default('')
      .refine((value) => {
        if (value === '') return true
        const parsed = Number(value)
        return !Number.isNaN(parsed) && parsed >= 0
      }, 'Must be zero or a positive number'),
    chunk_id: z.string().trim().optional().default(''),
    document_id: z.string().trim().optional().default(''),
    manufacturer_id: z.string().trim().optional().default(''),
    page_number: z
      .string()
      .trim()
      .optional()
      .default('')
      .refine((value) => {
        if (value === '') return true
        const parsed = Number(value)
        return Number.isInteger(parsed) && parsed >= 0
      }, 'Must be a non-negative integer'),
  })

const errorCodeFormSchema = errorCodeSchemaBase.superRefine((values, ctx) => {
  if (!values.chunk_id && !values.document_id && !values.manufacturer_id) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Select at least one relation (chunk, document, or manufacturer)',
      path: ['document_id'],
    })
  }
})

export interface ErrorCodeFormValues {
  error_code: string
  error_description: string
  solution_text: string
  severity_level: SeverityLevel
  extraction_method: '' | ExtractionMethod
  requires_technician: boolean
  requires_parts: boolean
  confidence_score: string
  estimated_fix_time_minutes: string
  chunk_id: string
  document_id: string
  manufacturer_id: string
  page_number: string
}

type BuildPayloadParams = { mode: 'create' | 'edit'; values: ErrorCodeFormValues }

const toOptionalString = (value?: string | null): NullableString => {
  if (value == null) return null
  const trimmed = value.trim()
  return trimmed.length ? trimmed : null
}

const toOptionalNumber = (value?: string | null): number | null => {
  const trimmed = toOptionalString(value)
  if (trimmed == null) return null
  const parsed = Number(trimmed)
  return Number.isNaN(parsed) ? null : parsed
}

const toOptionalInteger = (value?: string | null): number | null => {
  const trimmed = toOptionalString(value)
  if (trimmed == null) return null
  const parsed = Number(trimmed)
  if (!Number.isInteger(parsed)) return null
  return parsed
}

const buildPayload = ({ mode, values }: BuildPayloadParams): ErrorCodeCreateInput | ErrorCodeUpdateInput => {
  const shared: ErrorCodeUpdateInput = {
    error_code: values.error_code.trim(),
    error_description: values.error_description.trim(),
    solution_text: toOptionalString(values.solution_text),
    severity_level: values.severity_level,
    extraction_method: values.extraction_method ? (values.extraction_method as ExtractionMethod) : null,
    requires_technician: values.requires_technician,
    requires_parts: values.requires_parts,
    confidence_score: toOptionalNumber(values.confidence_score),
    estimated_fix_time_minutes: toOptionalNumber(values.estimated_fix_time_minutes),
    chunk_id: toOptionalString(values.chunk_id),
    document_id: toOptionalString(values.document_id),
    manufacturer_id: toOptionalString(values.manufacturer_id),
    page_number: toOptionalInteger(values.page_number),
  }

  if (mode === 'create') {
    return shared as ErrorCodeCreateInput
  }

  return shared
}

const mapErrorCodeToValues = (data: Partial<ErrorCode> | undefined, mode: 'create' | 'edit'): ErrorCodeFormValues => ({
  error_code: data?.error_code ?? '',
  error_description: data?.error_description ?? '',
  solution_text: data?.solution_text ?? '',
  severity_level: data?.severity_level ?? SeverityLevel.MEDIUM,
  extraction_method: (data?.extraction_method ?? '') as ErrorCodeFormValues['extraction_method'],
  requires_technician: data?.requires_technician ?? false,
  requires_parts: data?.requires_parts ?? false,
  confidence_score: data?.confidence_score != null ? String(data.confidence_score) : '',
  estimated_fix_time_minutes: data?.estimated_fix_time_minutes != null ? String(data.estimated_fix_time_minutes) : '',
  chunk_id: data?.chunk_id ?? '',
  document_id: data?.document_id ?? '',
  manufacturer_id: data?.manufacturer_id ?? '',
  page_number: data?.page_number != null ? String(data.page_number) : '',
})

const enumLabel = (value: string) =>
  value
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')

export const ErrorCodeForm = forwardRef<ErrorCodeFormHandle, ErrorCodeFormProps>(
  ({ mode, initialData, onSubmit, onChange, formId = 'error-code-form', className }, ref) => {
    const defaultValues = useMemo(() => mapErrorCodeToValues(initialData, mode), [initialData, mode])

    const form = useForm<ErrorCodeFormValues>({
      defaultValues,
      resolver: zodResolver(errorCodeFormSchema),
    })

    useEffect(() => {
      form.reset(defaultValues)
    }, [defaultValues, form])

    useEffect(() => {
      if (!onChange) return
      const subscription = form.watch((watchValues) => {
        onChange(watchValues as ErrorCodeFormValues, form)
      }) as ReturnType<typeof form.watch>
      return () => subscription.unsubscribe()
    }, [form, onChange])

    const { data: documentsData, isLoading: documentsLoading } = useDocuments({ page_size: 100 })
    const { data: manufacturersData, isLoading: manufacturersLoading } = useManufacturers({ page_size: 100 })

    const documents = useMemo<Document[]>(() => documentsData?.documents ?? [], [documentsData?.documents])
    const manufacturers = useMemo<Manufacturer[]>(
      () => manufacturersData?.manufacturers ?? [],
      [manufacturersData?.manufacturers],
    )

    useImperativeHandle(
      ref,
      () => ({
        submit: () =>
          form.handleSubmit((values: ErrorCodeFormValues) => onSubmit({ mode, data: buildPayload({ mode, values }) }))(),
        reset: (values) => form.reset(values ?? defaultValues),
        getValues: () => form.getValues(),
        getForm: () => form,
      }),
      [form, mode, onSubmit, defaultValues],
    )

    const {
      register,
      control,
      handleSubmit,
      formState: { errors },
    } = form

    return (
      <form
        id={formId}
        onSubmit={handleSubmit((values: ErrorCodeFormValues) => onSubmit({ mode, data: buildPayload({ mode, values }) }))}
        className={cn('space-y-6', className)}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="error_code">Error code *</Label>
            <Input id="error_code" {...register('error_code')} />
            {errors.error_code && <p className="text-sm text-destructive">{errors.error_code.message}</p>}
          </div>
          <Controller
            control={control}
            name="severity_level"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Severity *</Label>
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select severity" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(SeverityLevel).map((severity) => (
                      <SelectItem key={severity} value={severity}>
                        {enumLabel(severity)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.severity_level && <p className="text-sm text-destructive">{errors.severity_level.message}</p>}
              </div>
            )}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="error_description">Description *</Label>
          <Textarea id="error_description" rows={4} {...register('error_description')} />
          {errors.error_description && <p className="text-sm text-destructive">{errors.error_description.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="solution_text">Solution</Label>
          <Textarea id="solution_text" rows={4} {...register('solution_text')} />
          {errors.solution_text && <p className="text-sm text-destructive">{errors.solution_text.message}</p>}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Controller
            control={control}
            name="extraction_method"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Extraction method</Label>
                <Select value={field.value ?? ''} onValueChange={(value: string) => field.onChange(value || undefined)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select extraction method" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Unspecified</SelectItem>
                    {Object.values(ExtractionMethod).map((method) => (
                      <SelectItem key={method} value={method}>
                        {enumLabel(method)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.extraction_method && (
                  <p className="text-sm text-destructive">{errors.extraction_method.message}</p>
                )}
              </div>
            )}
          />

          <div className="grid grid-cols-2 gap-4 rounded-md border p-3">
            <Controller
              control={control}
              name="requires_technician"
              render={({ field }) => (
                <label className="flex items-center justify-between gap-2 text-sm font-medium">
                  <span>Requires technician</span>
                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                </label>
              )}
            />
            <Controller
              control={control}
              name="requires_parts"
              render={({ field }) => (
                <label className="flex items-center justify-between gap-2 text-sm font-medium">
                  <span>Requires parts</span>
                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                </label>
              )}
            />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="confidence_score">Confidence (0-1)</Label>
            <Input id="confidence_score" type="number" step="0.01" min="0" max="1" {...register('confidence_score')} />
            {errors.confidence_score && <p className="text-sm text-destructive">{errors.confidence_score.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="estimated_fix_time_minutes">Estimated fix time (minutes)</Label>
            <Input
              id="estimated_fix_time_minutes"
              type="number"
              inputMode="numeric"
              min="0"
              step="1"
              {...register('estimated_fix_time_minutes')}
            />
            {errors.estimated_fix_time_minutes && (
              <p className="text-sm text-destructive">{errors.estimated_fix_time_minutes.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="page_number">Page number</Label>
            <Input id="page_number" type="number" inputMode="numeric" min="0" step="1" {...register('page_number')} />
            {errors.page_number && <p className="text-sm text-destructive">{errors.page_number.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="chunk_id">Chunk ID</Label>
            <Input id="chunk_id" {...register('chunk_id')} placeholder="Optional chunk reference" />
            {errors.chunk_id && <p className="text-sm text-destructive">{errors.chunk_id.message}</p>}
          </div>
          <Controller
            control={control}
            name="document_id"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Document</Label>
                <Select
                  value={field.value ?? ''}
                  onValueChange={(value: string) => field.onChange(value || undefined)}
                  disabled={documentsLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select document" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Unassigned</SelectItem>
                    {documents.map((document: Document) => (
                      <SelectItem key={document.id} value={document.id}>
                        {document.filename}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.document_id && <p className="text-sm text-destructive">{errors.document_id.message}</p>}
              </div>
            )}
          />
          <Controller
            control={control}
            name="manufacturer_id"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Manufacturer</Label>
                <Select
                  value={field.value ?? ''}
                  onValueChange={(value: string) => field.onChange(value || undefined)}
                  disabled={manufacturersLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select manufacturer" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Unassigned</SelectItem>
                    {manufacturers.map((manufacturer: Manufacturer) => (
                      <SelectItem key={manufacturer.id} value={manufacturer.id}>
                        {manufacturer.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.manufacturer_id && <p className="text-sm text-destructive">{errors.manufacturer_id.message}</p>}
              </div>
            )}
          />
        </div>
      </form>
    )
  },
)

ErrorCodeForm.displayName = 'ErrorCodeForm'

export default ErrorCodeForm
