"""
NewsGenie — AI-Powered Information and News Assistant
Streamlit UI  |  Run: streamlit run streamlit_app.py
"""
import os, json, warnings, time
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
from typing import TypedDict, List, Annotated
import operator
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NewsGenie — AI News Assistant",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Lazy imports (only after API key confirmed) ───────────────────────────────
def get_imports():
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langgraph.graph import StateGraph, END, START
    from langgraph.checkpoint.memory import MemorySaver
    from duckduckgo_search import DDGS
    import requests
    return ChatOpenAI, HumanMessage, AIMessage, SystemMessage, ChatPromptTemplate, \
           StateGraph, END, START, MemorySaver, DDGS, requests

NEWS_CATEGORIES = ["Technology", "Finance", "Sports", "Health", "Science", "General"]
CATEGORY_ICONS  = {"Technology":"💻","Finance":"💰","Sports":"⚽","Health":"🏥","Science":"🔬","General":"🌐"}

# ── Build NewsGenie graph ─────────────────────────────────────────────────────
@st.cache_resource
def build_newsgenie():
    ChatOpenAI, HumanMessage, AIMessage, SystemMessage, ChatPromptTemplate, \
    StateGraph, END, START, MemorySaver, DDGS, requests = get_imports()

    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    class NewsGenieState(TypedDict):
        user_query    : str
        query_type    : str
        news_category : str
        news_results  : List[dict]
        search_results: str
        chat_response : str
        final_response: str
        error         : str
        messages      : Annotated[List, operator.add]

    def route_query(state):
        router_prompt = ChatPromptTemplate.from_messages([
            ("system", """Classify the query into: "news", "search", or "chat".
Also identify news category: technology, finance, sports, health, science, general.
Respond JSON only: {"type": "...", "category": "..."}"""),
            ("human", "{query}")
        ])
        try:
            result  = (router_prompt | llm).invoke({"query": state["user_query"]})
            content = result.content.strip()
            if "```" in content:
                content = content.split("```")[1].replace("json","").strip()
            parsed = json.loads(content)
            qt = parsed.get("type","chat")
            cat = parsed.get("category","general").lower()
            if qt not in ("news","search","chat"): qt = "chat"
        except:
            qt, cat = "chat", "general"
        return {**state, "query_type": qt, "news_category": cat, "error": ""}

    def fetch_news(state):
        cat   = state.get("news_category","general")
        query = state["user_query"]
        # Try NewsAPI
        articles = []
        if NEWSAPI_KEY:
            try:
                cat_map = {"finance":"business","technology":"technology","sports":"sports",
                           "health":"health","science":"science","general":"general"}
                r = requests.get("https://newsapi.org/v2/top-headlines",
                    params={"apiKey":NEWSAPI_KEY,"language":"en","pageSize":5,"category":cat_map.get(cat,"general")},
                    timeout=8)
                if r.status_code == 200:
                    articles = [{"title":a.get("title",""),"source":a.get("source",{}).get("name",""),
                                 "summary":a.get("description","") or "","url":a.get("url",""),
                                 "published":a.get("publishedAt","")[:10]} for a in r.json().get("articles",[]) if a.get("title")]
            except: pass
        # DuckDuckGo fallback
        if not articles:
            try:
                with DDGS() as ddgs:
                    raw = list(ddgs.news(f"{cat} news today", max_results=5))
                articles = [{"title":r.get("title",""),"source":r.get("source",""),
                             "summary":r.get("body","")[:200],"url":r.get("url",""),
                             "published":r.get("date","")[:10]} for r in raw if r.get("title")]
            except: pass
        if not articles:
            return {**state,"news_results":[],"final_response":f"⚠️ No {cat} news found right now.","error":"no_news"}
        return {**state,"news_results":articles,"error":""}

    def web_search(state):
        query = state["user_query"]
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=4))
            snippets = "\n\n".join(f"**{r.get('title','')}**\n{r.get('body','')[:300]}" for r in results)
            return {**state,"search_results":snippets,"error":""}
        except:
            fallback = llm.invoke(f"Answer briefly: {query}").content
            return {**state,"search_results":fallback,"error":"search_fallback"}

    SYSTEM = """You are NewsGenie, a helpful AI news and information assistant. Be concise and friendly."""
    def chat(state):
        msgs = [SystemMessage(content=SYSTEM)] + state.get("messages",[])[-6:] + [HumanMessage(content=state["user_query"])]
        response = llm.invoke(msgs)
        return {**state,"chat_response":response.content,"error":""}

    def format_resp(state):
        if state.get("error") == "no_news":
            return {**state,"messages":[HumanMessage(content=state["user_query"]),AIMessage(content=state["final_response"])]}
        qtype = state.get("query_type","chat")
        if qtype == "news":
            articles  = state.get("news_results",[])
            category  = state.get("news_category","general").title()
            icon      = CATEGORY_ICONS.get(category,"📰")
            lines     = [f"{icon} **Top {category} News** — {datetime.now().strftime('%b %d, %Y')}\n"]
            for i, a in enumerate(articles,1):
                lines.append(f"**{i}. {a['title']}**")
                if a.get("summary"): lines.append(f"   {a['summary'][:150]}...")
                if a.get("source"):  lines.append(f"   *{a['source']}*")
                if a.get("url"):     lines.append(f"   [Read more]({a['url']})")
                lines.append("")
            final = "\n".join(lines)
        elif qtype == "search":
            snippets = state.get("search_results","")
            if snippets:
                synth = f"Answer using these search results.\nQuestion: {state['user_query']}\n\nResults:\n{snippets[:2000]}\n\nAnswer in 2-4 sentences."
                final = llm.invoke(synth).content
            else:
                final = "Couldn't find current information. Please rephrase."
        else:
            final = state.get("chat_response","I'm not sure. Could you rephrase?")

        new_msgs = [HumanMessage(content=state["user_query"]), AIMessage(content=final)]
        return {**state,"final_response":final,"messages":new_msgs}

    g = StateGraph(NewsGenieState)
    g.add_node("router",    route_query)
    g.add_node("news",      fetch_news)
    g.add_node("search",    web_search)
    g.add_node("chat",      chat)
    g.add_node("formatter", format_resp)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s.get("query_type","chat"),
                             {"news":"news","search":"search","chat":"chat"})
    g.add_edge("news",      "formatter")
    g.add_edge("search",    "formatter")
    g.add_edge("chat",      "formatter")
    g.add_edge("formatter", END)

    return g.compile(checkpointer=MemorySaver())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📰 NewsGenie")
    st.caption("AI-Powered News & Information Assistant")
    st.divider()

    api_key = os.getenv("OPENAI_API_KEY","")
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key: os.environ["OPENAI_API_KEY"] = api_key

    newsapi_key = os.getenv("NEWSAPI_KEY","")
    if not newsapi_key:
        newsapi_key = st.text_input("NewsAPI Key (optional)", type="password",
                                     help="Get free key at newsapi.org — DuckDuckGo used if blank")
        if newsapi_key: os.environ["NEWSAPI_KEY"] = newsapi_key

    st.divider()
    st.subheader("📂 News Category")
    selected_cat = st.selectbox("Select category for news",
                                NEWS_CATEGORIES, index=0,
                                format_func=lambda c: f"{CATEGORY_ICONS.get(c,'📰')} {c}")

    st.divider()
    page = st.radio("Navigate", ["💬 Chat & News", "📊 Dashboard", "🧪 Test Cases"],
                    label_visibility="collapsed")
    st.divider()
    st.caption("Course End Project — Applied GenAI")

