# Design System Documentation

## Overview

This design system provides a comprehensive set of design tokens, components, and patterns to ensure consistency across the KRAI application. It's built on top of **shadcn/ui** with **Tailwind CSS v4** and includes full dark mode support.

### Benefits

- **Consistency**: Single source of truth for design decisions
- **Scalability**: Easy to maintain and extend
- **Type Safety**: TypeScript-based tokens with IDE autocomplete
- **Accessibility**: WCAG-compliant color contrasts and focus states
- **Developer Experience**: Clear documentation and reusable patterns

---

## Design Tokens

Design tokens are defined in `frontend/src/styles/tokens.ts` and consumed by Tailwind configuration.

### Color System

Colors use HSL format for easy manipulation and theme switching.

#### Brand Colors
```typescript
colors.brand.primary           // Primary brand color
colors.brand.primaryForeground // Text on primary
colors.brand.secondary         // Secondary brand color
colors.brand.secondaryForeground // Text on secondary
```

#### Semantic Colors
```typescript
colors.semantic.success        // Green - success states
colors.semantic.warning        // Amber - warning states
colors.semantic.error          // Red - error states
colors.semantic.info           // Blue - informational states
```

#### UI Colors
```typescript
colors.ui.background           // Page background
colors.ui.foreground           // Primary text
colors.ui.card                 // Card background
colors.ui.muted                // Muted backgrounds
colors.ui.accent               // Accent backgrounds
colors.ui.border               // Border color
colors.ui.input                // Input border color
colors.ui.ring                 // Focus ring color
```

**Usage in Tailwind:**
```tsx
<div className="bg-primary text-primary-foreground">Primary Button</div>
<div className="bg-success text-success-foreground">Success Message</div>
```

---

### Spacing Scale

Consistent spacing ensures visual rhythm and hierarchy.

| Token | Value | Pixels | Usage |
|-------|-------|--------|-------|
| `xs` | 0.25rem | 4px | Tight spacing, badges |
| `sm` | 0.5rem | 8px | Small gaps, compact layouts |
| `md` | 1rem | 16px | Default spacing |
| `lg` | 1.5rem | 24px | Section padding |
| `xl` | 2rem | 32px | Large spacing |
| `2xl` | 3rem | 48px | Extra large spacing |
| `3xl` | 4rem | 64px | Hero sections |
| `4xl` | 6rem | 96px | Maximum spacing |

**Usage in Tailwind:**
```tsx
<div className="p-md gap-sm">Content with medium padding and small gap</div>
<div className="mt-xl mb-2xl">Large vertical spacing</div>
```

---

### Typography

#### Font Families
- **Sans**: Inter, system-ui fallbacks
- **Mono**: JetBrains Mono, monospace fallbacks

#### Font Sizes
| Token | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `xs` | 12px | 16px | Captions, labels |
| `sm` | 14px | 20px | Body text (small) |
| `base` | 16px | 24px | Body text |
| `lg` | 18px | 28px | Subheadings |
| `xl` | 20px | 28px | Headings |
| `2xl` | 24px | 32px | Large headings |
| `3xl` | 30px | 36px | Hero text |
| `4xl` | 36px | 40px | Display text |

#### Font Weights
- `light` (300), `normal` (400), `medium` (500)
- `semibold` (600), `bold` (700), `black` (900)

**Usage in Tailwind:**
```tsx
<h1 className="text-4xl font-bold">Display Heading</h1>
<p className="text-base font-normal">Body text</p>
<span className="text-sm font-medium">Small label</span>
```

---

### Shadows

Elevation system for depth and hierarchy.

| Token | Usage |
|-------|-------|
| `xs` | Subtle elevation |
| `sm` | Cards, buttons |
| `md` | Dropdowns, popovers |
| `lg` | Modals, dialogs |
| `xl` | Maximum elevation |
| `2xl` | Hero elements |

**Usage in Tailwind:**
```tsx
<div className="shadow-sm">Card</div>
<div className="shadow-md">Dropdown</div>
<div className="shadow-lg">Modal</div>
```

---

### Border Radius

Consistent corner rounding.

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | calc(var(--radius) - 4px) | Tight radius |
| `md` | calc(var(--radius) - 2px) | Default radius |
| `lg` | var(--radius) | Large radius |
| `xl` | calc(var(--radius) + 4px) | Extra large |
| `2xl` | calc(var(--radius) + 8px) | Maximum |
| `full` | 9999px | Circular |

**Usage in Tailwind:**
```tsx
<button className="rounded-md">Button</button>
<div className="rounded-lg">Card</div>
<img className="rounded-full" />
```

