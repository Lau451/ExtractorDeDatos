# Coding Conventions

**Analysis Date:** 2026-03-18

## Project Status

This is a pre-implementation project (ExtraccionDeDatosNE2.0) in initial setup phase. These conventions establish the coding standards to be followed during development.

## Naming Patterns

**Files:**
- Source files: `camelCase.ts` (e.g., `userService.ts`, `dataExtractor.ts`)
- Component files: `PascalCase.tsx` (e.g., `UserCard.tsx`, `DataTable.tsx`)
- Test files: `<name>.test.ts` or `<name>.spec.ts` (e.g., `userService.test.ts`)
- Config files: `kebab-case.config.ts` (e.g., `build.config.ts`)
- Index files: `index.ts` for barrel exports

**Functions:**
- Regular functions: `camelCase` (e.g., `extractData()`, `parseInput()`)
- Constructor/Class names: `PascalCase` (e.g., `DataExtractor`, `UserRepository`)
- Private methods: `camelCase` prefixed with `_` or use `#` private fields (e.g., `_validate()`)
- Async functions: same naming, but clearly indicate async behavior in documentation

**Variables:**
- Constants: `UPPER_SNAKE_CASE` for module-level constants (e.g., `DEFAULT_TIMEOUT`, `API_ENDPOINT`)
- Regular variables: `camelCase` (e.g., `userData`, `extractionCount`)
- Boolean variables: prefix with `is`, `has`, `should`, `can` (e.g., `isValid`, `hasData`, `shouldRetry`)
- React hooks: prefix with `use` (e.g., `useData`, `useExtractor`)

**Types:**
- Interfaces: `PascalCase` prefixed with `I` or unprefixed (e.g., `IUserData` or `UserData`)
- Types: `PascalCase` (e.g., `ExtractionResult`, `DataSource`)
- Enums: `PascalCase` (e.g., `ExtractionStatus`, `DataFormat`)
- Generic type params: Single uppercase letter (e.g., `T`, `K`, `V`) or descriptive name (e.g., `TData`)

**Directories:**
- Feature directories: `lowercase` (e.g., `src/features/extraction`, `src/services/data`)
- Utility directories: `lowercase` (e.g., `src/utils`, `src/helpers`)
- Type directories: `types` or `@types` (e.g., `src/types`, `src/@types`)

## Code Style

**Formatting:**
- Indentation: 2 spaces (not tabs)
- Max line length: 100 characters
- Semicolons: Required at end of statements
- Quotes: Single quotes `'` for strings (unless interpolation is needed)
- Trailing commas: Always include in multi-line objects/arrays

**Linting:**
- Tool: ESLint (configured with TypeScript support)
- Expected rules: Standard ESLint rules with Prettier integration
- Auto-format on save: Enabled via Prettier

**Prettier Configuration (assumed):**
```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

## Import Organization

**Order:**
1. Node.js built-in modules (e.g., `fs`, `path`, `http`)
2. Third-party packages (e.g., `react`, `lodash`, `axios`)
3. Absolute path imports (e.g., `@/services`, `@/types`)
4. Relative imports (e.g., `../utils`, `./types`)
5. Side-effect imports (e.g., `import './styles.css'`) at end if needed

**Path Aliases:**
- `@/` - project root or src directory
- `@/types` - type definitions
- `@/services` - service layer
- `@/utils` - utility functions
- `@/features` - feature modules

**Example:**
```typescript
import fs from 'fs';
import path from 'path';
import axios from 'axios';
import { DataService } from '@/services/dataService';
import { ExtractionUtils } from '@/utils/extraction';
import { extractData } from '../helpers';
import type { DataSource } from '@/types';
```

## Error Handling

**Patterns:**
- Use `try-catch` for async operations
- Create custom error classes extending `Error` (e.g., `class ValidationError extends Error {}`)
- Include error context: always pass meaningful error messages
- Log errors with context before throwing
- Never swallow errors silently

**Example:**
```typescript
class ExtractionError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'ExtractionError';
  }
}

