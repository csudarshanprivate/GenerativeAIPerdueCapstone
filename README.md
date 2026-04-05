# NewsGenie — Agentic AI News & Information Assistant
**Course End Project (CEP) — Applied Generative AI Specialisation**

---

## Overview

NewsGenie is a truly **agentic** AI news and information assistant built with **LangGraph `create_react_agent`**. Unlike a traditional rule-based pipeline, the LLM autonomously decides which tools to invoke and in what order — a classic **ReAct (Reasoning + Acting)** loop.

**Core capabilities:**

- 📰 **Real-time news headlines** — fetches top stories by category (Technology, Finance, Sports, Health, Science, Entertainment, General)
- 🔍 **Topic news search** — finds recent articles on any specific subject or event
- 🌐 **Live web search** — retrieves real-time facts, prices, and current information
- 🌤️ **Weather forecasts** — current conditions and 3-day forecasts for any city worldwide
- 💬 **Conversational AI** — answers general knowledge questions directly from LLM training
- 🧠 **Multi-turn memory** — remembers context across the full conversation via `MemorySaver`

---

## Agentic Architecture

```
User Query
    │
    ▼
create_react_agent  (LangGraph ReAct Loop)
    │
    ├── LLM Reasoning  ←── decides which tool(s) to call
    │
    ├── Tool Execution
    │       ├── get_top_headlines(category)   ← news by category
    │       ├── search_news(query)             ← topic news search
    │       ├── search_web(query)              ← live web facts
    │       ├── get_weather(location)          ← weather forecast
    │       └── get_news_categories()          ← list categories
    │
    ├── Tool Results  ──► LLM Synthesises Final Answer
    │
    └── MemorySaver  ←── persists conversation across turns
```

**What makes it agentic:**
The LLM reads each tool's docstring and autonomously decides which tool(s) to call, what arguments to pass, and how to synthesise results — with no hard-coded routing logic.

---

## Project Structure

```
AgenticsNewsGenie/
├── AgenticsNewsGenie_Capstone.ipynb  # Main notebook — all steps, demos, test cases
├── tools.py                          # @tool-decorated agent tools (5 tools)
├── agents.py                         # create_react_agent setup + system prompt
├── workflow.py                       # run_agent() helper + MemorySaver
├── streamlit_app.py                  # Streamlit UI — 3 pages
├── requirements.txt                  # Python dependencies
├── .env                              # API keys (fill before running)
├── test_cases.md                     # 30 detailed test cases
├── README.md                         # This file
└── README.docx                       # Word version of this README
```

---

## Prerequisites

