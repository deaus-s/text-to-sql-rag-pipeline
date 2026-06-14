"""
app.py — QueryMind Cyberpunk Dark UI
Run with: streamlit run app.py
"""

import sys
import os
import sqlite3
import tempfile
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from schema_rag import get_schema_documents, build_vector_store
from sql_engine import ask as run_query

load_dotenv()

st.set_page_config(page_title="QueryMind — AI Database Assistant", page_icon="⚡", layout="wide")

# Beautiful Custom Cyberpunk Dark UI Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #08070b !important;
        color: #f3f4f6 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .block-container { padding: 2rem 4rem !important; }
    
    /* Custom Header Cards */
    .main-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #312e81;
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.7);
    }
    .main-header h1 {
        font-size: 2.8rem !important;
        font-weight: 700;
        background: linear-gradient(90deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* Cards & Containers */
    div[data-testid="stVerticalBlock"] > div {
        background-color: transparent;
    }
    .content-card {
        background: #111019;
        border: 1px solid #232135;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* SQL Code Blocks */
    .sql-box {
        background: #050508 !important;
        border-left: 4px solid #a855f7 !important;
        font-family: 'JetBrains Mono', monospace !important;
        padding: 1rem;
        border-radius: 6px;
        color: #e9d5ff !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper Utilities
def get_db_schema(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    schema = {}
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t})")
        cols = cursor.fetchall()
        schema[t] = [(c[1], c[2], bool(c[5])) for c in cols]
    conn.close()
    return schema

def csv_to_sqlite(csv_file, db_path: str):
    import csv, io
    content = csv_file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows: return None
    cols = list(rows[0].keys())
    table_name = os.path.splitext(csv_file.name)[0].replace(" ", "_").lower()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
    cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
    placeholders = ", ".join(["?" for _ in cols])
    for row in rows:
        cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', [row[c] for c in cols])
    conn.commit()
    conn.close()
    return table_name

# Initialize App States
if "session_id" not in st.session_state:
    st.session_state.session_id = next(tempfile._get_candidate_names())
    st.session_state.db_path = None
    st.session_state.index_dir = None
    st.session_state.db_name = None
    st.session_state.history = []

# App Header
st.markdown("""
<div class="main-header">
    <h1>QueryMind ⚡</h1>
    <p style="color: #9ca3af; font-size: 1.1rem;">Talk directly with your custom relational data models in conversational English.</p>
</div>
""", unsafe_allow_html=True)

layout_left, layout_right = st.columns([2.5, 1], gap="large")

with layout_right:
    st.subheader("🛠️ Data Workspace")
    uploaded = st.file_uploader("Upload `.db` or `.csv` files", type=["db", "csv"])
    
    if uploaded:
        if st.session_state.db_name != uploaded.name:
            user_dir = os.path.join(tempfile.gettempdir(), st.session_state.session_id)
            os.makedirs(user_dir, exist_ok=True)
            
            target_db = os.path.join(user_dir, "isolated_source.db")
            target_index = os.path.join(user_dir, "faiss_index")
            
            with st.spinner("Processing structural data pipeline..."):
                if uploaded.name.endswith(".csv"):
                    csv_to_sqlite(uploaded, target_db)
                else:
                    with open(target_db, "wb") as f:
                        f.write(uploaded.getbuffer())
                
                docs = get_schema_documents(target_db)
                build_vector_store(docs, target_index)
                
                st.session_state.db_path = target_db
                st.session_state.index_dir = target_index
                st.session_state.db_name = uploaded.name
                st.session_state.history = []
            st.rerun()
            
    if st.session_state.db_name:
        st.success(f"Active Target: {st.session_state.db_name}")
        if st.button("Reset Session Workspace"):
            st.session_state.db_path = None
            st.session_state.index_dir = None
            st.session_state.db_name = None
            st.session_state.history = []
            st.rerun()
            
    if st.session_state.db_path:
        with st.expander("📊 Inspect Active Schema Context", expanded=True):
            schema = get_db_schema(st.session_state.db_path)
            for table, cols in schema.items():
                st.markdown(f"**🔹 Table: `{table}`**")
                for c in cols:
                    pk_marker = " 🔑" if c[2] else ""
                    st.markdown(f"- `{c[0]}` ({c[1].lower()}){pk_marker}")

with layout_left:
    st.subheader("💬 Ask Your Database")
    
    if not st.session_state.db_path:
        default_db = "data/company.db"
        if os.path.exists(default_db):
            user_dir = os.path.join(tempfile.gettempdir(), st.session_state.session_id)
            os.makedirs(user_dir, exist_ok=True)
            target_index = os.path.join(user_dir, "company_idx")
            
            if not os.path.exists(target_index):
                docs = get_schema_documents(default_db)
                build_vector_store(docs, target_index)
                
            st.session_state.db_path = default_db
            st.session_state.index_dir = target_index
            st.session_state.db_name = "sample_company.db"
            st.rerun()
        else:
            st.info("Please upload a .db or .csv database file on the sidebar workspace to get started.")
            
    if st.session_state.db_path:
        with st.form("query_form", clear_on_submit=True):
            user_prompt = st.text_input("Enter natural text prompt:", placeholder="e.g., Return top 5 staff tiers by pay scale")
            submit_btn = st.form_submit_button("Run Analytics Engine")
            
        if submit_btn and user_prompt.strip():
            with st.spinner("Analyzing semantics & executing execution query..."):
                response_payload = run_query(user_prompt.strip(), st.session_state.db_path, st.session_state.index_dir)
                st.session_state.history.insert(0, response_payload)
                
        for run in st.session_state.history:
            st.markdown(f"### Q: {run['question']}")
            if run["error"]:
                st.error(run["answer"])
            else:
                st.markdown(f"💡 **Analysis:** {run['answer']}")
                
                with st.expander("View Execution Metrics"):
                    st.markdown("**Generated Execution String:**")
                    st.code(run["sql"], language="sql")
                    
                    if run["rows"]:
                        st.markdown("**Resulting Matrix View:**")
                        df_res = pd.DataFrame(run["rows"], columns=run["columns"])
                        st.dataframe(df_res, use_container_width=True)
            st.markdown("---")