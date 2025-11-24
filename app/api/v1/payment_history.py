"""
Payment History API Endpoints (Phase 29)

Provides REST API for:
- Recording payment occurrences
- Viewing payment history
- Auto-linking suggestions
- Payment statistics
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services.payment_history_service import PaymentHistoryService

router = APIRouter(prefix="/api/v1/payment-history", tags=["Payment History"])


# ==================== PYDANTIC MODELS ====================

class RecordPaymentRequest(BaseModel):
    recurring_payment_id: int = Field(..., description="Recurring payment ID")
    scheduled_date: date = Field(..., description="When payment was scheduled")
    actual_date: date = Field(..., description="When payment was actually made")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency_code: str = Field("USD", min_length=3, max_length=3)
    linked_entry_id: Optional[int] = Field(None, description="Optional link to expense entry")
    note: Optional[str] = Field(None, description="Optional note")
    confirmation_number: Optional[str] = Field(None, max_length=100, description="Confirmation/transaction number")


class SkipPaymentRequest(BaseModel):
    recurring_payment_id: int = Field(..., description="Recurring payment ID")
    scheduled_date: date = Field(..., description="When payment was scheduled")
    note: Optional[str] = Field(None, description="Reason for skipping")


class LinkToEntryRequest(BaseModel):
    occurrence_id: int = Field(..., description="Payment occurrence ID")
    entry_id: int = Field(..., description="Entry ID to link")


# ==================== PAYMENT OCCURRENCE ENDPOINTS ====================

@router.post("/record")
def record_payment(
    data: RecordPaymentRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Record an actual payment occurrence.

    Users can manually record when they paid a bill, including:
    - When it was due vs when actually paid
    - Amount paid
    - Optional link to expense entry
    - Notes and confirmation number
    """
    service = PaymentHistoryService(db)

    try:
        occurrence = service.record_payment(
            user_id=user.id,
            recurring_payment_id=data.recurring_payment_id,
            scheduled_date=data.scheduled_date,
            actual_date=data.actual_date,
            amount=data.amount,
            currency_code=data.currency_code,
            linked_entry_id=data.linked_entry_id,
            note=data.note,
            confirmation_number=data.confirmation_number
        )

        return {
            "success": True,
            "occurrence_id": occurrence.id,
            "is_late": occurrence.is_late,
            "message": "Payment recorded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/skip")
