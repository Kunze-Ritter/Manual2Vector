import { apiClient } from './api-client'
import { handleRequestError } from './utils/error-handler'
import type { ApiResponse, DashboardOverview } from '@/types/api'

const dashboardApi = {
  async getOverview(): Promise<DashboardOverview> {
    try {
      const response = await apiClient.get<ApiResponse<DashboardOverview>>('/api/v1/dashboard/overview')

      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to load dashboard overview')
      }

      return response.data.data
    } catch (error) {
      return handleRequestError(error)
    }
  },
}

export default dashboardApi
