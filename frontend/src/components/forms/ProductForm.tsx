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
import { useManufacturers, useManufacturerSeries } from '@/hooks/use-manufacturers'
import { useProducts, useProductTypes } from '@/hooks/use-products'
import {
  type ProductCreateInput,
  type ProductUpdateInput,
  type ProductWithRelations,
} from '@/types/api'

const numericString = z
  .string()
  .optional()
  .transform((value) => value?.trim())
  .refine((value) => !value || !Number.isNaN(Number(value)), 'Must be a valid number')

const positiveNumericString = numericString.refine(
  (value) => !value || Number(value) >= 0,
  'Must be zero or a positive number',
)

const dimensionsSchema = z.object({
  width: numericString,
  height: numericString,
  depth: numericString,
})

const productFormSchema = z.object({
  manufacturer_id: z.string().min(1, 'Manufacturer is required'),
  series_id: z.string().optional(),
  parent_product_id: z.string().optional(),
  model_number: z.string().min(1, 'Model number is required'),
  model_name: z.string().min(1, 'Model name is required'),
  product_type: z.string().min(1, 'Product type is required'),
  description: z.string().optional(),
  launch_date: z.string().optional(),
  end_of_life_date: z.string().optional(),
  msrp_usd: positiveNumericString,
  currency: z.string().optional(),
  weight_kg: positiveNumericString,
  dimensions: dimensionsSchema,
  color_options: z.string().optional(),
  connectivity_options: z.string().optional(),
  network_capable: z.boolean(),
  wireless_capable: z.boolean(),
  mobile_print_support: z.boolean(),
  print_technology: z.string().optional(),
  max_print_speed_ppm: positiveNumericString,
  max_resolution_dpi: positiveNumericString,
  max_paper_size: z.string().optional(),
  duplex_capable: z.boolean(),
  supported_languages: z.string().optional(),
  energy_star_certified: z.boolean(),
  warranty_months: positiveNumericString,
  service_manual_url: z.string().optional(),
  parts_catalog_url: z.string().optional(),
  driver_download_url: z.string().optional(),
  firmware_version: z.string().optional(),
  option_dependencies: z.string().optional(),
  replacement_parts: z.string().optional(),
  common_issues: z.string().optional(),
  metadata: z.string().optional(),
})

export type ProductFormValues = z.infer<typeof productFormSchema>

export interface ProductFormHandle {
  submit: () => void
  reset: (values?: ProductFormValues) => void
  getValues: () => ProductFormValues
  getForm: () => UseFormReturn<ProductFormValues>
}

export interface ProductFormSubmit {
  mode: 'create' | 'edit'
  data: ProductCreateInput | ProductUpdateInput
}

export interface ProductFormProps {
  mode: 'create' | 'edit'
  initialData?: ProductWithRelations
  onSubmit: (payload: ProductFormSubmit) => void | Promise<void>
  onChange?: (values: ProductFormValues, form: UseFormReturn<ProductFormValues>) => void
  formId?: string
  className?: string
}

const toOptionalString = (value?: string): string | null => {
  const trimmed = (value ?? '').trim()
  return trimmed ? trimmed : null
}

const toOptionalNumber = (value?: string): number | null => {
  const trimmed = (value ?? '').trim()
  if (!trimmed) return null
  const parsed = Number(trimmed)
  return Number.isNaN(parsed) ? null : parsed
}

const toOptionalStringArray = (value?: string): string[] | null => {
  if (!value) return null
  const pieces = value
    .split(',')
    .map((token) => token.trim())
    .filter(Boolean)
  return pieces.length ? pieces : null
}

const toOptionalJson = (value?: string): Record<string, unknown> | null => {
  const trimmed = (value ?? '').trim()
  if (!trimmed) return null
  try {
    const parsed = JSON.parse(trimmed)
    if (parsed && typeof parsed === 'object') {
      return parsed as Record<string, unknown>
    }
  } catch (error) {
    // handled separately by schema refinement if needed
  }
  return null
}

