import { SeverityLevel } from './api';

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: SeverityLevel;
  source: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  metadata?: Record<string, unknown> | null;
  details?: Record<string, unknown> | null;
}

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  severity: SeverityLevel;
  condition: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface QueueStatusResponse {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
  items: QueueItem[];
  metrics: {
    avg_processing_time_seconds: number;
    success_rate: number;
    throughput_items_per_hour: number;
  };
}

export interface QueueItem {
  id: string;
  task_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  priority: number;
  document_id?: string | null;
  scheduled_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  retry_count: number;
  error_message?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface PipelineStatus {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'paused' | 'error';
  current_stage?: string | null;
  progress: number;
  total_items: number;
  processed_items: number;
  failed_items: number;
  start_time?: string | null;
  end_time?: string | null;
  last_updated: string;
  error?: string | null;
  stages: PipelineStage[];
}

export interface PipelineStage {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress: number;
  start_time?: string | null;
  end_time?: string | null;
  error?: string | null;
  metrics: {
    processed: number;
    failed: number;
    skipped: number;
    success_rate: number;
    avg_duration_seconds: number;
  };
}

export interface DataQualityMetrics {
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  avg_confidence_score: number;
  avg_processing_time_seconds: number;
  issues_by_type: Record<string, number>;
  issues_by_severity: Record<SeverityLevel, number>;
  last_updated: string;
}

export interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    load: number[];
  };
  memory: {
    total: number;
    used: number;
    free: number;
    usage: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    usage: number;
  };
  network: {
    rx: number;
    tx: number;
    rxRate: number;
    txRate: number;
  };
  processes: Array<{
    pid: number;
    name: string;
    cpu: number;
    memory: number;
  }>;
  timestamp: string;
}

export interface MonitoringMetrics {
  pipeline: PipelineStatus;
  queue: QueueStatusResponse;
  data_quality: DataQualityMetrics;
  system: SystemMetrics;
  alerts: Alert[];
  timestamp: string;
}

export interface WebSocketMessage<T = unknown> {
  event: string;
  data: T;
  timestamp: string;
}

export type WebSocketEvent =
  | 'metrics_update'
  | 'alert_created'
  | 'alert_updated'
  | 'pipeline_status_update'
  | 'queue_update'
  | 'system_metrics_update'
  | 'data_quality_update';

export interface WebSocketError {
  code: number;
  message: string;
  details?: unknown;
}
