import { forwardRef, useEffect, useImperativeHandle, useMemo } from 'react'
import { Controller, useForm, type UseFormReturn } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import {
  type Manufacturer,
  type ManufacturerCreateInput,
  type ManufacturerUpdateInput,
} from '@/types/api'

export interface ManufacturerFormHandle {
  submit: () => void
  reset: (values?: ManufacturerFormValues) => void
  getValues: () => ManufacturerFormValues
  getForm: () => UseFormReturn<ManufacturerFormValues>
}

export interface ManufacturerFormSubmit {
  mode: 'create' | 'edit'
  data: ManufacturerCreateInput | ManufacturerUpdateInput
}

export interface ManufacturerFormProps {
  mode: 'create' | 'edit'
  initialData?: Partial<Manufacturer>
  onSubmit: (payload: ManufacturerFormSubmit) => void | Promise<void>
  onChange?: (values: ManufacturerFormValues, form: UseFormReturn<ManufacturerFormValues>) => void
  formId?: string
  className?: string
}

const optionalTrimmedString = z.string().trim().optional()

const optionalNumericString = z
  .string()
  .trim()
  .optional()
  .refine((value) => !value || !Number.isNaN(Number(value)), 'Must be a valid number')

const optionalNonNegativeNumericString = optionalNumericString.refine(
  (value) => !value || Number(value) >= 0,
  'Must be zero or a positive number',
)

const optionalPercentageString = optionalNumericString.refine(
  (value) => !value || (Number(value) >= 0 && Number(value) <= 100),
  'Must be between 0 and 100',
)

const manufacturerSchema = z
  .object({
    name: z.string().trim().min(1, 'Name is required'),
    short_name: optionalTrimmedString,
    country: optionalTrimmedString,
    founded_year: optionalNumericString.refine(
      (value) => {
        if (!value) return true
        const parsed = Number(value)
        const currentYear = new Date().getFullYear()
        return parsed >= 1800 && parsed <= currentYear
      },
      'Enter a valid year between 1800 and the current year',
    ),
    website: z.string().trim().url('Must be a valid URL (http/https)').optional(),
    support_email: z.string().trim().email('Must be a valid email address').optional(),
    support_phone: optionalTrimmedString,
    logo_url: z.string().trim().url('Must be a valid URL (http/https)').optional(),
    headquarters_address: optionalTrimmedString,
    stock_symbol: optionalTrimmedString,
    is_competitor: z.boolean(),
    market_share_percent: optionalPercentageString,
    annual_revenue_usd: optionalNonNegativeNumericString,
    employee_count: optionalNonNegativeNumericString,
    primary_business_segment: optionalTrimmedString,
    notes: optionalTrimmedString,
  })

export type ManufacturerFormValues = z.infer<typeof manufacturerSchema>

type BuildPayloadParams = { mode: 'create' | 'edit'; values: ManufacturerFormValues }

type NullableString = string | null

const toOptionalString = (value?: string): NullableString => {
  const trimmed = (value ?? '').trim()
  return trimmed ? trimmed : null
}

const toOptionalNumber = (value?: string): number | null => {
  const trimmed = (value ?? '').trim()
  if (!trimmed) return null
  const parsed = Number(trimmed)
  return Number.isNaN(parsed) ? null : parsed
}

const buildSubmitPayload = ({ mode, values }: BuildPayloadParams): ManufacturerCreateInput | ManufacturerUpdateInput => {
  const shared: ManufacturerUpdateInput = {
    name: values.name.trim(),
    short_name: toOptionalString(values.short_name),
    country: toOptionalString(values.country),
    founded_year: toOptionalNumber(values.founded_year),
    website: toOptionalString(values.website),
    support_email: toOptionalString(values.support_email),
    support_phone: toOptionalString(values.support_phone),
    logo_url: toOptionalString(values.logo_url),
    headquarters_address: toOptionalString(values.headquarters_address),
    stock_symbol: toOptionalString(values.stock_symbol),
    is_competitor: values.is_competitor,
    market_share_percent: toOptionalNumber(values.market_share_percent),
    annual_revenue_usd: toOptionalNumber(values.annual_revenue_usd),
    employee_count: toOptionalNumber(values.employee_count),
    primary_business_segment: toOptionalString(values.primary_business_segment),
  }

  if (mode === 'create') {
    return shared as ManufacturerCreateInput
  }

  return shared
}

const mapManufacturerToValues = (data: Partial<Manufacturer> | undefined): ManufacturerFormValues => ({
  name: data?.name ?? '',
  short_name: data?.short_name ?? '',
  country: data?.country ?? '',
  founded_year: data?.founded_year != null ? String(data.founded_year) : '',
  website: data?.website ?? '',
  support_email: data?.support_email ?? '',
  support_phone: data?.support_phone ?? '',
  logo_url: data?.logo_url ?? '',
  headquarters_address: data?.headquarters_address ?? '',
  stock_symbol: data?.stock_symbol ?? '',
  is_competitor: data?.is_competitor ?? false,
  market_share_percent: data?.market_share_percent != null ? String(data.market_share_percent) : '',
  annual_revenue_usd: data?.annual_revenue_usd != null ? String(data.annual_revenue_usd) : '',
  employee_count: data?.employee_count != null ? String(data.employee_count) : '',
  primary_business_segment: data?.primary_business_segment ?? '',
  notes: (data as { notes?: string })?.notes ?? '',
})

