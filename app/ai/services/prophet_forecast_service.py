"""
Prophet-based Time Series Forecasting Service

Advanced forecasting using Facebook Prophet for:
- Seasonal pattern detection (weekly, monthly, yearly)
- Holiday effects
- Trend analysis
- Multi-horizon forecasting with uncertainty intervals
- Category-specific predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import warnings
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️  Prophet not installed. Install with: pip install prophet")

from app.models.entry import Entry
from app.models.category import Category


class ProphetForecastService:
    """
    Advanced time series forecasting using Facebook Prophet

    Features:
    - Automatic seasonality detection
    - Holiday effects
    - Trend changepoints
    - Multi-step ahead forecasting
    - Uncertainty intervals (confidence bands)
    """

    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.is_trained = False

        if not PROPHET_AVAILABLE:
            raise ImportError(
                "Prophet is not installed. "
                "Install it with: pip install prophet"
            )

    def forecast_total_spending(
        self,
        user_id: int,
        days_ahead: int = 90,
        include_history: bool = True
    ) -> Dict:
        """
        Forecast total spending for the next N days

        Args:
            user_id: User ID
            days_ahead: Number of days to forecast (default 90)
            include_history: Include historical data in response

        Returns:
            Dictionary with forecast data, trends, and insights
        """
        try:
            # Get historical data (minimum 60 days for reliable forecasting)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=180)  # 6 months history

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 30:
                return {
                    'success': False,
                    'message': 'Need at least 30 days of data for Prophet forecasting',
                    'min_days_needed': 30,
                    'current_days': len(set(e.date for e in entries))
                }

            # Prepare data in Prophet format (ds, y)
            df = pd.DataFrame([{
                'ds': e.date,
                'y': float(e.amount)
            } for e in entries])

            # Aggregate by day
            daily_spending = df.groupby('ds')['y'].sum().reset_index()

            # Fill missing dates with 0 spending
            date_range = pd.date_range(start=start_date, end=end_date)
            daily_spending = daily_spending.set_index('ds').reindex(
                date_range,
                fill_value=0
            ).reset_index()
            daily_spending.columns = ['ds', 'y']

            if len(daily_spending) < 14:
                return {
                    'success': False,
                    'message': 'Need at least 14 days of historical data'
                }

            # Initialize and train Prophet model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True if len(daily_spending) >= 365 else False,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05,  # Flexibility of trend
                interval_width=0.95  # 95% confidence intervals
            )

            # Add monthly seasonality
            model.add_seasonality(
                name='monthly',
                period=30.5,
                fourier_order=5
            )

            print(f"Training Prophet model on {len(daily_spending)} days of data...")
            model.fit(daily_spending)
            self.model = model
            self.is_trained = True

            # Create future dataframe
            future = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future)

            # Extract forecast results
            forecast_results = forecast.tail(days_ahead)

            # Calculate summary statistics
            total_predicted = forecast_results['yhat'].sum()
            avg_daily = forecast_results['yhat'].mean()

            # Identify trend
            trend_start = forecast_results['trend'].iloc[0]
            trend_end = forecast_results['trend'].iloc[-1]
            trend_change = ((trend_end - trend_start) / trend_start * 100) if trend_start > 0 else 0

            # Prepare forecast data for visualization
            forecast_data = []
            for idx, row in forecast_results.iterrows():
                forecast_data.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted': round(float(row['yhat']), 2),
                    'lower_bound': round(float(row['yhat_lower']), 2),
                    'upper_bound': round(float(row['yhat_upper']), 2),
                    'trend': round(float(row['trend']), 2)
                })

            # Historical data (if requested)
            historical_data = []
            if include_history:
                for idx, row in daily_spending.tail(30).iterrows():  # Last 30 days
                    historical_data.append({
                        'date': row['ds'].strftime('%Y-%m-%d'),
                        'actual': round(float(row['y']), 2)
                    })

            # Detect significant patterns
            insights = self._generate_forecast_insights(
                forecast_results,
                daily_spending,
                days_ahead
            )

            return {
                'success': True,
                'forecast': forecast_data,
                'historical': historical_data,
                'summary': {
                    'total_predicted': round(float(total_predicted), 2),
                    'avg_daily_spending': round(float(avg_daily), 2),
                    'forecast_period_days': days_ahead,
                    'trend_direction': 'increasing' if trend_change > 2 else 'decreasing' if trend_change < -2 else 'stable',
                    'trend_change_percent': round(float(trend_change), 2),
                    'confidence_level': '95%'
                },
                'insights': insights,
                'model_info': {
                    'training_days': len(daily_spending),
                    'model_type': 'Facebook Prophet',
                    'seasonalities': ['weekly', 'monthly', 'yearly'] if len(daily_spending) >= 365 else ['weekly', 'monthly']
                }
            }

        except Exception as e:
            print(f"Error in Prophet forecasting: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Forecasting failed: {str(e)}",
                'error': str(e)
            }

    def forecast_by_category(
        self,
        user_id: int,
        category_id: int,
        months_ahead: int = 3
    ) -> Dict:
        """
        Forecast spending for a specific category

        Args:
            user_id: User ID
            category_id: Category ID
            months_ahead: Number of months to forecast

        Returns:
            Dictionary with category-specific forecast
        """
        try:
            # Get category info
            category = self.db.query(Category).filter(
                Category.id == category_id
            ).first()

            if not category:
                return {
                    'success': False,
                    'message': 'Category not found'
                }

            # Get historical data (6 months minimum)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=180)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.category_id == category_id,
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 20:
                return {
                    'success': False,
                    'message': f'Need at least 20 transactions in {category.name} for forecasting',
                    'category': category.name
                }

            # Prepare data
            df = pd.DataFrame([{
                'ds': e.date,
                'y': float(e.amount)
            } for e in entries])

            # Aggregate by week (more stable for categories)
            df['week'] = pd.to_datetime(df['ds']).dt.to_period('W').apply(lambda r: r.start_time)
            weekly_spending = df.groupby('week')['y'].sum().reset_index()
            weekly_spending.columns = ['ds', 'y']

            if len(weekly_spending) < 8:
                return {
                    'success': False,
                    'message': f'Need at least 8 weeks of data for {category.name}'
                }

            # Train Prophet model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=False,
                yearly_seasonality=False,
                changepoint_prior_scale=0.1,
                interval_width=0.80  # 80% confidence for category-level
            )

            model.fit(weekly_spending)

            # Forecast
            periods = int(months_ahead * 4.33)  # weeks
            future = model.make_future_dataframe(periods=periods, freq='W')
            forecast = model.predict(future)

            # Extract results
            forecast_results = forecast.tail(periods)

            # Calculate monthly totals from weekly forecasts
            monthly_forecasts = []
            current_month_start = datetime.now().replace(day=1).date()

            for i in range(months_ahead):
                month_date = current_month_start + timedelta(days=30 * (i + 1))
                month_name = month_date.strftime('%B %Y')

                # Get weeks in this month
                month_data = forecast_results[
                    (pd.to_datetime(forecast_results['ds']).dt.month == month_date.month) &
                    (pd.to_datetime(forecast_results['ds']).dt.year == month_date.year)
                ]

                if len(month_data) > 0:
                    monthly_total = month_data['yhat'].sum()
                    monthly_lower = month_data['yhat_lower'].sum()
                    monthly_upper = month_data['yhat_upper'].sum()

                    monthly_forecasts.append({
                        'month': month_name,
                        'predicted_total': round(float(monthly_total), 2),
                        'lower_bound': round(float(max(0, monthly_lower)), 2),
                        'upper_bound': round(float(monthly_upper), 2)
                    })

            # Historical average
            historical_avg = weekly_spending['y'].mean() * 4.33  # Convert to monthly

            return {
                'success': True,
                'category': category.name,
                'category_id': category_id,
                'monthly_forecasts': monthly_forecasts,
                'historical_monthly_avg': round(float(historical_avg), 2),
                'weeks_analyzed': len(weekly_spending),
                'confidence_level': '80%'
            }

        except Exception as e:
            print(f"Error in category forecasting: {e}")
            return {
                'success': False,
                'message': f"Category forecasting failed: {str(e)}",
                'error': str(e)
            }

    def detect_seasonal_patterns(self, user_id: int) -> Dict:
        """
        Detect and analyze seasonal spending patterns

        Args:
            user_id: User ID

        Returns:
            Dictionary with seasonal insights
        """
        try:
            # Get 1 year of data for seasonal analysis
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)

            entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).all()

            if len(entries) < 90:
                return {
                    'success': False,
                    'message': 'Need at least 90 days of data for seasonal analysis'
                }

            # Prepare data
            df = pd.DataFrame([{
                'ds': e.date,
                'y': float(e.amount)
            } for e in entries])

            daily_spending = df.groupby('ds')['y'].sum().reset_index()

            # Train model with seasonal components
            model = Prophet(
                weekly_seasonality=True,
                yearly_seasonality=True if len(daily_spending) >= 180 else False,
                seasonality_mode='multiplicative'
            )

            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            model.fit(daily_spending)

            # Extract seasonal components
            future = model.make_future_dataframe(periods=0)
            forecast = model.predict(future)

            # Analyze patterns
            patterns = {
                'weekly': self._analyze_weekly_pattern(forecast),
                'monthly': self._analyze_monthly_pattern(forecast),
            }

            if 'yearly' in forecast.columns:
                patterns['yearly'] = self._analyze_yearly_pattern(forecast)

            return {
                'success': True,
                'patterns': patterns,
                'insights': self._generate_seasonal_insights(patterns)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Seasonal analysis failed: {str(e)}",
                'error': str(e)
            }

    def _generate_forecast_insights(
        self,
        forecast: pd.DataFrame,
        historical: pd.DataFrame,
        days_ahead: int
    ) -> List[str]:
        """Generate human-readable insights from forecast"""
        insights = []

        # Compare forecast to historical average
        historical_avg = historical['y'].mean()
        forecast_avg = forecast['yhat'].mean()

        difference_pct = ((forecast_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

        if abs(difference_pct) > 10:
            direction = "higher" if difference_pct > 0 else "lower"
            insights.append(
                f"Predicted spending is {abs(difference_pct):.1f}% {direction} "
                f"than your historical average"
            )

        # Check for trend
        trend_start = forecast['trend'].iloc[0]
        trend_end = forecast['trend'].iloc[-1]
        trend_change = ((trend_end - trend_start) / trend_start * 100) if trend_start > 0 else 0

        if abs(trend_change) > 5:
            if trend_change > 0:
                insights.append(
                    f"Your spending shows an upward trend of {trend_change:.1f}% "
                    f"over the next {days_ahead} days"
                )
            else:
                insights.append(
                    f"Your spending shows a downward trend of {abs(trend_change):.1f}% "
                    f"over the next {days_ahead} days"
                )

        # Check uncertainty
        avg_uncertainty = (forecast['yhat_upper'] - forecast['yhat_lower']).mean()
        if avg_uncertainty > forecast_avg:
            insights.append(
                "High variability detected in your spending patterns - "
                "predictions have wider uncertainty ranges"
            )

        return insights

    def _analyze_weekly_pattern(self, forecast: pd.DataFrame) -> Dict:
        """Analyze weekly spending patterns"""
        if 'weekly' in forecast.columns:
            weekly_component = forecast['weekly'].mean()
            return {
                'detected': True,
                'strength': 'strong' if abs(weekly_component) > 10 else 'moderate' if abs(weekly_component) > 5 else 'weak',
                'description': 'Weekly spending patterns detected'
            }
        return {'detected': False}

    def _analyze_monthly_pattern(self, forecast: pd.DataFrame) -> Dict:
        """Analyze monthly spending patterns"""
        if 'monthly' in forecast.columns:
            monthly_component = forecast['monthly'].mean()
            return {
                'detected': True,
                'strength': 'strong' if abs(monthly_component) > 15 else 'moderate' if abs(monthly_component) > 8 else 'weak',
                'description': 'Monthly spending patterns detected (e.g., payday cycles)'
            }
        return {'detected': False}

    def _analyze_yearly_pattern(self, forecast: pd.DataFrame) -> Dict:
        """Analyze yearly/seasonal spending patterns"""
        if 'yearly' in forecast.columns:
            yearly_component = forecast['yearly'].mean()
            return {
                'detected': True,
                'strength': 'strong' if abs(yearly_component) > 20 else 'moderate' if abs(yearly_component) > 10 else 'weak',
                'description': 'Seasonal patterns detected (e.g., holiday spending)'
            }
        return {'detected': False}

    def _generate_seasonal_insights(self, patterns: Dict) -> List[str]:
        """Generate insights from seasonal patterns"""
        insights = []

        for pattern_type, pattern_data in patterns.items():
            if pattern_data.get('detected'):
                strength = pattern_data.get('strength', 'unknown')
                if strength in ['strong', 'moderate']:
                    insights.append(
                        f"{pattern_type.capitalize()} {strength} {pattern_data['description']}"
                    )

        if not insights:
            insights.append("No significant seasonal patterns detected in your spending")

        return insights

    def get_model_diagnostics(self) -> Dict:
        """
        Get diagnostic information about the trained model

        Returns:
            Dictionary with model diagnostics
        """
        if not self.is_trained or not self.model:
            return {
                'is_trained': False,
                'message': 'Model not trained yet'
            }

        return {
            'is_trained': True,
            'changepoints': len(self.model.changepoints),
            'seasonalities': list(self.model.seasonalities.keys()),
            'interval_width': self.model.interval_width,
            'model_type': 'Facebook Prophet'
        }