- Python **3.9+**
- **OpenAI API key** (required) — used for the ReAct agent LLM
- **NewsAPI key** (optional — free tier at [newsapi.org](https://newsapi.org); DuckDuckGo used automatically if not set)
- No key required for weather (Open-Meteo) or web search (DuckDuckGo)

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
| Setup | Load `.env`, install imports |
| Step 1 | Environment setup and library imports |
| Step 2 | Define 5 `@tool`-decorated agent tools |
| Step 3 | Create ReAct agent with `create_react_agent` + `MemorySaver` |
| Step 4 | 7 sample scenarios (tech news, finance, topic search, CEO lookup, chat, multi-turn, categories) |
| Step 5 | 10 automated test cases — tool selection + response validation |
| Step 6 | 2 visualisations (test results + agent architecture diagram) |

### Option B — Streamlit UI
```bash
streamlit run streamlit_app.py
```
Open **http://localhost:8501**

| Page | Description |
|---|---|
| 💬 AI News Chat | Main chat interface — agent shows which tools it called per response |
| 📊 Quick Headlines | One-click category buttons with active highlight + instant news fetch |
| 🧪 Test Cases | Run 10 automated tests with colour-coded pass/fail results |

---

## Tools

| Tool | Trigger | Data Source |
|---|---|---|
| `get_top_headlines(category)` | "latest tech news", "top sports headlines" | NewsAPI / DuckDuckGo News |
| `search_news(query)` | "news about Tesla", "OpenAI recent news" | NewsAPI / DuckDuckGo News |
| `search_web(query)` | "who is CEO of Apple", "Bitcoin price" | DuckDuckGo Web Search |
| `get_weather(location)` | "weather in London", "will it rain in Chicago?" | Open-Meteo (free, no key) |
| `get_news_categories()` | "what categories do you support?" | Built-in |

---

## Query Examples

| User Query | Tool Called | Result |
|---|---|---|
| "Latest technology news today" | `get_top_headlines("technology")` | Top tech headlines |
| "Top sports headlines" | `get_top_headlines("sports")` | Sports stories |
| "Search for news about OpenAI" | `search_news("OpenAI recent news")` | OpenAI articles |
| "Who is the CEO of Microsoft?" | `search_web("CEO of Microsoft")` | Satya Nadella |
| "Weather in Aurora, Illinois" | `get_weather("Aurora, Illinois")` | Current + 3-day forecast |
| "What is machine learning?" | *(no tool — LLM answers directly)* | Explanation |
| "Which story was most important?" | *(no tool — uses conversation memory)* | Follow-up answer |

---

## Content Reliability Filter

A key requirement of NewsGenie is filtering out unreliable or misleading content. Every article passes through a reliability scoring layer before being shown to the user.

| Score | Badge | Criteria |
|---|---|---|
| Trusted | ✅ Trusted Source | Article from a known reputable outlet (Reuters, BBC, Bloomberg, ESPN, etc.) |
| Unverified | ❓ Unverified Source | Source not in trusted list — shown but flagged |
| Flagged | ⚠️ Possible Clickbait | Sensational title patterns detected (e.g. "You won't believe…", "!!!") |
| Removed | *(filtered out)* | Known misinformation sources (e.g. InfoWars) — dropped entirely |

**How it works:**
1. Each article's source is matched against a curated trusted-sources list (50+ major outlets)
2. Article titles are checked against clickbait regex patterns (sensational language, excessive punctuation, listicle bait)
3. Known unreliable domains are removed before results reach the user
4. All remaining articles display a reliability badge alongside the source name

---

## Fallback Mechanisms

| Scenario | Behaviour |
|---|---|
| No `NEWSAPI_KEY` | Automatically uses DuckDuckGo News |
| DuckDuckGo rate-limited | Retries 3 times with backoff |
| General knowledge question | LLM answers from training data (no tool needed) |
| Ambiguous city name | Geocoding picks best match by state/country hint |
| All results flagged as unreliable | Returns informative message, prompts retry |

---

## Test Cases

See **`test_cases.md`** for full details. Summary:

| Category | Test IDs |
|---|---|
| News routing (technology, finance, sports, health) | TC-01 to TC-04 |
| Web search routing (factual queries) | TC-05 to TC-07 |
| General chat (LLM answers without tools) | TC-08 to TC-09 |
| Multi-turn memory | TC-10 |

**Pass criteria:** ≥ 80% PASS across all test cases.

---

## Key Libraries

| Library | Purpose |
|---|---|
| `langgraph` | `create_react_agent` — ReAct agentic loop with `MemorySaver` |
| `langchain-openai` | GPT-4o-mini LLM for reasoning and synthesis |
| `langchain-core` | `@tool` decorator for defining agent tools |
| `ddgs` | DuckDuckGo news and web search (no API key) |
| `requests` | NewsAPI and Open-Meteo HTTP calls |
| `streamlit` | Interactive multi-page web UI |
| `python-dotenv` | API key management via `.env` |
| `python-docx` | README Word document generation |

---

## CEP Requirements Coverage

| Requirement | Implementation |
|---|---|
| Agentic AI with tool use | `create_react_agent` — LLM autonomously selects and calls tools |
| Real-time news API integration | NewsAPI.org + DuckDuckGo fallback |
| Technology, finance, sports, health, science categories | All 7 categories supported |
| Web search tool | `search_web` tool via DuckDuckGo |
| Weather integration | `get_weather` tool via Open-Meteo (no key needed) |
| Multi-turn conversation memory | `MemorySaver` checkpointer across all turns |
| LangGraph-based workflow | `create_react_agent` built on LangGraph internals |
| Fallback mechanisms | DuckDuckGo fallback + rate-limit retry + direct LLM fallback |
| Streamlit UI with session management | 3-page app with persistent session state |
| Filter unreliable/misleading content | Reliability filter — trusted-source list + clickbait detection + flagged-domain removal |
| Automated test cases | 10 tests validating tool selection and response quality |
| Multi-file architecture | `tools.py` → `agents.py` → `workflow.py` → `streamlit_app.py` |
