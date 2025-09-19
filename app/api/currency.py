from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.deps import current_user
from app.db.session import get_db
from app.services.user_preferences import user_preferences_service
from app.core.currency import CURRENCIES, currency_service
from app.templates import render

router = APIRouter(prefix="/currency", tags=["currency"])

@router.get("/settings", response_class=HTMLResponse)
async def currency_settings_page(
    request: Request,
    user = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Currency settings page"""
    current_currency = user_preferences_service.get_user_currency(db, user["id"])
    return render(request, "settings/currency_settings.html", {
        "currencies": CURRENCIES,
        "current_currency": current_currency,
        "user": user
    })

@router.post("/update")
async def update_currency(
    currency_code: str = Form(...),
    user = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Update user's preferred currency"""
    try:
        user_preferences_service.update_currency(db, user["id"], currency_code)
        return JSONResponse({
            "success": True,
            "message": f"Currency updated to {CURRENCIES.get(currency_code, {}).get('name', currency_code)}",
            "currency": currency_code
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/rates")
async def get_exchange_rates():
    """Get current exchange rates"""
    rates = await currency_service.get_exchange_rates()
    return JSONResponse({
        "base_currency": "USD",
        "rates": rates,
        "currencies": CURRENCIES
    })

@router.post("/convert")
async def convert_amount(
    request: Request,
    user = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Convert amounts for HTMX requests"""
    user_currency = user_preferences_service.get_user_currency(db, user["id"])
    return JSONResponse({
        "currency": user_currency,
        "symbol": CURRENCIES.get(user_currency, {}).get('symbol', '$')
    })

@router.get("/rates-display", response_class=HTMLResponse)
async def get_exchange_rates_display(request: Request):
    """Get current exchange rates as HTML"""
    rates = await currency_service.get_exchange_rates()
    
    return render(request, "settings/_exchange_rates.html", {
        "rates": rates,
        "currencies": CURRENCIES,
        "base_currency": "USD"
    })