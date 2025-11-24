"""
Payment History Service (Phase 29)

Manages payment occurrences and auto-linking suggestions for recurring payments.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.payment_history import PaymentOccurrence, PaymentLinkSuggestion
from app.models.recurring_payment import RecurringPayment
from app.models.entry import Entry, EntryType
from app.services.recurring_payment_service import RecurringPaymentService


class PaymentHistoryService:
    """Service for managing payment history and occurrences"""

    def __init__(self, db: Session):
        self.db = db
        self.recurring_service = RecurringPaymentService(db)

    # ==================== PAYMENT OCCURRENCE MANAGEMENT ====================

    def record_payment(
        self,
        user_id: int,
        recurring_payment_id: int,
        scheduled_date: date,
        actual_date: date,
        amount: float,
        currency_code: str,
        linked_entry_id: Optional[int] = None,
        note: Optional[str] = None,
        confirmation_number: Optional[str] = None
    ) -> PaymentOccurrence:
        """
        Record an actual payment occurrence for a recurring payment.

        Args:
            user_id: User ID
            recurring_payment_id: Recurring payment ID
            scheduled_date: When the payment was scheduled
            actual_date: When the payment was actually made
            amount: Payment amount
            currency_code: Currency code
            linked_entry_id: Optional link to expense entry
            note: Optional note
            confirmation_number: Optional confirmation/transaction number

        Returns:
            PaymentOccurrence instance
        """
        is_late = actual_date > scheduled_date

        occurrence = PaymentOccurrence(
            user_id=user_id,
            recurring_payment_id=recurring_payment_id,
            scheduled_date=scheduled_date,
            actual_date=actual_date,
            amount=Decimal(str(amount)),
            currency_code=currency_code,
            is_paid=True,
            is_skipped=False,
            is_late=is_late,
            linked_entry_id=linked_entry_id,
            note=note,
            confirmation_number=confirmation_number,
            paid_at=datetime.utcnow()
        )

        self.db.add(occurrence)
        self.db.commit()
        self.db.refresh(occurrence)

        return occurrence

    def skip_payment(
        self,
        user_id: int,
        recurring_payment_id: int,
        scheduled_date: date,
        note: Optional[str] = None
    ) -> PaymentOccurrence:
        """
        Mark a scheduled payment as skipped.

        Args:
            user_id: User ID
            recurring_payment_id: Recurring payment ID
            scheduled_date: When the payment was scheduled
            note: Optional reason for skipping

        Returns:
            PaymentOccurrence instance
        """
        # Get payment details
        payment = self.db.query(RecurringPayment).filter(
            RecurringPayment.id == recurring_payment_id,
            RecurringPayment.user_id == user_id
        ).first()

        if not payment:
            raise ValueError("Recurring payment not found")

        occurrence = PaymentOccurrence(
            user_id=user_id,
            recurring_payment_id=recurring_payment_id,
            scheduled_date=scheduled_date,
            actual_date=None,
            amount=payment.amount,
            currency_code=payment.currency_code,
            is_paid=False,
            is_skipped=True,
            is_late=False,
            note=note
        )

        self.db.add(occurrence)
        self.db.commit()
        self.db.refresh(occurrence)

        return occurrence

    def link_payment_to_entry(
        self,
        occurrence_id: int,
        entry_id: int,
        user_id: int
    ) -> PaymentOccurrence:
        """
        Link a payment occurrence to an expense entry.

        Args:
            occurrence_id: Payment occurrence ID
            entry_id: Entry ID to link
            user_id: User ID (for authorization)

        Returns:
            Updated PaymentOccurrence
        """
        occurrence = self.db.query(PaymentOccurrence).filter(
            PaymentOccurrence.id == occurrence_id,
            PaymentOccurrence.user_id == user_id
        ).first()

        if not occurrence:
            raise ValueError("Payment occurrence not found")

        # Verify entry belongs to user
        entry = self.db.query(Entry).filter(
            Entry.id == entry_id,
            Entry.user_id == user_id
        ).first()

        if not entry:
            raise ValueError("Entry not found")

        occurrence.linked_entry_id = entry_id
        occurrence.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(occurrence)

        return occurrence

    def get_payment_history(
        self,
        user_id: int,
        recurring_payment_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_skipped: bool = True
    ) -> List[PaymentOccurrence]:
        """
        Get payment history with optional filters.

        Args:
            user_id: User ID
            recurring_payment_id: Optional filter by specific recurring payment
            start_date: Optional start date filter
            end_date: Optional end date filter
            include_skipped: Whether to include skipped payments

        Returns:
            List of PaymentOccurrence instances
        """
        query = self.db.query(PaymentOccurrence).filter(
            PaymentOccurrence.user_id == user_id
        )

        if recurring_payment_id:
            query = query.filter(PaymentOccurrence.recurring_payment_id == recurring_payment_id)

        if start_date:
            query = query.filter(PaymentOccurrence.scheduled_date >= start_date)

        if end_date:
            query = query.filter(PaymentOccurrence.scheduled_date <= end_date)

        if not include_skipped:
            query = query.filter(PaymentOccurrence.is_skipped == False)

        return query.order_by(PaymentOccurrence.scheduled_date.desc()).all()

    def get_payment_statistics(
        self,
        user_id: int,
        recurring_payment_id: Optional[int] = None,
        months: int = 12
    ) -> Dict:
        """
        Get payment statistics for a user.

        Args:
            user_id: User ID
            recurring_payment_id: Optional filter by specific payment
            months: Number of months to analyze

        Returns:
            Dict with statistics
        """
        start_date = date.today() - timedelta(days=months * 30)

        query = self.db.query(PaymentOccurrence).filter(
            PaymentOccurrence.user_id == user_id,
            PaymentOccurrence.scheduled_date >= start_date
        )

        if recurring_payment_id:
            query = query.filter(PaymentOccurrence.recurring_payment_id == recurring_payment_id)

        occurrences = query.all()

        total_payments = len([o for o in occurrences if o.is_paid])
        skipped_payments = len([o for o in occurrences if o.is_skipped])
        late_payments = len([o for o in occurrences if o.is_late])
        total_amount = sum(float(o.amount) for o in occurrences if o.is_paid)

        on_time_rate = 0.0
        if total_payments > 0:
            on_time_rate = ((total_payments - late_payments) / total_payments) * 100

        return {
            'total_payments': total_payments,
            'skipped_payments': skipped_payments,
            'late_payments': late_payments,
            'on_time_payments': total_payments - late_payments,
            'on_time_rate': round(on_time_rate, 2),
            'total_amount_paid': round(total_amount, 2),
            'average_payment': round(total_amount / total_payments, 2) if total_payments > 0 else 0.0,
            'analysis_period_months': months
        }

    # ==================== AUTO-LINKING SUGGESTIONS ====================

    def generate_link_suggestions(
        self,
        user_id: int,
        days_back: int = 30
    ) -> int:
        """
        Generate auto-linking suggestions by analyzing recent entries.

        Matches entries to recurring payments based on:
        - Amount similarity
        - Date proximity to due dates
        - Category match
        - Description keywords

        Args:
            user_id: User ID
            days_back: How many days back to analyze

        Returns:
            Number of suggestions created
        """
        start_date = date.today() - timedelta(days=days_back)

        # Get active recurring payments
        payments = self.db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            RecurringPayment.is_active == True
        ).all()

        # Get unlinked expense entries
        unlinked_entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == EntryType.EXPENSE,
            Entry.date >= start_date,
            ~Entry.id.in_(
                self.db.query(PaymentOccurrence.linked_entry_id).filter(
                    PaymentOccurrence.linked_entry_id.isnot(None)
                )
            )
        ).all()

        suggestions_created = 0

        for payment in payments:
            for entry in unlinked_entries:
                # Check if suggestion already exists
                existing = self.db.query(PaymentLinkSuggestion).filter(
                    PaymentLinkSuggestion.recurring_payment_id == payment.id,
                    PaymentLinkSuggestion.entry_id == entry.id
                ).first()

                if existing:
                    continue

                # Calculate match score and reason
                score, reason = self._calculate_match_score(payment, entry)

                # Only create suggestion if confidence is high enough
                if score >= 0.6:  # 60% confidence threshold
                    suggestion = PaymentLinkSuggestion(
                        user_id=user_id,
                        recurring_payment_id=payment.id,
                        entry_id=entry.id,
                        confidence_score=Decimal(str(score)),
                        match_reason=json.dumps(reason),
                        is_dismissed=False,
                        is_accepted=False
                    )

                    self.db.add(suggestion)
                    suggestions_created += 1

        self.db.commit()
        return suggestions_created

    def _calculate_match_score(
        self,
        payment: RecurringPayment,
        entry: Entry
    ) -> tuple[float, Dict]:
        """
        Calculate how likely an entry matches a recurring payment.

        Returns:
            Tuple of (confidence_score, match_reasons)
        """
        score = 0.0
        reasons = []

        # Amount similarity (40% weight)
        amount_diff = abs(float(payment.amount) - float(entry.amount))
        amount_similarity = max(0, 1 - (amount_diff / float(payment.amount)))
        score += amount_similarity * 0.4

        if amount_similarity > 0.9:
            reasons.append(f"Amount matches closely (${entry.amount})")
        elif amount_similarity > 0.7:
            reasons.append(f"Amount is similar (${entry.amount})")

        # Category match (30% weight)
        if entry.category_id == payment.category_id:
            score += 0.3
            reasons.append("Category matches")

        # Date proximity to due date (20% weight)
        next_due = self.recurring_service.calculate_next_due_date(payment, entry.date)
        if next_due:
            days_diff = abs((entry.date - next_due).days)
            if days_diff <= 3:
                date_score = 1.0 - (days_diff / 7)
                score += date_score * 0.2
                reasons.append(f"Date is {days_diff} days from due date")

        # Description/note match (10% weight)
        if entry.note and payment.name.lower() in entry.note.lower():
            score += 0.1
            reasons.append("Description contains payment name")

        return min(score, 1.0), {
            'score': round(score, 4),
            'reasons': reasons,
            'entry_date': entry.date.isoformat(),
            'entry_amount': float(entry.amount)
        }

    def get_active_suggestions(
        self,
        user_id: int,
        min_confidence: float = 0.6
    ) -> List[Dict]:
        """
        Get active (not dismissed/accepted) link suggestions.

        Args:
            user_id: User ID
            min_confidence: Minimum confidence score

        Returns:
            List of suggestion dicts with details
        """
        suggestions = self.db.query(PaymentLinkSuggestion).filter(
            PaymentLinkSuggestion.user_id == user_id,
            PaymentLinkSuggestion.is_dismissed == False,
            PaymentLinkSuggestion.is_accepted == False,
            PaymentLinkSuggestion.confidence_score >= min_confidence
        ).order_by(PaymentLinkSuggestion.confidence_score.desc()).all()

        result = []
        for suggestion in suggestions:
            match_reason = json.loads(suggestion.match_reason)

            result.append({
                'id': suggestion.id,
                'recurring_payment_id': suggestion.recurring_payment_id,
                'recurring_payment_name': suggestion.recurring_payment.name,
                'entry_id': suggestion.entry_id,
                'entry_amount': float(suggestion.entry.amount),
                'entry_date': suggestion.entry.date.isoformat(),
                'entry_note': suggestion.entry.note,
                'confidence_score': float(suggestion.confidence_score),
                'match_reasons': match_reason['reasons'],
                'created_at': suggestion.created_at.isoformat()
            })

        return result

    def accept_suggestion(
        self,
        suggestion_id: int,
        user_id: int
    ) -> PaymentOccurrence:
        """
        Accept a link suggestion and create payment occurrence.

        Args:
            suggestion_id: Suggestion ID
            user_id: User ID

        Returns:
            Created PaymentOccurrence
        """
        suggestion = self.db.query(PaymentLinkSuggestion).filter(
            PaymentLinkSuggestion.id == suggestion_id,
            PaymentLinkSuggestion.user_id == user_id
        ).first()

        if not suggestion:
            raise ValueError("Suggestion not found")

        entry = suggestion.entry
        payment = suggestion.recurring_payment

        # Create payment occurrence
        occurrence = self.record_payment(
            user_id=user_id,
            recurring_payment_id=payment.id,
            scheduled_date=entry.date,  # Assume entry date is close to scheduled
            actual_date=entry.date,
            amount=float(entry.amount),
            currency_code=entry.currency_code,
            linked_entry_id=entry.id,
            note=f"Auto-linked from suggestion (confidence: {float(suggestion.confidence_score):.0%})"
        )

        # Mark suggestion as accepted
        suggestion.is_accepted = True
        suggestion.accepted_at = datetime.utcnow()
        self.db.commit()

        return occurrence

    def dismiss_suggestion(
        self,
        suggestion_id: int,
        user_id: int
    ) -> bool:
        """
        Dismiss a link suggestion.

        Args:
            suggestion_id: Suggestion ID
            user_id: User ID

        Returns:
            Success boolean
        """
        suggestion = self.db.query(PaymentLinkSuggestion).filter(
            PaymentLinkSuggestion.id == suggestion_id,
            PaymentLinkSuggestion.user_id == user_id
        ).first()

        if not suggestion:
            return False

        suggestion.is_dismissed = True
        suggestion.dismissed_at = datetime.utcnow()
        self.db.commit()

        return True
