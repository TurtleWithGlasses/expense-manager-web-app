"""Receipt Scanning API – Phase 32B + Phase A (persistence) + Phase C (category) + Phase D (duplicate detection)"""
import base64
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.entry import Entry
from app.models.user import User
from app.models.category import Category
from app.models.receipt import Receipt
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
    db: Session = Depends(get_db),
):
    """
    Accept an uploaded image, run Tesseract OCR, persist the receipt record,
    and return extracted fields + receipt_id.
    """
    from app.services.receipt_scanner_service import scan_receipt as _scan

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

    # Phase C – suggest a category based on merchant name / OCR text
    from app.services.category_suggester import suggest_category
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name).all()
    suggestion = suggest_category(result.merchant, result.raw_text, categories, db=db, user_id=user.id)

    # Persist the receipt record immediately (entry_id linked later when user saves)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    extracted_json = json.dumps({
        "total_amount": float(result.total_amount) if result.total_amount else None,
        "date": result.scan_date.isoformat() if result.scan_date else None,
        "merchant": result.merchant,
        "line_items": result.line_items,
        "suggested_category_id": suggestion["category_id"] if suggestion else None,
        "suggested_category_name": suggestion["category_name"] if suggestion else None,
    })

    receipt = Receipt(
        user_id=user.id,
        entry_id=None,
        image_data=image_b64,
        ocr_text=result.raw_text,
        extracted_data=extracted_json,
        confidence=result.confidence,
        merchant=result.merchant,
        amount=float(result.total_amount) if result.total_amount else None,
        receipt_date=result.scan_date,
        created_at=datetime.utcnow(),
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    # Phase D – duplicate detection: look for entries with the same amount
    # on the same date (±1 day window to handle timezone edge cases)
    duplicates = []
    if result.total_amount and result.scan_date:
        amount_val = float(result.total_amount)
        date_from  = result.scan_date - timedelta(days=1)
        date_to    = result.scan_date + timedelta(days=1)
        tolerance  = 0.01

        dup_entries = (
            db.query(Entry)
            .filter(
                Entry.user_id == user.id,
                Entry.type    == "expense",
                Entry.date    >= date_from,
                Entry.date    <= date_to,
                func.abs(Entry.amount - amount_val) <= tolerance,
            )
            .limit(5)
            .all()
        )
        for e in dup_entries:
            duplicates.append({
                "entry_id": e.id,
                "amount":   float(e.amount),
                "date":     e.date.isoformat(),
                "note":     e.note or "",
                "category": e.category.name if e.category else "",
            })

    response_data = {"success": True, "receipt_id": receipt.id, **result.to_dict()}
    if suggestion:
        response_data["suggested_category_id"]   = suggestion["category_id"]
        response_data["suggested_category_name"] = suggestion["category_name"]
    response_data["duplicates"] = duplicates
    return JSONResponse(response_data)


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


@router.get("/history", response_class=HTMLResponse)
async def receipt_history(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Receipt history page – lists all scanned receipts for the user."""
    receipts = (
        db.query(Receipt)
        .filter(Receipt.user_id == user.id)
        .order_by(Receipt.created_at.desc())
        .limit(100)
        .all()
    )

    user_currency_code = user_preferences_service.get_user_currency(db, user.id)
    user_currency = CURRENCIES.get(user_currency_code, CURRENCIES["USD"])

    return render(request, "receipts/history.html", {
        "user": user,
        "request": request,
        "receipts": receipts,
        "user_currency": user_currency,
        "user_currency_code": user_currency_code,
    })
