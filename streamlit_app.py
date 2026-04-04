"""
InsightForge — AI-Powered Business Intelligence Assistant
Streamlit UI

Run: streamlit run streamlit_app.py
"""

import os
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import MergerRetriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.retrievers import BaseRetriever
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import Field
from typing import List

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InsightForge — AI-Powered BI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_PATH = "../Datasets_New/sales_data.csv"

# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    df["Year"]       = df["Date"].dt.year
    df["Month"]      = df["Date"].dt.month
    df["Quarter"]    = df["Date"].dt.quarter
    df["Month_Name"] = df["Date"].dt.strftime("%b")
    return df


def create_knowledge_documents(df: pd.DataFrame) -> list:
    docs = []
    docs.append(Document(
        page_content=(
            f"Overall Business Summary:\n"
            f"Total Sales Revenue: ${df['Sales'].sum():,.0f}\n"
            f"Average Daily Sales: ${df['Sales'].mean():.2f}\n"
            f"Median Daily Sales:  ${df['Sales'].median():.2f}\n"
            f"Std Dev of Sales:    ${df['Sales'].std():.2f}\n"
            f"Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}\n"
            f"Total Transactions: {len(df):,}"
        ),
        metadata={"source": "overall_summary"}
    ))

    product_stats = df.groupby("Product")["Sales"].agg(["sum", "mean", "count"]).round(2)
    text = "Product Sales Analysis:\n" + "\n".join(
        f"  {p}: Total=${r['sum']:,.0f}, Avg=${r['mean']:.2f}, Days={int(r['count'])}"
        for p, r in product_stats.iterrows()
    )
    docs.append(Document(page_content=text, metadata={"source": "product_analysis"}))

    region_stats = df.groupby("Region")["Sales"].agg(["sum", "mean", "count"]).round(2)
    text = "Regional Sales Analysis:\n" + "\n".join(
        f"  {r}: Total=${row['sum']:,.0f}, Avg=${row['mean']:.2f}, Days={int(row['count'])}"
        for r, row in region_stats.iterrows()
    )
    docs.append(Document(page_content=text, metadata={"source": "regional_analysis"}))

    monthly = df.groupby(["Year", "Month"])["Sales"].sum().reset_index()
    text = "Monthly Sales Trends:\n" + "\n".join(
        f"  {int(r['Year'])}-{int(r['Month']):02d}: ${r['Sales']:,.0f}"
        for _, r in monthly.iterrows()
    )
    docs.append(Document(page_content=text, metadata={"source": "monthly_trends"}))

    age_stats    = df["Customer_Age"].describe()
    gender_sales = df.groupby("Customer_Gender")["Sales"].agg(["sum", "mean"]).round(2)
    sat_stats    = df["Customer_Satisfaction"].describe()
    text = (
        f"Customer Demographics Analysis:\n"
        f"  Age — Mean: {age_stats['mean']:.1f}, Min: {age_stats['min']:.0f}, "
        f"Max: {age_stats['max']:.0f}, Std: {age_stats['std']:.1f}\n"
        f"  Satisfaction — Mean: {sat_stats['mean']:.2f}\n"
        f"  Gender Sales:\n"
        + "\n".join(
            f"    {g}: Total=${row['sum']:,.0f}, Avg=${row['mean']:.2f}"
            for g, row in gender_sales.iterrows()
        )
    )
    docs.append(Document(page_content=text, metadata={"source": "customer_demographics"}))
    return docs