# ── Init agent ────────────────────────────────────────────────────────────────
if "newsgenie" not in st.session_state:
    st.session_state.newsgenie = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "test_results" not in st.session_state:
    st.session_state.test_results = []

if api_key and st.session_state.newsgenie is None:
    with st.spinner("Loading NewsGenie..."):
        try:
            st.session_state.newsgenie = build_newsgenie()
        except Exception as e:
            st.error(f"Failed to initialise: {e}")

def run_query(query, category="general"):
    from langchain_core.messages import HumanMessage
    config = {"configurable": {"thread_id": "streamlit_session"}}
    initial = {"user_query":query,"query_type":"","news_category":category.lower(),
               "news_results":[],"search_results":"","chat_response":"",
               "final_response":"","error":"","messages":[]}
    return st.session_state.newsgenie.invoke(initial, config=config)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Chat & News
# ══════════════════════════════════════════════════════════════════════════════
if page == "💬 Chat & News":
    st.title("📰 NewsGenie — AI News & Information Assistant")

    if not api_key:
        st.warning("Enter your OpenAI API key in the sidebar to get started.")
        st.stop()
    if st.session_state.newsgenie is None:
        st.info("Initialising NewsGenie...")
        st.stop()

    # Welcome message
    if not st.session_state.chat_history:
        st.session_state.chat_history.append({"role":"assistant","content":
            f"👋 Hello! I'm **NewsGenie**, your AI news assistant.\n\n"
            f"I can:\n- 📰 Fetch **{selected_cat}** headlines (currently selected)\n"
            f"- 🔍 Search the web for live information\n- 💬 Answer general questions\n\n"
            f"Just type a question or ask for today's news!"})

    # Quick news buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"📰 Today's {selected_cat} News"):
            st.session_state._prefill = f"What are the latest {selected_cat.lower()} news today?"
    with col2:
        if st.button("🔍 Search Web"):
            st.session_state._prefill = f"Search for the latest updates on {selected_cat.lower()}"
    with col3:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.divider()

    # Chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prefill = st.session_state.pop("_prefill", None)
    user_input = st.chat_input(f"Ask NewsGenie about {selected_cat.lower()} news or anything else...") or prefill

    if user_input:
        st.session_state.chat_history.append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("NewsGenie is fetching..."):
                result = run_query(user_input, selected_cat)
                response = result.get("final_response","No response.")
                qtype    = result.get("query_type","?")
                cat      = result.get("news_category","?")

            # Route badge
            badge_color = {"news":"🟢","search":"🔵","chat":"🟣"}.get(qtype,"⚪")
            st.caption(f"{badge_color} Route: **{qtype}** | Category: **{cat}**")
            st.markdown(response)

            # Show articles in expander
            articles = result.get("news_results",[])
            if articles:
                with st.expander(f"📋 All {len(articles)} articles"):
                    for a in articles:
                        st.markdown(f"**{a['title']}** — *{a.get('source','')}* ({a.get('published','')})")
                        if a.get("summary"): st.caption(a["summary"][:120])
                        if a.get("url"):     st.markdown(f"[🔗 Read more]({a['url']})")
                        st.divider()

        st.session_state.chat_history.append({"role":"assistant","content":response})

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.title("📊 NewsGenie Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("News Categories", len(NEWS_CATEGORIES))
    col2.metric("Chat Sessions", len([m for m in st.session_state.chat_history if m["role"]=="user"]))
    col3.metric("Test Cases Run", len(st.session_state.test_results))

    st.divider()
    st.subheader("🔀 LangGraph Workflow Architecture")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis("off")

    def box(x,y,w,h,text,color):
        rect = mpatches.FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle="round,pad=0.1",
               facecolor=color,edgecolor="#333",linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x,y,text,ha="center",va="center",fontsize=9,fontweight="bold",color="white")

    def arrow(x1,y1,x2,y2,label=""):
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle="->",color="#555",lw=1.5))
        if label: ax.text((x1+x2)/2+0.1,(y1+y2)/2,label,fontsize=8,color="#555",style="italic")

    box(5,5.2,2.5,0.7,"User Query","#2E86AB")
    box(5,4.0,2.5,0.7,"Router Node\n(classify intent)","#A23B72")
    box(2,2.5,2.2,0.7,"News Node\n(NewsAPI/DuckDuckGo)","#2A9D8F")
    box(5,2.5,2.2,0.7,"Search Node\n(DuckDuckGo Web)","#F18F01")
    box(8,2.5,2.2,0.7,"Chat Node\n(GPT-4o-mini)","#264653")
    box(5,1.0,2.5,0.7,"Formatter Node","#E76F51")

    arrow(5,4.85,5,4.35)
    arrow(3.7,3.65,2.5,2.85,"news")
    arrow(5,3.65,5,2.85,"search")
    arrow(6.3,3.65,7.5,2.85,"chat")
    arrow(2,2.15,4.0,1.35)
    arrow(5,2.15,5,1.35)
    arrow(8,2.15,6.0,1.35)
    ax.text(5,0.3,"MemorySaver — conversation memory",ha="center",fontsize=9,color="#777",style="italic")
    ax.set_title("NewsGenie — LangGraph Workflow",fontsize=13,fontweight="bold",pad=15)
    plt.tight_layout()
    st.pyplot(fig)

    st.divider()
    st.subheader("📂 Supported News Categories")
    cols = st.columns(len(NEWS_CATEGORIES))
    for i, cat in enumerate(NEWS_CATEGORIES):
        cols[i].metric(f"{CATEGORY_ICONS[cat]} {cat}", "Active")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Test Cases
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧪 Test Cases":
    st.title("🧪 NewsGenie Test Cases")
    st.caption("Run automated test cases to validate routing, news fetching, and chat responses.")

    if not api_key or st.session_state.newsgenie is None:
        st.warning("API key required to run tests.")
        st.stop()

    test_cases = [
        ("TC-01","What are the latest technology news?","news","technology"),
        ("TC-02","Show me top finance headlines today","news","finance"),
        ("TC-03","What are today's top sports stories?","news","sports"),
        ("TC-04","What is machine learning?","chat","general"),
        ("TC-05","Latest news in health and medicine","news","health"),
        ("TC-06","What is ChatGPT?","chat","general"),
        ("TC-07","What's happening in science today?","news","science"),
        ("TC-08","Search for latest OpenAI news","search","general"),
        ("TC-09","Explain quantum computing simply","chat","general"),
        ("TC-10","Give me general news headlines","news","general"),
    ]

    if st.button("▶️ Run All Test Cases", type="primary"):
        results = []
        progress = st.progress(0)
        status_box = st.empty()

        for i, (tc_id, query, exp_type, exp_cat) in enumerate(test_cases):
            status_box.info(f"Running {tc_id}: {query[:60]}...")
            try:
                result = run_query(query, exp_cat)
                actual_type = result.get("query_type","")
                has_resp    = bool(result.get("final_response","").strip())
                type_match  = actual_type == exp_type
                status      = "✅ PASS" if (type_match and has_resp) else "⚠️ FAIL"
                results.append({"ID":tc_id,"Query":query[:55]+"...","Expected":exp_type,
                                 "Got":actual_type,"Category":result.get("news_category",""),
                                 "Response":has_resp,"Status":status})
            except Exception as e:
                results.append({"ID":tc_id,"Query":query[:55]+"...","Expected":exp_type,
                                 "Got":"ERROR","Category":"","Response":False,
                                 "Status":"❌ ERROR"})
            progress.progress((i+1)/len(test_cases))
            time.sleep(0.5)

        status_box.empty()
        st.session_state.test_results = results
        df = pd.DataFrame(results)
        passed = df["Status"].str.contains("PASS").sum()
        st.success(f"✅ {passed}/{len(test_cases)} test cases passed ({passed/len(test_cases)*100:.0f}%)")

    if st.session_state.test_results:
        df = pd.DataFrame(st.session_state.test_results)

        # Colour rows
        def highlight(row):
            color = "#d4edda" if "PASS" in row["Status"] else "#f8d7da" if "ERROR" in row["Status"] else "#fff3cd"
            return [f"background-color: {color}"]*len(row)

        st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

        # Summary chart
        fig, ax = plt.subplots(figsize=(5,3))
        counts = df["Status"].value_counts()
        colors = ["#2A9D8F" if "PASS" in s else "#E76F51" for s in counts.index]
        ax.bar(counts.index, counts.values, color=colors, width=0.4)
        for i, (idx, val) in enumerate(counts.items()):
            ax.text(i, val+0.1, str(val), ha="center", fontsize=11, fontweight="bold")
        ax.set_title("Test Results Summary", fontweight="bold")
        ax.set_ylabel("Count")
        plt.tight_layout()
        st.pyplot(fig)
