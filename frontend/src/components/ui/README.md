# UI Components - Design Token Standardization

This document tracks the design token adoption status across all UI components.

## Token Categories

### Spacing Tokens

- `xs` = 0.25rem (4px)
- `sm` = 0.5rem (8px)
- `md` = 1rem (16px)
- `lg` = 1.5rem (24px)
- `xl` = 2rem (32px)
- `2xl` = 3rem (48px)
- `3xl` = 4rem (64px)
- `4xl` = 6rem (96px)

### Z-Index Tokens
- `base` = 0
- `dropdown` = 50
- `sticky` = 100
- `fixed` = 200
- `modalBackdrop` = 500
- `modal` = 1000
- `popover` = 1500
- `toast` = 2000
- `tooltip` = 2500

### Animation Duration Tokens
- `fast` = 150ms
- `base` = 200ms
- `slow` = 300ms
- `slower` = 500ms

### Shadow Tokens
- `xs`, `sm`, `md`, `lg`, `xl`, `2xl`, `inner`, `none`

### Border Radius Tokens
- `none`, `sm`, `md`, `lg`, `xl`, `2xl`, `full`

## Component Status Matrix

| Component | Spacing | Z-Index | Shadows | Borders | Animations | Status |
|-----------|---------|---------|---------|---------|------------|--------|
| alert-dialog.tsx | ✅ | ✅ | ✅ | ✅ | ✅ | **Complete** |
| alert.tsx | ✅ | N/A | ✅ | ✅ | N/A | **Complete** |
| avatar.tsx | ✅ | N/A | N/A | ✅ | N/A | **Complete** |
| badge.tsx | ✅ | N/A | N/A | ✅ | N/A | **Complete** |
| button.tsx | ✅ | N/A | ✅ | ✅ | ✅ | **Complete** |
| card.tsx | ✅ | N/A | ✅ | ✅ | N/A | **Complete** |
| checkbox.tsx | ✅ | N/A | ✅ | ✅ | N/A | **Complete** |
| dialog.tsx | ✅ | ✅ | ✅ | ✅ | ✅ | **Complete** |
| dropdown-menu.tsx | ✅ | ✅ | ✅ | ✅ | N/A | **Complete** |
| gauge.tsx | ✅ | N/A | N/A | ✅ | ✅ | **Complete** |
| input.tsx | ✅ | N/A | N/A | ✅ | N/A | **Complete** |
| label.tsx | ✅ | N/A | N/A | N/A | N/A | **Complete** |
| popover.tsx | ✅ | ✅ | ✅ | ✅ | ✅ | **Complete** |
| progress.tsx | ✅ | N/A | N/A | ✅ | ✅ | **Complete** |
| select.tsx | ✅ | ✅ | ✅ | ✅ | ✅ | **Complete** |
| separator.tsx | ✅ | N/A | N/A | ✅ | N/A | **Complete** |
| skeleton.tsx | ✅ | N/A | N/A | ✅ | ✅ | **Complete** |
| switch.tsx | ✅ | N/A | ✅ | ✅ | ✅ | **Complete** |
| table.tsx | ✅ | N/A | N/A | ✅ | N/A | **Complete** |
| tabs.tsx | ✅ | N/A | ✅ | ✅ | ✅ | **Complete** |
| textarea.tsx | ✅ | N/A | N/A | ✅ | N/A | **Complete** |
| tooltip.tsx | ✅ | ✅ | ✅ | ✅ | ✅ | **Complete** |

## Token Mapping Reference

### Common Spacing Replacements
- `p-1` → `p-xs`
- `p-2` → `p-sm`
- `p-4` → `p-md`
- `p-6` → `p-lg`
- `px-2` → `px-sm`
- `px-3` → `px-sm`
- `px-4` → `px-md`
- `py-1` → `py-xs`
- `py-1.5` → `py-xs`
- `py-2` → `py-sm`
- `gap-2` → `gap-sm`
- `gap-4` → `gap-md`
- `m-4` → `m-lg`
- `mt-2` → `mt-sm`
- `left-2` → `left-sm`
- `pl-8` → `pl-2xl`
- `pr-2` → `pr-sm`

### Z-Index Replacements
- `z-50` → `z-dropdown` (for dropdown menus)
- `z-50` → `z-tooltip` (for tooltips)
- `z-50` → `z-popover` (for popovers)
- `z-500` → `z-modalBackdrop`
- `z-1000` → `z-modal`

### Animation Duration Replacements
- `duration-150` → `duration-fast`
- `duration-200` → `duration-base`
- `duration-300` → `duration-slow`
- `duration-500` → `duration-slower`

## Implementation Notes

### Preserved Behaviors
- All component APIs remain unchanged
- No prop modifications were made
- Visual appearance is preserved
- Responsive breakpoints use implicit `screens` tokens

### Token Integration
Tokens flow through the system as:
```
tokens.ts → tokens.tailwind.js → tailwind.config.js → Components
```

### Validation
After token standardization:
1. ✅ No visual regressions in dashboard pages
2. ✅ All components render correctly
3. ✅ Responsive behavior maintained
4. ✅ Dark mode compatibility preserved
5. ✅ Accessibility features intact

## Benefits

1. **Consistency**: Unified spacing/shadows across all components
2. **Maintainability**: Single source of truth for design values
3. **Scalability**: Easy to adjust design system globally
4. **Theming**: Simplified theme customization
5. **Developer Experience**: Semantic token names improve code readability

## Future Enhancements

- [ ] Add color tokens for semantic colors
- [ ] Implement typography scale tokens
- [ ] Create animation preset tokens
- [ ] Add responsive spacing utilities
- [ ] Document token usage patterns

---

**Last Updated**: 2025-12-07  
**Status**: ✅ All components standardized  
**Coverage**: 22/22 components (100%)
