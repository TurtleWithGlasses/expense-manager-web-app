"""
Service for managing user-defined recurring payments (bills & subscriptions)

This replaces the AI-detected recurring bills with a user-managed system where:
- Users manually create/configure their bills & subscriptions
- Users select categories and set due dates
- AI only provides warnings about upcoming payments
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.recurring_payment import RecurringPayment, PaymentReminder, RecurrenceFrequency
from app.models.category import Category
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RecurringPaymentService:
    """Service for managing recurring payments and reminders"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== RECURRING PAYMENT CRUD ====================

    def create_recurring_payment(
        self,
        user_id: int,
        category_id: int,
        name: str,
        amount: float,
        frequency: RecurrenceFrequency,
        due_day: int,
        start_date: date,
        description: Optional[str] = None,
        currency_code: str = 'USD',
        end_date: Optional[date] = None,
        remind_days_before: int = 3,
        auto_add_to_expenses: bool = False
    ) -> RecurringPayment:
        """
        Create a new recurring payment (bill or subscription)

        Args:
            user_id: User ID
            category_id: Category ID (user-selected)
            name: Payment name (e.g., "Netflix", "Electric Bill")
            amount: Payment amount
            frequency: How often it recurs
            due_day: Day of month (1-31) for monthly+ frequencies, or day of week (0-6) for weekly
            start_date: When this payment starts
            description: Optional description/notes
            currency_code: Currency code
            end_date: Optional end date
            remind_days_before: Days before due date to send reminder

        Returns:
            Created RecurringPayment
        """
        payment = RecurringPayment(
            user_id=user_id,
            category_id=category_id,
            name=name,
            description=description,
            amount=amount,
            currency_code=currency_code,
            frequency=frequency,
            due_day=due_day,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_add_to_expenses=auto_add_to_expenses,
            remind_days_before=remind_days_before,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        logger.info(f"Created recurring payment: {name} for user {user_id}")
        return payment

    def get_user_recurring_payments(
        self,
        user_id: int,
        include_inactive: bool = False
    ) -> List[RecurringPayment]:
        """
        Get all recurring payments for a user

        Args:
            user_id: User ID
            include_inactive: Whether to include inactive payments

        Returns:
            List of RecurringPayment objects
        """
        query = self.db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id
        )

        if not include_inactive:
            query = query.filter(RecurringPayment.is_active == True)

        return query.order_by(RecurringPayment.due_day).all()

    def update_recurring_payment(
        self,
        payment_id: int,
        user_id: int,
        **updates
    ) -> Optional[RecurringPayment]:
        """
        Update a recurring payment

        Args:
            payment_id: Payment ID
            user_id: User ID (for security)
            **updates: Fields to update

        Returns:
            Updated payment or None if not found
        """
        payment = self.db.query(RecurringPayment).filter(
            and_(
                RecurringPayment.id == payment_id,
                RecurringPayment.user_id == user_id
            )
        ).first()

        if not payment:
            return None

        for key, value in updates.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        payment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)

        logger.info(f"Updated recurring payment {payment_id}")
        return payment

    def delete_recurring_payment(
        self,
        payment_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a recurring payment

        Args:
            payment_id: Payment ID
            user_id: User ID (for security)

        Returns:
            True if deleted, False if not found
        """
        payment = self.db.query(RecurringPayment).filter(
            and_(
                RecurringPayment.id == payment_id,
                RecurringPayment.user_id == user_id
            )
        ).first()

        if not payment:
            return False

        self.db.delete(payment)
        self.db.commit()

        logger.info(f"Deleted recurring payment {payment_id}")
        return True

    def toggle_active_status(
        self,
        payment_id: int,
        user_id: int
    ) -> Optional[RecurringPayment]:
        """
        Toggle active/inactive status of a payment

        Args:
            payment_id: Payment ID
            user_id: User ID

        Returns:
            Updated payment or None
        """
        payment = self.db.query(RecurringPayment).filter(
            and_(
                RecurringPayment.id == payment_id,
                RecurringPayment.user_id == user_id
            )
        ).first()

        if not payment:
            return None

        payment.is_active = not payment.is_active
        payment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)

        logger.info(f"Toggled payment {payment_id} active status to {payment.is_active}")
        return payment

    # ==================== NEXT DUE DATE CALCULATION ====================

    def calculate_next_due_date(
        self,
        payment: RecurringPayment,
        after_date: Optional[date] = None
    ) -> Optional[date]:
        """
        Calculate the next due date for a recurring payment

        Args:
            payment: RecurringPayment object
            after_date: Calculate next due date after this date (default: today)

        Returns:
            Next due date or None if payment has ended
        """
        if after_date is None:
            after_date = date.today()

        # Check if payment has ended
        if payment.end_date and after_date > payment.end_date:
            return None

        # Check if we haven't started yet
        if after_date < payment.start_date:
            return self._calculate_first_due_date(payment)

        # Calculate based on frequency
        if payment.frequency == RecurrenceFrequency.WEEKLY:
            return self._next_weekly_due(payment, after_date)
        elif payment.frequency == RecurrenceFrequency.BIWEEKLY:
            return self._next_biweekly_due(payment, after_date)
        elif payment.frequency == RecurrenceFrequency.MONTHLY:
            return self._next_monthly_due(payment, after_date)
        elif payment.frequency == RecurrenceFrequency.QUARTERLY:
            return self._next_quarterly_due(payment, after_date)
        elif payment.frequency == RecurrenceFrequency.ANNUALLY:
            return self._next_annually_due(payment, after_date)

        return None

    def _calculate_first_due_date(self, payment: RecurringPayment) -> date:
        """Calculate the first due date based on start_date and due_day"""
        if payment.frequency == RecurrenceFrequency.WEEKLY:
            # Find next occurrence of due_day (day of week)
            days_ahead = payment.due_day - payment.start_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return payment.start_date + timedelta(days=days_ahead)
        elif payment.frequency == RecurrenceFrequency.BIWEEKLY:
            days_ahead = payment.due_day - payment.start_date.weekday()
            if days_ahead < 0:
                days_ahead += 14
            return payment.start_date + timedelta(days=days_ahead)
        else:
            # Monthly, quarterly, annually - use due_day as day of month
            try:
                return date(payment.start_date.year, payment.start_date.month, payment.due_day)
            except ValueError:
                # Handle invalid dates (e.g., Feb 30)
                return self._last_day_of_month(payment.start_date.year, payment.start_date.month)

    def _next_weekly_due(self, payment: RecurringPayment, after_date: date) -> date:
        """Calculate next weekly due date"""
        days_ahead = payment.due_day - after_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_due = after_date + timedelta(days=days_ahead)

        if payment.end_date and next_due > payment.end_date:
            return None
        return next_due

    def _next_biweekly_due(self, payment: RecurringPayment, after_date: date) -> date:
        """Calculate next biweekly due date"""
        # Find the most recent occurrence
        days_since_start = (after_date - payment.start_date).days
        weeks_since_start = days_since_start // 14

        # Calculate next occurrence
        next_occurrence_week = weeks_since_start + 1
        next_due = payment.start_date + timedelta(days=next_occurrence_week * 14)

        # Adjust to correct day of week
        days_ahead = payment.due_day - next_due.weekday()
        if days_ahead < 0:
            days_ahead += 14
        next_due = next_due + timedelta(days=days_ahead)

        if payment.end_date and next_due > payment.end_date:
            return None
        return next_due

    def _next_monthly_due(self, payment: RecurringPayment, after_date: date) -> date:
        """Calculate next monthly due date"""
        year = after_date.year
        month = after_date.month

        # If we're past the due day this month, move to next month
        if after_date.day >= payment.due_day:
            month += 1
            if month > 12:
                month = 1
                year += 1

        try:
            next_due = date(year, month, payment.due_day)
        except ValueError:
            # Handle invalid dates (e.g., Feb 30)
            next_due = self._last_day_of_month(year, month)

        if payment.end_date and next_due > payment.end_date:
            return None
        return next_due

    def _next_quarterly_due(self, payment: RecurringPayment, after_date: date) -> date:
        """Calculate next quarterly due date"""
        year = after_date.year
        month = after_date.month

        # Move to next quarter
        if after_date.day >= payment.due_day:
            month += 3
        else:
            # Check if we're in the same quarter
            current_quarter_month = ((after_date.month - 1) // 3) * 3 + 1
            start_quarter_month = ((payment.start_date.month - 1) // 3) * 3 + 1

            if current_quarter_month < start_quarter_month:
                month = start_quarter_month
            else:
                month = current_quarter_month + 3

        while month > 12:
            month -= 12
            year += 1

        try:
            next_due = date(year, month, payment.due_day)
        except ValueError:
            next_due = self._last_day_of_month(year, month)

        if payment.end_date and next_due > payment.end_date:
            return None
        return next_due

    def _next_annually_due(self, payment: RecurringPayment, after_date: date) -> date:
        """Calculate next annually due date"""
        year = after_date.year

        # Use start month for annual payments
        month = payment.start_date.month

        # If we're past the due date this year, move to next year
        try:
            next_due = date(year, month, payment.due_day)
            if next_due <= after_date:
                next_due = date(year + 1, month, payment.due_day)
        except ValueError:
            next_due = self._last_day_of_month(year, month)
            if next_due <= after_date:
                next_due = self._last_day_of_month(year + 1, month)

        if payment.end_date and next_due > payment.end_date:
            return None
        return next_due

    def _last_day_of_month(self, year: int, month: int) -> date:
        """Get the last day of a given month"""
        if month == 12:
            return date(year, 12, 31)
        else:
            return date(year, month + 1, 1) - timedelta(days=1)

    # ==================== REMINDERS ====================

    def generate_reminders(self, user_id: int) -> int:
        """
        Generate payment reminders for upcoming recurring payments

        This should be called periodically (e.g., daily) to create reminders
        for payments that are due soon.

        Args:
            user_id: User ID

        Returns:
            Number of reminders created
        """
        payments = self.get_user_recurring_payments(user_id, include_inactive=False)
        reminders_created = 0
        today = date.today()

        for payment in payments:
            next_due = self.calculate_next_due_date(payment, today)

            if not next_due:
                continue

            # Calculate reminder date
            reminder_date = next_due - timedelta(days=payment.remind_days_before)

            # Only create reminder if it should show today or later
            if reminder_date <= today:
                # Check if reminder already exists for this due date
                existing = self.db.query(PaymentReminder).filter(
                    and_(
                        PaymentReminder.user_id == user_id,
                        PaymentReminder.recurring_payment_id == payment.id,
                        PaymentReminder.due_date == next_due,
                        PaymentReminder.is_dismissed == False
                    )
                ).first()

                if not existing:
                    reminder = PaymentReminder(
                        user_id=user_id,
                        recurring_payment_id=payment.id,
                        reminder_date=reminder_date,
                        due_date=next_due,
                        amount=payment.amount,
                        is_dismissed=False,
                        is_paid=False,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(reminder)
                    reminders_created += 1

        if reminders_created > 0:
            self.db.commit()
            logger.info(f"Generated {reminders_created} reminders for user {user_id}")

        return reminders_created

    def get_active_reminders(
        self,
        user_id: int,
        days_ahead: int = 14
    ) -> List[Dict]:
        """
        Get active payment reminders for a user

        Args:
            user_id: User ID
            days_ahead: How many days ahead to look

        Returns:
            List of reminder dictionaries with payment details
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)

        reminders = self.db.query(PaymentReminder).filter(
            and_(
                PaymentReminder.user_id == user_id,
                PaymentReminder.is_dismissed == False,
                PaymentReminder.due_date <= cutoff_date
            )
        ).order_by(PaymentReminder.due_date).all()

        result = []
        for reminder in reminders:
            payment = reminder.recurring_payment
            category_name = payment.category.name if payment.category else 'Uncategorized'

            days_until_due = (reminder.due_date - date.today()).days

            result.append({
                'reminder_id': reminder.id,
                'payment_id': payment.id,
                'name': payment.name,
                'description': payment.description,
                'amount': float(payment.amount),
                'currency_code': payment.currency_code,
                'category_name': category_name,
                'category_id': payment.category_id,
                'due_date': reminder.due_date.isoformat(),
                'days_until_due': days_until_due,
                'is_paid': reminder.is_paid,
                'urgency': 'urgent' if days_until_due <= 2 else 'upcoming'
            })

        return result

    def dismiss_reminder(self, reminder_id: int, user_id: int) -> bool:
        """
        Dismiss a payment reminder

        Args:
            reminder_id: Reminder ID
            user_id: User ID

        Returns:
            True if dismissed, False if not found
        """
        reminder = self.db.query(PaymentReminder).filter(
            and_(
                PaymentReminder.id == reminder_id,
                PaymentReminder.user_id == user_id
            )
        ).first()

        if not reminder:
            return False

        reminder.is_dismissed = True
        self.db.commit()
        return True

    def mark_reminder_paid(
        self,
        reminder_id: int,
        user_id: int,
        entry_id: Optional[int] = None
    ) -> bool:
        """
        Mark a reminder as paid

        Args:
            reminder_id: Reminder ID
            user_id: User ID
            entry_id: Optional entry ID linking to the actual payment

        Returns:
            True if marked paid, False if not found
        """
        reminder = self.db.query(PaymentReminder).filter(
            and_(
                PaymentReminder.id == reminder_id,
                PaymentReminder.user_id == user_id
            )
        ).first()

        if not reminder:
            return False

        reminder.is_paid = True
        if entry_id:
            reminder.paid_entry_id = entry_id
        self.db.commit()
        return True

    # ==================== SUMMARY & ANALYTICS ====================

    def get_payment_summary(self, user_id: int) -> Dict:
        """
        Get summary of all recurring payments

        Args:
            user_id: User ID

        Returns:
            Summary dictionary with totals and counts
        """
        payments = self.get_user_recurring_payments(user_id, include_inactive=False)

        total_monthly_cost = 0
        total_annual_cost = 0

        for payment in payments:
            # Convert to monthly cost
            if payment.frequency == RecurrenceFrequency.WEEKLY:
                monthly_cost = float(payment.amount) * 4
            elif payment.frequency == RecurrenceFrequency.BIWEEKLY:
                monthly_cost = float(payment.amount) * 2
            elif payment.frequency == RecurrenceFrequency.MONTHLY:
                monthly_cost = float(payment.amount)
            elif payment.frequency == RecurrenceFrequency.QUARTERLY:
                monthly_cost = float(payment.amount) / 3
            elif payment.frequency == RecurrenceFrequency.ANNUALLY:
                monthly_cost = float(payment.amount) / 12
            else:
                monthly_cost = 0

            total_monthly_cost += monthly_cost
            total_annual_cost += monthly_cost * 12

        # Get upcoming reminders
        upcoming_count = len(self.get_active_reminders(user_id, days_ahead=7))

        return {
            'total_payments': len(payments),
            'total_monthly_cost': round(total_monthly_cost, 2),
            'total_annual_cost': round(total_annual_cost, 2),
            'upcoming_reminders_count': upcoming_count,
            'payments': [
                {
                    'id': p.id,
                    'name': p.name,
                    'amount': float(p.amount),
                    'currency_code': p.currency_code,
                    'frequency': p.frequency.value,
                    'category_name': p.category.name if p.category else 'Uncategorized',
                    'next_due_date': self.calculate_next_due_date(p).isoformat() if self.calculate_next_due_date(p) else None,
                    'is_active': p.is_active
                }
                for p in payments
            ]
        }
