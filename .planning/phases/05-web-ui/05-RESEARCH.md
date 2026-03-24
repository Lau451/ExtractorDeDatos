# Phase 5: Web UI - Research

**Researched:** 2026-03-23
**Domain:** React SPA with Vite, Tailwind CSS, shadcn/ui, polling-based workflow integration
**Confidence:** HIGH

## Summary

Phase 5 is a greenfield React SPA that sits in front of an already-complete FastAPI backend. All five REST endpoints are verified as working: `POST /extract` (returns job_id), `GET /jobs/{id}` (polling, always HTTP 200 even on error), `PATCH /jobs/{id}/doc_type` (returns 202, triggers re-extraction), `PATCH /jobs/{id}/fields` (deep-merge, returns full updated JobResponse), and `GET /jobs/{id}/export` (returns CSV bytes). The UI's only job is to drive this workflow linearly: upload → poll → review → download → reset.

The tech stack (React + Vite + Tailwind + shadcn/ui) is locked by user decision. All four libraries are current, well-documented, and compose cleanly. Vite's dev proxy eliminates CORS entirely during development. Production deployment is a single FastAPI process that mounts `frontend/dist/` as static files with an `index.html` catch-all — no second server needed.

The most complex UI interaction is the click-to-edit review table with two distinct structures: a two-column header table and a multi-column line items table (only for purchase_order, invoice, supplier_comparison). PATCH requests fire on blur/Enter for individual cells and carry the changed field at the correct nesting level of the `extraction_result` dict. The document type override dropdown triggers a PATCH to `/jobs/{id}/doc_type` which returns 202 and restarts polling.

**Primary recommendation:** Scaffold `frontend/` with `npm create vite@latest -- --template react-ts`, install Tailwind v4 + `@vitejs/plugin-react`, initialize shadcn/ui, add react-dropzone and lucide-react, then build components top-down following the linear flow state machine.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **React** with **Vite** as the build tool (fast HMR, first-class React support)
- **Tailwind CSS** for styling (utility-first, no separate stylesheets)
- **shadcn/ui** component library on top of Tailwind (copy-paste Radix UI components — Table, Input, Dropdown, Button)
- **Frontend directory:** `frontend/` at repo root, alongside `src/` (Python)
- Review table: **Two-column table** (Label | Value) for header fields, powered by shadcn/ui Table
- Line items: **Separate multi-column table below header fields** (not tabs, not collapsible); document types without line items show only the header table
- Inline editing: **Click-to-edit** — clicking value cell switches to `<input>`, save on blur or Enter
- Value cells have subtle hover highlight (`hover:bg-muted/50`) to signal editability
- "Not found" displayed as **muted gray italic** (`text-muted-foreground italic`)
- Processing indicator: **Centered spinner + status text** that updates from `status` field of polling response
- Status text stages: `"Uploading..."` → `"Classifying document..."` → `"Extracting fields..."` → done
- Error feedback: **Inline error banner** replaces spinner area on failure, shows human-readable message from `error_code`, with **"Try again" button** that resets to upload state
- No toast notifications
- After CSV download: **"Upload another document" button** resets to upload state
- Flow is linear: upload → process → review → download → reset (no persistent upload zone)
- **Vite dev proxy:** all `/api/*` requests proxied to `http://localhost:8000`
- **Production:** FastAPI serves built Vite output from `frontend/dist/`; one URL, one process
- Status polling every **1-2 seconds** until `status` is `complete` or `error`
- No WebSocket or SSE