class SalesDataRetriever(BaseRetriever):
    dataframe: pd.DataFrame = Field(description="Sales DataFrame")

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str) -> List[Document]:
        docs, q = [], query.lower()
        docs.append(Document(
            page_content=(
                f"Overall Summary:\n"
                f"  Total Sales: ${self.dataframe['Sales'].sum():,.0f}\n"
                f"  Avg Daily: ${self.dataframe['Sales'].mean():.2f}\n"
                f"  Median: ${self.dataframe['Sales'].median():.2f}\n"
                f"  Records: {len(self.dataframe):,}"
            ),
            metadata={"source": "live_overall"}
        ))
        if any(w in q for w in ["product", "widget", "best", "top", "perform"]):
            ps = self.dataframe.groupby("Product")["Sales"].agg(["sum","mean"]).round(2)
            text = "Live Product Stats:\n" + "\n".join(
                f"  {p}: Total=${r['sum']:,.0f}, Avg/day=${r['mean']:.2f}"
                for p, r in ps.iterrows()
            )
            docs.append(Document(page_content=text, metadata={"source": "live_product"}))
        if any(w in q for w in ["region", "north", "south", "east", "west", "area"]):
            rs = self.dataframe.groupby("Region")["Sales"].agg(["sum","mean"]).round(2)
            text = "Live Regional Stats:\n" + "\n".join(
                f"  {r}: Total=${row['sum']:,.0f}, Avg/day=${row['mean']:.2f}"
                for r, row in rs.iterrows()
            )
            docs.append(Document(page_content=text, metadata={"source": "live_region"}))
        if any(w in q for w in ["time", "month", "year", "quarter", "trend", "season"]):
            monthly = self.dataframe.groupby(["Year","Month"])["Sales"].sum().reset_index()
            text = "Live Monthly Sales:\n" + "\n".join(
                f"  {int(r['Year'])}-{int(r['Month']):02d}: ${r['Sales']:,.0f}"
                for _, r in monthly.iterrows()
            )
            docs.append(Document(page_content=text, metadata={"source": "live_monthly"}))
        if any(w in q for w in ["customer", "age", "gender", "satisfaction", "demograph"]):
            g = self.dataframe.groupby("Customer_Gender")["Sales"].mean().round(2)
            text = (
                f"Live Customer Stats:\n"
                f"  Avg Age: {self.dataframe['Customer_Age'].mean():.1f}\n"
                f"  Avg Satisfaction: {self.dataframe['Customer_Satisfaction'].mean():.2f}\n"
                + "\n".join(f"  {gender}: Avg=${val:.2f}" for gender, val in g.items())
            )
            docs.append(Document(page_content=text, metadata={"source": "live_customer"}))
        return docs


def format_docs(docs):
    seen, parts = set(), []
    for doc in docs:
        k = doc.metadata.get("source", "")
        if k not in seen:
            seen.add(k)
            parts.append(doc.page_content)
    return "\n\n---\n\n".join(parts)


@st.cache_resource
def build_chain(_df):
    """Build and cache the InsightForge RAG chain with memory."""
    embeddings     = OpenAIEmbeddings()
    knowledge_docs = create_knowledge_documents(_df)
    splitter       = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    split_docs     = splitter.split_documents(knowledge_docs)
    vectorstore    = FAISS.from_documents(split_docs, embeddings)
    faiss_ret      = vectorstore.as_retriever(search_kwargs={"k": 4})
    pandas_ret     = SalesDataRetriever(dataframe=_df)
    hybrid_ret     = MergerRetriever(retrievers=[pandas_ret, faiss_ret])

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are InsightForge, an AI-powered Business Intelligence Assistant.
Use ONLY the data context below. Always cite specific numbers.
If the data does not contain the answer, say so clearly.

