# NaturalQuery Frontend Redesign — Design Spec
**Date:** 2026-03-20
**Scope:** Surgical component-level refinement (no structural changes)
**Direction:** AI Conversational (inspired by Perplexity, Claude.ai)

---

## Overview

The current frontend is functionally solid but visually generic. This redesign elevates every component individually to create a cohesive AI-first identity without changing the underlying layout (sidebar + main area + chat bar).

**Pain points addressed:**
- Empty state is too generic (A)
- Results lack visual hierarchy (C)
- No distinct visual identity (E)

**New elements added:**
- Typing animation on loading
- Syntax highlight on SQL
- AI avatar/badge on responses
- Timestamps and metadata on history items

---

## Section 1 — Visual Identity

**Color system:** The existing indigo accent (`#6366f1`) is retained for UI chrome. A second accent, cyan (`#06b6d4`), is introduced exclusively for AI-origin elements — responses, badges, highlights, and hover states on example cards. This two-tone system creates an immediate visual distinction: indigo = product/UI, cyan = AI intelligence.

**AI Avatar Badge:** A small hexagonal icon with a cyan→indigo gradient used consistently to mark AI-generated content. Appears before response text and in the loading state. Implemented as a reusable React component `<AIBadge />`.

**Typography:** No font change (Inter). Result explanation text gets `font-weight: 500` and `letter-spacing: -0.2px` for slightly more authority. No other typography changes.

**New CSS variables added:**
```css
--accent-ai: #06b6d4;
--accent-ai-dim: rgba(6, 182, 212, 0.10);
--accent-ai-glow: rgba(6, 182, 212, 0.20);
```

---

## Section 2 — Empty State

Replaces the current generic database icon + static text with an interactive welcome screen.

**Structure:**
1. `<AIBadge />` centered at top
2. Heading: "What do you want to know?" (22px, weight 600)
3. Subtitle: "Ask in plain English. I'll handle the SQL." (muted)
4. 2×3 grid of clickable query example cards

**Query example cards (6 total):**

| Icon | Question | Category |
|------|----------|----------|
| 📦 | Top 5 best-selling products | Products |
| 📦 | Products with low stock | Products |
| 💰 | Monthly revenue this year | Revenue |
| 💰 | Revenue by category | Revenue |
| 👤 | Top 10 customers by spend | Customers |
| 👤 | New customers last month | Customers |

**Interaction:** Clicking a card sets the chat input value and immediately submits the query (calls `handleQuery` directly). Cards have a subtle cyan border on hover.

**Component:** Extracted into `<EmptyState onSelect={handleQuery} />` in `src/components/Chat/EmptyState.tsx`.

---

## Section 3 — Loading State

Replaces the static "Thinking..." text with a 3-phase animated sequence.

**Phases (cycle every 1500ms):**
1. "Analyzing your question..."
2. "Generating SQL query..."
3. "Fetching results..."

**Visual:** `<AIBadge />` on the left + phase text + animated ellipsis (`...` pulsing via CSS keyframes). Fade transition between phases using CSS `opacity` animation.

**Implementation:** React `useState` + `useEffect` with `setInterval` (cleared on unmount). Pure CSS animation — no external library.

**Component:** `<LoadingState />` in `src/components/Chat/LoadingState.tsx`.

---

## Section 4 — Results Area

### 4a — AI Response Card
The explanation box is replaced by an AI response card:
- `<AIBadge />` + "NaturalQuery AI" label above the text
- Left border: 3px solid `--accent-ai` (cyan)
- Background: `--accent-ai-dim`
- Replaces `.explanation-box` with `.ai-response-card` CSS class

### 4b — Result Metadata Bar
A horizontal bar between the AI card and the data, containing:
- Row count badge: `↗ {n} rows` (styled with cyan text)
- Execution time: `~0.3s` (muted, omitted if unavailable — backend doesn't currently send this, so show only row count)
- "Copy SQL" button on the right (copies `sql_generated` to clipboard via `navigator.clipboard`)

### 4c — Chart before Table
When `chart_config` is present, `<ChartDisplay>` renders before `<ResultsTable>`. The chart is the insight; the table is the detail. Order change only — no component modifications.

### 4d — SQL Syntax Highlight
**Library:** `highlight.js` (specifically `highlight.js/lib/core` + `highlight.js/lib/languages/sql` + one dark theme). Chosen for minimal bundle size (~10kb gzipped for core + one language).

**Implementation:** `<SqlBlock sql={sql_generated} />` component in `src/components/Results/SqlBlock.tsx`. Uses `useEffect` to run `hljs.highlightElement()` on a `<code>` ref after mount. Replaces the current `<pre className="sql-block">` inline in `DashboardPage`.

**Install:** `npm install highlight.js`

---

## Section 5 — History Sidebar

Each history item gains two lines instead of one:
- **Line 1:** Question text (truncated, same as before)
- **Line 2:** Relative timestamp (`2 min ago`, `Yesterday`, date if older) + row count badge (`12 rows`) if available

Timestamp formatting: plain JS `Intl.RelativeTimeFormat` — no date library needed.

The sidebar header changes from just "HISTORY" to "History · {n} queries" where n is the total count.

If `chart_config` is present on a history item, a small chart icon (SVG) appears at the right edge of the item on hover.

**No backend changes required.** All data (`row_count`, `created_at`) is already returned by the history API endpoint.

---

## Files Changed

| File | Change |
|------|--------|
| `src/App.css` | Add CSS variables, new classes (`.ai-response-card`, `.query-card`, `.result-meta-bar`, `.loading-phase`) |
| `src/pages/DashboardPage.tsx` | Wire up new components, reorder chart/table |
| `src/components/Chat/EmptyState.tsx` | New component |
| `src/components/Chat/LoadingState.tsx` | New component |
| `src/components/Layout/AIBadge.tsx` | New reusable component |
| `src/components/Results/SqlBlock.tsx` | New component wrapping highlight.js |
| `src/components/Sidebar/QueryHistory.tsx` | Add timestamp + row count metadata |
| `package.json` / `frontend/package.json` | Add `highlight.js` dependency |

---

## Out of Scope

- No layout structural changes (sidebar width, header height, overall grid)
- No backend changes
- No new API endpoints
- No routing changes
- No mobile/responsive work
- No dark/light theme toggle

---

## Dependencies

| Package | Version | Reason |
|---------|---------|--------|
| `highlight.js` | latest | SQL syntax highlighting |

No other new dependencies.
