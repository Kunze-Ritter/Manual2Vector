# KRAI Design System

> Comprehensive design system built on shadcn/ui with Tailwind CSS v4

## Quick Start

### For Developers

1. **Import design tokens** (optional, for TypeScript usage):
   ```typescript
   import { spacing, typography, colors } from '@/styles/tokens'
   ```

2. **Use Tailwind classes** with design tokens:
   ```tsx
   <div className="p-md gap-sm shadow-md rounded-lg">
     <h1 className="text-2xl font-bold">Hello World</h1>
   </div>
   ```

3. **Access theme context**:
   ```typescript
   import { useTheme } from '@/contexts/ThemeContext'
   
   const { theme, setTheme, actualTheme } = useTheme()
   ```

---

## Design Token Reference

### Spacing
- `xs` (4px), `sm` (8px), `md` (16px), `lg` (24px)
- `xl` (32px), `2xl` (48px), `3xl` (64px), `4xl` (96px)

### Colors
- **Brand**: `primary`, `secondary`
- **Semantic**: `success`, `warning`, `error` (destructive), `info`
- **UI**: `background`, `foreground`, `card`, `muted`, `accent`, `border`

### Typography
- **Sizes**: `xs`, `sm`, `base`, `lg`, `xl`, `2xl`, `3xl`, `4xl`
- **Weights**: `light`, `normal`, `medium`, `semibold`, `bold`, `black`

### Shadows
- `xs`, `sm`, `md`, `lg`, `xl`, `2xl`

### Z-Index
- `dropdown` (50), `sticky` (100), `fixed` (200)
- `modalBackdrop` (500), `modal` (1000), `popover` (1500)
- `toast` (2000), `tooltip` (2500)

---

## Component Usage Examples

### Button
```tsx
import { Button } from '@/components/ui/button'

<Button variant="default">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

### Card
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description text</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content goes here</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### Input & Form
```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

<div className="space-y-sm">
  <Label htmlFor="email">Email</Label>
  <Input id="email" type="email" placeholder="you@example.com" />
</div>
```

### Dialog
```tsx
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'

<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Are you sure?</DialogTitle>
      <DialogDescription>This action cannot be undone.</DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button variant="destructive">Delete</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Select
```tsx
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'

<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
    <SelectItem value="option3">Option 3</SelectItem>
  </SelectContent>
</Select>
```

### Table
```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>John Doe</TableCell>
      <TableCell>Active</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

---

## Responsive Design Patterns

### Grid Layouts
```tsx
{/* Mobile: 1 column, Tablet: 2 columns, Desktop: 3 columns */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
  <Card>...</Card>
  <Card>...</Card>
  <Card>...</Card>
</div>
```

### Responsive Spacing
```tsx
{/* Small padding on mobile, large on desktop */}
<div className="p-md lg:p-xl">
  Content
</div>
```

### Responsive Typography
```tsx
{/* Smaller text on mobile, larger on desktop */}
<h1 className="text-2xl md:text-3xl lg:text-4xl">
  Responsive Heading
</h1>
```

### Hide/Show Elements
```tsx
{/* Hidden on mobile, visible on desktop */}
<div className="hidden lg:block">
  Desktop only content
</div>

{/* Visible on mobile, hidden on desktop */}
<div className="block lg:hidden">
  Mobile only content
</div>
```

---

## Dark Mode

### Using Theme Context
```tsx
import { useTheme } from '@/contexts/ThemeContext'

function ThemeToggle() {
  const { actualTheme, setTheme } = useTheme()
  
  return (
    <button onClick={() => setTheme(actualTheme === 'light' ? 'dark' : 'light')}>
      {actualTheme === 'light' ? '🌙' : '☀️'}
    </button>
  )
}
```

### Theme-Aware Styling
All color tokens automatically adapt to the current theme. No additional classes needed!

```tsx
{/* Automatically uses correct colors in both themes */}
<div className="bg-background text-foreground border-border">
  Content
</div>
```

---

## Best Practices

### ✅ DO

- Use design tokens for all spacing (`p-md`, `gap-sm`)
- Use semantic colors for states (`bg-success`, `text-error`)
- Follow mobile-first responsive design
- Test in both light and dark modes
- Use the `.focus-ring` utility for focus states
- Keep components accessible (ARIA labels, keyboard navigation)

### ❌ DON'T

- Use arbitrary values (`p-[13px]`) - use tokens instead
- Hardcode colors - use semantic tokens
- Forget to test dark mode
- Skip accessibility features
- Use inline styles when Tailwind classes work
- Create custom z-index values - use tokens

---

## Common Patterns

### Form with Validation
```tsx
<form className="space-y-md">
  <div className="space-y-sm">
    <Label htmlFor="name">Name</Label>
    <Input id="name" placeholder="Enter name" />
  </div>
  
  <div className="space-y-sm">
    <Label htmlFor="email">Email</Label>
    <Input id="email" type="email" placeholder="you@example.com" />
  </div>
  
  <div className="flex gap-sm justify-end">
    <Button variant="outline">Cancel</Button>
    <Button type="submit">Submit</Button>
  </div>
</form>
```

### Loading State
```tsx
import { Skeleton } from '@/components/ui/skeleton'

{isLoading ? (
  <div className="space-y-sm">
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-4 w-1/2" />
  </div>
) : (
  <div>{content}</div>
)}
```

### Error State
```tsx
<div className="bg-destructive/10 border border-destructive text-destructive rounded-md p-md">
  <p className="font-medium">Error</p>
  <p className="text-sm">{errorMessage}</p>
</div>
```

### Success State
```tsx
<div className="bg-success/10 border border-success text-success rounded-md p-md">
  <p className="font-medium">Success!</p>
  <p className="text-sm">{successMessage}</p>
</div>
```

---

## File Structure

```
frontend/
├── src/
│   ├── styles/
│   │   ├── tokens.ts          # Design token definitions
│   │   └── README.md          # Detailed documentation
│   ├── contexts/
│   │   └── ThemeContext.tsx   # Theme provider
│   ├── components/
│   │   ├── ui/                # Reusable UI components
│   │   └── layout/            # Layout components
│   ├── index.css              # Global styles & CSS variables
│   └── App.tsx                # App with ThemeProvider
├── tailwind.config.js         # Tailwind configuration
└── DESIGN_SYSTEM.md           # This file
```

---

## Resources

- **Detailed Documentation**: `frontend/src/styles/README.md`
- **Component Reference**: `frontend/src/components/ui/README.md`
- **Responsive Guide**: `frontend/src/styles/responsive.md`
- **Design Tokens**: `frontend/src/styles/tokens.ts`
- **shadcn/ui**: https://ui.shadcn.com/
- **Tailwind CSS**: https://tailwindcss.com/

---

## Contributing

When adding new components or patterns:

1. Use existing design tokens
2. Follow the established component structure
3. Include both light and dark mode support
4. Add responsive behavior
5. Document usage with examples
6. Test accessibility
7. Update this documentation

---

## Support

For questions or issues:
- Check the detailed documentation in `frontend/src/styles/README.md`
- Review component examples in `frontend/src/components/ui/`
- Consult the shadcn/ui documentation

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-07
