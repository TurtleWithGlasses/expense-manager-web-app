"""Anomaly Detection Service for Unusual Spending Patterns"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from app.models.entry import Entry
from app.models.category import Category


class AnomalyDetectionService:
    """Service for detecting unusual spending patterns and transactions"""

    def __init__(self, db: Session):
        self.db = db
        self.model = None  # Will be created with adaptive contamination
        self.scaler = StandardScaler()
        self.is_trained = False

        # Seasonal awareness: major holidays (month-day)
        self.holidays = [
            (1, 1),   # New Year's Day
            (2, 14),  # Valentine's Day
            (7, 4),   # Independence Day (US)
            (10, 31), # Halloween
            (11, 24), # Black Friday (approximate)
            (12, 24), # Christmas Eve
            (12, 25), # Christmas
            (12, 31)  # New Year's Eve
        ]

    def detect_spending_anomalies(self, user_id: int, days_back: int = 90) -> Dict:
        """
        Detect unusual spending patterns in recent transactions

        Args:
            user_id: User ID
            days_back: Number of days to analyze

        Returns:
            Dictionary with detected anomalies
        """
        try:
            # Get transactions
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 10:
                return {
                    'success': False,
                    'message': 'Need at least 10 transactions for anomaly detection',
                    'min_transactions_needed': 10,
                    'current_transactions': len(entries)
                }

            # Convert to DataFrame
            df = pd.DataFrame([{
                'id': e.id,
                'date': e.date,
                'amount': float(e.amount),
                'category_id': e.category_id if e.category_id else 0,
                'category_name': e.category.name if e.category else 'Uncategorized',
                'note': e.note or '',
                'weekday': e.date.weekday(),
                'day_of_month': e.date.day
            } for e in entries])

            # Extract features for anomaly detection
            features = self._extract_anomaly_features(df, user_id)

            if features is None or len(features) < 10:
                return {
                    'success': False,
                    'message': 'Insufficient data for anomaly detection'
                }

            # Calculate adaptive contamination rate based on historical data
            contamination_rate = self._calculate_adaptive_contamination(df)

            # Create model with adaptive contamination
            self.model = IsolationForest(
                contamination=contamination_rate,
                random_state=42,
                n_estimators=100
            )

            # Scale features
            features_scaled = self.scaler.fit_transform(features)

            # Fit model and detect anomalies
            self.model.fit(features_scaled)
            anomaly_predictions = self.model.predict(features_scaled)
            anomaly_scores = self.model.decision_function(features_scaled)

            # Add predictions to DataFrame
            df['anomaly_score'] = anomaly_scores
            df['is_anomaly'] = anomaly_predictions == -1

            # Get anomalous transactions
            anomalies = df[df['is_anomaly']].copy()

            if len(anomalies) == 0:
                return {
                    'success': True,
                    'anomalies': [],
                    'total_transactions_analyzed': len(df),
                    'anomalies_detected': 0,
                    'message': 'No unusual spending patterns detected. Great job!'
                }

            # Analyze each anomaly
            anomaly_details = []
            for idx, row in anomalies.iterrows():
                explanation = self._explain_anomaly(row, df)

                anomaly_details.append({
                    'entry_id': int(row['id']),
                    'date': row['date'].isoformat(),
                    'amount': round(float(row['amount']), 2),
                    'category': row['category_name'],
                    'note': row['note'],
                    'anomaly_score': round(float(row['anomaly_score']), 3),
                    'severity': self._get_severity_level(row['anomaly_score']),
                    'explanation': explanation
                })

            # Sort by severity (most severe first)
            anomaly_details.sort(key=lambda x: x['anomaly_score'])

            return {
                'success': True,
                'anomalies': anomaly_details,
                'total_transactions_analyzed': len(df),
                'anomalies_detected': len(anomalies),
                'anomaly_rate': round(float(len(anomalies) / len(df) * 100), 2),
                'summary': self._generate_anomaly_summary(anomalies, df)
            }

        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return {
                'success': False,
                'message': f"Anomaly detection failed: {str(e)}",
                'error': str(e)
            }

    def _calculate_adaptive_contamination(self, df: pd.DataFrame) -> float:
        """
        Calculate adaptive contamination rate based on spending variance

        Users with high spending variance may naturally have more outliers,
        so we adjust the contamination rate accordingly.
        """
        try:
            # Calculate coefficient of variation (std/mean)
            cv = df['amount'].std() / df['amount'].mean() if df['amount'].mean() > 0 else 0

            # High variance users: expect more anomalies (up to 15%)
            # Low variance users: expect fewer anomalies (down to 5%)
            if cv > 1.0:
                return min(0.15, 0.1 + cv * 0.05)
            elif cv < 0.3:
                return max(0.05, 0.1 - (0.3 - cv) * 0.1)
            else:
                return 0.1  # Default 10%

        except Exception:
            return 0.1  # Fallback to default

    def _is_near_holiday(self, date) -> bool:
        """Check if date is within 3 days of a major holiday"""
        for holiday_month, holiday_day in self.holidays:
            if date.month == holiday_month:
                if abs(date.day - holiday_day) <= 3:
                    return True
        return False

    def _get_season(self, month: int) -> int:
        """Get season number (0-3) from month"""
        if month in [12, 1, 2]:
            return 0  # Winter
        elif month in [3, 4, 5]:
            return 1  # Spring
        elif month in [6, 7, 8]:
            return 2  # Summer
        else:
            return 3  # Fall

    def _extract_anomaly_features(self, df: pd.DataFrame, user_id: int) -> Optional[np.ndarray]:
        """Extract enhanced features for anomaly detection with seasonal awareness"""
        try:
            features_list = []

            for idx, row in df.iterrows():
                # Original features
                amount = row['amount']
                amount_zscore = (amount - df['amount'].mean()) / df['amount'].std() if df['amount'].std() > 0 else 0
                weekday = row['weekday']
                day_of_month = row['day_of_month']

                category_counts = df['category_id'].value_counts()
                category_frequency = category_counts.get(row['category_id'], 0) / len(df)

                category_avg = df[df['category_id'] == row['category_id']]['amount'].mean()
                amount_vs_category_avg = amount / category_avg if category_avg > 0 else 1

                # NEW SEASONAL FEATURES
                # Feature 7: Month (1-12) - seasonal patterns
                month = row['date'].month

                # Feature 8: Quarter (1-4)
                quarter = (month - 1) // 3 + 1

                # Feature 9: Is weekend (0 or 1)
                is_weekend = 1 if weekday >= 5 else 0

                # Feature 10: Near holiday (0 or 1)
                near_holiday = 1 if self._is_near_holiday(row['date']) else 0

                # Feature 11: Season (0-3: winter, spring, summer, fall)
                season = self._get_season(month)

                # Feature 12: Days since similar transaction
                same_category_dates = df[df['category_id'] == row['category_id']]['date']
                if len(same_category_dates) > 1:
                    days_since_similar = (row['date'] - same_category_dates[same_category_dates < row['date']].max()).days if len(same_category_dates[same_category_dates < row['date']]) > 0 else 30
                else:
                    days_since_similar = 30

                features_list.append([
                    amount,
                    amount_zscore,
                    weekday,
                    day_of_month,
                    category_frequency,
                    amount_vs_category_avg,
                    month,
                    quarter,
                    is_weekend,
                    near_holiday,
                    season,
                    min(days_since_similar, 90)  # Cap at 90 days
                ])

            return np.array(features_list)

        except Exception as e:
            print(f"Error extracting features: {e}")
            return None

    def _explain_anomaly(self, transaction: pd.Series, all_transactions: pd.DataFrame) -> str:
        """Generate enhanced human-readable explanation with seasonal context"""
        explanations = []
        amount = transaction['amount']
        trans_date = transaction['date']

        # Check if amount is unusually high
        mean_amount = all_transactions['amount'].mean()
        std_amount = all_transactions['amount'].std()
        z_score = (amount - mean_amount) / std_amount if std_amount > 0 else 0

        if z_score > 2:
            times_higher = amount / mean_amount
            explanations.append(f"Amount is {times_higher:.1f}x higher than your average transaction")

        # Check against category average
        same_category = all_transactions[all_transactions['category_id'] == transaction['category_id']]
        if len(same_category) > 1:
            category_avg = same_category['amount'].mean()
            category_std = same_category['amount'].std()

            if category_std > 0:
                category_z = (amount - category_avg) / category_std
                if category_z > 2:
                    explanations.append(f"Unusually high for '{transaction['category_name']}' category")

        # Check transaction frequency for this amount range
        amount_range = (amount * 0.8, amount * 1.2)
        similar_amounts = all_transactions[
            (all_transactions['amount'] >= amount_range[0]) &
            (all_transactions['amount'] <= amount_range[1])
        ]

        if len(similar_amounts) <= 2:
            explanations.append("Rare transaction amount for you")

        # ENHANCED: Seasonal context
        if self._is_near_holiday(trans_date):
            explanations.append("Near a major holiday (higher spending expected)")

        # ENHANCED: Weekend spending pattern
        if trans_date.weekday() >= 5:
            weekend_avg = all_transactions[all_transactions['weekday'] >= 5]['amount'].mean()
            if weekend_avg > 0 and amount > weekend_avg * 1.5:
                explanations.append("Significantly higher than your typical weekend spending")

        # ENHANCED: Month comparison
        same_month = all_transactions[all_transactions['date'].dt.month == trans_date.month]
        if len(same_month) > 3:
            month_avg = same_month['amount'].mean()
            if amount > month_avg * 1.8:
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                explanations.append(f"Unusually high for {month_names[trans_date.month - 1]}")

        # Check timing patterns
        same_weekday = all_transactions[all_transactions['weekday'] == transaction['weekday']]
        if len(same_weekday) < len(all_transactions) * 0.1:
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            explanations.append(f"Unusual spending on {weekday_names[transaction['weekday']]}")

        if not explanations:
            explanations.append("Multiple factors contribute to this unusual pattern")

        return '; '.join(explanations)

    def _get_severity_level(self, anomaly_score: float) -> str:
        """Determine severity level based on anomaly score"""
        # Isolation Forest scores are typically negative, more negative = more anomalous
        if anomaly_score < -0.5:
            return 'high'
        elif anomaly_score < -0.2:
            return 'medium'
        else:
            return 'low'

    def _generate_anomaly_summary(self, anomalies: pd.DataFrame, all_transactions: pd.DataFrame) -> Dict:
        """Generate summary statistics about detected anomalies"""
        total_anomaly_amount = anomalies['amount'].sum()
        total_all_amount = all_transactions['amount'].sum()

        # Find most common anomaly category
        if len(anomalies) > 0:
            top_anomaly_category = anomalies['category_name'].value_counts().index[0]
            top_category_count = anomalies['category_name'].value_counts().values[0]
        else:
            top_anomaly_category = None
            top_category_count = 0

        return {
            'total_anomaly_amount': round(float(total_anomaly_amount), 2),
            'percentage_of_total': round(float(total_anomaly_amount / total_all_amount * 100), 2) if total_all_amount > 0 else 0,
            'most_common_anomaly_category': top_anomaly_category,
            'anomalies_in_top_category': int(top_category_count),
            'avg_anomaly_amount': round(float(anomalies['amount'].mean()), 2),
            'max_anomaly_amount': round(float(anomalies['amount'].max()), 2)
        }

    def detect_category_anomalies(self, user_id: int, category_id: int) -> Dict:
        """
        Detect anomalies within a specific category

        Args:
            user_id: User ID
            category_id: Category ID to analyze

        Returns:
            Dictionary with category-specific anomalies
        """
        try:
            # Get category
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                return {'success': False, 'message': 'Category not found'}

            # Get transactions for this category (last 90 days)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.category_id == category_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 5:
                return {
                    'success': False,
                    'message': f'Need at least 5 transactions in {category.name} for anomaly detection',
                    'category': category.name
                }

            # Calculate statistics
            amounts = [float(e.amount) for e in entries]
            mean_amount = np.mean(amounts)
            std_amount = np.std(amounts)
            median_amount = np.median(amounts)

            # Detect outliers using IQR method
            q1 = np.percentile(amounts, 25)
            q3 = np.percentile(amounts, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Find anomalies
            anomalies = []
            for entry in entries:
                amount = float(entry.amount)
                if amount < lower_bound or amount > upper_bound:
                    z_score = (amount - mean_amount) / std_amount if std_amount > 0 else 0

                    anomalies.append({
                        'entry_id': entry.id,
                        'date': entry.date.isoformat(),
                        'amount': round(amount, 2),
                        'note': entry.note or '',
                        'z_score': round(float(z_score), 2),
                        'deviation_from_mean': round(float(amount - mean_amount), 2),
                        'explanation': f"Amount is {abs(z_score):.1f} standard deviations from average"
                    })

            return {
                'success': True,
                'category': category.name,
                'anomalies': anomalies,
                'total_transactions': len(entries),
                'anomalies_detected': len(anomalies),
                'statistics': {
                    'mean': round(float(mean_amount), 2),
                    'median': round(float(median_amount), 2),
                    'std_dev': round(float(std_amount), 2),
                    'min': round(float(min(amounts)), 2),
                    'max': round(float(max(amounts)), 2),
                    'iqr_range': {
                        'lower': round(float(lower_bound), 2),
                        'upper': round(float(upper_bound), 2)
                    }
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Category anomaly detection failed: {str(e)}",
                'error': str(e)
            }

    def detect_recurring_anomalies(self, user_id: int) -> Dict:
        """
        Detect recurring transactions that have unusual amounts

        Args:
            user_id: User ID

        Returns:
            Dictionary with recurring anomalies
        """
        try:
            # Get last 6 months of data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=180)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 20:
                return {
                    'success': False,
                    'message': 'Need at least 20 transactions to detect recurring anomalies'
                }

            # Group by note/description to find recurring transactions
            df = pd.DataFrame([{
                'id': e.id,
                'date': e.date,
                'amount': float(e.amount),
                'note': e.note or '',
                'category_name': e.category.name if e.category else 'Uncategorized'
            } for e in entries])

            # Find transactions with same note that appear multiple times
            note_counts = df['note'].value_counts()
            recurring_notes = note_counts[note_counts >= 3].index.tolist()

            if not recurring_notes:
                return {
                    'success': True,
                    'recurring_anomalies': [],
                    'message': 'No recurring transactions with anomalies detected'
                }

            recurring_anomalies = []

            for note in recurring_notes:
                if not note or len(note.strip()) < 3:
                    continue

                transactions = df[df['note'] == note]
                amounts = transactions['amount'].values

                # Check for amount variance
                mean_amount = np.mean(amounts)
                std_amount = np.std(amounts)

                if std_amount > mean_amount * 0.2:  # More than 20% variance
                    # Find which transactions are anomalous
                    anomalous_transactions = []
                    for idx, row in transactions.iterrows():
                        z_score = abs((row['amount'] - mean_amount) / std_amount) if std_amount > 0 else 0
                        if z_score > 1.5:
                            anomalous_transactions.append({
                                'entry_id': int(row['id']),
                                'date': row['date'].isoformat(),
                                'amount': round(float(row['amount']), 2),
                                'expected_amount': round(float(mean_amount), 2),
                                'difference': round(float(row['amount'] - mean_amount), 2)
                            })

                    if anomalous_transactions:
                        recurring_anomalies.append({
                            'recurring_transaction': note,
                            'category': transactions.iloc[0]['category_name'],
                            'typical_amount': round(float(mean_amount), 2),
                            'amount_variance': round(float(std_amount), 2),
                            'occurrences': len(transactions),
                            'anomalous_occurrences': anomalous_transactions
                        })

            return {
                'success': True,
                'recurring_anomalies': recurring_anomalies,
                'total_recurring_patterns_analyzed': len(recurring_notes),
                'patterns_with_anomalies': len(recurring_anomalies)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Recurring anomaly detection failed: {str(e)}",
                'error': str(e)
            }

    def get_anomaly_insights(self, user_id: int) -> Dict:
        """
        Get comprehensive anomaly insights and recommendations

        Args:
            user_id: User ID

        Returns:
            Dictionary with insights and recommendations
        """
        try:
            # Run all anomaly detection methods
            general_anomalies = self.detect_spending_anomalies(user_id, days_back=30)
            recurring_anomalies = self.detect_recurring_anomalies(user_id)

            insights = []
            recommendations = []

            # Analyze general anomalies
            if general_anomalies.get('success') and general_anomalies.get('anomalies'):
                anomaly_count = general_anomalies['anomalies_detected']
                anomaly_amount = general_anomalies['summary']['total_anomaly_amount']

                insights.append(f"Detected {anomaly_count} unusual transactions in the last 30 days")
                insights.append(f"Unusual spending totals {anomaly_amount:.2f}")

                # High severity anomalies
                high_severity = [a for a in general_anomalies['anomalies'] if a['severity'] == 'high']
                if high_severity:
                    recommendations.append(f"Review {len(high_severity)} high-priority unusual transactions")

            # Analyze recurring anomalies
            if recurring_anomalies.get('success') and recurring_anomalies.get('recurring_anomalies'):
                patterns_count = recurring_anomalies['patterns_with_anomalies']
                if patterns_count > 0:
                    insights.append(f"Found {patterns_count} recurring transactions with unusual amounts")
                    recommendations.append("Check if subscription or bill amounts have changed")

            if not insights:
                insights.append("No significant anomalies detected in your spending")
                recommendations.append("Your spending patterns are consistent and predictable")

            return {
                'success': True,
                'insights': insights,
                'recommendations': recommendations,
                'detailed_anomalies': {
                    'general': general_anomalies if general_anomalies.get('success') else {},
                    'recurring': recurring_anomalies if recurring_anomalies.get('success') else {}
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Anomaly insights generation failed: {str(e)}",
                'error': str(e)
            }
