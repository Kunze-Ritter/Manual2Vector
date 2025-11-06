import type { AxiosError } from 'axios';
import type { ApiError, ApiResponse } from '@/types/api';

/**
 * Handles API errors and throws a consistent error response
 * @param error The error object from axios or other sources
 * @throws {ApiError} A standardized error format
 */
export function handleRequestError(error: unknown): never {
  // Default error response
  const defaultError: ApiError = {
    success: false,
    error: 'An unexpected error occurred',
    detail: null,
    error_code: 'UNKNOWN_ERROR',
  };

  // Handle Axios errors with response
  if (isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError | ApiResponse<unknown>>;
    
    // Network error (no response from server)
    if (!axiosError.response) {
      throw {
        ...defaultError,
        error: 'Network Error',
        detail: 'Unable to connect to the server. Please check your internet connection.',
        error_code: 'NETWORK_ERROR',
      } satisfies ApiError;
    }

    // Handle 401 Unauthorized
    if (axiosError.response.status === 401) {
      // Clear auth tokens and redirect to login
      clearAuthTokens();
      window.location.href = '/login';
      
      throw {
        ...defaultError,
        error: 'Unauthorized',
        detail: 'Your session has expired. Please log in again.',
        error_code: 'UNAUTHORIZED',
      } satisfies ApiError;
    }

    // Handle other HTTP errors with response data
    if (axiosError.response.data) {
      const responseData = axiosError.response.data;
      
      // Handle both ApiError and ApiResponse error cases
      if ('error' in responseData) {
        // This is an ApiError
        throw {
          success: false,
          error: responseData.error,
          detail: responseData.detail || null,
          error_code: responseData.error_code || 'API_ERROR',
        } satisfies ApiError;
      } else if ('success' in responseData && !responseData.success) {
        // This is a failed ApiResponse
        throw {
          success: false,
          error: responseData.message || 'Request failed',
          detail: null,
          error_code: 'API_ERROR',
        } satisfies ApiError;
      }
    }
  }

  // Handle other types of errors
  if (error instanceof Error) {
    throw {
      ...defaultError,
      error: error.message,
      detail: error.stack || null,
      error_code: 'UNKNOWN_ERROR',
    } satisfies ApiError;
  }

  // Fallback for unknown error types
  throw defaultError;
}

/**
 * Type guard to check if an error is an AxiosError
 */
function isAxiosError(error: unknown): error is AxiosError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as any).isAxiosError === true
  );
}

/**
 * Clears authentication tokens from storage
 */
function clearAuthTokens(): void {
  try {
    localStorage.removeItem('krai_auth_token');
    localStorage.removeItem('krai_refresh_token');
  } catch (error) {
    console.error('Failed to clear auth tokens:', error);
  }
}
