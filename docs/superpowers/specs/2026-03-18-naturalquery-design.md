# NaturalQuery — Design Spec

**Date:** 2026-03-18
**Status:** Approved

---

## Overview

NaturalQuery is a full-stack web application that lets authenticated users query a pre-loaded e-commerce demo database using plain English or Portuguese. Claude (Anthropic API) converts the question into SQL via tool use, executes it against a read-only SQLite database, and returns the results alongside a natural language explanation and an auto-selected chart.

---

## Architecture

```
Frontend (React/TS)  ──►  Backend (Django/DRF)  ──►  Claude API (Tool Use)
                               │                           │
                               ▼                           ▼
                         app.sqlite                  execute_sql tool
                      (users, history)          ──►  demo.sqlite (e-commerce)
```

### Query Flow

1. Authenticated user submits `{"question": "..."}` → `POST /api/query`
2. Backend sends to Claude: e-commerce schema + question + `execute_sql` tool definition
3. Claude generates SQL and calls `execute_sql` — backend enters the **tool use loop**
4. Backend validates SQL (SELECT-only), executes against `demo.sqlite`, returns rows to Claude
5. Claude writes a natural language explanation
6. Backend detects best chart type from result shape, builds `chart_config`
7. Response returned: `{sql, results, explanation, chart_config}`
8. Frontend renders: explanation → results table → Chart.js visualization → collapsible SQL
9. Backend saves query to `QueryHistory`

### Two SQLite Databases

- `app.sqlite` — application data: users, auth tokens, query history
- `demo.sqlite` — e-commerce demo data (read-only, pre-seeded)

---

## E-commerce Schema (demo.sqlite)

```sql
customers   (id, name, email, city, state, created_at)
categories  (id, name)
products    (id, name, category_id, price, stock_qty)
orders      (id, customer_id, status, created_at, total)
order_items (id, order_id, product_id, quantity, unit_price)
```

**Seed data:**
- ~200 customers across Brazilian states
- ~50 products in 8 categories
- ~1,000 orders over 2 years
- Order statuses: `pending`, `shipped`, `delivered`, `cancelled`

---

## Backend

**Tech:** Django 5 + Django REST Framework + Token Authentication

### App Structure

```
backend/
├── core/          # settings, urls, wsgi
├── accounts/      # User model, register, login — Token auth
├── ai_engine/     # Claude integration: tool use loop, prompt builder, schema loader
├── query_runner/  # SQL executor with SELECT-only validation
├── history/       # QueryHistory model, GET /api/history endpoint
└── demo_db/       # demo.sqlite file + seed management command
```

---

## API Endpoints

### Authentication

All protected endpoints require the header:
```
Authorization: Token <token>
```

---

### `POST /api/auth/register`

**Request:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response 201:**
```json
{
  "token": "string",
  "user_id": 1,
  "username": "string"
}
```

**Response 400:**
```json
{
  "errors": {
    "username": ["A user with that username already exists."],
    "password": ["This field is required."]
  }
}
```

---

