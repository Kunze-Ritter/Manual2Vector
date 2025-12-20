# Code Review Checklist

Use this checklist when reviewing pull requests to ensure code quality and consistency.

## Functionality

- [ ] Feature works as expected
- [ ] Edge cases are handled
- [ ] Error handling is implemented
- [ ] Loading states are shown
- [ ] Success/error feedback is provided (toasts)

## Code Quality

- [ ] Design tokens used (no hardcoded colors/spacing)
- [ ] TypeScript types are correct and explicit
- [ ] No `any` types (use `unknown` if needed)
- [ ] No ESLint warnings or errors
- [ ] Code follows consistent patterns (see INTERACTION_PATTERNS.md)
- [ ] No console.log statements
- [ ] No commented-out code
- [ ] Meaningful variable and function names

## Component Structure

- [ ] Components are properly organized
- [ ] Reusable logic extracted to hooks/utilities
- [ ] Props are documented with JSDoc
- [ ] Types are exported
- [ ] forwardRef used where needed (forms, modals)
- [ ] Design tokens used for styling

## State Management

- [ ] TanStack Query used for server state
- [ ] react-hook-form used for form state
- [ ] Local state minimized
- [ ] No prop drilling (use Context if needed)

## Error Handling

- [ ] try-catch blocks in mutations
- [ ] Error messages extracted safely
- [ ] Toast notifications for user feedback
- [ ] API responses validated (`response.success`)
- [ ] Query errors handled with Alert component

## Loading States

- [ ] Skeleton components for content loading
- [ ] Spinner/Loader2 for action loading
- [ ] Buttons disabled during loading
- [ ] Loading states prevent duplicate actions

## Forms

- [ ] zod schema defined
- [ ] react-hook-form used
- [ ] Field-level errors displayed
- [ ] Required fields marked with asterisk
- [ ] Optional fields handled correctly
- [ ] Form submission prevents default
- [ ] Loading state on submit button

## Tables

- [ ] DataTable component used
- [ ] Columns defined with proper types
- [ ] Sorting enabled where appropriate
- [ ] Pagination implemented for large datasets
- [ ] Row selection works correctly
- [ ] Action column has proper handlers
- [ ] Empty state message provided

## Modals

- [ ] CrudModal used for forms
- [ ] AlertDialog/ConfirmDialog for destructive actions
- [ ] Modal state managed correctly
- [ ] ESC/backdrop click handled
- [ ] Form ref implemented
- [ ] Loading state disables submit

## Testing

- [ ] data-testid attributes added
- [ ] Unit tests written for utilities
- [ ] Integration tests for components
- [ ] Tests pass (`npm test`)
- [ ] Test coverage >80% for new code
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)

## Documentation

- [ ] Props documented with JSDoc
- [ ] README updated if needed
- [ ] CHANGELOG updated if needed
- [ ] Pattern documentation updated if new pattern introduced
- [ ] Comments explain "why", not "what"

## Performance

- [ ] No unnecessary re-renders
- [ ] Lazy loading used where appropriate
- [ ] Optimistic updates implemented where beneficial
- [ ] Large lists virtualized if needed
- [ ] Images optimized

## Accessibility

- [ ] Proper semantic HTML
- [ ] Labels associated with inputs
- [ ] Keyboard navigation works
- [ ] Focus states visible
- [ ] ARIA attributes where needed
- [ ] Color contrast sufficient

## Security

- [ ] No sensitive data in console/logs
- [ ] User input sanitized
- [ ] API keys not hardcoded
- [ ] XSS prevention considered

## Git

- [ ] Commit messages follow Conventional Commits
- [ ] Branch named appropriately
- [ ] No merge conflicts
- [ ] PR description complete
- [ ] Related issues linked

## Final Checks

- [ ] Code builds without errors (`npm run build`)
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] Linter passes (`npm run lint`)
- [ ] Tests pass (`npm test`)
- [ ] Manual testing completed
- [ ] Responsive design tested
- [ ] Dark mode tested (if applicable)

---

## Approval Criteria

A PR can be approved if:

1. **All critical items checked** - Functionality, code quality, testing
2. **No blocking issues** - Security, performance, accessibility
3. **Documentation complete** - Props, patterns, README
4. **CI passes** - Build, lint, tests all green

## Common Issues to Watch For

### Anti-Patterns

- ❌ Inline styles instead of Tailwind classes
- ❌ Hardcoded colors/spacing instead of design tokens
- ❌ `any` type usage
- ❌ Unhandled promises
- ❌ Direct DOM manipulation
- ❌ Missing error handling
- ❌ Missing loading states
- ❌ Missing data-testid attributes

### Best Practices

- ✅ Design tokens for all styling
- ✅ TanStack Query for server state
- ✅ react-hook-form + zod for forms
- ✅ try-catch + toast for errors
- ✅ Skeleton components for loading
- ✅ data-testid for testing
- ✅ TypeScript strict mode
- ✅ Consistent patterns

---

## Questions During Review?

- Check [Interaction Patterns](./src/docs/INTERACTION_PATTERNS.md)
- Check [Component Library](./src/docs/COMPONENT_LIBRARY.md)
- Check [Contributing Guidelines](./CONTRIBUTING.md)
- Ask the author for clarification
- Discuss in team chat if unsure

---

**Remember:** Code reviews are about improving code quality and sharing knowledge, not criticizing the author. Be constructive and respectful in your feedback.
