# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate the NaturalQuery frontend to an AI-first visual identity with a new empty state, animated loading, AI response card, syntax-highlighted SQL, and enriched history sidebar — without changing layout structure or backend.

**Architecture:** Component-level surgical changes only. Five new components are extracted from inline JSX into dedicated files. `DashboardPage.tsx` is rewired to use them in the correct render order. CSS variables for the cyan AI accent are added to `App.css`.

**Tech Stack:** React 19 + TypeScript, Vite 8, highlight.js (new), existing CSS custom properties pattern

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/package.json` | Modify | Add `highlight.js` dependency |
| `frontend/src/App.css` | Modify | Add `--accent-ai` variables + new component classes |
| `frontend/src/components/UI/AIBadge.tsx` | **Create** | Reusable hexagonal AI badge (cyan→indigo gradient) |
| `frontend/src/components/Chat/EmptyState.tsx` | **Create** | Welcome screen with 6 clickable query cards |
| `frontend/src/components/Chat/LoadingState.tsx` | **Create** | 3-phase animated loading sequence |
| `frontend/src/components/Results/ResultMetaBar.tsx` | **Create** | Row count badge + Copy SQL button |
| `frontend/src/components/Results/SqlBlock.tsx` | **Create** | `<details>` wrapper with highlight.js-highlighted SQL |
| `frontend/src/pages/DashboardPage.tsx` | Modify | Wire all new components, reorder chart before table |
| `frontend/src/components/Sidebar/QueryHistory.tsx` | Modify | 2-line items (question + timestamp/rowcount), header count |

---

## Chunk 1: Foundation — highlight.js + CSS variables + AIBadge

### Task 1: Install highlight.js

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install the dependency**

Run inside `frontend/`:
```bash
npm install highlight.js
```

Expected output: `added 1 package` (or similar), no errors.

- [ ] **Step 2: Verify types are included**

```bash
ls node_modules/highlight.js/types/index.d.ts
```

Expected: file exists. highlight.js ships its own types — no `@types/highlight.js` needed.

---

### Task 2: Add CSS variables and new component classes to App.css

**Files:**
- Modify: `frontend/src/App.css`

- [ ] **Step 1: Add the three AI accent CSS variables to the `:root` block**

In `App.css`, append to the existing `:root` block (after line 11, `--accent-glow`):

```css
  --accent-ai: #06b6d4;
  --accent-ai-dim: rgba(6, 182, 212, 0.10);
  --accent-ai-glow: rgba(6, 182, 212, 0.20);
```

- [ ] **Step 2: Replace the `.empty-state` block and add all new component classes**

Replace everything from `.empty-state {` through the end of `/* ── Loading ── */` section (lines 350–567) with the following (keeping the new `.loading-text` animation at the end):

```css
/* ── Empty state ───────────────────────────────────────────────────────────── */

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
}

.empty-state-heading {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.3px;
  margin-top: 8px;
}

.empty-state-subtitle {
  font-size: 14px;
  color: var(--text-muted);
}

.query-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 8px;
  width: 100%;
  max-width: 520px;
}

.query-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 12px 14px;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  transition: border-color 0.15s, background 0.15s;
  text-align: left;
}

.query-card:hover {
  border-color: var(--accent-ai);
  background: var(--bg-hover);
}

