/* eslint-disable @typescript-eslint/no-unused-vars */
export enum DocumentType {
  SERVICE_MANUAL = "service_manual",
  PARTS_CATALOG = "parts_catalog",
  TECHNICAL_BULLETIN = "technical_bulletin",
  CPMD_DATABASE = "cpmd_database",
  USER_MANUAL = "user_manual",
  INSTALLATION_GUIDE = "installation_guide",
  TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
}

export enum ProcessingStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_hash: string;
  storage_path: string;
  storage_url: string;
  document_type: DocumentType;
  language: string;
  version: string | null;
  publish_date: string | null;
  page_count: number | null;
  word_count: number | null;
  character_count: number | null;
  processing_status: ProcessingStatus;
  confidence_score: number | null;
  manufacturer: string | null;
  series: string | null;
  models: string[] | null;
  manual_review_required?: boolean | null;
  manual_review_notes?: string | null;
  stage_status?: Record<string, unknown> | null;
  product_id: string | null;
  manufacturer_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreateInput {
  filename: string;
  original_filename: string;
  file_size: number;
  file_hash: string;
  storage_path: string;
  storage_url: string;
  document_type: DocumentType;
  language: string;
  version?: string | null;
  publish_date?: string | null;
  page_count?: number | null;
  word_count?: number | null;
  character_count?: number | null;
  manufacturer?: string | null;
  series?: string | null;
  models?: string[] | null;
  product_id?: string | null;
  manufacturer_id?: string | null;
}

export interface DocumentUpdateInput {
  filename?: string;
  original_filename?: string;
  file_size?: number;
  file_hash?: string;
  storage_path?: string;
  storage_url?: string;
  document_type?: DocumentType;
  language?: string;
  version?: string | null;
  publish_date?: string | null;
  page_count?: number | null;
  word_count?: number | null;
  character_count?: number | null;
  processing_status?: ProcessingStatus;
  confidence_score?: number | null;
  manufacturer?: string | null;
  series?: string | null;
  models?: string[] | null;
  manual_review_required?: boolean | null;
  manual_review_notes?: string | null;
  stage_status?: Record<string, unknown> | null;
  product_id?: string | null;
  manufacturer_id?: string | null;
}

