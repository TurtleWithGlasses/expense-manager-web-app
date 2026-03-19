"""Receipt Scanning API – Phase 32 Part B"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.models.category import Category
from app.services.user_preferences import user_preferences_service
from app.core.currency import CURRENCIES
from app.templates import render

router = APIRouter(prefix="/receipts", tags=["Receipts"])

# Accepted MIME types / extensions
_ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "image/bmp", "image/tiff", "image/gif",
}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("/scan", response_class=HTMLResponse)
async def receipt_scan_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Receipt scanning UI page."""
    from app.services.receipt_scanner_service import _ocr_available

    user_currency_code = user_preferences_service.get_user_currency(db, user.id)
    user_currency = CURRENCIES.get(user_currency_code, CURRENCIES["USD"])
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name).all()

    return render(request, "receipts/scan.html", {
        "user": user,
        "request": request,
        "user_currency": user_currency,
        "user_currency_code": user_currency_code,
        "categories": categories,
        "ocr_available": _ocr_available(),
    })


@router.post("/scan")
async def scan_receipt(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    """
    Accept an uploaded image, run Tesseract OCR, return extracted fields.

    Response JSON:
    {
      "success": true,
      "total_amount": 18.50,
      "date": "2026-03-15",
      "merchant": "Starbucks",
      "line_items": [...],
      "confidence": "high",
      "raw_text": "..."
    }
    """
    from app.services.receipt_scanner_service import scan_receipt as _scan

    # Validate content type
    ct = (file.content_type or "").lower()
    if ct not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ct}'. Upload a JPEG, PNG, WebP, BMP or TIFF image.",
        )

    image_bytes = await file.read()

    if len(image_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large ({len(image_bytes) // 1024} KB). Maximum is 10 MB.",
        )

    if len(image_bytes) < 100:
        raise HTTPException(status_code=400, detail="Uploaded file appears to be empty.")

    try:
        result = _scan(image_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {exc}")

    return JSONResponse({"success": True, **result.to_dict()})


@router.get("/scan/status")
async def ocr_status(user: User = Depends(current_user)):
    """Return whether Tesseract is available on this server."""
    from app.services.receipt_scanner_service import _ocr_available, TESSERACT_AVAILABLE

    available = _ocr_available()
    info: dict = {"available": available}

    if available:
        try:
            import pytesseract
            info["version"] = str(pytesseract.get_tesseract_version())
        except Exception:
            pass
    else:
        info["install_hint"] = (
            "Linux/Railway: apt-get install tesseract-ocr  |  "
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    return JSONResponse(info)