def skip_payment(
    data: SkipPaymentRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a scheduled payment as skipped.

    Useful for tracking when users intentionally don't pay a bill
    (e.g., skipped a month of subscription, payment holiday, etc.)
    """
    service = PaymentHistoryService(db)

    try:
        occurrence = service.skip_payment(
            user_id=user.id,
            recurring_payment_id=data.recurring_payment_id,
            scheduled_date=data.scheduled_date,
            note=data.note
        )

        return {
            "success": True,
            "occurrence_id": occurrence.id,
            "message": "Payment marked as skipped"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/link-to-entry")
def link_payment_to_entry(
    data: LinkToEntryRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Link a payment occurrence to an expense entry.

    This connects payment history with actual expense tracking,
    allowing users to see which entry corresponds to which bill payment.
    """
    service = PaymentHistoryService(db)

    try:
        occurrence = service.link_payment_to_entry(
            occurrence_id=data.occurrence_id,
            entry_id=data.entry_id,
            user_id=user.id
        )

        return {
            "success": True,
            "occurrence_id": occurrence.id,
            "linked_entry_id": occurrence.linked_entry_id,
            "message": "Payment linked to entry"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
def get_payment_history(
    recurring_payment_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_skipped: bool = True,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment history with optional filters.

    Returns all payment occurrences for the user, with options to filter by:
    - Specific recurring payment
    - Date range
    - Include/exclude skipped payments
    """
    service = PaymentHistoryService(db)

    occurrences = service.get_payment_history(
        user_id=user.id,
        recurring_payment_id=recurring_payment_id,
        start_date=start_date,
        end_date=end_date,
        include_skipped=include_skipped
    )

    result = []
    for occurrence in occurrences:
        result.append({
            "id": occurrence.id,
            "recurring_payment_id": occurrence.recurring_payment_id,
            "recurring_payment_name": occurrence.recurring_payment.name,
            "scheduled_date": occurrence.scheduled_date.isoformat(),
            "actual_date": occurrence.actual_date.isoformat() if occurrence.actual_date else None,
            "amount": float(occurrence.amount),
            "currency_code": occurrence.currency_code,
            "is_paid": occurrence.is_paid,
            "is_skipped": occurrence.is_skipped,
            "is_late": occurrence.is_late,
            "linked_entry_id": occurrence.linked_entry_id,
            "note": occurrence.note,
            "confirmation_number": occurrence.confirmation_number,
            "paid_at": occurrence.paid_at.isoformat() if occurrence.paid_at else None,
            "created_at": occurrence.created_at.isoformat()
        })

    return {
        "occurrences": result,
        "count": len(result)
    }


@router.get("/statistics")
def get_payment_statistics(
    recurring_payment_id: Optional[int] = None,
    months: int = 12,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment statistics and analytics.

    Provides insights like:
    - Total payments made
    - Late payment rate
    - On-time payment percentage
    - Skipped payments
    - Average payment amount
    """
    service = PaymentHistoryService(db)

    stats = service.get_payment_statistics(
        user_id=user.id,
        recurring_payment_id=recurring_payment_id,
        months=months
    )

    return {
        "success": True,
        "statistics": stats
    }


# ==================== AUTO-LINKING ENDPOINTS ====================

@router.post("/generate-suggestions")
def generate_link_suggestions(
    days_back: int = 30,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Generate auto-linking suggestions.

    AI analyzes recent expense entries and suggests which ones might be
    payments for recurring bills based on:
    - Amount similarity
    - Date proximity to due dates
    - Category matching
    - Description keywords
    """
    service = PaymentHistoryService(db)

    try:
        count = service.generate_link_suggestions(
            user_id=user.id,
            days_back=days_back
        )

        return {
            "success": True,
            "suggestions_created": count,
            "message": f"Generated {count} link suggestion(s)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
def get_active_suggestions(
    min_confidence: float = 0.6,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get active auto-linking suggestions.

    Returns AI-generated suggestions for linking expense entries to bills,
    sorted by confidence score (highest first).
    """
    service = PaymentHistoryService(db)

    suggestions = service.get_active_suggestions(
        user_id=user.id,
        min_confidence=min_confidence
    )

    return {
        "suggestions": suggestions,
        "count": len(suggestions)
    }


@router.post("/suggestions/{suggestion_id}/accept")
def accept_suggestion(
    suggestion_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an auto-linking suggestion.

    Creates a payment occurrence and links it to the suggested entry.
    Marks the suggestion as accepted.
    """
    service = PaymentHistoryService(db)

    try:
        occurrence = service.accept_suggestion(
            suggestion_id=suggestion_id,
            user_id=user.id
        )

        return {
            "success": True,
            "occurrence_id": occurrence.id,
            "message": "Suggestion accepted and payment recorded"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/dismiss")
def dismiss_suggestion(
    suggestion_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Dismiss an auto-linking suggestion.

    Marks the suggestion as dismissed. The entry won't be suggested again
    for this recurring payment.
    """
    service = PaymentHistoryService(db)

    success = service.dismiss_suggestion(
        suggestion_id=suggestion_id,
        user_id=user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return {
        "success": True,
        "message": "Suggestion dismissed"
    }


# ==================== BULK OPERATIONS ====================

@router.delete("/occurrences/{occurrence_id}")
def delete_occurrence(
    occurrence_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a payment occurrence.

    Allows users to remove incorrectly recorded payments.
    """
    from app.models.payment_history import PaymentOccurrence

    occurrence = db.query(PaymentOccurrence).filter(
        PaymentOccurrence.id == occurrence_id,
        PaymentOccurrence.user_id == user.id
    ).first()

    if not occurrence:
        raise HTTPException(status_code=404, detail="Payment occurrence not found")

    db.delete(occurrence)
    db.commit()

    return {
        "success": True,
        "message": "Payment occurrence deleted"
    }
