"""
tools.py — NewsGenie Agent Tools
Defines @tool-decorated functions that the ReAct agent autonomously selects and calls.
"""

import os
import json
import requests
from langchain_core.tools import tool

# ── Optional: NewsAPI ──────────────────────────────────────────────────────────
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

CATEGORY_ALIASES = {
    "tech": "technology", "ai": "technology", "artificial intelligence": "technology",
    "business": "finance", "economy": "finance", "market": "finance", "stock": "finance",
    "sport": "sports", "soccer": "sports", "football": "sports", "cricket": "sports",
    "medicine": "health", "medical": "health", "wellness": "health",
    "space": "science", "physics": "science", "research": "science",
}

VALID_CATEGORIES = ["technology", "finance", "sports", "health", "science", "general", "entertainment"]


def _normalize_category(category: str) -> str:
    c = category.lower().strip()
    return CATEGORY_ALIASES.get(c, c if c in VALID_CATEGORIES else "general")


def _fetch_via_newsapi(category: str, query: str = "") -> list[dict]:
    """Fetch articles via NewsAPI.org."""
    cat = _normalize_category(category)
    # Map our categories to NewsAPI categories
    newsapi_cats = {"technology", "sports", "health", "science", "entertainment", "general", "business"}
    newsapi_cat = "business" if cat == "finance" else cat if cat in newsapi_cats else "general"

    params = {
        "apiKey": NEWSAPI_KEY,
        "language": "en",
        "pageSize": 5,
    }
    if query:
        params["q"] = query
        url = "https://newsapi.org/v2/everything"
        params["sortBy"] = "publishedAt"
    else:
        params["category"] = newsapi_cat
        url = "https://newsapi.org/v2/top-headlines"

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    articles = []
    for art in data.get("articles", [])[:5]:
        articles.append({
            "title": art.get("title", "No title"),
            "source": art.get("source", {}).get("name", "NewsAPI"),
            "description": art.get("description", ""),
            "url": art.get("url", ""),
        })
    return articles


def _fetch_via_duckduckgo(query: str) -> list[dict]:
    """Fetch results via DuckDuckGo (no API key needed)."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=5):
                results.append({
                    "title": r.get("title", "No title"),
                    "source": r.get("source", "DuckDuckGo"),
                    "description": r.get("body", ""),
                    "url": r.get("url", ""),
                })
        return results
    except Exception:
        return []


def _fetch_ddg_text(query: str) -> list[dict]:
    """Fetch web text results via DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", ""),
                })
        return results
    except Exception:
        return []


def _format_articles(articles: list[dict]) -> str:
    if not articles:
        return "No articles found."
    lines = []
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. **{art['title']}**")
        lines.append(f"   Source: {art.get('source', 'Unknown')}")
        if art.get("description"):
            lines.append(f"   {art['description'][:150]}...")
        if art.get("url"):
            lines.append(f"   URL: {art['url']}")
        lines.append("")
    return "\n".join(lines)


# ── Tools ──────────────────────────────────────────────────────────────────────

@tool
def get_top_headlines(category: str = "general") -> str:
    """
    Fetch the latest top news headlines for a specific category.

    Use this tool when the user asks for news, headlines, or top stories in a category.
    Supported categories: technology, finance, sports, health, science, general, entertainment.

    Examples:
    - "latest technology news" → category="technology"
    - "top sports headlines" → category="sports"
    - "business news today" → category="finance"
    """
    cat = _normalize_category(category)
    articles = []

    if NEWSAPI_KEY and len(NEWSAPI_KEY) > 20:
        try:
            articles = _fetch_via_newsapi(cat)
        except Exception:
            articles = []

    if not articles:
        query_map = {
            "technology": "technology news today",
            "finance": "finance business news today",
            "sports": "sports news today",
            "health": "health medicine news today",
            "science": "science space news today",
            "entertainment": "entertainment news today",
            "general": "top news headlines today",
        }
        articles = _fetch_via_duckduckgo(query_map.get(cat, f"{cat} news today"))

    if not articles:
        return f"Could not fetch {cat} news at this time. Please try again."

    return f"## Top {cat.capitalize()} Headlines\n\n" + _format_articles(articles)


@tool
def search_news(query: str) -> str:
    """
    Search for specific news topics, recent events, or news about a person/company/event.

    Use this tool when the user asks about a specific topic in the news, or wants to
    find recent news about something specific (not just category-based headlines).

    Examples:
    - "latest news about Tesla" → query="Tesla latest news"
    - "what happened with OpenAI recently" → query="OpenAI recent news"
    - "news about climate summit" → query="climate summit news"
    """
    articles = []

    if NEWSAPI_KEY and len(NEWSAPI_KEY) > 20:
        try:
            articles = _fetch_via_newsapi("general", query=query)
        except Exception:
            articles = []

    if not articles:
        articles = _fetch_via_duckduckgo(query)

    if not articles:
        return f"No news found for '{query}'. Try a different search term."

    return f"## News Results: {query}\n\n" + _format_articles(articles)


@tool
def search_web(query: str) -> str:
    """
    Search the web for real-time facts, current data, prices, or information not in news.

    Use this tool when the user asks for factual information that requires a live web search,
    such as current prices, live scores, company information, or general knowledge questions
    that need up-to-date answers.

    Examples:
    - "who is the CEO of Microsoft" → factual web search
    - "current Bitcoin price" → live data search
    - "what is quantum computing" → knowledge question needing current info
    """
    results = _fetch_ddg_text(query)

    if not results:
        return f"No web results found for '{query}'."

    lines = [f"## Web Search Results: {query}\n"]
    for i, r in enumerate(results[:4], 1):
        lines.append(f"{i}. **{r['title']}**")
        lines.append(f"   {r['body'][:200]}...")
        if r.get("href"):
            lines.append(f"   Source: {r['href']}")
        lines.append("")

    return "\n".join(lines)


@tool
def get_news_categories() -> str:
    """
    Return the list of available news categories that NewsGenie can fetch.

    Use this when the user asks what topics or categories are available,
    or when you need to clarify what categories exist before fetching news.
    """
    categories = {
        "technology": "AI, software, gadgets, cybersecurity, tech companies",
        "finance": "stocks, markets, economy, business, cryptocurrency",
        "sports": "football, cricket, tennis, Olympics, sports events",
        "health": "medicine, wellness, diseases, healthcare, research",
        "science": "space, physics, climate, discoveries, research",
        "entertainment": "movies, music, celebrities, TV shows, culture",
        "general": "top stories, breaking news, world events",
    }
    lines = ["## Available News Categories\n"]
    for cat, desc in categories.items():
        lines.append(f"- **{cat.capitalize()}**: {desc}")
    lines.append("\nYou can ask for news in any of these categories!")
    return "\n".join(lines)