### Claude's Discretion
- Exact polling interval (1s vs 2s) and backoff strategy
- Drag-and-drop implementation details (react-dropzone or native HTML5)
- Exact component breakdown and file structure inside `frontend/`
- How PATCH requests are batched or debounced (per-field on blur vs. batch on download)
- Document type override dropdown placement and trigger timing

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REV-01 | User can see all extracted fields displayed in a review table before downloading CSV | `extraction_result` dict from `GET /jobs/{id}` when `status === "complete"`; header fields + optional line items array; shadcn/ui Table renders both structures |
| REV-02 | User can edit any extracted field value inline in the review table | Click-to-edit `<input>` on value cells; on blur/Enter fires `PATCH /jobs/{id}/fields` with `{fields: {field_name: new_value}}`; PATCH returns full updated JobResponse |
| REV-03 | Fields that could not be extracted are shown as "Not found" (not blank) | Backend already serializes `None → "Not found"` in `_serialize_extraction()`; UI must preserve and display these strings with `text-muted-foreground italic` styling |
| REV-04 | User can see extraction progress (spinner with status text) while document is being processed | Poll `GET /jobs/{id}` every 1-2s; map `status` field to human-readable stage text; show spinner; on `complete` transition to review table; on `error` show error banner |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.4 | UI rendering | Locked decision |
| react-dom | 19.2.4 | DOM renderer | Paired with React |
| vite | 8.0.2 | Build tool, dev server, proxy | Locked decision; fast HMR |
| @vitejs/plugin-react | latest | Vite React transform (Fast Refresh) | Official Vite plugin for React |
| tailwindcss | 4.2.2 | Utility-first styling | Locked decision |
| @tailwindcss/vite | latest | Vite integration for Tailwind v4 | Replaces PostCSS config in Tailwind v4 |
| typescript | 6.0.2 | Type safety | Standard for React + Vite scaffold |

**Version verified:** 2026-03-23 via `npm view`.

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-dropzone | 15.0.0 | Drag-and-drop + file picker | Preferred over native HTML5: handles drag state, ARIA, file filtering in one hook |
| lucide-react | 1.0.1 | Icon set (spinner, upload, check, alert) | Tailwind-friendly SVG icons; works with shadcn/ui |
| clsx | 2.1.1 | Conditional class composition | Cleaner than template literals for conditional Tailwind classes |
| tailwind-merge | 3.5.0 | Merge conflicting Tailwind classes | Required by shadcn/ui `cn()` util |
| class-variance-authority | 0.7.1 | Variant-based component styling | Required by shadcn/ui component internals |

**shadcn/ui** is NOT an npm package — it is a CLI that copies component source into `frontend/src/components/ui/`. Components needed: `Table`, `Button`, `Input`, `Select` (for doc type dropdown), `Badge` (optional doc type display).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-dropzone | Native HTML5 `<input type="file">` + drag events | Native saves a dep but requires manual drag-over state, ARIA, multi-event wiring — react-dropzone resolves in ~10 lines |
| shadcn/ui Table | Plain HTML `<table>` + Tailwind | shadcn/ui Table provides consistent spacing/borders; plain table is fine but requires more custom CSS |
| lucide-react | heroicons or react-icons | Any works; lucide-react is already the shadcn/ui default icon set |

**Installation (scaffold):**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install tailwindcss @tailwindcss/vite
npm install react-dropzone lucide-react clsx tailwind-merge class-variance-authority
npx shadcn@latest init
npx shadcn@latest add table button input select badge
```

**Important:** Tailwind v4 uses `@tailwindcss/vite` plugin (not PostCSS). The shadcn CLI version `shadcn@latest` handles Tailwind v4 automatically. If targeting Tailwind v3 compatibility, use `shadcn@2.3.0`.

---

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui copied components (Table, Button, etc.)
│   │   ├── UploadZone.tsx   # react-dropzone, file validation feedback
│   │   ├── ProgressView.tsx # spinner + status text, error banner
│   │   ├── ReviewTable.tsx  # header fields two-column table
│   │   ├── LineItemsTable.tsx # multi-column line items (conditional)
│   │   ├── DocTypeBar.tsx   # doc type display + override dropdown
│   │   └── EditableCell.tsx # click-to-edit cell (shared by both tables)
│   ├── hooks/
│   │   ├── useJobPoller.ts  # polling logic, returns {status, data, error}
│   │   └── useFileUpload.ts # POST /extract, returns jobId
│   ├── lib/
│   │   ├── api.ts           # fetch wrappers for all 5 endpoints
│   │   ├── errorMessages.ts # error_code → human-readable string map
│   │   ├── fieldLabels.ts   # extraction_result key → human-readable label
│   │   └── utils.ts         # cn() (shadcn/ui standard)
│   ├── types/
│   │   └── api.ts           # TypeScript interfaces matching JobResponse shape
│   ├── App.tsx              # top-level state machine: upload|processing|review|done
│   └── main.tsx
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### Pattern 1: Linear Flow State Machine in App.tsx
**What:** Top-level component holds a `phase` discriminated union: `'upload' | 'processing' | 'review' | 'done'`. Each phase renders exactly one view. State transitions are driven by events (file dropped, poll completed, download clicked, reset clicked).

**When to use:** Single-page linear flows where back-navigation is intentionally disabled. Avoids router complexity for a 4-step wizard.

**Example:**
```typescript
// App.tsx — state machine pattern
type Phase =
  | { tag: 'upload' }
  | { tag: 'processing'; jobId: string }
  | { tag: 'review'; jobId: string; jobData: JobResponse }
  | { tag: 'done'; jobId: string; jobData: JobResponse };

