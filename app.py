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
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .main-header h1 {
        font-size: 2.5rem !important;
        font-weight: 700;
        background: linear-gradient(90deg, #a855f7, #f43f5e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
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
        schema[t] = [(c[1], c[2]) for c in cols]
    conn.close()
    return schema

if "session_id" not in st.session_state:
    st.session_state.session_id = next(tempfile._get_candidate_names())
    st.session_state.db_path = None
    st.session_state.index_dir = None
    st.session_state.db_name = None
    st.session_state.history = []

st.markdown("""
<div class="main-header">
    <h1>QueryMind Enterprise AI Engine ⚡</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; margin: 0;">Talk to your business database using natural language and automatically generate analytical insights.</p>
</div>
""", unsafe_allow_html=True)

layout_left, layout_right = st.columns([3, 1], gap="large")

with layout_right:
    st.markdown("### 🛠️ Infrastructure Connect")
    uploaded = st.file_uploader("Upload local SQLite database (`.db`)", type=["db"])
    
    if uploaded and st.session_state.db_name != uploaded.name:
        user_dir = os.path.join(tempfile.gettempdir(), st.session_state.session_id)
        os.makedirs(user_dir, exist_ok=True)
        target_db = os.path.join(user_dir, "source.db")
        target_index = os.path.join(user_dir, "faiss_index")
        
        with open(target_db, "wb") as f:
            f.write(uploaded.getbuffer())
            
        with st.spinner("Analyzing Database Schema..."):
            docs = get_schema_documents(target_db)
            build_vector_store(docs, target_index)
            
        st.session_state.db_path = target_db
        st.session_state.index_dir = target_index
        st.session_state.db_name = uploaded.name
        st.session_state.history = []
        st.rerun()

    if st.session_state.db_name:
        st.success(f"Connected to: **{st.session_state.db_name}**")
        if st.button("Reset Session Connection", use_container_width=True):
            st.session_state.db_path = None
            st.session_state.index_dir = None
            st.session_state.db_name = None
            st.session_state.history = []
            st.rerun()
            
    if st.session_state.db_path:
        with st.expander("📊 Inspected Database Schema Matrix", expanded=False):
            schema = get_db_schema(st.session_state.db_path)
            for table, cols in schema.items():
                st.markdown(f"**Table:** `{table}`")
                for c in cols:
                    st.markdown(f"- {c[0]} *({c[1].lower()})*")

with layout_left:
    st.markdown("### 💬 Natural Language Workspace Query Terminal")
    
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
            st.warning("Please upload a `.db` file in the sidebar to initialize the AI analysis layer.")

    if st.session_state.db_path:
        user_prompt = st.text_input("Ask anything about your data (e.g., 'What is our total revenue by region?')")
        if st.button("Execute Intelligence Query", type="primary"):
            if user_prompt.strip():
                with st.spinner("AI is generating SQL & summarizing results..."):
                    payload = run_query(user_prompt.strip(), st.session_state.db_path, st.session_state.index_dir)
                    st.session_state.history.insert(0, payload)
                    st.rerun()
                    
        for idx, run in enumerate(st.session_state.history):
            with st.container():
                st.markdown(f"#### 🤔 Question: *\"{run['question']}\"*")
                if run["error"]:
                    st.error(f"Error Encountered: {run['error']}")
                else:
                    st.markdown(f"💡 **AI Summary Takeaway:** {run['answer']}")
                    
                    with st.expander("🛠️ View Executed SQL Query Engine Terminal", expanded=False):
                        custom_sql = st.text_area("SQL Code Editor Override", value=run["sql"], key=f"sql_{idx}")
                        if st.button("Re-run Modified SQL Override", key=f"btn_{idx}"):
                            try:
                                r_rows, r_cols = execute_sql(custom_sql, st.session_state.db_path)
                                run["sql"] = custom_sql
                                run["rows"] = r_rows
                                run["columns"] = r_cols
                                run["answer"] = interpret_results(run["question"], custom_sql, r_rows, r_cols)
                                st.success("Query updated!")
                                st.rerun()
                            except Exception as interactive_err:
                                st.error(f"Custom Query Error: {interactive_err}")
                    
                    if run["rows"]:
                        st.markdown("**Tabular Output Matrix:**")
                        df_res = pd.DataFrame(run["rows"], columns=run["columns"])
                        st.dataframe(df_res, use_container_width=True, hide_index=True)
                        
                        # Data Visualization Layer
                        numeric_cols = df_res.select_dtypes(include=['number']).columns.tolist()
                        categorical_cols = df_res.select_dtypes(include=['object', 'string']).columns.tolist()
                        
                        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                            st.markdown("**📈 Auto-Generated Business Trends Analysis Visualization:**")
                            chart_df = df_res.set_index(categorical_cols[0])[numeric_cols[:1]]
                            st.bar_chart(chart_df, use_container_width=True)
            st.markdown("---")