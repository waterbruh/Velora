"""
Chat-Verlauf für Telegram-Gespräche.
Speichert die letzten Nachrichten damit Claude Kontext hat.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = Path(__file__).parent.parent.parent / "memory"
HISTORY_FILE = MEMORY_DIR / "chat_history.json"
MAX_MESSAGES = 30


def load_history() -> list[dict]:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history: list[dict]):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_MESSAGES:], f, indent=2, ensure_ascii=False, default=str)


def add_message(role: str, text: str):
    """Fügt eine Nachricht zum Verlauf hinzu. role = 'user' oder 'assistant'."""
    history = load_history()
    history.append({
        "role": role,
        "text": text[:2000],  # Begrenzen damit der Kontext nicht explodiert
        "time": datetime.now().isoformat(),
    })
    save_history(history)


def get_history_for_prompt() -> str:
    """Formatiert den Chat-Verlauf für den Claude-Prompt."""
    history = load_history()
    if not history:
        return "Kein vorheriger Chat-Verlauf."

    lines = ["=== CHAT-VERLAUF (letzte Nachrichten) ==="]
    for msg in history[-15:]:  # Letzte 15 Nachrichten
        role = "DU" if msg["role"] == "assistant" else "NUTZER"
        time = msg["time"][11:16] if "T" in msg.get("time", "") else ""
        lines.append(f"[{time}] {role}: {msg['text']}")
    return "\n".join(lines)


def clear_history():
    """Löscht den Chat-Verlauf."""
    save_history([])