const mapProductToFormValues = (product: ProductWithRelations | undefined): ProductFormValues => ({
  manufacturer_id: product?.manufacturer_id ?? '',
  series_id: product?.series_id ?? undefined,
  parent_product_id: product?.parent_product_id ?? undefined,
  model_number: product?.model_number ?? '',
  model_name: product?.model_name ?? '',
  product_type: product?.product_type ?? '',
  description: product?.description ?? '',
  launch_date: product?.launch_date ?? '',
  end_of_life_date: product?.end_of_life_date ?? '',
  msrp_usd: product?.msrp_usd != null ? String(product.msrp_usd) : '',
  currency: product?.currency ?? '',
  weight_kg: product?.weight_kg != null ? String(product.weight_kg) : '',
  dimensions: {
    width: product?.dimensions_mm?.width != null ? String(product.dimensions_mm.width) : '',
    height: product?.dimensions_mm?.height != null ? String(product.dimensions_mm.height) : '',
    depth: product?.dimensions_mm?.depth != null ? String(product.dimensions_mm.depth) : '',
  },
  color_options: product?.color_options?.join(', ') ?? '',
  connectivity_options: product?.connectivity_options?.join(', ') ?? '',
  network_capable: product?.network_capable ?? false,
  wireless_capable: product?.wireless_capable ?? false,
  mobile_print_support: product?.mobile_print_support ?? false,
  print_technology: product?.print_technology ?? '',
  max_print_speed_ppm: product?.max_print_speed_ppm != null ? String(product.max_print_speed_ppm) : '',
  max_resolution_dpi: product?.max_resolution_dpi != null ? String(product.max_resolution_dpi) : '',
  max_paper_size: product?.max_paper_size ?? '',
  duplex_capable: product?.duplex_capable ?? false,
  supported_languages: product?.supported_languages?.join(', ') ?? '',
  energy_star_certified: product?.energy_star_certified ?? false,
  warranty_months: product?.warranty_months != null ? String(product.warranty_months) : '',
  service_manual_url: product?.service_manual_url ?? '',
  parts_catalog_url: product?.parts_catalog_url ?? '',
  driver_download_url: product?.driver_download_url ?? '',
  firmware_version: product?.firmware_version ?? '',
  option_dependencies: product?.option_dependencies ? JSON.stringify(product.option_dependencies, null, 2) : '',
  replacement_parts: product?.replacement_parts ? JSON.stringify(product.replacement_parts, null, 2) : '',
  common_issues: product?.common_issues ? JSON.stringify(product.common_issues, null, 2) : '',
  metadata: product?.metadata ? JSON.stringify(product.metadata, null, 2) : '',
})

const buildCreatePayload = (values: ProductFormValues): ProductCreateInput => ({
  manufacturer_id: values.manufacturer_id,
  series_id: toOptionalString(values.series_id),
  parent_product_id: toOptionalString(values.parent_product_id),
  model_number: values.model_number.trim(),
  model_name: values.model_name.trim(),
  product_type: values.product_type.trim(),
  description: toOptionalString(values.description),
  launch_date: toOptionalString(values.launch_date),
  end_of_life_date: toOptionalString(values.end_of_life_date),
  msrp_usd: toOptionalNumber(values.msrp_usd),
  currency: toOptionalString(values.currency),
  weight_kg: toOptionalNumber(values.weight_kg),
  dimensions_mm: {
    width: toOptionalNumber(values.dimensions.width),
    height: toOptionalNumber(values.dimensions.height),
    depth: toOptionalNumber(values.dimensions.depth),
  },
  color_options: toOptionalStringArray(values.color_options),
  connectivity_options: toOptionalStringArray(values.connectivity_options),
  network_capable: values.network_capable,
  wireless_capable: values.wireless_capable,
  mobile_print_support: values.mobile_print_support,
  print_technology: toOptionalString(values.print_technology),
  max_print_speed_ppm: toOptionalNumber(values.max_print_speed_ppm),
  max_resolution_dpi: toOptionalNumber(values.max_resolution_dpi),
  max_paper_size: toOptionalString(values.max_paper_size),
  duplex_capable: values.duplex_capable,
  supported_languages: toOptionalStringArray(values.supported_languages),
  energy_star_certified: values.energy_star_certified,
  warranty_months: toOptionalNumber(values.warranty_months),
  service_manual_url: toOptionalString(values.service_manual_url),
  parts_catalog_url: toOptionalString(values.parts_catalog_url),
  driver_download_url: toOptionalString(values.driver_download_url),
  firmware_version: toOptionalString(values.firmware_version),
  option_dependencies: toOptionalJson(values.option_dependencies),
  replacement_parts: toOptionalJson(values.replacement_parts),
  common_issues: toOptionalJson(values.common_issues),
  metadata: toOptionalJson(values.metadata),
})

