"""Advanced Temporal Feature Engineering for ML Models"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
import numpy as np

from app.models.entry import Entry


class TemporalFeatureExtractor:
    """Extract advanced temporal patterns from transaction history"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_temporal_features(self, entry: Entry, user_id: int, 
                                  historical_entries: Optional[List[Entry]] = None) -> Dict:
        """
        Extract comprehensive temporal features for an entry
        
        Args:
            entry: The entry to extract features for
            user_id: User ID for historical context
            historical_entries: Optional pre-fetched historical entries for efficiency
        
        Returns:
            Dictionary of temporal features
        """
        features = {}
        
        # Get historical entries if not provided
        if historical_entries is None:
            historical_entries = self._get_historical_entries(user_id, entry.date)
        
        # Basic time features
        features.update(self._basic_time_features(entry))
        
        # Weekly patterns
        features.update(self._weekly_patterns(entry))
        
        # Monthly patterns
        features.update(self._monthly_patterns(entry))
        
        # Seasonal patterns
        features.update(self._seasonal_patterns(entry))
        
        # Historical context
        features.update(self._historical_context(entry, historical_entries))
        
        # Recurrence detection
        features.update(self._recurrence_features(entry, historical_entries))
        
        # Spending trends
        features.update(self._spending_trends(entry, historical_entries))
        
        return features
    
    def _get_historical_entries(self, user_id: int, before_date: datetime.date, 
                                days_back: int = 180) -> List[Entry]:
        """Get historical entries for context (last 6 months by default)"""
        start_date = before_date - timedelta(days=days_back)
        
        return self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date < before_date
        ).order_by(Entry.date.desc()).all()
    
    def _basic_time_features(self, entry: Entry) -> Dict:
        """Extract basic time-based features"""
        weekday = entry.date.weekday()  # 0=Monday, 6=Sunday
        
        return {
            'weekday': weekday,
            'month': entry.date.month,
            'day_of_month': entry.date.day,
            'is_weekend': int(weekday >= 5),
            'is_monday': int(weekday == 0),
            'is_friday': int(weekday == 4),
            'week_of_year': entry.date.isocalendar()[1],
            'quarter': (entry.date.month - 1) // 3 + 1  # 1-4
        }
    
    def _weekly_patterns(self, entry: Entry) -> Dict:
        """Extract weekly pattern features"""
        day = entry.date.day
        
        return {
            'is_first_week': int(day <= 7),
            'is_second_week': int(8 <= day <= 14),
            'is_third_week': int(15 <= day <= 21),
            'is_fourth_week': int(day >= 22),
            'is_week_start': int(entry.date.weekday() in [0, 1]),  # Mon, Tue
            'is_week_end': int(entry.date.weekday() in [4, 5, 6])  # Fri, Sat, Sun
        }
    
    def _monthly_patterns(self, entry: Entry) -> Dict:
        """Extract monthly pattern features"""
        day = entry.date.day
        
        return {
            'is_month_start': int(day <= 5),
            'is_month_mid': int(8 <= day <= 23),
            'is_month_end': int(day >= 24),
            'is_first_day': int(day == 1),
            'is_last_week': int(day >= 24),
            'days_from_month_start': day,
            'days_to_month_end': self._days_in_month(entry.date) - day
        }
    
    def _seasonal_patterns(self, entry: Entry) -> Dict:
        """Extract seasonal pattern features"""
        month = entry.date.month
        
        # Northern hemisphere seasons
        if month in [12, 1, 2]:
            season = 0  # Winter
        elif month in [3, 4, 5]:
            season = 1  # Spring
        elif month in [6, 7, 8]:
            season = 2  # Summer
        else:
            season = 3  # Fall
        
        return {
            'season': season,
            'is_winter': int(season == 0),
            'is_spring': int(season == 1),
            'is_summer': int(season == 2),
            'is_fall': int(season == 3),
            'is_holiday_season': int(month in [11, 12])  # Nov, Dec
        }
    
    def _historical_context(self, entry: Entry, historical_entries: List[Entry]) -> Dict:
        """Extract features based on historical context"""
        if not historical_entries:
            return {
                'has_history': 0,
                'similar_transactions_count': 0,
                'avg_transaction_amount': 0,
                'days_since_last_transaction': 999
            }
        
        # Find similar transactions (similar text or amount)
        entry_text = (entry.note or '').lower()
        entry_amount = float(entry.amount)
        
        similar_count = 0
        same_category_entries = []
        
        for hist_entry in historical_entries:
            hist_text = (hist_entry.note or '').lower()
            hist_amount = float(hist_entry.amount)
            
            # Similar if text matches or amount within 10%
            if entry_text and hist_text and entry_text in hist_text:
                similar_count += 1
            elif abs(hist_amount - entry_amount) / entry_amount < 0.1:
                similar_count += 1
            
            # Track same category entries
            if hist_entry.category_id == entry.category_id:
                same_category_entries.append(hist_entry)
        
        # Calculate days since last transaction
        if historical_entries:
            days_since_last = (entry.date - historical_entries[0].date).days
        else:
            days_since_last = 999
        
        # Average transaction amount
        amounts = [float(e.amount) for e in historical_entries]
        avg_amount = np.mean(amounts) if amounts else 0
        
        return {
            'has_history': 1,
            'similar_transactions_count': similar_count,
            'total_historical_transactions': len(historical_entries),
            'avg_transaction_amount': avg_amount,
            'amount_vs_avg_ratio': entry_amount / avg_amount if avg_amount > 0 else 1.0,
            'days_since_last_transaction': min(days_since_last, 365),
            'same_category_count': len(same_category_entries)
        }
    
    def _recurrence_features(self, entry: Entry, historical_entries: List[Entry]) -> Dict:
        """Detect recurring patterns (subscriptions, bills, etc.)"""
        if not historical_entries:
            return {
                'is_recurring': 0,
                'recurring_interval_days': 0,
                'recurring_confidence': 0.0
            }
        
        entry_amount = float(entry.amount)
        entry_text = (entry.note or '').lower()
        
        # Find transactions with similar amounts (±5%)
        similar_amounts = []
        for hist_entry in historical_entries:
            hist_amount = float(hist_entry.amount)
            if abs(hist_amount - entry_amount) / entry_amount < 0.05:
                similar_amounts.append(hist_entry)
        
        if len(similar_amounts) < 2:
            return {
                'is_recurring': 0,
                'recurring_interval_days': 0,
                'recurring_confidence': 0.0
            }
        
        # Calculate intervals between similar transactions
        intervals = []
        for i in range(len(similar_amounts) - 1):
            days_diff = (similar_amounts[i].date - similar_amounts[i + 1].date).days
            intervals.append(days_diff)
        
        if not intervals:
            return {
                'is_recurring': 0,
                'recurring_interval_days': 0,
                'recurring_confidence': 0.0
            }
        
        # Check for common patterns
        avg_interval = np.mean(intervals)
        interval_std = np.std(intervals) if len(intervals) > 1 else 999
        
        # Common recurring patterns
        is_weekly = abs(avg_interval - 7) < 2
        is_biweekly = abs(avg_interval - 14) < 3
        is_monthly = abs(avg_interval - 30) < 5
        is_yearly = abs(avg_interval - 365) < 10
        
        # Confidence based on consistency
        confidence = 1.0 / (1.0 + interval_std / avg_interval) if avg_interval > 0 else 0.0
        
        return {
            'is_recurring': int(confidence > 0.7 and len(similar_amounts) >= 3),
            'is_weekly_recurring': int(is_weekly),
            'is_monthly_recurring': int(is_monthly),
            'is_yearly_recurring': int(is_yearly),
            'recurring_interval_days': int(avg_interval),
            'recurring_confidence': confidence,
            'recurring_count': len(similar_amounts)
        }
    
    def _spending_trends(self, entry: Entry, historical_entries: List[Entry]) -> Dict:
        """Analyze spending trends"""
        if not historical_entries:
            return {
                'spending_trend': 0.0,
                'is_above_average': 0,
                'spending_volatility': 0.0
            }
        
        entry_amount = float(entry.amount)
        
        # Last 30 days
        thirty_days_ago = entry.date - timedelta(days=30)
        recent_entries = [e for e in historical_entries if e.date >= thirty_days_ago]
        
        # Last 90 days
        ninety_days_ago = entry.date - timedelta(days=90)
        older_entries = [e for e in historical_entries 
                        if ninety_days_ago <= e.date < thirty_days_ago]
        
        # Calculate averages
        recent_avg = np.mean([float(e.amount) for e in recent_entries]) if recent_entries else 0
        older_avg = np.mean([float(e.amount) for e in older_entries]) if older_entries else 0
        
        # Trend: positive = spending increasing
        if older_avg > 0:
            trend = (recent_avg - older_avg) / older_avg
        else:
            trend = 0.0
        
        # Volatility
        all_amounts = [float(e.amount) for e in historical_entries[:30]]  # Last 30 transactions
        volatility = np.std(all_amounts) / np.mean(all_amounts) if len(all_amounts) > 1 and np.mean(all_amounts) > 0 else 0
        
        return {
            'spending_trend_30d': trend,
            'recent_avg_amount': recent_avg,
            'is_above_recent_avg': int(entry_amount > recent_avg),
            'spending_volatility': volatility,
            'amount_percentile': self._calculate_percentile(entry_amount, all_amounts)
        }
    
    def _days_in_month(self, date: datetime.date) -> int:
        """Get number of days in month"""
        if date.month == 12:
            next_month = date.replace(year=date.year + 1, month=1, day=1)
        else:
            next_month = date.replace(month=date.month + 1, day=1)
        last_day = next_month - timedelta(days=1)
        return last_day.day
    
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate what percentile this value is in the list"""
        if not values:
            return 0.5
        
        sorted_values = sorted(values)
        position = sum(1 for v in sorted_values if v < value)
        return position / len(sorted_values)

