import { useQuery } from '@tanstack/react-query'
import dashboardApi from '@/lib/api/dashboard'
import type { DashboardOverview } from '@/types/api'

const DASHBOARD_QUERY_KEY = ['dashboard', 'overview']

export function useDashboardOverview(options = {}) {
  return useQuery<DashboardOverview, Error>({
    queryKey: DASHBOARD_QUERY_KEY,
    queryFn: () => dashboardApi.getOverview(),
    // Avoid aggressive polling/retries while the dashboard API is unstable
    staleTime: 60_000,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    ...options,
  })
}
