# NaturalQuery Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack web app where authenticated users ask questions in plain English and get SQL results, explanations, and charts powered by Claude API tool use against a pre-seeded e-commerce SQLite database.

**Architecture:** Django + DRF backend with Token auth orchestrates a Claude tool-use loop (`execute_sql` tool) against a read-only `demo.sqlite`. Results + explanation + auto-detected chart config are returned to a React/TypeScript frontend and persisted in `QueryHistory`. Single Railway service: Django serves the Vite build via Whitenoise.

**Tech Stack:** Python 3.11+, Django 5, DRF, anthropic SDK, sqlglot, pytest, pytest-django — React 18, TypeScript, Vite, Axios, Chart.js + react-chartjs-2, react-router-dom

---

## File Map

```
naturalquery/
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── settings.py          # All settings incl. DEMO_DB_PATH, CLAUDE_MODEL
│   │   ├── urls.py              # Root URL conf: /api/auth/, /api/query, /api/history
│   │   └── wsgi.py
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── serializers.py       # RegisterSerializer, LoginSerializer
│   │   ├── views.py             # RegisterView, LoginView
│   │   ├── urls.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_auth.py
│   ├── ai_engine/
│   │   ├── __init__.py
│   │   ├── prompt.py            # SCHEMA constant, build_system_prompt()
│   │   ├── engine.py            # run_query(), QueryEngineError
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_engine.py
│   ├── query_runner/
│   │   ├── __init__.py
│   │   ├── validator.py         # validate_select_only(), InvalidSQLError
│   │   ├── executor.py          # execute_sql(sql, db_path=None) -> dict
│   │   ├── chart.py             # detect_chart_type(columns, rows) -> dict | None
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_validator.py
│   │       ├── test_executor.py
│   │       └── test_chart.py
│   ├── history/
│   │   ├── __init__.py
│   │   ├── models.py            # QueryHistory
│   │   ├── serializers.py       # QueryHistorySerializer
│   │   ├── views.py             # QueryView (POST /api/query), HistoryView (GET /api/history)
│   │   ├── urls.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_history.py
│   ├── demo_db/
│   │   ├── __init__.py
│   │   └── management/
│   │       └── commands/
│   │           ├── __init__.py
│   │           └── seed_demo.py # Creates + populates demo.sqlite
│   ├── conftest.py              # pytest fixtures: api_client, auth_client, demo_db_path
│   ├── pytest.ini
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── types/index.ts       # All shared TS interfaces
│   │   ├── api/client.ts        # Axios instance + typed API functions
│   │   ├── components/
│   │   │   ├── Auth/LoginForm.tsx
│   │   │   ├── Auth/RegisterForm.tsx
│   │   │   ├── Layout/Header.tsx
│   │   │   ├── Sidebar/QueryHistory.tsx
│   │   │   ├── Chat/ChatInput.tsx
│   │   │   ├── Results/ResultsTable.tsx
│   │   │   └── Results/ChartDisplay.tsx
│   │   ├── pages/LoginPage.tsx
│   │   ├── pages/DashboardPage.tsx
│   │   ├── App.tsx              # Auth state, routing
│   │   ├── App.css              # Dark theme global styles
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
├── requirements.txt
├── railway.toml
├── Procfile
├── .gitignore
└── README.md
```

---

## Chunk 1: Backend Scaffold, Settings, Demo Database & Auth

### Task 1: Initialize Django project and install dependencies

**Files:**
- Create: `requirements.txt`
- Create: `backend/manage.py` (via django-admin)
- Create: `backend/core/__init__.py`, `backend/core/wsgi.py`

- [ ] **Step 1: Create requirements.txt**

```
Django==5.0.6
djangorestframework==3.15.2
django-cors-headers==4.3.1
anthropic==0.40.0
sqlglot==25.0.0
gunicorn==22.0.0
whitenoise==6.7.0
pytest==8.2.2
pytest-django==4.8.0
```

- [ ] **Step 2: Create virtual environment and install**

Run from `naturalquery/`:
```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

Expected: All packages installed without errors.

- [ ] **Step 3: Scaffold Django project**

Run from `naturalquery/`:
```bash
mkdir backend && cd backend
django-admin startproject core .
```

Expected: `backend/manage.py`, `backend/core/` created.

- [ ] **Step 4: Create all Django apps**

Run from `naturalquery/backend/`:
```bash
python manage.py startapp accounts
python manage.py startapp ai_engine
python manage.py startapp query_runner
python manage.py startapp history
python manage.py startapp demo_db
```

- [ ] **Step 5: Create test directories**

Run from `naturalquery/backend/`:
```bash
mkdir -p accounts/tests ai_engine/tests query_runner/tests history/tests
touch accounts/tests/__init__.py ai_engine/tests/__init__.py
touch query_runner/tests/__init__.py history/tests/__init__.py
touch demo_db/management/__init__.py demo_db/management/commands/__init__.py
mkdir -p demo_db/management/commands
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "chore: scaffold Django project and create all apps"
```

---

### Task 2: Django settings

**Files:**
- Modify: `backend/core/settings.py`
- Create: `backend/core/urls.py`
- Create: `backend/pytest.ini`

- [ ] **Step 1: Write settings.py**

Replace `backend/core/settings.py` entirely:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "accounts",
    "ai_engine",
    "query_runner",
    "history",
    "demo_db",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend_dist"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
        ]},
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "app.sqlite",
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "frontend_dist"] if (BASE_DIR / "frontend_dist").exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True

# Project-specific settings
DEMO_DB_PATH = BASE_DIR / "demo_db" / "demo.sqlite"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-5-20250514"  # Update to latest Sonnet if needed

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
```

- [ ] **Step 2: Write core/urls.py**

```python
from django.urls import path, include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("api/auth/", include("accounts.urls")),
    path("api/", include("history.urls")),
]

# Catch-all: serve React SPA for non-API routes
urlpatterns += [
    re_path(r"^(?!api/).*$", TemplateView.as_view(template_name="index.html")),
]
```

