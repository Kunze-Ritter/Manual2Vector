/**
 * Default values and constants for DataTable components
 * Use these to ensure consistency across all table implementations
 */

// ============================================================================
// Pagination Defaults
// ============================================================================

/**
 * Default number of items per page
 */
export const DEFAULT_PAGE_SIZE = 20

/**
 * Available page size options for user selection
 */
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

/**
 * Default starting page
 */
export const DEFAULT_PAGE = 1

// ============================================================================
// Empty State Messages
// ============================================================================

/**
 * Default message when no data is available
 */
export const DEFAULT_EMPTY_MESSAGE = 'No data available'

/**
 * Entity-specific empty messages
 */
export const EMPTY_MESSAGES = {
  documents: 'No documents found',
  products: 'No products found',
  manufacturers: 'No manufacturers found',
  users: 'No users found',
  categories: 'No categories found',
  tags: 'No tags found'
} as const

// ============================================================================
// Loading State Defaults
// ============================================================================

/**
 * Number of skeleton rows to show during loading
 */
export const DEFAULT_SKELETON_ROWS = 10

// ============================================================================
// Sorting Defaults
// ============================================================================

/**
 * Default sort direction
 */
export const DEFAULT_SORT_DIRECTION = 'asc' as const

/**
 * Common sort fields
 */
export const COMMON_SORT_FIELDS = {
  name: 'name',
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  status: 'status'
} as const

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get empty message for a specific entity type
 */
export function getEmptyMessage(entity: keyof typeof EMPTY_MESSAGES): string {
  return EMPTY_MESSAGES[entity] ?? DEFAULT_EMPTY_MESSAGE
}

/**
 * Calculate total pages from total items and page size
 */
export function calculateTotalPages(totalItems: number, pageSize: number): number {
  return Math.ceil(totalItems / pageSize)
}

/**
 * Validate page number is within bounds
 */
export function validatePage(page: number, totalPages: number): number {
  if (page < 1) return 1
  if (page > totalPages) return totalPages
  return page
}

/**
 * Validate page size is in allowed options
 */
export function validatePageSize(pageSize: number): number {
  if (!PAGE_SIZE_OPTIONS.includes(pageSize)) {
    return DEFAULT_PAGE_SIZE
  }
  return pageSize
}
