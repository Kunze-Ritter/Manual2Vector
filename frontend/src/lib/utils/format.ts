/**
 * Format bytes as human-readable text.
 * 
 * @param bytes Number of bytes.
 * @param si True to use metric (SI) units, aka powers of 1000. False to use 
 *           binary (IEC) units, aka powers of 1024.
 * @param dp Number of decimal places to display.
 * @returns Formatted string.
 */
export function formatBytes(bytes: number, si = false, dp = 1): string {
  if (bytes === 0) return '0 B';

  const thresh = si ? 1000 : 1024;
  const units = si 
    ? ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];

  let u = -1;
  let r = bytes;

  while (Math.abs(r) >= thresh && u < units.length - 1) {
    r /= thresh;
    u++;
  }

  return `${r.toFixed(dp)} ${units[u]}`;
}

/**
 * Format a duration in milliseconds to a human-readable string.
 * 
 * @param ms Duration in milliseconds.
 * @returns Formatted duration string.
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = Math.floor(ms / 1000) % 60;
  const minutes = Math.floor(ms / (1000 * 60)) % 60;
  const hours = Math.floor(ms / (1000 * 60 * 60));

  const parts: string[] = [];
  
  if (hours > 0) {
    parts.push(`${hours}h`);
  }
  
  if (minutes > 0 || hours > 0) {
    parts.push(`${minutes}m`);
  }
  
  parts.push(`${seconds}s`);
  
  return parts.join(' ');
}

/**
 * Format a number with a fixed number of decimal places.
 * 
 * @param value The number to format.
 * @param decimals Number of decimal places.
 * @returns Formatted number string.
 */
export function formatNumber(value: number, decimals = 1): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format a percentage value.
 * 
 * @param value The value to format (0-1).
 * @param decimals Number of decimal places.
 * @returns Formatted percentage string.
 */
export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a date as a relative time string.
 * 
 * @param date The date to format.
 * @returns Relative time string (e.g., "2 minutes ago").
 */
export function formatRelativeTime(date: Date | string | number): string {
  const now = new Date();
  const target = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - target.getTime()) / 1000);
  
  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
    second: 1,
  } as const;
  
  for (const [unit, secondsInUnit] of Object.entries(intervals)) {
    const interval = Math.floor(diffInSeconds / secondsInUnit);
    
    if (interval >= 1) {
      return interval === 1 
        ? `1 ${unit} ago` 
        : `${interval} ${unit}s ago`;
    }
  }
  
  return 'just now';
}
