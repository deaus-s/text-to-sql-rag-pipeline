# 🗄️ AI That Talks to Your Database
### Text-to-SQL using RAG + GPT-4o + FAISS + Streamlit

Ask any question in plain English. The AI writes the SQL, runs it, and explains the result.

---

## 🏗️ Architecture

```
User Question
     │
     ▼
[Embed Question]  ──OpenAI text-embedding-3-small──►  vector
     │
     ▼
[FAISS Vector Store]  ──similarity search──►  top-k schema chunks  (RAG)
     │
     ▼
[GPT-4o]  ←── question + schema context  ──►  SQL Query
     │
     ▼
[SQLite]  ──execute──►  raw rows
     │
     ▼
[GPT-4o]  ──interpret──►  Human-friendly Answer
```

---

## 📁 Project Structure

```
text-to-sql-rag/
│
├── app.py                   # Streamlit UI (entry point)
├── requirements.txt         # Python dependencies
├── .env.example             # Template for API key
│
├── src/
│   ├── setup_database.py    # Creates SQLite DB with sample data
│   ├── schema_rag.py        # Schema extraction + FAISS vector store
│   └── sql_engine.py        # Core RAG → SQL → Execute → Interpret pipeline
│
└── data/                    # Auto-created on first run
    ├── company.db           # SQLite database
    └── faiss_index/         # Saved FAISS vector index
```

---

## 🚀 Setup (Step by Step)

### Step 1 — Clone / download this project
Place the folder anywhere on your machine.

### Step 2 — Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up your OpenAI API key
1. Copy `.env.example` → `.env`
2. Open `.env` and replace the placeholder with your real key:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```
Get your key at: https://platform.openai.com/api-keys

### Step 5 — Run the app
```bash
streamlit run app.py
```

The app will automatically:
- Create the SQLite database with sample data
- Build the FAISS vector index
- Open in your browser at http://localhost:8501

---

## 💡 Example Questions to Try

| Question | What it does |
|----------|-------------|
| Who are the top 5 highest paid employees? | Sorts by salary |
| How many employees are in each department? | GROUP BY |
| What is the total revenue per region? | SUM + GROUP BY |
| Which products are low on stock (less than 100)? | WHERE filter |
| Show all sales made in March 2024 | Date filtering |
| Which employee made the most sales? | JOIN + aggregate |
| What is the average salary in Engineering? | AVG + WHERE |

---

## 🧠 How RAG Works Here

Instead of dumping the entire database schema into every prompt (expensive + slow),
we use **Retrieval-Augmented Generation**:

1. Each table's schema is converted into a text document
2. Documents are embedded into vectors using `text-embedding-3-small`
3. When a question comes in, the most **semantically similar** schema chunks are retrieved
4. Only those chunks are sent to GPT-4o → smaller prompt, better accuracy, lower cost

---

## 🔧 Customizing with Your Own Database

Edit `src/setup_database.py` to replace the sample data with your own tables.
Then delete `data/faiss_index/` and restart the app — it will rebuild automatically.

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `openai` | GPT-4o + text-embedding-3-small API |
| `langchain` | Document/retriever abstractions |
| `langchain-openai` | LangChain ↔ OpenAI integration |
| `faiss-cpu` | Fast vector similarity search |
| `streamlit` | Web UI |
| `python-dotenv` | Load `.env` API key |
| `pandas` | Display result tables |
| `sqlalchemy` | (available for future DB expansion) |
