"""
Budget Intelligence Service for Phase 28: Advanced AI Features

This service provides:
1. Smart Budget Recommendations
2. Bill Prediction & Reminders
3. Subscription Detection
4. Duplicate Transaction Detection
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from collections import defaultdict
import statistics
import numpy as np

from app.models.entry import Entry
from app.models.category import Category
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BudgetIntelligenceService:
    """Service for intelligent budget analysis and recommendations"""

    def __init__(self, db: Session):
        self.db = db

        # Seasonal adjustment factors (multipliers for different months)
        # Based on typical spending patterns: holidays, back-to-school, etc.
        self.seasonal_factors = {
            1: 1.0,   # January (New Year recovery)
            2: 0.95,  # February (lowest spending month)
            3: 1.0,   # March
            4: 1.05,  # April (Spring shopping)
            5: 1.05,  # May
            6: 1.1,   # June (Summer vacation prep)
            7: 1.15,  # July (Summer vacation)
            8: 1.1,   # August (Back-to-school)
            9: 1.0,   # September
            10: 1.05, # October (Fall shopping)
            11: 1.2,  # November (Thanksgiving, Black Friday)
            12: 1.25  # December (Holiday season)
        }

    # ==================== SMART BUDGET RECOMMENDATIONS ====================

    def get_budget_recommendations(self, user_id: int) -> Dict:
        """
        Analyze spending patterns and suggest realistic budgets per category

        Args:
            user_id: User ID

        Returns:
            Dictionary with budget recommendations per category
        """
        # Analyze last 3 months of spending
        three_months_ago = datetime.now() - timedelta(days=90)

        # Fetch individual expense entries and aggregate per month in Python to remain DB-agnostic
        expense_rows = self.db.query(
            Entry.category_id,
            Category.name.label('category_name'),
            Entry.date,
            Entry.amount
        ).join(
            Category, Entry.category_id == Category.id
        ).filter(
            and_(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= three_months_ago
            )
        ).all()

        # Group by category/month
        category_data = defaultdict(lambda: {
            'name': '',
            'monthly_totals': defaultdict(float),
            'entry_count': 0
        })

        for row in expense_rows:
            month_key = row.date.strftime('%Y-%m')
            category_info = category_data[row.category_id]
            category_info['name'] = row.category_name
            category_info['monthly_totals'][month_key] += float(row.amount)
            category_info['entry_count'] += 1

        # Convert monthly totals dict to list for downstream calculations
        for data in category_data.values():
            data['monthly_amounts'] = list(data['monthly_totals'].values())
            del data['monthly_totals']

        recommendations = []
        total_recommended = 0

        current_month = datetime.now().month

        for category_id, data in category_data.items():
            amounts = data['monthly_amounts']
            if not amounts:
                continue

            avg_monthly = statistics.mean(amounts)
            max_monthly = max(amounts)
            min_monthly = min(amounts)

            # Calculate variability
            variability = ((max_monthly - min_monthly) / avg_monthly * 100) if avg_monthly > 0 else 0

            # ENHANCED: Use percentile-based budget for highly variable categories
            if variability > 50:
                # For variable spending, use 75th percentile instead of mean
                recommended = np.percentile(amounts, 75)
                recommendation_method = 'percentile-based'
                confidence = 'low'
                description = 'Highly variable spending - using 75th percentile'
            elif variability > 30:
                # Moderate variability: use median + 20%
                recommended = statistics.median(amounts) * 1.2
                recommendation_method = 'median-based'
                confidence = 'medium'
                description = 'Moderate spending variation'
            else:
                # Consistent spending: use average + 15% buffer
                recommended = avg_monthly * 1.15
                recommendation_method = 'average-based'
                confidence = 'high'
                description = 'Consistent spending pattern'

            # ENHANCED: Apply seasonal adjustment for current month
            seasonal_factor = self.seasonal_factors.get(current_month, 1.0)
            seasonal_recommended = recommended * seasonal_factor

            # ENHANCED: Calculate spending trend (increasing/decreasing)
            if len(amounts) >= 2:
                # Simple linear trend: compare first half vs second half
                mid = len(amounts) // 2
                first_half_avg = statistics.mean(amounts[:mid]) if mid > 0 else avg_monthly
                second_half_avg = statistics.mean(amounts[mid:])
                trend_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

                if trend_pct > 10:
                    trend = 'increasing'
                    trend_note = f'Spending trending up ({trend_pct:.1f}% increase)'
                elif trend_pct < -10:
                    trend = 'decreasing'
                    trend_note = f'Spending trending down ({abs(trend_pct):.1f}% decrease)'
                else:
                    trend = 'stable'
                    trend_note = 'Spending is stable'
            else:
                trend = 'unknown'
                trend_note = 'Not enough data for trend analysis'

            recommendations.append({
                'category_id': category_id,
                'category_name': data['name'],
                'recommended_budget': round(recommended, 2),
                'seasonal_recommended_budget': round(seasonal_recommended, 2),
                'seasonal_factor': seasonal_factor,
                'current_average': round(avg_monthly, 2),
                'max_spent': round(max_monthly, 2),
                'min_spent': round(min_monthly, 2),
                'variability_percent': round(variability, 1),
                'confidence': confidence,
                'description': description,
                'recommendation_method': recommendation_method,
                'trend': trend,
                'trend_note': trend_note,
                'entry_count': data['entry_count']
            })

            total_recommended += recommended

        # Sort by recommended budget (highest first)
        recommendations.sort(key=lambda x: x['recommended_budget'], reverse=True)

        return {
            'recommendations': recommendations,
            'total_recommended_monthly': round(total_recommended, 2),
            'analysis_period_days': 90,
            'generated_at': datetime.now().isoformat()
        }

    def check_budget_alert(self, user_id: int, category_id: int, current_month_spent: float) -> Optional[Dict]:
        """
        Check if spending is approaching recommended budget limit

        Args:
            user_id: User ID
            category_id: Category ID
            current_month_spent: Amount spent in current month

        Returns:
            Alert dictionary if approaching limit, None otherwise
        """
        recommendations = self.get_budget_recommendations(user_id)

        for rec in recommendations['recommendations']:
            if rec['category_id'] == category_id:
                recommended = rec['recommended_budget']
                percentage = (current_month_spent / recommended * 100) if recommended > 0 else 0

                if percentage >= 90:
                    return {
                        'level': 'critical',
                        'message': f"You've spent {percentage:.0f}% of your recommended budget",
                        'category': rec['category_name'],
                        'spent': current_month_spent,
                        'budget': recommended,
                        'remaining': recommended - current_month_spent
                    }
                elif percentage >= 75:
                    return {
                        'level': 'warning',
                        'message': f"You've spent {percentage:.0f}% of your recommended budget",
                        'category': rec['category_name'],
                        'spent': current_month_spent,
                        'budget': recommended,
                        'remaining': recommended - current_month_spent
                    }

        return None

    # ==================== BILL PREDICTION & REMINDERS ====================

    def detect_recurring_bills(self, user_id: int) -> List[Dict]:
        """
        Detect recurring bills by analyzing entry patterns

        Args:
            user_id: User ID

        Returns:
            List of detected recurring bills
        """
        # Look at last 6 months
        six_months_ago = datetime.now() - timedelta(days=180)

        # Get all expenses
        entries = self.db.query(Entry).filter(
            and_(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= six_months_ago
            )
        ).order_by(Entry.date).all()

        # Group by category and similar amounts
        potential_bills = defaultdict(list)

        for entry in entries:
            # Create a key based on category and similar amount (rounded to nearest 5)
            rounded_amount = round(entry.amount / 5) * 5
            key = f"{entry.category_id}_{rounded_amount}"
            potential_bills[key].append(entry)

        recurring_bills = []

        for key, bill_entries in potential_bills.items():
            if len(bill_entries) >= 3:  # At least 3 occurrences
                # Calculate average interval between bills
                intervals = []
                for i in range(1, len(bill_entries)):
                    days_diff = (bill_entries[i].date - bill_entries[i-1].date).days
                    intervals.append(days_diff)

                if intervals:
                    avg_interval = statistics.mean(intervals)
                    std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0

                    # Check if intervals are consistent
                    is_monthly = 25 <= avg_interval <= 35 and std_interval < 10
                    is_weekly = 5 <= avg_interval <= 9 and std_interval < 3
                    is_biweekly = 12 <= avg_interval <= 16 and std_interval < 5

                    if is_monthly or is_weekly or is_biweekly:
                        frequency = 'monthly' if is_monthly else ('weekly' if is_weekly else 'biweekly')

                        # Predict next occurrence
                        last_entry = bill_entries[-1]
                        next_due_date = last_entry.date + timedelta(days=int(avg_interval))
                        days_until_due = (next_due_date - datetime.now().date()).days

                        # Get category name
                        category_name = 'Uncategorized'
                        if last_entry.category:
                            category_name = last_entry.category.name

                        # Use note from first entry or category name
                        description = bill_entries[0].note or category_name

                        recurring_bills.append({
                            'description': description,
                            'category_id': bill_entries[0].category_id,
                            'category_name': category_name,
                            'avg_amount': round(statistics.mean([e.amount for e in bill_entries]), 2),
                            'frequency': frequency,
                            'avg_interval_days': round(avg_interval, 1),
                            'occurrences': len(bill_entries),
                            'last_date': last_entry.date.isoformat(),
                            'predicted_next_date': next_due_date.isoformat(),
                            'days_until_due': days_until_due,
                            'confidence': 'high' if std_interval < 3 else 'medium'
                        })

        # Sort by next due date
        recurring_bills.sort(key=lambda x: x['days_until_due'])

        return recurring_bills

    def get_upcoming_bill_reminders(self, user_id: int, days_ahead: int = 7) -> List[Dict]:
        """
        Get reminders for bills due in the next N days

        Args:
            user_id: User ID
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming bill reminders
        """
        recurring_bills = self.detect_recurring_bills(user_id)

        reminders = []
        for bill in recurring_bills:
            if 0 <= bill['days_until_due'] <= days_ahead:
                urgency = 'urgent' if bill['days_until_due'] <= 2 else 'upcoming'

                reminders.append({
                    **bill,
                    'urgency': urgency,
                    'reminder_message': f"{bill['description']} is due in {bill['days_until_due']} days"
                })

        return reminders

    # ==================== SUBSCRIPTION DETECTION ====================

    def detect_subscriptions(self, user_id: int) -> List[Dict]:
        """
        Identify recurring subscription charges

        Args:
            user_id: User ID

        Returns:
            List of detected subscriptions
        """
        # Get recurring bills
        recurring_bills = self.detect_recurring_bills(user_id)

        # Subscription keywords
        subscription_keywords = [
            'subscription', 'premium', 'pro', 'plus', 'netflix', 'spotify',
            'amazon', 'prime', 'youtube', 'membership', 'monthly', 'annual',
            'hulu', 'disney', 'apple', 'google', 'microsoft', 'adobe',
            'dropbox', 'github', 'linkedin', 'gym', 'fitness'
        ]

        subscriptions = []

        for bill in recurring_bills:
            description_lower = bill['description'].lower()

            # Check if it's likely a subscription
            is_subscription = any(keyword in description_lower for keyword in subscription_keywords)

            # Also consider monthly recurring charges as potential subscriptions
            if bill['frequency'] == 'monthly' or is_subscription:
                annual_cost = bill['avg_amount'] * (12 if bill['frequency'] == 'monthly' else 52 if bill['frequency'] == 'weekly' else 26)

                subscriptions.append({
                    **bill,
                    'annual_cost': round(annual_cost, 2),
                    'type': 'subscription',
                    'is_confirmed': is_subscription
                })

        # Sort by annual cost (highest first)
        subscriptions.sort(key=lambda x: x['annual_cost'], reverse=True)

        return subscriptions

    def get_subscription_summary(self, user_id: int) -> Dict:
        """
        Get summary of all subscriptions

        Args:
            user_id: User ID

        Returns:
            Subscription summary with totals
        """
        subscriptions = self.detect_subscriptions(user_id)

        total_monthly = sum(
            s['avg_amount'] if s['frequency'] == 'monthly' else
            s['avg_amount'] * 4 if s['frequency'] == 'weekly' else
            s['avg_amount'] * 2
            for s in subscriptions
        )

        total_annual = sum(s['annual_cost'] for s in subscriptions)

        return {
            'subscriptions': subscriptions,
            'count': len(subscriptions),
            'total_monthly_cost': round(total_monthly, 2),
            'total_annual_cost': round(total_annual, 2),
            'generated_at': datetime.now().isoformat()
        }

    # ==================== DUPLICATE TRANSACTION DETECTION ====================

    def find_duplicate_transactions(self, user_id: int, days_window: int = 30) -> List[Dict]:
        """
        Find potential duplicate entries

        Args:
            user_id: User ID
            days_window: Number of days to look back

        Returns:
            List of potential duplicate groups
        """
        cutoff_date = datetime.now() - timedelta(days=days_window)

        # Get recent entries
        entries = self.db.query(Entry).filter(
            and_(
                Entry.user_id == user_id,
                Entry.date >= cutoff_date
            )
        ).order_by(desc(Entry.date)).all()

        duplicates = []
        checked = set()

        for i, entry1 in enumerate(entries):
            if entry1.id in checked:
                continue

            potential_duplicates = []

            for entry2 in entries[i+1:]:
                if entry2.id in checked:
                    continue

                # Check for duplicates
                same_amount = abs(entry1.amount - entry2.amount) < 0.01
                same_category = entry1.category_id == entry2.category_id
                same_type = entry1.type == entry2.type
                date_diff = abs((entry1.date - entry2.date).days)
                within_date_range = date_diff <= 2

                # Check note similarity
                notes_similar = False
                if entry1.note and entry2.note:
                    notes_similar = entry1.note.lower().strip() == entry2.note.lower().strip()
                elif not entry1.note and not entry2.note:
                    notes_similar = True

                if same_amount and same_category and same_type and within_date_range:
                    confidence = 'high' if notes_similar and date_diff == 0 else 'medium'

                    if not potential_duplicates:
                        potential_duplicates.append({
                            'id': entry1.id,
                            'amount': entry1.amount,
                            'category': entry1.category.name if entry1.category else 'Uncategorized',
                            'date': entry1.date.isoformat(),
                            'notes': entry1.note or '',
                            'type': entry1.type
                        })

                    potential_duplicates.append({
                        'id': entry2.id,
                        'amount': entry2.amount,
                        'category': entry2.category.name if entry2.category else 'Uncategorized',
                        'date': entry2.date.isoformat(),
                        'notes': entry2.note or '',
                        'type': entry2.type
                    })
                    checked.add(entry2.id)

            if len(potential_duplicates) > 1:
                duplicates.append({
                    'group_id': f"dup_{entry1.id}",
                    'entries': potential_duplicates,
                    'count': len(potential_duplicates),
                    'confidence': confidence,
                    'total_amount': sum(e['amount'] for e in potential_duplicates)
                })
                checked.add(entry1.id)

        return duplicates
