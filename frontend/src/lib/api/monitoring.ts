import { apiClient } from './api-client';
import { handleRequestError } from './utils/error-handler';
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
  ProcessorHealthResponse,
  StageQueueResponse,
  StageErrorLogsResponse,
} from '@/types/api';

const monitoringApi = {
  // Pipeline Status
  async getPipelineStatus(): Promise<PipelineStatusResponse> {
    try {
      const response = await apiClient.get<PipelineStatusResponse>(
        '/api/v1/monitoring/pipeline'
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Queue Status
  async getQueueStatus(params: { limit?: number; status_filter?: string } = {}): Promise<QueueStatusResponse> {
    try {
      const query = new URLSearchParams();
      
      if (params.status_filter) {
        query.append('status_filter', params.status_filter);
      }
      
      if (params.limit) {
        query.append('limit', params.limit.toString());
      }
      
      const url = `/api/v1/monitoring/queue${query.toString() ? `?${query.toString()}` : ''}`;
      const response = await apiClient.get<QueueStatusResponse>(url);
      
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Data Quality
  async getDataQuality(): Promise<DataQualityResponse> {
    try {
      const response = await apiClient.get<DataQualityResponse>(
        '/api/v1/monitoring/data-quality'
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Alerts
  async getAlerts(params: { 
    limit?: number; 
    severity?: AlertSeverity; 
    acknowledged?: boolean 
  } = {}): Promise<AlertListResponse> {
    try {
      const query = new URLSearchParams();
      
      if (params.limit) {
        query.append('limit', params.limit.toString());
      }
      
      if (params.severity) {
        query.append('severity', params.severity);
      }
      
      if (params.acknowledged !== undefined) {
        query.append('acknowledged', params.acknowledged.toString());
      }
      
      const url = `/api/v1/monitoring/alerts${query.toString() ? `?${query.toString()}` : ''}`;
      const response = await apiClient.get<AlertListResponse>(url);
      
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Acknowledge Alert
  async acknowledgeAlert(alertId: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.post<{ success: boolean; message: string }>(
        `/api/v1/monitoring/alerts/${alertId}/acknowledge`
      );
      return { message: response.data.message };
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Dismiss Alert
  async dismissAlert(alertId: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.delete<{ success: boolean; message: string }>(
        `/api/v1/monitoring/alerts/${alertId}`
      );
      return { message: response.data.message };
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Alert Rules
  async getAlertRules(): Promise<AlertRule[]> {
    try {
      const response = await apiClient.get<AlertRule[]>(
        '/api/v1/monitoring/alert-rules'
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  async createAlertRule(rule: Omit<AlertRule, 'id' | 'created_at' | 'updated_at'>): Promise<{ id: string }> {
    try {
      const response = await apiClient.post<{ rule_id: string }>(
        '/api/v1/monitoring/alert-rules',
        rule
      );
      return { id: response.data.rule_id };
    } catch (error) {
      return handleRequestError(error);
    }
  },

  async updateAlertRule(
    ruleId: string,
    updates: Partial<Omit<AlertRule, 'id' | 'created_at' | 'updated_at'>>
  ): Promise<void> {
    try {
      await apiClient.put<void>(
        `/api/v1/monitoring/alert-rules/${ruleId}`,
        updates
      );
    } catch (error) {
      return handleRequestError(error);
    }
  },

  async deleteAlertRule(id: string): Promise<void> {
    try {
      await apiClient.delete(`/api/v1/monitoring/alert-rules/${id}`);
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Get aggregated metrics
  async getMetrics(): Promise<{ 
    pipeline: PipelineMetrics; 
    queue: QueueMetrics; 
    hardware: HardwareStatus; 
    timestamp: string 
  }> {
    try {
      const response = await apiClient.get<{
        pipeline: PipelineMetrics;
        queue: QueueMetrics;
        hardware: HardwareStatus;
        timestamp: string;
      }>('/api/v1/monitoring/metrics');
      
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Processor Health
  async getProcessorHealth(): Promise<ProcessorHealthResponse> {
    try {
      const response = await apiClient.get<ProcessorHealthResponse>(
        '/api/v1/monitoring/processors'
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Stage Queue
  async getStageQueue(stageName: string, limit: number = 50): Promise<StageQueueResponse> {
    try {
      const response = await apiClient.get<StageQueueResponse>(
        `/api/v1/monitoring/stages/${stageName}/queue`,
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Stage Errors
  async getStageErrors(stageName: string, limit: number = 100): Promise<StageErrorLogsResponse> {
    try {
      const response = await apiClient.get<StageErrorLogsResponse>(
        `/api/v1/monitoring/stages/${stageName}/errors`,
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },

  // Retry Stage
  async retryStage(stageName: string, documentId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post<{ success: boolean; message: string }>(
        `/api/v1/monitoring/stages/${stageName}/retry`,
        { document_id: documentId }
      );
      return response.data;
    } catch (error) {
      return handleRequestError(error);
    }
  },
};

export default monitoringApi;