### `POST /api/auth/login`

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "token": "string",
  "user_id": 1,
  "username": "string"
}
```

**Response 400:**
```json
{
  "errors": {
    "non_field_errors": ["Unable to log in with provided credentials."]
  }
}
```

---

### `POST /api/query` *(requires auth)*

**Request:**
```json
{
  "question": "What are the top 5 best selling products?"
}
```

**Response 200:**
```json
{
  "question": "What are the top 5 best selling products?",
  "sql": "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY total_sold DESC LIMIT 5",
  "explanation": "I found the 5 best-selling products by summing quantities across all order items...",
  "results": {
    "columns": ["name", "total_sold"],
    "rows": [
      ["Wireless Headphones", 342],
      ["USB-C Cable", 289]
    ]
  },
  "chart_config": {
    "type": "bar",
    "x_key": "name",
    "y_key": "total_sold",
    "label": "Total Sold"
  },
  "row_count": 5
}
```

**Response 400 (SQL validation rejected):**
```json
{
  "errors": {
    "query": ["Only SELECT queries are allowed."]
  }
}
```

**Response 422 (Claude could not answer):**
```json
{
  "errors": {
    "question": ["Could not generate a valid query for this question. Please try rephrasing."]
  }
}
```

> `chart_config` is `null` when chart type cannot be determined (fallback to table only).

---

### `GET /api/history` *(requires auth)*

**Response 200:**
```json
{
  "results": [
    {
      "id": 1,
      "question": "What are the top 5 best selling products?",
      "sql_generated": "SELECT ...",
      "explanation": "I found...",
      "chart_config": { "type": "bar", "x_key": "name", "y_key": "total_sold", "label": "Total Sold" },
      "row_count": 5,
      "created_at": "2026-03-18T14:30:00Z"
    }
  ]
}
```

Ordered by `created_at` descending. No pagination for MVP (history capped at last 50 entries per user).

**History sidebar click behavior:** clicking a history item re-populates the results area with the stored `explanation`, `sql_generated`, `chart_config`, and `row_count` from the history record. No re-execution occurs.

---

## Claude Tool Use Loop

**Model:** `claude-sonnet-4-5-20250514`
**Temperature:** 0.0 (deterministic SQL)
**Max tokens:** 1024

The `ai_engine` module drives the following loop:

```
1. Send messages=[{role: user, content: schema + question}] + tools=[execute_sql]
2. Receive response
   a. If stop_reason == "tool_use":
      - Extract SQL from tool input
      - Validate SQL (SELECT-only) → if invalid, raise immediately, return 400
      - Execute SQL against demo.sqlite
      - Append assistant message + tool_result to messages
      - Increment iteration counter
      - If iteration > 3: raise error, return 422
      - Loop back to step 1
   b. If stop_reason == "end_turn":
      - Extract text explanation from response
      - Exit loop
   c. If stop_reason == "max_tokens" or other:
      - Raise error, return 422
3. Return (last_sql_executed, results, explanation)
```

If Claude produces a final `end_turn` response without ever calling `execute_sql` (e.g., the question cannot be answered with the schema), the backend returns 422 with a user-friendly message.

---

## Security

### SQL Validation (SELECT-only)

Applied in `query_runner` before every execution:

```python
import sqlglot

def validate_select_only(sql: str):
    statements = sqlglot.parse(sql)
    if not statements or len(statements) != 1:
        raise ValidationError("Only single SELECT statements are allowed.")
    stmt = statements[0]
    if not isinstance(stmt, sqlglot.exp.Select):
        raise ValidationError("Only SELECT queries are allowed.")
```

Using `sqlglot` (pure Python, no system deps) ensures case-insensitive detection, handles leading comments, and rejects multi-statement strings. If `sqlglot` is not available at deploy time, fallback: normalize to uppercase, strip leading whitespace/comments, assert starts with `SELECT`, assert no `;` in string.

### Row Limit

All queries have `LIMIT 500` appended by `query_runner` if no `LIMIT` clause is present. This caps token usage and prevents UI performance issues.

### Other

- Auth token required on all protected endpoints
- `ANTHROPIC_API_KEY` never included in API responses
- All inputs validated by DRF serializers before processing

---

## Chart Auto-Selection Algorithm

Detection runs on `results.columns` and `results.rows` after SQL execution.

```python
def detect_chart_type(columns: list[str], rows: list[list]) -> dict | None:
    if not rows or len(columns) < 2:
        return None

    # Classify each column as "text", "numeric", or "date"
    # by inspecting Python types of values in first non-null row
    col_types = []
    for i, col in enumerate(columns):
        sample = next((r[i] for r in rows if r[i] is not None), None)
        if isinstance(sample, (int, float)):
            col_types.append("numeric")
        elif isinstance(sample, str):
            name_lower = col.lower()
            if any(k in name_lower for k in ("date", "month", "year", "week", "period", "day")):
                col_types.append("date")
            elif any(k in name_lower for k in ("pct", "percent", "rate", "share")):
                col_types.append("percent")
            else:
                col_types.append("text")
        else:
            col_types.append("text")

    text_cols = [columns[i] for i, t in enumerate(col_types) if t == "text"]
    date_cols = [columns[i] for i, t in enumerate(col_types) if t == "date"]
    num_cols  = [columns[i] for i, t in enumerate(col_types) if t == "numeric"]
    pct_cols  = [columns[i] for i, t in enumerate(col_types) if t == "percent"]

    if date_cols and num_cols:
        return {"type": "line", "x_key": date_cols[0], "y_key": num_cols[0], "label": num_cols[0]}
    if pct_cols and text_cols:
        return {"type": "pie", "x_key": text_cols[0], "y_key": pct_cols[0], "label": pct_cols[0]}
    if text_cols and num_cols:
        return {"type": "bar", "x_key": text_cols[0], "y_key": num_cols[0], "label": num_cols[0]}
    return None  # table only
