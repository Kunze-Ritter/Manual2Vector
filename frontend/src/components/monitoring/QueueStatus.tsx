import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { QueueStatusResponse, QueueItem } from '@/types/api';
import { formatDuration, formatRelativeTime } from '@/lib/utils/format';

interface QueueStatusProps {
  data?: QueueStatusResponse;
}

const statusVariant: Record<QueueItem['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  processing: 'default',
  completed: 'outline',
  failed: 'destructive',
};

function calculateDuration(item: QueueItem): string {
  if (!item.started_at) return '—';
  const start = new Date(item.started_at).getTime();
  const end = item.completed_at ? new Date(item.completed_at).getTime() : Date.now();
  return formatDuration(end - start);
}

export default function QueueStatus({ data }: QueueStatusProps) {
  if (!data) {
    return <div>No queue data available</div>;
  }

  const metrics = data.queue_metrics;
  const queueItems = data.queue_items;

  const totalItems = metrics.total_items;
  const completedItems = metrics.completed_count;
  const failedItems = metrics.failed_count;
  const processingItems = metrics.processing_count;
  const pendingItems = metrics.pending_count;

  const progress = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

  const recentItems = [...queueItems]
    .sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime())
    .slice(0, 7);

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Queue Status</CardTitle>
            <CardDescription>
              Monitoring document processing tasks
            </CardDescription>
          </div>
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            <div className="rounded-md bg-blue-500/10 px-3 py-2">
              <div className="text-sm font-semibold">{processingItems}</div>
              <div className="text-muted-foreground">Processing</div>
            </div>
            <div className="rounded-md bg-amber-500/10 px-3 py-2">
              <div className="text-sm font-semibold">{pendingItems}</div>
              <div className="text-muted-foreground">Pending</div>
            </div>
            <div className="rounded-md bg-emerald-500/10 px-3 py-2">
              <div className="text-sm font-semibold">{completedItems}</div>
              <div className="text-muted-foreground">Completed</div>
            </div>
            <div className="rounded-md bg-red-500/10 px-3 py-2">
              <div className="text-sm font-semibold">{failedItems}</div>
              <div className="text-muted-foreground">Failed</div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex justify-between mb-2 text-sm">
            <span className="font-medium">Queue Progress</span>
            <span className="text-muted-foreground">
              {completedItems} completed, {processingItems} processing
            </span>
          </div>
          <Progress value={progress} className="h-2" />
          <p className="mt-2 text-xs text-muted-foreground">
            Avg wait {formatDuration(metrics.avg_wait_time_seconds * 1000)} • Oldest item waiting {formatDuration(metrics.oldest_item_age_seconds * 1000)}
          </p>
        </div>

        <div>
          <h3 className="text-lg font-medium mb-3">Recent Items</h3>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Task Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Priority</TableHead>
                  <TableHead className="text-right">Retries</TableHead>
                  <TableHead className="text-right">Duration</TableHead>
                  <TableHead className="text-right">Scheduled</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentItems.length > 0 ? (
                  recentItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-mono text-xs">{item.id.slice(0, 8)}…</TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.task_type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusVariant[item.status]} className="capitalize">
                          {item.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-sm">{item.priority}</TableCell>
                      <TableCell className="text-right text-sm">{item.retry_count}</TableCell>
                      <TableCell className="text-right text-sm">{calculateDuration(item)}</TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {formatRelativeTime(item.scheduled_at)}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-6 text-muted-foreground">
                      Queue is empty
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-medium mb-3">Item Distribution</h3>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(metrics.by_task_type).map(([task, count]) => (
              <div key={task} className="rounded-md border bg-muted/40 p-3">
                <div className="text-sm font-medium">{task}</div>
                <div className="text-xl font-semibold">{count}</div>
              </div>
            ))}
          </div>
        </div>

        {failedItems > 0 && (
          <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm dark:border-red-900/50 dark:bg-red-900/20">
            <p className="font-medium text-red-700 dark:text-red-200">
              {failedItems} item{failedItems === 1 ? '' : 's'} require attention. Investigate recent failures to prevent backlog growth.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
