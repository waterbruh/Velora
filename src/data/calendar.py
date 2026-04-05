"""
Earnings-Kalender und Event-Tracking.
Holt kommende Earnings-Termine für Portfolio-Positionen.
"""

import logging
from datetime import datetime

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_earnings_calendar(tickers: list[dict]) -> list[dict]:
    """Holt kommende Earnings-Termine für alle Ticker."""
    events = []
    for t in tickers:
        ticker = t.get("ticker")
        if not ticker:
            continue
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            if cal is not None and not cal.empty if hasattr(cal, 'empty') else cal:
                if isinstance(cal, dict):
                    earnings_date = cal.get("Earnings Date")
                    if earnings_date:
                        events.append({
                            "ticker": ticker,
                            "name": t["name"],
                            "event": "Earnings",
                            "date": str(earnings_date[0]) if isinstance(earnings_date, list) else str(earnings_date),
                        })
                elif hasattr(cal, 'to_dict'):
                    cal_dict = cal.to_dict()
                    for key in cal_dict:
                        if "earning" in str(key).lower() or "dividend" in str(key).lower():
                            val = cal_dict[key]
                            if isinstance(val, dict):
                                val = list(val.values())[0] if val else None
                            if val:
                                events.append({
                                    "ticker": ticker,
                                    "name": t["name"],
                                    "event": str(key),
                                    "date": str(val),
                                })
        except Exception as e:
            logger.debug(f"Earnings-Kalender für {ticker}: {e}")

    # Sortiere nach Datum
    events.sort(key=lambda x: x.get("date", "9999"))
    return events


def format_earnings_calendar(events: list[dict]) -> str:
    """Formatiert den Earnings-Kalender für den Prompt."""
    if not events:
        return "Keine kommenden Earnings-Termine gefunden."

    lines = ["Kommende Events für deine Positionen:"]
    for e in events:
        lines.append(f"  {e['date']} | {e['name']} ({e['ticker']}): {e['event']}")
    return "\n".join(lines)
