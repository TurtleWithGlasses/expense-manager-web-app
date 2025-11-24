"""
API endpoints for Budget Intelligence features (Phase 28)

Provides:
- Smart budget recommendations
- Recurring bill detection and reminders
- Subscription tracking
- Duplicate transaction detection
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.services.budget_intelligence_service import BudgetIntelligenceService
from app.models.user import User

router = APIRouter(prefix="/api/v1/intelligence", tags=["Budget Intelligence"])


# ==================== SMART BUDGET RECOMMENDATIONS ====================

@router.get("/budget-recommendations")
def get_budget_recommendations(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get smart budget recommendations based on spending patterns

    Analyzes the last 3 months of spending and suggests realistic budgets per category
    """
    service = BudgetIntelligenceService(db)
    return service.get_budget_recommendations(user.id)


@router.get("/budget-alert/{category_id}")
def check_budget_alert(
    category_id: int,
    current_month_spent: float = Query(..., description="Amount spent in current month"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Check if spending is approaching the recommended budget limit for a category
    """
    service = BudgetIntelligenceService(db)
    alert = service.check_budget_alert(user.id, category_id, current_month_spent)

    if alert:
        return alert
    else:
        return {"level": "ok", "message": "Spending is within recommended budget"}


# ==================== BILL PREDICTION & REMINDERS ====================

@router.get("/recurring-bills")
def get_recurring_bills(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Detect recurring bills by analyzing spending patterns over the last 6 months

    Identifies bills that occur regularly (monthly, weekly, biweekly) and predicts next due dates
    """
    service = BudgetIntelligenceService(db)
    return {
        "recurring_bills": service.detect_recurring_bills(user.id)
    }


@router.get("/bill-reminders")
def get_bill_reminders(
    days_ahead: int = Query(7, description="Number of days to look ahead for upcoming bills"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get reminders for bills due in the next N days

    Returns urgent and upcoming bill reminders with predictions
    """
    service = BudgetIntelligenceService(db)
    return {
        "reminders": service.get_upcoming_bill_reminders(user.id, days_ahead)
    }


# ==================== SUBSCRIPTION DETECTION ====================

@router.get("/subscriptions")
def get_subscriptions(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Detect and track subscription charges

    Identifies recurring subscription-like charges and calculates annual costs
    """
    service = BudgetIntelligenceService(db)
    return service.detect_subscriptions(user.id)


@router.get("/subscription-summary")
def get_subscription_summary(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive summary of all subscriptions

    Includes total monthly and annual costs across all detected subscriptions
    """
    service = BudgetIntelligenceService(db)
    return service.get_subscription_summary(user.id)


# ==================== DUPLICATE TRANSACTION DETECTION ====================

@router.get("/duplicates")
def find_duplicate_transactions(
    days_window: int = Query(30, description="Number of days to look back for duplicates"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Find potential duplicate transactions

    Identifies entries that might be duplicates based on:
    - Same amount
    - Same category
    - Same or similar dates (within 2 days)
    - Similar notes
    """
    service = BudgetIntelligenceService(db)
    return {
        "duplicates": service.find_duplicate_transactions(user.id, days_window),
        "days_analyzed": days_window
    }