export const ManufacturerForm = forwardRef<ManufacturerFormHandle, ManufacturerFormProps>(
  ({ mode, initialData, onSubmit, onChange, formId = 'manufacturer-form', className }, ref) => {
    const defaultValues = useMemo(() => mapManufacturerToValues(initialData), [initialData])

    const form = useForm<ManufacturerFormValues>({
      defaultValues,
      resolver: zodResolver(manufacturerSchema),
    })

    useEffect(() => {
      form.reset(defaultValues)
    }, [defaultValues, form])

    useEffect(() => {
      if (!onChange) return
      const subscription = form.watch((values) => {
        onChange(values as ManufacturerFormValues, form)
      })
      return () => subscription.unsubscribe()
    }, [form, onChange])

    useImperativeHandle(
      ref,
      () => ({
        submit: () =>
          form.handleSubmit((values: ManufacturerFormValues) =>
            onSubmit({ mode, data: buildSubmitPayload({ mode, values }) }),
          )(),
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
        onSubmit={handleSubmit((values: ManufacturerFormValues) =>
          onSubmit({ mode, data: buildSubmitPayload({ mode, values }) }),
        )}
        className={cn('space-y-6', className)}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input id="name" {...register('name')} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="short_name">Short name</Label>
            <Input id="short_name" {...register('short_name')} />
            {errors.short_name && <p className="text-sm text-destructive">{errors.short_name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="country">Country</Label>
            <Input id="country" {...register('country')} />
            {errors.country && <p className="text-sm text-destructive">{errors.country.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="founded_year">Founded year</Label>
            <Input id="founded_year" type="number" inputMode="numeric" {...register('founded_year')} />
            {errors.founded_year && <p className="text-sm text-destructive">{errors.founded_year.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="website">Website</Label>
            <Input id="website" type="url" {...register('website')} />
            {errors.website && <p className="text-sm text-destructive">{errors.website.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="support_email">Support email</Label>
            <Input id="support_email" type="email" {...register('support_email')} />
            {errors.support_email && <p className="text-sm text-destructive">{errors.support_email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="support_phone">Support phone</Label>
            <Input id="support_phone" {...register('support_phone')} />
            {errors.support_phone && <p className="text-sm text-destructive">{errors.support_phone.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="logo_url">Logo URL</Label>
            <Input id="logo_url" type="url" {...register('logo_url')} />
            {errors.logo_url && <p className="text-sm text-destructive">{errors.logo_url.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="headquarters_address">Headquarters address</Label>
            <Textarea id="headquarters_address" rows={3} {...register('headquarters_address')} />
            {errors.headquarters_address && (
              <p className="text-sm text-destructive">{errors.headquarters_address.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="stock_symbol">Stock symbol</Label>
            <Input id="stock_symbol" {...register('stock_symbol')} />
            {errors.stock_symbol && <p className="text-sm text-destructive">{errors.stock_symbol.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="is_competitor" className="text-sm font-medium">
                Competitor
              </Label>
              <p className="text-xs text-muted-foreground">Mark if this manufacturer is a direct competitor</p>
            </div>
            <Controller
              control={control}
              name="is_competitor"
              render={({ field }) => <Switch id="is_competitor" checked={field.value} onCheckedChange={field.onChange} />}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="market_share_percent">Market share (%)</Label>
            <Input id="market_share_percent" type="number" inputMode="decimal" {...register('market_share_percent')} />
            {errors.market_share_percent && (
              <p className="text-sm text-destructive">{errors.market_share_percent.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="annual_revenue_usd">Annual revenue (USD)</Label>
            <Input id="annual_revenue_usd" type="number" inputMode="decimal" {...register('annual_revenue_usd')} />
            {errors.annual_revenue_usd && (
              <p className="text-sm text-destructive">{errors.annual_revenue_usd.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="employee_count">Employees</Label>
            <Input id="employee_count" type="number" inputMode="numeric" {...register('employee_count')} />
            {errors.employee_count && <p className="text-sm text-destructive">{errors.employee_count.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="primary_business_segment">Primary business segment</Label>
            <Input id="primary_business_segment" {...register('primary_business_segment')} />
            {errors.primary_business_segment && (
              <p className="text-sm text-destructive">{errors.primary_business_segment.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea id="notes" rows={4} {...register('notes')} />
            {errors.notes && <p className="text-sm text-destructive">{errors.notes.message}</p>}
          </div>
        </div>
      </form>
    )
  },
)

ManufacturerForm.displayName = 'ManufacturerForm'

export default ManufacturerForm
