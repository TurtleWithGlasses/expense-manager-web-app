"""
Receipt Scanner Service – Phase 32 Part B  (improved in Phase B)

Accepts an uploaded image, preprocesses it with Pillow, extracts text via
Tesseract OCR, then parses the raw text into structured receipt fields:
  - total_amount  (Decimal | None)
  - date          (date | None)
  - merchant      (str | None)
  - raw_text      (str)
  - line_items    (list[dict])  – best-effort line-by-line totals
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
    """Return a Pillow Image optimised for Tesseract."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    img = Image.open(io.BytesIO(image_bytes))

    # Normalise mode (handles RGBA / palette / CMYK / greyscale-alpha)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # ── 1. Upscale – Tesseract works best at 300 DPI equivalent
    #       target: longest side at least 1800px for A4-ish receipts
    w, h = img.size
    target = 1800
    if max(w, h) < target:
        scale = target / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), resample=Image.LANCZOS)

    # ── 2. Greyscale
    img = img.convert("L")

    # ── 3. Auto-contrast normalises the histogram regardless of lighting
    img = ImageOps.autocontrast(img, cutoff=2)

    # ── 4. Denoise with median filter before sharpening
    img = img.filter(ImageFilter.MedianFilter(size=3))

    # ── 5. Sharpen twice for crisper character edges
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)

    # ── 6. Boost contrast so faint ink stands out
    img = ImageEnhance.Contrast(img).enhance(2.5)

    # ── 7. Adaptive-style binarisation:
    #       use the image's own mean luminance as the threshold so that
    #       both over-exposed and under-exposed shots work reasonably well.
    import statistics
    pixels = list(img.getdata())
    try:
        mean_lum = int(statistics.mean(pixels))
    except Exception:
        mean_lum = 128
    # Clamp threshold to a sensible range
    threshold = max(100, min(180, mean_lum))
    img = img.point(lambda p: 255 if p > threshold else 0, "1").convert("L")

    return img


# ---------------------------------------------------------------------------
# OCR – try two PSM modes and keep the richer result
# ---------------------------------------------------------------------------

def _extract_text(image_bytes: bytes) -> str:
    """Run Tesseract with multiple PSM modes; return the output with more content."""
    import pytesseract

    img = _preprocess(image_bytes)

    results = {}
    for psm in (6, 4):          # PSM 6 = uniform block; PSM 4 = single-column
        cfg = f"--psm {psm} --oem 3 -l eng"
        text = pytesseract.image_to_string(img, config=cfg)
        results[psm] = text

    # Pick whichever PSM produced more non-whitespace characters
    best = max(results, key=lambda k: len(results[k].replace(" ", "").replace("\n", "")))
    return results[best]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

# ── Amount ──────────────────────────────────────────────────────────────────

# Pattern A – labelled total (broadened keyword list)
_TOTAL_KEYWORDS = (
    r"(?:grand\s+)?total(?:\s+due)?(?:\s+amount)?"
    r"|amount\s+(?:due|paid|charged)"
    r"|balance\s+(?:due|forward)"
    r"|net\s+(?:total|amount)"
    r"|subtotal"
    r"|sub-total"
    r"|payment\s+(?:due|amount)"
    r"|charge(?:d)?"
    r"|due(?:\s+now)?"
    r"|amt(?:\s+due)?"
    r"|pay\s+this\s+amount"
    r"|to\s+pay"
    r"|payable"
)

_AMOUNT_LABELLED = re.compile(
    r"(?:" + _TOTAL_KEYWORDS + r")"
    r"[\s:.*\-]+"                          # separator (colon, spaces, dots, dashes)
    r"[£€$₺₩¥]?\s*(\d{1,6}[.,]\d{2})",
    re.IGNORECASE,
)

# Pattern B – currency symbol immediately before amount
_AMOUNT_CURRENCY_PREFIX = re.compile(
    r"[£€$₺₩¥]\s*(\d{1,6}[.,]\d{2})\b"
)

# Pattern C – amount followed by currency code
_AMOUNT_CURRENCY_SUFFIX = re.compile(
    r"\b(\d{1,6}[.,]\d{2})\s*(?:USD|EUR|GBP|TRY|JPY|CAD|AUD|TL|CHF)\b",
    re.IGNORECASE,
)

# Pattern D – bare amounts (last-resort; only used for bottom-of-receipt scan)
_AMOUNT_BARE = re.compile(r"\b(\d{1,4}[.,]\d{2})\b")


