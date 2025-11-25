"""
Payment Analytics Dashboard endpoints for visualizing payment trends
"""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services.payment_analytics_service import get_payment_analytics_service
from app.services.user_preferences import user_preferences_service
from app.core.currency import currency_service

router = APIRouter(prefix="/payment-analytics", tags=["payment-analytics"])
templates = Jinja2Templates(directory="app/templates")


def _get_currency_formatter(db: Session, user_id: int):
    """Get currency formatter for the user's currency preference."""
    currency_code = user_preferences_service.get_user_currency(db, user_id)

    def format_currency(amount: float):
        return currency_service.format_amount(amount, currency_code)

    return format_currency


@router.get("", response_class=HTMLResponse)
def payment_analytics_dashboard(
    request: Request,
    period: str = Query("12months", description="Analysis period: 3months, 6months, 12months, all"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Display payment analytics dashboard with comprehensive payment trends.

    Shows payment reliability, spending patterns, projections, and trends.
    """
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
        start_date = date(2000, 1, 1)  # Far back to include all
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

    # Get currency formatter
    format_currency = _get_currency_formatter(db, user.id)

    # Prepare chart data for JavaScript
    # Payment trends chart
    trends_labels = [t['month_name'] for t in payment_trends]
    trends_due = [t['total_due'] for t in payment_trends]
    trends_paid = [t['total_paid'] for t in payment_trends]

    # Category breakdown chart
    category_labels = [c['category_name'] for c in category_breakdown[:10]]  # Top 10
    category_values = [c['total_spent'] for c in category_breakdown[:10]]

    return templates.TemplateResponse(
        "intelligence/payment_analytics.html",
        {
            "request": request,
            "user": user,
            "payment_statistics": payment_statistics,
            "payment_trends": payment_trends,
            "recurring_vs_onetime": recurring_vs_onetime,
            "payment_reliability": payment_reliability,
            "cost_projection": cost_projection,
            "category_breakdown": category_breakdown,
            "format_currency": format_currency,
            "current_period": period,
            "period_display": {
                "3months": "Last 3 Months",
                "6months": "Last 6 Months",
                "12months": "Last 12 Months",
                "all": "All Time"
            }.get(period, "Last 12 Months"),
            # Chart data
            "trends_labels": trends_labels,
            "trends_due": trends_due,
            "trends_paid": trends_paid,
            "category_labels": category_labels,
            "category_values": category_values,
        }
    )