export interface DocumentFilters {
  manufacturer_id?: string;
  product_id?: string;
  document_type?: DocumentType;
  language?: string;
  processing_status?: ProcessingStatus;
  manual_review_required?: boolean;
  search?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DocumentStats {
  total_documents: number;
  by_type: Record<DocumentType, number>;
  by_status: Record<ProcessingStatus, number>;
  by_manufacturer: Record<string, number>;
}

export interface DocumentBatchResult {
  id: string;
  status: "success" | "failed";
  error?: string | null;
}

export interface DocumentBatchResponse {
  success: boolean;
  total: number;
  successful: number;
  failed: number;
  results: DocumentBatchResult[];
}

export interface Product {
  id: string;
  manufacturer_id: string;
  series_id: string | null;
  parent_product_id: string | null;
  model_number: string;
  model_name: string;
  product_type: string;
  description: string | null;
  launch_date: string | null;
  end_of_life_date: string | null;
  msrp_usd: number | null;
  currency: string | null;
  weight_kg: number | null;
  dimensions_mm: {
    width: number | null;
    height: number | null;
    depth: number | null;
  } | null;
  color_options: string[] | null;
  connectivity_options: string[] | null;
  network_capable: boolean;
  wireless_capable: boolean | null;
  mobile_print_support: boolean | null;
  print_technology: string | null;
  max_print_speed_ppm: number | null;
  max_resolution_dpi: number | null;
  max_paper_size: string | null;
  duplex_capable: boolean | null;
  supported_languages: string[] | null;
  energy_star_certified: boolean | null;
  warranty_months: number | null;
  service_manual_url: string | null;
  parts_catalog_url: string | null;
  driver_download_url: string | null;
  firmware_version: string | null;
  option_dependencies: Record<string, unknown> | null;
  replacement_parts: Record<string, unknown> | null;
  common_issues: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProductSeries {
  id: string;
  manufacturer_id: string | null;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductWithRelations extends Product {
  manufacturer?: Manufacturer | null;
  series?: ProductSeries | null;
  parent_product?: Product | null;
}

export interface ProductCreateInput {
  manufacturer_id: string;
  series_id: string | null;
  parent_product_id?: string | null;
  model_number: string;
  model_name: string;
  product_type: string;
  description?: string | null;
  launch_date?: string | null;
  end_of_life_date?: string | null;
  msrp_usd?: number | null;
  currency?: string | null;
  weight_kg?: number | null;
  dimensions_mm?: {
    width: number | null;
    height: number | null;
    depth: number | null;
  } | null;
  color_options?: string[] | null;
  connectivity_options?: string[] | null;
  network_capable?: boolean;
  wireless_capable?: boolean | null;
  mobile_print_support?: boolean | null;
  print_technology?: string | null;
  max_print_speed_ppm?: number | null;
  max_resolution_dpi?: number | null;
  max_paper_size?: string | null;
  duplex_capable?: boolean | null;
  supported_languages?: string[] | null;
  energy_star_certified?: boolean | null;
  warranty_months?: number | null;
  service_manual_url?: string | null;
  parts_catalog_url?: string | null;
  driver_download_url?: string | null;
  firmware_version?: string | null;
  option_dependencies?: Record<string, unknown> | null;
  replacement_parts?: Record<string, unknown> | null;
  common_issues?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface ProductUpdateInput {
  manufacturer_id?: string;
  series_id?: string | null;
  parent_product_id?: string | null;
  model_number?: string;
  model_name?: string;
  product_type?: string;
  description?: string | null;
  launch_date?: string | null;
  end_of_life_date?: string | null;
  msrp_usd?: number | null;
  currency?: string | null;
  weight_kg?: number | null;
  dimensions_mm?: {
    width: number | null;
    height: number | null;
    depth: number | null;
  } | null;
  color_options?: string[] | null;
  connectivity_options?: string[] | null;
  network_capable?: boolean;
  wireless_capable?: boolean | null;
  mobile_print_support?: boolean | null;
  print_technology?: string | null;
  max_print_speed_ppm?: number | null;
  max_resolution_dpi?: number | null;
  max_paper_size?: string | null;
  duplex_capable?: boolean | null;
  supported_languages?: string[] | null;
  energy_star_certified?: boolean | null;
  warranty_months?: number | null;
  service_manual_url?: string | null;
  parts_catalog_url?: string | null;
  driver_download_url?: string | null;
  firmware_version?: string | null;
  option_dependencies?: Record<string, unknown> | null;
  replacement_parts?: Record<string, unknown> | null;
  common_issues?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface ProductFilters {
  manufacturer_id?: string;
  series_id?: string;
  product_type?: string;
  launch_date_from?: string;
  launch_date_to?: string;
  min_price?: number;
  max_price?: number;
  print_technology?: string;
  network_capable?: boolean;
  search?: string;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProductTypesResponse {
  product_types: string[];
}

export interface ProductStats {
  total_products: number;
  by_type: Record<string, number>;
  by_manufacturer: Record<string, number>;
  active_products: number;
  discontinued_products: number;
}

export interface ProductBatchResult {
  id: string;
  status: "success" | "failed";
  error?: string | null;
}

export interface ProductBatchResponse {
  success: boolean;
  total: number;
  successful: number;
  failed: number;
  results: ProductBatchResult[];
}

export interface Manufacturer {
  id: string;
  name: string;
  short_name: string | null;
  country: string | null;
  founded_year: number | null;
  website: string | null;
  support_email: string | null;
  support_phone: string | null;
  logo_url: string | null;
  headquarters_address: string | null;
  stock_symbol: string | null;
  is_competitor: boolean;
  market_share_percent: number | null;
  annual_revenue_usd: number | null;
  employee_count: number | null;
  primary_business_segment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ManufacturerWithStats extends Manufacturer {
  product_count?: number;
  document_count?: number;
  series_count?: number;
}

export interface ManufacturerCreateInput {
  name: string;
  short_name?: string | null;
  country?: string | null;
  founded_year?: number | null;
  website?: string | null;
  support_email?: string | null;
  support_phone?: string | null;
  logo_url?: string | null;
  headquarters_address?: string | null;
  stock_symbol?: string | null;
  is_competitor?: boolean;
  market_share_percent?: number | null;
  annual_revenue_usd?: number | null;
  employee_count?: number | null;
  primary_business_segment?: string | null;
}

export interface ManufacturerUpdateInput {
  name?: string;
  short_name?: string | null;
  country?: string | null;
  founded_year?: number | null;
  website?: string | null;
  support_email?: string | null;
  support_phone?: string | null;
  logo_url?: string | null;
  headquarters_address?: string | null;
  stock_symbol?: string | null;
  is_competitor?: boolean;
  market_share_percent?: number | null;
  annual_revenue_usd?: number | null;
  employee_count?: number | null;
  primary_business_segment?: string | null;
}

export interface ManufacturerFilters {
  country?: string;
  is_competitor?: boolean;
  founded_year_from?: number;
  founded_year_to?: number;
  search?: string;
}

export interface ManufacturerListResponse {
  manufacturers: Manufacturer[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ManufacturerStats {
  total_manufacturers: number;
  by_country: Record<string, number>;
  competitors_count: number;
  total_market_share: number;
}

export enum SeverityLevel {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
  INFO = "info"
}

export enum ExtractionMethod {
  MANUAL = "manual",
  OCR = "ocr",
  LLM = "llm",
  HYBRID = "hybrid"
}

export interface ErrorCode {
  id: string;
  error_code: string;
  error_description: string;
  solution_text: string | null;
  chunk_id: string | null;
  document_id: string | null;
  manufacturer_id: string | null;
  page_number: number | null;
  confidence_score: number | null;
  extraction_method: ExtractionMethod | null;
  requires_technician: boolean | null;
  requires_parts: boolean | null;
  estimated_fix_time_minutes: number | null;
  severity_level: SeverityLevel;
  ai_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChunkSummary {
  id: string;
  document_id: string;
  content: string;
  tokens?: number | null;
}

export interface ErrorCodeWithRelations extends ErrorCode {
  document?: Document | null;
  manufacturer?: Manufacturer | null;
  chunk?: ChunkSummary | null;
}

export interface ErrorCodeCreateInput {
  error_code: string;
  error_description: string;
  solution_text?: string | null;
  chunk_id?: string | null;
  document_id?: string | null;
  manufacturer_id?: string | null;
  page_number?: number | null;
  confidence_score?: number | null;
  extraction_method?: ExtractionMethod | null;
  requires_technician?: boolean | null;
  requires_parts?: boolean | null;
  estimated_fix_time_minutes?: number | null;
  severity_level?: SeverityLevel;
  ai_notes?: string | null;
}

export interface ErrorCodeUpdateInput {
  error_code?: string;
  error_description?: string;
  solution_text?: string | null;
  chunk_id?: string | null;
  document_id?: string | null;
  manufacturer_id?: string | null;
  page_number?: number | null;
  confidence_score?: number | null;
  extraction_method?: ExtractionMethod | null;
  requires_technician?: boolean | null;
  requires_parts?: boolean | null;
  estimated_fix_time_minutes?: number | null;
  severity_level?: SeverityLevel;
  ai_notes?: string | null;
}

export interface ErrorCodeFilters {
  manufacturer_id?: string;
  document_id?: string;
  chunk_id?: string;
  error_code?: string;
  severity_level?: SeverityLevel;
  requires_technician?: boolean;
  requires_parts?: boolean;
  search?: string;
}

export interface ErrorCodeListResponse {
  error_codes: ErrorCode[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ErrorCodeSearchRequest {
  query: string;
  search_in?: string[];
  manufacturer_id?: string;
  severity_level?: SeverityLevel;
  limit?: number;
}

export interface ErrorCodeSearchResult {
  id: string;
  error_code: string;
  error_description: string;
  severity_level: SeverityLevel;
  confidence_score: number | null;
  document?: Document | null;
  manufacturer?: Manufacturer | null;
  chunk?: ChunkSummary | null;
}

export interface ErrorCodeSearchResponse {
  results: ErrorCodeSearchResult[];
  total: number;
  query: string;
  search_duration_ms: number;
}

export enum VideoPlatform {
  YOUTUBE = "youtube",
  VIMEO = "vimeo",
  BRIGHTCOVE = "brightcove",
  DIRECT = "direct"
}

export interface Video {
  id: string;
  title: string;
  description: string | null;
  video_url: string;
  platform: VideoPlatform;
  youtube_id: string | null;
  thumbnail_url: string | null;
  duration_seconds: number | null;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  channel_id: string | null;
  channel_title: string | null;
  published_at: string | null;
  manufacturer_id: string | null;
  series_id: string | null;
  document_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface VideoWithRelations extends Video {
  manufacturer?: Manufacturer | null;
  series?: ProductSeries | null;
  document?: Document | null;
  linked_products?: Product[];
}

export interface VideoCreateInput {
  title: string;
  video_url: string;
  platform: VideoPlatform;
  youtube_id?: string | null;
  description?: string | null;
  thumbnail_url?: string | null;
  duration_seconds?: number | null;
  view_count?: number | null;
  like_count?: number | null;
  comment_count?: number | null;
  channel_id?: string | null;
  channel_title?: string | null;
  published_at?: string | null;
  manufacturer_id?: string | null;
  series_id?: string | null;
  document_id?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface VideoUpdateInput {
  title?: string;
  video_url?: string;
  platform?: VideoPlatform;
  youtube_id?: string | null;
  description?: string | null;
  thumbnail_url?: string | null;
  duration_seconds?: number | null;
  view_count?: number | null;
  like_count?: number | null;
  comment_count?: number | null;
  channel_id?: string | null;
  channel_title?: string | null;
  published_at?: string | null;
  manufacturer_id?: string | null;
  series_id?: string | null;
  document_id?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface VideoFilters {
  manufacturer_id?: string;
  series_id?: string;
  document_id?: string;
  platform?: VideoPlatform;
  youtube_id?: string;
  search?: string;
}

export interface VideoListResponse {
  videos: Video[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VideoProductLinkRequest {
  product_ids: string[];
}

export interface VideoEnrichmentRequest {
  video_url: string;
  document_id?: string | null;
  manufacturer_id?: string | null;
}

export interface VideoEnrichmentResponse {
  success: boolean;
  video_id?: string;
  title?: string;
  platform?: VideoPlatform;
  duration?: number | null;
  error?: string | null;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export enum SortOrder {
  ASC = "asc",
  DESC = "desc"
}

// ======================
// Monitoring Types
// ======================

export enum AlertSeverity {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
  INFO = "info"
}

export enum AlertType {
  PROCESSING_FAILURE = "processing_failure",
  QUEUE_OVERFLOW = "queue_overflow",
  HARDWARE_THRESHOLD = "hardware_threshold",
  DATA_QUALITY = "data_quality",
  SYSTEM_ERROR = "system_error"
}

export enum WebSocketEvent {
  PIPELINE_UPDATE = "pipeline_update",
  QUEUE_UPDATE = "queue_update",
  HARDWARE_UPDATE = "hardware_update",
  ALERT_TRIGGERED = "alert_triggered",
  STAGE_COMPLETED = "stage_completed",
  STAGE_FAILED = "stage_failed"
}

export interface ThroughputPoint {
  timestamp: string;
  throughput: number;
}

export interface PipelineMetrics {
  total_documents: number;
  documents_pending: number;
  documents_processing: number;
  documents_completed: number;
  documents_failed: number;
  success_rate: number;
  avg_processing_time_seconds: number;
  current_throughput_docs_per_hour: number;
  throughput_history?: ThroughputPoint[];
}

export interface StageMetrics {
  stage_name: string;
  pending_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  skipped_count: number;
  avg_duration_seconds: number;
  success_rate: number;
  is_active: boolean;
  last_activity?: string;
}

export interface HardwareStatus {
  cpu_percent: number;
  ram_percent: number;
  ram_available_gb: number;
  gpu_available: boolean;
  gpu_percent: number | null;
  gpu_memory_used_gb: number | null;
  gpu_memory_total_gb: number | null;
  disk_usage_percent: number;
  disk_available_gb: number;
  disk_total_gb: number;
  timestamp: string;
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

export interface QueueMetrics {
  total_items: number;
  pending_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  avg_wait_time_seconds: number;
  by_task_type: Record<string, number>;
  oldest_item_age_seconds: number;
}

export interface QueueStatusResponse {
  queue_metrics: QueueMetrics;
  queue_items: QueueItem[];
  timestamp: string;
}

export interface PipelineStatusResponse {
  pipeline_metrics: PipelineMetrics;
  stage_metrics: StageMetrics[];
  hardware_status: HardwareStatus;
  timestamp: string;
}

export interface DuplicateMetrics {
  total_duplicates: number;
  duplicate_by_hash: number;
  duplicate_by_filename: number;
  duplicate_documents: Array<{
    document_id: string;
    filename: string;
    duplicate_type: 'hash' | 'filename';
    duplicate_of: string[];
  }>;
}

export interface ValidationMetrics {
  total_validation_errors: number;
  errors_by_stage: Record<string, number>;
  documents_with_errors: Array<{
    document_id: string;
    filename: string;
    error_count: number;
    last_error: string;
  }>;
}

export interface ProcessingMetrics {
  total_processed: number;
  successful: number;
  failed: number;
  success_rate: number;
  avg_processing_time: number;
  processing_by_type: Record<string, number>;
  recent_errors: Array<{
    timestamp: string;
    document_id: string;
    error: string;
  }>;
}

export interface DataQualityResponse {
  duplicate_metrics: DuplicateMetrics;
  validation_metrics: ValidationMetrics;
  processing_metrics: ProcessingMetrics;
  timestamp: string;
}

export interface AlertRule {
  id: string;
  name: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  threshold_value: number;
  threshold_operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  metric_key: string;
  enabled: boolean;
  notification_channels: string[];
  cooldown_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  metadata: Record<string, unknown>;
  triggered_at: string;
  acknowledged: boolean;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  resolved: boolean;
  resolved_at?: string | null;
  resolved_by?: string | null;
}

export interface AlertListResponse {
  alerts: Alert[];
  total: number;
  unacknowledged_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface WebSocketMessage<T = unknown> {
  type: WebSocketEvent;
  data: T;
  timestamp: string;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: Array<{
    name: string;
    status: 'operational' | 'degraded' | 'outage' | 'maintenance';
    updated_at: string;
    message?: string;
  }>;
  last_updated: string;
}

export interface SystemStats {
  total_documents: number;
  total_products: number;
  total_error_codes: number;
  total_videos: number;
  storage_used_gb: number;
  storage_total_gb: number;
  daily_processing_stats: Array<{
    date: string;
    processed: number;
    failed: number;
    avg_processing_time: number;
  }>;
  last_updated: string;
}

export interface SortParams {
  sort_by?: string;
  sort_order?: SortOrder;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string | null;
}

export interface ApiError {
  success: false;
  error: string;
  detail?: string | null;
  error_code?: string | null;
}
