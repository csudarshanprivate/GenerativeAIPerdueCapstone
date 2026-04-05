"""
HealthAgent — Agentic Healthcare Assistant
Streamlit UI

Run: streamlit run streamlit_app.py
"""
import os, json, warnings
warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import wikipedia

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HealthAgent — AI Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = "../Datasets_New/Agentic Healthcare Assistant for Medical Task Automation/"

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_patient_db():
    df = pd.read_excel(DATA_DIR + "records.xlsx")
    db = {}
    for _, row in df.iterrows():
        name = str(row.get("Name", "")).strip()
        if name:
            db[name.lower()] = {
                "name": name, "age": row.get("Age"), "gender": row.get("Gender"),
                "phone": str(row.get("Phone_number", "")),
                "email": str(row.get("Email", "")),
                "address": str(row.get("Address", "")),
                "summary": str(row.get("Summary", "No summary available.")),
            }
    return db

@st.cache_resource
def build_vectorstore():
    embeddings = OpenAIEmbeddings()
    pdf_files = ["sample_patient.pdf","sample_report_anjali.pdf",
                 "sample_report_david.pdf","sample_report_ramesh.pdf"]
    all_docs = []
    for fname in pdf_files:
        try:
            loader = PyPDFLoader(DATA_DIR + fname)
            pages = loader.load()
            for p in pages: p.metadata["source"] = fname
            all_docs.extend(pages)
        except: pass
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    split_docs = splitter.split_documents(all_docs)
    vs = FAISS.from_documents(split_docs, embeddings)
    return vs.as_retriever(search_kwargs={"k": 4})

def make_schedule():
    today = datetime.today()
    return {
        "general physician":  {(today+timedelta(days=1)).strftime("%Y-%m-%d"):["09:00","10:00","11:00","14:00"],
                                (today+timedelta(days=2)).strftime("%Y-%m-%d"):["09:00","10:30","15:00"]},
        "cardiologist":        {(today+timedelta(days=1)).strftime("%Y-%m-%d"):["10:00","13:00"],
                                (today+timedelta(days=3)).strftime("%Y-%m-%d"):["09:00","11:00","14:00"]},
        "nephrologist":        {(today+timedelta(days=2)).strftime("%Y-%m-%d"):["09:30","11:30","14:00"],
                                (today+timedelta(days=4)).strftime("%Y-%m-%d"):["10:00","13:00"]},
        "endocrinologist":     {(today+timedelta(days=1)).strftime("%Y-%m-%d"):["09:00","11:00"],
                                (today+timedelta(days=2)).strftime("%Y-%m-%d"):["10:00","14:00","15:30"]},
        "pulmonologist":       {(today+timedelta(days=1)).strftime("%Y-%m-%d"):["09:00","10:00","14:00"],
                                (today+timedelta(days=3)).strftime("%Y-%m-%d"):["11:00","15:00"]},
    }

# ── Session state init ────────────────────────────────────────────────────────
if "patient_db" not in st.session_state:
    st.session_state.patient_db = load_patient_db()
if "schedule" not in st.session_state:
    st.session_state.schedule = make_schedule()
if "bookings" not in st.session_state:
    st.session_state.bookings = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Build agent (only when API key available) ─────────────────────────────────
