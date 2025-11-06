import { useMemo } from 'react'
import type { ReactNode } from 'react'
import { CheckCircle2, Loader2, MoreHorizontal } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

export interface BatchAction {
  key: string
  label: string
  icon?: ReactNode
  onAction: () => Promise<void> | void
  disabled?: boolean
  destructive?: boolean
  tooltip?: string
}

export interface BatchActionsToolbarProps {
  selectedCount: number
  actions: BatchAction[]
  onClearSelection?: () => void
  isProcessing?: boolean
  className?: string
  children?: ReactNode
}

const DEFAULT_ACTIONS_TO_DISPLAY = 3

export function BatchActionsToolbar({
  selectedCount,
  actions,
  onClearSelection,
  isProcessing = false,
  className,
  children,
}: BatchActionsToolbarProps) {
  const [primaryActions, overflowActions] = useMemo(() => {
    const primary = actions.slice(0, DEFAULT_ACTIONS_TO_DISPLAY)
    const overflow = actions.slice(DEFAULT_ACTIONS_TO_DISPLAY)
    return [primary, overflow]
  }, [actions])

  const renderActionButton = (action: BatchAction) => {
    const content = (
      <Button
        key={action.key}
        variant={action.destructive ? 'destructive' : 'default'}
        size="sm"
        className="flex items-center gap-2"
        onClick={action.onAction}
        disabled={isProcessing || action.disabled}
        data-testid={action.key === 'delete' ? 'batch-delete-button' : undefined}
      >
        {action.icon ?? <CheckCircle2 className="h-4 w-4" />}
        <span>{action.label}</span>
      </Button>
    )

    if (!action.tooltip) {
      return content
    }

    return (
      <Tooltip key={action.key} delayDuration={150}>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent>{action.tooltip}</TooltipContent>
      </Tooltip>
    )
  }

  const renderOverflowMenu = () => {
    if (!overflowActions.length) return null

    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="outline" className="flex items-center gap-2">
            <MoreHorizontal className="h-4 w-4" />
            More
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          {overflowActions.map((action) => (
            <DropdownMenuItem
              key={action.key}
              className={cn(action.destructive ? 'text-destructive focus:text-destructive' : undefined)}
              onClick={() => action.onAction()}
              disabled={isProcessing || action.disabled}
              data-testid={`batch-${action.key}-menu-item`}
            >
              <div className="flex items-center gap-2">
                {action.icon ?? <CheckCircle2 className="h-4 w-4" />}
                <span>{action.label}</span>
              </div>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    )
  }

  return (
    <TooltipProvider>
      <div
        data-testid="batch-actions-toolbar"
        className={cn(
          'flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-card p-3 shadow-sm',
          className,
        )}
      >
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="text-sm font-medium">
            {selectedCount} selected
          </Badge>
          {onClearSelection && (
            <Button variant="ghost" size="sm" onClick={onClearSelection} disabled={isProcessing}>
              Clear
            </Button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {isProcessing && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          {primaryActions.map(renderActionButton)}
          {renderOverflowMenu()}
          {children}
        </div>
      </div>
    </TooltipProvider>
  )
}
