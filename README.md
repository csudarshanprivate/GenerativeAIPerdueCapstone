# InsightForge — AI-Powered Business Intelligence Assistant
**Advanced Generative AI | Capstone Project**

---

## Project Overview

InsightForge is an end-to-end AI-powered Business Intelligence assistant built on **LangChain**, **OpenAI GPT-4o-mini**, and **FAISS**. It analyzes 2,500 sales transactions and enables natural-language querying of business data through a **RAG pipeline with conversational memory**, evaluated via **QAEvalChain**, and presented through an interactive **Streamlit dashboard**.

---

## Project Structure

```
AIPowered_BI/
├── AIPowered_BI_Capstone.ipynb   # Main notebook — all 8 steps
├── streamlit_app.py              # Interactive Streamlit UI
├── requirements.txt              # Python dependencies
├── .env                          # OpenAI API key (see setup below)
└── README.md                     # This file
```

**Dataset** (outside this folder):
```
../Datasets_New/sales_data.csv    # 2,500 rows — Date, Product, Region, Sales,
                                  # Customer_Age, Customer_Gender, Customer_Satisfaction
```

---

## Prerequisites

- Python **3.9+**
- An **OpenAI API key** with active billing credits
- ~500 MB disk space (for pip packages)

---

## Setup Instructions

### Step 1 — Install dependencies

Open a terminal, navigate to the `AIPowered_BI` folder, and run:

```bash
pip install -r requirements.txt
```

> If `pip` is not on your PATH, use `pip3` or `python3 -m pip`.

### Step 2 — Add your OpenAI API key

Create a file named `.env` inside the `AIPowered_BI` folder with the following content:

```
OPENAI_API_KEY=sk-your-key-here
```

> The `.env` file may already be present in the submitted package. If so, replace the key value with your own.

---

## Running the Project

### Option A — Jupyter Notebook (recommended for grading)

```bash
jupyter notebook AIPowered_BI_Capstone.ipynb
```

Run cells **top to bottom**. Each step is clearly labelled with objectives and explanations.

| Step | What runs |
|---|---|
| Setup | Loads `.env`, imports all libraries |
| Step 1 | Loads `sales_data.csv`, EDA, feature engineering |
| Step 2 | Builds FAISS knowledge base from sales summaries |
| Step 3 | Custom `SalesDataRetriever` + LLM analysis chains |
| Step 4 | Sequential chain: metrics extraction → executive summary |
| Step 5 | Hybrid RAG chain (pandas + FAISS) via LCEL |
| Step 6 | Memory-enabled conversational assistant (multi-turn demo) |
| Step 7 | `QAEvalChain` evaluation — 5 Q&A pairs graded by LLM |
| Step 8 | 4 matplotlib/seaborn visualizations saved as PNG files |

### Option B — Streamlit UI

```bash
streamlit run streamlit_app.py
```

Then open **http://localhost:8501** in your browser.

| Page | Description |
|---|---|
| 📈 Dashboard | KPI cards + all 4 business charts |
| 💬 AI Assistant | Chat interface with RAG + conversational memory |
| 📋 Data Explorer | Filter, pivot table, and CSV download |

---

## Architecture Summary

```
sales_data.csv
      │
      ▼
  pandas DataFrame
      │
      ├──► SalesDataRetriever (live stats, query-aware)
      │                │
      ├──► FAISS VectorStore (OpenAI Embeddings)    ──► MergerRetriever (hybrid)
      │                                                        │
      └──────────────────────────────────────────► RAG Chain (LCEL)
                                                            │
                                              ChatOpenAI (gpt-4o-mini)
                                                            │
                                             RunnableWithMessageHistory
                                                (conversational memory)
                                                            │
                                                    ┌───────┴────────┐
                                               Notebook          Streamlit UI
                                            (evaluation +      (dashboard +
                                            visualizations)      chat UI)
```

---

## Key Libraries

| Library | Purpose |
|---|---|
| `langchain` / `langchain-openai` | LLM chains, prompts, LCEL pipeline |
| `langchain-community` | FAISS vectorstore, chat message history |
| `openai` | GPT-4o-mini via OpenAI API |
| `faiss-cpu` | Vector similarity search |
| `pandas` / `numpy` | Data processing and statistics |
| `matplotlib` / `seaborn` | Visualizations |
| `streamlit` | Interactive web UI |
| `python-dotenv` | API key management |

---

## Capstone Requirements Coverage

| Requirement | Implementation |
|---|---|
| Data preparation | Step 1 — pandas EDA + feature engineering |
| Knowledge base creation | Step 2 — 7 document types → FAISS |
| LLM application + advanced data summary | Step 3 — analysis chains (time, product, region, customer) |
| Chain prompts | Step 4 — sequential chain (metrics → executive summary) |
| RAG system setup | Step 5 — hybrid MergerRetriever + LCEL |
| Memory integration | Step 6 — `RunnableWithMessageHistory` |
| Model evaluation | Step 7 — `QAEvalChain` with 5 graded Q&A pairs |
| Data visualizations | Step 8 — 4 charts (trends, product, regional, demographics) |
| Streamlit UI | `streamlit_app.py` — dashboard + chat + data explorer |