const buildUpdatePayload = (values: ProductFormValues): ProductUpdateInput => ({
  manufacturer_id: values.manufacturer_id,
  series_id: toOptionalString(values.series_id),
  parent_product_id: toOptionalString(values.parent_product_id),
  model_number: values.model_number.trim(),
  model_name: values.model_name.trim(),
  product_type: values.product_type.trim(),
  description: toOptionalString(values.description),
  launch_date: toOptionalString(values.launch_date),
  end_of_life_date: toOptionalString(values.end_of_life_date),
  msrp_usd: toOptionalNumber(values.msrp_usd),
  currency: toOptionalString(values.currency),
  weight_kg: toOptionalNumber(values.weight_kg),
  dimensions_mm: {
    width: toOptionalNumber(values.dimensions.width),
    height: toOptionalNumber(values.dimensions.height),
    depth: toOptionalNumber(values.dimensions.depth),
  },
  color_options: toOptionalStringArray(values.color_options),
  connectivity_options: toOptionalStringArray(values.connectivity_options),
  network_capable: values.network_capable,
  wireless_capable: values.wireless_capable,
  mobile_print_support: values.mobile_print_support,
  print_technology: toOptionalString(values.print_technology),
  max_print_speed_ppm: toOptionalNumber(values.max_print_speed_ppm),
  max_resolution_dpi: toOptionalNumber(values.max_resolution_dpi),
  max_paper_size: toOptionalString(values.max_paper_size),
  duplex_capable: values.duplex_capable,
  supported_languages: toOptionalStringArray(values.supported_languages),
  energy_star_certified: values.energy_star_certified,
  warranty_months: toOptionalNumber(values.warranty_months),
  service_manual_url: toOptionalString(values.service_manual_url),
  parts_catalog_url: toOptionalString(values.parts_catalog_url),
  driver_download_url: toOptionalString(values.driver_download_url),
  firmware_version: toOptionalString(values.firmware_version),
  option_dependencies: toOptionalJson(values.option_dependencies),
  replacement_parts: toOptionalJson(values.replacement_parts),
  common_issues: toOptionalJson(values.common_issues),
  metadata: toOptionalJson(values.metadata),
})

const buildSubmitPayload = (
  mode: 'create' | 'edit',
  values: ProductFormValues,
): ProductCreateInput | ProductUpdateInput => (mode === 'create' ? buildCreatePayload(values) : buildUpdatePayload(values))