- [ ] **Step 3: Write pytest.ini**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
pythonpath = .
python_files = tests/*.py test_*.py
python_classes = Test*
python_functions = test_*
```

- [ ] **Step 4: Run migrations**

```bash
cd backend && python manage.py migrate
```

Expected: `app.sqlite` created, auth tables created. No errors.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: configure Django settings, URLs, and pytest"
```

---

### Task 3: Demo database seed command

**Files:**
- Create: `backend/demo_db/management/commands/seed_demo.py`

- [ ] **Step 1: Write seed_demo.py**

```python
import random
import sqlite3
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

BRAZILIAN_STATES = ["SP", "RJ", "MG", "BA", "RS", "PR", "PE", "CE", "SC", "GO"]
FIRST_NAMES = ["Ana","Carlos","Maria","João","Fernanda","Pedro","Juliana","Lucas","Beatriz","Rafael",
               "Camila","Diego","Larissa","Bruno","Mariana","Felipe","Aline","Ricardo","Vanessa","Thiago"]
LAST_NAMES = ["Silva","Santos","Oliveira","Souza","Lima","Costa","Ferreira","Rodrigues","Almeida","Nascimento"]
CATEGORIES = ["Electronics","Clothing","Home & Garden","Sports","Books","Toys","Beauty","Automotive"]
PRODUCT_TEMPLATES = [
    ("Wireless Headphones","Electronics",189.90),("USB-C Cable","Electronics",29.90),
    ("Smart Watch","Electronics",459.00),("Bluetooth Speaker","Electronics",149.90),
    ("Phone Case","Electronics",39.90),("T-Shirt Basic","Clothing",49.90),
    ("Jeans Slim","Clothing",129.90),("Running Shoes","Sports",299.90),
    ("Yoga Mat","Sports",89.90),("Water Bottle","Sports",49.90),
    ("Coffee Maker","Home & Garden",199.90),("Air Fryer","Home & Garden",349.90),
    ("Knife Set","Home & Garden",149.90),("Plant Pot","Home & Garden",39.90),
    ("Python Book","Books",79.90),("React Book","Books",89.90),
    ("Cookbook","Books",59.90),("Toy Car","Toys",49.90),
    ("Building Blocks","Toys",89.90),("Face Cream","Beauty",79.90),
    ("Shampoo","Beauty",29.90),("Perfume","Beauty",189.90),
    ("Motor Oil","Automotive",49.90),("Car Wax","Automotive",39.90),
    ("Sunglasses","Clothing",89.90),("Backpack","Clothing",149.90),
    ("Desk Lamp","Home & Garden",99.90),("Notebook","Books",19.90),
    ("Jump Rope","Sports",29.90),("Beard Trimmer","Beauty",149.90),
    ("Laptop Stand","Electronics",79.90),("Mouse Pad","Electronics",24.90),
    ("Ceramic Mug","Home & Garden",29.90),("Tea Set","Home & Garden",89.90),
    ("Cycling Gloves","Sports",49.90),("Puzzle 1000pc","Toys",59.90),
    ("Action Figure","Toys",39.90),("Lip Balm","Beauty",14.90),
    ("Car Charger","Automotive",34.90),("Floor Mat","Automotive",59.90),
    ("Long Sleeve Shirt","Clothing",69.90),("Hoodie","Clothing",159.90),
    ("Ear Buds","Electronics",99.90),("Power Bank","Electronics",129.90),
    ("Scented Candle","Home & Garden",44.90),("Canvas Bag","Clothing",34.90),
    ("Fitness Band","Sports",199.90),("Dictionary","Books",49.90),
    ("Board Game","Toys",119.90),
]
STATUSES = ["pending", "shipped", "delivered", "delivered", "delivered", "cancelled"]


class Command(BaseCommand):
    help = "Seed the demo e-commerce SQLite database"

    def handle(self, *args, **options):
        db_path = settings.DEMO_DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        try:
            self._create_tables(conn)
            self._seed(conn)
            conn.commit()
        finally:
            conn.close()
        self.stdout.write(self.style.SUCCESS(f"Seeded demo database at {db_path}"))

    def _create_tables(self, conn):
        conn.executescript("""
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS categories;
            DROP TABLE IF EXISTS customers;

            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id),
                price REAL NOT NULL,
                stock_qty INTEGER NOT NULL
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                total REAL NOT NULL
            );
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            );
        """)

    def _seed(self, conn):
        rng = random.Random(42)
        base_date = datetime(2024, 1, 1)

        # Categories
        cat_ids = {}
        for cat in CATEGORIES:
            cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
            cat_ids[cat] = cur.lastrowid

        # Products
        product_ids = []
        product_prices = {}
        for name, cat, price in PRODUCT_TEMPLATES:
            stock = rng.randint(10, 500)
            cur = conn.execute(
                "INSERT INTO products (name, category_id, price, stock_qty) VALUES (?, ?, ?, ?)",
                (name, cat_ids[cat], price, stock),
            )
            product_ids.append(cur.lastrowid)
            product_prices[cur.lastrowid] = price

        # Customers
        customer_ids = []
        used_emails = set()
        for i in range(200):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            name = f"{first} {last}"
            email_base = f"{first.lower()}.{last.lower()}{i}"
            email = f"{email_base}@example.com"
            state = rng.choice(BRAZILIAN_STATES)
            city = f"City{rng.randint(1, 30)}"
            days_ago = rng.randint(30, 800)
            created_at = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                "INSERT INTO customers (name, email, city, state, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, email, city, state, created_at),
            )
            customer_ids.append(cur.lastrowid)

        # Orders + order_items
        for _ in range(1000):
            customer_id = rng.choice(customer_ids)
            status = rng.choice(STATUSES)
            days_ago = rng.randint(1, 730)
            created_at = (base_date + timedelta(days=rng.randint(0, 365))).strftime("%Y-%m-%d %H:%M:%S")

            items = rng.randint(1, 4)
            chosen_products = rng.sample(product_ids, min(items, len(product_ids)))
            total = 0.0
            item_rows = []
            for pid in chosen_products:
                qty = rng.randint(1, 3)
                price = product_prices[pid]
                total += qty * price
                item_rows.append((pid, qty, price))

            cur = conn.execute(
                "INSERT INTO orders (customer_id, status, created_at, total) VALUES (?, ?, ?, ?)",
                (customer_id, status, created_at, round(total, 2)),
            )
            order_id = cur.lastrowid
            for pid, qty, price in item_rows:
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, pid, qty, price),
                )
```

- [ ] **Step 2: Run seed command**

```bash
cd backend && python manage.py seed_demo
```

Expected: `Seeded demo database at .../demo_db/demo.sqlite`

- [ ] **Step 3: Verify seed**

```bash
python -c "
import sqlite3; conn = sqlite3.connect('demo_db/demo.sqlite')
print('customers:', conn.execute('SELECT COUNT(*) FROM customers').fetchone())
print('products:', conn.execute('SELECT COUNT(*) FROM products').fetchone())
print('orders:', conn.execute('SELECT COUNT(*) FROM orders').fetchone())
"
```

Expected: customers: (200,), products: (50,), orders: (1000,)

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: add demo database seed command with e-commerce data"
```

---

### Task 4: conftest.py

**Files:**
- Create: `backend/conftest.py`

- [ ] **Step 1: Write conftest.py**

```python
import pytest
import sqlite3
from pathlib import Path


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(db, django_user_model):
    from rest_framework.test import APIClient
    from rest_framework.authtoken.models import Token

    user = django_user_model.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client, user


@pytest.fixture
def demo_db_path(tmp_path):
    """In-memory-style test DB with e-commerce schema and minimal seed data."""
    db_path = tmp_path / "test_demo.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, email TEXT, city TEXT, state TEXT, created_at TEXT);
        CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, price REAL, stock_qty INTEGER);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, status TEXT, created_at TEXT, total REAL);
        CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL);

        INSERT INTO categories VALUES (1, 'Electronics');
        INSERT INTO customers VALUES (1, 'Alice', 'alice@test.com', 'SP', 'SP', '2024-01-01');
        INSERT INTO products VALUES (1, 'Headphones', 1, 199.90, 50);
        INSERT INTO products VALUES (2, 'Cable', 1, 29.90, 200);
        INSERT INTO orders VALUES (1, 1, 'delivered', '2024-03-01', 229.80);
        INSERT INTO order_items VALUES (1, 1, 1, 1, 199.90);
        INSERT INTO order_items VALUES (2, 1, 2, 1, 29.90);
    """)
    conn.commit()
    conn.close()
    return db_path
```

- [ ] **Step 2: Commit**

```bash
git add backend/conftest.py
git commit -m "test: add pytest conftest with api_client, auth_client, demo_db_path fixtures"
```

---

### Task 5: Register endpoint (TDD)

**Files:**
- Create: `backend/accounts/serializers.py`
- Create: `backend/accounts/views.py`
- Create: `backend/accounts/urls.py`
- Create: `backend/accounts/tests/test_auth.py`

- [ ] **Step 1: Write failing tests**

`backend/accounts/tests/test_auth.py`:
```python
import pytest

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"


@pytest.mark.django_db
def test_register_returns_token(api_client):
    resp = api_client.post(REGISTER_URL, {"username": "alice", "email": "a@b.com", "password": "secure123"})
    assert resp.status_code == 201
    assert "token" in resp.json()
    assert resp.json()["username"] == "alice"


@pytest.mark.django_db
def test_register_duplicate_username_returns_400(api_client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="x")
    resp = api_client.post(REGISTER_URL, {"username": "alice", "email": "b@b.com", "password": "secure123"})
    assert resp.status_code == 400
    assert "errors" in resp.json()


@pytest.mark.django_db
def test_register_missing_password_returns_400(api_client):
    resp = api_client.post(REGISTER_URL, {"username": "bob", "email": "b@b.com"})
    assert resp.status_code == 400
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && pytest accounts/tests/test_auth.py::test_register_returns_token -v
```

Expected: FAIL — `accounts.urls` not found or 404.

- [ ] **Step 3: Write serializers.py**

```python
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def save(self):
        user = User.objects.create_user(
            username=self.validated_data["username"],
            email=self.validated_data["email"],
            password=self.validated_data["password"],
        )
        token, _ = Token.objects.get_or_create(user=user)
        return user, token
```

- [ ] **Step 4: Write views.py**

```python
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if not s.is_valid():
            return Response({"errors": s.errors}, status=400)
        user, token = s.save()
        return Response({"token": token.key, "user_id": user.id, "username": user.username}, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"errors": {"non_field_errors": ["Unable to log in with provided credentials."]}},
                status=400,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.id, "username": user.username})
```

- [ ] **Step 5: Write urls.py**

```python
from django.urls import path
from .views import RegisterView, LoginView

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
]
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
pytest accounts/tests/test_auth.py -v
```

Expected: 3 PASSED.

- [ ] **Step 7: Add login tests**

Append to `backend/accounts/tests/test_auth.py`:
```python
@pytest.mark.django_db
def test_login_returns_token(api_client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="secure123")
    resp = api_client.post(LOGIN_URL, {"username": "alice", "password": "secure123"})
    assert resp.status_code == 200
    assert "token" in resp.json()


@pytest.mark.django_db
def test_login_wrong_password_returns_400(api_client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="secure123")
    resp = api_client.post(LOGIN_URL, {"username": "alice", "password": "wrong"})
    assert resp.status_code == 400
    assert "errors" in resp.json()
```

- [ ] **Step 8: Run all auth tests**

```bash
pytest accounts/tests/test_auth.py -v
```

Expected: 5 PASSED.

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: register and login endpoints with token auth"
```

---

## Chunk 2: Query Runner, AI Engine, and Query Endpoint

### Task 6: SQL validator (TDD)

**Files:**
- Create: `backend/query_runner/validator.py`
- Create: `backend/query_runner/tests/test_validator.py`

- [ ] **Step 1: Write failing tests**

`backend/query_runner/tests/test_validator.py`:
```python
import pytest
from query_runner.validator import validate_select_only, InvalidSQLError


def test_valid_select_passes():
    validate_select_only("SELECT id, name FROM products")


def test_select_case_insensitive():
    validate_select_only("select * from customers")


def test_select_with_joins_passes():
    validate_select_only(
        "SELECT p.name, SUM(oi.quantity) FROM products p "
        "JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id"
    )


def test_insert_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("INSERT INTO products VALUES (1, 'x', 1, 9.9, 10)")


def test_update_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("UPDATE products SET price=0 WHERE id=1")


def test_delete_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("DELETE FROM products")


def test_drop_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("DROP TABLE products")


def test_multiple_statements_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("SELECT 1; DROP TABLE customers")
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest query_runner/tests/test_validator.py -v
```

Expected: ERROR — module not found.

- [ ] **Step 3: Write validator.py**

```python
import sqlglot


class InvalidSQLError(Exception):
    pass


def validate_select_only(sql: str) -> None:
    """Raises InvalidSQLError if sql is not a single SELECT statement."""
    try:
        statements = sqlglot.parse(sql)
    except Exception as e:
        raise InvalidSQLError(f"Could not parse SQL: {e}") from e

    if not statements or len(statements) != 1:
        raise InvalidSQLError("Only single SELECT statements are allowed.")

    stmt = statements[0]
    if not isinstance(stmt, sqlglot.exp.Select):
        raise InvalidSQLError("Only SELECT queries are allowed.")
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest query_runner/tests/test_validator.py -v
```

Expected: 8 PASSED.

- [ ] **Step 5: Commit**

```bash
git add query_runner/validator.py query_runner/tests/test_validator.py
git commit -m "feat: SQL SELECT-only validator with sqlglot"
```

---

### Task 7: SQL executor with row limit (TDD)

**Files:**
- Create: `backend/query_runner/executor.py`
- Create: `backend/query_runner/tests/test_executor.py`

- [ ] **Step 1: Write failing tests**

`backend/query_runner/tests/test_executor.py`:
```python
import pytest
from query_runner.executor import execute_sql


def test_returns_columns_and_rows(demo_db_path):
    result = execute_sql("SELECT name FROM products ORDER BY id", db_path=demo_db_path)
    assert result["columns"] == ["name"]
    assert ["Headphones"] in result["rows"]


def test_returns_dict_with_correct_shape(demo_db_path):
    result = execute_sql("SELECT * FROM categories", db_path=demo_db_path)
    assert "columns" in result
    assert "rows" in result
    assert isinstance(result["rows"], list)


def test_auto_appends_limit_when_missing(demo_db_path):
    # Table has 2 products; without LIMIT we get all, but the SQL gets LIMIT 500 appended
    result = execute_sql("SELECT id FROM products", db_path=demo_db_path)
    assert len(result["rows"]) <= 500


def test_respects_explicit_limit(demo_db_path):
    result = execute_sql("SELECT id FROM products LIMIT 1", db_path=demo_db_path)
    assert len(result["rows"]) == 1


def test_empty_result(demo_db_path):
    result = execute_sql("SELECT * FROM customers WHERE id = 99999", db_path=demo_db_path)
    assert result["rows"] == []
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest query_runner/tests/test_executor.py -v
```

Expected: ERROR — module not found.

- [ ] **Step 3: Write executor.py**

```python
import sqlite3
from django.conf import settings


def execute_sql(sql: str, db_path=None) -> dict:
    """Execute a validated SELECT query. Returns {"columns": [...], "rows": [...]}."""
    if db_path is None:
        db_path = settings.DEMO_DB_PATH

    # Append LIMIT 500 if not present
    if "LIMIT" not in sql.upper():
        sql = f"{sql.rstrip(';')} LIMIT 500"

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows}
    finally:
        conn.close()
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest query_runner/tests/test_executor.py -v
```

Expected: 5 PASSED.

- [ ] **Step 5: Commit**

```bash
git add query_runner/executor.py query_runner/tests/test_executor.py
git commit -m "feat: SQL executor with automatic LIMIT 500 guard"
```

---

### Task 8: Chart auto-selector (TDD)

**Files:**
- Create: `backend/query_runner/chart.py`
- Create: `backend/query_runner/tests/test_chart.py`

- [ ] **Step 1: Write failing tests**

`backend/query_runner/tests/test_chart.py`:
```python
import pytest
from query_runner.chart import detect_chart_type


def test_text_plus_numeric_returns_bar():
    result = detect_chart_type(["name", "total_sold"], [["Headphones", 342], ["Cable", 289]])
    assert result is not None
    assert result["type"] == "bar"
    assert result["x_key"] == "name"
    assert result["y_key"] == "total_sold"


def test_date_column_returns_line():
    result = detect_chart_type(["month", "revenue"], [["2024-01", 5000.0], ["2024-02", 6000.0]])
    assert result is not None
    assert result["type"] == "line"


def test_percent_column_returns_pie():
    result = detect_chart_type(["category", "share_percent"], [["Electronics", 45.0], ["Clothing", 30.0]])
    assert result is not None
    assert result["type"] == "pie"


def test_single_column_returns_none():
    result = detect_chart_type(["name"], [["Alice"]])
    assert result is None


def test_empty_rows_returns_none():
    result = detect_chart_type(["name", "total"], [])
    assert result is None


def test_all_numeric_returns_none():
    result = detect_chart_type(["id", "price"], [[1, 9.99], [2, 19.99]])
    assert result is None
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest query_runner/tests/test_chart.py -v
```

Expected: ERROR — module not found.

- [ ] **Step 3: Write chart.py**

```python
def detect_chart_type(columns: list, rows: list) -> dict | None:
    """Auto-detect best chart type from result shape. Returns chart_config dict or None."""
    if not rows or len(columns) < 2:
        return None

    col_types = []
    for i, col in enumerate(columns):
        sample = next((r[i] for r in rows if r[i] is not None), None)
        name_lower = col.lower()

        # Keyword check takes priority over value type
        if any(k in name_lower for k in ("pct", "percent", "rate", "share")):
            col_types.append("percent")
        elif any(k in name_lower for k in ("date", "month", "year", "week", "period", "day")):
            col_types.append("date")
        elif isinstance(sample, (int, float)):
            col_types.append("numeric")
        elif isinstance(sample, str):
            col_types.append("text")
        else:
            col_types.append("text")

    text_cols = [columns[i] for i, t in enumerate(col_types) if t == "text"]
    date_cols = [columns[i] for i, t in enumerate(col_types) if t == "date"]
    num_cols = [columns[i] for i, t in enumerate(col_types) if t == "numeric"]
    pct_cols = [columns[i] for i, t in enumerate(col_types) if t == "percent"]

    if date_cols and num_cols:
        return {"type": "line", "x_key": date_cols[0], "y_key": num_cols[0], "label": num_cols[0]}
    if pct_cols and text_cols:
        return {"type": "pie", "x_key": text_cols[0], "y_key": pct_cols[0], "label": pct_cols[0]}
    if text_cols and num_cols:
        return {"type": "bar", "x_key": text_cols[0], "y_key": num_cols[0], "label": num_cols[0]}
    return None
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest query_runner/tests/test_chart.py -v
```

Expected: 6 PASSED.

- [ ] **Step 5: Commit**

```bash
git add query_runner/chart.py query_runner/tests/test_chart.py
git commit -m "feat: chart auto-selector (bar/line/pie detection)"
```

---

### Task 9: AI Engine — prompt builder and Claude tool use loop (TDD)

**Files:**
- Create: `backend/ai_engine/prompt.py`
- Create: `backend/ai_engine/engine.py`
- Create: `backend/ai_engine/tests/test_engine.py`

- [ ] **Step 1: Write prompt.py**

```python
SCHEMA = """
You are an assistant that helps users query an e-commerce database.
The database has the following tables:

customers(id INTEGER, name TEXT, email TEXT, city TEXT, state TEXT, created_at TEXT)
categories(id INTEGER, name TEXT)
products(id INTEGER, name TEXT, category_id INTEGER REFERENCES categories(id), price REAL, stock_qty INTEGER)
orders(id INTEGER, customer_id INTEGER REFERENCES customers(id),
       status TEXT -- values: 'pending','shipped','delivered','cancelled',
       created_at TEXT, total REAL)
order_items(id INTEGER, order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER, unit_price REAL)

Use the execute_sql tool to run SELECT queries.
After seeing the results, give a friendly, concise answer in the user's language.
Never modify data. Only use SELECT queries.
"""


def build_user_message(question: str) -> str:
    return f"{SCHEMA}\n\nQuestion: {question}"
```

- [ ] **Step 2: Write failing tests**

`backend/ai_engine/tests/test_engine.py`:
```python
import pytest
from unittest.mock import MagicMock, patch


def _make_tool_use_response(sql: str, tool_id: str = "toolu_01"):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.input = {"sql": sql}
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = [block]
    return resp


def _make_end_turn_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


FAKE_RESULTS = {"columns": ["name"], "rows": [["Headphones"]]}


@pytest.mark.django_db
def test_run_query_success(demo_db_path, settings):
    from ai_engine.engine import run_query

    settings.DEMO_DB_PATH = demo_db_path
    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use_response("SELECT name FROM products LIMIT 5"),
        _make_end_turn_response("Here are the top products."),
    ]

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with patch("ai_engine.engine.execute_sql", return_value=FAKE_RESULTS):
            sql, results, explanation = run_query("What are the top products?")

    assert sql == "SELECT name FROM products LIMIT 5"
    assert results == FAKE_RESULTS
    assert "products" in explanation.lower()


@pytest.mark.django_db
def test_run_query_raises_on_no_tool_call(settings):
    from ai_engine.engine import run_query, QueryEngineError

    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_end_turn_response("I don't know.")

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(QueryEngineError):
            run_query("Tell me a joke")


@pytest.mark.django_db
def test_run_query_raises_invalid_sql(settings):
    from ai_engine.engine import run_query
    from query_runner.validator import InvalidSQLError

    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_tool_use_response(
        "DROP TABLE customers"
    )

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(InvalidSQLError):
            run_query("Delete all customers")


@pytest.mark.django_db
def test_run_query_hits_iteration_limit(settings):
    from ai_engine.engine import run_query, QueryEngineError

    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    # Always returns tool_use → triggers iteration cap
    mock_client.messages.create.return_value = _make_tool_use_response("SELECT 1")

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with patch("ai_engine.engine.execute_sql", return_value={"columns": ["1"], "rows": [[1]]}):
            with pytest.raises(QueryEngineError):
                run_query("Infinite loop question")
```

- [ ] **Step 3: Run — verify fail**

```bash
pytest ai_engine/tests/test_engine.py -v
```

Expected: ERROR — module not found.

- [ ] **Step 4: Write engine.py**

```python
import json
import anthropic
from django.conf import settings
from query_runner.validator import validate_select_only
from query_runner.executor import execute_sql
from .prompt import build_user_message

TOOLS = [
    {
        "name": "execute_sql",
        "description": "Execute a SELECT SQL query against the e-commerce database and return results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "The SELECT SQL query to execute"}
            },
            "required": ["sql"],
        },
    }
]


class QueryEngineError(Exception):
    pass


def run_query(question: str) -> tuple:
    """
    Run a natural language question through the Claude tool-use loop.
    Returns (sql_generated: str, results: dict, explanation: str).
    Raises InvalidSQLError if Claude generates a non-SELECT query.
    Raises QueryEngineError if Claude cannot answer.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": build_user_message(question)}]

    last_sql = None
    last_results = None
    max_iterations = 3

    for iteration in range(max_iterations):
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            temperature=0,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_use = next((b for b in response.content if b.type == "tool_use"), None)
            if not tool_use:
                raise QueryEngineError(
                    "Could not generate a valid query for this question. Please try rephrasing."
                )

            sql = tool_use.input["sql"]
            validate_select_only(sql)  # raises InvalidSQLError — propagates to view

            results = execute_sql(sql)
            last_sql = sql
            last_results = results

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(results),
                }],
            })

        elif response.stop_reason == "end_turn":
            explanation = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            if last_sql is None:
                raise QueryEngineError(
                    "Could not generate a valid query for this question. Please try rephrasing."
                )
            return last_sql, last_results, explanation

        else:
            raise QueryEngineError(
                "Could not generate a valid query for this question. Please try rephrasing."
            )

    raise QueryEngineError(
        "Could not generate a valid query for this question. Please try rephrasing."
    )
```

- [ ] **Step 5: Run — verify pass**

```bash
pytest ai_engine/tests/test_engine.py -v
```

Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add ai_engine/ query_runner/
git commit -m "feat: Claude tool-use engine with SELECT validation and chart detection"
```

---

## Chunk 3: History Endpoint, Frontend, and Deploy

### Task 10: QueryHistory model + Query + History endpoints (TDD)

**Files:**
- Create: `backend/history/models.py`
- Create: `backend/history/serializers.py`
- Create: `backend/history/views.py`
- Create: `backend/history/urls.py`
- Create: `backend/history/tests/test_history.py`

- [ ] **Step 1: Write the model**

`backend/history/models.py`:
```python
from django.db import models
from django.contrib.auth.models import User


class QueryHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="queries")
    question = models.TextField()
    sql_generated = models.TextField()
    explanation = models.TextField()
    results = models.JSONField()          # {"columns": [...], "rows": [...]}
    chart_config = models.JSONField(null=True, blank=True)
    row_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
```

- [ ] **Step 2: Run migration**

```bash
cd backend && python manage.py makemigrations history && python manage.py migrate
```

Expected: New migration created and applied.

- [ ] **Step 3: Write failing tests**

`backend/history/tests/test_history.py`:
```python
import pytest
from unittest.mock import patch

QUERY_URL = "/api/query"
HISTORY_URL = "/api/history"

FAKE_ENGINE_RESULT = (
    "SELECT name FROM products LIMIT 5",
    {"columns": ["name"], "rows": [["Headphones"], ["Cable"]]},
    "Here are the top 2 products.",
)


@pytest.mark.django_db
def test_query_requires_auth(api_client):
    resp = api_client.post(QUERY_URL, {"question": "show products"})
    assert resp.status_code == 401


@pytest.mark.django_db
def test_query_returns_full_response(auth_client):
    client, user = auth_client
    with patch("history.views.run_query", return_value=FAKE_ENGINE_RESULT):
        resp = client.post(QUERY_URL, {"question": "show products"}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sql_generated"] == "SELECT name FROM products LIMIT 5"
    assert data["results"]["columns"] == ["name"]
    assert data["explanation"] == "Here are the top 2 products."
    assert data["row_count"] == 2


@pytest.mark.django_db
def test_query_saves_to_history(auth_client):
    from history.models import QueryHistory
    client, user = auth_client
    with patch("history.views.run_query", return_value=FAKE_ENGINE_RESULT):
        client.post(QUERY_URL, {"question": "show products"}, format="json")
    assert QueryHistory.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_query_missing_question_returns_400(auth_client):
    client, _ = auth_client
    resp = client.post(QUERY_URL, {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_history_returns_user_queries(auth_client):
    from history.models import QueryHistory
    client, user = auth_client
    QueryHistory.objects.create(
        user=user, question="Q", sql_generated="SELECT 1",
        explanation="E", results={"columns": ["id"], "rows": [[1]]},
        chart_config=None, row_count=1,
    )
    resp = client.get(HISTORY_URL)
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@pytest.mark.django_db
def test_history_requires_auth(api_client):
    resp = api_client.get(HISTORY_URL)
    assert resp.status_code == 401


@pytest.mark.django_db
def test_history_capped_at_50(auth_client):
    from history.models import QueryHistory
    client, user = auth_client
    for i in range(55):
        QueryHistory.objects.create(
            user=user, question=f"Q{i}", sql_generated="SELECT 1",
            explanation="E", results={"columns": [], "rows": []},
            chart_config=None, row_count=0,
        )
    resp = client.get(HISTORY_URL)
    assert len(resp.json()["results"]) == 50
```

- [ ] **Step 4: Run — verify fail**

```bash
pytest history/tests/test_history.py -v
```

Expected: FAIL — 404 or import errors.

- [ ] **Step 5: Write serializers.py**

```python
from rest_framework import serializers
from .models import QueryHistory


class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = ["id", "question", "sql_generated", "explanation", "results",
                  "chart_config", "row_count", "created_at"]
```

- [ ] **Step 6: Write views.py**

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ai_engine.engine import run_query, QueryEngineError
from query_runner.validator import InvalidSQLError
from query_runner.chart import detect_chart_type
from .models import QueryHistory
from .serializers import QueryHistorySerializer


class QueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"errors": {"question": ["This field is required."]}}, status=400)

        try:
            sql_generated, results, explanation = run_query(question)
        except InvalidSQLError as e:
            return Response({"errors": {"query": [str(e)]}}, status=400)
        except QueryEngineError as e:
            return Response({"errors": {"question": [str(e)]}},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        chart_config = detect_chart_type(results["columns"], results["rows"])
        row_count = len(results["rows"])

        QueryHistory.objects.create(
            user=request.user,
            question=question,
            sql_generated=sql_generated,
            explanation=explanation,
            results=results,
            chart_config=chart_config,
            row_count=row_count,
        )

        # Keep only the latest 50 per user
        old_ids = list(
            QueryHistory.objects.filter(user=request.user)
            .values_list("id", flat=True)[50:]
        )
        if old_ids:
            QueryHistory.objects.filter(id__in=old_ids).delete()

        return Response({
            "question": question,
            "sql_generated": sql_generated,
            "explanation": explanation,
            "results": results,
            "chart_config": chart_config,
            "row_count": row_count,
        })


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = QueryHistory.objects.filter(user=request.user)[:50]
        return Response({"results": QueryHistorySerializer(qs, many=True).data})
```

- [ ] **Step 7: Write urls.py**

```python
from django.urls import path
from .views import QueryView, HistoryView

urlpatterns = [
    path("query", QueryView.as_view()),
    path("history", HistoryView.as_view()),
]
```

- [ ] **Step 8: Run — verify pass**

```bash
pytest history/tests/test_history.py -v
```

Expected: 7 PASSED.

- [ ] **Step 9: Run full backend test suite**

```bash
pytest -v
```

Expected: All tests PASS. No errors.

- [ ] **Step 10: Commit**

```bash
git add history/
git commit -m "feat: QueryHistory model + /api/query + /api/history endpoints"
```

---

### Task 11: Frontend scaffold + types + API client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Scaffold Vite React TypeScript app**

Run from `naturalquery/`:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
npm install axios react-router-dom chart.js react-chartjs-2
npm install --save-dev @types/react-router-dom
```

- [ ] **Step 2: Configure Vite proxy for local dev**

Replace `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 3: Write types/index.ts**

```typescript
export interface AuthResponse {
  token: string
  user_id: number
  username: string
}

export interface QueryResults {
  columns: string[]
  rows: (string | number | null)[][]
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie'
  x_key: string
  y_key: string
  label: string
}

export interface QueryResponse {
  question: string
  sql_generated: string
  explanation: string
  results: QueryResults
  chart_config: ChartConfig | null
  row_count: number
}

export interface HistoryItem {
  id: number
  question: string
  sql_generated: string
  explanation: string
  results: QueryResults
  chart_config: ChartConfig | null
  row_count: number
  created_at: string
}
```

- [ ] **Step 4: Write api/client.ts**

```typescript
import axios from 'axios'
import type { AuthResponse, QueryResponse, HistoryItem } from '../types'

const api = axios.create({ baseURL: '/api' })

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`
    localStorage.setItem('auth_token', token)
  } else {
    delete api.defaults.headers.common['Authorization']
    localStorage.removeItem('auth_token')
  }
}

export function loadStoredToken(): string | null {
  return localStorage.getItem('auth_token')
}

export async function register(username: string, email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', { username, email, password })
  return data
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { username, password })
  return data
}

export async function postQuery(question: string): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', { question })
  return data
}

export async function getHistory(): Promise<HistoryItem[]> {
  const { data } = await api.get<{ results: HistoryItem[] }>('/history')
  return data.results
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold with Vite, TypeScript types, and API client"
```

---

### Task 12: Dark theme CSS + Auth components + Login page

**Files:**
- Create: `frontend/src/App.css`
- Create: `frontend/src/components/Auth/LoginForm.tsx`
- Create: `frontend/src/components/Auth/RegisterForm.tsx`
- Create: `frontend/src/pages/LoginPage.tsx`

- [ ] **Step 1: Write App.css (dark theme)**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0f1117;
  color: #e2e8f0;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 14px;
}

input, textarea, button {
  font-family: inherit;
  font-size: inherit;
}

.page-center {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f1117;
}

.auth-card {
  background: #1a1f2e;
  border: 1px solid #2d3748;
  border-radius: 8px;
  padding: 32px;
  width: 360px;
}

.auth-card h2 { margin-bottom: 24px; color: #a78bfa; font-size: 20px; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; color: #94a3b8; font-size: 13px; }
.form-group input {
  width: 100%;
  background: #0f1117;
  border: 1px solid #2d3748;
  border-radius: 4px;
  padding: 8px 12px;
  color: #e2e8f0;
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus { border-color: #7c3aed; }

.btn {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}
.btn:hover { opacity: 0.85; }
.btn-primary { background: #7c3aed; color: white; }
.btn-secondary { background: transparent; border: 1px solid #4b5563; color: #94a3b8; }

.error-msg { color: #f87171; font-size: 12px; margin-top: 8px; }
.link-btn { background: none; border: none; color: #a78bfa; cursor: pointer; font-size: 13px; }
.link-btn:hover { text-decoration: underline; }

/* Dashboard layout */
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 52px;
  background: #1a1f2e;
  border-bottom: 1px solid #2d3748;
  flex-shrink: 0;
}
.header h1 { font-size: 16px; color: #a78bfa; font-weight: 700; }

.dashboard-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: #1a1f2e;
  border-right: 1px solid #2d3748;
  overflow-y: auto;
  padding: 12px;
  flex-shrink: 0;
}
.sidebar h3 { color: #4b5563; font-size: 11px; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }
.history-item {
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  color: #94a3b8;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s;
}
.history-item:hover, .history-item.active { background: #252d3d; color: #e2e8f0; }

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.results-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #4b5563;
  gap: 8px;
}
.empty-state p { font-size: 13px; }

.explanation-box {
  background: #1a1f2e;
  border: 1px solid #2d3748;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  line-height: 1.6;
  color: #cbd5e1;
}

.table-wrap { overflow-x: auto; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #252d3d; color: #94a3b8; text-align: left; padding: 8px 12px; border-bottom: 1px solid #2d3748; }
td { padding: 7px 12px; border-bottom: 1px solid #1e2433; color: #cbd5e1; }
tr:hover td { background: #1a1f2e; }

.chart-wrap { background: #1a1f2e; border: 1px solid #2d3748; border-radius: 6px; padding: 16px; margin-bottom: 16px; max-height: 320px; }

.sql-toggle { margin-bottom: 16px; }
.sql-toggle summary { cursor: pointer; color: #4b5563; font-size: 12px; user-select: none; }
.sql-toggle summary:hover { color: #94a3b8; }
.sql-block {
  background: #0a0e1a;
  border: 1px solid #2d3748;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #7dd3fc;
  overflow-x: auto;
  margin-top: 8px;
  white-space: pre-wrap;
}

.chat-bar {
  border-top: 1px solid #2d3748;
  padding: 12px 20px;
  display: flex;
  gap: 10px;
  background: #1a1f2e;
  flex-shrink: 0;
}
.chat-bar input {
  flex: 1;
  background: #0f1117;
  border: 1px solid #2d3748;
  border-radius: 6px;
  padding: 10px 14px;
  color: #e2e8f0;
  outline: none;
}
.chat-bar input:focus { border-color: #7c3aed; }
.chat-bar button {
  background: #7c3aed;
  border: none;
  border-radius: 6px;
  padding: 0 20px;
  color: white;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}
.chat-bar button:hover { opacity: 0.85; }
.chat-bar button:disabled { opacity: 0.4; cursor: not-allowed; }

.loading-text { color: #4b5563; font-size: 13px; padding: 8px 0; }
```

- [ ] **Step 2: Write LoginForm.tsx**

```tsx
import { useState } from 'react'

interface Props {
  onLogin: (username: string, password: string) => Promise<void>
  onSwitchToRegister: () => void
}

export function LoginForm({ onLogin, onSwitchToRegister }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onLogin(username, password)
    } catch {
      setError('Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-card">
      <h2>Sign in to NaturalQuery</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={e => setUsername(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <p style={{ marginTop: 16, textAlign: 'center', color: '#4b5563', fontSize: 13 }}>
        No account?{' '}
        <button className="link-btn" onClick={onSwitchToRegister}>Register</button>
      </p>
    </div>
  )
}
```

- [ ] **Step 3: Write RegisterForm.tsx**

```tsx
import { useState } from 'react'

interface Props {
  onRegister: (username: string, email: string, password: string) => Promise<void>
  onSwitchToLogin: () => void
}

export function RegisterForm({ onRegister, onSwitchToLogin }: Props) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onRegister(username, email, password)
    } catch (err: any) {
      const data = err?.response?.data?.errors
      if (data?.username) setError(data.username[0])
      else if (data?.password) setError(data.password[0])
      else setError('Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-card">
      <h2>Create account</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={e => setUsername(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Register'}
        </button>
      </form>
      <p style={{ marginTop: 16, textAlign: 'center', color: '#4b5563', fontSize: 13 }}>
        Have an account?{' '}
        <button className="link-btn" onClick={onSwitchToLogin}>Sign in</button>
      </p>
    </div>
  )
}
```

- [ ] **Step 4: Write pages/LoginPage.tsx**

```tsx
import { useState } from 'react'
import { LoginForm } from '../components/Auth/LoginForm'
import { RegisterForm } from '../components/Auth/RegisterForm'

interface Props {
  onAuth: (token: string, username: string) => void
}

export function LoginPage({ onAuth }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const _ = loading  // suppress unused warning during typing

  async function handleLogin(username: string, password: string) {
    const { login, setAuthToken } = await import('../api/client')
    const data = await login(username, password)
    setAuthToken(data.token)
    onAuth(data.token, data.username)
  }

  async function handleRegister(username: string, email: string, password: string) {
    const { register, setAuthToken } = await import('../api/client')
    const data = await register(username, email, password)
    setAuthToken(data.token)
    onAuth(data.token, data.username)
  }

  return (
    <div className="page-center">
      {mode === 'login' ? (
        <LoginForm onLogin={handleLogin} onSwitchToRegister={() => setMode('register')} />
      ) : (
        <RegisterForm onRegister={handleRegister} onSwitchToLogin={() => setMode('login')} />
      )}
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: dark theme CSS, auth forms, and login page"
```

---

### Task 13: Dashboard components

**Files:**
- Create: `frontend/src/components/Layout/Header.tsx`
- Create: `frontend/src/components/Sidebar/QueryHistory.tsx`
- Create: `frontend/src/components/Chat/ChatInput.tsx`
- Create: `frontend/src/components/Results/ResultsTable.tsx`
- Create: `frontend/src/components/Results/ChartDisplay.tsx`

- [ ] **Step 1: Write Header.tsx**

```tsx
interface Props {
  username: string
  onLogout: () => void
}

export function Header({ username, onLogout }: Props) {
  return (
    <header className="header">
      <h1>NaturalQuery</h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: '#4b5563', fontSize: 13 }}>{username}</span>
        <button className="btn btn-secondary" style={{ width: 'auto', padding: '5px 12px', fontSize: 12 }} onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  )
}
```

- [ ] **Step 2: Write Sidebar/QueryHistory.tsx**

```tsx
import type { HistoryItem } from '../../types'

interface Props {
  items: HistoryItem[]
  activeId: number | null
  onSelect: (item: HistoryItem) => void
}

export function QueryHistory({ items, activeId, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <h3>History</h3>
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
          {item.question}
        </div>
      ))}
    </aside>
  )
}
```

- [ ] **Step 3: Write Chat/ChatInput.tsx**

```tsx
import { useState } from 'react'

interface Props {
  onSubmit: (question: string) => void
  disabled: boolean
}

export function ChatInput({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = value.trim()
    if (!q) return
    onSubmit(q)
    setValue('')
  }

  return (
    <form className="chat-bar" onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder="Ask a question about the store data..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        {disabled ? '...' : 'Ask'}
      </button>
    </form>
  )
}
```

- [ ] **Step 4: Write Results/ResultsTable.tsx**

```tsx
import type { QueryResults } from '../../types'

interface Props {
  results: QueryResults
}

export function ResultsTable({ results }: Props) {
  if (!results.rows.length) {
    return <p style={{ color: '#4b5563', fontSize: 13 }}>No results found.</p>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {results.columns.map(col => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {results.rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => <td key={j}>{cell ?? '—'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 5: Write Results/ChartDisplay.tsx**

```tsx
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Title, Tooltip, Legend,
} from 'chart.js'
import { Bar, Line, Pie } from 'react-chartjs-2'
import type { ChartConfig, QueryResults } from '../../types'

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Title, Tooltip, Legend
)

interface Props {
  config: ChartConfig
  results: QueryResults
}

const COLORS = ['#7c3aed','#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#84cc16']

export function ChartDisplay({ config, results }: Props) {
  const xIdx = results.columns.indexOf(config.x_key)
  const yIdx = results.columns.indexOf(config.y_key)

  if (xIdx === -1 || yIdx === -1) return null

  const labels = results.rows.map(r => String(r[xIdx]))
  const data = results.rows.map(r => Number(r[yIdx]))

  const chartData = {
    labels,
    datasets: [{
      label: config.label,
      data,
      backgroundColor: config.type === 'pie' ? COLORS : '#7c3aed',
      borderColor: config.type === 'line' ? '#7c3aed' : undefined,
      borderWidth: config.type === 'line' ? 2 : undefined,
      fill: false,
    }],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#94a3b8' } } },
    scales: config.type !== 'pie' ? {
      x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2433' } },
      y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2433' } },
    } : undefined,
  }

  const style = { height: '100%' }

  return (
    <div className="chart-wrap">
      {config.type === 'bar' && <Bar data={chartData} options={options} style={style} />}
      {config.type === 'line' && <Line data={chartData} options={options} style={style} />}
      {config.type === 'pie' && <Pie data={chartData} options={options} style={style} />}
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: dashboard components — header, sidebar, chat input, table, chart"
```

---

### Task 14: DashboardPage + App.tsx + routing

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write DashboardPage.tsx**

```tsx
import { useState, useEffect } from 'react'
import { Header } from '../components/Layout/Header'
import { QueryHistory as QueryHistorySidebar } from '../components/Sidebar/QueryHistory'
import { ChatInput } from '../components/Chat/ChatInput'
import { ResultsTable } from '../components/Results/ResultsTable'
import { ChartDisplay } from '../components/Results/ChartDisplay'
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
      setActiveId(null)
      // Refresh history
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
              <div className="empty-state">
                <p>Ask a question about the store data to get started.</p>
                <p style={{ fontSize: 12 }}>Example: "What are the top 5 best selling products?"</p>
              </div>
            )}
            {loading && <p className="loading-text">Thinking...</p>}
            {error && <p className="error-msg" style={{ padding: '8px 0' }}>{error}</p>}
            {result && !loading && (
              <>
                <div className="explanation-box">{result.explanation}</div>
                <ResultsTable results={result.results} />
                {result.chart_config && (
                  <ChartDisplay config={result.chart_config} results={result.results} />
                )}
                <details className="sql-toggle">
                  <summary>View generated SQL</summary>
                  <pre className="sql-block">{result.sql_generated}</pre>
                </details>
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

- [ ] **Step 2: Write App.tsx**

```tsx
import { useState, useEffect } from 'react'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { setAuthToken, loadStoredToken } from './api/client'
import './App.css'

export default function App() {
  const [token, setToken] = useState<string | null>(null)
  const [username, setUsername] = useState('')

  useEffect(() => {
    const stored = loadStoredToken()
    if (stored) {
      setAuthToken(stored)
      setToken(stored)
      setUsername(localStorage.getItem('auth_username') || '')
    }
  }, [])

  function handleAuth(t: string, u: string) {
    setToken(t)
    setUsername(u)
    localStorage.setItem('auth_username', u)
  }

  function handleLogout() {
    setAuthToken(null)
    setToken(null)
    setUsername('')
    localStorage.removeItem('auth_username')
  }

  if (!token) return <LoginPage onAuth={handleAuth} />
  return <DashboardPage username={username} onLogout={handleLogout} />
}
```

- [ ] **Step 3: Write main.tsx**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

- [ ] **Step 4: Remove default Vite files**

```bash
rm -f frontend/src/assets/react.svg frontend/public/vite.svg
# Delete content of frontend/src/index.css (not needed — using App.css)
```

- [ ] **Step 5: Test frontend locally**

In one terminal:
```bash
cd backend && python manage.py runserver
```

In another:
```bash
cd frontend && npm run dev
```

Open http://localhost:5173 — verify login page renders with dark theme. Register a user, verify redirect to dashboard. Type a question, verify the query reaches the backend (check Django logs). If ANTHROPIC_API_KEY is set, verify a full response returns with table + chart.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: dashboard page — results, chart, history sidebar, full app wiring"
```

---

### Task 15: Deploy config + .gitignore + README

**Files:**
- Create: `railway.toml`
- Create: `Procfile`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Write railway.toml**

```toml
[build]
buildCommand = "cd frontend && npm install && npm run build && mkdir -p ../backend/frontend_dist && cp -r dist/. ../backend/frontend_dist/ && cd ../backend && pip install -r ../requirements.txt && python manage.py migrate && python manage.py seed_demo && python manage.py collectstatic --noinput"

[deploy]
startCommand = "cd backend && gunicorn core.wsgi --bind 0.0.0.0:$PORT --workers 2"
```

- [ ] **Step 2: Write Procfile (local fallback)**

```
web: cd backend && gunicorn core.wsgi --bind 0.0.0.0:$PORT
```

- [ ] **Step 3: Write .gitignore**

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
*.sqlite3
*.sqlite
*.egg-info/

# Django
backend/staticfiles/
backend/app.sqlite
backend/demo_db/demo.sqlite
backend/frontend_dist/

# Frontend
frontend/node_modules/
frontend/dist/

# Env
.env
.env.*
!.env.example

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

- [ ] **Step 4: Write README.md**

```markdown
# NaturalQuery

Query an e-commerce database using plain English. Powered by Claude AI.

![NaturalQuery Dashboard](docs/screenshot-placeholder.png)

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
```

- [ ] **Step 5: Run backend tests one final time**

```bash
cd backend && pytest -v
```

Expected: All tests PASS.

- [ ] **Step 6: Final commit**

```bash
git add railway.toml Procfile .gitignore README.md
git commit -m "feat: deploy config (railway.toml), gitignore, README"
```

---

## Summary

| Chunk | Tasks | Description |
|---|---|---|
| 1 | 1–5 | Django project, settings, demo DB seed, auth endpoints |
| 2 | 6–9 | SQL validator, executor, chart detector, AI engine |
| 3 | 10–15 | History model + endpoints, full React frontend, deploy config |

**All backend logic is TDD.** Run `pytest -v` from `backend/` at any point to verify the full suite.
