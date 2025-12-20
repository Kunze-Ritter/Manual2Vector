import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, Circle, XCircle, Clock, AlertCircle } from 'lucide-react'
import type { DocumentStageStatusResponse, StageStatus, StageName } from '@/types/api'
import { CANONICAL_STAGES } from '@/types/api'
import { useDocumentStages } from '@/hooks/use-document-stages'

interface DocumentProcessingTimelineProps {
  documentId: string
  onStageClick?: (stageName: string) => void
}

const STAGE_LABELS: Record<StageName, string> = {
  upload: "Upload",
  text_extraction: "Text",
  table_extraction: "Tables",
  svg_processing: "SVG",
  image_processing: "Images",
  visual_embedding: "Visual AI",
  link_extraction: "Links",
  chunk_prep: "Chunks",
  classification: "Classification",
  metadata_extraction: "Metadata",
  parts_extraction: "Parts",
  series_detection: "Series",
  storage: "Storage",
  embedding: "Embeddings",
  search_indexing: "Search"
}

const getStageIcon = (status: StageStatus) => {
  switch (status) {
    case 'completed': return <CheckCircle2 className="h-5 w-5 text-green-600" />
    case 'failed': return <XCircle className="h-5 w-5 text-red-600" />
    case 'processing': return <Clock className="h-5 w-5 text-blue-600 animate-pulse" />
    case 'skipped': return <AlertCircle className="h-5 w-5 text-gray-400" />
    default: return <Circle className="h-5 w-5 text-gray-300" />
  }
}

const getStageVariant = (status: StageStatus): 'default' | 'secondary' | 'destructive' | 'outline' => {
  switch (status) {
    case 'completed': return 'default'
    case 'failed': return 'destructive'
    case 'processing': return 'secondary'
    default: return 'outline'
  }
}

export function DocumentProcessingTimeline({ documentId, onStageClick }: DocumentProcessingTimelineProps) {
  const { data: stageStatus, isLoading } = useDocumentStages(documentId)

  if (isLoading || !stageStatus) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-sm text-muted-foreground">Loading stage status...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Overall Progress Bar */}
      <div>
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm text-muted-foreground">{Math.round(stageStatus.overall_progress)}%</span>
        </div>
        <Progress value={stageStatus.overall_progress} className="h-2" />
      </div>

      {/* Horizontal Stage Timeline */}
      <div className="relative">
        <div className="flex items-center justify-between">
          {CANONICAL_STAGES.map((stageName, index) => {
            const stage = stageStatus.stages[stageName]
            const isActive = stageStatus.current_stage === stageName
            
            return (
              <div key={stageName} className="flex flex-col items-center flex-1">
                {/* Stage Icon */}
                <button
                  onClick={() => onStageClick?.(stageName)}
                  className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
                    isActive ? 'border-primary bg-primary/10 scale-110' : 'border-gray-300 bg-white'
                  } hover:scale-110 hover:shadow-md`}
                >
                  {getStageIcon(stage?.status || 'pending')}
                </button>
                
                {/* Stage Label */}
                <span className={`mt-2 text-xs text-center ${isActive ? 'font-semibold' : 'text-muted-foreground'}`}>
                  {STAGE_LABELS[stageName]}
                </span>
                
                {/* Stage Status Badge */}
                {stage && (
                  <Badge variant={getStageVariant(stage.status)} className="mt-1 text-xs">
                    {stage.status}
                  </Badge>
                )}
                
                {/* Connector Line */}
                {index < CANONICAL_STAGES.length - 1 && (
                  <div className="absolute top-5 left-1/2 w-full h-0.5 bg-gray-300 -z-10" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
