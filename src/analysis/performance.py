"""
Performance-Tracking: Benchmark-Vergleich, Recommendation-Tracking, Tax-Loss-Harvesting.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = Path(__file__).parent.parent.parent / "memory"


def calculate_benchmark_comparison(market_data: dict) -> str:
    """Vergleicht Portfolio-Performance mit Benchmarks."""
    indices = market_data.get("indices", {})
    benchmarks = {}

    for name in ["S&P 500", "NASDAQ", "DAX", "ATX", "Euro Stoxx 50", "Gold", "BTC/USD"]:
        if name in indices:
            change = indices[name].get("change_pct", 0)
            benchmarks[name] = change

    if not benchmarks:
        return "Keine Benchmark-Daten verfügbar."

    lines = ["BENCHMARK-VERGLEICH (Wochenperformance):"]
    for name, change in sorted(benchmarks.items(), key=lambda x: x[1], reverse=True):
        bar = "+" * int(abs(change)) if change > 0 else "-" * int(abs(change))
        lines.append(f"  {name:20s}: {change:+.2f}% {bar}")

    return "\n".join(lines)


def find_tax_loss_harvesting(portfolio: dict, market_data: dict, tax_rate: float = None) -> str:
    """Identifiziert Tax-Loss-Harvesting Opportunitäten."""
    if tax_rate is None:
        # Versuche aus Settings zu laden
        try:
            settings_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
            import json
            with open(settings_path) as f:
                settings = json.load(f)
            tax_rate = settings.get("user", {}).get("tax_rate", 0.275)
        except Exception:
            tax_rate = 0.275
    gains = []
    losses = []

    indices = market_data.get("indices", {})
    eur_usd = indices.get("EUR/USD", {}).get("value", 1.0)

    for account_name, account in portfolio["accounts"].items():
        for pos in account["positions"]:
            ticker = pos.get("ticker")
            if not ticker or ticker not in market_data.get("positions", {}):
                continue

            shares = pos["shares"]
            buy_in = pos["buy_in"]
            currency = pos.get("currency", "EUR")
            current_price = market_data["positions"][ticker].get("price", {}).get("current_price")

            if not current_price:
                continue

            # Alles in EUR
            if currency == "USD":
                buy_in_eur = buy_in / eur_usd
                current_eur = current_price / eur_usd
            else:
                buy_in_eur = buy_in
                current_eur = current_price

            pnl_eur = (current_eur - buy_in_eur) * shares
            pnl_pct = ((current_eur / buy_in_eur) - 1) * 100 if buy_in_eur else 0

            entry = {
                "name": pos["name"],
                "ticker": ticker,
                "pnl_eur": round(pnl_eur, 2),
                "pnl_pct": round(pnl_pct, 1),
                "account": account_name,
            }

            if pnl_eur > 0:
                gains.append(entry)
            elif pnl_eur < 0:
                losses.append(entry)

    total_gains = sum(g["pnl_eur"] for g in gains)
    total_losses = sum(l["pnl_eur"] for l in losses)
    potential_tax = total_gains * tax_rate
    net_after_harvesting = (total_gains + total_losses) * tax_rate

    lines = [
        "TAX-LOSS-HARVESTING ANALYSE (KESt 27.5%):",
        f"  Unrealisierte Gewinne: {total_gains:+.2f}€",
        f"  Unrealisierte Verluste: {total_losses:+.2f}€",
        f"  Potenzielle KESt auf Gewinne: {potential_tax:.2f}€",
        f"  KESt nach Verlustverrechnung: {max(0, net_after_harvesting):.2f}€",
        f"  Mögliche Steuerersparnis: {potential_tax - max(0, net_after_harvesting):.2f}€",
        "",
        "  Verlust-Positionen (Kandidaten für Harvesting):",
    ]
    for l in sorted(losses, key=lambda x: x["pnl_eur"]):
        lines.append(f"    {l['name']} ({l['ticker']}): {l['pnl_eur']:+.2f}€ ({l['pnl_pct']:+.1f}%) [{l['account']}]")

    lines.append("")
    lines.append("  Gewinn-Positionen:")
    for g in sorted(gains, key=lambda x: x["pnl_eur"], reverse=True):
        lines.append(f"    {g['name']} ({g['ticker']}): {g['pnl_eur']:+.2f}€ ({g['pnl_pct']:+.1f}%) [{g['account']}]")

    return "\n".join(lines)


def track_recommendation_performance(market_data: dict) -> str:
    """Trackt wie vergangene Empfehlungen performt haben."""
    recs_path = MEMORY_DIR / "recommendations.json"
    if not recs_path.exists():
        return "Noch keine Empfehlungen zum Tracken."

    with open(recs_path) as f:
        recs = json.load(f)

    if not recs:
        return "Noch keine Empfehlungen zum Tracken."

    lines = ["EMPFEHLUNGS-BILANZ:"]
    wins = 0
    losses = 0
    open_count = 0

    for rec in recs:
        ticker = rec.get("ticker", "?")
        action = rec.get("action", "?")
        status = rec.get("status", "open")
        date = rec.get("date", "?")[:10]

        if status == "open":
            open_count += 1
            unrealized = rec.get("unrealized_pct")
            if unrealized is not None:
                emoji = "📈" if unrealized > 0 else "📉"
                lines.append(f"  {emoji} OFFEN {date}: {action} {ticker} → {unrealized:+.1f}%")
        elif status == "target_hit":
            wins += 1
            lines.append(f"  ✅ {date}: {action} {ticker} → Ziel erreicht")
        elif status == "stop_hit":
            losses += 1
            lines.append(f"  ❌ {date}: {action} {ticker} → Stop ausgelöst")

    total = wins + losses
    hit_rate = (wins / total * 100) if total > 0 else 0
    lines.insert(1, f"  Abgeschlossen: {total} (Hit-Rate: {hit_rate:.0f}%) | Offen: {open_count}")

    return "\n".join(lines)
