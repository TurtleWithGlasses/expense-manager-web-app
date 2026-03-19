"""
Receipt Scanner Service – Phase 32 Part B

Accepts an uploaded image, preprocesses it with Pillow, extracts text via
Tesseract OCR, then parses the raw text into structured receipt fields:
  - total_amount  (Decimal | None)
  - date          (date | None)
  - merchant      (str | None)
  - raw_text      (str)
  - line_items    (list[dict])  – best-effort line-by-line totals

No images are stored – scan is performed in-memory on the upload bytes.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Tesseract availability check
# ---------------------------------------------------------------------------

def _tesseract_available() -> bool:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


TESSERACT_AVAILABLE: bool | None = None  # lazily set on first call


def _ocr_available() -> bool:
    global TESSERACT_AVAILABLE
    if TESSERACT_AVAILABLE is None:
        TESSERACT_AVAILABLE = _tesseract_available()
    return TESSERACT_AVAILABLE


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def _preprocess(image_bytes: bytes):
    """Return a Pillow Image ready for Tesseract."""
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary (handles RGBA / palette / CMYK)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Upscale very small images so OCR has enough pixels to work with
    min_dim = 1200
    w, h = img.size
    if max(w, h) < min_dim:
        scale = min_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), resample=Image.LANCZOS)

    # Greyscale
    img = img.convert("L")

    # Sharpen then boost contrast
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # Binarise with Otsu-like threshold (simple: > 128 → white)
    threshold = 128
    img = img.point(lambda p: 255 if p > threshold else 0, "1").convert("L")

    return img


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _extract_text(image_bytes: bytes) -> str:
    import pytesseract

    img = _preprocess(image_bytes)
    config = "--psm 6 -l eng"  # Assume uniform block of text
    text = pytesseract.image_to_string(img, config=config)
    return text


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

# Amount: matches "$12.50", "€ 8,99", "12.50 USD", "Total: 45.00" etc.
_AMOUNT_PATTERNS = [
    # "Total  $12.50" / "TOTAL: 12.50"
    re.compile(
        r"(?:total|amount|subtotal|grand\s+total|balance\s+due|due|charge)"
        r"[:\s]*"
        r"[£€$₺₩¥]?\s*(\d{1,6}[.,]\d{2})",
        re.IGNORECASE,
    ),
    # Standalone currency symbol followed by amount  "$12.50"
    re.compile(r"[£€$₺₩¥]\s*(\d{1,6}[.,]\d{2})"),
    # Amount followed by currency code  "12.50 USD"
    re.compile(r"(\d{1,6}[.,]\d{2})\s*(?:USD|EUR|GBP|TRY|JPY|CAD|AUD)\b", re.IGNORECASE),
]

_DATE_PATTERNS = [
    # 2024-03-18 or 18/03/2024 or 03/18/2024 or 18 Mar 2024 etc.
    re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})"),
    re.compile(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"),
    re.compile(
        r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4})",
        re.IGNORECASE,
    ),
]

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_amount(text: str) -> Optional[Decimal]:
    """Return the most likely total amount from OCR text."""
    candidates: list[Decimal] = []

    for pattern in _AMOUNT_PATTERNS:
        for m in pattern.finditer(text):
            raw = m.group(1).replace(",", ".")
            try:
                candidates.append(Decimal(raw))
            except InvalidOperation:
                pass

    if not candidates:
        return None

    # The "total" pattern (first) takes priority; otherwise return the largest
    return candidates[0] if len(candidates) == 1 else max(candidates)


def _parse_date(text: str) -> Optional[date]:
    """Return the first recognisable date from OCR text."""
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        raw = m.group(1).strip()

        # Try ISO / numeric formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
                    "%d-%m-%Y", "%m-%d-%Y", "%d/%m/%y", "%m/%d/%y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass

        # Try textual month formats
        try:
            parts = re.split(r"[\s,]+", raw)
            if len(parts) == 3:
                p0, p1, p2 = parts
                # day month year
                if p0.isdigit() and not p1.isdigit():
                    month = _MONTH_MAP.get(p1[:3].lower())
                    if month:
                        return date(int(p2), month, int(p0))
                # month day year
                if not p0.isdigit() and p1.isdigit():
                    month = _MONTH_MAP.get(p0[:3].lower())
                    if month:
                        year = int(p2) if len(p2) == 4 else 2000 + int(p2)
                        return date(year, month, int(p1))
        except (ValueError, KeyError):
            pass

    return None


def _parse_merchant(lines: list[str]) -> Optional[str]:
    """
    Heuristic: the merchant name is usually the first non-trivial line near
    the top of a receipt that isn't a date or purely numeric.
    """
    skip_patterns = re.compile(
        r"^\s*$|^\d|receipt|invoice|order|date|time|cashier|vat|tax|tel|phone|www|http",
        re.IGNORECASE,
    )
    for line in lines[:8]:  # only inspect first 8 lines
        line = line.strip()
        if len(line) < 3:
            continue
        if skip_patterns.match(line):
            continue
        # Looks like a name – return title-cased version
        return line.title()
    return None


def _parse_line_items(lines: list[str]) -> list[dict]:
    """
    Extract individual line items: lines containing a description + price
    pattern such as  "Coffee       2.50"
    """
    pattern = re.compile(
        r"^(.+?)\s+(\d{1,4}[.,]\d{2})\s*$"
    )
    items = []
    for line in lines:
        m = pattern.match(line.strip())
        if m:
            desc = m.group(1).strip()
            try:
                amt = float(m.group(2).replace(",", "."))
            except ValueError:
                continue
            # Skip lines that look like totals / subtotals
            if re.search(r"total|subtotal|tax|vat|tip|change|cash", desc, re.IGNORECASE):
                continue
            if len(desc) >= 2:
                items.append({"description": desc, "amount": amt})
    return items[:20]  # cap at 20 items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ScanResult:
    def __init__(
        self,
        raw_text: str,
        total_amount: Optional[Decimal],
        scan_date: Optional[date],
        merchant: Optional[str],
        line_items: list[dict],
        confidence: str,
    ):
        self.raw_text = raw_text
        self.total_amount = total_amount
        self.scan_date = scan_date
        self.merchant = merchant
        self.line_items = line_items
        self.confidence = confidence  # "high" | "medium" | "low"

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "date": self.scan_date.isoformat() if self.scan_date else None,
            "merchant": self.merchant,
            "line_items": self.line_items,
            "confidence": self.confidence,
        }


def scan_receipt(image_bytes: bytes) -> ScanResult:
    """
    Main entry point.  Raises RuntimeError if Tesseract is not installed.
    """
    if not _ocr_available():
        raise RuntimeError(
            "Tesseract OCR is not installed or not on PATH.  "
            "Install with: apt-get install tesseract-ocr  (Linux / Railway)  "
            "or download from https://github.com/UB-Mannheim/tesseract/wiki  (Windows)."
        )

    logger.info("Scanning receipt – %d bytes", len(image_bytes))

    raw_text = _extract_text(image_bytes)
    logger.debug("OCR raw text:\n%s", raw_text)

    lines = [l for l in raw_text.splitlines() if l.strip()]

    total_amount = _parse_amount(raw_text)
    scan_date = _parse_date(raw_text)
    merchant = _parse_merchant(lines)
    line_items = _parse_line_items(lines)

    # Simple confidence heuristic
    found = sum([total_amount is not None, scan_date is not None, merchant is not None])
    confidence = "high" if found == 3 else "medium" if found >= 1 else "low"

    logger.info(
        "Scan complete – amount=%s date=%s merchant=%s confidence=%s items=%d",
        total_amount, scan_date, merchant, confidence, len(line_items),
    )

    return ScanResult(
        raw_text=raw_text,
        total_amount=total_amount,
        scan_date=scan_date,
        merchant=merchant,
        line_items=line_items,
        confidence=confidence,
    )
