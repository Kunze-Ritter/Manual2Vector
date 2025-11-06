import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { PipelineStatusResponse, StageMetrics } from '@/types/api';

interface PipelineStatusProps {
  data?: PipelineStatusResponse;
}

function getStageStatus(stage: StageMetrics): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } {
  if (stage.is_active) {
    return { label: 'Running', variant: 'default' };
  }

  if (stage.failed_count > 0) {
    return { label: 'Attention', variant: 'destructive' };
  }

  if (stage.completed_count > 0 && stage.processing_count === 0 && stage.pending_count === 0) {
    return { label: 'Completed', variant: 'secondary' };
  }

  return { label: 'Idle', variant: 'outline' };
}

export default function PipelineStatus({ data }: PipelineStatusProps) {
  if (!data) {
    return <div>No pipeline data available</div>;
  }

  const { pipeline_metrics: metrics, stage_metrics: stages } = data;

  const totalTasks = metrics.total_documents;
  const completedTasks = metrics.documents_completed;
  const inProgressTasks = metrics.documents_processing;
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <Card data-testid="pipeline-status">
      <CardHeader>
        <CardTitle>Pipeline Status</CardTitle>
        <CardDescription>
          Current status of the data processing pipeline
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm text-muted-foreground">
              {completedTasks} completed / {inProgressTasks} processing / {totalTasks} total
            </span>
          </div>
          <Progress value={progress} className="h-2" data-testid="pipeline-progress" />
        </div>

        <div>
          <h3 className="text-lg font-medium mb-4">Stage Overview</h3>
          <Table data-testid="stage-metrics-table">
            <TableHeader>
              <TableRow>
                <TableHead>Stage</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Pending</TableHead>
                <TableHead className="text-right">Processing</TableHead>
                <TableHead className="text-right">Completed</TableHead>
                <TableHead className="text-right">Failed</TableHead>
                <TableHead className="text-right">Success Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {stages.map((stage) => {
                const status = getStageStatus(stage);
                return (
                  <TableRow key={stage.stage_name} data-testid="stage-row">
                    <TableCell className="font-medium">{stage.stage_name}</TableCell>
                    <TableCell>
                      <Badge variant={status.variant}>{status.label}</Badge>
                    </TableCell>
                    <TableCell className="text-right">{stage.pending_count}</TableCell>
                    <TableCell className="text-right">{stage.processing_count}</TableCell>
                    <TableCell className="text-right">{stage.completed_count}</TableCell>
                    <TableCell className="text-right">{stage.failed_count}</TableCell>
                    <TableCell className="text-right">
                      {stage.success_rate !== undefined ? `${Math.round(stage.success_rate * 100)}%` : 'N/A'}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="p-4 bg-muted/40 rounded-lg" data-testid="metric-success-rate">
            <p className="text-sm text-muted-foreground">Success Rate</p>
            <p className="text-2xl font-semibold mt-1">{Math.round(metrics.success_rate * 100)}%</p>
            <p className="text-xs text-muted-foreground mt-2">
              Average processing time: {Math.round(metrics.avg_processing_time_seconds)}s
            </p>
          </div>
          <div className="p-4 bg-muted/40 rounded-lg" data-testid="metric-throughput">
            <p className="text-sm text-muted-foreground">Throughput</p>
            <p className="text-2xl font-semibold mt-1">{metrics.current_throughput_docs_per_hour}/hr</p>
            <p className="text-xs text-muted-foreground mt-2">
              Documents processed per hour
            </p>
          </div>
          <div className="p-4 bg-muted/40 rounded-lg" data-testid="metric-failures">
            <p className="text-sm text-muted-foreground">Failures</p>
            <p className="text-2xl font-semibold mt-1">{metrics.documents_failed}</p>
            <p className="text-xs text-muted-foreground mt-2">
              Total failed documents
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
