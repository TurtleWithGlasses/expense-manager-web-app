"""
AI Receipt Service — Phase G-1

Uses Claude Haiku vision to extract structured data from a receipt image.
Much more accurate than Tesseract, especially for:
  - Non-English receipts (Turkish, etc.)
  - Poor lighting / curved / crumpled receipts
  - Unusual layouts

Falls back gracefully — caller catches any exception and uses Tesseract instead.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_PROMPT = """Extract data from this receipt image. Return ONLY valid JSON — no markdown fences, no extra text.

Required structure:
{
  "merchant": "store name as printed, or null",
  "total_amount": 12.50,
  "currency": "TRY",
  "date": "YYYY-MM-DD",
  "line_items": [{"description": "item name", "qty": 1, "unit_price": 5.99, "amount": 5.99}],
  "confidence": "high"
}

Rules:
- total_amount: the final amount paid (after tax, after discounts). Use a plain number.
- Turkish receipts: "Tutar", "Toplam", "Ödenecek" all mean total.
- currency: ISO code (TRY, USD, EUR, GBP …). Infer from ₺/$/€/£ symbols if no code printed.
- date: YYYY-MM-DD format. null if not readable.
- line_items: individual product lines only — skip tax, total, subtotal, discount, tip rows.
  - qty: quantity as a number (default 1 if not shown)
  - unit_price: price per unit (same as amount if qty=1)
  - amount: total for that line (qty × unit_price)
  - Empty list [] if no individual items are legible.
- confidence: "high" all fields clear / "medium" some unclear / "low" mostly unreadable.
- Use null for any field you cannot read reliably."""


def _detect_media_type(image_bytes: bytes) -> str:
    header = image_bytes[:12]
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if header[:4] in (b"RIFF", b"WEBP") or header[8:12] == b"WEBP":
        return "image/webp"
    if header[:2] in (b"BM",):
        return "image/bmp"
    return "image/jpeg"


def scan_with_ai(image_bytes: bytes, api_key: str) -> dict:
    """
    Send image to Claude Haiku vision and return a dict with the same
    keys as ScanResult.to_dict() plus source="ai".

    Raises on any API or parsing error — caller should catch and fall back.
    """
    import anthropic

    media_type = _detect_media_type(image_bytes)
    b64_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    logger.debug("AI receipt raw response: %s", raw)

    # Strip accidental markdown fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) >= 2 else raw
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())

    # Normalise total_amount to float | None
    total_amount: Optional[float] = None
    raw_amt = data.get("total_amount")
    if raw_amt is not None:
        try:
            total_amount = float(raw_amt)
            if total_amount <= 0:
                total_amount = None
        except (ValueError, TypeError):
            pass

    # Normalise date to ISO string | None
    receipt_date: Optional[str] = None
    raw_date = data.get("date")
    if raw_date:
        try:
            from datetime import datetime
            receipt_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass

    confidence = data.get("confidence", "medium")
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"

    # Normalise line items — ensure qty/unit_price/amount are numbers
    raw_items = data.get("line_items") or []
    line_items = []
    for item in raw_items:
        try:
            amt = float(item.get("amount") or 0)
            if amt <= 0:
                continue
            qty = float(item.get("qty") or 1) or 1
            unit_price = float(item.get("unit_price") or amt / qty)
            line_items.append({
                "description": str(item.get("description") or "Item"),
                "qty": qty,
                "unit_price": round(unit_price, 2),
                "amount": round(amt, 2),
            })
        except (TypeError, ValueError, ZeroDivisionError):
            continue

    return {
        "merchant": data.get("merchant") or None,
        "total_amount": total_amount,
        "date": receipt_date,
        "currency": data.get("currency") or None,
        "line_items": line_items,
        "confidence": confidence,
        "raw_text": f"[AI Vision · {confidence} confidence]",
        "source": "ai",
    }
