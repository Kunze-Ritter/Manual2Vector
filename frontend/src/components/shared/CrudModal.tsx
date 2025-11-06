import { useCallback, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

type CrudModalMode = 'create' | 'edit'

export interface CrudModalProps {
  open: boolean
  mode: CrudModalMode
  title: string
  description?: string
  children?: ReactNode
  isSubmitting?: boolean
  disableSubmit?: boolean
  submitLabel?: string
  cancelLabel?: string
  submitVariant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link'
  cancelVariant?: 'ghost' | 'outline' | 'default'
  onSubmit: () => void | Promise<void>
  onCancel?: () => void
  onOpenChange?: (open: boolean) => void
  className?: string
  footerContent?: ReactNode
}

export function CrudModal({
  open,
  onOpenChange,
  mode,
  title,
  description,
  children,
  isSubmitting = false,
  disableSubmit = false,
  submitLabel,
  cancelLabel,
  submitVariant = 'default',
  cancelVariant = 'ghost',
  onSubmit,
  onCancel,
  className,
  footerContent,
}: CrudModalProps) {
  const resolvedSubmitLabel = submitLabel ?? (mode === 'create' ? 'Create' : 'Save changes')
  const resolvedCancelLabel = cancelLabel ?? 'Cancel'

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (!nextOpen && open) {
        onCancel?.()
      }
      onOpenChange?.(nextOpen)
    },
    [onCancel, onOpenChange, open],
  )

  const handleCancel = useCallback(() => {
    onCancel?.()
    onOpenChange?.(false)
  }, [onCancel, onOpenChange])

  const handleSubmit = useCallback(() => {
    if (disableSubmit || isSubmitting) return
    onSubmit()
  }, [disableSubmit, isSubmitting, onSubmit])

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className={cn('space-y-4', className)} data-testid="crud-modal">
        <DialogHeader>
          <DialogTitle data-testid="modal-title">{title}</DialogTitle>
          {description ? <DialogDescription data-testid="modal-description">{description}</DialogDescription> : null}
        </DialogHeader>

        <div className="space-y-4" data-testid="crud-modal-body">
          {typeof children === 'function' ? (children as () => ReactNode)() : children}
        </div>

        <DialogFooter className="gap-2">
          <div className="flex w-full flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">{footerContent}</div>
            <div className="flex items-center gap-2">
              <Button type="button" variant={cancelVariant} onClick={handleCancel} disabled={isSubmitting} data-testid="modal-cancel-button">
                {resolvedCancelLabel}
              </Button>
              <Button
                type="button"
                variant={submitVariant}
                onClick={handleSubmit}
                disabled={isSubmitting || disableSubmit}
                data-testid="modal-save-button"
              >
                {isSubmitting ? 'Saving…' : resolvedSubmitLabel}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default CrudModal
