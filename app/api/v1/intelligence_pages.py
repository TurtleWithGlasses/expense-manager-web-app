"""
Budget Intelligence UI Pages (Phase 28)

Provides web pages for:
- Smart budget recommendations
- Recurring bill tracking
- Subscription management
- Duplicate detection
"""

from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.services.budget_intelligence_service import BudgetIntelligenceService
from app.services.recurring_payment_service import RecurringPaymentService
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
    budget_service = BudgetIntelligenceService(db)
    payment_service = RecurringPaymentService(db)

    # Get summary data for dashboard
    budget_recs = budget_service.get_budget_recommendations(user.id)
    payment_summary = payment_service.get_payment_summary(user.id)
    active_reminders = payment_service.get_active_reminders(user.id, days_ahead=7)
    duplicates = budget_service.find_duplicate_transactions(user.id, days_window=30)

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/dashboard.html",
        {
            "user": user,
            "budget_recommendations_count": len(budget_recs['recommendations']),
            "total_recommended_budget": budget_recs['total_recommended_monthly'],
            "recurring_bills_count": payment_summary['total_payments'],
            "bill_reminders_count": len(active_reminders),
            "subscriptions_count": payment_summary['total_payments'],
            "subscription_monthly_cost": payment_summary['total_monthly_cost'],
            "subscription_annual_cost": payment_summary['total_annual_cost'],
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


@router.get("/bills-subscriptions", response_class=HTMLResponse)
def bills_subscriptions_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Unified bills & subscriptions management page

    User-managed system where users:
    - Create and configure recurring payments
    - Select categories for bills/subscriptions
    - Set due dates and amounts
    - Get AI warnings for upcoming payments
    """
    payment_service = RecurringPaymentService(db)

    # Get all recurring payments
    payments = payment_service.get_user_recurring_payments(user.id, include_inactive=False)

    # Get active reminders (AI warnings)
    reminders = payment_service.get_active_reminders(user.id, days_ahead=14)

    # Get payment summary
    summary = payment_service.get_payment_summary(user.id)

    # Get user's categories for the form
    from app.models.category import Category
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name).all()

    # Format payments with next due dates
    formatted_payments = []
    for payment in payments:
        next_due = payment_service.calculate_next_due_date(payment)
        formatted_payments.append({
            'id': payment.id,
            'name': payment.name,
            'description': payment.description,
            'amount': float(payment.amount),
            'currency_code': payment.currency_code,
            'frequency': payment.frequency.value,
            'due_day': payment.due_day,
            'category_id': payment.category_id,
            'category_name': payment.category.name if payment.category else 'Uncategorized',
            'next_due_date': next_due.isoformat() if next_due else None,
            'days_until_due': (next_due - date.today()).days if next_due else None,
            'is_active': payment.is_active
        })

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/bills_subscriptions.html",
        {
            "user": user,
            "payments": formatted_payments,
            "reminders": reminders,
            "total_payments": summary['total_payments'],
            "total_monthly_cost": summary['total_monthly_cost'],
            "total_annual_cost": summary['total_annual_cost'],
            "categories": categories,
            **currency_ctx,
        }
    )


# Keep old routes for backward compatibility, redirect to new unified page
@router.get("/recurring-bills", response_class=HTMLResponse)
def recurring_bills_page_redirect(request: Request):
    """Redirect to unified bills & subscriptions page"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/intelligence/bills-subscriptions", status_code=301)


@router.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_page_redirect(request: Request):
    """Redirect to unified bills & subscriptions page"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/intelligence/bills-subscriptions", status_code=301)


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