.query-card-icon {
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

.query-card-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* ── AI Badge ──────────────────────────────────────────────────────────────── */

.ai-badge {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

/* ── Loading state ─────────────────────────────────────────────────────────── */

.loading-phase {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}

.loading-phase-text {
  color: var(--text-secondary);
  font-size: 14px;
}

@keyframes ellipsis-pulse {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 1; }
}

.loading-dots span {
  animation: ellipsis-pulse 1.2s ease-in-out infinite;
  color: var(--accent-ai);
  font-weight: 700;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

/* ── AI Response Card ──────────────────────────────────────────────────────── */

.ai-response-card {
  background: var(--accent-ai-dim);
  border: 1px solid rgba(6, 182, 212, 0.18);
  border-left: 3px solid var(--accent-ai);
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-response-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--accent-ai);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.ai-response-text {
  line-height: 1.65;
  color: #cbd5e1;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.2px;
}

/* ── Result meta bar ───────────────────────────────────────────────────────── */

.result-meta-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.row-badge {
  background: var(--accent-ai-dim);
  color: var(--accent-ai);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-radius: 5px;
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.copy-sql-btn {
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: 5px;
  padding: 3px 10px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.copy-sql-btn:hover {
  color: var(--text-secondary);
  border-color: var(--border-default);
}

/* ── SQL block ─────────────────────────────────────────────────────────────── */

.sql-toggle { margin-bottom: 16px; }

.sql-toggle summary {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 12px;
  user-select: none;
  font-weight: 500;
  list-style: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.sql-toggle summary::before {
  content: '▸';
  font-size: 10px;
  transition: transform 0.15s;
}

details.sql-toggle[open] > summary::before {
  transform: rotate(90deg);
}

.sql-toggle summary:hover { color: var(--text-secondary); }

.sql-block {
  background: #050810;
  border: 1px solid var(--border-default);
  border-left: 2px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  padding: 14px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 8px;
  white-space: pre-wrap;
  line-height: 1.65;
}

/* highlight.js overrides — keep our bg, not hljs default */
.sql-block.hljs { background: #050810; }

/* ── Results (unchanged) ───────────────────────────────────────────────────── */

.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.table-wrap {
  overflow-x: auto;
  margin-bottom: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-default);
}

table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead { background: var(--bg-elevated); }

th {
  color: var(--text-muted);
  text-align: left;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-default);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

td {
  padding: 9px 14px;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-primary);
}

tr:last-child td { border-bottom: none; }
tr:nth-child(even) td { background: rgba(255, 255, 255, 0.015); }
tr:hover td { background: var(--bg-hover); }

.chart-wrap {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  max-height: 340px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

/* ── Chat bar ──────────────────────────────────────────────────────────────── */

.chat-bar {
  border-top: 1px solid var(--border-default);
  padding: 14px 20px;
  display: flex;
  gap: 10px;
  background: linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-elevated) 100%);
  flex-shrink: 0;
}

.chat-bar input {
  flex: 1;
  background: var(--bg-base);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 11px 16px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.chat-bar input::placeholder { color: var(--text-muted); }

.chat-bar input:focus {
  border-color: var(--accent);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25), 0 0 0 3px var(--accent-glow);
}

.chat-bar button {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 8px;
  padding: 0 22px;
  color: white;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: opacity 0.2s, box-shadow 0.2s, transform 0.1s;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
  white-space: nowrap;
}

.chat-bar button:hover {
  opacity: 0.92;
  box-shadow: 0 4px 22px rgba(99, 102, 241, 0.52);
}

.chat-bar button:active { transform: scale(0.98); }

.chat-bar button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

/* ── Loading (legacy pulse for fallback) ───────────────────────────────────── */

@keyframes pulse-shimmer {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.9; }
}

.loading-text {
  color: var(--text-muted);
  font-size: 13px;
  padding: 8px 0;
  animation: pulse-shimmer 1.6s ease-in-out infinite;
}
```

- [ ] **Step 3: Start dev server and verify no CSS errors**

```bash
cd frontend && npm run dev
```

Expected: Vite starts without errors. Browser shows the app normally (login page).

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/App.css
git commit -m "feat: add highlight.js, AI accent CSS variables and component classes"
```

---

### Task 3: Create AIBadge component

**Files:**
- Create: `frontend/src/components/UI/AIBadge.tsx`

> Note: Create the `UI/` directory if it doesn't exist yet.

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/UI/AIBadge.tsx
export function AIBadge() {
  return (
    <svg
      className="ai-badge"
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="NaturalQuery AI"
    >
      <defs>
        <linearGradient id="ai-badge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06b6d4" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      {/* Hexagon path (flat-top orientation) */}
      <path
        d="M14 2L25.26 8.5V21.5L14 28L2.74 21.5V8.5L14 2Z"
        fill="url(#ai-badge-grad)"
        opacity="0.15"
      />
      <path
        d="M14 2L25.26 8.5V21.5L14 28L2.74 21.5V8.5L14 2Z"
        stroke="url(#ai-badge-grad)"
        strokeWidth="1.5"
        fill="none"
      />
      {/* Spark / lightning bolt icon inside */}
      <path
        d="M15.5 8L11 15h3.5L12.5 20L18 13h-3.5L15.5 8Z"
        fill="url(#ai-badge-grad)"
      />
    </svg>
  )
}
```

- [ ] **Step 2: Verify in browser**

Import `AIBadge` temporarily into `DashboardPage.tsx` and drop `<AIBadge />` anywhere visible. Confirm it renders a small hexagonal icon. Remove the temporary import after verifying.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/UI/AIBadge.tsx
git commit -m "feat: add AIBadge reusable hexagonal icon component"
```

---

## Chunk 2: EmptyState + LoadingState

### Task 4: Create EmptyState component

**Files:**
- Create: `frontend/src/components/Chat/EmptyState.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/Chat/EmptyState.tsx
import { AIBadge } from '../UI/AIBadge'

interface Props {
  onSelect: (question: string) => void
}

const QUERY_CARDS = [
  { icon: '📦', question: 'Top 5 best-selling products' },
  { icon: '📦', question: 'Products with low stock' },
  { icon: '💰', question: 'Monthly revenue this year' },
  { icon: '💰', question: 'Revenue by category' },
  { icon: '👤', question: 'Top 10 customers by spend' },
  { icon: '👤', question: 'New customers last month' },
]

export function EmptyState({ onSelect }: Props) {
  return (
    <div className="empty-state">
      <AIBadge />
      <p className="empty-state-heading">What do you want to know?</p>
      <p className="empty-state-subtitle">Ask in plain English. I'll handle the SQL.</p>
      <div className="query-cards-grid">
        {QUERY_CARDS.map(({ icon, question }) => (
          <button
            key={question}
            className="query-card"
            onClick={() => onSelect(question)}
          >
            <span className="query-card-icon">{icon}</span>
            <span className="query-card-text">{question}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire into DashboardPage temporarily to verify**

In `DashboardPage.tsx`, replace the empty-state `<div>` block with:
```tsx
<EmptyState onSelect={handleQuery} />
```
And add the import:
```tsx
import { EmptyState } from '../components/Chat/EmptyState'
```

Open the app while logged in and not having submitted a query. Verify:
- AIBadge renders at top
- "What do you want to know?" heading appears
- 6 cards in a 2-column grid
- Clicking a card triggers the query (check network tab or loading state)
- Cards have cyan border on hover

Leave the wiring in place (this is the final state for this component in `DashboardPage`).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Chat/EmptyState.tsx frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add EmptyState component with interactive query cards"
```

---

### Task 5: Create LoadingState component

**Files:**
- Create: `frontend/src/components/Chat/LoadingState.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/Chat/LoadingState.tsx
import { useState, useEffect } from 'react'
import { AIBadge } from '../UI/AIBadge'

const PHASES = [
  'Analyzing your question',
  'Generating SQL query',
  'Fetching results',
]

export function LoadingState() {
  const [phaseIndex, setPhaseIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setPhaseIndex(i => (i + 1) % PHASES.length)
    }, 1500)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="loading-phase">
      <AIBadge />
      <span className="loading-phase-text">{PHASES[phaseIndex]}</span>
      <span className="loading-dots">
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </span>
    </div>
  )
}
```

- [ ] **Step 2: Wire into DashboardPage temporarily to verify**

In `DashboardPage.tsx`, replace `{loading && <p className="loading-text">Thinking...</p>}` with:
```tsx
{loading && <LoadingState />}
```
And add the import:
```tsx
import { LoadingState } from '../components/Chat/LoadingState'
```

Submit a query and verify:
- The 3 phases cycle every ~1.5 seconds
- The animated dots pulse
- The loading indicator disappears when results arrive

Leave the wiring in place.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Chat/LoadingState.tsx frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add LoadingState component with 3-phase animation"
```

---

## Chunk 3: ResultMetaBar + SqlBlock

### Task 6: Create ResultMetaBar component

**Files:**
- Create: `frontend/src/components/Results/ResultMetaBar.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/Results/ResultMetaBar.tsx
interface Props {
  rowCount: number
  sql: string
}

export function ResultMetaBar({ rowCount, sql }: Props) {
  function handleCopy() {
    navigator.clipboard.writeText(sql).catch(() => {})
  }

  return (
    <div className="result-meta-bar">
      <span className="row-badge">↗ {rowCount} {rowCount === 1 ? 'row' : 'rows'}</span>
      <button className="copy-sql-btn" onClick={handleCopy}>Copy SQL</button>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

Verification is done together with Task 7 — the `ResultMetaBar` and `SqlBlock` are wired into `DashboardPage.tsx` in the same commit (Task 7 Step 3).

---

### Task 7: Create SqlBlock component with highlight.js

**Files:**
- Create: `frontend/src/components/Results/SqlBlock.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/Results/SqlBlock.tsx
import { useEffect, useRef } from 'react'
import hljs from 'highlight.js/lib/core'
import sql from 'highlight.js/lib/languages/sql'
import 'highlight.js/styles/atom-one-dark.css'

hljs.registerLanguage('sql', sql)

interface Props {
  sql: string
}

export function SqlBlock({ sql: sqlText }: Props) {
  const codeRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (codeRef.current && !codeRef.current.dataset.highlighted) {
      hljs.highlightElement(codeRef.current)
    }
  }, [sqlText])

  return (
    <details className="sql-toggle">
      <summary>View generated SQL</summary>
      <pre className="sql-block">
        <code ref={codeRef} className="language-sql">
          {sqlText}
        </code>
      </pre>
    </details>
  )
}
```

- [ ] **Step 2: Wire into DashboardPage temporarily to verify**

Replace the existing `<details className="sql-toggle">` block in `DashboardPage.tsx` with:
```tsx
<SqlBlock sql={result.sql_generated} />
```
And add:
```tsx
import { SqlBlock } from '../components/Results/SqlBlock'
```

Submit a query and expand "View generated SQL". Verify:
- SQL keywords are highlighted (SELECT, FROM, WHERE, etc. in different colors)
- Background stays dark (atom-one-dark theme)
- The collapsible toggle still works
- No console errors about double-invocation in React StrictMode

Leave the wiring in place.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Results/ResultMetaBar.tsx frontend/src/components/Results/SqlBlock.tsx frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add ResultMetaBar and SqlBlock with highlight.js syntax highlighting"
```

---

## Chunk 4: DashboardPage wiring + QueryHistory

### Task 8: Final DashboardPage wiring

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`

This task locks in the final render order and adds the `AIResponseCard` inline (no separate component — it's simple enough to be inline).

- [ ] **Step 1: Rewrite DashboardPage.tsx to final state**

Full file content:

```tsx
import { useState, useEffect } from 'react'
import { Header } from '../components/Layout/Header'
import { QueryHistory as QueryHistorySidebar } from '../components/Sidebar/QueryHistory'
import { ChatInput } from '../components/Chat/ChatInput'
import { ResultsTable } from '../components/Results/ResultsTable'
import { ChartDisplay } from '../components/Results/ChartDisplay'
import { EmptyState } from '../components/Chat/EmptyState'
import { LoadingState } from '../components/Chat/LoadingState'
import { ResultMetaBar } from '../components/Results/ResultMetaBar'
import { SqlBlock } from '../components/Results/SqlBlock'
import { AIBadge } from '../components/UI/AIBadge'
import { postQuery, getHistory } from '../api/client'
import type { QueryResponse, HistoryItem } from '../types'

interface Props {
  username: string
  onLogout: () => void
}

export function DashboardPage({ username, onLogout }: Props) {
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getHistory().then(setHistory).catch(() => {})
  }, [])

  async function handleQuery(question: string) {
    setLoading(true)
    setError('')
    try {
      const data = await postQuery(question)
      setResult(data)
      const h = await getHistory()
      setHistory(h)
      if (h.length > 0) setActiveId(h[0].id)
    } catch (err: any) {
      const errors = err?.response?.data?.errors
      if (errors?.question) setError(errors.question[0])
      else if (errors?.query) setError(errors.query[0])
      else setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleHistorySelect(item: HistoryItem) {
    setActiveId(item.id)
    setResult({
      question: item.question,
      sql_generated: item.sql_generated,
      explanation: item.explanation,
      results: item.results,
      chart_config: item.chart_config,
      row_count: item.row_count,
    })
  }

  return (
    <div className="dashboard">
      <Header username={username} onLogout={onLogout} />
      <div className="dashboard-body">
        <QueryHistorySidebar items={history} activeId={activeId} onSelect={handleHistorySelect} />
        <div className="main-area">
          <div className="results-area">
            {!result && !loading && (
              <EmptyState onSelect={handleQuery} />
            )}
            {loading && <LoadingState />}
            {error && <p className="error-msg" style={{ padding: '8px 0' }}>{error}</p>}
            {result && !loading && (
              <>
                {/* 1. AI Response Card */}
                <div className="ai-response-card">
                  <div className="ai-response-header">
                    <AIBadge />
                    NaturalQuery AI
                  </div>
                  <p className="ai-response-text">{result.explanation}</p>
                </div>

                {/* 2. Result Meta Bar */}
                <ResultMetaBar rowCount={result.row_count} sql={result.sql_generated} />

                {/* 3. Chart (before table — insight first) */}
                {result.chart_config && (
                  <ChartDisplay config={result.chart_config} results={result.results} />
                )}

                {/* 4. Table */}
                <ResultsTable results={result.results} />

                {/* 5. SQL Block */}
                <SqlBlock sql={result.sql_generated} />
              </>
            )}
          </div>
          <ChatInput onSubmit={handleQuery} disabled={loading} />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify the full flow**

Submit a query with chart data (e.g. "Monthly revenue this year"). Check:
1. Empty state shows on fresh load ✓
2. Loading cycles through 3 phases ✓
3. AI Response Card (cyan left border, AIBadge + "NaturalQuery AI" label) ✓
4. Result Meta Bar (row count badge + Copy SQL button) ✓
5. **Chart renders BEFORE the table** ✓
6. SQL block is collapsible with syntax highlighting ✓

Also submit a query without chart data and verify chart is absent but everything else works.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx
git commit -m "feat: wire all redesigned components into DashboardPage"
```

---

### Task 9: Update QueryHistory sidebar

**Files:**
- Modify: `frontend/src/components/Sidebar/QueryHistory.tsx`
- Modify: `frontend/src/App.css` (`.history-item` and `.sidebar h3`)

- [ ] **Step 1: Add CSS for 2-line history items**

In `App.css`, find and update the `.history-item` rule. Replace `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;` with a flex-column layout:

Find this block:
```css
.history-item {
  position: relative;
  padding: 8px 10px 8px 18px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s, color 0.15s;
}
```

Replace with:
```css
.history-item {
  position: relative;
  padding: 8px 10px 8px 18px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: background 0.15s, color 0.15s;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-item-question {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
}

.history-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
}

.history-item-rows {
  color: var(--accent-ai);
  font-weight: 600;
}

.history-chart-icon {
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.15s;
  color: var(--accent-ai);
}

.history-item:hover .history-chart-icon {
  opacity: 1;
}
```

- [ ] **Step 2: Update QueryHistory.tsx**

```tsx
// frontend/src/components/Sidebar/QueryHistory.tsx
import type { HistoryItem } from '../../types'

interface Props {
  items: HistoryItem[]
  activeId: number | null
  onSelect: (item: HistoryItem) => void
}

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days = Math.floor(diff / 86_400_000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  if (hours < 24) return `${hours}h ago`
  if (days === 1) return 'Yesterday'

  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(
    new Date(isoString)
  )
}

// Chart icon SVG (inline, 12px)
function ChartIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <rect x="1" y="7" width="2" height="4" />
      <rect x="5" y="4" width="2" height="7" />
      <rect x="9" y="1" width="2" height="10" />
    </svg>
  )
}

export function QueryHistory({ items, activeId, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <h3>History · {items.length} {items.length === 1 ? 'query' : 'queries'}</h3>
      {items.length === 0 && (
        <p style={{ color: '#374151', fontSize: 12, marginTop: 8 }}>No queries yet</p>
      )}
      {items.map(item => (
        <div
          key={item.id}
          className={`history-item${activeId === item.id ? ' active' : ''}`}
          onClick={() => onSelect(item)}
          title={item.question}
        >
          <span className="history-item-question">{item.question}</span>
          <span className="history-item-meta">
            <span>{formatRelativeTime(item.created_at)}</span>
            {item.row_count != null && (
              <span className="history-item-rows">{item.row_count} rows</span>
            )}
            {item.chart_config && (
              <span className="history-chart-icon"><ChartIcon /></span>
            )}
          </span>
        </div>
      ))}
    </aside>
  )
}
```

- [ ] **Step 3: Verify in browser**

After running a few queries, check the sidebar:
- Header shows "History · N queries"
- Each item shows question (truncated) + metadata line below
- Timestamp shows relative format ("2 min ago", etc.)
- Row count is cyan
- If a query has a chart, hovering the item reveals the chart icon

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Sidebar/QueryHistory.tsx frontend/src/App.css
git commit -m "feat: enrich history sidebar with timestamps, row count and chart indicator"
```

---

## Final Verification Checklist

- [ ] `npm run build` inside `frontend/` completes without TypeScript errors
- [ ] Empty state: AIBadge + heading + subtitle + 6 cards visible; clicking a card triggers query
- [ ] Loading: phases cycle (not "Thinking..."); cleanup fires on unmount (no console warnings)
- [ ] AI Response Card: cyan left border, AIBadge + "NaturalQuery AI" label, explanation text
- [ ] Result Meta Bar: `↗ N rows` in cyan; "Copy SQL" copies to clipboard
- [ ] Chart renders before table when `chart_config` is present
- [ ] SQL block: collapsible toggle works; keywords syntax-highlighted; background stays dark
- [ ] History sidebar: header shows count; items are 2-line; timestamps are relative; chart icon appears on hover
- [ ] No new console errors in browser

- [ ] **Final commit (if any CSS/copy tweaks were needed)**

```bash
git add -p
git commit -m "fix: post-integration visual tweaks"
```
