"""
setup_database.py
-----------------
Creates a sample SQLite database with realistic business data.
Run this once before starting the app: python src/setup_database.py
"""

import sqlite3
import os

DB_PATH = "data/company.db"


def create_database():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Table 1: employees ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            department  TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            salary      REAL    NOT NULL,
            hire_date   TEXT    NOT NULL,
            city        TEXT    NOT NULL
        )
    """)

    employees = [
        ("Arjun Sharma",    "Engineering",  "Backend Engineer",      85000, "2021-03-15", "Bangalore"),
        ("Priya Nair",      "Engineering",  "Frontend Engineer",     78000, "2022-06-01", "Hyderabad"),
        ("Rahul Mehta",     "Sales",        "Sales Manager",         92000, "2020-01-10", "Mumbai"),
        ("Sneha Iyer",      "HR",           "HR Specialist",         65000, "2022-09-20", "Chennai"),
        ("Vikram Singh",    "Engineering",  "ML Engineer",           95000, "2021-07-05", "Bangalore"),
        ("Anjali Patel",    "Marketing",    "Marketing Lead",        80000, "2019-11-30", "Mumbai"),
        ("Kiran Kumar",     "Sales",        "Sales Executive",       60000, "2023-02-14", "Delhi"),
        ("Divya Rao",       "Engineering",  "DevOps Engineer",       88000, "2021-04-22", "Bangalore"),
        ("Amit Joshi",      "Finance",      "Finance Analyst",       72000, "2020-08-18", "Pune"),
        ("Meera Pillai",    "Marketing",    "Content Strategist",    68000, "2022-12-01", "Hyderabad"),
        ("Suresh Babu",     "Engineering",  "Backend Engineer",      82000, "2023-01-15", "Bangalore"),
        ("Nisha Kapoor",    "HR",           "HR Manager",            74000, "2019-06-10", "Delhi"),
        ("Rohan Das",       "Sales",        "Sales Executive",       58000, "2023-05-20", "Kolkata"),
        ("Pooja Menon",     "Finance",      "Finance Manager",       90000, "2018-03-05", "Mumbai"),
        ("Arun Verma",      "Engineering",  "ML Engineer",           97000, "2020-10-12", "Bangalore"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO employees (name, department, role, salary, hire_date, city) VALUES (?,?,?,?,?,?)",
        employees
    )

    # ── Table 2: products ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL,
            supplier    TEXT    NOT NULL
        )
    """)

    products = [
        ("Laptop Pro 15",       "Electronics",  75000, 120, "TechWorld"),
        ("Wireless Mouse",      "Accessories",   1200,  500, "PeriTech"),
        ("USB-C Hub",           "Accessories",   2500,  300, "PeriTech"),
        ("4K Monitor",          "Electronics",  35000,   80, "TechWorld"),
        ("Mechanical Keyboard", "Accessories",   5500,  200, "PeriTech"),
        ("Office Chair",        "Furniture",    18000,   60, "ComfortPlus"),
        ("Standing Desk",       "Furniture",    32000,   40, "ComfortPlus"),
        ("Webcam HD",           "Electronics",   4500,  150, "TechWorld"),
        ("Headphones Pro",      "Electronics",   8000,  180, "AudioMax"),
        ("Notebook Pack",       "Stationery",     350, 1000, "OfficeSupply"),
        ("Whiteboard",          "Furniture",     6000,   55, "ComfortPlus"),
        ("SSD 1TB",             "Electronics",   7500,  220, "TechWorld"),
        ("Ethernet Cable",      "Accessories",    600,  800, "PeriTech"),
        ("Desk Lamp",           "Furniture",     2200,  180, "ComfortPlus"),
        ("Pen Drive 64GB",      "Accessories",    800,  600, "TechWorld"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, category, price, stock, supplier) VALUES (?,?,?,?,?)",
        products
    )

    # ── Table 3: sales ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            quantity    INTEGER NOT NULL,
            total_price REAL    NOT NULL,
            sale_date   TEXT    NOT NULL,
            region      TEXT    NOT NULL,
            FOREIGN KEY (product_id)  REFERENCES products(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)

    sales = [
        (1,  3,  2, 150000, "2024-01-05", "West"),
        (4,  3,  5, 175000, "2024-01-12", "West"),
        (2,  7,  10,  12000, "2024-01-18", "North"),
        (6,  7,  3,  54000, "2024-02-01", "North"),
        (1, 13,  1,  75000, "2024-02-10", "East"),
        (9,  3,  4,  32000, "2024-02-15", "West"),
        (5,  7,  6,  33000, "2024-03-01", "North"),
        (7, 13,  2,  64000, "2024-03-08", "East"),
        (3,  3, 15,  37500, "2024-03-20", "West"),
        (8,  7,  8,  36000, "2024-04-02", "North"),
        (1, 13,  3, 225000, "2024-04-15", "East"),
        (12, 3,  5,  37500, "2024-04-22", "West"),
        (4,  7,  2,  70000, "2024-05-05", "North"),
        (9, 13,  6,  48000, "2024-05-18", "East"),
        (6,  3,  4,  72000, "2024-06-01", "West"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO sales (product_id, employee_id, quantity, total_price, sale_date, region) VALUES (?,?,?,?,?,?)",
        sales
    )

    conn.commit()
    conn.close()
    print(f"✅ Database created at: {DB_PATH}")
    print("   Tables: employees, products, sales")
    print("   Sample rows: 15 employees | 15 products | 15 sales")


if __name__ == "__main__":
    create_database()