async function extractData(source: DataSource): Promise<Data> {
  try {
    const result = await fetchData(source);
    return parseData(result);
  } catch (error) {
    logger.error('Data extraction failed', { source, error });
    throw new ExtractionError('Failed to extract data', 'EXTRACTION_FAILED');
  }
}
```

## Logging

**Framework:** `console` or structured logging library (e.g., `winston`, `pino`)

**Patterns:**
- Use log levels: `debug`, `info`, `warn`, `error`
- Include context in log messages: operation name, user id, request id
- Avoid logging sensitive data (passwords, tokens, PII)
- Use structured logging (JSON format) for production

**Example:**
```typescript
logger.info('Extraction started', { source: 'api', userId: user.id });
logger.debug('Processing chunk', { chunkSize: data.length });
logger.warn('Timeout approaching', { remaining: 5000 });
logger.error('Extraction failed', { source, error: error.message });
```

## Comments

**When to Comment:**
- Complex business logic that isn't obvious from reading the code
- Non-obvious workarounds or hacks (with explanation of why)
- Public API documentation (JSDoc for functions, classes, exports)
- Important assumptions or constraints

**When NOT to Comment:**
- What the code obviously does (don't comment obvious loops/conditionals)
- Variable names that already explain intent
- Every line of code

**JSDoc/TSDoc:**
- Required for all exported functions and classes
- Include `@param`, `@returns`, `@throws` tags
- Include `@example` for complex functions

**Example:**
```typescript
/**
 * Extracts data from the specified source using configured parsers.
 *
 * @param source - The data source to extract from
 * @param options - Extraction options (timeout, retries, format)
 * @returns Promise resolving to extracted data
 * @throws {ExtractionError} If extraction fails after retries
 *
 * @example
 * const data = await extractData({ url: 'https://api.example.com' });
 */
export async function extractData(
  source: DataSource,
  options?: ExtractionOptions,
): Promise<Data> {
  // implementation
}
```

## Function Design

**Size:**
- Target: 20-40 lines per function
- Maximum: 100 lines without strong justification
- If a function exceeds 100 lines, refactor into smaller functions

**Parameters:**
- Maximum 3 parameters (if more needed, use object destructuring)
- Use object parameters for optional configuration
- Type all parameters explicitly

**Return Values:**
- Single responsibility: return one type of value
- Use union types for multiple success/error paths sparingly
- Prefer explicit error throwing over returning null/undefined
- For async functions, always return a Promise with explicit type

**Example:**
```typescript
// Good: clear parameters, specific return type
export function validateExtraction(data: Data, config: ValidationConfig): ValidationResult {
  // implementation
}

// Avoid: too many parameters
export function process(a: string, b: number, c: boolean, d: string, e: object) {}

// Better: use object parameter
export function process(options: ProcessOptions) {}
```

## Module Design

**Exports:**
- Default exports: rarely used, prefer named exports
- Export types alongside implementations
- Create `index.ts` barrel files to group related exports
- Mark internal/private modules clearly (e.g., `internal/` directory)

**Example:**
```typescript
// src/services/dataService.ts
export interface DataServiceConfig {}
export class DataService {}
export async function extractData() {}

// src/services/index.ts (barrel file)
export * from './dataService';
export * from './validationService';
```

## Barrel Files

- Use barrel files (`index.ts`) to expose public APIs of modules
- Keep barrel files simple: just re-exports, no logic
- Group related functionality in barrels
- Location: `src/services/index.ts`, `src/types/index.ts`, etc.

## TypeScript Strictness

- `strict: true` in tsconfig.json (all strict checks enabled)
- No `any` types - use `unknown` with type narrowing if necessary
- All function returns typed explicitly
- All parameters typed explicitly

---

*Convention analysis: 2026-03-18*
