"""
API endpoints for user-managed recurring payments (bills & subscriptions)

This replaces AI-detected bills with a user-managed system where:
- Users manually create and configure their recurring payments
- Users select categories and set due dates
- AI only provides warnings about upcoming payments
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

from app.db.session import get_db
from app.deps import current_user
from app.services.recurring_payment_service import RecurringPaymentService
from app.models.recurring_payment import RecurrenceFrequency
from app.models.user import User

router = APIRouter(prefix="/api/v1/recurring-payments", tags=["Recurring Payments"])


# ==================== PYDANTIC MODELS ====================

class RecurringPaymentCreate(BaseModel):
    category_id: int = Field(..., description="Category ID for this payment")
    name: str = Field(..., min_length=1, max_length=255, description="Payment name (e.g., 'Netflix')")
    description: Optional[str] = Field(None, description="Optional description/notes")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency_code: str = Field("USD", min_length=3, max_length=3)
    frequency: str = Field(..., description="Frequency: WEEKLY, BIWEEKLY, MONTHLY, QUARTERLY, ANNUALLY")
    due_day: int = Field(..., description="Day of month (1-31) or day of week (0-6)")
    start_date: date = Field(..., description="Start date")
    end_date: Optional[date] = Field(None, description="Optional end date")
    remind_days_before: int = Field(3, ge=0, le=30, description="Days before due date to remind")
    auto_add_to_expenses: bool = Field(False, description="Automatically add to expenses on due date")


class RecurringPaymentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    frequency: Optional[str] = None
    due_day: Optional[int] = None
    end_date: Optional[date] = None
    remind_days_before: Optional[int] = Field(None, ge=0, le=30)
    auto_add_to_expenses: Optional[bool] = None


# ==================== CRUD ENDPOINTS ====================

@router.post("/")
def create_recurring_payment(
    payment_data: RecurringPaymentCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new recurring payment (bill or subscription)

    Users manually configure their bills/subscriptions by:
    - Selecting a category
    - Setting amount and frequency
    - Defining due dates
    """
    service = RecurringPaymentService(db)

    try:
        frequency_enum = RecurrenceFrequency[payment_data.frequency.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid frequency. Must be one of: {[f.name for f in RecurrenceFrequency]}"
        )

    payment = service.create_recurring_payment(
        user_id=user.id,
        category_id=payment_data.category_id,
        name=payment_data.name,
        amount=payment_data.amount,
        frequency=frequency_enum,
        due_day=payment_data.due_day,
        start_date=payment_data.start_date,
        description=payment_data.description,
        currency_code=payment_data.currency_code,
        end_date=payment_data.end_date,
        remind_days_before=payment_data.remind_days_before,
        auto_add_to_expenses=payment_data.auto_add_to_expenses
    )

    # Calculate next due date
    next_due = service.calculate_next_due_date(payment)

    return {
        "id": payment.id,
        "name": payment.name,
        "amount": float(payment.amount),
        "currency_code": payment.currency_code,
        "frequency": payment.frequency.value,
        "due_day": payment.due_day,
        "category_id": payment.category_id,
        "category_name": payment.category.name if payment.category else "Uncategorized",
        "next_due_date": next_due.isoformat() if next_due else None,
        "is_active": payment.is_active,
        "auto_add_to_expenses": payment.auto_add_to_expenses,
        "created_at": payment.created_at.isoformat()
    }


