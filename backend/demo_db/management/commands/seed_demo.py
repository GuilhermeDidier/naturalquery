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
        for i in range(200):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            name = f"{first} {last}"
            email = f"{first.lower()}.{last.lower()}{i}@example.com"
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
