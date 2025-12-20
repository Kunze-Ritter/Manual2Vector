import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ProcessorErrorLogs } from './ProcessorErrorLogs';
import { useStageQueue } from '@/hooks/use-monitoring';
import { formatDistanceToNow } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';

interface StageDetailsModalProps {
  stageName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function StageDetailsModal({
  stageName,
  open,
  onOpenChange,
}: StageDetailsModalProps) {
  const { data: queueData, isLoading } = useStageQueue(stageName, 50);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Stage Details: {stageName}</DialogTitle>
        </DialogHeader>

        {/* Stage Metrics */}
        {queueData && (
          <div className="grid grid-cols-4 gap-4 p-4 bg-muted rounded-lg">
            <div>
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-2xl font-bold">{queueData.pending_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Processing</p>
              <p className="text-2xl font-bold">{queueData.processing_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Avg Wait Time</p>
              <p className="text-2xl font-bold">{queueData.avg_wait_time_seconds.toFixed(1)}s</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Oldest Item</p>
              <p className="text-2xl font-bold">{Math.round(queueData.oldest_item_age_seconds / 60)}m</p>
            </div>
          </div>
        )}

        <Tabs defaultValue="queue" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="queue">Queue</TabsTrigger>
            <TabsTrigger value="errors">Errors</TabsTrigger>
          </TabsList>

          <TabsContent value="queue" className="space-y-4">
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : queueData && queueData.queue_items.length > 0 ? (
              <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document ID</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Scheduled</TableHead>
                      <TableHead>Retry Count</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {queueData.queue_items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>
                          <code className="text-xs">{item.document_id || 'N/A'}</code>
                        </TableCell>
                        <TableCell>
                          <Badge variant={item.status === 'processing' ? 'default' : 'secondary'}>
                            {item.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{item.priority}</TableCell>
                        <TableCell className="text-sm">
                          {formatDistanceToNow(new Date(item.scheduled_at), { addSuffix: true })}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{item.retry_count}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">No items in queue</p>
            )}
          </TabsContent>

          <TabsContent value="errors">
            <ProcessorErrorLogs stageName={stageName} limit={50} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
