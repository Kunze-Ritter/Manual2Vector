import { forwardRef, useEffect, useImperativeHandle, useMemo } from 'react'
import { Controller, useForm, type UseFormReturn } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { useManufacturers } from '@/hooks/use-manufacturers'
import { useProducts } from '@/hooks/use-products'
import {
  DocumentType,
  ProcessingStatus,
  type Document,
  type DocumentCreateInput,
  type DocumentUpdateInput,
} from '@/types/api'

export interface DocumentFormHandle {
  submit: () => void
  reset: (values?: DocumentFormValues) => void
  getValues: () => DocumentFormValues
  getForm: () => UseFormReturn<DocumentFormValues>
}

export interface DocumentFormSubmit {
  mode: 'create' | 'edit'
  data: DocumentCreateInput | DocumentUpdateInput
}

export interface DocumentFormProps {
  mode: 'create' | 'edit'
  initialData?: Partial<Document>
  onSubmit: (payload: DocumentFormSubmit) => void | Promise<void>
  onChange?: (values: DocumentFormValues, form: UseFormReturn<DocumentFormValues>) => void
  formId?: string
  className?: string
}

const documentSchema = z.object({
  filename: z.string().trim().min(1, 'Filename is required'),
  original_filename: z.string().trim().min(1, 'Original filename is required'),
  language: z.string().trim().min(1, 'Language is required'),
  document_type: z.nativeEnum(DocumentType, { errorMap: () => ({ message: 'Document type is required' }) }),
  processing_status: z.nativeEnum(ProcessingStatus),
  manufacturer_id: z.string().optional(),
  product_id: z.string().optional(),
  manual_review_required: z.boolean(),
  manual_review_notes: z.string().optional(),
  storage_url: z.string().trim().url('Must be a valid URL'),
  publish_date: z.string().optional(),
})

type DocumentFormValues = z.infer<typeof documentSchema>

type BuildPayloadParams = { mode: 'create' | 'edit'; values: DocumentFormValues }

const toOptionalString = (value?: string): string | null => {
  const trimmed = (value ?? '').trim()
  return trimmed ? trimmed : null
}

const buildPayload = ({ mode, values }: BuildPayloadParams): DocumentCreateInput | DocumentUpdateInput => {
  const shared = {
    filename: values.filename.trim(),
    original_filename: values.original_filename.trim(),
    language: values.language.trim(),
    document_type: values.document_type,
    processing_status: values.processing_status,
    manufacturer_id: toOptionalString(values.manufacturer_id),
    product_id: toOptionalString(values.product_id),
    manual_review_required: values.manual_review_required,
    manual_review_notes: toOptionalString(values.manual_review_notes),
    storage_url: values.storage_url.trim(),
    publish_date: toOptionalString(values.publish_date),
  }

  if (mode === 'create') {
    return {
      ...shared,
      file_size: 0,
      file_hash: '',
      storage_path: '',
    }
  }

  return shared
}

const mapDocumentToValues = (data: Partial<Document> | undefined, mode: 'create' | 'edit'): DocumentFormValues => ({
  filename: data?.filename ?? '',
  original_filename: data?.original_filename ?? '',
  language: data?.language ?? '',
  document_type: data?.document_type ?? DocumentType.SERVICE_MANUAL,
  processing_status:
    mode === 'create' ? ProcessingStatus.PENDING : data?.processing_status ?? ProcessingStatus.PENDING,
  manufacturer_id: data?.manufacturer_id ?? '',
  product_id: data?.product_id ?? '',
  manual_review_required: data?.manual_review_required ?? false,
  manual_review_notes: data?.manual_review_notes ?? '',
  storage_url: data?.storage_url ?? '',
  publish_date: data?.publish_date ?? '',
})

const enumLabel = (value: string) =>
  value
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')

