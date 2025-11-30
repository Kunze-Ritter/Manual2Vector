import { forwardRef, useEffect, useImperativeHandle, useMemo } from 'react'
import { Controller, useForm, type UseFormReturn } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import { useDocuments } from '@/hooks/use-documents'
import { useManufacturers, useManufacturerSeries } from '@/hooks/use-manufacturers'
import { useProducts } from '@/hooks/use-products'
import {
  VideoPlatform,
  type Video,
  type VideoCreateInput,
  type VideoUpdateInput,
} from '@/types/api'

export interface VideoFormHandle {
  submit: () => void
  reset: (values?: VideoFormValues) => void
  getValues: () => VideoFormValues
  getForm: () => UseFormReturn<VideoFormValues>
}

export interface VideoFormSubmit {
  mode: 'create' | 'edit'
  data: VideoCreateInput | VideoUpdateInput
}

export interface VideoFormProps {
  mode: 'create' | 'edit'
  initialData?: Partial<Video>
  onSubmit: (payload: VideoFormSubmit) => void | Promise<void>
  onChange?: (values: VideoFormValues, form: UseFormReturn<VideoFormValues>) => void
  formId?: string
  className?: string
}

const optionalTrimmedString = z
  .string()
  .trim()
  .optional()

const optionalUrl = z
  .string()
  .trim()
  .optional()
  .refine((value) => {
    if (!value?.length) return true
    try {
      new URL(value)
      return true
    } catch (error) {
      return false
    }
  }, 'Must be a valid URL')

const optionalNonNegativeNumber = z
  .string()
  .trim()
  .optional()
  .refine((value) => {
    if (!value?.length) return true
    const parsed = Number(value)
    return !Number.isNaN(parsed) && parsed >= 0
  }, 'Must be zero or a positive number')

const videoFormSchema = z.object({
  title: z.string().trim().min(1, 'Title is required'),
  video_url: z.string().trim().url('Must be a valid URL'),
  platform: z.nativeEnum(VideoPlatform),
  youtube_id: optionalTrimmedString,
  description: optionalTrimmedString,
  thumbnail_url: optionalUrl,
  duration_seconds: optionalNonNegativeNumber,
  published_at: optionalTrimmedString,
  channel_id: optionalTrimmedString,
  channel_title: optionalTrimmedString,
  manufacturer_id: optionalTrimmedString,
  series_id: optionalTrimmedString,
  document_id: optionalTrimmedString,
  metadata: optionalTrimmedString,
})

export type VideoFormValues = z.infer<typeof videoFormSchema>

type BuildPayloadParams = { mode: 'create' | 'edit'; values: VideoFormValues }

type NullableString = string | null

type DetectedVideoInfo = {
  platform?: VideoPlatform
  youtubeId?: string
}

const toOptionalString = (value?: string | null | undefined): NullableString => {
  const trimmed = (value ?? '').trim()
  return trimmed.length ? trimmed : null
}

const toOptionalNumber = (value?: string | null | undefined): number | null => {
  const trimmed = (value ?? '').trim()
  if (!trimmed.length) return null
  const parsed = Number(trimmed)
  return Number.isNaN(parsed) ? null : parsed
}

const toOptionalJson = (value?: string | null | undefined): Record<string, unknown> | null => {
  const trimmed = (value ?? '').trim()
  if (!trimmed.length) return null
  try {
    const parsed = JSON.parse(trimmed)
    if (parsed && typeof parsed === 'object') {
      return parsed as Record<string, unknown>
    }
  } catch (error) {
    return null
  }
  return null
}

const parseYouTubeId = (url: string): string | undefined => {
  try {
    const parsed = new URL(url)
    const hostname = parsed.hostname.toLowerCase()
    if (hostname.includes('youtube.com')) {
      if (parsed.searchParams.has('v')) {
        return parsed.searchParams.get('v') ?? undefined
      }
      const pathSegments = parsed.pathname.split('/').filter(Boolean)
      if (pathSegments[0] === 'shorts' && pathSegments[1]) {
        return pathSegments[1]
      }
    }
    if (hostname === 'youtu.be') {
      const segment = parsed.pathname.replace('/', '')
      return segment || undefined
    }
  } catch (error) {
    // ignore parse errors
  }
  return undefined
}

const detectVideoInfo = (url?: string | null): DetectedVideoInfo => {
  if (!url) return {}
  const value = url.trim()
  if (!value) return {}

  try {
    const parsed = new URL(value)
    const hostname = parsed.hostname.toLowerCase()
    if (hostname.includes('youtube.com') || hostname === 'youtu.be') {
      return {
        platform: VideoPlatform.YOUTUBE,
        youtubeId: parseYouTubeId(value),
      }
    }
    if (hostname.includes('vimeo.com')) {
      return { platform: VideoPlatform.VIMEO }
    }
    if (hostname.includes('brightcove.com')) {
      return { platform: VideoPlatform.BRIGHTCOVE }
    }
  } catch (error) {
    return {}
  }

  return { platform: VideoPlatform.DIRECT }
}

