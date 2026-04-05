"""
agents.py — NewsGenie ReAct Agent
Creates the LangGraph ReAct agent using create_react_agent with @tool-decorated tools.
The LLM autonomously decides which tools to call and in what sequence.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from tools import get_top_headlines, search_news, search_web, get_news_categories, get_weather

load_dotenv()

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are NewsGenie, an intelligent AI news and information assistant.

Your capabilities:
1. Fetch latest news headlines by category (technology, finance, sports, health, science, entertainment, general)
2. Search for specific news topics or recent events
3. Search the web for real-time facts, data, and information
4. Get current weather and 3-day forecast for any city
5. List available news categories

How to respond:
- For news requests (e.g., "latest tech news", "show me sports headlines"), use get_top_headlines with the appropriate category
- For specific topic searches (e.g., "news about Tesla", "what happened with the election"), use search_news
- For factual/web queries (e.g., "who is the CEO of Apple", "current gold price"), use search_web
- For questions about what's available, use get_news_categories
- Always present results in a clear, readable format
- Add a brief summary or insight after presenting news articles
- Remember context from earlier in the conversation for follow-up questions

Be concise, informative, and helpful. Always use a tool to fetch current information rather than relying on training data for news queries.
"""

# ── Tools ──────────────────────────────────────────────────────────────────────
TOOLS = [get_top_headlines, search_news, search_web, get_weather, get_news_categories]


def create_news_agent(checkpointer=None):
    """
    Create and return the NewsGenie ReAct agent.

    Uses create_react_agent from langgraph.prebuilt — the LLM autonomously
    decides which tools to invoke and in what order (true agentic behaviour).

    Args:
        checkpointer: LangGraph checkpointer for memory (default: MemorySaver)

    Returns:
        Compiled LangGraph agent with tool-calling capability
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    memory = checkpointer or MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )

    return agent
