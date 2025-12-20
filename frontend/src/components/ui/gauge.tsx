import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const gaugeVariants = cva(
  'relative rounded-full',
  {
    variants: {
      variant: {
        default: 'bg-primary/20',
        success: 'bg-emerald-100 dark:bg-emerald-900/20',
        warning: 'bg-amber-100 dark:bg-amber-900/20',
        destructive: 'bg-red-100 dark:bg-red-900/20',
      },
      size: {
        sm: 'h-2 w-16',
        default: 'h-2.5 w-20',
        lg: 'h-3 w-24',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

const gaugeFillVariants = cva(
  'absolute top-0 left-0 h-full rounded-full transition-all duration-slower',
  {
    variants: {
      variant: {
        default: 'bg-primary',
        success: 'bg-emerald-500',
        warning: 'bg-amber-500',
        destructive: 'bg-red-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

interface GaugeProps 
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof gaugeVariants> {
  value: number;
  showValue?: boolean;
  valueSuffix?: string;
  max?: number;
}

const Gauge = React.forwardRef<HTMLDivElement, GaugeProps>(
  ({
    className,
    value,
    showValue = false,
    valueSuffix = '%',
    max = 100,
    variant,
    size,
    ...props
  }, ref) => {
    const percentage = Math.min(Math.max(0, (value / max) * 100), 100);
    const variantClass = React.useMemo(() => {
      if (variant) return variant;
      if (percentage > 90) return 'destructive';
      if (percentage > 70) return 'warning';
      if (percentage > 30) return 'default';
      return 'success';
    }, [percentage, variant]);

    return (
      <div className={cn('flex items-center gap-sm', className)}>
        <div 
          ref={ref}
          className={cn(gaugeVariants({ variant: variantClass, size }))}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
          {...props}
        >
          <div 
            className={cn(gaugeFillVariants({ variant: variantClass }))}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showValue && (
          <span className="text-sm font-medium tabular-nums">
            {Math.round(percentage)}{valueSuffix}
          </span>
        )}
      </div>
    );
  }
);
Gauge.displayName = 'Gauge';

export { Gauge, gaugeVariants, gaugeFillVariants };
export type { GaugeProps };
