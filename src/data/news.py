"""
News-Recherche: Brave Search + Bloomberg RSS + Finnhub.
Kombiniert mehrere Quellen für bessere Abdeckung.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _parse_bloomberg_feed(feed_url: str, max_per_feed: int) -> list[dict]:
    items = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:max_per_feed]:
            items.append({
                "title": entry.get("title", ""),
                "description": entry.get("summary", entry.get("description", ""))[:200],
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": "bloomberg",
            })
    except Exception as e:
        logger.debug(f"Bloomberg RSS Fehler: {e}")
    return items


def fetch_bloomberg_headlines(max_per_feed: int = 5) -> list[dict]:
    """Holt aktuelle Bloomberg-Headlines via RSS (parallel pro Feed)."""
    results = []
    with ThreadPoolExecutor(max_workers=len(BLOOMBERG_FEEDS)) as ex:
        futures = [ex.submit(_parse_bloomberg_feed, url, max_per_feed) for url in BLOOMBERG_FEEDS]
        for fut in as_completed(futures):
            results.extend(fut.result())
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


def _run_brave_queries(queries: list[str], api_key: str, count: int, freshness: str, max_workers: int = 3) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(queries))) as ex:
        futures = [ex.submit(search_brave, q, api_key, count, freshness) for q in queries]
        for fut in as_completed(futures):
            results.extend(fut.result())
    return results


def search_macro_news(api_key: str) -> list[dict]:
    """Sucht allgemeine Makro-/Marktnews (parallel)."""
    queries = [
        "stock market outlook this week analysis",
        "federal reserve ECB interest rate latest",
        "geopolitical risks markets 2026",
    ]
    return _run_brave_queries(queries, api_key, count=3, freshness="pw")


def search_new_opportunities(api_key: str) -> list[dict]:
    """Sucht nach neuen Investment-Opportunitäten (parallel)."""
    queries = [
        "undervalued stocks to buy analysts recommendation",
        "best growth stocks overlooked 2026",
        "value investing opportunities small cap",
    ]
    return _run_brave_queries(queries, api_key, count=3, freshness="pm")


def get_merged_headlines(news_data: dict, limit: int = 20) -> list[dict]:
    """Mergt Bloomberg + Macro-News, sortiert nach Aktualität."""
    all_news = []
    for item in news_data.get("bloomberg_headlines", []):
        item.setdefault("source", "bloomberg")
        all_news.append(item)
    for item in news_data.get("macro_news", []):
        item.setdefault("source", "brave")
        all_news.append(item)
    all_news.sort(key=lambda x: x.get("published", ""), reverse=True)
    return all_news[:limit]


# ── Collector ────────────────────────────────────────────────────

def _is_us_ticker(ticker: str) -> bool:
    return not any(c in ticker for c in [".", "AT0"])


def _collect_position_news(portfolio_tickers: list[dict], brave_api_key: str, finnhub_api_key: str) -> dict:
    """Holt Brave + Finnhub News pro Ticker — je eigener Pool um Rate-Limits zu respektieren."""
    brave_results: dict[str, list[dict]] = {}
    finnhub_results: dict[str, list[dict]] = {}

    # Brave: max 3 parallel (Free Tier ~1 req/s)
    if brave_api_key:
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {
                ex.submit(search_position_news, t["name"], t["ticker"], brave_api_key): t["ticker"]
                for t in portfolio_tickers
            }
            for fut in as_completed(futures):
                ticker = futures[fut]
                news = fut.result()
                if news:
                    brave_results[ticker] = news

    # Finnhub: mehr parallel erlaubt, nur für US-Ticker
    if finnhub_api_key:
        us_tickers = [t for t in portfolio_tickers if _is_us_ticker(t["ticker"])]
        if us_tickers:
            with ThreadPoolExecutor(max_workers=min(8, len(us_tickers))) as ex:
                futures = {
                    ex.submit(fetch_finnhub_news, t["ticker"], finnhub_api_key): t["ticker"]
                    for t in us_tickers
                }
                for fut in as_completed(futures):
                    ticker = futures[fut]
                    news = fut.result()
                    if news:
                        finnhub_results[ticker] = news

    # Merge
    merged: dict[str, list[dict]] = {}
    for ticker in set(list(brave_results.keys()) + list(finnhub_results.keys())):
        merged[ticker] = brave_results.get(ticker, []) + finnhub_results.get(ticker, [])
    return merged


def _collect_sentiment(portfolio_tickers: list[dict], finnhub_api_key: str) -> dict:
    if not finnhub_api_key:
        return {}
    candidates = [t["ticker"] for t in portfolio_tickers[:8] if _is_us_ticker(t["ticker"])]
    if not candidates:
        return {}
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(candidates))) as ex:
        futures = {ex.submit(fetch_finnhub_sentiment, tk, finnhub_api_key): tk for tk in candidates}
        for fut in as_completed(futures):
            tk = futures[fut]
            s = fut.result()
            if s:
                results[tk] = s
    return results


def collect_all_news(portfolio_tickers: list[dict], brave_api_key: str, finnhub_api_key: str = "") -> dict:
    """Sammelt News aus allen Quellen: Brave + Bloomberg RSS + Finnhub (parallel)."""
    logger.info("News-Collection (parallel)...")

    # Die 4 Top-Level-Blöcke sind unabhängig voneinander → parallel starten.
    with ThreadPoolExecutor(max_workers=4) as ex:
        bloomberg_fut = ex.submit(fetch_bloomberg_headlines, 5)
        position_fut = ex.submit(_collect_position_news, portfolio_tickers, brave_api_key, finnhub_api_key)
        sentiment_fut = ex.submit(_collect_sentiment, portfolio_tickers, finnhub_api_key)
        macro_fut = ex.submit(search_macro_news, brave_api_key) if brave_api_key else None
        opps_fut = ex.submit(search_new_opportunities, brave_api_key) if brave_api_key else None

        bloomberg = bloomberg_fut.result()
        position_news = position_fut.result()
        sentiment = sentiment_fut.result()
        macro_news = macro_fut.result() if macro_fut else []
        opportunities = opps_fut.result() if opps_fut else []

    return {
        "position_news": position_news,
        "bloomberg_headlines": bloomberg,
        "sentiment": sentiment,
        "macro_news": macro_news,
        "opportunities": opportunities,
        "collected_at": datetime.now().isoformat(),
    }
