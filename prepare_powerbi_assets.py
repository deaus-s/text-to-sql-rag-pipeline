"""
prepare_powerbi_assets.py
-------------------------
Pre-calculates Z-Scores, Quantile-tiers, and targets from your database,
and splits the data into separate Fact and Dimension CSVs ready for Power BI.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

# Change this if your database file is in a different location
DB_PATH = "data/company.db"
OUTPUT_DIR = "power_bi_prepared_data"

def main():
    print("🚀 Starting Automated Data Prep Layer for Power BI...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Connect and pull transactional sales data joined with descriptive properties
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        s.id AS sale_id,
        s.product_id,
        p.name AS product_name,
        p.category AS product_category,
        s.employee_id,
        e.name AS employee_name,
        e.department AS employee_department,
        s.quantity,
        s.total_price AS revenue,
        s.sale_date,
        s.region
    FROM sales s
    LEFT JOIN products p ON s.product_id = p.id
    LEFT JOIN employees e ON s.employee_id = e.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("❌ Error: No transactional logs found in database source.")
        return

    print(f"📥 Loaded {len(df)} base raw transactions. Calculating advanced features...")

    # 2. RUNTIME STATISTICAL COMPUTATIONS (Advanced Features)
    # Feature A: Statistical Outlier Flags (Z-Scores on Revenue)
    rev_mean = df['revenue'].mean()
    rev_std = df['revenue'].std() if df['revenue'].std() != 0 else 1
    df['z_score'] = ((df['revenue'] - rev_mean) / rev_std).round(2)
    df['is_anomaly'] = df['z_score'].apply(lambda x: "🚨 Anomaly" if abs(x) > 1.96 else "✅ Normal")
    
    # Feature B: Dynamic Quantile Ranking Tiers (RFM style positioning)
    try:
        df['performance_quantile'] = pd.qcut(
            df['revenue'], 
            q=4, 
            labels=['Bronze Tier', 'Silver Tier', 'Gold Tier', 'Platinum Tier']
        )
    except Exception:
        df['performance_quantile'] = 'Standard Growth'
        
    # Feature C: Predictive Forecasting Multiplier (+12.5% Next-Gen Milestone target)
    df['forward_target'] = (df['revenue'] * 1.125).round(2)

    # 3. EXTRACT AND REFACTOR TABLES INTO STAR SCHEMA DESIGN
    print("📐 Splitting data structures into high-performance Star Schema blocks...")

    # A. Dim_Products Lookup Table
    dim_products = df[['product_id', 'product_name', 'product_category']].drop_duplicates().reset_index(drop=True)
    
    # B. Dim_Employees Lookup Table
    dim_employees = df[['employee_id', 'employee_name', 'employee_department']].drop_duplicates().reset_index(drop=True)
    
    # C. Dim_Date Time Intelligence Calendar Dimension Table
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    min_date = df['sale_date'].min()
    max_date = df['sale_date'].max()
    
    # Generate continuous dates matching the transaction range
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    dim_date = pd.DataFrame({"DateKey": date_range})
    dim_date['Year'] = dim_date['DateKey'].dt.year
    dim_date['Quarter'] = "Q" + dim_date['DateKey'].dt.quarter.astype(str)
    dim_date['MonthName'] = dim_date['DateKey'].dt.strftime('%B')
    dim_date['MonthNumber'] = dim_date['DateKey'].dt.month
    dim_date['DayOfWeek'] = dim_date['DateKey'].dt.strftime('%A')

    # D. Fact_Insights Table (Keeps metrics + keys connecting to dimension lookups)
    fact_insights = df[[
        'sale_id', 'product_id', 'employee_id', 'sale_date', 'region',
        'quantity', 'revenue', 'forward_target', 'z_score', 'is_anomaly', 'performance_quantile'
    ]].copy()
    fact_insights.rename(columns={'sale_date': 'DateKey'}, inplace=True)

    # 4. SAVE PRE-PREPARED POWER BI DIRECTORIES
    print("💾 Storing final optimized data assets...")
    
    fact_insights.to_csv(os.path.join(OUTPUT_DIR, "Fact_Insights.csv"), index=False)
    dim_products.to_csv(os.path.join(OUTPUT_DIR, "Dim_Products.csv"), index=False)
    dim_employees.to_csv(os.path.join(OUTPUT_DIR, "Dim_Employees.csv"), index=False)
    dim_date.to_csv(os.path.join(OUTPUT_DIR, "Dim_Date.csv"), index=False)
    
    print(f"✅ Success! 4 reporting matrices generated and exported to: /{OUTPUT_DIR}")
    print("   👉 [Fact_Insights.csv, Dim_Products.csv, Dim_Employees.csv, Dim_Date.csv]")

if __name__ == "__main__":
    main()