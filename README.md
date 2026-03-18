# NaturalQuery

Query an e-commerce database using plain English. Powered by Claude AI.

## Features

- Natural language to SQL via Claude tool use
- Auto-generated charts (bar, line, pie)
- Query history per user
- Token-based authentication

## Tech Stack

**Backend:** Django 5, DRF, Anthropic SDK, sqlglot  
**Frontend:** React 18, TypeScript, Vite, Chart.js  
**Deploy:** Railway (single service)

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend

```bash
cd naturalquery
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo
ANTHROPIC_API_KEY=your_key python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `DJANGO_SECRET_KEY` | Django secret key | Yes (prod) |
| `DEBUG` | `True` / `False` | No (default True) |
| `ALLOWED_HOSTS` | Comma-separated hosts | Yes (prod) |

## Deploy to Railway

1. Push to GitHub
2. Create new Railway project → Deploy from GitHub
3. Set environment variables in Railway dashboard
4. Railway auto-runs the build command from `railway.toml`

## Example Questions

- "What are the top 5 best selling products?"
- "Show monthly revenue for 2024"
- "Which state has the most customers?"
- "How many orders were cancelled last month?"
