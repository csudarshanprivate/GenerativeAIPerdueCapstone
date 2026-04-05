# NewsGenie — AI-Powered Information and News Assistant
**Course End Project (CEP) — Applied Generative AI Specialisation**

---

## Overview

NewsGenie is a unified agentic AI platform that helps users navigate today's fast-paced digital news landscape by:

- 💬 **Handling conversations** — interprets general queries and answers via GPT-4o-mini
- 📰 **Fetching real-time news** — curates top headlines by category (Technology, Finance, Sports, Health, Science, General)
- 🔍 **Performing web searches** — enriches responses with live external information via DuckDuckGo
- 🔀 **Routing intelligently** — LangGraph `StateGraph` classifies every query and dispatches to the right handler
- 🛡️ **Handling failures gracefully** — automatic fallback from NewsAPI → DuckDuckGo → LLM

---

## Project Structure

```
AgenticsNewsGenie/
├── AgenticsNewsGenie_Capstone.ipynb  # Main notebook — all steps + test cases
├── streamlit_app.py                  # Interactive Streamlit UI (3 pages)
├── requirements.txt                  # Python dependencies
├── .env                              # API keys (fill before running)
├── test_cases.md                     # 30+ detailed test cases
├── README.md                         # This file
└── README.docx                       # Word version of README
```

---

## Prerequisites

- Python **3.9+**
- **OpenAI API key** (required)
- **NewsAPI key** (optional — free tier at [newsapi.org](https://newsapi.org). DuckDuckGo is used automatically if not set)

---

## Setup Instructions

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Configure API keys

Edit `.env`:
```
OPENAI_API_KEY=your-openai-key-here
NEWSAPI_KEY=your-newsapi-key-here   # optional
```

---

## Running the Project

### Option A — Jupyter Notebook (recommended for grading)
```bash
jupyter notebook AgenticsNewsGenie_Capstone.ipynb
```
Run cells top to bottom.

| Step | Description |
|---|---|
| Setup | Load `.env`, import all libraries |
| Step 1 | Define `NewsGenieState` + Router node (LLM-powered query classification) |
| Step 2 | News Fetching node — NewsAPI (primary) + DuckDuckGo (fallback) |
| Step 3 | Web Search node — DuckDuckGo text search + LLM synthesis |
| Step 4 | Chat node — GPT-4o-mini with conversation history |
| Step 5 | Build and compile full LangGraph `StateGraph` workflow |
| Step 6 | 6 sample scenarios (tech news, finance, sports, chat, search, multi-turn) |
| Step 7 | 10 automated test cases — routing + response validation |
| Step 8 | 3 visualisations (test results, category distribution, workflow diagram) |

### Option B — Streamlit UI
```bash
streamlit run streamlit_app.py
```
Open **http://localhost:8501**

| Page | Description |
|---|---|
| 💬 Chat & News | Main chat interface with route badge, article expander, quick buttons |
| 📊 Dashboard | LangGraph workflow diagram + category overview + session metrics |
| 🧪 Test Cases | Run all 10 automated tests with colour-coded pass/fail table |

---

## Architecture

```
User Query
    │
    ▼
┌──────────────────────────────────────┐
│         LangGraph StateGraph         │
│                                      │
│  [Router Node] ← LLM intent detect  │
│       │                              │
│  ┌────┴────────────────┐             │
│  │         │           │             │
│ [News]  [Search]    [Chat]           │
│  │         │           │             │
│  └────┬────┴───────────┘             │
│       │                              │
│  [Formatter Node] ← assemble output │
│       │                              │
│  [MemorySaver] ← session memory     │
└──────────────────────────────────────┘
    │
    ▼
Final Response to User
```

### Query Routing Logic

| Query Example | Classified As | Handler |
|---|---|---|
| "Latest tech news today" | `news` → technology | News Node |
| "Top finance headlines" | `news` → finance | News Node |
| "What is machine learning?" | `chat` → general | Chat Node |
| "Current Bitcoin price?" | `search` → finance | Search Node |
| "Summarise what you told me" | `chat` → general | Chat Node (with memory) |

### Fallback Mechanisms

| Failure | Fallback |
|---|---|
| NewsAPI unavailable / no key | DuckDuckGo News |
| DuckDuckGo news empty | Error message with retry suggestion |
| DuckDuckGo search fails | LLM answers from training knowledge |
| JSON parse error in router | Defaults to `chat` type |

---

## Test Cases

See **`test_cases.md`** for full details. Summary:

| Category | Count |
|---|---|
| TC-01 to TC-04 | News routing — technology, finance, sports, health |
| TC-05 to TC-07 | Chat routing — general queries, explanations |
| TC-08 to TC-09 | Web search routing — live data queries |
| TC-10 to TC-15 | Fallback & error handling |
| TC-16 to TC-20 | Multi-turn memory validation |
| TC-21 to TC-25 | Edge cases — empty queries, ambiguous input |
| TC-26 to TC-30 | Streamlit UI interaction tests |

**Pass criteria:** ≥ 80% PASS across all test cases.

---

## Key Libraries

| Library | Purpose |
|---|---|
| `langgraph` | `StateGraph` workflow — nodes, conditional routing, memory |
| `langchain-openai` | GPT-4o-mini LLM for routing, chat, and synthesis |
| `duckduckgo-search` | No-key news and web search fallback |
| `newsapi-python` | Real-time news headlines by category |
| `streamlit` | Interactive web UI |
| `python-dotenv` | API key management |
| `python-docx` | README Word document generation |

---

## CEP Requirements Coverage

| Requirement | Implementation |
|---|---|
| AI chatbot — conversation management | GPT-4o-mini Chat Node with `MemorySaver` history |
| Query differentiation | LangGraph Router Node — `news` / `search` / `chat` |
| Real-time news API integration | NewsAPI.org + DuckDuckGo fallback |
| Technology, finance, sports categories | All 6 categories supported |
| Web search tool | DuckDuckGo text search + LLM synthesis |
| LangGraph-based workflow | Full `StateGraph` with 5 nodes |
| Fallback mechanisms | 3-tier fallback chain for each failure mode |
| Streamlit UI with session management | 3-page Streamlit app with `MemorySaver` |
| Error handling | Missing keys, failed APIs, empty results |
| Workflow and error handling documentation | `test_cases.md` + notebook Step 7 |
