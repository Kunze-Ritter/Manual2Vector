/**
 * Standardized toast messages for consistent user feedback
 * Use these functions to ensure uniform messaging across the application
 */

export type ToastMessage = {
  title: string
  description: string
}

// ============================================================================
// CRUD Operations
// ============================================================================

export const TOAST_MESSAGES = {
  // Create
  CREATE_SUCCESS: (entity: string): ToastMessage => ({
    title: `${entity} created`,
    description: `The ${entity.toLowerCase()} has been added successfully.`
  }),

  CREATE_FAILED: (entity: string): ToastMessage => ({
    title: `Failed to create ${entity.toLowerCase()}`,
    description: 'An error occurred. Please try again.'
  }),

  // Update
  UPDATE_SUCCESS: (entity: string): ToastMessage => ({
    title: `${entity} updated`,
    description: 'Changes saved successfully.'
  }),

  UPDATE_FAILED: (entity: string): ToastMessage => ({
    title: `Failed to update ${entity.toLowerCase()}`,
    description: 'An error occurred. Please try again.'
  }),

  // Delete
  DELETE_SUCCESS: (entity: string): ToastMessage => ({
    title: `${entity} deleted`,
    description: `The ${entity.toLowerCase()} has been removed.`
  }),

  DELETE_FAILED: (entity: string): ToastMessage => ({
    title: `Failed to delete ${entity.toLowerCase()}`,
    description: 'An error occurred. Please try again.'
  }),

  // Batch Delete
  BATCH_DELETE_SUCCESS: (count: number, entity: string): ToastMessage => ({
    title: `${count} ${entity.toLowerCase()}s deleted`,
    description: `Successfully removed ${count} items.`
  }),

  BATCH_DELETE_FAILED: (entity: string): ToastMessage => ({
    title: `Failed to delete ${entity.toLowerCase()}s`,
    description: 'An error occurred. Please try again.'
  }),

  // Generic Operation
  OPERATION_SUCCESS: (operation: string): ToastMessage => ({
    title: `${operation} successful`,
    description: 'The operation completed successfully.'
  }),

  OPERATION_FAILED: (operation: string): ToastMessage => ({
    title: `${operation} failed`,
    description: 'An error occurred. Please try again.'
  })
}

// ============================================================================
// Network & API Errors
// ============================================================================

export const NETWORK_ERRORS = {
  CONNECTION_FAILED: (): ToastMessage => ({
    title: 'Connection failed',
    description: 'Could not connect to the server. Please check your internet connection.'
  }),

  TIMEOUT: (): ToastMessage => ({
    title: 'Request timeout',
    description: 'The request took too long. Please try again.'
  }),

  SERVER_ERROR: (): ToastMessage => ({
    title: 'Server error',
    description: 'The server encountered an error. Please try again later.'
  }),

  UNAUTHORIZED: (): ToastMessage => ({
    title: 'Unauthorized',
    description: 'You do not have permission to perform this action.'
  }),

  NOT_FOUND: (entity: string): ToastMessage => ({
    title: `${entity} not found`,
    description: `The requested ${entity.toLowerCase()} could not be found.`
  })
}

// ============================================================================
// Validation Errors
// ============================================================================

export const VALIDATION_ERRORS = {
  REQUIRED_FIELD: (field: string): ToastMessage => ({
    title: 'Validation error',
    description: `${field} is required.`
  }),

  INVALID_FORMAT: (field: string): ToastMessage => ({
    title: 'Validation error',
    description: `${field} has an invalid format.`
  }),

  INVALID_EMAIL: (): ToastMessage => ({
    title: 'Validation error',
    description: 'Please enter a valid email address.'
  }),

  INVALID_URL: (): ToastMessage => ({
    title: 'Validation error',
    description: 'Please enter a valid URL.'
  }),

  PASSWORD_MISMATCH: (): ToastMessage => ({
    title: 'Validation error',
    description: 'Passwords do not match.'
  }),

  MIN_LENGTH: (field: string, length: number): ToastMessage => ({
    title: 'Validation error',
    description: `${field} must be at least ${length} characters.`
  }),

  MAX_LENGTH: (field: string, length: number): ToastMessage => ({
    title: 'Validation error',
    description: `${field} must be at most ${length} characters.`
  })
}

// ============================================================================
// File Upload
// ============================================================================

export const UPLOAD_MESSAGES = {
  UPLOAD_SUCCESS: (count: number = 1): ToastMessage => ({
    title: count === 1 ? 'File uploaded' : `${count} files uploaded`,
    description: count === 1 ? 'The file has been uploaded successfully.' : `Successfully uploaded ${count} files.`
  }),

  UPLOAD_FAILED: (): ToastMessage => ({
    title: 'Upload failed',
    description: 'An error occurred while uploading the file.'
  }),

  FILE_TOO_LARGE: (maxSize: string): ToastMessage => ({
    title: 'File too large',
    description: `File size must be less than ${maxSize}.`
  }),

  INVALID_FILE_TYPE: (allowedTypes: string): ToastMessage => ({
    title: 'Invalid file type',
    description: `Only ${allowedTypes} files are allowed.`
  }),

  UPLOAD_IN_PROGRESS: (): ToastMessage => ({
    title: 'Uploading...',
    description: 'Please wait while the file is being uploaded.'
  })
}

// ============================================================================
// Authentication
// ============================================================================

export const AUTH_MESSAGES = {
  LOGIN_SUCCESS: (): ToastMessage => ({
    title: 'Login successful',
    description: 'Welcome back!'
  }),

  LOGIN_FAILED: (): ToastMessage => ({
    title: 'Login failed',
    description: 'Invalid email or password.'
  }),

  LOGOUT_SUCCESS: (): ToastMessage => ({
    title: 'Logged out',
    description: 'You have been logged out successfully.'
  }),

  SESSION_EXPIRED: (): ToastMessage => ({
    title: 'Session expired',
    description: 'Please log in again.'
  }),

  PASSWORD_CHANGED: (): ToastMessage => ({
    title: 'Password changed',
    description: 'Your password has been updated successfully.'
  })
}

// ============================================================================
// Processing & Background Tasks
// ============================================================================

export const PROCESSING_MESSAGES = {
  PROCESSING_STARTED: (task: string): ToastMessage => ({
    title: `${task} started`,
    description: 'Your request is being processed.'
  }),

  PROCESSING_COMPLETE: (task: string): ToastMessage => ({
    title: `${task} complete`,
    description: 'The task has been completed successfully.'
  }),

  PROCESSING_FAILED: (task: string): ToastMessage => ({
    title: `${task} failed`,
    description: 'An error occurred during processing.'
  })
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get a custom error message with fallback
 */
export function getErrorMessage(error: unknown, fallback: string = 'An unexpected error occurred'): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return fallback
}

/**
 * Create a custom toast message
 */
export function createToastMessage(title: string, description: string): ToastMessage {
  return { title, description }
}
