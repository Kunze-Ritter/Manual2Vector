import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Gauge } from '@/components/ui/gauge';
import type { HardwareStatus } from '@/types/api';
import { formatNumber } from '@/lib/utils/format';

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  footer?: string;
}

const MetricCard = ({ title, value, description, footer }: MetricCardProps) => (
  <Card>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {footer && <p className="text-xs text-muted-foreground mt-1">{footer}</p>}
    </CardContent>
  </Card>
);

interface SystemMetricsProps {
  metrics?: HardwareStatus;
}

export default function SystemMetrics({ metrics }: SystemMetricsProps) {
  if (!metrics) {
    return <div>No metrics data available</div>;
  }

  const diskUsed = metrics.disk_total_gb - metrics.disk_available_gb;
  const gpuPercent = metrics.gpu_percent ?? 0;
  const hasGpu = metrics.gpu_available && metrics.gpu_percent !== null;

  const StatsGrid = () => (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
          <CardDescription>Current overall load</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{formatNumber(metrics.cpu_percent, 1)}%</div>
            <Gauge value={metrics.cpu_percent} showValue size="sm" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
          <CardDescription>Available memory</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{formatNumber(metrics.ram_percent, 1)}%</div>
            <Gauge value={metrics.ram_percent} showValue size="sm" />
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {formatNumber(metrics.ram_available_gb, 1)} GB available
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
          <CardDescription>Storage consumption</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{formatNumber(metrics.disk_usage_percent, 1)}%</div>
            <Gauge value={metrics.disk_usage_percent} showValue size="sm" />
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {formatNumber(diskUsed, 1)} GB used / {formatNumber(metrics.disk_total_gb, 1)} GB total
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">GPU Utilization</CardTitle>
          <CardDescription>{hasGpu ? 'Active accelerator detected' : 'No GPU detected'}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">
              {hasGpu ? `${formatNumber(gpuPercent, 1)}%` : 'N/A'}
            </div>
            <Gauge value={hasGpu ? gpuPercent : 0} showValue size="sm" />
          </div>
          {hasGpu && metrics.gpu_memory_total_gb !== null && metrics.gpu_memory_used_gb !== null && (
            <p className="text-xs text-muted-foreground mt-2">
              {formatNumber(metrics.gpu_memory_used_gb, 1)} GB of {formatNumber(metrics.gpu_memory_total_gb, 1)} GB
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      <StatsGrid />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="Disk Available"
          value={`${formatNumber(metrics.disk_available_gb, 1)} GB`}
          description="Free capacity"
          footer={`Last updated ${new Date(metrics.timestamp).toLocaleTimeString()}`}
        />
        <MetricCard
          title="Oldest Data Snapshot"
          value={`${formatNumber(metrics.disk_total_gb - metrics.disk_available_gb, 1)} GB`}
          description="Stored monitoring data"
        />
        <MetricCard
          title="System Health"
          value={metrics.cpu_percent < 80 && metrics.ram_percent < 80 && metrics.disk_usage_percent < 85 ? 'Nominal' : 'Attention'}
          description="Automated assessment"
        />
      </div>
    </div>
  );
}
