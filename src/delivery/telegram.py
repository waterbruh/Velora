"""
Telegram Bot: Sendet Briefings + empfängt Trade-Updates und Ticker-Anfragen.
"""

import json
import logging
import re
from pathlib import Path

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
MAX_MESSAGE_LENGTH = 4096

# Pending trades die auf Bestätigung warten
_pending_trades = {}


async def send_briefing(bot_token: str, chat_id: str, text: str):
    """Sendet ein Briefing als Telegram-Nachricht(en)."""
    bot = Bot(token=bot_token)
    chunks = split_message(text, MAX_MESSAGE_LENGTH)
    for chunk in chunks:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            # Fallback ohne HTML-Formatierung
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
            )


async def send_document(bot_token: str, chat_id: str, file_path: str, caption: str = None):
    """Sendet eine Datei (z.B. PDF) als Telegram-Dokument."""
    bot = Bot(token=bot_token)
    with open(file_path, "rb") as f:
        await bot.send_document(
            chat_id=chat_id,
            document=f,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )


async def send_error_alert(bot_token: str, chat_id: str, error_msg: str):
    """Sendet eine Fehler-Benachrichtigung."""
    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=chat_id,
        text=f"⚠️ <b>System-Fehler</b>\n\n<code>{error_msg[:500]}</code>",
        parse_mode=ParseMode.HTML,
    )