def build_agent():
    patient_db = st.session_state.patient_db
    schedule   = st.session_state.schedule
    bookings   = st.session_state.bookings

    retriever = build_vectorstore()

    @tool
    def get_patient_history(patient_name: str) -> str:
        """Retrieve structured patient information and medical summary."""
        key = patient_name.strip().lower()
        match = next((v for k, v in patient_db.items() if key in k or k in v["name"].lower()), None)
        if not match:
            return f"No patient found for '{patient_name}'. Available: {[v['name'] for v in patient_db.values()]}"
        return (f"Patient: {match['name']} | Age: {match['age']} | Gender: {match['gender']}\n"
                f"Phone: {match['phone']} | Address: {match['address']}\n"
                f"Summary: {match['summary']}")

    @tool
    def retrieve_medical_documents(patient_name: str) -> str:
        """Retrieve detailed clinical notes from patient PDF records."""
        docs = retriever.invoke(patient_name)
        if not docs: return f"No clinical documents found for '{patient_name}'."
        return "\n\n---\n\n".join(d.page_content.strip() for d in docs)

    @tool
    def book_appointment(patient_name: str, specialty: str, preferred_date: str = "") -> str:
        """Book a medical appointment for a patient with a specialist."""
        spec_key = specialty.strip().lower()
        matched = next((s for s in schedule if spec_key in s or s in spec_key), None)
        if not matched:
            return f"No {specialty} found. Available: {list(schedule.keys())}"
        slots = schedule[matched]
        if preferred_date and preferred_date in slots and slots[preferred_date]:
            date, slot = preferred_date, slots[preferred_date][0]
        else:
            future = {d: s for d, s in sorted(slots.items()) if s}
            if not future: return f"No available slots for {matched}."
            date, slot = next(iter(future.items())); slot = slot[0]
        schedule[matched][date].remove(slot)
        bookings.append({"patient": patient_name, "specialty": matched,
                         "date": date, "time": slot,
                         "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        return (f"✅ Appointment Confirmed!\nPatient: {patient_name}\n"
                f"Specialist: {matched.title()}\nDate: {date} at {slot}\n"
                f"Ref: APT-{len(bookings):04d}")

    @tool
    def update_patient_record(patient_name: str, update_notes: str) -> str:
        """Add or update a patient's medical notes in the database."""
        key = patient_name.strip().lower()
        match_key = next((k for k in patient_db if key in k or k in patient_name.lower()), None)
        if not match_key: return f"Patient '{patient_name}' not found."
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        patient_db[match_key]["summary"] += f"\n[Updated {ts}]: {update_notes}"
        return f"✅ Record updated for {patient_db[match_key]['name']}\nAdded: {update_notes}"

    @tool
    def search_medical_info(query: str) -> str:
        """Search for medical information about diseases and treatments."""
        try:
            result = wikipedia.summary(query, sentences=6, auto_suggest=True)
            return f"Medical Info — '{query}':\n\n{result}"
        except wikipedia.exceptions.DisambiguationError as e:
            try: return wikipedia.summary(e.options[0], sentences=6)
            except: return f"Multiple topics found. Try a more specific term."
        except Exception as e:
            return f"Search error: {str(e)}"

    @tool
    def list_booked_appointments(filter_patient: str = "") -> str:
        """List all booked appointments, optionally filtered by patient."""
        if not bookings: return "No appointments booked yet."
        filtered = [a for a in bookings if not filter_patient or filter_patient.lower() in a["patient"].lower()]
        if not filtered: return f"No appointments found for '{filter_patient}'."
        lines = ["Booked Appointments:"]
        for i, a in enumerate(filtered):
            lines.append(f"  [{a['date']} {a['time']}] {a['patient']} → {a['specialty'].title()} (APT-{i+1:04d})")
        return "\n".join(lines)

    agent_tools = [get_patient_history, retrieve_medical_documents, book_appointment,
                   update_patient_record, search_medical_info, list_booked_appointments]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    memory = MemorySaver()
    SYSTEM = """You are HealthAgent, an intelligent Agentic Healthcare Assistant.
Help patients and staff by retrieving patient histories, booking appointments,
updating records, and providing medical information. Always be professional and accurate."""

    return create_react_agent(model=llm, tools=agent_tools, prompt=SYSTEM, checkpointer=memory)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 HealthAgent")
    st.caption("Agentic AI Healthcare Assistant")
    st.divider()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    if api_key and st.session_state.agent is None:
        with st.spinner("Initializing HealthAgent..."):
            try:
                st.session_state.agent = build_agent()
                st.success("HealthAgent ready!")
            except Exception as e:
                st.error(f"Init error: {e}")

    st.divider()
    page = st.radio("Navigate", ["💬 AI Assistant", "📋 Patient Records",
                                  "📅 Appointments", "📊 Dashboard"],
                    label_visibility="collapsed")
    st.divider()
    st.caption("Applied Generative AI — Capstone Project")

# ── Load data ─────────────────────────────────────────────────────────────────
patient_db = st.session_state.patient_db
bookings   = st.session_state.bookings

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
if page == "💬 AI Assistant":
    st.title("💬 HealthAgent AI Assistant")
    st.caption("Ask anything about patients, appointments, or medical information.")

    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Please enter your OpenAI API key in the sidebar.")
        st.stop()
    if st.session_state.agent is None:
        st.info("Initializing agent... please wait.")
        st.stop()

    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": ("Hello! I'm **HealthAgent**, your AI healthcare assistant. I can help you:\n\n"
                        "- 📋 **Retrieve** patient medical histories\n"
                        "- 📅 **Book** specialist appointments\n"
                        "- ✏️ **Update** patient records\n"
                        "- 🔍 **Search** medical information\n\n"
                        "What can I help you with today?")
        })

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    with st.expander("💡 Sample Queries"):
        samples = [
            "Show me Ramesh Kulkarni's medical history",
            "Book a cardiologist for Anjali Mehra",
            "What are the treatments for Type 2 Diabetes?",
            "My 70-year-old father has chronic kidney disease. Book a nephrologist for Ramesh Kulkarni and summarize treatment options.",
            "Update David Thompson's record: HbA1c 8.2%, metformin increased to 1000mg BID",
        ]
        for s in samples:
            if st.button(s, key=f"btn_{s[:30]}"):
                st.session_state._prefill = s

    prefill = st.session_state.pop("_prefill", None)
    user_input = st.chat_input("Ask HealthAgent...") or prefill

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("HealthAgent is thinking..."):
                config = {"configurable": {"thread_id": "streamlit_session"}}
                result = st.session_state.agent.invoke(
                    {"messages": [HumanMessage(content=user_input)]}, config=config
                )
                response = next(
                    (m.content for m in reversed(result["messages"]) if m.type == "ai" and m.content),
                    "I could not generate a response."
                )

                # Show tool usage trace
                tool_calls = []
                for msg in result["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_calls.append(tc["name"])
                if tool_calls:
                    st.caption(f"🔧 Tools used: {' → '.join(tool_calls)}")

                st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})

    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PATIENT RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Patient Records":
    st.title("📋 Patient Records")
    st.caption(f"{len(patient_db)} patients in database")

    search = st.text_input("🔍 Search patient by name")
    filtered = {k: v for k, v in patient_db.items()
                if not search or search.lower() in v["name"].lower()}

    for key, patient in filtered.items():
        with st.expander(f"🧑 {patient['name']}  •  Age {patient['age']}  •  {patient['gender']}"):
            col1, col2 = st.columns(2)
            col1.markdown(f"**Phone:** {patient['phone']}")
            col1.markdown(f"**Email:** {patient['email']}")
            col2.markdown(f"**Address:** {patient['address']}")
            st.markdown("**Medical Summary:**")
            st.info(patient["summary"])

            if st.session_state.agent and os.getenv("OPENAI_API_KEY"):
                if st.button(f"📄 Retrieve full clinical notes", key=f"notes_{key}"):
                    with st.spinner("Retrieving..."):
                        config = {"configurable": {"thread_id": f"notes_{key}"}}
                        result = st.session_state.agent.invoke(
                            {"messages": [HumanMessage(content=f"Retrieve detailed clinical documents for {patient['name']}")]},
                            config=config
                        )
                        resp = next((m.content for m in reversed(result["messages"]) if m.type == "ai" and m.content), "")
                        st.markdown(resp)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: APPOINTMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Appointments":
    st.title("📅 Appointment Management")

    tab1, tab2 = st.tabs(["Book Appointment", "View Bookings"])

    with tab1:
        st.subheader("Book New Appointment")
        col1, col2 = st.columns(2)
        with col1:
            pt_name  = st.selectbox("Patient", [v["name"] for v in patient_db.values()])
            specialty = st.selectbox("Specialty", [s.title() for s in st.session_state.schedule])
        with col2:
            schedule = st.session_state.schedule
            spec_key = specialty.lower()
            avail_dates = [d for d, slots in sorted(schedule.get(spec_key, {}).items()) if slots]
            if avail_dates:
                pref_date = st.selectbox("Preferred Date", avail_dates)
                avail_slots = schedule[spec_key].get(pref_date, [])
                pref_slot = st.selectbox("Preferred Time", avail_slots) if avail_slots else st.write("No slots available")
            else:
                st.warning(f"No available slots for {specialty}.")
                pref_date = pref_slot = None

        if st.button("✅ Confirm Booking", type="primary") and pref_date and os.getenv("OPENAI_API_KEY"):
            if st.session_state.agent:
                with st.spinner("Booking..."):
                    config = {"configurable": {"thread_id": "booking_ui"}}
                    result = st.session_state.agent.invoke(
                        {"messages": [HumanMessage(content=f"Book a {specialty} appointment for {pt_name} on {pref_date}")]},
                        config=config
                    )
                    resp = next((m.content for m in reversed(result["messages"]) if m.type == "ai" and m.content), "")
                    st.success(resp)

    with tab2:
        st.subheader("All Bookings")
        if not bookings:
            st.info("No appointments booked yet. Use the Book Appointment tab or AI Assistant.")
        else:
            apt_df = pd.DataFrame(bookings)
            apt_df["specialty"] = apt_df["specialty"].str.title()
            st.dataframe(apt_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.title("📊 Healthcare Dashboard")
    sns.set_theme(style="whitegrid")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Patients", len(patient_db))
    col2.metric("Appointments Booked", len(bookings))
    total_slots = sum(len(s) for d in st.session_state.schedule.values() for s in d.values())
    col3.metric("Available Slots", total_slots)

    st.divider()

    # Patient demographics
    ages    = [v["age"] for v in patient_db.values() if isinstance(v["age"], (int, float))]
    names   = [v["name"].split()[0] for v in patient_db.values() if isinstance(v["age"], (int, float))]
    genders = [v["gender"] for v in patient_db.values() if v["gender"]]

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Patient Age Profile")
        fig, ax = plt.subplots(figsize=(6, 3.5))
        colors = ["#2E86AB","#A23B72","#F18F01","#C73E1D","#264653"]
        bars = ax.bar(names, ages, color=colors[:len(names)])
        ax.bar_label(bars, labels=[f"{a} yrs" for a in ages], padding=2, fontsize=9)
        ax.set_ylabel("Age"); ax.set_ylim(0, max(ages)+15)
        plt.tight_layout(); st.pyplot(fig)

    with col_b:
        st.subheader("Doctor Availability")
        spec_slots = {s.title(): sum(len(sl) for sl in d.values())
                      for s, d in st.session_state.schedule.items()}
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.barh(list(spec_slots.keys()), list(spec_slots.values()), color="#2A9D8F")
        ax.set_xlabel("Available Slots")
        plt.tight_layout(); st.pyplot(fig)

    if bookings:
        st.subheader("Appointment Bookings by Specialty")
        apt_df = pd.DataFrame(bookings)
        spec_counts = apt_df["specialty"].value_counts()
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.bar(spec_counts.index, spec_counts.values, color="#E9C46A")
        ax.set_ylabel("Count")
        plt.tight_layout(); st.pyplot(fig)