const [phase, setPhase] = useState<Phase>({ tag: 'upload' });

// Transition: file submitted
const handleUpload = async (file: File) => {
  const { job_id } = await api.postExtract(file);
  setPhase({ tag: 'processing', jobId: job_id });
};

// Transition: poll returned complete
const handlePollComplete = (jobId: string, data: JobResponse) => {
  setPhase({ tag: 'review', jobId, jobData: data });
};

// Transition: reset
const handleReset = () => setPhase({ tag: 'upload' });
```

### Pattern 2: Polling Hook with Cleanup
**What:** `useJobPoller` encapsulates `setInterval` polling against `GET /jobs/{id}`. Returns current status data. Stops automatically when `status` is `complete` or `error`. Cleans up on unmount.

**When to use:** Always — never inline polling logic in a component. The hook isolates timing, cleanup, and status mapping.

**Example:**
```typescript
// hooks/useJobPoller.ts
function useJobPoller(jobId: string | null, onComplete: (data: JobResponse) => void, onError: (data: JobResponse) => void) {
  useEffect(() => {
    if (!jobId) return;
    const id = setInterval(async () => {
      const data = await api.getJob(jobId);
      if (data.status === 'complete') {
        clearInterval(id);
        onComplete(data);
      } else if (data.status === 'error') {
        clearInterval(id);
        onError(data);
      }
    }, 1500); // 1.5s — midpoint of 1-2s range
    return () => clearInterval(id);
  }, [jobId]);
}
```

**Pitfall:** Missing the `return () => clearInterval(id)` cleanup causes polling to continue after the component unmounts (e.g., after reset), silently updating stale state.

### Pattern 3: EditableCell with Blur/Enter Save
**What:** A cell that renders display text when inactive, switches to a controlled `<input>` on click, and fires the PATCH on blur or Enter key.

**When to use:** Both the header field table and the line items table reuse this component.

**Example:**
```typescript
// components/EditableCell.tsx
function EditableCell({ value, onSave }: { value: string; onSave: (v: string) => void }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);

  const commit = () => { setEditing(false); if (draft !== value) onSave(draft); };

  if (editing) {
    return (
      <input
        autoFocus
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false); }}
        className="w-full bg-transparent border-b border-primary outline-none px-1"
      />
    );
  }
  const isNotFound = value === 'Not found';
  return (
    <span
      onClick={() => { setDraft(value === 'Not found' ? '' : value); setEditing(true); }}
      className={`cursor-pointer hover:bg-muted/50 px-1 rounded ${isNotFound ? 'text-muted-foreground italic' : ''}`}
    >
      {value}
    </span>
  );
}
```

### Pattern 4: PATCH fields — nested path handling
**What:** Line item edits need to be sent as `{ fields: { line_items: [{ ...updated_row }] } }`. The deep-merge backend handles this correctly if the entire updated line items array is sent.

**When to use:** When the user edits a cell in the line items table. The simplest correct approach is to send the entire mutated `line_items` array in the PATCH body, not individual row diffs.

**Rationale:** The backend `_deep_merge` function merges recursively. Sending `{ line_items: [row0, row1_mutated, row2] }` correctly updates the line items array without overwriting unrelated header fields.

### Pattern 5: Vite Dev Proxy
**What:** All `/api/*` fetch calls are rewritten to `http://localhost:8000` by Vite's dev server. The React code uses relative paths (`/api/...`) with no hardcoded host.

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  resolve: {
    alias: { '@': '/src' },
  },
});
```

**Note:** The backend routes use `/extract`, `/jobs/...`, not `/api/extract`. The `rewrite` strips `/api` prefix so that `fetch('/api/extract')` reaches `POST http://localhost:8000/extract`.

### Pattern 6: FastAPI SPA Static Serving (Production)
**What:** Mount `frontend/dist/` as static files, then add a catch-all GET route that returns `index.html` for all non-API paths. This enables client-side navigation (though this app has no routes) and ensures direct URL access works.

```python
# src/main.py addition — production static serving
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        index = os.path.join(dist_dir, "index.html")
        return FileResponse(index)
```

**Critical ordering:** The catch-all route MUST be registered AFTER all API routers. FastAPI evaluates routes in registration order — a leading catch-all would shadow `/extract`, `/jobs/...`, etc.

### Anti-Patterns to Avoid
- **Global fetch state in component body:** Never call `fetch()` directly inside a component render path. Always use `useEffect` or an event handler.
- **Polling without cleanup:** Always return the `clearInterval` from `useEffect` to prevent memory leaks and ghost state updates after component unmount.
- **Mutating `extraction_result` in place:** Always spread/copy the data before editing — React state mutations cause missed re-renders.
- **Catch-all route registered before API routes:** Shadows all API endpoints in production.
- **`vite.config.ts` proxy without `rewrite`:** If backend routes don't have an `/api` prefix, the rewrite is mandatory.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag-and-drop + file picker | Manual `ondragover`, `ondrop`, `ondragleave` events | react-dropzone `useDropzone` hook | Handles drag state, keyboard access, MIME filtering, `accept` prop, mobile fallback |
| Spinner / loading animation | Custom CSS `@keyframes` | Tailwind `animate-spin` on a `lucide-react` `Loader2` icon | Zero effort, consistent with design system |
| Modal/dropdown for doc type | Custom absolute-positioned div | shadcn/ui `Select` (wraps Radix UI) | Handles keyboard navigation, ARIA, focus trap, portal positioning |
| Table component | `<table>` + manual cell padding | shadcn/ui `Table` | Consistent header/row/cell sizing, built-in responsive behavior |
| Class conditional logic | Ternary template literals | `clsx` + `tailwind-merge` via `cn()` | Handles conflicting class deduplication (shadcn/ui standard pattern) |
| Icon SVGs | Inline SVG markup | lucide-react | Tree-shakeable, consistent stroke width, size via className |

**Key insight:** All the "widget" complexity (dropdowns, tables, focus management, ARIA) is already solved by the Radix UI primitives that shadcn/ui wraps. The implementation effort should be spent on workflow state and data shape mapping, not UI primitives.

---

## Common Pitfalls

### Pitfall 1: API Route Shadowing in Production
**What goes wrong:** FastAPI catch-all for SPA is registered before the API routers, causing all API calls to return `index.html` (200 HTML, not JSON).
**Why it happens:** Developers add the catch-all mount at the top of `main.py` for visibility.
**How to avoid:** Register all `include_router()` calls first. Add the catch-all route LAST, guarded by `if os.path.isdir(dist_dir)`.
**Warning signs:** All API calls return 200 with HTML content-type in production.

### Pitfall 2: Vite Proxy Rewrite Mismatch
**What goes wrong:** `fetch('/api/extract')` reaches FastAPI as `/api/extract`, which doesn't match the registered route `/extract` → 404.
**Why it happens:** Forgetting the `rewrite: (path) => path.replace(/^\/api/, '')` in `vite.config.ts`.
**How to avoid:** Always verify the rewrite strips the prefix. Test with `curl http://localhost:5173/api/health`.
**Warning signs:** 404s in dev that don't happen when calling FastAPI port directly.

### Pitfall 3: Polling Ghost After Reset
**What goes wrong:** User hits "Try again" while polling is active. The old interval continues, fires `onComplete`, and transitions to review state even though a new upload hasn't happened.
**Why it happens:** `useEffect` cleanup (the `return` function) isn't triggered if `jobId` doesn't change, or the interval isn't stored in a ref.
**How to avoid:** `useJobPoller` must accept `jobId` as a dependency and clean up the previous interval when `jobId` changes. Use a `useRef` to store the interval ID so cleanup always references the live value.

### Pitfall 4: doc_type Override Polling Race
**What goes wrong:** User overrides doc type. PATCH returns 202 with `status: "extracting"`. UI needs to re-enter the polling loop. If polling was stopped at `complete`, the interval is already cleared.
**Why it happens:** The polling hook only starts once (on job creation). Re-extraction from doc-type override restarts the job status.
**How to avoid:** After `PATCH /jobs/{id}/doc_type` responds 202, explicitly restart the polling hook. Either pass a `pollingKey` that changes on override, or call a `restart()` function exposed by the hook.

### Pitfall 5: Line Items Edit Sends Wrong PATCH Shape
**What goes wrong:** Editing a line item cell sends `{ fields: { description: "new value" } }`, which deep-merges into the root `extraction_result` dict (not into the correct line item row).
**Why it happens:** The flat PATCH shape works for header fields but line items are nested under a key (e.g., `line_items`, `items`) as an array of dicts.
**How to avoid:** For line items, send the entire updated array: `{ fields: { line_items: [...updatedRows] } }`. The deep-merge on the backend will correctly replace the array.

### Pitfall 6: "Not Found" String Overwritten Without User Input
**What goes wrong:** User accidentally clicks a "Not found" cell and blurs away without typing — PATCH fires with empty string, replacing the "Not found" placeholder.
**Why it happens:** The `EditableCell` transitions to input mode when clicked, and blur fires the commit even if nothing was typed.
**How to avoid:** In `commit()`, skip the PATCH call if the draft equals `""` AND the original value was `"Not found"`. Only PATCH when `draft !== ""` or when the original was a real value being changed.

### Pitfall 7: Tailwind v4 vs v3 shadcn/ui Init
**What goes wrong:** Running `npx shadcn-ui@latest init` (old package name) or `npx shadcn@2.3.0` against a Tailwind v4 project produces broken configuration.
**Why it happens:** shadcn/ui changed the CLI package name from `shadcn-ui` to `shadcn`. The v4-compatible CLI is `npx shadcn@latest`.
**How to avoid:** Always use `npx shadcn@latest init` for Tailwind v4. Verify `tailwindcss` version before running init.

---

## Code Examples

### API layer (verified shape from source inspection)
```typescript
// src/lib/api.ts — typed wrappers matching actual backend responses
export interface JobResponse {
  job_id: string;
  status: 'pending' | 'processing' | 'classifying' | 'extracting' | 'complete' | 'error' | string;
  doc_type: string | null;
  extraction_result: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
}

export const api = {
  async postExtract(file: File): Promise<{ job_id: string; status: string }> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/extract', { method: 'POST', body: form });
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async getJob(jobId: string): Promise<JobResponse> {
    // Always returns HTTP 200 — check .status field for error state
    const res = await fetch(`/api/jobs/${jobId}`);
    return res.json();
  },

  async patchDocType(jobId: string, docType: string): Promise<void> {
    await fetch(`/api/jobs/${jobId}/doc_type`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_type: docType }),
    });
    // Returns 202 — caller must restart polling
  },

  async patchFields(jobId: string, fields: Record<string, unknown>): Promise<JobResponse> {
    const res = await fetch(`/api/jobs/${jobId}/fields`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields }),
    });
    return res.json(); // Returns full updated JobResponse
  },

  exportUrl(jobId: string): string {
    return `/api/jobs/${jobId}/export`;
    // Use as href or window.location — returns CSV with Content-Disposition: attachment
  },
};
```

### Error code → human readable message map
```typescript
// src/lib/errorMessages.ts — sourced from src/core/errors.py
export const ERROR_MESSAGES: Record<string, string> = {
  DOCLING_TIMEOUT: 'The document took too long to parse. Try a smaller file.',
  DOCLING_PARSE_ERROR: 'The document could not be read. Check the file is not corrupted.',
  GEMINI_ERROR: 'Gemini failed to process this document. Try uploading again.',
  INVALID_FILE_TYPE: 'Unsupported file type. Supported: PDF, XLSX, XLS, PNG, JPG, HTML.',
  FILE_TOO_LARGE: 'File is too large to process.',
};

export function getErrorMessage(code: string | null): string {
  if (!code) return 'An unexpected error occurred.';
  return ERROR_MESSAGES[code] ?? `Processing failed (${code}).`;
}
```

### Status text mapping for progress indicator
```typescript
// src/lib/statusText.ts
export const STATUS_TEXT: Record<string, string> = {
  pending: 'Uploading...',
  processing: 'Parsing document...',
  classifying: 'Classifying document...',
  extracting: 'Extracting fields...',
};

export function getStatusText(status: string): string {
  return STATUS_TEXT[status] ?? 'Processing...';
}
```

### Document types with line items
```typescript
// src/lib/docTypes.ts — derived from REQUIREMENTS.md EXT-06/07/08
export const DOC_TYPES_WITH_LINE_ITEMS = new Set([
  'purchase_order',
  'invoice',
  'supplier_comparison',
]);

export const VALID_DOC_TYPES = [
  'purchase_order',
  'tender_rfq',
  'quotation',
  'invoice',
  'supplier_comparison',
] as const;
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `shadcn-ui` npm CLI package | `shadcn` CLI package | 2024 | Old `npx shadcn-ui@latest` breaks; use `npx shadcn@latest` |
| Tailwind v3 PostCSS plugin | Tailwind v4 `@tailwindcss/vite` plugin | Tailwind v4 (2025) | No PostCSS config needed; direct Vite plugin |
| `@tailwindcss/forms` reset | Tailwind v4 built-in form reset | v4 | Fewer required plugins |
| CRA (create-react-app) | Vite | 2023-2024 | CRA is deprecated; Vite is the standard scaffolding tool |

**Deprecated/outdated:**
- `npx shadcn-ui@latest`: Old CLI package name — broken, replaced by `npx shadcn@latest`
- `create-react-app`: Officially deprecated — never use
- `@vitejs/plugin-react-swc`: Not needed by default; standard `@vitejs/plugin-react` (Babel) is sufficient unless build speed is critical

---

## Open Questions

1. **exact `extraction_result` structure per doc_type**
   - What we know: `extraction_result` is `Optional[dict]`; header fields are flat keys; line items are under a key (likely `line_items` or `items`)
   - What's unclear: The exact key names for line item arrays per doc type (e.g., is it `line_items` for purchase_order and `items` for invoice?)
   - Recommendation: Before writing `ReviewTable.tsx`, read `src/extraction/schemas/` to confirm the exact dict keys for each doc type's line items field. This determines the conditional rendering logic and the PATCH shape.

2. **doc_type override — when is the dropdown available?**
   - What we know: The endpoint `PATCH /jobs/{id}/doc_type` requires the job to exist; doc_type is available from polling once classification completes
   - What's unclear: Whether to show the dropdown during the `classifying` phase (when `doc_type` is null) or only after classification is complete
   - Recommendation: Show the dropdown only when `doc_type` is non-null (i.e., after classification). This avoids an empty dropdown and aligns with the poll loop already handling the classifying→extracting transition automatically.

3. **field label mapping**
   - What we know: `extraction_result` keys are snake_case strings (e.g., `invoice_number`, `total_amount`)
   - What's unclear: Whether a central label registry exists in the backend schemas
   - Recommendation: Build `src/lib/fieldLabels.ts` as a manual mapping during Wave 0 by reading all Pydantic schema files. Use a fallback of `key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())` for any unlisted key.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) + Vitest (new, for frontend) |
| Config file | `frontend/vite.config.ts` (Vitest shares Vite config) |
| Quick run command | `cd frontend && npx vitest run --reporter=verbose` |
| Full suite command | `pytest tests/ && cd frontend && npx vitest run` |

**Note:** The existing test suite is pytest-based (Python). Frontend tests are a new concern. Vitest is the standard choice for Vite projects — it reuses the same config, transforms, and module resolution as the build.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REV-01 | Review table renders all fields from `extraction_result` | unit (component) | `npx vitest run src/components/ReviewTable.test.tsx` | ❌ Wave 0 |
| REV-02 | Inline edit cell sends PATCH on blur/Enter | unit (component) | `npx vitest run src/components/EditableCell.test.tsx` | ❌ Wave 0 |
| REV-03 | "Not found" cells render with muted italic style | unit (component) | `npx vitest run src/components/EditableCell.test.tsx` | ❌ Wave 0 |
| REV-04 | Progress view shows correct status text per poll response | unit (component) | `npx vitest run src/components/ProgressView.test.tsx` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run --reporter=verbose`
- **Per wave merge:** `pytest tests/ && cd frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/src/components/ReviewTable.test.tsx` — covers REV-01
- [ ] `frontend/src/components/EditableCell.test.tsx` — covers REV-02, REV-03
- [ ] `frontend/src/components/ProgressView.test.tsx` — covers REV-04
- [ ] Framework install: `cd frontend && npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom` — Vitest + React Testing Library not yet installed (frontend scaffold doesn't exist yet)
- [ ] `frontend/src/test-setup.ts` — `@testing-library/jest-dom` matchers config

---

## Sources

### Primary (HIGH confidence)
- `src/api/models.py` — JobResponse shape, PatchFieldsRequest, DocTypeOverrideRequest (direct code inspection)
- `src/api/routes/extract.py` — POST /extract, file upload, job creation
- `src/api/routes/jobs.py` — GET /jobs/{id}, status polling, `_serialize_extraction` (None → "Not found")
- `src/api/routes/patch.py` — PATCH /jobs/{id}/fields, deep merge, returns full JobResponse
- `src/api/routes/export.py` — GET /jobs/{id}/export, CSV bytes response
- `src/api/routes/doc_type.py` — PATCH /jobs/{id}/doc_type, 202 response, re-extraction trigger
- `src/core/errors.py` — Error code constants
- `npm view` output — Verified package versions as of 2026-03-23

### Secondary (MEDIUM confidence)
- [shadcn/ui official Vite installation](https://ui.shadcn.com/docs/installation/vite) — init steps, Tailwind v4 notes
- [Vite server.proxy official docs](https://vite.dev/config/server-options) — proxy config shape
- [FastAPI static files discussion](https://github.com/fastapi/fastapi/discussions/5134) — SPAStaticFiles pattern for SPA catch-all
- [react-dropzone official docs](https://react-dropzone.js.org/) — hook API, accept prop, pitfalls

### Tertiary (LOW confidence)
- WebSearch results on FastAPI + React production serving patterns — multiple sources agree on SPAStaticFiles / catch-all approach

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified via `npm view` 2026-03-23
- API integration: HIGH — sourced directly from existing backend Python files
- Architecture patterns: HIGH — derived from locked user decisions and backend contracts
- Pitfalls: MEDIUM — combination of backend code inspection + verified web sources
- Tailwind v4 / shadcn CLI: MEDIUM — web search verified against official shadcn docs URL

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable ecosystem; shadcn/ui updates frequently but not breaking)
