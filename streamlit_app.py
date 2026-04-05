"""
streamlit_app.py — NewsGenie Agentic UI
Multi-page Streamlit app backed by a LangGraph ReAct agent.
"""

import streamlit as st
import sys
import os

# Ensure project directory is on path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NewsGenie — AI News Assistant",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.title("📰 NewsGenie")
st.sidebar.caption("AI-Powered Agentic News Assistant")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["💬 AI News Chat", "📊 Quick Headlines", "🧪 Test Cases"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("**How it works**")
st.sidebar.markdown(
    "NewsGenie uses a **LangGraph ReAct agent** with `create_react_agent`. "
    "The LLM autonomously decides which tools to call:\n"
    "- `get_top_headlines` — category news\n"
    "- `search_news` — topic search\n"
    "- `search_web` — live web facts\n"
    "- `get_news_categories` — list categories"
)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — AI News Chat
# ══════════════════════════════════════════════════════════════════════════════
if page == "💬 AI News Chat":
    st.title("💬 NewsGenie — AI News Chat")
    st.caption("Ask anything about news, current events, or search the web. The agent decides which tools to use.")

    # Clear chat button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            from workflow import reset_agent
            reset_agent()
            import uuid
            st.session_state.thread_id = str(uuid.uuid4())
            st.rerun()

    # Welcome message
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Hello! I'm **NewsGenie**, your AI-powered news assistant.\n\n"
                "I can fetch the latest headlines, search for specific news topics, "
                "or look up real-time information on the web.\n\n"
                "Try asking:\n"
                "- *\"What are the latest technology news?\"*\n"
                "- *\"Show me top sports headlines\"*\n"
                "- *\"Search for recent news about OpenAI\"*\n"
                "- *\"Who is the current CEO of Apple?\"*"
            ),
            "tools": [],
        })

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tools"):
                st.caption(f"Tools used: {', '.join(msg['tools'])}")

    # Chat input
    if prompt := st.chat_input("Ask about news or any topic..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "tools": []})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NewsGenie is thinking..."):
                try:
                    from workflow import run_agent
                    result = run_agent(prompt, thread_id=st.session_state.thread_id)
                    response = result["response"]
                    tools = result["tools_used"]
                except Exception as e:
                    response = f"Sorry, I encountered an error: {str(e)}"
                    tools = []

            st.markdown(response)
            if tools:
                st.caption(f"Tools used: {', '.join(tools)}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "tools": tools,
        })


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Quick Headlines
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Quick Headlines":
    st.title("📊 Quick Headlines")
    st.caption("Select a category and fetch the latest headlines instantly.")

    CATEGORIES = ["Technology", "Finance", "Sports", "Health", "Science", "Entertainment", "General"]

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_cat = st.selectbox("News Category", CATEGORIES, index=0)
    with col2:
        st.write("")
        st.write("")
        fetch_btn = st.button(f"📰 Fetch {selected_cat} News", use_container_width=True)

    st.markdown("---")

    # Quick-access buttons
    st.markdown("**Quick Access:**")
    btn_cols = st.columns(len(CATEGORIES))
    clicked_cat = None
    for i, cat in enumerate(CATEGORIES):
        with btn_cols[i]:
            if st.button(cat, key=f"quick_{cat}", use_container_width=True):
                clicked_cat = cat

    active_cat = clicked_cat if clicked_cat else (selected_cat if fetch_btn else None)

    if active_cat:
        with st.spinner(f"Fetching {active_cat} news..."):
            try:
                from workflow import run_agent
                import uuid
                result = run_agent(
                    f"Get the top {active_cat.lower()} headlines",
                    thread_id=f"headlines-{uuid.uuid4()}",
                )
                st.markdown(result["response"])
                if result["tools_used"]:
                    st.success(f"Agent used: `{'`, `'.join(result['tools_used'])}`")
            except Exception as e:
                st.error(f"Error fetching news: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Test Cases
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧪 Test Cases":
    st.title("🧪 NewsGenie — Automated Test Cases")
    st.caption("Validates the agentic system across routing, tool selection, and multi-turn memory.")

    TEST_CASES = [
        {
            "id": "TC-01",
            "name": "Technology Headlines",
            "input": "What are the latest technology news stories today?",
            "check": lambda r: len(r) > 50,
            "expect": "Technology news articles",
            "tool_check": "get_top_headlines",
        },
        {
            "id": "TC-02",
            "name": "Finance Headlines",
            "input": "Show me top finance and business headlines",
            "check": lambda r: len(r) > 50,
            "expect": "Finance/business headlines",
            "tool_check": "get_top_headlines",
        },
        {
            "id": "TC-03",
            "name": "Sports Headlines",
            "input": "What are today's top sports stories?",
            "check": lambda r: len(r) > 50,
            "expect": "Sports headlines",
            "tool_check": "get_top_headlines",
        },
        {
            "id": "TC-04",
            "name": "Health News",
            "input": "Latest news in health and medicine",
            "check": lambda r: len(r) > 50,
            "expect": "Health/medicine news",
            "tool_check": "get_top_headlines",
        },
        {
            "id": "TC-05",
            "name": "Factual Chat — ML Definition",
            "input": "What is machine learning?",
            "check": lambda r: len(r) > 100,
            "expect": "Clear ML explanation",
            "tool_check": None,
        },
        {
            "id": "TC-06",
            "name": "Web Search — CEO Query",
            "input": "Who is the current CEO of Microsoft?",
            "check": lambda r: any(kw in r.lower() for kw in ["satya", "nadella", "microsoft"]),
            "expect": "Satya Nadella mentioned",
            "tool_check": "search_web",
        },
        {
            "id": "TC-07",
            "name": "Specific News Search",
            "input": "Search for recent developments in electric vehicles",
            "check": lambda r: any(kw in r.lower() for kw in ["electric", "ev", "vehicle", "tesla", "battery"]),
            "expect": "EV-related content",
            "tool_check": "search_news",
        },
        {
            "id": "TC-08",
            "name": "Science News",
            "input": "What's happening in science and space exploration today?",
            "check": lambda r: len(r) > 50,
            "expect": "Science/space content",
            "tool_check": "get_top_headlines",
        },
        {
            "id": "TC-09",
            "name": "List Categories",
            "input": "What news categories do you support?",
            "check": lambda r: any(kw in r.lower() for kw in ["technology", "finance", "sports", "health"]),
            "expect": "Category list shown",
            "tool_check": "get_news_categories",
        },
        {
            "id": "TC-10",
            "name": "Ambiguous Query Fallback",
            "input": "news",
            "check": lambda r: len(r) > 50,
            "expect": "Non-empty response, no crash",
            "tool_check": None,
        },
    ]

    col_run, col_info = st.columns([2, 3])
    with col_run:
        run_all = st.button("▶ Run All Test Cases", use_container_width=True)
    with col_info:
        st.info("Runs 10 automated tests against the live agent. Takes ~60 seconds.")

    if run_all:
        from workflow import run_agent
        import uuid

        results = []
        progress = st.progress(0)
        status_placeholder = st.empty()

        for i, tc in enumerate(TEST_CASES):
            status_placeholder.text(f"Running {tc['id']}: {tc['name']}...")
            try:
                result = run_agent(tc["input"], thread_id=f"test-{uuid.uuid4()}")
                response = result["response"]
                tools = result["tools_used"]

                passed = tc["check"](response)
                tool_ok = True
                if tc["tool_check"]:
                    tool_ok = tc["tool_check"] in tools

                results.append({
                    "ID": tc["id"],
                    "Test": tc["name"],
                    "Status": "PASS" if passed else "FAIL",
                    "Tool Check": "OK" if tool_ok else "MISS",
                    "Tools Used": ", ".join(tools) if tools else "none (LLM only)",
                    "Response Preview": response[:100] + "..." if len(response) > 100 else response,
                })
            except Exception as e:
                results.append({
                    "ID": tc["id"],
                    "Test": tc["name"],
                    "Status": "ERROR",
                    "Tool Check": "N/A",
                    "Tools Used": "error",
                    "Response Preview": str(e)[:100],
                })

            progress.progress((i + 1) / len(TEST_CASES))

        status_placeholder.empty()

        passed_count = sum(1 for r in results if r["Status"] == "PASS")
        total = len(results)
        pct = int(passed_count / total * 100)

        if pct >= 80:
            st.success(f"Result: {passed_count}/{total} tests passed ({pct}%) — PASS")
        else:
            st.warning(f"Result: {passed_count}/{total} tests passed ({pct}%) — Below 80% threshold")

        import pandas as pd
        df = pd.DataFrame(results)

        def color_status(val):
            if val == "PASS":
                return "background-color: #d4edda; color: #155724"
            elif val == "FAIL":
                return "background-color: #f8d7da; color: #721c24"
            else:
                return "background-color: #fff3cd; color: #856404"

        st.dataframe(
            df.style.applymap(color_status, subset=["Status"]),
            use_container_width=True,
            height=400,
        )