const mapVideoToValues = (data: Partial<Video> | undefined, mode: 'create' | 'edit'): VideoFormValues => ({
  title: data?.title ?? '',
  video_url: data?.video_url ?? '',
  platform: data?.platform ?? VideoPlatform.YOUTUBE,
  youtube_id: data?.youtube_id ?? '',
  description: data?.description ?? '',
  thumbnail_url: data?.thumbnail_url ?? '',
  duration_seconds: data?.duration_seconds != null ? String(data.duration_seconds) : '',
  published_at: data?.published_at ?? '',
  channel_id: data?.channel_id ?? '',
  channel_title: data?.channel_title ?? '',
  manufacturer_id: data?.manufacturer_id ?? '',
  series_id: data?.series_id ?? '',
  document_id: data?.document_id ?? '',
  metadata: data?.metadata ? JSON.stringify(data.metadata, null, 2) : '',
})

const buildCreatePayload = (values: VideoFormValues): VideoCreateInput => ({
  title: values.title.trim(),
  video_url: values.video_url.trim(),
  platform: values.platform,
  youtube_id: toOptionalString(values.youtube_id),
  description: toOptionalString(values.description),
  thumbnail_url: toOptionalString(values.thumbnail_url),
  duration_seconds: toOptionalNumber(values.duration_seconds),
  channel_id: toOptionalString(values.channel_id),
  channel_title: toOptionalString(values.channel_title),
  published_at: toOptionalString(values.published_at),
  manufacturer_id: toOptionalString(values.manufacturer_id),
  series_id: toOptionalString(values.series_id),
  document_id: toOptionalString(values.document_id),
  metadata: toOptionalJson(values.metadata),
})

const buildUpdatePayload = (values: VideoFormValues): VideoUpdateInput => ({
  title: values.title.trim(),
  video_url: values.video_url.trim(),
  platform: values.platform,
  youtube_id: toOptionalString(values.youtube_id),
  description: toOptionalString(values.description),
  thumbnail_url: toOptionalString(values.thumbnail_url),
  duration_seconds: toOptionalNumber(values.duration_seconds),
  channel_id: toOptionalString(values.channel_id),
  channel_title: toOptionalString(values.channel_title),
  published_at: toOptionalString(values.published_at),
  manufacturer_id: toOptionalString(values.manufacturer_id),
  series_id: toOptionalString(values.series_id),
  document_id: toOptionalString(values.document_id),
  metadata: toOptionalJson(values.metadata),
})

const buildPayload = ({ mode, values }: BuildPayloadParams): VideoCreateInput | VideoUpdateInput =>
  mode === 'create' ? buildCreatePayload(values) : buildUpdatePayload(values)