```

---

## Data Models

### QueryHistory

```python
class QueryHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    sql_generated = models.TextField()
    explanation = models.TextField()
    chart_config = models.JSONField(null=True, blank=True)
    row_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
```

---

## Frontend

**Tech:** React + TypeScript + Chart.js + Axios

### Component Structure

```
frontend/src/
├── components/
│   ├── Auth/          # LoginForm, RegisterForm
│   ├── Sidebar/       # QueryHistory list
│   ├── Chat/          # ChatInput, MessageBubble
│   ├── Results/       # ResultsTable, ChartDisplay
│   └── Layout/        # DashboardLayout, Header
├── pages/
│   ├── LoginPage.tsx
│   └── DashboardPage.tsx
├── api/               # axios client and typed API calls
└── types/             # shared TypeScript interfaces
```

### UI Layout (Dark Theme)

```
┌─────────────────────────────────────────────────────┐
│ NaturalQuery                              [Logout]   │
├──────────────┬──────────────────────────────────────┤
│ History      │  [Natural language explanation]       │
│              │  [Results table]                      │
│ • query 1    │  [Chart.js visualization]             │
│ • query 2    │  [Generated SQL — collapsible]        │
│ • query 3    │                                       │
│              ├──────────────────────────────────────┤
│              │  Ask a question...             [→]    │
└──────────────┴──────────────────────────────────────┘
```

### API Client

All requests include `Authorization: Token <token>` header. Errors are read from `response.errors` (object keyed by field) or `response.errors.non_field_errors` for general errors.

---

## Environment Variables

```
ANTHROPIC_API_KEY     # Claude API key (required)
DJANGO_SECRET_KEY     # Django secret key
DEBUG                 # True locally, False in production
ALLOWED_HOSTS         # Railway domain in production
```

---

## Deployment (Railway — Single Service)

Django serves the React SPA via Whitenoise.

**`Procfile`:**
```
web: cd frontend && npm run build && cd ../backend && python manage.py collectstatic --noinput && gunicorn core.wsgi --bind 0.0.0.0:$PORT
```

**Django settings for static + SPA routing:**
```python
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR.parent / "frontend" / "dist"]  # React build output
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware", ...]

# Catch-all for React SPA routing (in core/urls.py)
# re_path(r"^(?!api/).*", TemplateView.as_view(template_name="index.html"))
TEMPLATES[0]["DIRS"] = [BASE_DIR.parent / "frontend" / "dist"]
```

---

## Project Structure

```
naturalquery/
├── backend/
│   ├── core/
│   ├── accounts/
│   ├── ai_engine/
│   ├── query_runner/
│   ├── history/
│   ├── demo_db/
│   └── manage.py
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   └── superpowers/specs/
├── requirements.txt
├── Procfile
└── README.md
```

---

## Out of Scope

- Dynamic database connection (user-provided credentials)
- Multiple database engine support (PostgreSQL, MySQL)
- Query editing or re-running from history
- Export to CSV/Excel
- Admin panel customization
- Pagination in history endpoint (capped at 50 entries)