export const ProductForm = forwardRef<ProductFormHandle, ProductFormProps>(
  (
    {
      mode,
      initialData,
      onSubmit,
      onChange,
      formId = 'product-form',
      className,
    },
    ref,
  ) => {
    const defaultValues = useMemo(() => mapProductToFormValues(initialData), [initialData])

    const form = useForm<ProductFormValues>({
      defaultValues,
      resolver: zodResolver(productFormSchema),
    })

    useEffect(() => {
      form.reset(defaultValues)
    }, [defaultValues, form])

    useEffect(() => {
      if (!onChange) return
      const subscription = form.watch((values) => {
        onChange(values as ProductFormValues, form)
      })
      return () => subscription.unsubscribe()
    }, [form, onChange])

    const { data: manufacturersData, isLoading: manufacturersLoading } = useManufacturers({ page_size: 100 })
    const manufacturers = useMemo(() => manufacturersData?.manufacturers ?? [], [manufacturersData?.manufacturers])

    const { data: productsData } = useProducts({ page_size: 100 })
    const products = useMemo(() => productsData?.products ?? [], [productsData?.products])

    const selectedManufacturerId = form.watch('manufacturer_id')
    const { data: seriesData } = useManufacturerSeries(selectedManufacturerId)
    const seriesOptions = useMemo(() => seriesData ?? [], [seriesData])

    const { data: productTypes = [], isLoading: productTypesLoading } = useProductTypes()

    const formatProductTypeLabel = (type: string) =>
      type
        .split('_')
        .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
        .join(' ')

    useImperativeHandle(
      ref,
      () => ({
        submit: () => form.handleSubmit((values) => onSubmit({ mode, data: buildSubmitPayload(mode, values) }))(),
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
        onSubmit={handleSubmit((values) => onSubmit({ mode, data: buildSubmitPayload(mode, values) }))}
        className={cn('space-y-6', className)}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Controller
            control={control}
            name="manufacturer_id"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Manufacturer *</Label>
                <Select value={field.value} onValueChange={field.onChange} disabled={manufacturersLoading}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select manufacturer" />
                  </SelectTrigger>
                  <SelectContent>
                    {manufacturers.map((manufacturer) => (
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
            name="series_id"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Series</Label>
                <Select value={field.value ?? ''} onValueChange={(value) => field.onChange(value || undefined)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select series" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Unassigned</SelectItem>
                    {seriesOptions.map((series) => (
                      <SelectItem key={series.id} value={series.id}>
                        {series.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.series_id && <p className="text-sm text-destructive">{errors.series_id.message}</p>}
              </div>
            )}
          />

          <Controller
            control={control}
            name="parent_product_id"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Parent product</Label>
                <Select value={field.value ?? ''} onValueChange={(value) => field.onChange(value || undefined)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent product" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        {product.model_number} — {product.model_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.parent_product_id && (
                  <p className="text-sm text-destructive">{errors.parent_product_id.message}</p>
                )}
              </div>
            )}
          />

          <div className="space-y-2">
            <Label htmlFor="model_number">Model number *</Label>
            <Input id="model_number" {...register('model_number')} />
            {errors.model_number && <p className="text-sm text-destructive">{errors.model_number.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="model_name">Model name *</Label>
            <Input id="model_name" {...register('model_name')} />
            {errors.model_name && <p className="text-sm text-destructive">{errors.model_name.message}</p>}
          </div>

          <Controller
            control={control}
            name="product_type"
            render={({ field }) => (
              <div className="space-y-2">
                <Label>Product type *</Label>
                <Select value={field.value} onValueChange={field.onChange} disabled={productTypesLoading}>
                  <SelectTrigger>
                    <SelectValue placeholder={productTypesLoading ? 'Loading…' : 'Select product type'} />
                  </SelectTrigger>
                  <SelectContent>
                    {productTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {formatProductTypeLabel(type)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.product_type && <p className="text-sm text-destructive">{errors.product_type.message}</p>}
              </div>
            )}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" rows={3} {...register('description')} />
            {errors.description && <p className="text-sm text-destructive">{errors.description.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="launch_date">Launch date</Label>
            <Input id="launch_date" type="date" {...register('launch_date')} />
            {errors.launch_date && <p className="text-sm text-destructive">{errors.launch_date.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="end_of_life_date">End of life date</Label>
            <Input id="end_of_life_date" type="date" {...register('end_of_life_date')} />
            {errors.end_of_life_date && <p className="text-sm text-destructive">{errors.end_of_life_date.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="msrp_usd">MSRP (USD)</Label>
            <Input id="msrp_usd" type="number" step="0.01" inputMode="decimal" {...register('msrp_usd')} />
            {errors.msrp_usd && <p className="text-sm text-destructive">{errors.msrp_usd.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="currency">Currency</Label>
            <Input id="currency" maxLength={3} {...register('currency')} />
            {errors.currency && <p className="text-sm text-destructive">{errors.currency.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="weight_kg">Weight (kg)</Label>
            <Input id="weight_kg" type="number" step="0.01" inputMode="decimal" {...register('weight_kg')} />
            {errors.weight_kg && <p className="text-sm text-destructive">{errors.weight_kg.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="dimensions.width">Width (mm)</Label>
            <Input id="dimensions.width" type="number" step="0.01" inputMode="decimal" {...register('dimensions.width')} />
            {errors.dimensions?.width && <p className="text-sm text-destructive">{errors.dimensions.width.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="dimensions.height">Height (mm)</Label>
            <Input id="dimensions.height" type="number" step="0.01" inputMode="decimal" {...register('dimensions.height')} />
            {errors.dimensions?.height && <p className="text-sm text-destructive">{errors.dimensions.height.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="dimensions.depth">Depth (mm)</Label>
            <Input id="dimensions.depth" type="number" step="0.01" inputMode="decimal" {...register('dimensions.depth')} />
            {errors.dimensions?.depth && <p className="text-sm text-destructive">{errors.dimensions.depth.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="color_options">Color options (comma-separated)</Label>
            <Input id="color_options" {...register('color_options')} />
            {errors.color_options && <p className="text-sm text-destructive">{errors.color_options.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="connectivity_options">Connectivity options (comma-separated)</Label>
            <Input id="connectivity_options" {...register('connectivity_options')} />
            {errors.connectivity_options && (
              <p className="text-sm text-destructive">{errors.connectivity_options.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="print_technology">Print technology</Label>
            <Input id="print_technology" {...register('print_technology')} />
            {errors.print_technology && (
              <p className="text-sm text-destructive">{errors.print_technology.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_print_speed_ppm">Max print speed (ppm)</Label>
            <Input id="max_print_speed_ppm" type="number" inputMode="decimal" {...register('max_print_speed_ppm')} />
            {errors.max_print_speed_ppm && (
              <p className="text-sm text-destructive">{errors.max_print_speed_ppm.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_resolution_dpi">Max resolution (dpi)</Label>
            <Input id="max_resolution_dpi" type="number" inputMode="decimal" {...register('max_resolution_dpi')} />
            {errors.max_resolution_dpi && (
              <p className="text-sm text-destructive">{errors.max_resolution_dpi.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_paper_size">Max paper size</Label>
            <Input id="max_paper_size" {...register('max_paper_size')} />
            {errors.max_paper_size && <p className="text-sm text-destructive">{errors.max_paper_size.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="supported_languages">Supported languages (comma-separated)</Label>
            <Input id="supported_languages" {...register('supported_languages')} />
            {errors.supported_languages && (
              <p className="text-sm text-destructive">{errors.supported_languages.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="warranty_months">Warranty (months)</Label>
            <Input id="warranty_months" type="number" inputMode="numeric" {...register('warranty_months')} />
            {errors.warranty_months && (
              <p className="text-sm text-destructive">{errors.warranty_months.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="service_manual_url">Service manual URL</Label>
            <Input id="service_manual_url" type="url" {...register('service_manual_url')} />
            {errors.service_manual_url && (
              <p className="text-sm text-destructive">{errors.service_manual_url.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="parts_catalog_url">Parts catalog URL</Label>
            <Input id="parts_catalog_url" type="url" {...register('parts_catalog_url')} />
            {errors.parts_catalog_url && <p className="text-sm text-destructive">{errors.parts_catalog_url.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="driver_download_url">Driver download URL</Label>
            <Input id="driver_download_url" type="url" {...register('driver_download_url')} />
            {errors.driver_download_url && (
              <p className="text-sm text-destructive">{errors.driver_download_url.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="firmware_version">Firmware version</Label>
            <Input id="firmware_version" {...register('firmware_version')} />
            {errors.firmware_version && (
              <p className="text-sm text-destructive">{errors.firmware_version.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="option_dependencies">Option dependencies (JSON)</Label>
            <Textarea id="option_dependencies" rows={4} {...register('option_dependencies')} />
            {errors.option_dependencies && (
              <p className="text-sm text-destructive">{errors.option_dependencies.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="replacement_parts">Replacement parts (JSON)</Label>
            <Textarea id="replacement_parts" rows={4} {...register('replacement_parts')} />
            {errors.replacement_parts && (
              <p className="text-sm text-destructive">{errors.replacement_parts.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="common_issues">Common issues (JSON)</Label>
            <Textarea id="common_issues" rows={4} {...register('common_issues')} />
            {errors.common_issues && (
              <p className="text-sm text-destructive">{errors.common_issues.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="metadata">Metadata (JSON)</Label>
            <Textarea id="metadata" rows={4} {...register('metadata')} />
            {errors.metadata && <p className="text-sm text-destructive">{errors.metadata.message}</p>}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="network_capable" className="text-sm font-medium">
                Network capable
              </Label>
              <p className="text-xs text-muted-foreground">Supports wired network connectivity</p>
            </div>
            <Controller
              control={control}
              name="network_capable"
              render={({ field }) => (
                <Switch id="network_capable" checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="wireless_capable" className="text-sm font-medium">
                Wireless capable
              </Label>
              <p className="text-xs text-muted-foreground">Supports Wi-Fi connectivity</p>
            </div>
            <Controller
              control={control}
              name="wireless_capable"
              render={({ field }) => (
                <Switch id="wireless_capable" checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="mobile_print_support" className="text-sm font-medium">
                Mobile print support
              </Label>
              <p className="text-xs text-muted-foreground">Supports AirPrint, Mopria, etc.</p>
            </div>
            <Controller
              control={control}
              name="mobile_print_support"
              render={({ field }) => (
                <Switch id="mobile_print_support" checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="duplex_capable" className="text-sm font-medium">
                Duplex capable
              </Label>
              <p className="text-xs text-muted-foreground">Supports automatic duplex printing</p>
            </div>
            <Controller
              control={control}
              name="duplex_capable"
              render={({ field }) => (
                <Switch id="duplex_capable" checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="energy_star_certified" className="text-sm font-medium">
                ENERGY STAR certified
              </Label>
              <p className="text-xs text-muted-foreground">Meets energy efficiency standards</p>
            </div>
            <Controller
              control={control}
              name="energy_star_certified"
              render={({ field }) => (
                <Switch
                  id="energy_star_certified"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              )}
            />
          </div>
        </div>
      </form>
    )
  },
)

ProductForm.displayName = 'ProductForm'

export default ProductForm
