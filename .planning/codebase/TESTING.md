# Testing Patterns

**Analysis Date:** 2026-03-18

## Project Status

This is a pre-implementation project (ExtraccionDeDatosNE2.0) in initial setup phase. These testing patterns establish the standards to be followed during development.

## Test Framework

**Runner:**
- Framework: Vitest (or Jest)
- Version: Latest stable
- Config: `vitest.config.ts` or `jest.config.js`

**Assertion Library:**
- Library: Vitest native assertions or `expect` from Jest/Vitest
- No additional assertion libraries required

**Run Commands:**
```bash
npm test                    # Run all tests
npm test -- --watch         # Watch mode (rerun on file changes)
npm test -- --coverage      # Run with coverage report
npm test -- --ui            # Open Vitest UI
npm test -- <pattern>       # Run tests matching pattern
```

## Test File Organization

**Location:**
- Pattern: Co-located with source code
- Structure: `src/features/extraction/extraction.test.ts` (next to `extraction.ts`)
- Alternatively: `src/__tests__/` directory for shared test utilities

**Naming:**
- Pattern: `<module>.test.ts` or `<module>.spec.ts`
- Examples:
  - `dataExtractor.test.ts`
  - `userService.test.ts`
  - `validation.spec.ts`

**Structure:**
```
src/
├── features/
│   ├── extraction/
│   │   ├── extraction.ts
│   │   ├── extraction.test.ts
│   │   └── types.ts
│   └── validation/
│       ├── validation.ts
│       └── validation.test.ts
├── services/
│   ├── dataService.ts
│   ├── dataService.test.ts
│   └── index.ts
└── __tests__/
    ├── fixtures/          # Test data
    ├── mocks/             # Mock generators
    └── setup.ts           # Test configuration
```

## Test Structure

**Suite Organization:**
```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DataExtractor } from './dataExtractor';

describe('DataExtractor', () => {
  let extractor: DataExtractor;

  beforeEach(() => {
    extractor = new DataExtractor();
  });

  describe('extractData', () => {
    it('should extract data from valid source', async () => {
      const result = await extractor.extractData({ url: 'https://example.com' });
      expect(result).toBeDefined();
      expect(result.rows).toHaveLength(10);
    });

    it('should throw on invalid source', async () => {
      await expect(extractor.extractData({ url: 'invalid' }))
        .rejects.toThrow('Invalid URL');
    });
  });
});
```

**Patterns:**
- Setup: `beforeEach()` for test initialization, `beforeAll()` for expensive setup
- Teardown: `afterEach()` for cleanup, `afterAll()` for final cleanup
- Assertion: Use `expect()` with chainable matchers (e.g., `expect().toBe()`, `expect().toThrow()`)
- Nesting: Use nested `describe()` blocks for test organization by feature/method

## Mocking

