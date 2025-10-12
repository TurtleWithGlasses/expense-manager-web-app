"""Time Series Analysis for Financial Data"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.entry import Entry
from app.models.category import Category


class TimeSeriesAnalyzer:
    """Analyze financial data across different time periods"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_weekly_analysis(self, user_id: int, weeks_back: int = 12) -> Dict:
        """
        Analyze spending patterns by week
        
        Args:
            user_id: User ID
            weeks_back: Number of weeks to analyze
        
        Returns:
            Dictionary with weekly insights
        """
        # Get data for last N weeks
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).all()
        
        if not entries:
            return {'error': 'No data available'}
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': e.date,
            'amount': float(e.amount),
            'type': e.type,
            'category_id': e.category_id,
            'category_name': e.category.name if e.category else 'Uncategorized',
            'weekday': e.date.weekday(),
            'week': e.date.isocalendar()[1]
        } for e in entries])
        
        # Weekly aggregations
        weekly_spending = df[df['type'] == 'expense'].groupby('week').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        
        weekly_income = df[df['type'] == 'income'].groupby('week').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Day of week patterns
        weekday_spending = df[df['type'] == 'expense'].groupby('weekday').agg({
            'amount': ['sum', 'mean', 'count']
        }).to_dict()
        
        return {
            'weekly_spending': weekly_spending.to_dict('records'),
            'weekly_income': weekly_income.to_dict('records'),
            'weekday_patterns': weekday_spending,
            'avg_weekly_spending': weekly_spending[('amount', 'sum')].mean() if not weekly_spending.empty else 0,
            'most_expensive_weekday': int(df[df['type'] == 'expense'].groupby('weekday')['amount'].sum().idxmax()) if len(df[df['type'] == 'expense']) > 0 else 0
        }
    
    def get_monthly_analysis(self, user_id: int, months_back: int = 12) -> Dict:
        """
        Analyze spending patterns by month
        
        Args:
            user_id: User ID
            months_back: Number of months to analyze
        
        Returns:
            Dictionary with monthly insights
        """
        # Get data for last N months
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months_back * 30)
        
        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).all()
        
        if not entries:
            return {'error': 'No data available'}
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': e.date,
            'amount': float(e.amount),
            'type': e.type,
            'category_id': e.category_id,
            'category_name': e.category.name if e.category else 'Uncategorized',
            'year': e.date.year,
            'month': e.date.month,
            'year_month': f"{e.date.year}-{e.date.month:02d}"
        } for e in entries])
        
        # Monthly aggregations
        monthly_spending = df[df['type'] == 'expense'].groupby('year_month').agg({
            'amount': ['sum', 'mean', 'count', 'std']
        }).reset_index()
        
        monthly_income = df[df['type'] == 'income'].groupby('year_month').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Category trends by month
        category_monthly = df[df['type'] == 'expense'].groupby(['year_month', 'category_name'])['amount'].sum().unstack(fill_value=0)
        
        # Calculate month-over-month growth
        if not monthly_spending.empty and len(monthly_spending) > 1:
            spending_values = monthly_spending[('amount', 'sum')].values
            mom_growth = [(spending_values[i] - spending_values[i-1]) / spending_values[i-1] * 100 
                         for i in range(1, len(spending_values)) if spending_values[i-1] > 0]
            avg_mom_growth = np.mean(mom_growth) if mom_growth else 0
        else:
            avg_mom_growth = 0
        
        return {
            'monthly_spending': monthly_spending.to_dict('records'),
            'monthly_income': monthly_income.to_dict('records'),
            'category_trends': category_monthly.to_dict('index'),
            'avg_monthly_spending': monthly_spending[('amount', 'sum')].mean() if not monthly_spending.empty else 0,
            'avg_monthly_income': monthly_income[('amount', 'sum')].mean() if not monthly_income.empty else 0,
            'month_over_month_growth': avg_mom_growth,
            'highest_spending_month': monthly_spending.loc[monthly_spending[('amount', 'sum')].idxmax(), 'year_month'] if not monthly_spending.empty else None
        }
    
    def get_annual_analysis(self, user_id: int, years_back: int = 3) -> Dict:
        """
        Analyze spending patterns by year
        
        Args:
            user_id: User ID
            years_back: Number of years to analyze
        
        Returns:
            Dictionary with annual insights
        """
        # Get data for last N years
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=years_back * 365)
        
        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).all()
        
        if not entries:
            return {'error': 'No data available'}
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': e.date,
            'amount': float(e.amount),
            'type': e.type,
            'category_id': e.category_id,
            'category_name': e.category.name if e.category else 'Uncategorized',
            'year': e.date.year,
            'quarter': (e.date.month - 1) // 3 + 1
        } for e in entries])
        
        # Yearly aggregations
        yearly_spending = df[df['type'] == 'expense'].groupby('year').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        
        yearly_income = df[df['type'] == 'income'].groupby('year').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Quarterly patterns
        quarterly_spending = df[df['type'] == 'expense'].groupby(['year', 'quarter']).agg({
            'amount': ['sum', 'mean']
        }).reset_index()
        
        # Year-over-year growth
        if not yearly_spending.empty and len(yearly_spending) > 1:
            yoy_growth = []
            for i in range(1, len(yearly_spending)):
                prev_year = yearly_spending.iloc[i-1][('amount', 'sum')]
                curr_year = yearly_spending.iloc[i][('amount', 'sum')]
                if prev_year > 0:
                    growth = (curr_year - prev_year) / prev_year * 100
                    yoy_growth.append(growth)
            avg_yoy_growth = np.mean(yoy_growth) if yoy_growth else 0
        else:
            avg_yoy_growth = 0
        
        return {
            'yearly_spending': yearly_spending.to_dict('records'),
            'yearly_income': yearly_income.to_dict('records'),
            'quarterly_spending': quarterly_spending.to_dict('records'),
            'avg_annual_spending': yearly_spending[('amount', 'sum')].mean() if not yearly_spending.empty else 0,
            'avg_annual_income': yearly_income[('amount', 'sum')].mean() if not yearly_income.empty else 0,
            'year_over_year_growth': avg_yoy_growth,
            'total_years_analyzed': len(yearly_spending)
        }
    
    def detect_spending_patterns(self, user_id: int) -> Dict:
        """
        Comprehensive pattern detection across all time scales
        
        Returns:
            Dictionary with detected patterns and recommendations
        """
        patterns = {}
        
        # Get 1 year of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        
        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).all()
        
        if not entries:
            return {'patterns': [], 'insights': []}
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': e.date,
            'amount': float(e.amount),
            'type': e.type,
            'category_name': e.category.name if e.category else 'Uncategorized',
            'weekday': e.date.weekday(),
            'day_of_month': e.date.day
        } for e in entries])
        
        detected_patterns = []
        
        # Pattern 1: Payday spending spike
        if self._detect_payday_spike(df):
            detected_patterns.append({
                'type': 'payday_spike',
                'description': 'Spending increases after income is received',
                'recommendation': 'Consider setting aside savings immediately after payday'
            })
        
        # Pattern 2: Month-end budget exhaustion
        if self._detect_month_end_pattern(df):
            detected_patterns.append({
                'type': 'month_end_fatigue',
                'description': 'Spending decreases at end of month',
                'recommendation': 'Better budget pacing could help avoid month-end constraints'
            })
        
        # Pattern 3: Weekend overspending
        weekend_avg = df[(df['weekday'] >= 5) & (df['type'] == 'expense')]['amount'].mean()
        weekday_avg = df[(df['weekday'] < 5) & (df['type'] == 'expense')]['amount'].mean()
        
        if weekend_avg > weekday_avg * 1.5:
            detected_patterns.append({
                'type': 'weekend_overspending',
                'description': f'Weekend spending is {((weekend_avg/weekday_avg - 1) * 100):.0f}% higher than weekdays',
                'recommendation': 'Set weekend spending limits to control costs'
            })
        
        return {
            'patterns': detected_patterns,
            'total_patterns_found': len(detected_patterns)
        }
    
    def _detect_payday_spike(self, df: pd.DataFrame) -> bool:
        """Detect if spending spikes after income"""
        # This is a simplified version - would need more sophisticated analysis
        return False
    
    def _detect_month_end_pattern(self, df: pd.DataFrame) -> bool:
        """Detect month-end spending patterns"""
        start_month_spending = df[(df['day_of_month'] <= 10) & (df['type'] == 'expense')]['amount'].sum()
        end_month_spending = df[(df['day_of_month'] >= 21) & (df['type'] == 'expense')]['amount'].sum()
        
        return end_month_spending < start_month_spending * 0.6

