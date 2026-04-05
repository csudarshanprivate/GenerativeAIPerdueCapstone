"""
tools.py — NewsGenie Agent Tools
Defines @tool-decorated functions that the ReAct agent autonomously selects and calls.
"""

import os
import time
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


def _get_ddgs():
    """Return a DDGS instance, preferring the new 'ddgs' package over the renamed 'duckduckgo_search'."""
    try:
        from ddgs import DDGS
        return DDGS
    except ImportError:
        from duckduckgo_search import DDGS
        return DDGS


def _fetch_via_duckduckgo(query: str) -> list[dict]:
    """Fetch news results via DuckDuckGo with retry on rate-limit."""
    DDGS = _get_ddgs()
    for attempt in range(3):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=5):
                    results.append({
                        "title": r.get("title", "No title"),
                        "source": r.get("source", "DuckDuckGo"),
                        "description": r.get("body", ""),
                        "url": r.get("url", ""),
                    })
            if results:
                return results
        except Exception as e:
            if "ratelimit" in str(e).lower() and attempt < 2:
                time.sleep(2 + attempt * 2)
                continue
            break
    return []


def _fetch_ddg_text(query: str) -> list[dict]:
    """Fetch web text results via DuckDuckGo with retry on rate-limit."""
    DDGS = _get_ddgs()
    for attempt in range(3):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "href": r.get("href", ""),
                    })
            if results:
                return results
        except Exception as e:
            if "ratelimit" in str(e).lower() and attempt < 2:
                time.sleep(2 + attempt * 2)
                continue
            break
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


@tool
def get_weather(location: str) -> str:
    """
    Get the current weather and today's forecast for any city or location.

    Use this tool when the user asks about weather, temperature, rain, or forecast.

    Examples:
    - "What's the weather in New York?" → location="New York"
    - "Is it raining in London?"        → location="London"
    - "Weather in Tokyo today"          → location="Tokyo"
    """
    try:
        # Step 1: Geocode — Open-Meteo only accepts city names, not full address strings.
        # Parse "Aurora, Illinois, United States" → city="Aurora", state hint="illinois"
        parts = [p.strip() for p in location.split(",")]
        city_name = parts[0]                              # always use first part as city
        hint = " ".join(parts[1:]).lower() if len(parts) > 1 else ""  # state/country hint

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city_name, "count": 10}, timeout=10)
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"Could not find location '{location}'. Please try just the city name (e.g. 'Aurora')."

        # Pick the best match: prefer result whose state (admin1) matches the hint.
        # Check state first (more specific), then country — avoids false matches on "united states".
        result = geo_data["results"][0]  # default to first
        if hint:
            hint_words = [w for w in hint.split() if len(w) > 3]
            # Pass 1: look for a state-level match
            for r in geo_data["results"]:
                state_r = r.get("admin1", "").lower()
                if any(word in state_r for word in hint_words):
                    result = r
                    break
            else:
                # Pass 2: fall back to country-level match
                for r in geo_data["results"]:
                    country_r = r.get("country", "").lower()
                    if any(word in country_r for word in hint_words):
                        result = r
                        break
        lat = result["latitude"]
        lon = result["longitude"]
        city = result.get("name", city_name)
        state = result.get("admin1", "")
        country = result.get("country", "")
        display_location = f"{city}, {state}, {country}" if state else f"{city}, {country}"

        # Step 2: Fetch current weather + daily forecast from Open-Meteo (no key needed)
        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m",
                        "weather_code", "apparent_temperature"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                      "weather_code"],
            "timezone": "auto",
            "forecast_days": 3,
        }
        w_resp = requests.get(weather_url, params=params, timeout=10)
        w = w_resp.json()

        current = w.get("current", {})
        daily = w.get("daily", {})

        # WMO weather code → description mapping
        WMO = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle",
            61: "Light rain", 63: "Rain", 65: "Heavy rain",
            71: "Light snow", 73: "Snow", 75: "Heavy snow",
            80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with hail",
        }
        code = current.get("weather_code", 0)
        condition = WMO.get(code, f"Code {code}")

        temp = current.get("temperature_2m", "N/A")
        feels = current.get("apparent_temperature", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        units = w.get("current_units", {})
        t_unit = units.get("temperature_2m", "°C")

        lines = [
            f"## Weather in {display_location}\n",
            f"**Condition:** {condition}",
            f"**Temperature:** {temp}{t_unit} (feels like {feels}{t_unit})",
            f"**Humidity:** {humidity}%",
            f"**Wind Speed:** {wind} km/h",
            "",
            "**3-Day Forecast:**",
        ]

        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        d_codes = daily.get("weather_code", [])

        for i in range(min(3, len(dates))):
            day_cond = WMO.get(d_codes[i] if i < len(d_codes) else 0, "")
            rain = precip[i] if i < len(precip) else 0
            lines.append(
                f"- **{dates[i]}**: {day_cond}, "
                f"High {max_temps[i] if i < len(max_temps) else 'N/A'}{t_unit} / "
                f"Low {min_temps[i] if i < len(min_temps) else 'N/A'}{t_unit}, "
                f"Rain {rain}mm"
            )

        lines.append("\n*Data from Open-Meteo (open-meteo.com)*")
        return "\n".join(lines)

    except Exception as e:
        return f"Could not fetch weather for '{location}': {str(e)}"
