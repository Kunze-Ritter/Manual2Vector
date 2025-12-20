import * as React from 'react'
import { CaretDownIcon, CheckIcon } from '@radix-ui/react-icons'
import * as SelectPrimitive from '@radix-ui/react-select'

import { cn } from '@/lib/utils'

const Select = SelectPrimitive.Root

const SelectGroup = SelectPrimitive.Group

const SelectValue = SelectPrimitive.Value

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      // Using design tokens: spacing (px-sm, py-sm), border radius (md), focus ring
      'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-sm py-sm text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors duration-base',
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <CaretDownIcon className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = 'popper', ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        // Using design tokens: z-index (dropdown), shadow (md), border radius (md), animation
        'relative z-dropdown min-w-[8rem] overflow-hidden rounded-md border border-border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        className,
      )}
      position={position}
      {...props}
    >
      <SelectPrimitive.ScrollUpButton className="flex h-6 cursor-default items-center justify-center bg-muted text-muted-foreground">
        <CaretDownIcon className="h-4 w-4 rotate-180" />
      </SelectPrimitive.ScrollUpButton>
      <SelectPrimitive.Viewport className="p-xs">{children}</SelectPrimitive.Viewport>
      <SelectPrimitive.ScrollDownButton className="flex h-6 cursor-default items-center justify-center bg-muted text-muted-foreground">
        <CaretDownIcon className="h-4 w-4" />
      </SelectPrimitive.ScrollDownButton>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
))
SelectContent.displayName = SelectPrimitive.Content.displayName

const SelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    // Using design tokens: spacing (px-sm, py-xs)
    className={cn('px-sm py-xs text-sm font-semibold text-foreground', className)}
    {...props}
  />
))
SelectLabel.displayName = SelectPrimitive.Label.displayName

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, value, ...props }, ref) => {
  // Radix Select does not allow an empty string as Item value. Normalize empty/undefined
  // values to a safe sentinel so that accidental "" values from callers don't crash
  // the entire React tree.
  const safeValue = value === '' || value == null ? '__empty__' : value

  if (value === '' || value == null) {
    console.warn('[SelectItem] Normalizing empty value for item', { children })
  }

  return (
    <SelectPrimitive.Item
      ref={ref}
      className={cn(
        // Using design tokens: spacing (px-sm, py-xs)
        'relative flex w-full cursor-default select-none items-center rounded-sm px-sm py-xs text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        className,
      )}
      value={safeValue}
      {...props}
    >
      <span className="absolute left-sm flex h-3.5 w-3.5 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <CheckIcon className="h-4 w-4" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  )
})
SelectItem.displayName = SelectPrimitive.Item.displayName

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator ref={ref} className={cn('-mx-1 my-1 h-px bg-muted', className)} {...props} />
))
SelectSeparator.displayName = SelectPrimitive.Separator.displayName

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectSeparator,
}