export const VideoForm = forwardRef<VideoFormHandle, VideoFormProps>(
  ({ mode, initialData, onSubmit, onChange, formId = 'video-form', className }, ref) => {
    const defaultValues = useMemo(() => mapVideoToValues(initialData, mode), [initialData, mode])

    const form = useForm<VideoFormValues>({
      defaultValues,
      resolver: zodResolver(videoFormSchema),
    })

    useEffect(() => {
      form.reset(defaultValues)
    }, [defaultValues, form])

    useEffect(() => {
      if (!onChange) return
      const subscription = form.watch((values) => onChange(values as VideoFormValues, form))
      return () => subscription.unsubscribe()
    }, [form, onChange])

    const { data: documentsData, isLoading: documentsLoading } = useDocuments({ page_size: 100 })
    const { data: manufacturersData, isLoading: manufacturersLoading } = useManufacturers({ page_size: 100 })
    const selectedManufacturerId = form.watch('manufacturer_id')
    const { data: seriesData, isLoading: seriesLoading } = useManufacturerSeries(selectedManufacturerId)
    const { data: productsData } = useProducts({ page_size: 50 })

    const documents = useMemo(() => documentsData?.documents ?? [], [documentsData?.documents])
    const manufacturers = useMemo(() => manufacturersData?.manufacturers ?? [], [manufacturersData?.manufacturers])
    const series = useMemo(() => seriesData ?? [], [seriesData])
    const linkedProducts = useMemo(() => productsData?.products ?? [], [productsData?.products])

    const videoUrl = form.watch('video_url')
    const currentPlatform = form.watch('platform')
    const currentYoutubeId = form.watch('youtube_id')

    useEffect(() => {
      if (!videoUrl) return
      const detected = detectVideoInfo(videoUrl)
      if (detected.platform && detected.platform !== currentPlatform) {
        const platformField = form.getFieldState('platform')
        if (!platformField.isDirty || currentPlatform === VideoPlatform.YOUTUBE) {
          form.setValue('platform', detected.platform, { shouldDirty: true, shouldValidate: true })
        }
      }
      if (detected.youtubeId && detected.youtubeId !== currentYoutubeId) {
        form.setValue('youtube_id', detected.youtubeId, { shouldDirty: true, shouldValidate: true })
      }
    }, [currentPlatform, currentYoutubeId, form, videoUrl])

    useImperativeHandle(
      ref,
      () => ({
        submit: () =>
          form.handleSubmit((values: VideoFormValues) => onSubmit({ mode, data: buildPayload({ mode, values }) }))(),
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
        onSubmit={handleSubmit((values: VideoFormValues) => onSubmit({ mode, data: buildPayload({ mode, values }) }))}
        className={cn('space-y-6', className)}
      >
        <Tabs defaultValue="details" className="space-y-4">
          <TabsList>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input id="title" {...register('title')} />
                {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
              </div>
              <Controller
                control={control}
                name="platform"
                render={({ field }) => (
                  <div className="space-y-2">
                    <Label>Platform *</Label>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select platform" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.values(VideoPlatform).map((platform) => (
                          <SelectItem key={platform} value={platform}>
                            {platform.charAt(0).toUpperCase() + platform.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.platform && <p className="text-sm text-destructive">{errors.platform.message}</p>}
                  </div>
                )}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="video_url">Video URL *</Label>
                <Input id="video_url" type="url" {...register('video_url')} />
                {errors.video_url && <p className="text-sm text-destructive">{errors.video_url.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="youtube_id">YouTube ID</Label>
                <Input id="youtube_id" {...register('youtube_id')} placeholder="Auto-filled for YouTube videos" />
                {errors.youtube_id && <p className="text-sm text-destructive">{errors.youtube_id.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" rows={3} {...register('description')} />
              {errors.description && <p className="text-sm text-destructive">{errors.description.message}</p>}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="thumbnail_url">Thumbnail URL</Label>
                <Input id="thumbnail_url" type="url" {...register('thumbnail_url')} />
                {errors.thumbnail_url && <p className="text-sm text-destructive">{errors.thumbnail_url.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="duration_seconds">Duration (seconds)</Label>
                <Input id="duration_seconds" type="number" inputMode="numeric" min="0" {...register('duration_seconds')} />
                {errors.duration_seconds && (
                  <p className="text-sm text-destructive">{errors.duration_seconds.message}</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="published_at">Published at</Label>
                <Input id="published_at" type="date" {...register('published_at')} />
                {errors.published_at && <p className="text-sm text-destructive">{errors.published_at.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-4 rounded-md border p-3">
                <Controller
                  control={control}
                  name="channel_id"
                  render={({ field }) => (
                    <div className="space-y-2">
                      <Label htmlFor="channel_id">Channel ID</Label>
                      <Input id="channel_id" value={field.value ?? ''} onChange={field.onChange} />
                    </div>
                  )}
                />
                <Controller
                  control={control}
                  name="channel_title"
                  render={({ field }) => (
                    <div className="space-y-2">
                      <Label htmlFor="channel_title">Channel title</Label>
                      <Input id="channel_title" value={field.value ?? ''} onChange={field.onChange} />
                    </div>
                  )}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <Controller
                control={control}
                name="manufacturer_id"
                render={({ field }) => (
                  <div className="space-y-2">
                    <Label>Manufacturer</Label>
                    <Select
                      value={field.value ?? '__unassigned__'}
                      onValueChange={(value: string) => field.onChange(value === '__unassigned__' ? undefined : value)}
                      disabled={manufacturersLoading}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select manufacturer" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__unassigned__">Unassigned</SelectItem>
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
                    <Select
                      value={field.value ?? '__unassigned__'}
                      onValueChange={(value: string) => field.onChange(value === '__unassigned__' ? undefined : value)}
                      disabled={!selectedManufacturerId || seriesLoading}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select series" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__unassigned__">Unassigned</SelectItem>
                        {series.map((item) => (
                          <SelectItem key={item.id} value={item.id}>
                            {item.name}
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
                name="document_id"
                render={({ field }) => (
                  <div className="space-y-2">
                    <Label>Document</Label>
                    <Select
                      value={field.value ?? '__unassigned__'}
                      onValueChange={(value: string) => field.onChange(value === '__unassigned__' ? undefined : value)}
                      disabled={documentsLoading}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select document" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__unassigned__">Unassigned</SelectItem>
                        {documents.map((document) => (
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
            </div>

            {mode === 'edit' && initialData && (
              <div className="rounded-md border p-4">
                <h3 className="text-sm font-semibold mb-2">Engagement (read-only)</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-1">
                    <Label>Views</Label>
                    <Input value={initialData.view_count ?? '—'} readOnly />
                  </div>
                  <div className="space-y-1">
                    <Label>Likes</Label>
                    <Input value={initialData.like_count ?? '—'} readOnly />
                  </div>
                  <div className="space-y-1">
                    <Label>Comments</Label>
                    <Input value={initialData.comment_count ?? '—'} readOnly />
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="metadata" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="metadata">Metadata (JSON)</Label>
              <Textarea id="metadata" rows={8} {...register('metadata')} placeholder='{"key": "value"}' />
              {errors.metadata && <p className="text-sm text-destructive">{errors.metadata.message}</p>}
            </div>

            <div className="space-y-2">
              <Label>Linked products</Label>
              <div className="rounded-md border p-3 text-sm text-muted-foreground">
                {linkedProducts.length ? (
                  <span>Select products to link in the detail view after saving.</span>
                ) : (
                  <span>No products available. Products can be linked later.</span>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </form>
    )
  },
)

VideoForm.displayName = 'VideoForm'

export default VideoForm