def split_message(text: str, max_length: int) -> list[str]:
    """Teilt lange Nachrichten in Telegram-kompatible Chunks."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


def parse_trade_message(text: str) -> dict | None:
    """Flexibles Parsing von Trade-Nachrichten. Versteht verschiedene Formate."""
    text_lower = text.lower().strip()

    # Bestimme ob Kauf oder Verkauf
    is_sell = any(w in text_lower for w in ["verkauft", "sold", "verkauf", "sell", "raus aus", "weg mit"])
    is_buy = any(w in text_lower for w in ["gekauft", "bought", "kauft", "kauf", "buy", "nachgekauft", "dazu"])

    if not is_sell and not is_buy:
        return None

    # Finde Zahlen und Ticker
    # Muster: Zahl + Ticker, Ticker + Zahl, etc.
    numbers = re.findall(r"(\d+\.?\d*)", text)
    # Ticker: Großbuchstaben-Wort, 1-5 Zeichen, optional mit .XX Suffix
    words = text.upper().split()
    ticker_candidates = [w for w in words if re.match(r"^[A-Z]{1,5}(\.[A-Z]{2})?$", w)
                         and w not in {"HAB", "HABE", "BEI", "VON", "STK", "EUR", "USD", "SOLD", "BOUGHT", "BUY", "SELL"}]

    if not numbers or not ticker_candidates:
        return None

    shares = float(numbers[0])
    ticker = ticker_candidates[0]
    price = float(numbers[1]) if len(numbers) > 1 else None

    return {
        "action": "sell" if is_sell else "buy",
        "ticker": ticker,
        "shares": shares,
        "price": price,
    }


def update_portfolio_position(action: str, ticker: str, shares: float, price: float = None) -> bool:
    """Aktualisiert eine Position im Portfolio."""
    portfolio_path = CONFIG_DIR / "portfolio.json"
    with open(portfolio_path) as f:
        portfolio = json.load(f)

    updated = False
    for account_name, account in portfolio["accounts"].items():
        for pos in account["positions"]:
            pos_ticker = pos.get("ticker", "")
            pos_name = pos.get("name", "")
            if (pos_ticker and (pos_ticker == ticker or pos_ticker.split(".")[0] == ticker)) \
               or ticker in pos_name.upper():
                if action == "buy":
                    old_total = pos["shares"] * pos["buy_in"]
                    new_total = old_total + (shares * (price or pos["buy_in"]))
                    pos["shares"] += shares
                    pos["buy_in"] = new_total / pos["shares"]
                    updated = True
                    break
                elif action == "sell":
                    pos["shares"] -= shares
                    if pos["shares"] <= 0.001:
                        account["positions"].remove(pos)
                    updated = True
                    break
        if updated:
            break

    if updated:
        from datetime import datetime
        portfolio["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(portfolio_path, "w") as f:
            json.dump(portfolio, f, indent=2, ensure_ascii=False)

    return updated


def update_watchlist(action: str, ticker: str, name: str = None):
    """Fügt einen Ticker zur Watchlist hinzu oder entfernt ihn."""
    watchlist_path = CONFIG_DIR / "watchlist.json"
    with open(watchlist_path) as f:
        watchlist = json.load(f)

    if action == "add":
        if not any(w.get("ticker") == ticker for w in watchlist["watchlist"]):
            watchlist["watchlist"].append({"ticker": ticker, "name": name or ticker})
            from datetime import datetime
            watchlist["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    elif action == "remove":
        watchlist["watchlist"] = [w for w in watchlist["watchlist"] if w.get("ticker") != ticker]

    with open(watchlist_path, "w") as f:
        json.dump(watchlist, f, indent=2, ensure_ascii=False)


def create_bot_app(bot_token: str, chat_id: str, on_ticker_request=None, on_briefing_request=None, on_free_chat=None) -> Application:
    """Erstellt die Telegram Bot Application mit Handlern."""

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(chat_id):
            return

        text = update.message.text.strip()

        # Trade-Update erkennen
        trade = parse_trade_message(text)
        if trade:
            trade_id = f"{update.message.message_id}"
            _pending_trades[trade_id] = trade

            action_text = "verkaufen" if trade["action"] == "sell" else "kaufen"
            price_text = f" @ {trade['price']}" if trade['price'] else ""

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Bestätigen", callback_data=f"trade_yes_{trade_id}"),
                    InlineKeyboardButton("❌ Abbrechen", callback_data=f"trade_no_{trade_id}"),
                ]
            ])
            await update.message.reply_text(
                f"Trade erkannt: <b>{trade['shares']} {trade['ticker']} {action_text}</b>{price_text}\n\nStimmt das?",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            return

        # Watchlist-Update erkennen
        watchlist_match = re.match(
            r"(?:watch|watchlist|beobachte|füg hinzu|add)\s+(\w+)",
            text, re.IGNORECASE,
        )
        if watchlist_match:
            ticker = watchlist_match.group(1).upper()
            update_watchlist("add", ticker)
            await update.message.reply_text(f"👁 {ticker} zur Watchlist hinzugefügt.")
            return

        remove_match = re.match(r"(?:unwatch|entferne|remove)\s+(\w+)", text, re.IGNORECASE)
        if remove_match:
            ticker = remove_match.group(1).upper()
            update_watchlist("remove", ticker)
            await update.message.reply_text(f"🗑 {ticker} von Watchlist entfernt.")
            return

        # Ticker-Analyse anfordern
        ticker_match = re.match(r"^[A-Z]{1,5}(?:\.[A-Z]{2})?$", text.upper())
        if ticker_match and on_ticker_request:
            ticker = text.upper()
            await update.message.reply_text(f"🔍 Analysiere {ticker}... Das kann ein paar Minuten dauern.")
            await on_ticker_request(ticker, update, context)
            return

        # Freie Frage an Claude weiterleiten
        if on_free_chat:
            await update.message.reply_text("💬 Denke nach...")
            await on_free_chat(text, update, context)
            return

        await update.message.reply_text("Das hab ich nicht verstanden. /help für Befehle.")

    async def handle_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("trade_yes_"):
            trade_id = data.replace("trade_yes_", "")
            trade = _pending_trades.pop(trade_id, None)
            if trade:
                success = update_portfolio_position(trade["action"], trade["ticker"], trade["shares"], trade["price"])
                if success:
                    emoji = "📉" if trade["action"] == "sell" else "📈"
                    await query.edit_message_text(
                        f"{emoji} Portfolio aktualisiert: {trade['shares']} {trade['ticker']} "
                        f"{'verkauft' if trade['action'] == 'sell' else 'gekauft'}"
                        + (f" @ {trade['price']}" if trade['price'] else "")
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Ticker {trade['ticker']} nicht im Portfolio gefunden."
                    )
        elif data.startswith("trade_no_"):
            trade_id = data.replace("trade_no_", "")
            _pending_trades.pop(trade_id, None)
            await query.edit_message_text("❌ Trade abgebrochen.")

    async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(chat_id):
            return
        with open(CONFIG_DIR / "portfolio.json") as f:
            portfolio = json.load(f)
        summary = f"📊 Portfolio (Stand: {portfolio['last_updated']})\n"
        for acc_name, acc in portfolio["accounts"].items():
            pos_count = len(acc["positions"])
            summary += f"\n<b>{acc_name}</b>: {pos_count} Positionen"
            for pos in acc["positions"]:
                summary += f"\n  • {pos['name']}: {pos['shares']:.2f} Stk"
        for name, bank_acc in portfolio.get("bank_accounts", {}).items():
            label = " (depot)" if bank_acc.get("is_depot_cash") else ""
            summary += f"\n💰 {name}: {bank_acc['value']:.2f}€{label}"
        await update.message.reply_text(summary, parse_mode=ParseMode.HTML)

    async def handle_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(chat_id):
            return
        if on_briefing_request:
            await update.message.reply_text("📊 Generiere Briefing... Das dauert ein paar Minuten.")
            await on_briefing_request(update, context)
        else:
            await update.message.reply_text("Briefing-Funktion nicht verfügbar.")

    async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(chat_id):
            return
        await update.message.reply_text(
            "<b>claudefolio</b> — AI Wealth Advisor\n\n"
            "<b>Analyse:</b>\n"
            "<code>TSLA</code> — Ticker analysieren\n"
            "<code>/briefing</code> — Briefing jetzt generieren\n"
            "<code>/status</code> — Portfolio-Übersicht\n\n"
            "<b>Portfolio:</b>\n"
            "<code>Hab 5 NVDA verkauft bei 180</code> — Trade loggen\n"
            "<code>watch TSLA</code> — Zur Watchlist\n"
            "<code>unwatch TSLA</code> — Von Watchlist\n\n"
            "<b>Chat:</b>\n"
            "Einfach schreiben — ich antworte als dein Berater\n\n"
            "<code>/help</code> — Diese Hilfe",
            parse_mode=ParseMode.HTML,
        )

    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("briefing", handle_briefing))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CallbackQueryHandler(handle_trade_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
