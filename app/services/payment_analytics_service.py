"""
Payment Analytics Service - Comprehensive payment trends and statistics
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.recurring_payment import RecurringPayment
from app.models.payment_history import PaymentOccurrence
from app.models.entry import Entry


class PaymentAnalyticsService:
    """Service for analyzing payment patterns and trends."""

    def __init__(self, db: Session):
        self.db = db

    def get_payment_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get overall payment statistics including reliability metrics.

        Returns:
            Dictionary with on-time rate, late payments, total paid, etc.
        """
        # Get all payment occurrences
        occurrences = self.db.query(PaymentOccurrence).join(
            RecurringPayment
        ).filter(
            RecurringPayment.user_id == user_id
        ).all()

        if not occurrences:
            return {
                'total_occurrences': 0,
                'on_time_count': 0,
                'late_count': 0,
                'missed_count': 0,
                'on_time_rate': 0.0,
                'late_rate': 0.0,
                'missed_rate': 0.0,
                'total_paid': 0.0,
                'average_days_late': 0.0
            }

        total = len(occurrences)
        on_time = sum(1 for occ in occurrences if occ.status == 'on_time')
        late = sum(1 for occ in occurrences if occ.status == 'late')
        missed = sum(1 for occ in occurrences if occ.status == 'missed')

        # Calculate total paid (sum of all linked entries)
        total_paid = 0.0
        late_days_list = []

        for occ in occurrences:
            if occ.linked_entry_id:
                entry = self.db.query(Entry).filter(Entry.id == occ.linked_entry_id).first()
                if entry:
                    total_paid += float(entry.amount)

                    # Calculate days late if applicable
                    if occ.status == 'late' and entry.date and occ.due_date:
                        days_late = (entry.date - occ.due_date).days
                        if days_late > 0:
                            late_days_list.append(days_late)

        average_days_late = sum(late_days_list) / len(late_days_list) if late_days_list else 0.0

        return {
            'total_occurrences': total,
            'on_time_count': on_time,
            'late_count': late,
            'missed_count': missed,
            'on_time_rate': (on_time / total * 100) if total > 0 else 0.0,
            'late_rate': (late / total * 100) if total > 0 else 0.0,
            'missed_rate': (missed / total * 100) if total > 0 else 0.0,
            'total_paid': total_paid,
            'average_days_late': average_days_late
        }

    def get_payment_trends(self, user_id: int, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get monthly payment trends over specified period.

        Args:
            user_id: User ID
            months: Number of months to look back

        Returns:
            List of monthly data with payment counts and totals
        """
        start_date = date.today() - timedelta(days=months * 30)

        # Get occurrences grouped by month
        occurrences = self.db.query(
            extract('year', PaymentOccurrence.due_date).label('year'),
            extract('month', PaymentOccurrence.due_date).label('month'),
            func.count(PaymentOccurrence.id).label('count'),
            func.sum(RecurringPayment.amount).label('total_due')
        ).join(
            RecurringPayment
        ).filter(
            RecurringPayment.user_id == user_id,
            PaymentOccurrence.due_date >= start_date
        ).group_by(
            extract('year', PaymentOccurrence.due_date),
            extract('month', PaymentOccurrence.due_date)
        ).order_by(
            extract('year', PaymentOccurrence.due_date),
            extract('month', PaymentOccurrence.due_date)
        ).all()

        # Calculate actual paid amounts by month
        paid_by_month = {}
        for occ in self.db.query(PaymentOccurrence).join(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            PaymentOccurrence.due_date >= start_date,
            PaymentOccurrence.linked_entry_id.isnot(None)
        ).all():
            entry = self.db.query(Entry).filter(Entry.id == occ.linked_entry_id).first()
            if entry and entry.date:
                key = (entry.date.year, entry.date.month)
                if key not in paid_by_month:
                    paid_by_month[key] = 0.0
                paid_by_month[key] += float(entry.amount)

        # Build monthly trends
        trends = []
        for row in occurrences:
            year = int(row.year)
            month = int(row.month)
            month_name = datetime(year, month, 1).strftime('%B %Y')

            trends.append({
                'year': year,
                'month': month,
                'month_name': month_name,
                'occurrence_count': row.count,
                'total_due': float(row.total_due) if row.total_due else 0.0,
                'total_paid': paid_by_month.get((year, month), 0.0)
            })

        return trends

    def get_recurring_vs_onetime_breakdown(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get breakdown of recurring payments vs one-time expenses.

        Args:
            user_id: User ID
            start_date: Start date for analysis (default: 1 year ago)
            end_date: End date for analysis (default: today)

        Returns:
            Dictionary with recurring and one-time spending totals
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get total from recurring payments (linked entries)
        recurring_total = 0.0
        occurrences = self.db.query(PaymentOccurrence).join(
            RecurringPayment
        ).filter(
            RecurringPayment.user_id == user_id,
            PaymentOccurrence.due_date >= start_date,
            PaymentOccurrence.due_date <= end_date,
            PaymentOccurrence.linked_entry_id.isnot(None)
        ).all()

        for occ in occurrences:
            entry = self.db.query(Entry).filter(Entry.id == occ.linked_entry_id).first()
            if entry:
                recurring_total += float(entry.amount)

        # Get linked entry IDs to exclude from one-time calculation
        linked_entry_ids = [occ.linked_entry_id for occ in occurrences if occ.linked_entry_id]

        # Get total from one-time expenses (entries not linked to recurring payments)
        onetime_query = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date,
            Entry.type == 'expense'
        )

        if linked_entry_ids:
            onetime_query = onetime_query.filter(Entry.id.notin_(linked_entry_ids))

        onetime_total = float(onetime_query.scalar() or 0.0)

        total = recurring_total + onetime_total

        return {
            'recurring_total': recurring_total,
            'onetime_total': onetime_total,
            'total_spending': total,
            'recurring_percentage': (recurring_total / total * 100) if total > 0 else 0.0,
            'onetime_percentage': (onetime_total / total * 100) if total > 0 else 0.0,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }

    def get_payment_reliability_by_bill(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get payment reliability metrics for each recurring payment.

        Returns:
            List of bills with their reliability statistics
        """
        recurring_payments = self.db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id
        ).all()

        results = []
        for payment in recurring_payments:
            occurrences = self.db.query(PaymentOccurrence).filter(
                PaymentOccurrence.recurring_payment_id == payment.id
            ).all()

            if not occurrences:
                continue

            total = len(occurrences)
            on_time = sum(1 for occ in occurrences if occ.status == 'on_time')
            late = sum(1 for occ in occurrences if occ.status == 'late')
            missed = sum(1 for occ in occurrences if occ.status == 'missed')

            results.append({
                'id': payment.id,
                'name': payment.name,
                'amount': float(payment.amount),
                'frequency': payment.frequency.value,
                'category_name': payment.category.name if payment.category else 'Uncategorized',
                'category_icon': payment.category.icon if payment.category else '📄',
                'total_occurrences': total,
                'on_time_count': on_time,
                'late_count': late,
                'missed_count': missed,
                'on_time_rate': (on_time / total * 100) if total > 0 else 0.0,
                'is_active': payment.is_active
            })

        # Sort by on-time rate (worst first for attention)
        results.sort(key=lambda x: x['on_time_rate'])

        return results

    def get_monthly_cost_projection(self, user_id: int) -> Dict[str, Any]:
        """
        Project monthly and annual costs based on active recurring payments.

        Returns:
            Dictionary with projected monthly and annual costs
        """
        active_payments = self.db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            RecurringPayment.is_active.is_(True)
        ).all()

        monthly_total = 0.0
        by_frequency = {
            'daily': 0.0,
            'weekly': 0.0,
            'monthly': 0.0,
            'quarterly': 0.0,
            'annually': 0.0
        }

        for payment in active_payments:
            amount = float(payment.amount)
            frequency = payment.frequency.value

            # Convert all to monthly equivalent
            if frequency == 'daily':
                monthly_equiv = amount * 30
            elif frequency == 'weekly':
                monthly_equiv = amount * 4.33  # Average weeks per month
            elif frequency == 'monthly':
                monthly_equiv = amount
            elif frequency == 'quarterly':
                monthly_equiv = amount / 3
            elif frequency == 'annually':
                monthly_equiv = amount / 12
            else:
                monthly_equiv = 0.0

            monthly_total += monthly_equiv
            by_frequency[frequency] += amount

        return {
            'monthly_projection': monthly_total,
            'annual_projection': monthly_total * 12,
            'by_frequency': by_frequency,
            'active_payment_count': len(active_payments)
        }

    def get_category_spending_breakdown(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Get spending breakdown by category for recurring payments.

        Args:
            user_id: User ID
            start_date: Start date for analysis (default: 1 year ago)
            end_date: End date for analysis (default: today)

        Returns:
            List of categories with spending totals
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get all paid occurrences in date range
        occurrences = self.db.query(PaymentOccurrence).join(
            RecurringPayment
        ).filter(
            RecurringPayment.user_id == user_id,
            PaymentOccurrence.due_date >= start_date,
            PaymentOccurrence.due_date <= end_date,
            PaymentOccurrence.linked_entry_id.isnot(None)
        ).all()

        # Group by category
        category_totals = {}
        for occ in occurrences:
            entry = self.db.query(Entry).filter(Entry.id == occ.linked_entry_id).first()
            if entry:
                payment = occ.recurring_payment
                category_id = payment.category_id
                category_name = payment.category.name if payment.category else 'Uncategorized'
                category_icon = payment.category.icon if payment.category else '📄'

                key = (category_id, category_name, category_icon)
                if key not in category_totals:
                    category_totals[key] = 0.0
                category_totals[key] += float(entry.amount)

        # Convert to list
        total_spending = sum(category_totals.values())
        results = []
        for (cat_id, cat_name, cat_icon), amount in category_totals.items():
            results.append({
                'category_id': cat_id,
                'category_name': cat_name,
                'category_icon': cat_icon,
                'total_spent': amount,
                'percentage': (amount / total_spending * 100) if total_spending > 0 else 0.0
            })

        # Sort by total spent (highest first)
        results.sort(key=lambda x: x['total_spent'], reverse=True)

        return results


# Global instance getter
def get_payment_analytics_service(db: Session) -> PaymentAnalyticsService:
    """Get payment analytics service instance."""
    return PaymentAnalyticsService(db)
