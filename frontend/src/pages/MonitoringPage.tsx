import { useMonitoringData } from '@/hooks/use-monitoring';
import { WebSocketEvent } from '@/types/api';
import { useWebSocket } from '@/hooks/use-websocket';
// import type { Page } from '@/types/api'; // removed unused import
import { useDismissAlert } from '@/hooks/use-monitoring';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Alerts,
  DataQuality,
  PipelineStatus,
  QueueStatus,
  SystemMetrics,
} from '@/components/monitoring';

export default function MonitoringPage() {
  const dismissAlert = useDismissAlert();
  const handleDismiss = (id: string) => {
    dismissAlert.mutate(id);
  };
  const {
    pipelineStatus,
    queueStatus,
    dataQuality,
    alerts,
    metrics,
    isLoading,
    error,
    refetch,
  } = useMonitoringData();

  // Set up WebSocket for real-time updates
  useWebSocket({
    enabled: true,
    onMessage: (message) => {
      switch (message.type) {
        case WebSocketEvent.PIPELINE_UPDATE:
        case WebSocketEvent.QUEUE_UPDATE:
        case WebSocketEvent.HARDWARE_UPDATE:
        case WebSocketEvent.ALERT_TRIGGERED:
          refetch();
          break;
        default:
          break;
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
    onReconnect: (attempt) => {
      console.log(`WebSocket reconnecting (attempt ${attempt})`);
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-1/3 mb-6" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading monitoring data</AlertTitle>
          <AlertDescription>
            {error.message || 'An unknown error occurred while loading monitoring data.'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const pipelineMetrics = pipelineStatus?.pipeline_metrics;
  const queueMetrics = queueStatus?.queue_metrics;
  const processingMetrics = dataQuality?.processing_metrics;
  const validationMetrics = dataQuality?.validation_metrics;
  const alertsList = alerts?.alerts ?? [];
  const hardwareMetrics = metrics?.hardware ?? pipelineStatus?.hardware_status;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Monitoring</h1>
        <p className="text-muted-foreground">
          Real-time monitoring of system performance and data processing
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="pipeline" data-testid="tab-pipeline">Pipeline</TabsTrigger>
          <TabsTrigger value="queue" data-testid="tab-queue">Queue</TabsTrigger>
          <TabsTrigger value="data-quality" data-testid="tab-data-quality">Data Quality</TabsTrigger>
          <TabsTrigger value="alerts" data-testid="tab-alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card data-testid="pipeline-status-card">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pipeline Status</CardTitle>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4 text-muted-foreground"
                >
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                </svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {pipelineMetrics ? `${Math.round(pipelineMetrics.success_rate * 100)}%` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {pipelineMetrics?.documents_processing ?? 0} processing • {pipelineMetrics?.documents_pending ?? 0} pending
                </p>
              </CardContent>
            </Card>

            <Card data-testid="queue-card">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Queue</CardTitle>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4 text-muted-foreground"
                >
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {queueMetrics?.pending_count ?? 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  {queueMetrics?.processing_count ?? 0} processing • {queueMetrics?.failed_count ?? 0} failed
                </p>
              </CardContent>
            </Card>

            <Card data-testid="data-quality-card">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Data Quality</CardTitle>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4 text-muted-foreground"
                >
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {processingMetrics ? `${Math.round(processingMetrics.success_rate * 100)}%` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {validationMetrics?.total_validation_errors ?? 0} validation errors detected
                </p>
              </CardContent>
            </Card>

            <Card data-testid="alerts-card">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4 text-muted-foreground"
                >
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                </svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {alertsList.filter((a) => !a.acknowledged).length}
                </div>
                <p className="text-xs text-muted-foreground">
                  {alerts?.total ?? alertsList.length} total alerts
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4" data-testid="system-metrics-card">
              <CardHeader>
                <CardTitle>System Metrics</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <SystemMetrics metrics={hardwareMetrics} />
              </CardContent>
            </Card>
            <Card className="col-span-3" data-testid="recent-alerts-card">
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
                <CardDescription>
                  {alerts?.total ?? alertsList.length} alerts in total
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alerts alerts={alertsList.slice(0, 5)} onDismiss={handleDismiss} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="pipeline" className="space-y-4">
          <PipelineStatus data={pipelineStatus} />
        </TabsContent>

        <TabsContent value="queue" className="space-y-4">
          <QueueStatus data={queueStatus} />
        </TabsContent>

        <TabsContent value="data-quality" className="space-y-4">
          <DataQuality data={dataQuality} />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Alerts alerts={alertsList} showAll onDismiss={handleDismiss} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
