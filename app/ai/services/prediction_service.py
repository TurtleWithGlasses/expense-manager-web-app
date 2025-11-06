"""Predictive Analytics Service for Budget Forecasting"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from app.models.entry import Entry
from app.models.category import Category


class PredictionService:
    """Service for predicting future spending and income patterns"""

    def __init__(self, db: Session):
        self.db = db
        self.spending_model = LinearRegression()
        self.income_model = LinearRegression()
        self.scaler = StandardScaler()

    def predict_next_month_spending(self, user_id: int) -> Dict:
        """
        Predict total spending for the next month

        Args:
            user_id: User ID

        Returns:
            Dictionary with prediction details
        """
        try:
            # Get historical data (last 6 months minimum)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=180)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 10:
                return {
                    'success': False,
                    'message': 'Not enough historical data for prediction. Need at least 10 expense entries.',
                    'min_entries_needed': 10,
                    'current_entries': len(entries)
                }

            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': e.date,
                'amount': float(e.amount),
                'year': e.date.year,
                'month': e.date.month,
                'year_month': f"{e.date.year}-{e.date.month:02d}"
            } for e in entries])

            # Aggregate by month
            monthly_spending = df.groupby('year_month')['amount'].sum().reset_index()
            monthly_spending.columns = ['year_month', 'total_spending']

            if len(monthly_spending) < 3:
                return {
                    'success': False,
                    'message': 'Need at least 3 months of data for reliable prediction.',
                    'months_available': len(monthly_spending)
                }

            # Prepare features for prediction
            monthly_spending['month_index'] = range(len(monthly_spending))
            X = monthly_spending[['month_index']].values
            y = monthly_spending['total_spending'].values

            # Train model
            self.spending_model.fit(X, y)

            # Predict next month
            next_month_index = len(monthly_spending)
            predicted_amount = self.spending_model.predict([[next_month_index]])[0]

            # Calculate confidence interval (simple approach using std)
            std_dev = np.std(y)
            confidence_interval = {
                'lower': max(0, predicted_amount - 1.96 * std_dev),
                'upper': predicted_amount + 1.96 * std_dev
            }

            # Calculate trend
            trend_percentage = ((y[-1] - y[0]) / y[0] * 100) if y[0] > 0 else 0

            # Get next month info
            next_month_date = datetime.now().date() + timedelta(days=30)
            next_month_name = next_month_date.strftime('%B %Y')

            return {
                'success': True,
                'prediction': {
                    'amount': round(float(predicted_amount), 2),
                    'month': next_month_name,
                    'confidence_interval': {
                        'lower': round(float(confidence_interval['lower']), 2),
                        'upper': round(float(confidence_interval['upper']), 2)
                    },
                    'confidence_level': '95%'
                },
                'historical_data': {
                    'months_analyzed': len(monthly_spending),
                    'avg_monthly_spending': round(float(np.mean(y)), 2),
                    'trend': 'increasing' if trend_percentage > 5 else 'decreasing' if trend_percentage < -5 else 'stable',
                    'trend_percentage': round(float(trend_percentage), 2)
                },
                'model_info': {
                    'r_squared': round(float(self.spending_model.score(X, y)), 3),
                    'intercept': round(float(self.spending_model.intercept_), 2),
                    'slope': round(float(self.spending_model.coef_[0]), 2)
                }
            }

        except Exception as e:
            print(f"Error in spending prediction: {e}")
            return {
                'success': False,
                'message': f"Prediction failed: {str(e)}",
                'error': str(e)
            }

    def predict_category_spending(self, user_id: int, category_id: int, days_ahead: int = 30) -> Dict:
        """
        Predict spending for a specific category

        Args:
            user_id: User ID
            category_id: Category ID
            days_ahead: Number of days to predict ahead

        Returns:
            Dictionary with category-specific prediction
        """
        try:
            # Get category info
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                return {'success': False, 'message': 'Category not found'}

            # Get historical data (last 3 months)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.category_id == category_id,
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 5:
                return {
                    'success': False,
                    'message': f'Not enough data for {category.name}. Need at least 5 transactions.',
                    'category': category.name
                }

            # Calculate simple statistics
            amounts = [float(e.amount) for e in entries]
            avg_amount = np.mean(amounts)
            std_amount = np.std(amounts)

            # Calculate transaction frequency
            days_in_period = (end_date - start_date).days
            transactions_per_day = len(entries) / days_in_period

            # Predict number of transactions in next period
            predicted_transactions = int(transactions_per_day * days_ahead)

            # Predict total spending
            predicted_amount = predicted_transactions * avg_amount

            return {
                'success': True,
                'category': category.name,
                'prediction': {
                    'total_amount': round(float(predicted_amount), 2),
                    'predicted_transactions': predicted_transactions,
                    'avg_transaction_amount': round(float(avg_amount), 2),
                    'period_days': days_ahead
                },
                'historical_data': {
                    'total_transactions': len(entries),
                    'avg_amount': round(float(avg_amount), 2),
                    'std_amount': round(float(std_amount), 2),
                    'transaction_frequency': f"{round(transactions_per_day * 7, 2)} per week"
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Category prediction failed: {str(e)}",
                'error': str(e)
            }

    def predict_cash_flow(self, user_id: int, months_ahead: int = 3) -> Dict:
        """
        Predict cash flow (income - expenses) for upcoming months

        Args:
            user_id: User ID
            months_ahead: Number of months to forecast

        Returns:
            Dictionary with cash flow predictions
        """
        try:
            # Get historical data (last 6 months)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=180)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 10:
                return {
                    'success': False,
                    'message': 'Need at least 10 entries for cash flow prediction'
                }

            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': e.date,
                'amount': float(e.amount),
                'type': e.type,
                'year_month': f"{e.date.year}-{e.date.month:02d}"
            } for e in entries])

            # Separate income and expenses
            income_df = df[df['type'] == 'income'].groupby('year_month')['amount'].sum()
            expense_df = df[df['type'] == 'expense'].groupby('year_month')['amount'].sum()

            # Calculate average monthly income and expenses
            avg_income = income_df.mean() if len(income_df) > 0 else 0
            avg_expense = expense_df.mean() if len(expense_df) > 0 else 0

            # Generate predictions for next N months
            predictions = []
            current_date = datetime.now().date()

            for i in range(1, months_ahead + 1):
                future_date = current_date + timedelta(days=30 * i)
                month_name = future_date.strftime('%B %Y')

                # Simple prediction using historical averages
                # In production, this could be more sophisticated
                predicted_income = avg_income
                predicted_expense = avg_expense
                predicted_net = predicted_income - predicted_expense

                predictions.append({
                    'month': month_name,
                    'predicted_income': round(float(predicted_income), 2),
                    'predicted_expense': round(float(predicted_expense), 2),
                    'predicted_net': round(float(predicted_net), 2),
                    'status': 'surplus' if predicted_net > 0 else 'deficit'
                })

            # Calculate historical cash flow
            historical_months = list(set(df['year_month']))
            historical_cash_flow = []

            for month in sorted(historical_months):
                month_income = income_df.get(month, 0)
                month_expense = expense_df.get(month, 0)

                historical_cash_flow.append({
                    'month': month,
                    'income': round(float(month_income), 2),
                    'expense': round(float(month_expense), 2),
                    'net': round(float(month_income - month_expense), 2)
                })

            return {
                'success': True,
                'predictions': predictions,
                'historical_cash_flow': historical_cash_flow[-3:],  # Last 3 months
                'summary': {
                    'avg_monthly_income': round(float(avg_income), 2),
                    'avg_monthly_expense': round(float(avg_expense), 2),
                    'avg_monthly_net': round(float(avg_income - avg_expense), 2)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Cash flow prediction failed: {str(e)}",
                'error': str(e)
            }

    def predict_budget_status(self, user_id: int) -> Dict:
        """
        Predict if user will stay within budget for current month

        Args:
            user_id: User ID

        Returns:
            Dictionary with budget forecast
        """
        try:
            # Get current month data
            now = datetime.now()
            month_start = now.replace(day=1).date()
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            today = now.date()

            # Get spending so far this month
            current_month_entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= month_start,
                Entry.date <= today
            ).all()

            if not current_month_entries:
                return {
                    'success': False,
                    'message': 'No spending data for current month'
                }

            # Calculate current spending
            current_spending = sum(float(e.amount) for e in current_month_entries)

            # Calculate daily average so far
            days_elapsed = (today - month_start).days + 1
            daily_avg = current_spending / days_elapsed if days_elapsed > 0 else 0

            # Calculate remaining days in month
            days_remaining = (month_end - today).days

            # Predict end-of-month total
            predicted_month_total = current_spending + (daily_avg * days_remaining)

            # Get previous month's spending for comparison
            prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
            prev_month_end = month_start - timedelta(days=1)

            prev_month_entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= prev_month_start,
                Entry.date <= prev_month_end
            ).all()

            prev_month_total = sum(float(e.amount) for e in prev_month_entries) if prev_month_entries else predicted_month_total

            # Calculate if on track
            expected_spending_by_now = prev_month_total * (days_elapsed / ((month_end - month_start).days + 1))
            spending_variance = current_spending - expected_spending_by_now
            spending_variance_percentage = (spending_variance / expected_spending_by_now * 100) if expected_spending_by_now > 0 else 0

            status = 'over_budget' if spending_variance_percentage > 10 else 'on_track' if abs(spending_variance_percentage) <= 10 else 'under_budget'

            return {
                'success': True,
                'current_month': now.strftime('%B %Y'),
                'current_spending': round(float(current_spending), 2),
                'predicted_month_total': round(float(predicted_month_total), 2),
                'previous_month_total': round(float(prev_month_total), 2),
                'status': status,
                'variance': {
                    'amount': round(float(spending_variance), 2),
                    'percentage': round(float(spending_variance_percentage), 2)
                },
                'daily_average': round(float(daily_avg), 2),
                'days_elapsed': days_elapsed,
                'days_remaining': days_remaining,
                'recommendation': self._get_budget_recommendation(status, spending_variance_percentage)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Budget prediction failed: {str(e)}",
                'error': str(e)
            }

    def _get_budget_recommendation(self, status: str, variance_percentage: float) -> str:
        """Generate budget recommendation based on status"""
        if status == 'over_budget':
            if variance_percentage > 30:
                return "You're significantly over your typical spending. Consider reducing discretionary expenses immediately."
            elif variance_percentage > 20:
                return "You're notably above your usual spending pace. Try to limit non-essential purchases."
            else:
                return "You're slightly over your typical spending. Monitor expenses carefully for the rest of the month."
        elif status == 'under_budget':
            return "You're doing well! Your spending is below average. Keep up the good financial discipline."
        else:
            return "You're on track with your typical spending pattern. Continue monitoring to stay on course."

    def get_spending_forecast_data(self, user_id: int, months_back: int = 6, months_ahead: int = 3) -> Dict:
        """
        Get comprehensive forecast data for visualization

        Args:
            user_id: User ID
            months_back: Historical months to include
            months_ahead: Future months to forecast

        Returns:
            Dictionary with historical and predicted data for charts
        """
        try:
            # Get historical data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=months_back * 30)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 5:
                return {
                    'success': False,
                    'message': 'Not enough historical data for visualization'
                }

            # Convert to DataFrame and aggregate by month
            df = pd.DataFrame([{
                'date': e.date,
                'amount': float(e.amount),
                'year_month': f"{e.date.year}-{e.date.month:02d}"
            } for e in entries])

            monthly_spending = df.groupby('year_month')['amount'].sum().reset_index()
            monthly_spending.columns = ['month', 'actual']

            # Train model for predictions
            monthly_spending['month_index'] = range(len(monthly_spending))
            X = monthly_spending[['month_index']].values
            y = monthly_spending['actual'].values

            self.spending_model.fit(X, y)

            # Generate predictions
            std_dev = np.std(y)
            predictions = []

            for i in range(1, months_ahead + 1):
                next_index = len(monthly_spending) + i - 1
                predicted_amount = self.spending_model.predict([[next_index]])[0]

                future_date = datetime.now().date() + timedelta(days=30 * i)
                month_str = f"{future_date.year}-{future_date.month:02d}"

                predictions.append({
                    'month': month_str,
                    'predicted': round(float(predicted_amount), 2),
                    'lower_bound': round(float(max(0, predicted_amount - 1.96 * std_dev)), 2),
                    'upper_bound': round(float(predicted_amount + 1.96 * std_dev), 2)
                })

            return {
                'success': True,
                'historical': monthly_spending[['month', 'actual']].to_dict('records'),
                'predictions': predictions,
                'model_accuracy': round(float(self.spending_model.score(X, y)), 3)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Forecast data generation failed: {str(e)}",
                'error': str(e)
            }
