"""
News-Recherche via Brave Search API.
Sucht gezielt nach relevanten Finanznews für Portfolio-Positionen.
"""

import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


def search_brave(query: str, api_key: str, count: int = 5, freshness: str = "pw") -> list[dict]:
    """Brave Search API Abfrage."""
    try:
        headers = {"X-Subscription-Token": api_key}
        params = {
            "q": query,
            "count": count,
            "freshness": freshness,
            "text_decorations": False,
            "search_lang": "en",
        }
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        data = resp.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "age": item.get("age", ""),
                "published": item.get("page_age", item.get("age", "?")),
            })
        return results
    except Exception as e:
        logger.error(f"Brave Search Fehler für '{query}': {e}")
        return []


def search_position_news(name: str, ticker: str, api_key: str) -> list[dict]:
    """Sucht News für eine bestimmte Position."""
    query = f"{name} stock news analysis outlook"
    return search_brave(query, api_key, count=3, freshness="pw")


def search_macro_news(api_key: str) -> list[dict]:
    """Sucht allgemeine Makro-/Marktnews."""
    queries = [
        "stock market outlook this week analysis",
        "federal reserve ECB interest rate latest",
        "geopolitical risks markets 2026",
    ]
    results = []
    for q in queries:
        results.extend(search_brave(q, api_key, count=3, freshness="pw"))
    return results


def search_new_opportunities(api_key: str, sectors: list[str] = None) -> list[dict]:
    """Sucht nach neuen Investment-Opportunitäten."""
    queries = [
        "undervalued stocks to buy analysts recommendation",
        "best growth stocks overlooked 2026",
        "value investing opportunities small cap",
    ]
    if sectors:
        for sector in sectors[:2]:
            queries.append(f"{sector} stocks best picks analyst")

    results = []
    for q in queries:
        results.extend(search_brave(q, api_key, count=3, freshness="pm"))
    return results


def collect_all_news(portfolio_tickers: list[dict], api_key: str) -> dict:
    """Sammelt alle News für Portfolio + Makro + neue Ideen."""
    if not api_key:
        logger.warning("Kein Brave Search API Key konfiguriert.")
        return {"position_news": {}, "macro_news": [], "opportunities": []}

    position_news = {}
    for t in portfolio_tickers:
        ticker = t["ticker"]
        name = t["name"]
        logger.info(f"News-Suche: {name}...")
        news = search_position_news(name, ticker, api_key)
        if news:
            position_news[ticker] = news

    macro_news = search_macro_news(api_key)
    opportunities = search_new_opportunities(api_key)

    return {
        "position_news": position_news,
        "macro_news": macro_news,
        "opportunities": opportunities,
        "collected_at": datetime.now().isoformat(),
    }
