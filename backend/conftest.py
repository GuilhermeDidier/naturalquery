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
