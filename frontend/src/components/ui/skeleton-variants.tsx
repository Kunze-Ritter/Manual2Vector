/**
 * Pre-built skeleton variants for common loading patterns
 */

import { Skeleton } from '@/components/ui/skeleton'

// ============================================================================
// Text Skeleton
// ============================================================================

type SkeletonTextProps = {
  lines?: number
}

export function SkeletonText({ lines = 3 }: SkeletonTextProps) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  )
}

// ============================================================================
// Card Skeleton
// ============================================================================

export function SkeletonCard() {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <Skeleton className="h-6 w-1/3" />
      <SkeletonText lines={2} />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  )
}

// ============================================================================
// Table Skeleton
// ============================================================================

type SkeletonTableProps = {
  rows?: number
  cols?: number
}

export function SkeletonTable({ rows = 5, cols = 4 }: SkeletonTableProps) {
  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex gap-4 pb-2 border-b">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-6 flex-1" />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} className="h-10 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// List Skeleton
// ============================================================================

type SkeletonListProps = {
  items?: number
}

export function SkeletonList({ items = 5 }: SkeletonListProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// Form Skeleton
// ============================================================================

type SkeletonFormProps = {
  fields?: number
}

export function SkeletonForm({ fields = 6 }: SkeletonFormProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// Avatar Skeleton
// ============================================================================

type SkeletonAvatarProps = {
  size?: 'sm' | 'md' | 'lg'
}

export function SkeletonAvatar({ size = 'md' }: SkeletonAvatarProps) {
  const sizeClass = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12'
  }[size]

  return <Skeleton className={`${sizeClass} rounded-full`} />
}

// ============================================================================
// Grid Skeleton
// ============================================================================

type SkeletonGridProps = {
  items?: number
  cols?: number
}

export function SkeletonGrid({ items = 6, cols = 3 }: SkeletonGridProps) {
  const gridClass = {
    1: '',
    2: 'md:grid-cols-2',
    3: 'md:grid-cols-3',
    4: 'md:grid-cols-4'
  }[cols]

  return (
    <div className={`grid gap-4 ${gridClass}`}>
      {Array.from({ length: items }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}
