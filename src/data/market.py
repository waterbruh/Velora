"""
Marktdaten: Kurse, Fundamentals, Insider-Transaktionen.
Primär yfinance, Fallback Twelve Data.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_portfolio() -> dict:
    with open(CONFIG_DIR / "portfolio.json") as f:
        return json.load(f)


def load_watchlist() -> dict:
    with open(CONFIG_DIR / "watchlist.json") as f:
        return json.load(f)


def get_all_tickers(portfolio: dict) -> list[dict]:
    """Extrahiert alle einzigartigen Ticker aus dem Portfolio."""
    tickers = []
    seen = set()
    for account_name, account in portfolio["accounts"].items():
        for pos in account["positions"]:
            ticker = pos.get("ticker")
            if ticker and ticker not in seen:
                seen.add(ticker)
                tickers.append({
                    "ticker": ticker,
                    "name": pos["name"],
                    "isin": pos["isin"],
                    "currency": pos["currency"],
                })
    return tickers


def validate_price(price, ticker: str, field: str) -> float | None:
    """Validiert dass ein Preis plausibel ist."""
    if price is None:
        return None
    try:
        price = float(price)
    except (TypeError, ValueError):
        logger.warning(f"Ungültiger Preis für {ticker}.{field}: {price}")
        return None
    if price <= 0 or price > 1_000_000:
        logger.warning(f"Unplausibler Preis für {ticker}.{field}: {price}")
        return None
    return price


def validate_ratio(value, ticker: str, field: str, min_val: float = -1000, max_val: float = 10000) -> float | None:
    """Validiert dass eine Kennzahl plausibel ist."""
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value < min_val or value > max_val:
        logger.warning(f"Unplausible Kennzahl für {ticker}.{field}: {value}")
        return None
    return round(value, 4)


def fetch_price_data(ticker: str, retries: int = 2) -> dict | None:
    """Holt aktuelle Kursdaten + Key Stats für einen Ticker. Mit Retry-Logik."""
    for attempt in range(retries + 1):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist_1m = stock.history(period="1mo")
            hist_6m = stock.history(period="6mo")
            hist_1y = stock.history(period="1y")

            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
            if not current_price and not hist_1m.empty:
                current_price = float(hist_1m["Close"].iloc[-1])

            current_price = validate_price(current_price, ticker, "current_price")
            if not current_price:
                if attempt < retries:
                    logger.info(f"Retry {attempt+1} für {ticker}...")
                    continue
                logger.error(f"Kein valider Kurs für {ticker} nach {retries+1} Versuchen")
                return None

            prev_close = validate_price(info.get("previousClose"), ticker, "prev_close")
            week_52_high = validate_price(info.get("fiftyTwoWeekHigh"), ticker, "52w_high")
            week_52_low = validate_price(info.get("fiftyTwoWeekLow"), ticker, "52w_low")

            # Performance nur berechnen wenn genug Datenpunkte (mind. 5 Tage für 1M)
            perf_1m = None
            if not hist_1m.empty and len(hist_1m) >= 5:
                perf_1m = (float(hist_1m["Close"].iloc[-1]) / float(hist_1m["Close"].iloc[0]) - 1) * 100

            perf_6m = None
            if not hist_6m.empty and len(hist_6m) >= 20:
                perf_6m = (float(hist_6m["Close"].iloc[-1]) / float(hist_6m["Close"].iloc[0]) - 1) * 100

            perf_1y = None
            if not hist_1y.empty and len(hist_1y) >= 50:
                perf_1y = (float(hist_1y["Close"].iloc[-1]) / float(hist_1y["Close"].iloc[0]) - 1) * 100

            # Cross-Validation: 52W-Range nur prüfen wenn beide Werte plausibel auseinanderliegen
            if week_52_high and week_52_low and current_price:
                range_spread = (week_52_high - week_52_low) / week_52_low if week_52_low > 0 else 0
                if range_spread > 0.02:  # Nur validieren wenn Range > 2% breit ist
                    if current_price > week_52_high * 1.10 or current_price < week_52_low * 0.90:
                        logger.warning(f"{ticker}: Kurs {current_price} außerhalb 52W-Range [{week_52_low}-{week_52_high}] — 52W-Daten möglicherweise veraltet")
                        # Unzuverlässige 52W-Daten nullen
                        week_52_high = None
                        week_52_low = None

            return {
                "ticker": ticker,
                "current_price": current_price,
                "previous_close": prev_close,
                "change_pct": round((current_price / prev_close - 1) * 100, 2) if current_price and prev_close else None,
                "52w_high": week_52_high,
                "52w_low": week_52_low,
                "perf_1m_pct": round(perf_1m, 2) if perf_1m is not None else None,
                "perf_6m_pct": round(perf_6m, 2) if perf_6m is not None else None,
                "perf_1y_pct": round(perf_1y, 2) if perf_1y is not None else None,
                "market_cap": info.get("marketCap"),
                "pe_ratio": validate_ratio(info.get("trailingPE"), ticker, "pe", -100, 5000),
                "forward_pe": validate_ratio(info.get("forwardPE"), ticker, "fwd_pe", -1000, 5000),
                "peg_ratio": validate_ratio(info.get("pegRatio"), ticker, "peg", -50, 100),
                "price_to_book": validate_ratio(info.get("priceToBook"), ticker, "pb", 0, 500),
                "dividend_yield": validate_ratio(info.get("dividendYield"), ticker, "div", 0, 50),
                "beta": validate_ratio(info.get("beta"), ticker, "beta", -5, 10),
                "short_interest": validate_ratio(info.get("shortPercentOfFloat"), ticker, "short", 0, 1),
                "insider_buy_pct": validate_ratio(info.get("heldPercentInsiders"), ticker, "insider", 0, 1),
                "institutional_pct": validate_ratio(info.get("heldPercentInstitutions"), ticker, "inst", 0, 1),
                "free_cash_flow": info.get("freeCashflow"),
                "revenue_growth": validate_ratio(info.get("revenueGrowth"), ticker, "rev_growth", -1, 100),
                "profit_margin": validate_ratio(info.get("profitMargins"), ticker, "margin", -10, 1),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "source": "yfinance",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            if attempt < retries:
                logger.info(f"Retry {attempt+1} für {ticker} nach Fehler: {e}")
                continue
            logger.error(f"Fehler beim Abrufen von {ticker}: {e}")
            return None


def fetch_index_data() -> dict:
    """Holt Daten für wichtige Indizes."""
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DAX": "^GDAXI",
        "ATX": "^ATX",
        "Euro Stoxx 50": "^STOXX50E",
        "VIX": "^VIX",
        "Gold": "GC=F",
        "EUR/USD": "EURUSD=X",
        "BTC/USD": "BTC-USD",
    }
    results = {}
    for name, ticker in indices.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if not hist.empty:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[0])
                results[name] = {
                    "value": round(current, 2),
                    "change_pct": round((current / prev - 1) * 100, 2),
                    "source": "yfinance",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Index {name} ({ticker}) Fehler: {e}")
    return results


def fetch_insider_activity(ticker: str) -> list[dict]:
    """Holt Insider-Transaktionen der letzten 3 Monate."""
    try:
        stock = yf.Ticker(ticker)
        insiders = stock.insider_transactions
        if insiders is None or insiders.empty:
            return []
        recent = []
        cutoff = datetime.now() - timedelta(days=90)
        for _, row in insiders.head(10).iterrows():
            recent.append({
                "insider": str(row.get("Insider", "")),
                "relation": str(row.get("Relation", "")),
                "transaction": str(row.get("Transaction", "")),
                "shares": row.get("Shares", 0),
                "value": row.get("Value", 0),
                "date": str(row.get("Date", "")),
            })
        return recent
    except Exception as e:
        logger.error(f"Insider-Daten für {ticker} Fehler: {e}")
        return []


def collect_all_market_data(portfolio: dict) -> dict:
    """Sammelt alle Marktdaten für das gesamte Portfolio."""
    tickers = get_all_tickers(portfolio)
    watchlist = load_watchlist()

    positions_data = {}
    for t in tickers:
        logger.info(f"Fetching {t['name']} ({t['ticker']})...")
        price_data = fetch_price_data(t["ticker"])
        insider_data = fetch_insider_activity(t["ticker"])
        if price_data:
            positions_data[t["ticker"]] = {
                **t,
                "price": price_data,
                "insiders": insider_data,
            }

    watchlist_data = {}
    for item in watchlist.get("watchlist", []):
        ticker = item.get("ticker")
        if ticker:
            logger.info(f"Fetching watchlist: {ticker}...")
            price_data = fetch_price_data(ticker)
            if price_data:
                watchlist_data[ticker] = {
                    "ticker": ticker,
                    "name": item.get("name", ticker),
                    "price": price_data,
                }

    indices = fetch_index_data()

    return {
        "positions": positions_data,
        "watchlist": watchlist_data,
        "indices": indices,
        "collected_at": datetime.now().isoformat(),
    }
