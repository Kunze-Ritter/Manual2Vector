import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useDocumentStages } from '@/hooks/use-document-stages'

interface DocumentStageProgressCellProps {
  documentId: string
  onViewClick: () => void
}

export function DocumentStageProgressCell({ documentId, onViewClick }: DocumentStageProgressCellProps) {
  const { data: stageStatus, isLoading } = useDocumentStages(documentId)

  if (isLoading || !stageStatus) {
    return <span className="text-muted-foreground text-xs">Loading...</span>
  }

  return (
    <div className="flex items-center gap-2">
      <Progress value={stageStatus.overall_progress} className="h-2 w-24" />
      <span className="text-xs text-muted-foreground min-w-[3ch]">
        {Math.round(stageStatus.overall_progress)}%
      </span>
      <Button variant="ghost" size="sm" onClick={onViewClick} className="h-7 px-2 text-xs">
        View
      </Button>
    </div>
  )
}