@router.get("/")
def get_all_recurring_payments(
    include_inactive: bool = False,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get all recurring payments for the current user
    """
    service = RecurringPaymentService(db)
    payments = service.get_user_recurring_payments(user.id, include_inactive=include_inactive)

    result = []
    for payment in payments:
        next_due = service.calculate_next_due_date(payment)
        result.append({
            "id": payment.id,
            "name": payment.name,
            "description": payment.description,
            "amount": float(payment.amount),
            "currency_code": payment.currency_code,
            "frequency": payment.frequency.value,
            "due_day": payment.due_day,
            "start_date": payment.start_date.isoformat(),
            "end_date": payment.end_date.isoformat() if payment.end_date else None,
            "category_id": payment.category_id,
            "category_name": payment.category.name if payment.category else "Uncategorized",
            "next_due_date": next_due.isoformat() if next_due else None,
            "days_until_due": (next_due - date.today()).days if next_due else None,
            "is_active": payment.is_active,
            "auto_add_to_expenses": payment.auto_add_to_expenses,
            "remind_days_before": payment.remind_days_before
        })

    return {"payments": result, "count": len(result)}


@router.get("/{payment_id}")
def get_recurring_payment(
    payment_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific recurring payment by ID
    """
    service = RecurringPaymentService(db)
    payments = service.get_user_recurring_payments(user.id, include_inactive=True)

    payment = next((p for p in payments if p.id == payment_id), None)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    next_due = service.calculate_next_due_date(payment)

    return {
        "id": payment.id,
        "name": payment.name,
        "description": payment.description,
        "amount": float(payment.amount),
        "currency_code": payment.currency_code,
        "frequency": payment.frequency.value,
        "due_day": payment.due_day,
        "start_date": payment.start_date.isoformat(),
        "end_date": payment.end_date.isoformat() if payment.end_date else None,
        "category_id": payment.category_id,
        "category_name": payment.category.name if payment.category else "Uncategorized",
        "next_due_date": next_due.isoformat() if next_due else None,
        "days_until_due": (next_due - date.today()).days if next_due else None,
        "is_active": payment.is_active,
        "remind_days_before": payment.remind_days_before,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat()
    }


@router.put("/{payment_id}")
def update_recurring_payment(
    payment_id: int,
    payment_data: RecurringPaymentUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Update a recurring payment
    """
    service = RecurringPaymentService(db)

    updates = {}
    if payment_data.name is not None:
        updates['name'] = payment_data.name
    if payment_data.description is not None:
        updates['description'] = payment_data.description
    if payment_data.amount is not None:
        updates['amount'] = payment_data.amount
    if payment_data.currency_code is not None:
        updates['currency_code'] = payment_data.currency_code
    if payment_data.frequency is not None:
        try:
            updates['frequency'] = RecurrenceFrequency[payment_data.frequency.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid frequency")
    if payment_data.due_day is not None:
        updates['due_day'] = payment_data.due_day
    if payment_data.end_date is not None:
        updates['end_date'] = payment_data.end_date
    if payment_data.remind_days_before is not None:
        updates['remind_days_before'] = payment_data.remind_days_before
    if payment_data.auto_add_to_expenses is not None:
        updates['auto_add_to_expenses'] = payment_data.auto_add_to_expenses

    payment = service.update_recurring_payment(payment_id, user.id, **updates)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    next_due = service.calculate_next_due_date(payment)

    return {
        "id": payment.id,
        "name": payment.name,
        "amount": float(payment.amount),
        "next_due_date": next_due.isoformat() if next_due else None,
        "is_active": payment.is_active,
        "updated_at": payment.updated_at.isoformat()
    }


@router.delete("/{payment_id}")
def delete_recurring_payment(
    payment_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a recurring payment
    """
    service = RecurringPaymentService(db)
    success = service.delete_recurring_payment(payment_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {"message": "Payment deleted successfully"}


@router.post("/{payment_id}/toggle")
def toggle_payment_active_status(
    payment_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle active/inactive status of a payment (pause/resume)
    """
    service = RecurringPaymentService(db)
    payment = service.toggle_active_status(payment_id, user.id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "id": payment.id,
        "name": payment.name,
        "is_active": payment.is_active,
        "message": f"Payment {'activated' if payment.is_active else 'paused'}"
    }


# ==================== REMINDERS ====================

@router.post("/generate-reminders")
def generate_payment_reminders(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Generate reminders for upcoming payments

    This is typically called automatically, but can be triggered manually
    """
    service = RecurringPaymentService(db)
    count = service.generate_reminders(user.id)

    return {
        "reminders_created": count,
        "message": f"Generated {count} reminder(s)"
    }


@router.get("/reminders/active")
def get_active_payment_reminders(
    days_ahead: int = 14,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get active payment reminders (AI warnings for upcoming bills)

    These are automatically generated based on user-defined payments.
    AI warns users about upcoming bills to help manage cash flow.
    """
    service = RecurringPaymentService(db)
    reminders = service.get_active_reminders(user.id, days_ahead=days_ahead)

    return {
        "reminders": reminders,
        "count": len(reminders)
    }


@router.post("/reminders/{reminder_id}/dismiss")
def dismiss_payment_reminder(
    reminder_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Dismiss a payment reminder
    """
    service = RecurringPaymentService(db)
    success = service.dismiss_reminder(reminder_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return {"message": "Reminder dismissed"}


@router.post("/reminders/{reminder_id}/mark-paid")
def mark_reminder_as_paid(
    reminder_id: int,
    entry_id: Optional[int] = Body(None, embed=True),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a reminder as paid (optionally link to an entry)
    """
    service = RecurringPaymentService(db)
    success = service.mark_reminder_paid(reminder_id, user.id, entry_id)

    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return {"message": "Reminder marked as paid"}


# ==================== SUMMARY ====================

@router.get("/summary")
def get_payment_summary(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary of all recurring payments

    Returns:
    - Total count
    - Total monthly cost
    - Total annual cost
    - Upcoming reminders count
    - List of all payments
    """
    service = RecurringPaymentService(db)
    return service.get_payment_summary(user.id)
