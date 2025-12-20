# Contributing to KRAI Dashboard

Thank you for your interest in contributing to the KRAI Dashboard! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Code Style](#code-style)
- [Component Guidelines](#component-guidelines)
- [Git Workflow](#git-workflow)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

---

## Code Style

### TypeScript

- Use **TypeScript strict mode**
- Define explicit types for all props, state, and function parameters
- Use type inference where appropriate
- Avoid `any` type - use `unknown` if type is truly unknown

```typescript
// ✅ Good
type UserProps = {
  name: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
}

// ❌ Bad
type UserProps = {
  name: any
  email: any
  role: string
}
```

### Naming Conventions

- **Components:** PascalCase (`DocumentForm`, `DataTable`)
- **Functions/Variables:** camelCase (`handleSubmit`, `isLoading`)
- **Constants:** UPPER_SNAKE_CASE (`DEFAULT_PAGE_SIZE`, `API_BASE_URL`)
- **Types/Interfaces:** PascalCase (`User`, `ApiResponse`)
- **Files:** kebab-case for utilities (`api-client.ts`), PascalCase for components (`DocumentForm.tsx`)

### ESLint & Prettier

- Run `npm run lint` before committing
- Fix all ESLint warnings and errors
- Prettier formatting is enforced automatically

---

## Component Guidelines

### Use Design Tokens

Always use design tokens from the theme system:

```tsx
// ✅ Good
<div className="p-md gap-sm bg-background text-foreground">

// ❌ Bad
<div style={{ padding: '16px', gap: '8px', background: '#fff' }}>
```

### Implement data-testid

Add `data-testid` attributes to all interactive elements:

```tsx
<Button data-testid="create-button">Create</Button>
<Input data-testid="search-input" />
<DataTable data-testid="documents-table" />
```

### Document Props with JSDoc

```typescript
/**
 * Form component for creating and editing documents
 * 
 * @param mode - 'create' or 'edit' mode
 * @param initialData - Initial form data (required for edit mode)
 * @param onSubmit - Callback when form is submitted
 */
type DocumentFormProps = {
  mode: 'create' | 'edit'
  initialData?: DocumentData | null
  onSubmit: (data: DocumentData) => void | Promise<void>
}
```

### Export Types

Always export component prop types:

```typescript
export type ButtonProps = {
  variant?: 'default' | 'destructive' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

export function Button({ variant = 'default', size = 'md', children }: ButtonProps) {
  // ...
}
```

---

## Git Workflow

### Branch Naming

- `feature/` - New features (`feature/add-batch-delete`)
- `bugfix/` - Bug fixes (`bugfix/fix-pagination-error`)
- `docs/` - Documentation (`docs/update-readme`)
- `refactor/` - Code refactoring (`refactor/simplify-api-hooks`)

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**
```
feat(documents): add batch delete functionality
fix(forms): resolve validation error display issue
docs(patterns): add form patterns documentation
refactor(api): simplify query hooks
```

### Commit Checklist

Before committing:

- [ ] Code follows style guidelines
- [ ] No ESLint warnings
- [ ] Tests pass (`npm test`)
- [ ] Types are correct (`npm run type-check`)
- [ ] Documentation updated if needed

---

## Testing Requirements

### Unit Tests

Write unit tests for:
- Utility functions
- Custom hooks
- Complex logic

```typescript
describe('formatDate', () => {
  it('formats date correctly', () => {
    const date = new Date('2024-01-01')
    expect(formatDate(date)).toBe('Jan 1, 2024')
  })
})
```

### Integration Tests

Write integration tests for:
- Components with user interactions
- Form submissions
- API integrations

```typescript
describe('DocumentForm', () => {
  it('submits form with valid data', async () => {
    render(<DocumentForm onSubmit={mockSubmit} />)
    await userEvent.type(screen.getByTestId('name-input'), 'Test')
    await userEvent.click(screen.getByTestId('submit-button'))
    expect(mockSubmit).toHaveBeenCalledWith({ name: 'Test' })
  })
})
```

### E2E Tests

Write E2E tests for:
- Critical user flows
- Multi-step processes
- Cross-component interactions

### Test Coverage

- Aim for **>80% coverage**
- Focus on critical paths
- Don't test implementation details

---

## Pull Request Process

### Before Creating PR

1. **Create feature branch** from `main`
2. **Implement changes** following guidelines
3. **Write tests** for new functionality
4. **Run test suite** (`npm test`)
5. **Run linter** (`npm run lint`)
6. **Update documentation** if needed
7. **Self-review** your changes

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass
```

### Code Review

Your PR will be reviewed for:
- Code quality and style
- Test coverage
- Documentation
- Performance implications
- Security considerations

See [Code Review Checklist](./CODE_REVIEW_CHECKLIST.md) for details.

### Merging

- PRs require **at least one approval**
- All CI checks must pass
- Conflicts must be resolved
- Squash and merge preferred for feature branches

---

## Questions?

If you have questions or need help:
- Check [Documentation](./src/docs/)
- Ask in team chat
- Create a discussion issue

Thank you for contributing! 🎉
