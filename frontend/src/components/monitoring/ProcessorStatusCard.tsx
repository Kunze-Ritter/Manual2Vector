import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ProcessorHealthStatus } from '@/types/api';
import { formatDistanceToNow } from 'date-fns';

interface ProcessorStatusCardProps {
  processor: ProcessorHealthStatus;
}

export function ProcessorStatusCard({ processor }: ProcessorStatusCardProps) {
  const getHealthScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getErrorRateColor = (rate: number) => {
    if (rate > 10) return 'bg-red-500';
    if (rate > 5) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold">
            {processor.processor_name}
          </CardTitle>
          <div className="flex items-center gap-2">
            {processor.is_active && (
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            )}
            <Badge variant={processor.status === 'running' ? 'default' : 'secondary'}>
              {processor.status}
            </Badge>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">{processor.stage_name}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Health Score */}
        <div className="flex items-center justify-center">
          <div className="relative w-24 h-24">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                className="text-gray-200"
              />
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - processor.health_score / 100)}`}
                className={getHealthScoreColor(processor.health_score)}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-2xl font-bold ${getHealthScoreColor(processor.health_score)}`}>
                {Math.round(processor.health_score)}
              </span>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-muted-foreground">Processing</p>
            <p className="font-semibold">{processor.documents_processing}</p>
          </div>
          <div>
            <p className="text-muted-foreground">In Queue</p>
            <p className="font-semibold">{processor.documents_in_queue}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Avg Time</p>
            <p className="font-semibold">{processor.avg_processing_time_seconds.toFixed(1)}s</p>
          </div>
          <div>
            <p className="text-muted-foreground">Error Rate</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${getErrorRateColor(processor.error_rate_percent)} transition-all`}
                  style={{ width: `${Math.min(processor.error_rate_percent, 100)}%` }}
                />
              </div>
              <span className="font-semibold text-xs">
                {processor.error_rate_percent.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Last Activity */}
        {processor.last_activity && (
          <div className="text-xs text-muted-foreground border-t pt-2">
            <p>Last activity: {formatDistanceToNow(new Date(processor.last_activity), { addSuffix: true })}</p>
            {processor.current_document_id && (
              <p className="truncate">
                Current doc: <span className="font-mono">{processor.current_document_id}</span>
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
