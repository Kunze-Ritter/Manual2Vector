// Barrel export for all page objects
export { default as BasePage } from './BasePage';
export { default as LoginPage } from './LoginPage';
export { default as DashboardPage } from './DashboardPage';
export { default as DocumentsPage } from './DocumentsPage';
export { default as ProductsPage } from './ProductsPage';
export { default as ManufacturersPage } from './ManufacturersPage';
export { default as ErrorCodesPage } from './ErrorCodesPage';
export { default as VideosPage } from './VideosPage';
export { default as MonitoringPage } from './MonitoringPage';

// Re-export types for convenience
export type { DocumentFormData } from './DocumentsPage';
export type { ProductFormData } from './ProductsPage';
export type { ManufacturerFormData } from './ManufacturersPage';
export type { ErrorCodeFormData } from './ErrorCodesPage';
export type { VideoFormData } from './VideosPage';
export type { StageMetrics, HardwareMetrics, AlertData } from './MonitoringPage';
export type { StatCard } from './DashboardPage';
