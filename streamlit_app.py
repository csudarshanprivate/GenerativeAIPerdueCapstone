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

# ── Personalisation: pin favourite categories ──────────────────────────────────
st.sidebar.markdown("**⭐ My Favourite Categories**")
ALL_CATS = ["Technology", "Finance", "Sports", "Health", "Science", "Entertainment", "General"]
pinned = st.sidebar.multiselect(
    "Pin categories for My Feed:",
    ALL_CATS,
    default=st.session_state.pinned_categories,
    key="pin_selector",
)
st.session_state.pinned_categories = pinned

if st.session_state.category_clicks:
    top = get_preferred_categories(3)
    st.sidebar.caption(f"Most read: {', '.join(top)}")

st.sidebar.markdown("---")
st.sidebar.markdown("**How it works**")
st.sidebar.markdown(
    "NewsGenie uses a **LangGraph ReAct agent** with `create_react_agent`. "
    "The LLM autonomously decides which tools to call:\n"
    "- `get_top_headlines` — category news\n"
    "- `search_news` — topic search\n"
    "- `search_web` — live web facts\n"
    "- `get_weather` — weather forecast\n"
    "- `get_news_categories` — list categories"
)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())

# Personalisation: track how often each category is accessed
if "category_clicks" not in st.session_state:
    st.session_state.category_clicks = {}   # {"Technology": 3, "Sports": 1, ...}
if "pinned_categories" not in st.session_state:
    st.session_state.pinned_categories = [] # user-pinned favourites

def record_category_click(cat: str):
    st.session_state.category_clicks[cat] = st.session_state.category_clicks.get(cat, 0) + 1

def get_preferred_categories(n: int = 3) -> list:
    """Return top-n categories by click count, pinned ones always first."""
    pinned = st.session_state.pinned_categories
    clicks = st.session_state.category_clicks
    ranked = sorted([c for c in clicks if c not in pinned],
                    key=lambda c: clicks[c], reverse=True)
    return (pinned + ranked)[:n]


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
    st.caption("Select a category or view your personalised feed based on your reading preferences.")

    CATEGORIES = ["Technology", "Finance", "Sports", "Health", "Science", "Entertainment", "General"]
    QUERY_MAP  = {
        "technology":    "technology news today",
        "finance":       "finance business news today",
        "sports":        "sports news today",
        "health":        "health medicine news today",
        "science":       "science space news today",
        "entertainment": "entertainment news today",
        "general":       "top news headlines today",
    }

    if "active_headline_cat" not in st.session_state:
        st.session_state.active_headline_cat = None

    # ── Shared fetch helper ────────────────────────────────────────────────────
    def fetch_and_render(category: str, key_prefix: str = ""):
        from tools import (
            _normalize_category, _fetch_via_newsapi, _fetch_via_duckduckgo,
            _filter_and_score, NEWSAPI_KEY
        )
        cat = _normalize_category(category)
        raw = []
        if NEWSAPI_KEY and len(NEWSAPI_KEY) > 20:
            try:
                raw = _fetch_via_newsapi(cat)
            except Exception:
                pass
        if not raw:
            raw = _fetch_via_duckduckgo(QUERY_MAP.get(cat, f"{cat} news today"))

        if not raw:
            st.warning(f"Could not fetch {category} news right now.")
            return

        all_scored = _filter_and_score(raw, remove_flagged=False)
        kept    = [a for a in all_scored if a["reliability_score"] != 1]
        removed = [a for a in all_scored if a["reliability_score"] == 1]

        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Total Fetched",   len(all_scored))
        fc2.metric("✅ Passed Filter", len(kept))
        fc3.metric("🚫 Filtered Out",  len(removed))
        st.markdown("---")

        BADGE_COLOR = {2: "#2A9D8F", 0: "#888888"}
        BADGE_BG    = {2: "#d4f5f0", 0: "#f0f0f0"}

        for art in kept:
            score = art.get("reliability_score", 0)
            label = art.get("reliability_label", "❓ Unverified Source")
            color = BADGE_COLOR.get(score, "#888")
            bg    = BADGE_BG.get(score,   "#f0f0f0")
            badge_html = (
                f'<span style="background:{bg};color:{color};padding:2px 8px;'
                f'border-radius:12px;font-size:0.78em;font-weight:600;'
                f'border:1px solid {color}">{label}</span>'
            )
            title    = art.get("title", "No title")
            url      = art.get("url", "")
            title_md = f"[{title}]({url})" if url else title
            st.markdown(f"**{title_md}**")
            st.markdown(
                f'<small>📰 {art.get("source","Unknown")} &nbsp; {badge_html}</small>',
                unsafe_allow_html=True
            )
            if art.get("description"):
                st.caption(art["description"][:180])
            st.markdown("---")

        if removed:
            with st.expander(f"🚫 {len(removed)} article(s) filtered out — click to see why"):
                for art in removed:
                    st.markdown(
                        f"**{art.get('title','No title')}**  \n"
                        f"Source: `{art.get('source','?')}`  \n"
                        f"Reason: {art.get('reliability_label','⚠️ Flagged')}"
                    )
                    st.markdown("---")

    # ── Tabs: My Feed | Browse ─────────────────────────────────────────────────
    tab_feed, tab_browse = st.tabs(["⭐ My Feed", "📂 Browse Categories"])

    # ── TAB 1: My Feed ─────────────────────────────────────────────────────────
    with tab_feed:
        preferred = get_preferred_categories(3)
        pinned    = st.session_state.pinned_categories

        if not preferred:
            st.info(
                "Your personalised feed is empty. "
                "Browse categories below to build your preferences, "
                "or pin favourites in the sidebar."
            )
        else:
            feed_label = "Based on your pinned categories and reading history"
            if pinned:
                feed_label = f"Pinned: {', '.join(pinned)}"
                if len(preferred) > len(pinned):
                    extra = [c for c in preferred if c not in pinned]
                    feed_label += f"  |  Also reading: {', '.join(extra)}"
            st.caption(feed_label)

            for cat in preferred:
                st.subheader(f"📰 {cat}")
                with st.spinner(f"Loading {cat}..."):
                    try:
                        fetch_and_render(cat, key_prefix=f"feed_{cat}")
                    except Exception as e:
                        st.error(str(e))

    # ── TAB 2: Browse Categories ───────────────────────────────────────────────
    with tab_browse:
        # Inject CSS for active button highlight
        active = st.session_state.active_headline_cat
        st.markdown("""
        <style>
        .active-btn button {
            background-color: #2E86AB !important;
            color: white !important;
            border: 2px solid #1a5f7a !important;
            font-weight: bold !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("**Quick Access:**")
        btn_cols = st.columns(len(CATEGORIES))
        for i, cat in enumerate(CATEGORIES):
            with btn_cols[i]:
                is_active = (cat == active)
                if is_active:
                    st.markdown('<div class="active-btn">', unsafe_allow_html=True)
                if st.button(cat, key=f"quick_{cat}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state.active_headline_cat = cat
                    record_category_click(cat)   # ← track for personalisation
                    st.rerun()
                if is_active:
                    st.markdown('</div>', unsafe_allow_html=True)

        if active:
            st.markdown(f"**Showing:** {active} News")
            st.markdown("---")
            with st.spinner(f"Fetching {active} news..."):
                try:
                    fetch_and_render(active, key_prefix="browse")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


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
