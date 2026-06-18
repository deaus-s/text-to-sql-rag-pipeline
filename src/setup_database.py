"""
setup_database.py
-----------------
Creates a sample SQLite database with realistic business data and automatically 
pre-calculates & exports Star Schema CSV assets ready for immediate Power BI upload.
"""

import sqlite3
import os
import pandas as pd

DB_PATH = "data/company.db"
OUTPUT_DIR = "power_bi_prepared_data"

def create_database():
    os.makedirs("data", exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
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
        ("Vikram Singh",    "Engineering",  "ML Engineer",           95000, "2021-11-05", "Bangalore"),
        ("Ananya Rao",      "Sales",        "Account Executive",     70000, "2023-02-18", "Delhi"),
        ("Rohan Joshi",     "Marketing",    "Growth Marketer",       72000, "2022-05-12", "Mumbai"),
        ("Kriti Deshmukh",  "HR",           "HR Manager",            88000, "2019-08-25", "Bangalore"),
        ("Aditya Verma",    "Engineering",  "DevOps Engineer",       82000, "2023-01-15", "Hyderabad"),
        ("Meera Reddy",     "Sales",        "Sales Executive",       55000, "2023-07-01", "Chennai")
    ]

    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO employees (name, department, role, salary, hire_date, city)
            VALUES (?, ?, ?, ?, ?, ?)
        """, employees)

    # ── Table 2: products ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL
        )
    """)

    products = [
        ("Cloud analytics Pro", "Software", 1500.0, 120),
        ("Enterprise DB Node",  "Software", 3500.0,  45),
        ("Developer Laptop X",  "Hardware", 2200.0,  80),
        ("AI Inference GPU",    "Hardware", 4500.0,  15),
        ("Cybersecurity Pack",  "Software",  950.0, 300),
        ("4K Business Monitor", "Hardware",  450.0, 150),
        ("SaaS CRM License",    "Software",  120.0, 500)
    ]

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO products (name, category, price, stock)
            VALUES (?, ?, ?, ?)
        """, products)

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
        (8,  2,  5,  45000, "2024-04-02", "South")
    ]

    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO sales (product_id, employee_id, quantity, total_price, sale_date, region)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sales)

    conn.commit()
    conn.close()
    print("✅ Database successfully created at: data/company.db")

def generate_powerbi_preprepared_data():
    """Extracts tables, models into a Star Schema, and outputs clean CSVs for Power BI."""
    print("📐 Running pipeline to pre-calculate and structure data maps for Power BI...")
    if not os.path.exists(DB_PATH):
        return
        
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        s.id AS sale_id, s.product_id, p.name AS product_name, p.category AS product_category,
        s.employee_id, e.name AS employee_name, e.department AS employee_department,
        s.quantity, s.total_price AS revenue, s.sale_date, s.region
    FROM sales s
    LEFT JOIN products p ON s.product_id = p.id
    LEFT JOIN employees e ON s.employee_id = e.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return

    # Advanced Calculations (Z-Score Outliers, Growth Targets, Quantiles)
    rev_mean = df['revenue'].mean()
    rev_std = df['revenue'].std() if df['revenue'].std() != 0 else 1
    df['z_score'] = ((df['revenue'] - rev_mean) / rev_std).round(2)
    df['is_anomaly'] = df['z_score'].apply(lambda x: "🚨 Anomaly" if abs(x) > 1.96 else "✅ Normal")
    
    try:
        df['performance_quantile'] = pd.qcut(df['revenue'], q=4, labels=['Bronze Tier', 'Silver Tier', 'Gold Tier', 'Platinum Tier'])
    except Exception:
        df['performance_quantile'] = 'Standard Growth'
        
    df['forward_target'] = (df['revenue'] * 1.125).round(2)

    # Split into high-performance Star Schema structure
    dim_products = df[['product_id', 'product_name', 'product_category']].drop_duplicates().reset_index(drop=True)
    dim_employees = df[['employee_id', 'employee_name', 'employee_department']].drop_duplicates().reset_index(drop=True)
    
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    date_range = pd.date_range(start=df['sale_date'].min(), end=df['sale_date'].max(), freq='D')
    dim_date = pd.DataFrame({"DateKey": date_range})
    dim_date['Year'] = dim_date['DateKey'].dt.year
    dim_date['Quarter'] = "Q" + dim_date['DateKey'].dt.quarter.astype(str)
    dim_date['MonthName'] = dim_date['DateKey'].dt.strftime('%B')
    dim_date['MonthNumber'] = dim_date['DateKey'].dt.month

    fact_insights = df[['sale_id', 'product_id', 'employee_id', 'sale_date', 'region', 'quantity', 'revenue', 'forward_target', 'z_score', 'is_anomaly', 'performance_quantile']].copy()
    fact_insights.rename(columns={'sale_date': 'DateKey'}, inplace=True)

    # Save finalized assets
    fact_insights.to_csv(os.path.join(OUTPUT_DIR, "Fact_Insights.csv"), index=False)
    dim_products.to_csv(os.path.join(OUTPUT_DIR, "Dim_Products.csv"), index=False)
    dim_employees.to_csv(os.path.join(OUTPUT_DIR, "Dim_Employees.csv"), index=False)
    dim_date.to_csv(os.path.join(OUTPUT_DIR, "Dim_Date.csv"), index=False)
    
    print(f"✅ Success! 4 Pre-prepared data tables exported to: /{OUTPUT_DIR}/")

if __name__ == "__main__":
    create_database()
    generate_powerbi_preprepared_data()