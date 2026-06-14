import sqlite3
import os
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

DB_PATH   = "data/company.db"
INDEX_DIR = "data/faiss_index"

def get_schema_documents(db_path: str = DB_PATH) -> list:
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    documents = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_descriptions = []
        for col in columns:
            col_id, name, dtype, notnull, default, pk = col
            desc = f"  - {name} ({dtype})"
            if pk: desc += " [PRIMARY KEY]"
            if notnull: desc += " [NOT NULL]"
            col_descriptions.append(desc)
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        fk_lines = [f"  - {fk[3]} -> {fk[2]}.{fk[4]}" for fk in fks]
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        col_names = [col[1] for col in columns]
        sample_lines = ["  " + str(dict(zip(col_names, row))) for row in rows]
        text_parts = [f"Table: {table}", "Columns:"] + col_descriptions
        if fk_lines:
            text_parts += ["Foreign Keys:"] + fk_lines
        text_parts += ["Sample rows:"] + sample_lines
        documents.append(Document(
            page_content="\n".join(text_parts),
            metadata={"table": table}
        ))
    conn.close()
    return documents

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vector_store(documents: list) -> FAISS:
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(INDEX_DIR)
    print(f"FAISS index saved to: {INDEX_DIR}")
    return vectorstore

def load_vector_store() -> FAISS:
    embeddings = get_embeddings()
    return FAISS.load_local(
        INDEX_DIR, embeddings,
        allow_dangerous_deserialization=True
    )

def get_or_build_vector_store() -> FAISS:
    if os.path.exists(INDEX_DIR):
        return load_vector_store()
    docs = get_schema_documents()
    return build_vector_store(docs)