def _normalise_amount(raw: str) -> Optional[Decimal]:
    """Turn '12,50' or '1.234,56' or '1,234.56' into a valid Decimal."""
    # Remove thousands separators that appear before a 2-digit decimal part
    # e.g. "1,234.56" → "1234.56"  or "1.234,56" → "1234.56"
    s = raw.strip()
    # Detect European format: last separator is comma with exactly 2 digits after
    if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', s):
        s = s.replace('.', '').replace(',', '.')
    # Detect US format: last separator is period with exactly 2 digits after
    elif re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', s):
        s = s.replace(',', '')
    else:
        # Simple two-digit decimal: just replace comma → dot
        s = s.replace(',', '.')
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _parse_amount(text: str) -> Optional[Decimal]:
    """Return the most likely total amount from OCR text."""
    # Priority 1: labelled totals (most reliable)
    for m in _AMOUNT_LABELLED.finditer(text):
        val = _normalise_amount(m.group(1))
        if val and val > 0:
            return val

    # Priority 2: currency-symbol-prefixed amounts → return the largest
    candidates: list[Decimal] = []
    for m in _AMOUNT_CURRENCY_PREFIX.finditer(text):
        val = _normalise_amount(m.group(1))
        if val and val > 0:
            candidates.append(val)
    if candidates:
        return max(candidates)

    # Priority 3: amount + currency code
    for m in _AMOUNT_CURRENCY_SUFFIX.finditer(text):
        val = _normalise_amount(m.group(1))
        if val and val > 0:
            return val

    # Priority 4: scan the bottom third of the receipt for the largest bare amount
    #             (totals are almost always near the end of a receipt)
    lines = text.splitlines()
    bottom = lines[max(0, len(lines) * 2 // 3):]
    bare: list[Decimal] = []
    for line in bottom:
        for m in _AMOUNT_BARE.finditer(line):
            val = _normalise_amount(m.group(1))
            if val and val > 0:
                bare.append(val)
    if bare:
        return max(bare)

    return None


# ── Date ────────────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
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
    # DD.MM.YYYY (common in Europe/Turkey)
    re.compile(r"(\d{1,2}\.\d{1,2}\.\d{2,4})"),
]

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_date(text: str) -> Optional[date]:
    """Return the first recognisable date from OCR text."""
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        raw = m.group(1).strip()

        for fmt in (
            "%Y-%m-%d", "%Y/%m/%d",
            "%d/%m/%Y", "%m/%d/%Y",
            "%d-%m-%Y", "%m-%d-%Y",
            "%d/%m/%y", "%m/%d/%y",
            "%d.%m.%Y", "%d.%m.%y",
        ):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass

        # Textual month formats
        try:
            parts = re.split(r"[\s,]+", raw)
            if len(parts) == 3:
                p0, p1, p2 = parts
                if p0.isdigit() and not p1.isdigit():
                    month = _MONTH_MAP.get(p1[:3].lower())
                    if month:
                        return date(int(p2), month, int(p0))
                if not p0.isdigit() and p1.isdigit():
                    month = _MONTH_MAP.get(p0[:3].lower())
                    if month:
                        year = int(p2) if len(p2) == 4 else 2000 + int(p2)
                        return date(year, month, int(p1))
        except (ValueError, KeyError):
            pass

    return None


# ── Merchant ────────────────────────────────────────────────────────────────

# Lines that are definitely NOT a merchant name
_SKIP_LINE = re.compile(
    r"^\s*$"                        # blank
    r"|^\d"                         # starts with digit
    r"|receipt|invoice|order"
    r"|date|time|cashier"
    r"|vat|tax|gst|hst"
    r"|tel|phone|fax|www|http"
    r"|thank\s+you"
    r"|welcome"
    r"|open\s+\d"                   # "open 24 hours"
    r"|page\s+\d",
    re.IGNORECASE,
)

# Minimum fraction of alphabetic chars a line must have to be a merchant name
_MIN_ALPHA_RATIO = 0.45


def _alpha_ratio(s: str) -> float:
    stripped = s.strip()
    if not stripped:
        return 0.0
    alpha = sum(1 for c in stripped if c.isalpha())
    return alpha / len(stripped)


def _parse_merchant(lines: list[str]) -> Optional[str]:
    """
    Heuristic: the merchant name is usually the first non-trivial line near
    the top of the receipt that looks like real text (high alpha ratio).
    """
    for line in lines[:10]:         # inspect first 10 lines
        line = line.strip()
        if len(line) < 3:
            continue
        if _SKIP_LINE.match(line):
            continue
        if _alpha_ratio(line) < _MIN_ALPHA_RATIO:
            continue                # reject ". > Se" type OCR noise
        # Looks like a name
        return line.title()
    return None


# ── Line items ───────────────────────────────────────────────────────────────

_LINE_ITEM_RE = re.compile(r"^(.+?)\s{2,}(\d{1,4}[.,]\d{2})\s*$")
_SKIP_ITEM = re.compile(
    r"total|subtotal|sub-total|tax|vat|gst|tip|change|cash|discount|coupon",
    re.IGNORECASE,
)


def _parse_line_items(lines: list[str]) -> list[dict]:
    items = []
    for line in lines:
        m = _LINE_ITEM_RE.match(line.strip())
        if not m:
            continue
        desc = m.group(1).strip()
        if _SKIP_ITEM.search(desc):
            continue
        val = _normalise_amount(m.group(2))
        if val is None:
            continue
        if len(desc) >= 2:
            items.append({"description": desc, "amount": float(val)})
    return items[:20]


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
    scan_date    = _parse_date(raw_text)
    merchant     = _parse_merchant(lines)
    line_items   = _parse_line_items(lines)

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
