"""
sql_engine.py
-------------
Orchestrates AI-driven SQL assembly, database query safety filters,
and analytical interpretations.
"""

import sqlite3
import re
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
3. Cryptic naming protection: Map fuzzy real-world text targets to matching system elements creatively.
4. Robust string matching: To avoid case mismatch errors with real-world inputs, always transform string comparisons into case-insensitive matching rules using LOWER() and LIKE keywords, e.g., LOWER(name) LIKE '%john%'.
5. Always use table aliases when joining.
6. Never execute DDL/DML besides SELECT statements.
"""

ANSWER_INTERPRETATION_SYSTEM = """You are a helpful data analyst assistant.
Given a user's original question, the SQL query that was run, and the raw results,
provide a clear, concise, human-friendly answer in 2-4 sentences. Include metrics from the results.
"""

def retrieve_schema_context(question: str, index_dir: str, k: int = 3) -> str:
    """Retrieves only the schema chunks that match the incoming question profile."""
    vectorstore = load_vector_store(index_dir)
    docs = vectorstore.similarity_search(question, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

def generate_sql(question: str, schema_context: str) -> str:
    """Uses Groq API to compile text questions to optimized raw SQL rows."""
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
    """Executes the verified read-only SELECT command sequences over the targeted DB node."""
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("Security Violation: Only read-only SELECT sequences are permitted.")

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
    """Generates the descriptive text analysis summary insight row."""
    if not rows:
        result_text = "The query returned no results."
    else:
        header = " | \".join(columns)"
        lines = [header, "-" * len(header)]
        for row in rows[:20]:
            lines.append(" | ".join(str(v) for v in row))
        result_text = "\n".join(lines)

    prompt = f"User Question: {question}\n\nSQL Executed:\n{sql}\n\nResults:\n{result_text}\n\nSummarize:"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ANSWER_INTERPRETATION_SYSTEM},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def ask(question: str, db_path: str, index_dir: str) -> dict:
    """Main entry point. Orchestrates schema RAG, query generation, and response parsing."""
    result = {"question": question, "schema_context": "", "sql": "", "columns": [], "rows": [], "answer": "", "error": None}
    try:
        schema_context = retrieve_schema_context(question, index_dir)
        result["schema_context"] = schema_context
        sql = generate_sql(question, schema_context)
        result["sql"] = sql
        rows, columns = execute_sql(sql, db_path)
        result["rows"] = rows
        result["columns"] = columns
        result["answer"] = interpret_results(question, sql, rows, columns)
    except Exception as e:
        result["error"] = str(e)
        result["answer"] = f"❌ Exception Error Encountered: {e}"
    return result