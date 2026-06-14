"""
app.py — Redesigned Professional Dark UI
Run with: streamlit run app.py
"""

import sys, os, sqlite3, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="QueryMind — AI Database Assistant",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── DESIGN SYSTEM ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0f !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stAppViewContainer"] > .main { background: #0a0a0f !important; }
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: #2d2d3d; border-radius: 2px; }

/* ── Top Nav ── */
.qm-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2.5rem;
    border-bottom: 1px solid #1e1e2e;
    background: #0d0d14;
    position: sticky;
    top: 0;
    z-index: 100;
}
.qm-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #e2e8f0;
}
.qm-logo-hex {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; color: white; font-weight: 700;
}
.qm-nav-right { display: flex; align-items: center; gap: 1rem; }
.qm-badge {
    background: #1a1a2e;
    border: 1px solid #2d2d4e;
    color: #7c7c9e;
    font-size: 0.72rem;
    padding: 0.25rem 0.6rem;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Hero ── */
.qm-hero {
    padding: 3.5rem 2.5rem 2rem;
    max-width: 860px;
}
.qm-hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.25);
    color: #818cf8;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    margin-bottom: 1.2rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.qm-hero h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    line-height: 1.15 !important;
    letter-spacing: -0.03em !important;
    color: #f1f5f9 !important;
    margin-bottom: 0.75rem !important;
}
.qm-hero h1 span {
    background: linear-gradient(135deg, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.qm-hero p {
    font-size: 1rem !important;
    color: #64748b !important;
    line-height: 1.6 !important;
    max-width: 520px !important;
}

/* ── Layout ── */
.qm-layout {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 0;
    min-height: calc(100vh - 200px);
    border-top: 1px solid #1e1e2e;
}
.qm-main { padding: 2rem 2.5rem; border-right: 1px solid #1e1e2e; }
.qm-panel { padding: 1.5rem; background: #0d0d14; }

/* ── Upload Zone ── */
.qm-upload-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.6rem;
    display: block;
}

[data-testid="stFileUploader"] {
    background: #111120 !important;
    border: 1.5px dashed #2d2d4e !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #6366f1 !important;
}
[data-testid="stFileUploadDropzone"] {
    background: transparent !important;
    color: #475569 !important;
}

/* ── Input ── */
.qm-input-wrap { margin: 1.5rem 0 1rem; position: relative; }
[data-testid="stTextInput"] input {
    background: #111120 !important;
    border: 1.5px solid #1e1e2e !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.85rem 1rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #374151 !important; }

/* ── Ask Button ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 1.8rem !important;
    letter-spacing: 0.01em !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary buttons ── */
[data-testid="stButton"] > button:not([kind="primary"]) {
    background: #111120 !important;
    color: #64748b !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    padding: 0.35rem 0.8rem !important;
    transition: all 0.15s !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: #6366f1 !important;
    color: #818cf8 !important;
}

/* ── Result Cards ── */
.qm-result {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    transition: border-color 0.2s;
}
.qm-result:hover { border-color: #2d2d4e; }
.qm-question {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.5rem;
}
.qm-answer {
    font-size: 0.98rem;
    color: #cbd5e1;
    line-height: 1.65;
    margin-bottom: 1rem;
    padding-left: 0.8rem;
    border-left: 2px solid #6366f1;
}
.qm-answer-error {
    font-size: 0.95rem;
    color: #f87171;
    line-height: 1.65;
    padding-left: 0.8rem;
    border-left: 2px solid #ef4444;
}
.qm-sql-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #374151;
    margin-bottom: 0.4rem;
    margin-top: 0.8rem;
}
.qm-sql {
    background: #080810;
    border: 1px solid #1a1a2e;
    border-radius: 8px;
    padding: 0.9rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #a78bfa;
    overflow-x: auto;
    white-space: pre;
    line-height: 1.6;
}

/* ── Panel Sections ── */
.qm-panel-section {
    margin-bottom: 1.8rem;
}
.qm-panel-title {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #374151;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1a1a2e;
}

/* ── Schema Tree ── */
.qm-table-name {
    font-size: 0.82rem;
    font-weight: 600;
    color: #818cf8;
    font-family: 'JetBrains Mono', monospace;
    margin: 0.6rem 0 0.3rem;
}
.qm-col-item {
    font-size: 0.75rem;
    color: #475569;
    font-family: 'JetBrains Mono', monospace;
    padding: 0.15rem 0 0.15rem 0.8rem;
    border-left: 1px solid #1e1e2e;
    margin-left: 0.4rem;
}
.qm-col-pk { color: #f59e0b; }
.qm-col-fk { color: #34d399; }

/* ── Toggles ── */
[data-testid="stToggle"] { margin-bottom: 0.3rem !important; }
[data-testid="stToggle"] label { font-size: 0.8rem !important; color: #475569 !important; }
[data-testid="stToggle"] span { font-size: 0.8rem !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    margin-top: 0.8rem !important;
}

/* ── Empty state ── */
.qm-empty {
    text-align: center;
    padding: 4rem 2rem;
    color: #1e1e2e;
}
.qm-empty-icon { font-size: 2.5rem; margin-bottom: 1rem; opacity: 0.3; }
.qm-empty-text { font-size: 0.9rem; color: #2d2d4e; }

/* ── Help modal ── */
.qm-help-section { margin-bottom: 1rem; }
.qm-help-step {
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
    margin-bottom: 0.7rem;
}
.qm-help-num {
    background: rgba(99,102,241,0.15);
    color: #818cf8;
    border-radius: 50%;
    width: 22px; height: 22px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
}
.qm-help-text { font-size: 0.82rem; color: #64748b; line-height: 1.5; }
.qm-help-text strong { color: #94a3b8; }

/* ── Status dot ── */
.qm-status {
    display: inline-flex; align-items: center; gap: 0.4rem;
    font-size: 0.72rem; color: #475569;
}
.qm-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #22c55e;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ─────────────────────────────────────────────────────────────────
def get_db_schema(db_path: str) -> dict:
    """Returns {table: [(col_name, type, is_pk, is_fk)]}"""
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    schema = {}
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t})")
        cols = cursor.fetchall()
        cursor.execute(f"PRAGMA foreign_key_list({t})")
        fk_cols = {fk[3] for fk in cursor.fetchall()}
        schema[t] = [(c[1], c[2], bool(c[5]), c[1] in fk_cols) for c in cols]
    conn.close()
    return schema

def csv_to_sqlite(csv_file, db_path: str):
    """Converts uploaded CSV to a SQLite table."""
    import csv, io
    content = csv_file.read().decode("utf-8")
    reader  = csv.DictReader(io.StringIO(content))
    rows    = list(reader)
    if not rows:
        raise ValueError("CSV file is empty.")
    cols    = list(rows[0].keys())
    table   = os.path.splitext(csv_file.name)[0].replace(" ", "_").lower()
    conn    = sqlite3.connect(db_path)
    cursor  = conn.cursor()
    col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')
    placeholders = ", ".join(["?" for _ in cols])
    for row in rows:
        cursor.execute(f'INSERT INTO "{table}" VALUES ({placeholders})',
                       [row[c] for c in cols])
    conn.commit()
    conn.close()
    return table


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "history"      not in st.session_state: st.session_state.history      = []
if "db_path"      not in st.session_state: st.session_state.db_path      = None
if "db_name"      not in st.session_state: st.session_state.db_name      = None
if "schema"       not in st.session_state: st.session_state.schema       = {}
if "show_help"    not in st.session_state: st.session_state.show_help    = False
if "index_built"  not in st.session_state: st.session_state.index_built  = False


# ── TOP NAV ──────────────────────────────────────────────────────────────────
col_nav1, col_nav2 = st.columns([1, 1])
with col_nav1:
    st.markdown("""
    <div class="qm-nav">
        <div class="qm-logo">
            <div class="qm-logo-hex">Q</div>
            QueryMind
        </div>
        <div class="qm-nav-right">
            <span class="qm-badge">RAG · Groq · SQLite</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Render nav across full width
st.markdown("""
<div class="qm-nav" style="margin-top:-3rem">
    <div class="qm-logo">
        <div class="qm-logo-hex">Q</div>
        QueryMind
    </div>
    <div class="qm-nav-right">
        <span class="qm-badge">RAG · Groq · SQLite</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="qm-hero">
    <div class="qm-hero-tag">⬡ AI-Powered</div>
    <h1>Ask your database<br><span>anything.</span></h1>
    <p>Upload a database or CSV file and query it in plain English.
    No SQL knowledge required.</p>
</div>
""", unsafe_allow_html=True)


# ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
left, right = st.columns([3, 1.1], gap="small")

# ═══════════════════════════════════════════
# RIGHT PANEL
# ═══════════════════════════════════════════
with right:
    st.markdown('<div class="qm-panel">', unsafe_allow_html=True)

    # ── Help toggle ──
    help_col1, help_col2 = st.columns([3,1])
    with help_col1:
        st.markdown('<div class="qm-panel-title">Controls</div>', unsafe_allow_html=True)
    with help_col2:
        if st.button("❓ Help", key="help_btn"):
            st.session_state.show_help = not st.session_state.show_help

    # ── Help modal ──
    if st.session_state.show_help:
        with st.expander("How QueryMind works", expanded=True):
            st.markdown("""
<div class="qm-help-section">
<div class="qm-help-step">
  <div class="qm-help-num">1</div>
  <div class="qm-help-text"><strong>Upload</strong> a SQLite .db or .csv file using the upload panel</div>
</div>
<div class="qm-help-step">
  <div class="qm-help-num">2</div>
  <div class="qm-help-text"><strong>Type</strong> any question in plain English about your data</div>
</div>
<div class="qm-help-step">
  <div class="qm-help-num">3</div>
  <div class="qm-help-text"><strong>RAG</strong> retrieves the most relevant parts of your schema</div>
</div>
<div class="qm-help-step">
  <div class="qm-help-num">4</div>
  <div class="qm-help-text"><strong>Llama 3</strong> writes a SQL query based on your question</div>
</div>
<div class="qm-help-step">
  <div class="qm-help-num">5</div>
  <div class="qm-help-text"><strong>Results</strong> are interpreted and explained in plain English</div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── Display toggles ──
    st.markdown('<div class="qm-panel-title" style="margin-top:1rem">Display</div>', unsafe_allow_html=True)
    show_sql   = st.toggle("Show SQL query",    value=True)
    show_table = st.toggle("Show result table", value=True)

    st.divider()

    # ── File upload ──
    st.markdown('<div class="qm-panel-title">Database</div>', unsafe_allow_html=True)

    # Status
    if st.session_state.db_name:
        st.markdown(f"""
        <div class="qm-status">
            <div class="qm-dot"></div>
            {st.session_state.db_name}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(" ")
        if st.button("⟳ Change database"):
            st.session_state.db_path     = None
            st.session_state.db_name     = None
            st.session_state.schema      = {}
            st.session_state.index_built = False
            st.session_state.history     = []
            st.rerun()
    else:
        uploaded = st.file_uploader(
            "Upload database",
            type=["db", "csv"],
            label_visibility="collapsed"
        )

        if uploaded:
            tmp_dir = tempfile.mkdtemp()
            db_path = os.path.join(tmp_dir, "user_db.db")

            if uploaded.name.endswith(".csv"):
                with st.spinner("Converting CSV..."):
                    csv_to_sqlite(uploaded, db_path)
            else:
                with open(db_path, "wb") as f:
                    f.write(uploaded.read())

            st.session_state.db_path     = db_path
            st.session_state.db_name     = uploaded.name
            st.session_state.schema      = get_db_schema(db_path)
            st.session_state.index_built = False
            st.session_state.history     = []
            st.rerun()

        st.markdown('<div class="qm-empty-text" style="font-size:0.75rem;color:#2d2d4e;margin-top:0.5rem">↑ Upload a .db or .csv file to begin</div>', unsafe_allow_html=True)

    # ── Schema explorer ──
    if st.session_state.schema:
        st.divider()
        st.markdown('<div class="qm-panel-title">Schema</div>', unsafe_allow_html=True)
        for table, cols in st.session_state.schema.items():
            st.markdown(f'<div class="qm-table-name">⬡ {table}</div>', unsafe_allow_html=True)
            for col_name, col_type, is_pk, is_fk in cols:
                css_class = "qm-col-pk" if is_pk else ("qm-col-fk" if is_fk else "")
                icon = "🔑 " if is_pk else ("⇢ " if is_fk else "· ")
                st.markdown(
                    f'<div class="qm-col-item {css_class}">{icon}{col_name} <span style="opacity:0.4">({col_type})</span></div>',
                    unsafe_allow_html=True
                )

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
# LEFT MAIN
# ═══════════════════════════════════════════
with left:
    st.markdown('<div class="qm-main">', unsafe_allow_html=True)

    # ── Build vector index when DB is loaded ──
  # ── Build vector index when DB is loaded ──
    if st.session_state.db_path and not st.session_state.index_built:
        import shutil
        from schema_rag import get_schema_documents, build_vector_store
        with st.spinner("Building search index for your database..."):
            if os.path.exists("data/faiss_index"):
                shutil.rmtree("data/faiss_index")
            docs = get_schema_documents(st.session_state.db_path)
            build_vector_store(docs)
            st.session_state.index_built = True

    # ── Default DB (sample) ──
  # ── Default DB (sample) — only if nothing uploaded ──
    if not st.session_state.db_path:
        from setup_database import create_database
        from schema_rag import get_schema_documents, build_vector_store
        default_db = "data/company.db"
        if not os.path.exists(default_db):
            create_database()
        with st.spinner("Loading sample database..."):
            docs = get_schema_documents(default_db)
            build_vector_store(docs)
            st.session_state.db_path     = default_db
            st.session_state.db_name     = "sample_company.db"
            st.session_state.schema      = get_db_schema(default_db)
            st.session_state.index_built = True

    # ── Rebuild index for uploaded DB ──
    elif not st.session_state.index_built:
        import shutil
        from schema_rag import get_schema_documents, build_vector_store
        with st.spinner("Building search index for your database..."):
            if os.path.exists("data/faiss_index"):
                shutil.rmtree("data/faiss_index")
            docs = get_schema_documents(st.session_state.db_path)
            build_vector_store(docs)
            st.session_state.index_built = True

    # ── Question input ──
    st.markdown('<div class="qm-input-wrap">', unsafe_allow_html=True)
    prefill  = st.session_state.pop("prefill", "")
    question = st.text_input(
        "question",
        value=prefill,
        placeholder="e.g.  Who are the top 5 highest paid employees?",
        label_visibility="collapsed",
        key="question_input"
    )

    btn_col1, btn_col2, btn_col3 = st.columns([1, 5, 1])
    with btn_col1:
        ask_btn = st.button("⬡ Ask", type="primary")
    with btn_col3:
        if st.button("Clear"):
            st.session_state.history = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Quick examples ──
    if not st.session_state.history:
        st.markdown('<div style="margin-bottom:0.5rem"><span style="font-size:0.72rem;color:#2d2d4e;letter-spacing:0.06em;text-transform:uppercase;font-weight:600">Try these →</span></div>', unsafe_allow_html=True)
        examples = [
            "Who are the top 5 highest paid employees?",
            "What is the total revenue per region?",
            "Which products are low on stock?",
            "How many employees per department?",
        ]
        ex_cols = st.columns(2)
        for i, eq in enumerate(examples):
            if ex_cols[i % 2].button(eq, key=f"ex_{i}"):
                st.session_state["prefill"] = eq
                st.rerun()

    # ── Handle query ──
    if ask_btn and question.strip():
        from sql_engine import ask as run_query
        with st.spinner("Querying..."):
            result = run_query(question.strip())
        st.session_state.history.insert(0, result)
        st.rerun()

    # ── Results ──
    if st.session_state.history:
        for result in st.session_state.history:
            st.markdown('<div class="qm-result">', unsafe_allow_html=True)

            st.markdown(f'<div class="qm-question">Question</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.95rem;color:#94a3b8;margin-bottom:0.8rem">{result["question"]}</div>', unsafe_allow_html=True)

            if result["error"]:
                st.markdown(f'<div class="qm-answer-error">{result["answer"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="qm-answer">{result["answer"]}</div>', unsafe_allow_html=True)

            if show_sql and result.get("sql"):
                st.markdown('<div class="qm-sql-label">Generated SQL</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="qm-sql">{result["sql"]}</div>', unsafe_allow_html=True)

            if show_table and result.get("rows") and not result["error"]:
                df = pd.DataFrame(result["rows"], columns=result["columns"])
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="qm-empty">
            <div class="qm-empty-icon">⬡</div>
            <div class="qm-empty-text">Ask a question above to query your database</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
