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

1. Authenticated user submits a question → `POST /api/query`
2. Backend sends to Claude: e-commerce schema + question + `execute_sql` tool definition
3. Claude generates SQL and calls the `execute_sql` tool
4. Backend executes SQL against `demo.sqlite` (read-only), returns results to Claude
5. Claude writes a natural language explanation
6. Backend detects best chart type from result shape
7. Response returned: `{sql, results, explanation, chart_config}`
8. Frontend renders: explanation → results table → Chart.js visualization → collapsible SQL

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
├── ai_engine/     # Claude integration: tool use, prompt builder, schema loader
├── query_runner/  # SQL executor with SELECT-only validation
├── history/       # QueryHistory model, GET /api/history endpoint
└── demo_db/       # demo.sqlite file + seed management command
```

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Create user account |
| POST | `/api/auth/login` | No | Returns auth token |
| POST | `/api/query` | Token | NL question → SQL + results + explanation + chart |
| GET | `/api/history` | Token | Returns authenticated user's query history |

### Claude Tool Use

The `ai_engine` module defines one tool:

```python
execute_sql(sql: str) -> list[dict]
```

Claude receives the full e-commerce schema and the user's question. It generates a `SELECT` query, calls `execute_sql`, receives the rows, and writes the explanation. The backend intercepts the tool call, validates the SQL (SELECT-only), executes it against `demo.sqlite`, and returns results back to the Claude conversation.

### Security

- `query_runner` rejects any SQL that is not a `SELECT` statement before execution
- Auth token required on `/api/query` and `/api/history`
- `ANTHROPIC_API_KEY` and database internals never exposed in API responses
- All inputs validated by DRF serializers before processing

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

### Chart Auto-Selection Logic

| Data shape | Chart type |
|-----------|------------|
| 1 text column + 1 numeric column | `bar` |
| Date/month column + numeric | `line` |
| Proportions / percentages | `pie` |
| Everything else | table only |

---

## Data Models

### QueryHistory

```python
class QueryHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    sql_generated = models.TextField()
    explanation = models.TextField()
    row_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Environment Variables

```
ANTHROPIC_API_KEY     # Claude API key (required)
DJANGO_SECRET_KEY     # Django secret key
DEBUG                 # True locally, False in production
ALLOWED_HOSTS         # Railway domain in production
```

---

## Deployment

**Platform:** Railway (single service)

- Django + Whitenoise serves the React build (`frontend/dist/`)
- `npm run build` runs during Railway deploy, output copied to Django's static root
- `Procfile`: `web: gunicorn core.wsgi`
- `requirements.txt` at project root

**Single service approach:** no CORS configuration needed, simpler Railway setup, mirrors the existing rag-chatbot deployment pattern.

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
- Query editing or re-running
- Export to CSV/Excel
- Admin panel customization
