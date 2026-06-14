"""
app.py
------
Streamlit UI for the Text-to-SQL RAG system.
Run with: streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
from sql_engine import ask
from setup_database import create_database
from schema_rag import get_schema_documents, build_vector_store
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Database Assistant",
    page_icon="🗄️",
    layout="wide"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .sql-box {
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    .answer-box {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem 1.2rem;
        border-radius: 4px;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    .error-box {
        background: #fff1f2;
        border-left: 4px solid #ef4444;
        padding: 1rem 1.2rem;
        border-radius: 4px;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    .stTextInput > div > div > input {
        font-size: 1rem;
        padding: 0.6rem;
    }
    .example-chip {
        display: inline-block;
        background: #e0e7ff;
        color: #3730a3;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.82rem;
        margin: 0.2rem;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)


# ── Initialize DB + Vector Store ─────────────────────────────────────────────
@st.cache_resource(show_spinner="Setting up database & vector index...")
def initialize():
    create_database()
    docs = get_schema_documents()
    build_vector_store(docs)
    return True

initialize()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗄️ Database Tables")
    st.markdown("""
    **employees**
    - id, name, department, role
    - salary, hire_date, city

    **products**
    - id, name, category, price
    - stock, supplier

    **sales**
    - id, product_id, employee_id
    - quantity, total_price
    - sale_date, region
    """)

    st.divider()
    st.markdown("## ⚙️ How it works")
    st.markdown("""
    1. Your question is **embedded** into a vector
    2. **RAG** retrieves relevant schema chunks
    3. **GPT-4o** writes the SQL query
    4. Query runs on **SQLite**
    5. GPT-4o **interprets** the results
    """)

    st.divider()
    show_sql     = st.toggle("Show generated SQL",     value=True)
    show_schema  = st.toggle("Show retrieved schema",  value=False)
    show_table   = st.toggle("Show raw result table",  value=True)


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🗄️ AI Database Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ask anything about your database in plain English — powered by RAG + GPT-4o</div>', unsafe_allow_html=True)

# Example questions
example_questions = [
    "Who are the top 5 highest paid employees?",
    "How many employees are in each department?",
    "What is the total revenue per region?",
    "Which products are low on stock (less than 100)?",
    "Show all sales made in March 2024",
    "What is the average salary in Engineering?",
    "Which employee made the most sales?",
    "List all products in the Electronics category",
]

st.markdown("**Try an example:**")
cols = st.columns(4)
for i, eq in enumerate(example_questions):
    if cols[i % 4].button(eq, key=f"ex_{i}", use_container_width=True):
        st.session_state["prefill"] = eq

# Text input
prefill = st.session_state.pop("prefill", "")
question = st.text_input(
    "Your question:",
    value=prefill,
    placeholder="e.g. What is the total revenue by region?",
    label_visibility="collapsed"
)

ask_btn = st.button("🔍 Ask", type="primary", use_container_width=False)

# ── Chat History ──────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

if ask_btn and question.strip():
    with st.spinner("Thinking..."):
        result = ask(question.strip())
    st.session_state.history.insert(0, result)

# ── Display Results ───────────────────────────────────────────────────────────
for result in st.session_state.history:
    with st.container():
        st.markdown(f"### 💬 {result['question']}")

        if result["error"]:
            st.markdown(f'<div class="error-box">{result["answer"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="answer-box">{result["answer"]}</div>', unsafe_allow_html=True)

        if show_sql and result["sql"]:
            st.markdown("**Generated SQL:**")
            st.markdown(f'<div class="sql-box">{result["sql"]}</div>', unsafe_allow_html=True)

        if show_schema and result["schema_context"]:
            with st.expander("Retrieved Schema Context"):
                st.code(result["schema_context"], language="text")

        if show_table and result["rows"] and not result["error"]:
            df = pd.DataFrame(result["rows"], columns=result["columns"])
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

if not st.session_state.history:
    st.info("👆 Type a question above or click one of the example buttons to get started.")
