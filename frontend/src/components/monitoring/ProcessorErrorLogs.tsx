import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ProcessorRetryControls } from './ProcessorRetryControls';
import { useStageErrors } from '@/hooks/use-monitoring';
import { formatDistanceToNow } from 'date-fns';
import { AlertCircle } from 'lucide-react';

interface ProcessorErrorLogsProps {
  stageName: string;
  limit?: number;
}

export function ProcessorErrorLogs({ stageName, limit = 100 }: ProcessorErrorLogsProps) {
  const { data, isLoading, error } = useStageErrors(stageName, limit);
  const [page, setPage] = useState(0);
  const itemsPerPage = 20;

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load error logs: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.errors.length === 0) {
    return (
      <Alert>
        <AlertDescription>No errors found for this stage.</AlertDescription>
      </Alert>
    );
  }

  const paginatedErrors = data.errors.slice(
    page * itemsPerPage,
    (page + 1) * itemsPerPage
  );
  const totalPages = Math.ceil(data.errors.length / itemsPerPage);

  return (
    <div className="space-y-4">
      {/* Header Metrics */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Total Errors</p>
            <p className="text-2xl font-bold">{data.total_errors}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Error Rate</p>
            <p className="text-2xl font-bold">{data.error_rate_percent.toFixed(1)}%</p>
          </div>
        </div>
      </div>

      {/* Error Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Document ID</TableHead>
              <TableHead>Error Message</TableHead>
              <TableHead>Retry Count</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedErrors.map((errorLog) => (
              <TableRow key={errorLog.id}>
                <TableCell className="text-sm">
                  {formatDistanceToNow(new Date(errorLog.occurred_at), { addSuffix: true })}
                </TableCell>
                <TableCell>
                  <code className="text-xs">{errorLog.document_id}</code>
                </TableCell>
                <TableCell>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <p className="text-sm truncate max-w-md cursor-help">
                          {errorLog.error_message}
                        </p>
                      </TooltipTrigger>
                      <TooltipContent className="max-w-md">
                        <p className="whitespace-pre-wrap">{errorLog.error_message}</p>
                        {errorLog.error_code && (
                          <p className="mt-2 text-xs text-muted-foreground">
                            Code: {errorLog.error_code}
                          </p>
                        )}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{errorLog.retry_count}</Badge>
                </TableCell>
                <TableCell>
                  <ProcessorRetryControls
                    stageName={errorLog.stage_name}
                    documentId={errorLog.document_id}
                    retryCount={errorLog.retry_count}
                    canRetry={errorLog.can_retry}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page + 1} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
