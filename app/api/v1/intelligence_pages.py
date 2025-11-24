"""
Budget Intelligence UI Pages (Phase 28)

Provides web pages for:
- Smart budget recommendations
- Recurring bill tracking
- Subscription management
- Duplicate detection
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.services.budget_intelligence_service import BudgetIntelligenceService
from app.services.user_preferences import user_preferences_service
from app.core.currency import CURRENCIES, currency_service
from app.models.user import User
from app.templates import render


def _get_currency_helpers(db: Session, user_id: int):
    """Return currency metadata and formatter for the user's preference."""
    currency_code = user_preferences_service.get_user_currency(db, user_id)
    currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])

    def format_currency(amount: float):
        return currency_service.format_amount(amount, currency_code)

    return {
        "user_currency_code": currency_code,
        "user_currency": currency_info,
        "format_currency": format_currency,
    }

router = APIRouter(prefix="/intelligence", tags=["Budget Intelligence Pages"])


@router.get("/", response_class=HTMLResponse)
def intelligence_dashboard(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Budget Intelligence dashboard with overview of all features
    """
    service = BudgetIntelligenceService(db)

    # Get summary data for dashboard
    budget_recs = service.get_budget_recommendations(user.id)
    recurring_bills = service.detect_recurring_bills(user.id)
    bill_reminders = service.get_upcoming_bill_reminders(user.id, days_ahead=7)
    subscription_summary = service.get_subscription_summary(user.id)
    duplicates = service.find_duplicate_transactions(user.id, days_window=30)

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/dashboard.html",
        {
            "user": user,
            "budget_recommendations_count": len(budget_recs['recommendations']),
            "total_recommended_budget": budget_recs['total_recommended_monthly'],
            "recurring_bills_count": len(recurring_bills),
            "bill_reminders_count": len(bill_reminders),
            "subscriptions_count": subscription_summary['count'],
            "subscription_monthly_cost": subscription_summary['total_monthly_cost'],
            "subscription_annual_cost": subscription_summary['total_annual_cost'],
            "duplicates_count": len(duplicates),
            **currency_ctx,
        }
    )


@router.get("/budget-recommendations", response_class=HTMLResponse)
def budget_recommendations_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Smart budget recommendations page
    """
    service = BudgetIntelligenceService(db)
    data = service.get_budget_recommendations(user.id)

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/budget_recommendations.html",
        {
            "user": user,
            **data
            ,
            **currency_ctx
        }
    )


@router.get("/recurring-bills", response_class=HTMLResponse)
def recurring_bills_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Recurring bills detection and reminders page
    """
    service = BudgetIntelligenceService(db)
    recurring_bills = service.detect_recurring_bills(user.id)
    reminders = service.get_upcoming_bill_reminders(user.id, days_ahead=14)

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/recurring_bills.html",
        {
            "user": user,
            "recurring_bills": recurring_bills,
            "bill_reminders": reminders,
            "total_bills": len(recurring_bills),
            **currency_ctx,
        }
    )


@router.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Subscription tracking and management page
    """
    service = BudgetIntelligenceService(db)
    data = service.get_subscription_summary(user.id)

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/subscriptions.html",
        {
            "user": user,
            **data,
            **currency_ctx,
        }
    )


@router.get("/duplicates", response_class=HTMLResponse)
def duplicates_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate transaction detection page
    """
    service = BudgetIntelligenceService(db)
    duplicates = service.find_duplicate_transactions(user.id, days_window=60)

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/duplicates.html",
        {
            "user": user,
            "duplicates": duplicates,
            "total_duplicates": len(duplicates),
            "days_analyzed": 60,
            **currency_ctx,
        }
    )
