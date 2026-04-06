"""
News-Recherche: Brave Search + Bloomberg RSS + Finnhub.
Kombiniert mehrere Quellen für bessere Abdeckung.
"""

import logging
from datetime import datetime

import feedparser
import requests

logger = logging.getLogger(__name__)


# ── Brave Search ─────────────────────────────────────────────────

def search_brave(query: str, api_key: str, count: int = 5, freshness: str = "pw") -> list[dict]:
    """Brave Search API Abfrage."""
    if not api_key:
        return []
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
            headers=headers, params=params, timeout=10,
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
                "source": "brave",
            })
        return results
    except Exception as e:
        logger.error(f"Brave Search Fehler für '{query}': {e}")
        return []


# ── Bloomberg RSS ────────────────────────────────────────────────

BLOOMBERG_FEEDS = [
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/technology/news.rss",
]


def fetch_bloomberg_headlines(max_per_feed: int = 5) -> list[dict]:
    """Holt aktuelle Bloomberg-Headlines via RSS (kostenlos, kein API Key)."""
    results = []
    for feed_url in BLOOMBERG_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:max_per_feed]:
                published = entry.get("published", "")
                results.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", entry.get("description", ""))[:200],
                    "url": entry.get("link", ""),
                    "published": published,
                    "source": "bloomberg",
                })
        except Exception as e:
            logger.debug(f"Bloomberg RSS Fehler: {e}")
    return results


# ── Finnhub ──────────────────────────────────────────────────────

def fetch_finnhub_news(ticker: str, api_key: str) -> list[dict]:
    """Holt Company-News von Finnhub (inkl. Sentiment)."""
    if not api_key:
        return []
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - __import__("datetime").timedelta(days=7)).strftime("%Y-%m-%d")
        resp = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={"symbol": ticker, "from": week_ago, "to": today, "token": api_key},
            timeout=10,
        )
        data = resp.json()
        results = []
        for item in data[:5]:
            results.append({
                "title": item.get("headline", ""),
                "description": item.get("summary", "")[:200],
                "url": item.get("url", ""),
                "published": datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d %H:%M"),
                "source": f"finnhub ({item.get('source', '?')})",
            })
        return results
    except Exception as e:
        logger.debug(f"Finnhub News für {ticker}: {e}")
        return []


def fetch_finnhub_sentiment(ticker: str, api_key: str) -> dict | None:
    """Holt Sentiment-Score von Finnhub."""
    if not api_key:
        return None
    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/news-sentiment",
            params={"symbol": ticker, "token": api_key},
            timeout=10,
        )
        data = resp.json()
        sentiment = data.get("sentiment") or {}
        buzz = data.get("buzz") or {}
        bullish = sentiment.get("bullishPercent")
        if bullish is None:
            return None
        return {
            "bullish": bullish,
            "bearish": sentiment.get("bearishPercent", 0),
            "buzz_volume": buzz.get("articlesInLastWeek"),
            "buzz_change": buzz.get("weeklyAverage"),
            "source": "finnhub",
        }
    except Exception as e:
        logger.debug(f"Finnhub Sentiment für {ticker}: {e}")
        return None


# ── Brave Position News ──────────────────────────────────────────

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


def search_new_opportunities(api_key: str) -> list[dict]:
    """Sucht nach neuen Investment-Opportunitäten."""
    queries = [
        "undervalued stocks to buy analysts recommendation",
        "best growth stocks overlooked 2026",
        "value investing opportunities small cap",
    ]
    results = []
    for q in queries:
        results.extend(search_brave(q, api_key, count=3, freshness="pm"))
    return results


# ── Collector ────────────────────────────────────────────────────

def collect_all_news(portfolio_tickers: list[dict], brave_api_key: str, finnhub_api_key: str = "") -> dict:
    """Sammelt News aus allen Quellen: Brave + Bloomberg RSS + Finnhub."""

    # 1. Bloomberg Headlines (immer, kein API Key nötig)
    logger.info("Bloomberg RSS...")
    bloomberg = fetch_bloomberg_headlines(max_per_feed=5)

    # 2. Position-News: Brave Search + Finnhub
    position_news = {}
    for t in portfolio_tickers:
        ticker = t["ticker"]
        name = t["name"]
        logger.info(f"News: {name}...")

        news = []
        # Brave Search
        if brave_api_key:
            news.extend(search_position_news(name, ticker, brave_api_key))
        # Finnhub (nur für US-Ticker, braucht reinen Ticker ohne Suffix)
        if finnhub_api_key and not any(c in ticker for c in [".", "AT0"]):
            finnhub_news = fetch_finnhub_news(ticker, finnhub_api_key)
            news.extend(finnhub_news)

        if news:
            position_news[ticker] = news

    # 3. Sentiment (Finnhub, nur für Top-Positionen)
    sentiment = {}
    if finnhub_api_key:
        for t in portfolio_tickers[:8]:
            ticker = t["ticker"]
            if not any(c in ticker for c in [".", "AT0"]):
                s = fetch_finnhub_sentiment(ticker, finnhub_api_key)
                if s:
                    sentiment[ticker] = s

    # 4. Makro-News + Opportunities (Brave)
    macro_news = search_macro_news(brave_api_key) if brave_api_key else []
    opportunities = search_new_opportunities(brave_api_key) if brave_api_key else []

    return {
        "position_news": position_news,
        "bloomberg_headlines": bloomberg,
        "sentiment": sentiment,
        "macro_news": macro_news,
        "opportunities": opportunities,
        "collected_at": datetime.now().isoformat(),
    }
