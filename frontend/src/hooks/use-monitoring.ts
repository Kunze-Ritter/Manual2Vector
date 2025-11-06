import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import monitoringApi from '@/lib/api/monitoring';
import type {
  PipelineStatusResponse,
  QueueStatusResponse,
  DataQualityResponse,
  AlertListResponse,
  AlertRule,
  AlertSeverity,
  PipelineMetrics,
  QueueMetrics,
  HardwareStatus,
} from '@/types/api';

// Query keys
const queryKeys = {
  pipelineStatus: ['monitoring', 'pipeline-status'],
  queueStatus: (params?: { status_filter?: string; limit?: number }) => 
    ['monitoring', 'queue-status', params],
  dataQuality: ['monitoring', 'data-quality'],
  alerts: (params?: { limit?: number; severity?: AlertSeverity; acknowledged?: boolean }) =>
    ['monitoring', 'alerts', params],
  alertRules: ['monitoring', 'alert-rules'],
  metrics: ['monitoring', 'metrics'],
};

// Pipeline status hook
export function usePipelineStatus(options = {}) {
  return useQuery<PipelineStatusResponse, Error>({
    queryKey: queryKeys.pipelineStatus,
    queryFn: () => monitoringApi.getPipelineStatus(),
    refetchInterval: 30000, // 30 seconds
    staleTime: 10000, // 10 seconds
    ...options,
  });
}

// Queue status hook
export function useQueueStatus(
  params: { status_filter?: string; limit?: number } = {},
  options = {}
) {
  return useQuery<QueueStatusResponse, Error>({
    queryKey: queryKeys.queueStatus(params),
    queryFn: () => monitoringApi.getQueueStatus(params),
    refetchInterval: 15000, // 15 seconds
    staleTime: 5000, // 5 seconds
    ...options,
  });
}

// Data quality hook
export function useDataQuality(options = {}) {
  return useQuery<DataQualityResponse, Error>({
    queryKey: queryKeys.dataQuality,
    queryFn: monitoringApi.getDataQuality,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

// Alerts hook
export function useAlerts(
  params: { limit?: number; severity?: AlertSeverity; acknowledged?: boolean } = {},
  options = {}
) {
  return useQuery<AlertListResponse, Error>({
    queryKey: queryKeys.alerts(params),
    queryFn: () => monitoringApi.getAlerts(params),
    refetchInterval: 30000, // 30 seconds
    ...options,
  });
}

// Acknowledge alert mutation
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (alertId: string) => monitoringApi.acknowledgeAlert(alertId),
    onSuccess: () => {
      // Invalidate all alerts queries to refetch
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'alerts'] });
    },
  });
}

// Dismiss alert mutation
export function useDismissAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (alertId: string) => monitoringApi.dismissAlert(alertId),
    onSuccess: () => {
      // Invalidate all alerts queries to refetch
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'alerts'] });
    },
  });
}

// Alert rules hook
export function useAlertRules(options = {}) {
  return useQuery<AlertRule[], Error>({
    queryKey: queryKeys.alertRules,
    queryFn: monitoringApi.getAlertRules,
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

// Create alert rule mutation
export function useCreateAlertRule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (rule: Omit<AlertRule, 'id' | 'created_at' | 'updated_at'>) => 
      monitoringApi.createAlertRule(rule),
    onSuccess: () => {
      // Invalidate alert rules query to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules });
    },
  });
}

// Update alert rule mutation
export function useUpdateAlertRule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, ...updates }: { id: string } & Partial<AlertRule>) => 
      monitoringApi.updateAlertRule(id, updates),
    onSuccess: () => {
      // Invalidate alert rules query to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules });
    },
  });
}

// Delete alert rule mutation
export function useDeleteAlertRule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => monitoringApi.deleteAlertRule(id),
    onSuccess: () => {
      // Invalidate alert rules query to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules });
    },
  });
}

// Metrics hook
export function useMetrics(options = {}) {
  return useQuery<{
    pipeline: PipelineMetrics;
    queue: QueueMetrics;
    hardware: HardwareStatus;
    timestamp: string;
  }, Error>({
    queryKey: queryKeys.metrics,
    queryFn: monitoringApi.getMetrics,
    refetchInterval: 10000, // 10 seconds
    staleTime: 5000, // 5 seconds
    ...options,
  });
}

// Combined hook for monitoring data
export function useMonitoringData() {
  const pipelineStatus = usePipelineStatus();
  const queueStatus = useQueueStatus({ limit: 20 });
  const dataQuality = useDataQuality();
  const alerts = useAlerts({ limit: 10, acknowledged: false });
  const metrics = useMetrics();

  const isLoading = [
    pipelineStatus.isLoading,
    queueStatus.isLoading,
    dataQuality.isLoading,
    alerts.isLoading,
    metrics.isLoading,
  ].some(Boolean);

  const error = [
    pipelineStatus.error,
    queueStatus.error,
    dataQuality.error,
    alerts.error,
    metrics.error,
  ].find(Boolean);

  return {
    pipelineStatus: pipelineStatus.data,
    queueStatus: queueStatus.data,
    dataQuality: dataQuality.data,
    alerts: alerts.data,
    metrics: metrics.data,
    isLoading,
    error,
    refetchers: {
      pipeline: pipelineStatus.refetch,
      queue: queueStatus.refetch,
      dataQuality: dataQuality.refetch,
      alerts: alerts.refetch,
      metrics: metrics.refetch,
    },
    refetchAll: () =>
      Promise.all([
        pipelineStatus.refetch(),
        queueStatus.refetch(),
        dataQuality.refetch(),
        alerts.refetch(),
        metrics.refetch(),
      ]).then(() => undefined),
    // Backwards compatibility for existing consumers
    refetch: () =>
      Promise.all([
        pipelineStatus.refetch(),
        queueStatus.refetch(),
        dataQuality.refetch(),
        alerts.refetch(),
        metrics.refetch(),
      ]).then(() => undefined),
  };
}
