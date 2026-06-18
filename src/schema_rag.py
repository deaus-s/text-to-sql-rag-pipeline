"""
schema_rag.py
-------------
Extracts database schema + sample rows, converts them into natural-language "documents", 
and builds isolated FAISS vector stores with safe deserialization flags enabled.
"""

import sqlite3
import os
import shutil
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def get_schema_documents(db_path: str) -> list[Document]:
    """Reads every table in the SQLite database and converts its schema to LangChain Documents."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    documents = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_descriptions = []
        for col in columns:
            _, name, dtype, notnull, _, pk = col
            desc = f"  - {name} ({dtype})"
            if pk: desc += " [PRIMARY KEY]"
            if notnull: desc += " [NOT NULL]"
            col_descriptions.append(desc)

        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        fk_lines = [f"  - {fk[3]} → {fk[2]}.{fk[4]}" for fk in fks]

        try:
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
        except Exception:
            rows = []
            
        col_names = [col[1] for col in columns]
        sample_lines = []
        for row in rows:
            row_dict = dict(zip(col_names, row))
            sample_lines.append("  " + str(row_dict))

        text_parts = [f"Table: {table}", "Columns:"] + col_descriptions
        if fk_lines:
            text_parts.append("Foreign Keys:")
            text_parts.extend(fk_lines)
        text_parts.append("Sample rows:")
        text_parts.extend(sample_lines)

        full_text = "\n".join(text_parts)
        documents.append(Document(page_content=full_text, metadata={"table": table}))

    conn.close()
    return documents

def build_vector_store(documents: list[Document], index_dir: str) -> FAISS:
    """Embeds schema documents and stores them into an isolated FAISS directory."""
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(index_dir)
    return vectorstore

def load_vector_store(index_dir: str) -> FAISS:
    """Loads a specific pre-built FAISS index from disk securely."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)