Context:
{context}"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    core_chain = (
        RunnablePassthrough.assign(
            context=lambda x: format_docs(hybrid_ret.invoke(x["question"]))
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    store: dict = {}

    def get_session_history(session_id: str) -> ChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    chain = RunnableWithMessageHistory(
        core_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history"
    )
    return chain, store


# ── Visualizations ────────────────────────────────────────────────────────────

def plot_sales_trends(df: pd.DataFrame):
    monthly = df.groupby(df["Date"].dt.to_period("M"))["Sales"].sum().reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(monthly["Date"], monthly["Sales"], marker="o", linewidth=2, color="#2E86AB", markersize=4)
    ax.fill_between(monthly["Date"], monthly["Sales"], alpha=0.15, color="#2E86AB")
    peak = monthly.loc[monthly["Sales"].idxmax()]
    ax.annotate(
        f"Peak\n${peak['Sales']:,.0f}",
        xy=(peak["Date"], peak["Sales"]),
        xytext=(12, 12), textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="red"), fontsize=8, color="red"
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.set_title("Monthly Sales Trends", fontweight="bold")
    ax.set_xlabel("Month"); ax.set_ylabel("Total Sales ($)")
    plt.xticks(rotation=45); plt.tight_layout()
    return fig


def plot_product_performance(df: pd.DataFrame):
    ps = df.groupby("Product")["Sales"].agg(["sum","mean"]).sort_values("sum", ascending=False)
    colors = ["#2E86AB","#A23B72","#F18F01","#C73E1D"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    bars = axes[0].bar(ps.index, ps["sum"], color=colors)
    axes[0].bar_label(bars, labels=[f"${v:,.0f}" for v in ps["sum"]], padding=3, fontsize=8)
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    axes[0].set_title("Total Sales by Product", fontweight="bold"); axes[0].set_xlabel("Product")
    bars2 = axes[1].bar(ps.index, ps["mean"], color=colors)
    axes[1].bar_label(bars2, labels=[f"${v:.0f}" for v in ps["mean"]], padding=3, fontsize=8)
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    axes[1].set_title("Avg Daily Sales by Product", fontweight="bold"); axes[1].set_xlabel("Product")
    plt.tight_layout(); return fig


def plot_regional_analysis(df: pd.DataFrame):
    rs = df.groupby("Region")["Sales"].sum().sort_values(ascending=True)
    colors = ["#264653","#2A9D8F","#E9C46A","#E76F51"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    bars = axes[0].barh(rs.index, rs.values, color=colors)
    axes[0].bar_label(bars, labels=[f"${v:,.0f}" for v in rs.values], padding=4, fontsize=8)
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    axes[0].set_title("Total Sales by Region", fontweight="bold")
    axes[1].pie(rs.values, labels=rs.index, autopct="%1.1f%%", colors=colors, startangle=90)
    axes[1].set_title("Regional Market Share", fontweight="bold")
    plt.tight_layout(); return fig


def plot_customer_demographics(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.5))
    axes[0].hist(df["Customer_Age"], bins=20, color="#2E86AB", edgecolor="white")
    axes[0].axvline(df["Customer_Age"].mean(), color="red", linestyle="--",
                    label=f"Mean: {df['Customer_Age'].mean():.1f}")
    axes[0].set_title("Customer Age Distribution", fontweight="bold")
    axes[0].set_xlabel("Age"); axes[0].set_ylabel("Count"); axes[0].legend(fontsize=8)
    gs = df.groupby("Customer_Gender")["Sales"].mean()
    bar_colors = ["#E76F51" if g == "Female" else "#2E86AB" for g in gs.index]
    bars = axes[1].bar(gs.index, gs.values, color=bar_colors)
    axes[1].bar_label(bars, labels=[f"${v:.0f}" for v in gs.values], padding=3, fontsize=9)
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    axes[1].set_title("Avg Daily Sales by Gender", fontweight="bold")
    axes[2].hist(df["Customer_Satisfaction"], bins=20, color="#A23B72", edgecolor="white")
    axes[2].axvline(df["Customer_Satisfaction"].mean(), color="orange", linestyle="--",
                    label=f"Mean: {df['Customer_Satisfaction'].mean():.2f}")
    axes[2].set_title("Customer Satisfaction", fontweight="bold")
    axes[2].set_xlabel("Score"); axes[2].set_ylabel("Count"); axes[2].legend(fontsize=8)
    plt.tight_layout(); return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 InsightForge")
    st.caption("AI-Powered Business Intelligence")
    st.divider()

    # API key input (if not in .env)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password", help="Enter your key if not set in .env")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    st.divider()
    page = st.radio(
        "Navigate",
        ["📈 Dashboard", "💬 AI Assistant", "📋 Data Explorer"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Advanced Generative AI — Capstone Project")


# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Dataset not found at `{DATA_PATH}`. Make sure the path is correct.")
    st.stop()

sns.set_theme(style="whitegrid")

# ── Page: Dashboard ───────────────────────────────────────────────────────────
if page == "📈 Dashboard":
    st.title("📊 InsightForge Business Dashboard")
    st.caption(f"Dataset: {len(df):,} transactions | {df['Date'].min().date()} → {df['Date'].max().date()}")

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue",    f"${df['Sales'].sum():,.0f}")
    col2.metric("Avg Daily Sales",  f"${df['Sales'].mean():,.0f}")
    col3.metric("Avg Satisfaction", f"{df['Customer_Satisfaction'].mean():.2f} / 5")
    col4.metric("Avg Customer Age", f"{df['Customer_Age'].mean():.1f} yrs")

    st.divider()

    # Row 1
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Sales Trends Over Time")
        st.pyplot(plot_sales_trends(df))
    with col_r:
        st.subheader("Regional Analysis")
        st.pyplot(plot_regional_analysis(df))

    # Row 2
    st.subheader("Product Performance")
    st.pyplot(plot_product_performance(df))

    # Row 3
    st.subheader("Customer Demographics")
    st.pyplot(plot_customer_demographics(df))


# ── Page: AI Assistant ────────────────────────────────────────────────────────
elif page == "💬 AI Assistant":
    st.title("💬 InsightForge AI Assistant")
    st.caption("Ask anything about your sales data. The assistant remembers your conversation.")

    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Please enter your OpenAI API key in the sidebar.")
        st.stop()

    chain, session_store = build_chain(df)

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Hello! I'm **InsightForge**, your AI-powered Business Intelligence Assistant. "
                "I have full access to your sales data and can answer questions about:\n\n"
                "- 📦 **Product performance** (best sellers, comparisons)\n"
                "- 🗺️ **Regional analysis** (top regions, market share)\n"
                "- 📅 **Sales trends** (monthly, quarterly, seasonality)\n"
                "- 👥 **Customer insights** (demographics, satisfaction)\n\n"
                "What would you like to know?"
            )
        })

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Suggested questions
    with st.expander("💡 Suggested Questions"):
        suggestions = [
            "What is the total sales revenue?",
            "Which product performs best and in which region?",
            "Show me the sales trends — any seasonal patterns?",
            "What are the key customer demographics?",
            "Compare Widget A vs Widget B performance.",
        ]
        for s in suggestions:
            if st.button(s, key=s):
                st.session_state._prefill = s

    # Chat input
    prefill = st.session_state.pop("_prefill", None)
    user_input = st.chat_input("Ask InsightForge...") or prefill

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = chain.invoke(
                    {"question": user_input},
                    config={"configurable": {"session_id": "streamlit_session"}}
                )
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        if "streamlit_session" in session_store:
            del session_store["streamlit_session"]
        st.rerun()


# ── Page: Data Explorer ───────────────────────────────────────────────────────
elif page == "📋 Data Explorer":
    st.title("📋 Data Explorer")
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        products = st.multiselect("Products", df["Product"].unique(), default=list(df["Product"].unique()))
    with col2:
        regions  = st.multiselect("Regions",  df["Region"].unique(),  default=list(df["Region"].unique()))
    with col3:
        years    = st.multiselect("Years",    sorted(df["Year"].unique()), default=sorted(df["Year"].unique()))

    filtered = df[
        df["Product"].isin(products) &
        df["Region"].isin(regions) &
        df["Year"].isin(years)
    ]

    # Summary stats for filtered data
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Filtered Records",  f"{len(filtered):,}")
    col_b.metric("Total Revenue",     f"${filtered['Sales'].sum():,.0f}")
    col_c.metric("Avg Daily Sales",   f"${filtered['Sales'].mean():,.0f}")

    # Pivot table
    st.subheader("Sales by Product × Region")
    pivot = filtered.groupby(["Product","Region"])["Sales"].sum().unstack(fill_value=0)
    st.dataframe(pivot.style.format("${:,.0f}").background_gradient(cmap="Blues"), use_container_width=True)

    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(filtered.head(200), use_container_width=True)

    # Download
    csv = filtered.to_csv(index=False).encode()
    st.download_button("⬇️ Download Filtered Data (CSV)", csv, "filtered_sales.csv", "text/csv")
