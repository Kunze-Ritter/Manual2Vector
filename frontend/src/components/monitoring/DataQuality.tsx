import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { DataQualityResponse } from '@/types/api';
import { formatRelativeTime } from '@/lib/utils/format';

interface DataQualityProps {
  data?: DataQualityResponse;
}

export default function DataQuality({ data }: DataQualityProps) {
  if (!data) {
    return <div>No data quality metrics available</div>;
  }

  const { duplicate_metrics: duplicate, validation_metrics: validation, processing_metrics: processing, timestamp } = data;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="col-span-1">
        <CardHeader>
          <CardTitle>Processing Summary</CardTitle>
          <CardDescription>
            Updated {formatRelativeTime(timestamp)}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="rounded-md border bg-muted/30 p-4">
            <p className="text-xs text-muted-foreground">Total Processed</p>
            <p className="text-2xl font-semibold mt-1">{processing.total_processed}</p>
            <p className="text-xs text-muted-foreground mt-2">Successful: {processing.successful}</p>
          </div>
          <div className="rounded-md border bg-muted/30 p-4">
            <p className="text-xs text-muted-foreground">Success Rate</p>
            <p className="text-2xl font-semibold mt-1">{Math.round(processing.success_rate * 100)}%</p>
            <p className="text-xs text-muted-foreground mt-2">Avg time {Math.round(processing.avg_processing_time)}s</p>
          </div>
          <div className="rounded-md border bg-muted/30 p-4">
            <p className="text-xs text-muted-foreground">Failures</p>
            <p className="text-2xl font-semibold mt-1">{processing.failed}</p>
            <p className="text-xs text-muted-foreground mt-2">
              {processing.recent_errors.length} recent issues
            </p>
          </div>
          <div className="rounded-md border bg-muted/30 p-4">
            <p className="text-xs text-muted-foreground">Duplicates</p>
            <p className="text-2xl font-semibold mt-1">{duplicate.total_duplicates}</p>
            <p className="text-xs text-muted-foreground mt-2">Hash based: {duplicate.duplicate_by_hash}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1">
        <CardHeader>
          <CardTitle>Validation Issues</CardTitle>
          <CardDescription>
            {validation.total_validation_errors} total errors
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {Object.entries(validation.errors_by_stage).map(([stage, count]) => (
              <div key={stage} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{stage}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>

          <div className="rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
            <p className="font-medium text-foreground mb-2">Common Error Documents</p>
            {validation.documents_with_errors.slice(0, 4).map((item) => (
              <div key={item.document_id} className="flex justify-between py-1">
                <span className="truncate pr-4">{item.filename}</span>
                <span className="text-foreground">{item.error_count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Recent Processing Errors</CardTitle>
          <CardDescription>
            Showing latest {Math.min(processing.recent_errors.length, 5)} issues
          </CardDescription>
        </CardHeader>
        <CardContent>
          {processing.recent_errors.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent errors detected.</p>
          ) : (
            <div className="space-y-3 text-sm">
              {processing.recent_errors.slice(0, 5).map((error) => (
                <div key={`${error.document_id}-${error.timestamp}`} className="rounded-md border bg-destructive/5 p-3">
                  <div className="flex justify-between">
                    <span className="font-medium text-foreground">
                      Document {error.document_id}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(error.timestamp)}
                    </span>
                  </div>
                  <p className="mt-1 text-muted-foreground">{error.error}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
