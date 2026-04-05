# HealthAgent — Agentic Healthcare Assistant for Medical Task Automation
**Applied Generative AI Specialisation — Capstone Project**

---

## Project Overview

HealthAgent is an **Agentic AI system** built on **LangGraph** and **OpenAI GPT-4o-mini** that autonomously handles multi-step healthcare tasks:

- 📅 **Appointment booking** — checks doctor availability and confirms slots
- 📋 **Medical history retrieval** — retrieves patient records from Excel and PDF files
- ✏️ **Record management** — adds/updates patient notes with timestamps
- 🔍 **Medical information search** — fetches disease and treatment information

---

## Project Structure

```
AgenticAIHealthCareAssistant/
├── AgenticHealthcare_Capstone.ipynb  # Main notebook — all 7 steps
├── streamlit_app.py                  # Interactive Streamlit UI
├── requirements.txt                  # Python dependencies
├── .env                              # OpenAI API key (see setup below)
├── test_cases.md                     # 30+ test cases for validation
└── README.md                         # This file
```

**Dataset** (outside this folder):
```
../Datasets_New/Agentic Healthcare Assistant for Medical Task Automation/
├── records.xlsx            # Patient database (5 patients)
├── sample_patient.pdf      # Rebeca Nagle — full clinical record
├── sample_report_anjali.pdf
├── sample_report_david.pdf
└── sample_report_ramesh.pdf
```

---

## Prerequisites

- Python **3.9+**
- An **OpenAI API key** with active billing credits

---

## Setup Instructions

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Add your OpenAI API key

Edit the `.env` file and replace the placeholder:

```
OPENAI_API_KEY=your-key-here
```

---

## Running the Project

### Option A — Jupyter Notebook (recommended for grading)

```bash
jupyter notebook AgenticHealthcare_Capstone.ipynb
```

Run cells **top to bottom**. Steps covered:

| Step | Description |
|---|---|
| Setup | Load `.env`, import libraries |
| Step 1 | Agent planning — ReAct loop explanation |
| Step 2 | Load patient DB (Excel + PDFs → FAISS) + mock doctor schedule |
| Step 3 | Define 6 tools: `get_patient_history`, `retrieve_medical_documents`, `book_appointment`, `update_patient_record`, `search_medical_info`, `list_booked_appointments` |
| Step 4 | Build LangGraph ReAct agent with `MemorySaver` |
| Scenarios | 5 sample runs: single-step and multi-step agent workflows |
| Step 5 | QAEvalChain evaluation — 5 graded Q&A pairs |
| Step 6 | Visualizations: demographics, bookings, availability, evaluation |
| Step 7 | Memory trace inspection |

### Option B — Streamlit UI

```bash
streamlit run streamlit_app.py
```

Open **http://localhost:8501**

| Page | Description |
|---|---|
| 💬 AI Assistant | Chat with HealthAgent — shows tool call trace |
| 📋 Patient Records | Browse and search all patients, retrieve clinical notes |
| 📅 Appointments | Book appointments via UI or view all bookings |
| 📊 Dashboard | Demographics, availability, and booking charts |

---

## Architecture

```
User Query
    │
    ▼
LangGraph ReAct Agent (gpt-4o-mini)
    │  Plans sub-goals, selects tools
    ├──► get_patient_history      → Excel patient database
    ├──► retrieve_medical_documents → FAISS (patient PDFs)
    ├──► book_appointment         → Mock doctor schedule
    ├──► update_patient_record    → In-memory patient DB
    ├──► search_medical_info      → Wikipedia medical search
    └──► list_booked_appointments → Booking registry
    │
    ▼
MemorySaver (multi-turn session memory)
    │
    ▼
Unified response to user
```

---

## Testing

See **`test_cases.md`** for 30+ test cases across 10 categories:

| Category | Test Cases |
|---|---|
| TC-01 | Patient history retrieval (known, partial name, unknown) |
| TC-02 | Clinical document retrieval (PDFs, ICD codes, treatment plans) |
| TC-03 | Appointment booking (by specialty, condition, availability) |
| TC-04 | Medical information search (conditions, medications, symptoms) |
| TC-05 | Record update (add notes, lab results, unknown patient) |
| TC-06 | Multi-step workflows (problem statement scenario + 2 others) |
| TC-07 | Conversational memory (multi-turn context retention) |
| TC-08 | Appointment listing and filtering |
| TC-09 | Edge cases and error handling |
| TC-10 | QAEvalChain evaluation (pass criteria: ≥ 80% correct) |

---

## Key Libraries

| Library | Purpose |
|---|---|
| `langgraph` | ReAct agent framework with memory checkpointing |
| `langchain-openai` | GPT-4o-mini LLM + OpenAI embeddings |
| `langchain-community` | FAISS vectorstore, PDF loader |
| `faiss-cpu` | Vector similarity search for patient documents |
| `wikipedia` | Medical information search |
| `openpyxl` | Read patient database from Excel |
| `pypdf` | Load patient PDF reports |
| `streamlit` | Interactive web UI |
| `python-dotenv` | API key management |

---

## Capstone Requirements Coverage

| Requirement | Implementation |
|---|---|
| Agent planning & goal decomposition | LangGraph ReAct — multi-step query breakdown |
| Tool and memory setup | 6 tools + FAISS KB + MemorySaver |
| Prompt engineering and task chaining | System prompt + tool docstrings guide planning |
| Agent execution flow | 5 sample scenarios (incl. problem statement scenario) |
| Model evaluation | QAEvalChain — 5 graded Q&A pairs |
| Data visualization and UI | 4 charts + full Streamlit dashboard |
| Memory and logs interface | Session memory trace inspection in notebook + UI |
