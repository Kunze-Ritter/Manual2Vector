import { format as formatDateFns, formatDistanceToNow } from 'date-fns'
import { type ProcessingStatus, type SeverityLevel, AlertSeverity, AlertType } from '@/types/api'

export function formatDate(date: string | Date, dateFormat = 'yyyy-MM-dd'): string {
  if (!date) return '-'
  const value = typeof date === 'string' ? new Date(date) : date
  if (Number.isNaN(value.getTime())) return '-'
  return formatDateFns(value, dateFormat)
}

export function formatDateTime(date: string | Date, dateFormat = 'yyyy-MM-dd HH:mm'): string {
  return formatDate(date, dateFormat)
}

export function formatRelativeTime(date: string | Date): string {
  if (!date) return '-'
  const value = typeof date === 'string' ? new Date(date) : date
  if (Number.isNaN(value.getTime())) return '-'
  return formatDistanceToNow(value, { addSuffix: true })
}

export function formatNumber(num: number, decimals = 0): string {
  if (num === null || num === undefined) return '-'
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

export function formatCurrency(amount: number, currency = 'USD'): string {
  if (amount === null || amount === undefined) return '-'
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
  }).format(amount)
}

export function formatPercentage(value: number, decimals = 1): string {
  if (value === null || value === undefined) return '-'
  return `${formatNumber(value, decimals)}%`
}

export function formatFileSize(bytes: number): string {
  if (bytes === null || bytes === undefined || Number.isNaN(bytes)) return '-'
  if (bytes === 0) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = bytes / 1024 ** i
  return `${formatNumber(size, size >= 100 ? 0 : 1)} ${sizes[i]}`
}

export function formatDuration(seconds: number): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return '-'
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  const parts = [
    hrs > 0 ? String(hrs).padStart(2, '0') : null,
    String(mins).padStart(hrs > 0 ? 2 : 1, '0'),
    String(secs).padStart(2, '0'),
  ].filter(Boolean)
  return parts.join(':')
}

export function truncate(text: string, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}…`
}

export function capitalize(text: string): string {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function toTitleCase(text: string): string {
  if (!text) return ''
  return text
    .toLowerCase()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function getStatusBadgeVariant(status: ProcessingStatus): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'completed':
      return 'default'
    case 'in_progress':
      return 'secondary'
    case 'failed':
    case 'cancelled':
      return 'destructive'
    default:
      return 'outline'
  }
}

export function getSeverityBadgeVariant(severity: SeverityLevel): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (severity) {
    case 'critical':
      return 'destructive'
    case 'high':
      return 'secondary'
    case 'medium':
      return 'default'
    case 'low':
    case 'info':
      return 'outline'
    default:
      return 'default'
  }
}

export function getAlertSeverityBadgeVariant(severity: AlertSeverity): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (severity) {
    case AlertSeverity.CRITICAL:
      return 'destructive'
    case AlertSeverity.HIGH:
      return 'secondary'
    case AlertSeverity.MEDIUM:
      return 'default'
    case AlertSeverity.LOW:
    case AlertSeverity.INFO:
      return 'outline'
    default:
      return 'outline'
  }
}

export function getAlertTypeIcon(type: AlertType): string {
  switch (type) {
    case AlertType.PROCESSING_FAILURE:
      return 'AlertCircle'
    case AlertType.QUEUE_OVERFLOW:
      return 'Layers'
    case AlertType.HARDWARE_THRESHOLD:
      return 'Cpu'
    case AlertType.DATA_QUALITY:
      return 'Database'
    case AlertType.SYSTEM_ERROR:
    default:
      return 'XCircle'
  }
}
