import * as React from "react"
import { cva } from "class-variance-authority"

import { cn } from "@/lib/utils"

const progressVariants = cva(
  "relative h-2 w-full overflow-hidden rounded-full bg-muted",
  {
    variants: {
      variant: {
        default: "bg-muted",
        primary: "bg-primary/20",
        success: "bg-emerald-100 dark:bg-emerald-900/30",
        warning: "bg-amber-100 dark:bg-amber-900/30",
        destructive: "bg-red-100 dark:bg-red-900/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const progressIndicatorVariants = cva(
  "h-full w-full flex-1 bg-primary transition-all",
  {
    variants: {
      variant: {
        default: "bg-primary",
        primary: "bg-primary",
        success: "bg-emerald-500",
        warning: "bg-amber-500",
        destructive: "bg-red-500",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number | null
  max?: number
  variant?: "default" | "primary" | "success" | "warning" | "destructive"
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, variant = "default", ...props }, ref) => {
    const percentage = React.useMemo(() => {
      if (value === null || value === undefined) return 0
      const clamped = Math.min(Math.max(value, 0), max)
      return (clamped / max) * 100
    }, [value, max])

    return (
      <div
        ref={ref}
        className={cn(progressVariants({ variant }), className)}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value ?? 0}
        {...props}
      >
        <div
          className={cn(progressIndicatorVariants({ variant }))}
          style={{ transform: `translateX(-${100 - percentage}%)` }}
        />
      </div>
    )
  }
)
Progress.displayName = "Progress"

export { Progress }