---

### Animation

Consistent timing for transitions.

#### Durations
- `fast`: 150ms - Quick interactions
- `base`: 200ms - Default transitions
- `slow`: 300ms - Deliberate animations
- `slower`: 500ms - Complex animations

#### Easing Functions
- `linear`: Constant speed
- `easeIn`: Accelerating
- `easeOut`: Decelerating
- `easeInOut`: Smooth (default)

**Usage in Tailwind:**
```tsx
<div className="transition-colors duration-base">Hover me</div>
<div className="transition-all duration-slow ease-in-out">Smooth</div>
```

---

### Z-Index

Layering system for stacking context.

| Token | Value | Usage |
|-------|-------|-------|
| `base` | 0 | Default layer |
| `dropdown` | 50 | Dropdown menus |
| `sticky` | 100 | Sticky headers |
| `fixed` | 200 | Fixed elements |
| `modalBackdrop` | 500 | Modal backdrop |
| `modal` | 1000 | Modal content |
| `popover` | 1500 | Popovers |
| `toast` | 2000 | Toast notifications |
| `tooltip` | 2500 | Tooltips |

**Usage in Tailwind:**
```tsx
<div className="z-fixed">Fixed Header</div>
<div className="z-modal">Modal</div>
<div className="z-toast">Toast</div>
```

---

## Dark Mode

Dark mode is implemented using CSS classes and managed by `ThemeContext`.

### Using Dark Mode

```tsx
import { useTheme } from '@/contexts/ThemeContext'

function MyComponent() {
  const { theme, setTheme, actualTheme } = useTheme()
  
  return (
    <button onClick={() => setTheme(actualTheme === 'light' ? 'dark' : 'light')}>
      Toggle Theme
    </button>
  )
}
```

### Theme Values
- `'light'`: Light mode
- `'dark'`: Dark mode
- `'system'`: Follow system preference

### Testing Dark Mode

1. Toggle theme using the theme switcher in the header
2. Check both light and dark variants of all components
3. Verify color contrast meets WCAG AA standards
4. Test focus states in both themes

---

## Responsive Design

Mobile-first approach using Tailwind breakpoints.

### Breakpoints

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | 640px | Small tablets |
| `md` | 768px | Tablets |
| `lg` | 1024px | Laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large screens |

### Responsive Patterns

```tsx
// Mobile-first: base styles apply to mobile, then override for larger screens
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* 1 column on mobile, 2 on tablet, 3 on desktop */}
</div>

<div className="text-sm md:text-base lg:text-lg">
  {/* Responsive text sizing */}
</div>

<div className="p-md lg:p-xl">
  {/* Responsive padding */}
</div>
```

---

## Utility Classes

Custom utility classes defined in `index.css`.

### Focus Ring
```tsx
<input className="focus-ring" />
// Applies consistent focus styling
```

### Card Hover
```tsx
<div className="card-hover">
  {/* Smooth shadow transition on hover */}
</div>
```

---

## Best Practices

### 1. Use Design Tokens
✅ **Do:**
```tsx
<div className="p-md gap-sm shadow-md">Content</div>
```

❌ **Don't:**
```tsx
<div className="p-4 gap-2 shadow">Content</div>
```

### 2. Maintain Consistency
- Use the spacing scale for all margins and padding
- Use semantic colors for states (success, warning, error)
- Apply consistent shadow levels for elevation

### 3. Accessibility
- Ensure sufficient color contrast (use semantic colors)
- Include focus states (use `.focus-ring` utility)
- Test keyboard navigation
- Provide alt text for images

### 4. Responsive Design
- Start with mobile styles
- Use breakpoint prefixes (sm:, md:, lg:)
- Test on multiple screen sizes
- Ensure touch targets are at least 44x44px

### 5. Performance
- Use CSS variables for theme switching (no JS required)
- Leverage Tailwind's purge for minimal CSS
- Avoid inline styles when possible

---

## Component Patterns

### Form Layout
```tsx
<form className="space-y-md">
  <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
    <Input placeholder="First Name" />
    <Input placeholder="Last Name" />
  </div>
  <Button type="submit">Submit</Button>
</form>
```

### Card Grid
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
  <Card>...</Card>
  <Card>...</Card>
  <Card>...</Card>
</div>
```

### Modal Dialog
```tsx
<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Description text</DialogDescription>
    </DialogHeader>
    {/* Content */}
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

---

## Migration Guide

When updating existing components:

1. **Identify hardcoded values**: Look for px values (p-4, gap-2, etc.)
2. **Replace with tokens**: Use spacing tokens (p-md, gap-sm)
3. **Add comments**: Document which tokens are being used
4. **Test thoroughly**: Verify visual consistency
5. **Check dark mode**: Ensure both themes work correctly

---

## UI Component Tokenization Status

This matrix tracks which UI components have been fully migrated to use design tokens instead of hardcoded values.

### Tokenization Coverage

| Component | Spacing | Typography | Shadows | Borders | Animation | Z-Index | Status |
|-----------|---------|------------|---------|---------|-----------|---------|--------|
| **button** | ✅ | ✅ | ✅ | ✅ | ✅ | N/A | ✅ **Complete** |
| **card** | ✅ | ✅ | ✅ | ✅ | N/A | N/A | ✅ **Complete** |
| **input** | ✅ | ✅ | ✅ | ✅ | ✅ | N/A | ✅ **Complete** |
| **table** | ✅ | ✅ | N/A | ✅ | ✅ | N/A | ✅ **Complete** |
| **dialog** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **Complete** |
| **select** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **Complete** |
| **badge** | ✅ | ✅ | ✅ | ✅ | ✅ | N/A | ✅ **Complete** |
| **alert** | ✅ | ✅ | N/A | ✅ | N/A | N/A | ✅ **Complete** |
| **alert-dialog** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **Complete** |
| **popover** | ✅ | ✅ | ✅ | ✅ | N/A | ✅ | ✅ **Complete** |
| **textarea** | ✅ | ✅ | N/A | ✅ | N/A | N/A | ✅ **Complete** |
| **skeleton** | N/A | N/A | N/A | ✅ | ✅ | N/A | ✅ **Complete** |
| **avatar** | ⚠️ | N/A | N/A | ✅ | N/A | N/A | ⚠️ **Partial** |
| **checkbox** | ⚠️ | N/A | N/A | ✅ | ✅ | N/A | ⚠️ **Partial** |
| **dropdown-menu** | ⚠️ | ✅ | ✅ | ✅ | N/A | ✅ | ⚠️ **Partial** |
| **gauge** | ⚠️ | ✅ | N/A | N/A | N/A | N/A | ⚠️ **Partial** |
| **label** | N/A | ✅ | N/A | N/A | N/A | N/A | ✅ **Complete** |
| **progress** | ⚠️ | N/A | N/A | ✅ | N/A | N/A | ⚠️ **Partial** |
| **separator** | N/A | N/A | N/A | N/A | N/A | N/A | ✅ **Complete** |
| **switch** | ⚠️ | N/A | N/A | ✅ | ✅ | N/A | ⚠️ **Partial** |
| **tabs** | ⚠️ | ✅ | N/A | ✅ | N/A | N/A | ⚠️ **Partial** |
| **tooltip** | ⚠️ | ✅ | N/A | ✅ | N/A | ✅ | ⚠️ **Partial** |

### Legend

- ✅ **Fully tokenized** - Uses design tokens consistently
- ⚠️ **Partially tokenized** - Mix of tokens and hardcoded values
- ❌ **Not tokenized** - Uses hardcoded values
- N/A - Token category not applicable to component

### Notes for Future Contributors

When updating components to use tokens:
1. Replace hardcoded spacing values (e.g., `p-4` → `p-md`, `gap-2` → `gap-sm`)
2. Replace hardcoded z-index values (e.g., `z-50` → `z-dropdown`)
3. Replace hardcoded durations (e.g., `duration-200` → `duration-base`)
4. Add inline comments documenting which tokens are used
5. Test visual consistency across breakpoints and themes
6. Update this matrix when completing tokenization

### Priority for Tokenization

Components marked as ⚠️ **Partial** should be updated in the following priority order:
1. **dropdown-menu** - High usage, complex spacing
2. **tabs** - Common UI pattern
3. **tooltip** - Frequent use across app
4. **switch**, **checkbox** - Form controls
5. **avatar**, **progress**, **gauge** - Lower priority

---

## Resources

- **Design Tokens**: `frontend/src/styles/tokens.ts`
- **Tailwind Config**: `frontend/tailwind.config.js`
- **Tailwind Tokens (JS)**: `frontend/src/styles/tokens.tailwind.js` (for Node.js consumption)
- **CSS Variables**: `frontend/src/index.css`
- **Theme Context**: `frontend/src/contexts/ThemeContext.tsx`
- **Theme Utils**: `frontend/src/lib/theme-utils.ts` (SSR-safe utilities)
- **Component Library**: `frontend/src/components/ui/`

---

**Last Updated**: 2024-12-07
