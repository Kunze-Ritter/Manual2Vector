import { useMemo } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { Alert as AlertType } from '@/types/api';
import { getAlertSeverityBadgeVariant, getAlertTypeIcon } from '@/lib/format';
import { BellRing, type LucideProps } from 'lucide-react';
import * as Icons from 'lucide-react';

interface AlertsProps {
  alerts: AlertType[];
  showAll?: boolean;
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
}

export default function Alerts({ alerts = [], showAll = false, onAcknowledge, onDismiss }: AlertsProps) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <BellRing className="mx-auto h-8 w-8 mb-2 opacity-30" />
        <p>No alerts to display</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const iconName = getAlertTypeIcon(alert.alert_type);
        const IconComponent = useMemo(() => {
          const component = Icons[iconName as keyof typeof Icons] ?? Icons.AlertTriangle;
          return component as React.ComponentType<LucideProps>;
        }, [iconName]);

        const severityVariant = getAlertSeverityBadgeVariant(alert.severity);
        const alertVariant = severityVariant === 'destructive' ? 'destructive' : 'default';

        return (
          <Alert 
            key={alert.id} 
            variant={alertVariant}
            className="relative"
            data-testid="alert-item"
          >
            <div className="flex items-start gap-3">
              <IconComponent className="h-5 w-5 mt-0.5" />
              <div className="flex-1 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <AlertTitle className="flex-1 text-sm font-medium leading-none">
                    {alert.title}
                  </AlertTitle>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant={severityVariant}>{alert.severity.replace('_', ' ')}</Badge>
                    <span>{new Date(alert.triggered_at).toLocaleString()}</span>
                  </div>
                </div>

                <AlertDescription>
                  <p>{alert.message}</p>
                  {alert.metadata && Object.keys(alert.metadata).length > 0 && (
                    <details className="mt-2 text-xs">
                      <summary className="cursor-pointer text-muted-foreground">
                        View details
                      </summary>
                      <pre className="mt-1 rounded bg-muted/40 p-2 text-[11px] leading-relaxed">
                        {JSON.stringify(alert.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </AlertDescription>

                <div className="flex gap-2">
                  {!alert.acknowledged && onAcknowledge && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onAcknowledge(alert.id)}
                      data-testid="acknowledge-button"
                    >
                      Acknowledge
                    </Button>
                  )}
                  {onDismiss && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDismiss(alert.id)}
                      data-testid="dismiss-button"
                    >
                      Dismiss
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </Alert>
        );
      })}
      
      {!showAll && alerts.length > 5 && (
        <div className="text-center pt-2">
          <Button variant="link" size="sm">
            View all alerts
          </Button>
        </div>
      )}
    </div>
  );
}
