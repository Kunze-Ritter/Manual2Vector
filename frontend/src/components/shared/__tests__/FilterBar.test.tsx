import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { FilterBar, type FilterValue } from '@/components/shared/FilterBar'

const noopFilters: Record<string, FilterValue> = {}

describe('FilterBar search debounce', () => {
  it('debounces search input changes by 300ms and only emits the latest value', () => {
    vi.useFakeTimers()

    const handleSearchChange = vi.fn()

    const { getByTestId } = render(
      <FilterBar
        searchValue=""
        onSearchChange={handleSearchChange}
        filters={[]}
        filterValues={noopFilters}
      />,
    )

    const input = getByTestId('search-input') as HTMLInputElement

    // Simulate rapid typing: multiple changes before the debounce delay elapses
    fireEvent.change(input, { target: { value: 't' } })
    fireEvent.change(input, { target: { value: 'te' } })
    fireEvent.change(input, { target: { value: 'test' } })

    // Immediately after changes: callback has not yet been invoked
    expect(handleSearchChange).not.toHaveBeenCalled()

    // Just before the debounce window expires: still no call
    vi.advanceTimersByTime(299)
    expect(handleSearchChange).not.toHaveBeenCalled()

    // After full debounce window: single call with the latest value only
    vi.advanceTimersByTime(1)
    expect(handleSearchChange).toHaveBeenCalledTimes(1)
    expect(handleSearchChange).toHaveBeenCalledWith('test')

    vi.useRealTimers()
  })
})
