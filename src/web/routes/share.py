"""Web Share Target — Screenshot-basiertes Trade-Logging.

Flow:
  1. User teilt Screenshot von Broker-App via iOS-Share-Sheet → Velora
  2. Browser schickt multipart/form-data an POST /api/share/trade
  3. Wir speichern Screenshot in memory/pending_shares/<uuid>.png + Meta-JSON
  4. Redirect auf /portfolio?share=<uuid> → Trade-Modal öffnet mit Thumbnail
  5. User tippt Shares/Preis manuell (schneller als OCR und zuverlässiger),
     Screenshot bleibt als Referenz im Modal sichtbar

Warum kein KI-OCR? Der Chat-Stream kann aktuell keine Bilder annehmen.
Das Share-Modal ist absichtlich simpel: Screenshot = visuelle Hilfe, der
User tippt in 5 Sekunden die Werte ein. Upgrade auf Vision-API später.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["share"])

SHARE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "memory" / "pending_shares"
SHARE_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_MAX_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/api/share/trade")
async def share_trade(
    title: str = Form(""),
    text: str = Form(""),
    screenshot: UploadFile | None = File(None),
):
    """Web Share Target Endpoint — nimmt Screenshots entgegen."""
    share_id = uuid.uuid4().hex[:12]
    meta = {
        "id": share_id,
        "title": title[:200],
        "text": text[:500],
        "created": datetime.now(timezone.utc).isoformat(),
    }

    if screenshot and screenshot.filename:
        ctype = (screenshot.content_type or "").lower()
        if ctype not in _ALLOWED_MIME:
            logger.warning("Share-Target: abgelehnter Content-Type %s", ctype)
            raise HTTPException(status_code=415, detail="Nur PNG/JPEG/WebP erlaubt.")

        ext = ".png" if "png" in ctype else (".webp" if "webp" in ctype else ".jpg")
        img_path = SHARE_DIR / f"{share_id}{ext}"
        data = await screenshot.read()
        if len(data) > _MAX_BYTES:
            raise HTTPException(status_code=413, detail="Bild zu groß (>8MB).")
        img_path.write_bytes(data)
        meta["screenshot"] = img_path.name
        meta["content_type"] = ctype
        logger.info("Share-Target: Screenshot gespeichert %s (%d KB)", share_id, len(data) // 1024)

    (SHARE_DIR / f"{share_id}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )

    # Redirect auf Portfolio-Seite mit Share-ID → Trade-Modal öffnet automatisch
    return RedirectResponse(url=f"/portfolio?share={share_id}", status_code=303)


@router.get("/api/share/{share_id}/image")
async def share_image(share_id: str):
    """Serviert das Thumbnail im Trade-Modal."""
    # share_id validieren (nur hex)
    if not share_id.isalnum() or len(share_id) > 24:
        raise HTTPException(status_code=400, detail="Invalid share_id")

    for ext in (".png", ".jpg", ".webp"):
        p = SHARE_DIR / f"{share_id}{ext}"
        if p.exists():
            return FileResponse(p, media_type=f"image/{ext.lstrip('.')}")
    raise HTTPException(status_code=404, detail="Nicht gefunden")


@router.get("/api/share/{share_id}/meta")
async def share_meta(share_id: str):
    if not share_id.isalnum() or len(share_id) > 24:
        raise HTTPException(status_code=400, detail="Invalid share_id")
    p = SHARE_DIR / f"{share_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return json.loads(p.read_text())