**Framework:** Vitest built-in `vi` module (or Jest's `jest.mock()`)

**Patterns:**
```typescript
// Mock module imports
vi.mock('@/services/dataService', () => ({
  DataService: vi.fn(() => ({
    fetch: vi.fn().mockResolvedValue({ data: [] }),
  })),
}));

// Mock individual functions
const mockFetch = vi.fn();
vi.mock('node-fetch', () => ({ default: mockFetch }));

// Spy on method and mock return value
const spy = vi.spyOn(extractor, 'validate').mockReturnValue(true);

// Verify mock was called
expect(mockFetch).toHaveBeenCalledWith('https://example.com');
```

**What to Mock:**
- External API calls (HTTP requests, database queries)
- File system operations (reading, writing files)
- Date/time operations (Date.now, setTimeout)
- Environment-specific dependencies
- Third-party services (Stripe, Auth0, etc.)

**What NOT to Mock:**
- Core business logic (validation, transformation, parsing)
- Internal function calls within the module
- Data structures and types
- Standard library functions (unless testing error cases)

## Fixtures and Factories

**Test Data:**
```typescript
// src/__tests__/fixtures/data.ts
export const mockDataSource = {
  url: 'https://example.com/api/data',
  format: 'csv',
  timeout: 5000,
};

export const mockExtractedData = {
  rows: [
    { id: 1, name: 'Test', value: 100 },
    { id: 2, name: 'Test2', value: 200 },
  ],
  metadata: {
    count: 2,
    extracted: new Date('2026-03-18'),
  },
};

// Factory pattern for generating test data
export function createDataSource(overrides?: Partial<DataSource>): DataSource {
  return {
    ...mockDataSource,
    ...overrides,
  };
}
```

**Location:**
- Fixtures: `src/__tests__/fixtures/` directory
- Factories: `src/__tests__/factories/` or alongside fixtures
- Import in tests: `import { mockDataSource, createDataSource } from '@/__tests__/fixtures/data'`

## Coverage

**Requirements:**
- Target: 80% line coverage minimum
- Target: 75% branch coverage minimum
- Critical paths: 100% coverage (extraction logic, validation, error handling)

**View Coverage:**
```bash
npm test -- --coverage
npm test -- --coverage --ui  # Interactive coverage viewer
```

**Coverage Report Location:**
- HTML report: `coverage/index.html`
- JSON report: `coverage/coverage-final.json`

## Test Types

**Unit Tests:**
- Scope: Single function or class method
- Isolation: All external dependencies mocked
- Focus: Business logic, edge cases, error conditions
- Example: Testing `validateData()` function with various inputs
- Location: `src/services/validation.test.ts`

**Integration Tests:**
- Scope: Multiple modules working together
- Isolation: Minimal mocking, test real interactions
- Focus: Data flow between components, API contracts
- Example: Testing data extraction pipeline from source to storage
- Location: `src/__tests__/integration/extraction.test.ts`

**E2E Tests:**
- Framework: Playwright or Cypress
- Scope: Complete user workflows
- Status: Not required for initial implementation
- Location: `e2e/` directory if added

## Common Patterns

**Async Testing:**
```typescript
// Using async/await with try-catch
it('should handle async operations', async () => {
  const result = await extractor.extractData(source);
  expect(result).toBeDefined();
});

// Using promises
it('should reject on error', () => {
  return expect(extractor.extractData(invalidSource))
    .rejects.toThrow('Invalid source');
});

// Testing timeout behavior
it('should timeout if operation takes too long', async () => {
  vi.useFakeTimers();
  const promise = extractor.extractData(slowSource);
  vi.advanceTimersByTime(6000);
  await expect(promise).rejects.toThrow('Timeout');
  vi.useRealTimers();
});
```

**Error Testing:**
```typescript
// Test specific error type
it('should throw ValidationError on invalid input', () => {
  expect(() => validator.validate(invalidData))
    .toThrow(ValidationError);
});

// Test error message
it('should include field name in error', () => {
  expect(() => validator.validate(invalidData))
    .toThrow('Field "email" is invalid');
});

// Test error code
it('should set appropriate error code', () => {
  try {
    validator.validate(invalidData);
  } catch (error) {
    expect(error.code).toBe('INVALID_EMAIL');
  }
});
```

**Testing Callbacks:**
```typescript
it('should call completion handler on success', (done) => {
  extractor.extractData(source, (error, result) => {
    if (error) done(error);
    expect(result).toBeDefined();
    done();
  });
});

// Or use vi.waitFor
it('should call handler eventually', async () => {
  let called = false;
  processor.on('complete', () => {
    called = true;
  });
  processor.start();

  await vi.waitFor(() => {
    expect(called).toBe(true);
  });
});
```

**Testing Promises:**
```typescript
// Return promise directly
it('should resolve with data', () => {
  return expect(extractor.extractData(source))
    .resolves.toHaveProperty('rows');
});

// Chain assertions
it('should resolve in correct order', async () => {
  const result = await pipeline.process(data);
  expect(result.status).toBe('completed');
  expect(result.rows).toHaveLength(10);
});
```

## Test Execution

**Default behavior:**
- Run all tests matching `**/*.test.ts` or `**/*.spec.ts`
- Exclude: `node_modules/`, `dist/`, `coverage/`

**Test lifecycle:**
1. Load test file
2. Run all `beforeAll` hooks
3. For each test:
   - Run `beforeEach` hooks
   - Execute test
   - Run `afterEach` hooks
4. Run all `afterAll` hooks
5. Report results

## Best Practices

1. **Test behavior, not implementation**: Tests should describe what the code does, not how it works
2. **One assertion concept per test**: A test should verify one thing (though may have multiple assertions)
3. **Clear test names**: `it('should extract data from valid CSV source')`  not `it('extraction works')`
4. **DRY test code**: Use factories, fixtures, and setup methods to avoid duplication
5. **Fast tests**: Avoid real I/O, use mocks; aim for < 100ms per test
6. **Deterministic**: Tests should not depend on time, random values, or external state
7. **Isolated**: Tests should not depend on other tests running before them

---

*Testing analysis: 2026-03-18*