export const DocumentForm = forwardRef<DocumentFormHandle, DocumentFormProps>(
  ({ mode, initialData, onSubmit, onChange, formId = 'document-form', className }, ref) => {
    const defaultValues = useMemo(() => mapDocumentToValues(initialData, mode), [initialData, mode])

    const form = useForm<DocumentFormValues>({
      defaultValues,
      resolver: zodResolver(documentSchema),
    })

    useEffect(() => {
      form.reset(defaultValues)
    }, [defaultValues, form])

    useEffect(() => {
      if (!onChange) return
      const subscription = form.watch((values) => {
        onChange(values as DocumentFormValues, form)
      })
      return () => subscription.unsubscribe()
    }, [form, onChange])

    const { data: manufacturersData, isLoading: manufacturersLoading } = useManufacturers({ page_size: 100 })
    const { data: productsData, isLoading: productsLoading } = useProducts({ page_size: 100 })

    useImperativeHandle(
      ref,
      () => ({
        submit: () => form.handleSubmit((values) => onSubmit({ mode, data: buildPayload({ mode, values }) }))(),
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
        onSubmit={handleSubmit((values) => onSubmit({ mode, data: buildPayload({ mode, values }) }))}
        className={cn('space-y-6', className)}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="filename">Filename</Label>
            <Input id="filename" {...register('filename')} />
            {errors.filename && <p className="text-sm text-destructive">{errors.filename.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="original_filename">Original filename</Label>
            <Input id="original_filename" {...register('original_filename')} />
            {errors.original_filename && <p className="text-sm text-destructive">{errors.original_filename.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Input id="language" {...register('language')} />
            {errors.language && <p className="text-sm text-destructive">{errors.language.message}</p>}
          </div>
          <Controller
            control={control}
            name="document_type"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Document type</Label>
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(DocumentType).map((value) => (
                      <SelectItem key={value} value={value}>
                        {enumLabel(value)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.document_type && <p className="text-sm text-destructive">{errors.document_type.message}</p>}
              </div>
            )}
          />
          <Controller
            control={control}
            name="processing_status"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Processing status</Label>
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(ProcessingStatus).map((value) => (
                      <SelectItem key={value} value={value}>
                        {enumLabel(value)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.processing_status && (
                  <p className="text-sm text-destructive">{errors.processing_status.message}</p>
                )}
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
                  onValueChange={(value) => field.onChange(value === '' ? undefined : value)}
                  disabled={manufacturersLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select manufacturer" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Unassigned</SelectItem>
                    {manufacturersData?.manufacturers.map((manufacturer) => (
                      <SelectItem key={manufacturer.id} value={manufacturer.id}>
                        {manufacturer.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.manufacturer_id && (
                  <p className="text-sm text-destructive">{errors.manufacturer_id.message}</p>
                )}
              </div>
            )}
          />
          <Controller
            control={control}
            name="product_id"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Product</Label>
                <Select
                  value={field.value ?? ''}
                  onValueChange={(value) => field.onChange(value || undefined)}
                  disabled={productsLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select product" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Unassigned</SelectItem>
                    {productsData?.products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        {product.model_number} — {product.model_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.product_id && <p className="text-sm text-destructive">{errors.product_id.message}</p>}
              </div>
            )}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="storage_url">Storage URL</Label>
            <Input id="storage_url" type="url" {...register('storage_url')} />
            {errors.storage_url && <p className="text-sm text-destructive">{errors.storage_url.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="publish_date">Publish date</Label>
            <Input id="publish_date" type="date" {...register('publish_date')} />
            {errors.publish_date && <p className="text-sm text-destructive">{errors.publish_date.message}</p>}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="manual_review_required">Manual review required</Label>
            <Controller
              control={control}
              name="manual_review_required"
              render={({ field }) => (
                <Switch
                  id="manual_review_required"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              )}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="manual_review_notes">Manual review notes</Label>
          <Textarea id="manual_review_notes" rows={4} {...register('manual_review_notes')} />
          {errors.manual_review_notes && (
            <p className="text-sm text-destructive">{errors.manual_review_notes.message}</p>
          )}
        </div>
      </form>
    )
  },
)

DocumentForm.displayName = 'DocumentForm'

export default DocumentForm
