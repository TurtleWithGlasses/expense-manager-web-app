from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.deps import current_user
from app.db.session import get_db
from app.services.user_preferences import user_preferences_service
from app.services.entries import bulk_update_entry_currencies
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
    current_currency = user_preferences_service.get_user_currency(db, user.id)
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
    """Update user's preferred currency and convert all existing entries"""
    try:
        # Get current currency to check if it's actually changing
        current_currency = user_preferences_service.get_user_currency(db, user.id)
        
        # Update user's preferred currency
        user_preferences_service.update_currency(db, user.id, currency_code)
        
        # If currency is actually changing, update all entries
        if current_currency != currency_code:
            update_result = await bulk_update_entry_currencies(db, user.id, currency_code)
            
            return JSONResponse({
                "success": True,
                "message": f"Currency updated to {CURRENCIES.get(currency_code, {}).get('name', currency_code)}. {update_result['message']}",
                "currency": currency_code,
                "entries_updated": update_result["updated_count"],
                "total_entries": update_result["total_entries"]
            })
        else:
            return JSONResponse({
                "success": True,
                "message": f"Currency is already set to {CURRENCIES.get(currency_code, {}).get('name', currency_code)}",
                "currency": currency_code,
                "entries_updated": 0,
                "total_entries": 0
            })
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # If entry update fails, we should still keep the currency preference change
        # but inform the user about the partial failure
        return JSONResponse({
            "success": True,
            "message": f"Currency updated to {CURRENCIES.get(currency_code, {}).get('name', currency_code)}, but some entries may not have been converted due to an error.",
            "currency": currency_code,
            "warning": str(e)
        })

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
    user_currency = user_preferences_service.get_user_currency(db, user.id)
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