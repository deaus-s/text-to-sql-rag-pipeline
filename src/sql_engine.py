"""
sql_engine.py
-------------
Orchestrates AI-driven SQL assembly, database query safety filters,
and real-time advanced business transformation calculations.
"""

import sqlite3
import re
import numpy as np
import pandas as pd
from groq import Groq
from schema_rag import load_vector_store
from dotenv import load_dotenv

load_dotenv()

client = Groq()
MODEL = "llama-3.3-70b-versatile"

SQL_GENERATION_SYSTEM = """You are an expert SQL assistant for a SQLite database.
Your job is to convert natural language questions into precise SQL queries.

Strict Operational Instructions:
1. Output ONLY the raw SQL query. No explanations, no markdown blocks, no backticks.
2. Use only the tables and columns provided in the schema context.
3. Robust string matching: Always transform string comparisons into case-insensitive matching rules using LOWER() and LIKE keywords, e.g., LOWER(name) LIKE '%john%'.
4. Always use explicit table aliases when joining multiple relations.
5. Never execute DDL/DML besides SELECT queries.
"""

ANSWER_INTERPRETATION_SYSTEM = """You are a master business intelligence data analyst.
Given a user's original question, the generated SQL query, and the compiled analytical results (including system-generated data insights),
provide a clear, executive-friendly response in 2-4 sentences highlighting major takeaways, metrics, or anomalies.
"""

def enrich_runtime_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Applies advanced machine learning and statistical indicators to transactional data streams on the fly."""
    columns_upper = [c.upper() for c in df.columns]
    
    # Target revenue field identification matching
    rev_col = next((c for c in df.columns if 'REVENUE' in c.upper() or 'PRICE' in c.upper() or 'TOTAL' in c.upper()), None)
    
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]) and len(df) > 1:
        # Feature 1: Z-Score Statistical Outlier Analysis
        mean_val = df[rev_col].mean()
        std_val = df[rev_col].std()
        std_val = 1 if std_val == 0 or pd.isna(std_val) else std_val
        
        df['z_score'] = ((df[rev_col] - mean_val) / std_val).round(2)
        df['is_anomaly'] = df['z_score'].apply(lambda x: "🚨 Anomaly" if abs(x) > 1.96 else "✅ Normal")
        
        # Feature 2: RFM / Percentile Segment Distribution
        try:
            df['performance_quantile'] = pd.qcut(
                df[rev_col], 
                q=min(4, len(df.drop_duplicates(subset=[rev_col]))), 
                labels=['Bronze Tier', 'Silver Tier', 'Gold Tier', 'Platinum Tier'][-min(4, len(df.drop_duplicates(subset=[rev_col]))):]
            )
        except Exception:
            df['performance_quantile'] = 'Standard Growth'
            
        # Feature 3: Growth Forecasting Vector (Next Quarter Target +12.5%)
        df['forward_target'] = (df[rev_col] * 1.125).round(2)
        
    return df

def retrieve_schema_context(question: str, index_dir: str, k: int = 3) -> str:
    vectorstore = load_vector_store(index_dir)
    docs = vectorstore.similarity_search(question, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

def generate_sql(question: str, schema_context: str) -> str:
    prompt = f"Database Schema Context:\n{schema_context}\n\nUser Question: {question}\n\nGenerate SQL:"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SQL_GENERATION_SYSTEM},
            {"role": "user",   "content": prompt}
        ],
        temperature=0
    )
    sql = response.choices[0].message.content.strip()
    return re.sub(r"```sql|```", "", sql).strip()

def execute_sql(sql: str, db_path: str) -> tuple:
    upper_sql = sql.strip().upper()
    if not upper_sql.startswith("SELECT"):
        raise ValueError("Security Violation: Only read-only SELECT sequences are permitted.")
    
    if "LIMIT" not in upper_sql:
        sql = sql.rstrip(';') + " LIMIT 150;"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    finally:
        conn.close()
    return rows, columns

def interpret_results(question: str, sql: str, rows: list, columns: list) -> str:
    if not rows:
        return "The query completed successfully but returned zero matching data matrix dimensions."
        
    df = pd.DataFrame(rows, columns=columns)
    result_text = df.head(20).to_string(index=False)

    prompt = f"User Question: {question}\n\nSQL Executed:\n{sql}\n\nProcessed Matrix Results:\n{result_text}\n\nSummarize Insights:"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ANSWER_INTERPRETATION_SYSTEM},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def ask(question: str, db_path: str, index_dir: str) -> dict:
    result = {"question": question, "schema_context": "", "sql": "", "columns": [], "rows": [], "enriched_df": None, "answer": "", "error": None}
    try:
        schema_context = retrieve_schema_context(question, index_dir)
        result["schema_context"] = schema_context
        
        sql = generate_sql(question, schema_context)
        result["sql"] = sql
        
        rows, columns = execute_sql(sql, db_path)
        result["rows"] = rows
        result["columns"] = columns
        
        # Assemble DataFrame and patch real-time feature engineering matrices
        if rows:
            base_df = pd.DataFrame(rows, columns=columns)
            enriched_df = enrich_runtime_dataframe(base_df)
            result["enriched_df"] = enriched_df
            result["columns"] = enriched_df.columns.tolist()
            result["rows"] = enriched_df.values.tolist()
            
        result["answer"] = interpret_results(question, sql, rows, columns)
    except Exception as e:
        result["error"] = str(e)
        result["answer"] = f"❌ Framework Exception Encountered: {e}"
    return result