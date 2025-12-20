import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useRetryStage } from '@/hooks/use-monitoring';
import { useToast } from '@/hooks/use-toast';
import { RotateCw } from 'lucide-react';

interface ProcessorRetryControlsProps {
  stageName: string;
  documentId: string;
  retryCount: number;
  canRetry: boolean;
}

export function ProcessorRetryControls({
  stageName,
  documentId,
  retryCount,
  canRetry,
}: ProcessorRetryControlsProps) {
  const retryMutation = useRetryStage();
  const toast = useToast();

  const handleRetry = async () => {
    try {
      await retryMutation.mutateAsync({ stageName, documentId });
      toast.success(`Stage ${stageName} will be retried for document ${documentId}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Retry failed');
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className="text-xs">
        Retries: {retryCount}
      </Badge>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            size="sm"
            variant="outline"
            disabled={!canRetry || retryCount >= 3 || retryMutation.isPending}
          >
            <RotateCw className="w-4 h-4 mr-1" />
            Retry
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Retry Stage Processing?</AlertDialogTitle>
            <AlertDialogDescription>
              This will retry the <strong>{stageName}</strong> stage for document{' '}
              <code className="text-xs">{documentId}</code>. The document will be re-queued for
              processing.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRetry}>
              Confirm Retry
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
