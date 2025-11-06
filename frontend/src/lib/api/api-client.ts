import axios from 'axios';
import type { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { getAccessToken } from '@/lib/auth';

/**
 * Create a configured Axios instance
 */
const createApiClient = (): AxiosInstance => {
  const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  });

  // Request interceptor to add auth token
  apiClient.interceptors.request.use(
    (config) => {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
      // Handle 401 Unauthorized errors (token expired, etc.)
      if (error.response?.status === 401) {
        // You might want to redirect to login or refresh the token here
        console.error('Authentication error:', error);
      }
      return Promise.reject(error);
    }
  );

  return apiClient;
};

// Export the configured API client
export const apiClient = createApiClient();

export default apiClient;
