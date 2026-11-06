"""
Generate Sample Data for the Multi-Source RAG + Text-to-SQL System.

Creates realistic e-commerce sample data in the PostgreSQL database:
  - 50 customers across three segments (SMB, Enterprise, Individual)
  - 20 products across multiple categories
  - 200 orders with varied statuses and amounts

Usage:
    python data/generate_sample_data.py

Requires DATABASE_URL in .env or as an environment variable.
"""

import os
import sys
import random
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Allow running from project root or from data/ directory
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv optional; rely on environment variables

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set.")
    print("Add DATABASE_URL=postgresql://... to your .env file.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Sample data definitions
# ---------------------------------------------------------------------------

CUSTOMER_NAMES = [
    "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown", "Emma Davis",
    "Frank Miller", "Grace Wilson", "Henry Moore", "Isla Taylor", "Jack Anderson",
    "Karen Thomas", "Liam Jackson", "Mia White", "Noah Harris", "Olivia Martin",
    "Peter Thompson", "Quinn Garcia", "Rachel Martinez", "Sam Robinson", "Tina Clark",
    "Uma Rodriguez", "Victor Lewis", "Wendy Lee", "Xavier Walker", "Yara Hall",
    "Zach Allen", "Amber Young", "Brian King", "Catherine Wright", "Daniel Scott",
    "Ella Green", "Finn Baker", "Gina Adams", "Hank Nelson", "Iris Carter",
    "Jake Mitchell", "Kara Perez", "Leo Roberts", "Maya Turner", "Nina Phillips",
    "Oscar Campbell", "Paige Parker", "Quinn Evans", "Rose Edwards", "Sam Collins",
    "Tara Stewart", "Umar Sanchez", "Vera Morris", "Will Rogers", "Xena Reed",
]

SEGMENTS = ["SMB", "Enterprise", "Individual"]
SEGMENT_WEIGHTS = [0.3, 0.2, 0.5]  # 30% SMB, 20% Enterprise, 50% Individual

COUNTRIES = ["USA", "UK", "Canada", "Australia", "Germany", "France", "India", "Japan"]

PRODUCTS = [
    # (name, category, price, stock)
    ("Laptop Pro 15",         "Electronics",  1299.99, 45),
    ("Wireless Mouse",        "Electronics",    29.99, 200),
    ("Mechanical Keyboard",   "Electronics",    89.99, 150),
    ("4K Monitor 27-inch",    "Electronics",   449.99,  60),
    ("USB-C Hub 7-port",      "Electronics",    49.99, 300),
    ("CRM Suite Enterprise",  "Software",      299.00,  999),
    ("Data Analytics Pro",    "Software",      199.00,  999),
    ("Project Manager Plus",  "Software",       99.00,  999),
    ("Security Suite",        "Software",      149.00,  999),
    ("Cloud Backup 1TB",      "Software",       79.00,  999),
    ("Server Rack 42U",       "Hardware",     2499.99,  10),
    ("Network Switch 24-port","Hardware",      399.99,  30),
    ("SSD 1TB NVMe",          "Hardware",       99.99, 180),
    ("RAM 32GB DDR5",         "Hardware",      149.99, 120),
    ("UPS 1500VA",            "Hardware",      249.99,  40),
    ("Office Chair Ergonomic","Furniture",     349.99,  25),
    ("Standing Desk 60-inch", "Furniture",     699.99,  15),
    ("Monitor Arm Dual",      "Furniture",     129.99,  80),
    ("Webcam 4K",             "Electronics",   199.99, 100),
    ("Noise-Cancelling Headphones", "Electronics", 349.99, 70),
]

STATUSES = ["Pending", "Processing", "Delivered", "Cancelled"]
STATUS_WEIGHTS = [0.15, 0.15, 0.60, 0.10]

SHIPPING_ADDRESSES = [
    "123 Main St, New York, NY 10001",
    "456 Oak Ave, Los Angeles, CA 90001",
    "789 Pine Rd, Chicago, IL 60601",
    "321 Elm St, Houston, TX 77001",
    "654 Maple Dr, Phoenix, AZ 85001",
    "987 Cedar Ln, Philadelphia, PA 19101",
    "147 Birch Blvd, San Antonio, TX 78201",
    "258 Walnut Way, San Diego, CA 92101",
    "369 Spruce St, Dallas, TX 75201",
    "741 Ash Ave, San Jose, CA 95101",
]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection():
    """Create and return a psycopg2 connection."""
    return psycopg2.connect(DATABASE_URL)


def insert_customers(cursor, n: int = 50) -> list[int]:
    """Insert n customers and return their IDs."""
    ids = []
    used_emails: set[str] = set()

    names = CUSTOMER_NAMES[:n] if n <= len(CUSTOMER_NAMES) else (
        CUSTOMER_NAMES * ((n // len(CUSTOMER_NAMES)) + 1)
    )[:n]

    for i, name in enumerate(names):
        first, *rest = name.split()
        last = rest[-1] if rest else "User"
        email_base = f"{first.lower()}.{last.lower()}"
        email = f"{email_base}@example.com"
        # Deduplicate
        suffix = 1
        while email in used_emails:
            email = f"{email_base}{suffix}@example.com"
            suffix += 1
        used_emails.add(email)

        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        country  = random.choice(COUNTRIES)

        cursor.execute(
            """
            INSERT INTO customers (name, email, segment, country)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE
                SET name    = EXCLUDED.name,
                    segment = EXCLUDED.segment,
                    country = EXCLUDED.country
            RETURNING id
            """,
            (name, email, segment, country),
        )
        ids.append(cursor.fetchone()[0])

    print(f"  ✓ Inserted/updated {len(ids)} customers")
    return ids


def insert_products(cursor) -> list[int]:
    """Insert products and return their IDs."""
    ids = []
    for name, category, price, stock in PRODUCTS:
        cursor.execute(
            """
            INSERT INTO products (name, category, price, stock_quantity, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            (name, category, price, stock, f"High-quality {name} for professionals."),
        )
        row = cursor.fetchone()
        if row:
            ids.append(row[0])

    # If all were conflicts (re-run), fetch existing IDs
    if not ids:
        cursor.execute("SELECT id FROM products ORDER BY id")
        ids = [r[0] for r in cursor.fetchall()]

    print(f"  ✓ Inserted/found {len(ids)} products")
    return ids


def insert_orders(cursor, customer_ids: list[int], n: int = 200):
    """Insert n orders spread across customers."""
    start_date = date.today() - timedelta(days=365)

    for _ in range(n):
        customer_id   = random.choice(customer_ids)
        order_date    = start_date + timedelta(days=random.randint(0, 365))
        total_amount  = round(random.uniform(25.0, 3500.0), 2)
        status        = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        shipping_addr = random.choice(SHIPPING_ADDRESSES)

        cursor.execute(
            """
            INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (customer_id, order_date, total_amount, status, shipping_addr),
        )

    print(f"  ✓ Inserted {n} orders")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Generating sample e-commerce data...")
    print("=" * 60)

    random.seed(42)  # Reproducible data

    conn = get_connection()
    try:
        conn.autocommit = False
        cursor = conn.cursor()

        print("\n[1/3] Inserting customers...")
        customer_ids = insert_customers(cursor, n=50)

        print("[2/3] Inserting products...")
        insert_products(cursor)

        print("[3/3] Inserting orders...")
        insert_orders(cursor, customer_ids, n=200)

        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Sample data generated successfully!")
        print("   50 customers | 20 products | 200 orders")
        print("=" * 60)

    except Exception as exc:
        conn.rollback()
        print(f"\n❌ Error generating data: {exc}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()

