import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { CalendarIcon, Filter, Search, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'

export type FilterType = 'select' | 'multi-select' | 'switch' | 'date-range' | 'text' | 'number' | 'date'

export interface FilterOption {
  label: string
  value: string
}

export interface FilterDefinition {
  key: string
  label: string
  type: FilterType
  options?: FilterOption[]
  placeholder?: string
  description?: string
}

export interface DateRangeValue {
  from?: string
  to?: string
}

export type FilterValue = string | string[] | boolean | number | DateRangeValue | null | undefined

export interface FilterBarProps {
  searchValue?: string
  searchPlaceholder?: string
  onSearchChange?: (value: string) => void
  filters?: FilterDefinition[]
  filterValues?: Record<string, FilterValue>
  onFilterChange?: (key: string, value: FilterValue) => void
  onReset?: () => void
  isLoading?: boolean
  extraContent?: ReactNode
  alignmentContent?: ReactNode
  className?: string
  showSearch?: boolean
}

const isEmptyValue = (value: FilterValue): boolean => {
  if (value === undefined || value === null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (typeof value === 'number') return false
  if (typeof value === 'boolean') return false
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') {
    const range = value as DateRangeValue
    return !range.from && !range.to
  }
  return false
}

const getDisplayValue = (definition: FilterDefinition, value: FilterValue): string | null => {
  if (value === undefined || value === null) return null

  switch (definition.type) {
    case 'select': {
      const option = definition.options?.find((opt) => opt.value === value)
      return option?.label ?? String(value)
    }
    case 'multi-select': {
      const values = Array.isArray(value) ? value : []
      if (!values.length) return null
      const labels = definition.options?.filter((opt) => values.includes(opt.value)).map((opt) => opt.label)
      return labels?.length ? labels.join(', ') : values.join(', ')
    }
    case 'switch': {
      return value ? 'Yes' : 'No'
    }
    case 'date-range': {
      const range = value as DateRangeValue
      if (!range.from && !range.to) return null
      if (range.from && range.to) return `${range.from} → ${range.to}`
      if (range.from) return `From ${range.from}`
      if (range.to) return `Until ${range.to}`
      return null
    }
    case 'text':
    case 'number':
    case 'date':
      return String(value)
    default:
      return String(value)
  }
}

export function FilterBar({
  searchValue,
  searchPlaceholder = 'Search…',
  onSearchChange,
  filters = [],
  filterValues = {},
  onFilterChange,
  onReset,
  isLoading = false,
  extraContent,
  alignmentContent,
  className,
  showSearch = true,
}: FilterBarProps) {
  const [internalSearch, setInternalSearch] = useState(searchValue ?? '')
  const searchDebounceRef = useRef<number | null>(null)

  useEffect(() => {
    setInternalSearch(searchValue ?? '')
  }, [searchValue])

  useEffect(() => {
    return () => {
      if (searchDebounceRef.current !== null) {
        window.clearTimeout(searchDebounceRef.current)
      }
    }
  }, [])

  const handleSearchInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextValue = event.target.value
    setInternalSearch(nextValue)

    if (!onSearchChange) return

    if (searchDebounceRef.current !== null) {
      window.clearTimeout(searchDebounceRef.current)
    }

    searchDebounceRef.current = window.setTimeout(() => {
      onSearchChange(nextValue)
    }, 300)
  }

  const activeFilters = useMemo(() => {
    return filters.reduce<Record<string, FilterValue>>((acc, filter) => {
      const value = filterValues[filter.key]
      if (!isEmptyValue(value)) {
        acc[filter.key] = value
      }
      return acc
    }, {})
  }, [filters, filterValues])

  const hasActiveFilters = Object.keys(activeFilters).length > 0

  return (
    <div className={cn('flex flex-col gap-3 rounded-md border border-border bg-card p-4 shadow-sm', className)} data-testid="filter-bar">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-1 flex-wrap items-center gap-2">
          {showSearch && (
            <div className="flex w-full items-center gap-2 md:w-64">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                value={internalSearch}
                onChange={handleSearchInputChange}
                placeholder={searchPlaceholder}
                disabled={isLoading || !onSearchChange}
                data-testid="search-input"
              />
            </div>
          )}

          {filters.map((filter) => {
            const value = filterValues[filter.key]
            switch (filter.type) {
              case 'text':
                return (
                  <Input
                    key={filter.key}
                    type="text"
                    value={typeof value === 'string' ? value : ''}
                    placeholder={filter.placeholder ?? filter.label}
                    onChange={(event) => onFilterChange?.(filter.key, event.target.value)}
                    disabled={isLoading}
                    className="w-48"
                    data-testid={`filter-${filter.key}-value`}
                  />
                )
              case 'number': {
                const numberValue = typeof value === 'number' && !Number.isNaN(value) ? value : undefined
                return (
                  <Input
                    key={filter.key}
                    type="number"
                    value={numberValue ?? ''}
                    placeholder={filter.placeholder ?? filter.label}
                    onChange={(event) => {
                      const raw = event.target.value
                      if (raw === '') {
                        onFilterChange?.(filter.key, undefined)
                        return
                      }
                      const parsed = Number(raw)
                      onFilterChange?.(filter.key, Number.isNaN(parsed) ? undefined : parsed)
                    }}
                    disabled={isLoading}
                    className="w-40"
                    data-testid={`filter-${filter.key}-value`}
                  />
                )
              }
              case 'date':
                return (
                  <Input
                    key={filter.key}
                    type="date"
                    value={typeof value === 'string' ? value : ''}
                    placeholder={filter.placeholder ?? filter.label}
                    onChange={(event) => {
                      const raw = event.target.value
                      onFilterChange?.(filter.key, raw || undefined)
                    }}
                    disabled={isLoading}
                    className="w-48"
                    data-testid={`filter-${filter.key}-value`}
                  />
                )
              case 'select':
                return (
                  <Select
                    key={filter.key}
                    value={typeof value === 'string' ? value : ''}
                    onValueChange={(newValue) => onFilterChange?.(filter.key, newValue)}
                    disabled={isLoading}
                  >
                    <SelectTrigger className="w-48" data-testid={`filter-${filter.key}`}>
                      <SelectValue placeholder={filter.placeholder ?? filter.label} />
                    </SelectTrigger>
                    <SelectContent>
                      {filter.options?.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )
              case 'multi-select': {
                const selectedValues = Array.isArray(value) ? value : []
                return (
                  <Popover key={filter.key}>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="justify-between" data-testid={`filter-${filter.key}`}>
                        <span className="flex items-center gap-1">
                          <Filter className="h-4 w-4" />
                          {filter.label}
                        </span>
                        {selectedValues.length > 0 && <Badge>{selectedValues.length}</Badge>}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-56 space-y-2" align="start">
                      <div className="text-sm font-medium">{filter.label}</div>
                      <div className="space-y-1">
                        {filter.options?.map((option) => {
                          const checked = selectedValues.includes(option.value)
                          return (
                            <label
                              key={option.value}
                              className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1 hover:bg-muted"
                            >
                              <Checkbox
                                checked={checked}
                                onCheckedChange={(next) => {
                                  const isChecked = next === true
                                  const nextValues = isChecked
                                    ? Array.from(new Set([...selectedValues, option.value]))
                                    : selectedValues.filter((item) => item !== option.value)
                                  onFilterChange?.(filter.key, nextValues)
                                }}
                              />
                              <span className="text-sm">{option.label}</span>
                            </label>
                          )
                        })}
                      </div>
                    </PopoverContent>
                  </Popover>
                )
              }
              case 'switch':
                return (
                  <label key={filter.key} className="flex items-center gap-2 text-sm font-medium text-foreground">
                    <Switch
                      checked={Boolean(value)}
                      onCheckedChange={(checked) => onFilterChange?.(filter.key, checked)}
                      disabled={isLoading}
                      data-testid={`filter-${filter.key}-value`}
                    />
                    {filter.label}
                  </label>
                )
              case 'date-range': {
                const range = (value as DateRangeValue) ?? {}
                return (
                  <div key={filter.key} className="flex items-center gap-2">
                    <div className="flex items-center gap-2 rounded-md border border-input px-3 py-2">
                      <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                      <input
                        type="date"
                        value={range.from ?? ''}
                        onChange={(event) =>
                          onFilterChange?.(filter.key, {
                            ...range,
                            from: event.target.value || undefined,
                          })
                        }
                        className="border-none bg-transparent text-sm outline-none"
                        disabled={isLoading}
                        data-testid={`filter-${filter.key}-value`}
                      />
                      <span className="text-muted-foreground">–</span>
                      <input
                        type="date"
                        value={range.to ?? ''}
                        onChange={(event) =>
                          onFilterChange?.(filter.key, {
                            ...range,
                            to: event.target.value || undefined,
                          })
                        }
                        className="border-none bg-transparent text-sm outline-none"
                        disabled={isLoading}
                        data-testid={`filter-${filter.key}-value`}
                      />
                    </div>
                  </div>
                )
              }
              default:
                return null
            }
          })}
        </div>

        <div className="flex items-center gap-2">
          {extraContent}
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={() => onReset?.()} disabled={isLoading} data-testid="reset-filters-button">
              Reset
            </Button>
          )}
          {alignmentContent}
        </div>
      </div>

      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          {filters.map((filter) => {
            const value = activeFilters[filter.key]
            if (value === undefined) return null
            const displayValue = getDisplayValue(filter, value)
            if (!displayValue) return null
            return (
              <Badge key={filter.key} variant="secondary" className="flex items-center gap-2">
                <span className="font-medium">{filter.label}:</span>
                <span>{displayValue}</span>
                <button
                  type="button"
                  className="rounded-full p-0.5 text-muted-foreground transition-colors hover:text-foreground"
                  onClick={() => onFilterChange?.(filter.key, undefined)}
                >
                  <X className="h-3 w-3" />
                  <span className="sr-only">Clear filter {filter.label}</span>
                </button>
              </Badge>
            )
          })}
        </div>
      )}
    </div>
  )
}
