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
from app.services.payment_history_service import PaymentHistoryService  # Phase 29
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


@router.get("/dashboard", response_class=HTMLResponse)
def intelligence_dashboard_alias(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Alias route for /intelligence/dashboard -> /intelligence/"""
    return intelligence_dashboard(request, user, db)


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
    - View payment history (Phase 29)
    - Get auto-linking suggestions (Phase 29)
    """
    payment_service = RecurringPaymentService(db)
    history_service = PaymentHistoryService(db)

    # Get all recurring payments
    payments = payment_service.get_user_recurring_payments(user.id, include_inactive=False)

    # Get active reminders (AI warnings)
    reminders = payment_service.get_active_reminders(user.id, days_ahead=14)

    # Get payment summary
    summary = payment_service.get_payment_summary(user.id)

    # Get auto-linking suggestions (Phase 29)
    suggestions = history_service.get_active_suggestions(user.id, min_confidence=0.6)

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
            "link_suggestions": suggestions,  # Phase 29
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


@router.get("/payment-history", response_class=HTMLResponse)
def payment_history_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Payment History page - view all payment occurrences

    Shows:
    - Timeline of all payments (paid, late, skipped)
    - Filter by bill/subscription
    - Payment reliability metrics
    - Auto-linking suggestions
    """
    history_service = PaymentHistoryService(db)
    payment_service = RecurringPaymentService(db)

    # Get all payment history (last 12 months)
    from datetime import timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    payment_history = history_service.get_payment_history(
        user_id=user.id,
        start_date=start_date,
        end_date=end_date,
        include_skipped=True
    )

    # Get payment statistics
    payment_stats = history_service.get_payment_statistics(user.id)

    # Get all recurring payments for filter dropdown
    recurring_payments = payment_service.get_user_recurring_payments(user.id, include_inactive=True)

    # Get auto-linking suggestions
    suggestions = history_service.get_active_suggestions(user.id, min_confidence=0.6)

    # Get user's categories
    from app.models.category import Category
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name).all()

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/payment_history.html",
        {
            "user": user,
            "payment_history": payment_history,
            "payment_stats": payment_stats,
            "recurring_payments": recurring_payments,
            "link_suggestions": suggestions,
            "categories": categories,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **currency_ctx,
        }
    )


@router.get("/payment-analytics", response_class=HTMLResponse)
def payment_analytics_page(
    request: Request,
    period: str = "12months",
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Payment Analytics page - visualize payment trends and patterns

    Shows:
    - Payment trends over time
    - On-time vs late payment rate
    - Cost projections
    - Category breakdown
    - Recurring vs one-time spending
    """
    from app.services.payment_analytics_service import get_payment_analytics_service
    from datetime import timedelta

    analytics_service = get_payment_analytics_service(db)

    # Determine date range based on period
    end_date = date.today()
    if period == "3months":
        start_date = end_date - timedelta(days=90)
        months_back = 3
    elif period == "6months":
        start_date = end_date - timedelta(days=180)
        months_back = 6
    elif period == "all":
        start_date = date(2000, 1, 1)
        months_back = 60
    else:  # Default to 12 months
        start_date = end_date - timedelta(days=365)
        months_back = 12
        period = "12months"

    # Get all analytics data
    payment_statistics = analytics_service.get_payment_statistics(user.id)
    payment_trends = analytics_service.get_payment_trends(user.id, months=months_back)
    recurring_vs_onetime = analytics_service.get_recurring_vs_onetime_breakdown(
        user.id, start_date=start_date, end_date=end_date
    )
    payment_reliability = analytics_service.get_payment_reliability_by_bill(user.id)
    cost_projection = analytics_service.get_monthly_cost_projection(user.id)
    category_breakdown = analytics_service.get_category_spending_breakdown(
        user.id, start_date=start_date, end_date=end_date
    )

    # Prepare chart data for JavaScript
    trends_labels = [t['month_name'] for t in payment_trends]
    trends_due = [t['total_due'] for t in payment_trends]
    trends_paid = [t['total_paid'] for t in payment_trends]

    category_labels = [c['category_name'] for c in category_breakdown[:10]]
    category_values = [c['total_spent'] for c in category_breakdown[:10]]

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(
        request,
        "intelligence/payment_analytics.html",
        {
            "user": user,
            "payment_statistics": payment_statistics,
            "payment_trends": payment_trends,
            "recurring_vs_onetime": recurring_vs_onetime,
            "payment_reliability": payment_reliability,
            "cost_projection": cost_projection,
            "category_breakdown": category_breakdown,
            "current_period": period,
            "period_display": {
                "3months": "Last 3 Months",
                "6months": "Last 6 Months",
                "12months": "Last 12 Months",
                "all": "All Time"
            }.get(period, "Last 12 Months"),
            "trends_labels": trends_labels,
            "trends_due": trends_due,
            "trends_paid": trends_paid,
            "category_labels": category_labels,
            "category_values": category_values,
            **currency_ctx,
        }
    )
