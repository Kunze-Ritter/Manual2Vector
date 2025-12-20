# Testing Patterns

This document describes testing patterns and conventions for the KRAI Dashboard.

## Table of Contents

- [data-testid Conventions](#data-testid-conventions)
- [Testing Library Patterns](#testing-library-patterns)
- [Mock Patterns](#mock-patterns)
- [Test Structure](#test-structure)

---

## data-testid Conventions

Use consistent naming for test IDs across the application.

### Naming Convention

```
{component}-{element-type}
```

### Common Patterns

**Buttons:**
```tsx
<Button data-testid="create-document-button">Create</Button>
<Button data-testid="save-button">Save</Button>
<Button data-testid="delete-button">Delete</Button>
<Button data-testid="cancel-button">Cancel</Button>
```

**Inputs:**
```tsx
<Input data-testid="search-input" />
<Input data-testid="name-input" />
<Input data-testid="email-input" />
```

**Modals:**
```tsx
<Dialog data-testid="crud-modal">
<AlertDialog data-testid="delete-confirm-dialog">
```

**Tables:**
```tsx
<DataTable data-testid="documents-table" />
<DataTable data-testid="products-table" />
```

**Forms:**
```tsx
<form data-testid="document-form">
<form data-testid="user-form">
```

---

## Testing Library Patterns

### Query Selectors

```tsx
import { render, screen } from '@testing-library/react'

// Preferred: getByTestId
const button = screen.getByTestId('create-button')

// Alternative: getByRole
const button = screen.getByRole('button', { name: /create/i })

// Text content
const heading = screen.getByText(/documents/i)
```

### User Interactions

```tsx
import { userEvent } from '@testing-library/user-event'

// Click
await userEvent.click(screen.getByTestId('create-button'))

// Type
await userEvent.type(screen.getByTestId('name-input'), 'Test Name')

// Select
await userEvent.selectOptions(screen.getByTestId('status-select'), 'active')
```

### Async Testing

```tsx
import { waitFor, findByTestId } from '@testing-library/react'

// waitFor
await waitFor(() => {
  expect(screen.getByTestId('success-message')).toBeInTheDocument()
})

// findBy (combines getBy + waitFor)
const element = await screen.findByTestId('loaded-content')
```

---

## Mock Patterns

### API Mocks (MSW)

```tsx
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.get('/api/documents', (req, res, ctx) => {
    return res(ctx.json({ items: mockDocuments }))
  }),
  rest.post('/api/documents', (req, res, ctx) => {
    return res(ctx.json({ success: true, data: mockDocument }))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### Hook Mocks

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
})

const wrapper = ({ children }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
)
```

### Context Mocks

```tsx
const mockAuthContext = {
  user: { id: '1', name: 'Test User', role: 'admin' },
  isAuthenticated: true,
  login: jest.fn(),
  logout: jest.fn()
}

<AuthContext.Provider value={mockAuthContext}>
  <ComponentUnderTest />
</AuthContext.Provider>
```

---

## Test Structure

### Arrange-Act-Assert Pattern

```tsx
describe('DocumentsPage', () => {
  it('creates a new document', async () => {
    // Arrange
    render(<DocumentsPage />)
    
    // Act
    await userEvent.click(screen.getByTestId('create-document-button'))
    await userEvent.type(screen.getByTestId('name-input'), 'New Document')
    await userEvent.click(screen.getByTestId('save-button'))
    
    // Assert
    await waitFor(() => {
      expect(screen.getByText(/document created/i)).toBeInTheDocument()
    })
  })
})
```

### Test Isolation

```tsx
beforeEach(() => {
  // Reset mocks
  jest.clearAllMocks()
})

afterEach(() => {
  // Cleanup
  cleanup()
})
```

### Snapshot Tests

Use sparingly for stable UI components:

```tsx
it('matches snapshot', () => {
  const { container } = render(<Button>Click me</Button>)
  expect(container).toMatchSnapshot()
})
```

---

## Best Practices

1. **Always add data-testid** - For all interactive elements
2. **Use semantic queries** - Prefer getByRole over getByTestId when possible
3. **Test user behavior** - Not implementation details
4. **Mock external dependencies** - API calls, context, etc.
5. **Keep tests isolated** - Each test should be independent
6. **Test error states** - Not just happy paths
7. **Use meaningful test descriptions** - Clear what is being tested
8. **Avoid testing implementation** - Test behavior, not code structure

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - Components to test
- [Interaction Patterns](./INTERACTION_PATTERNS.md) - Patterns to test
- [Quick Start](./QUICK_START.md) - Testing checklist
