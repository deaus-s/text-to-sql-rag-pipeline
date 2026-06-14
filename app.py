"""
app.py — QueryMind Enterprise Dark Analytics Suite
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
from sql_engine import ask as run_query, execute_sql, interpret_results

load_dotenv()

st.set_page_config(page_title="QueryMind Enterprise — AI Engine", page_icon="⚡", layout="wide")

# Enhanced Premium Cyberpunk Interface Stylings
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #060509 !important;
        color: #f3f4f6 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .block-container { padding: 2rem 4rem !important; }
    
    .main-header {
        background: linear-gradient(135deg, #16122c 0%, #090b14 100%);
        border: 1px solid #281f54;
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 35px -12px rgba(0,0,0,0.8);
    }
    .main-header h1 {
        font-size: 2.9rem !important;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .pill-container {
        display: flex;
        gap: 10px;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

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

# Setup App States
if "session_id" not in st.session_state:
    st.session_state.session_id = next(tempfile._get_candidate_names())
    st.session_state.db_path = None
    st.session_state.index_dir = None
    st.session_state.db_name = None
    st.session_state.history = []
    st.session_state.pill_input = ""

# Main Layout Render
st.markdown("""
<div class="main-header">
    <h1>QueryMind Enterprise ⚡</h1>
    <p style="color: #a1a1aa; font-size: 1.1rem;">Talk directly with unstructured data matrices using case-insensitive semantic interpretation pipelines.</p>
</div>
""", unsafe_allow_html=True)

layout_left, layout_right = st.columns([2.4, 1], gap="large")

with layout_right:
    st.subheader("🛠️ File System Sandbox")
    uploaded = st.file_uploader("Upload active working `.db` or `.csv` sets", type=["db", "csv"])
    
    if uploaded and st.session_state.db_name != uploaded.name:
        user_dir = os.path.join(tempfile.gettempdir(), st.session_state.session_id)
        os.makedirs(user_dir, exist_ok=True)
        
        target_db = os.path.join(user_dir, "isolated_source.db")
        target_index = os.path.join(user_dir, "faiss_index")
        
        # Real-time layered loader status timeline animation
        with st.status("Initializing Data Infrastructure Core...", expanded=True) as state_tracker:
            state_tracker.write("Extracting tabular data dimensions...")
            if uploaded.name.endswith(".csv"):
                csv_to_sqlite(uploaded, target_db)
            else:
                with open(target_db, "wb") as f:
                    f.write(uploaded.getbuffer())
            
            state_tracker.write("Building dynamic neural FAISS semantic metadata arrays...")
            docs = get_schema_documents(target_db)
            build_vector_store(docs, target_index)
            
            st.session_state.db_path = target_db
            st.session_state.index_dir = target_index
            st.session_state.db_name = uploaded.name
            st.session_state.history = []
            state_tracker.update(label="Structural Pipeline Fully Synced!", state="complete")
        st.rerun()

    if st.session_state.db_name:
        st.success(f"Target Cluster: {st.session_state.db_name}")
        if st.button("Purge Active Session Cache"):
            st.session_state.db_path = None
            st.session_state.index_dir = None
            st.session_state.db_name = None
            st.session_state.history = []
            st.rerun()
            
    if st.session_state.db_path:
        with st.expander("📊 Structural Database Meta Schema Explorer", expanded=True):
            schema = get_db_schema(st.session_state.db_path)
            for table, cols in schema.items():
                st.markdown(f"**🔹 Table Name: `{table}`**")
                for c in cols:
                    pk_marker = " 🔑 [PK]" if c[2] else ""
                    st.markdown(f"- `{c[0]}` ({c[1].lower()}){pk_marker}")

with layout_left:
    st.subheader("💬 Natural Language Engine Workspace")
    
    # Auto fallback connection checking loops
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
            st.info("Drop target data configurations in the side channel interface block to establish processing connections.")

    if st.session_state.db_path:
        # UX Enhancement: Pre-configured sample question pills
        st.markdown("<p style='color:#a1a1aa; font-size:0.9rem; margin-bottom: 2px;'>Quick Analytics Shortcuts:</p>", unsafe_allow_html=True)
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            if st.button("📊 Headcount by Department", use_container_width=True):
                st.session_state.pill_input = "Show total headcount grouped by departments"
        with cp2:
            if st.button("💰 Top 5 Compensations", use_container_width=True):
                st.session_state.pill_input = "Show top 5 employees with the highest salary tiers"
        with cp3:
            if st.button("🗺️ Geographic Revenue Metrics", use_container_width=True):
                st.session_state.pill_input = "Calculate cumulative financial totals across regions"

        # Search Query processing configuration block
        with st.form("query_workspace_form", clear_on_submit=False):
            search_value = st.session_state.pill_input if st.session_state.pill_input else ""
            user_prompt = st.text_input("Ask anything regarding data records:", value=search_value, placeholder="Search criteria (e.g., list managers in Hyderabad city block)...")
            submit_btn = st.form_submit_button("Launch Cognitive Extraction Pipeline")
            
        if submit_btn and user_prompt.strip():
            st.session_state.pill_input = ""  # Reset suggestion states cleanly
            with st.spinner("Processing semantics & executing query..."):
                response_payload = run_query(user_prompt.strip(), st.session_state.db_path, st.session_state.index_dir)
                st.session_state.history.insert(0, response_payload)
                st.rerun()
                
        # Interactive History Execution Layer Displays
        for idx, run in enumerate(st.session_state.history):
            st.markdown(f"### Q: {run['question']}")
            if run["error"]:
                st.error(run["answer"])
            else:
                st.markdown(f"💡 **Analysis Summary:** {run['answer']}")
                
                with st.expander("🛠️ Modify Generated Code & Diagnostic Core Metrics", expanded=False):
                    st.markdown("**Editable Generated Target SQL Block:**")
                    custom_sql_input = st.text_area("Live SQL Editing Command Console", value=run["sql"], key=f"sql_mod_{idx}")
                    
                    if st.button("Force Re-Run Adjustments", key=f"rerun_btn_{idx}"):
                        with st.spinner("Re-executing custom code overrides..."):
                            try:
                                r_rows, r_cols = execute_sql(custom_sql_input, st.session_state.db_path)
                                run["sql"] = custom_sql_input
                                run["rows"] = r_rows
                                run["columns"] = r_cols
                                run["answer"] = interpret_results(run["question"], custom_sql_input, r_rows, r_cols)
                                st.success("Query updated!")
                                st.rerun()
                            except Exception as interactive_err:
                                st.error(f"Custom Query Error: {interactive_err}")
                    
                    if run["rows"]:
                        st.markdown("**Tabular Output Matrix:**")
                        df_res = pd.DataFrame(run["rows"], columns=run["columns"])
                        st.dataframe(df_res, use_container_width=True, hide_index=True)
                        
                        # UX Enhancement: Auto Data Visualization Detection Mapping Engine
                        numeric_cols = df_res.select_dtypes(include=['number']).columns.tolist()
                        categorical_cols = df_res.select_dtypes(include=['object', 'string']).columns.tolist()
                        
                        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                            st.markdown("**📈 Auto-Generated Business Trends Analysis Visualization:**")
                            chart_df = df_res.set_index(categorical_cols[0])[numeric_cols[:1]]
                            st.bar_chart(chart_df, use_container_width=True)
            st.markdown("---")