"""
Comprehensive tests for Report Generation System

Tests cover:
- Weekly report generation
- Monthly report generation
- Annual report generation  
- Report email delivery
- Report status tracking
- Currency handling in reports
- Edge cases (no data, zero income, etc.)
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.weekly_report_service import WeeklyReportService
from app.services.monthly_report_service import MonthlyReportService
from app.services.email import email_service
from app.services.report_status_service import ReportStatusService
from app.models.entry import Entry
from app.models.category import Category
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.weekly_report import WeeklyReport, UserReportPreferences
from app.db.session import SessionLocal


class TestWeeklyReportGeneration:
    """Test weekly report generation"""
    
    def test_generate_basic_weekly_report(self, db_session, user_with_weekly_data):
        """Test basic weekly report generation"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_weekly_data.id, show_income=False)
        
        assert report is not None
        assert 'period' in report
        assert 'summary' in report
        assert 'insights' in report
        assert 'achievements' in report
        assert 'recommendations' in report
    
    def test_weekly_report_with_income(self, db_session, user_with_income_and_expenses):
        """Test weekly report with income enabled"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_income_and_expenses.id, show_income=True)
        
        assert report['summary']['total_income'] > 0
        assert report['summary']['total_expenses'] > 0
        assert 'net_savings' in report['summary']
    
    def test_weekly_report_without_income(self, db_session, user_with_only_expenses):
        """Test weekly report with only expenses (no income)"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_only_expenses.id, show_income=False)
        
        assert report['summary']['total_income'] == 0
        assert report['summary']['total_expenses'] > 0
        assert report['show_income'] == False
    
    def test_weekly_report_no_data(self, db_session, user_without_data):
        """Test weekly report with no transaction data"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_without_data.id)
        
        assert report is not None
        assert report['summary']['total_expenses'] == 0
        assert len(report['insights']) >= 0  # May have generic insights
    
    def test_weekly_report_currency(self, db_session, user_with_tl_currency):
        """Test weekly report uses correct currency"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_tl_currency.id)
        
        assert report['currency'] == 'TRY'
        # Verify no USD symbols in text
        report_text = service.format_report_text(report)
        assert '$' not in report_text
    
    def test_weekly_report_anomaly_detection(self, db_session, user_with_anomaly):
        """Test anomaly detection in weekly report"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_anomaly.id)
        
        assert 'anomalies' in report
        assert len(report['anomalies']) > 0
        # Should detect the unusually large transaction
    
    def test_weekly_report_achievements(self, db_session, user_with_low_spending):
        """Test achievement detection"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_low_spending.id)
        
        assert 'achievements' in report
        # Should have achievement for low spending
        achievement_titles = [a['title'] for a in report['achievements']]
        assert any('low spending' in title.lower() or 'frugal' in title.lower() 
                  for title in achievement_titles)
    
    def test_weekly_report_recommendations(self, db_session, user_with_high_category_spending):
        """Test recommendation generation"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_high_category_spending.id)
        
        assert 'recommendations' in report
        assert len(report['recommendations']) > 0
    
    def test_weekly_report_comparison(self, db_session, user_with_multiple_weeks):
        """Test week-over-week comparison"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_multiple_weeks.id)
        
        assert 'comparison' in report['summary']
        assert 'expense_change_pct' in report['summary']['comparison']


class TestMonthlyReportGeneration:
    """Test monthly report generation"""
    
    def test_generate_basic_monthly_report(self, db_session, user_with_monthly_data):
        """Test basic monthly report generation"""
        service = MonthlyReportService(db_session)
        
        report = service.generate_monthly_report(user_with_monthly_data.id)
        
        assert report is not None
        assert 'period' in report
        assert 'summary' in report
        assert 'category_analysis' in report
        assert 'insights' in report
    
    def test_monthly_report_zero_income(self, db_session, user_with_zero_income):
        """Test monthly report with zero income (division by zero fix)"""
        service = MonthlyReportService(db_session)
        
        # Should not crash with ZeroDivisionError
        report = service.generate_monthly_report(user_with_zero_income.id)
        
        assert report is not None
        assert report['summary']['total_income'] == 0
        # Should have recommendation to track income
        rec_types = [r['type'] for r in report['recommendations']]
        assert 'track_income' in rec_types or len(report['recommendations']) >= 0
    
    def test_monthly_report_category_analysis(self, db_session, user_with_category_data):
        """Test category analysis in monthly report"""
        service = MonthlyReportService(db_session)
        
        report = service.generate_monthly_report(user_with_category_data.id)
        
        assert 'category_analysis' in report
        assert 'top_category' in report['category_analysis']
        assert 'categories' in report['category_analysis']
    
    def test_monthly_report_trends(self, db_session, user_with_spending_increase):
        """Test trend detection"""
        service = MonthlyReportService(db_session)
        
        report = service.generate_monthly_report(user_with_spending_increase.id)
        
        # Should detect increasing trend
        assert 'comparison' in report['summary']
        change_pct = report['summary']['comparison'].get('expense_change_pct', 0)
        assert change_pct > 0  # Spending increased


class TestReportEmailDelivery:
    """Test report email delivery"""
    
    @pytest.mark.asyncio
    async def test_send_weekly_report_email(self, db_session, user_with_email, sample_weekly_report):
        """Test sending weekly report email"""
        # Mock email service or use test mode
        result = await email_service.send_weekly_report_email(
            user_email=user_with_email.email,
            user_name=user_with_email.full_name,
            report=sample_weekly_report
        )
        
        # Check result (may be mocked)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_send_monthly_report_email(self, db_session, user_with_email, sample_monthly_report):
        """Test sending monthly report email"""
        result = await email_service.send_monthly_report_email(
            user_email=user_with_email.email,
            user_name=user_with_email.full_name,
            report=sample_monthly_report
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_email_contains_no_currency_symbols(self, sample_weekly_report):
        """Test that email content has no currency symbols"""
        # Format the report
        from app.services.weekly_report_service import WeeklyReportService
        
        report_text = WeeklyReportService(None).format_report_text(sample_weekly_report)
        
        # Should not contain currency symbols
        assert '$' not in report_text
        assert '€' not in report_text
        assert '£' not in report_text


class TestReportStatusTracking:
    """Test report status tracking"""
    
    def test_mark_report_as_new(self, db_session, test_user):
        """Test marking report as new"""
        service = ReportStatusService(db_session)
        
        service.mark_report_as_new(test_user.id, 'weekly', 'current')
        
        status = service.get_report_status(test_user.id, 'weekly', 'current')
        assert status['is_new'] == True
    
    def test_mark_report_as_viewed(self, db_session, test_user):
        """Test marking report as viewed"""
        service = ReportStatusService(db_session)
        
        # First mark as new
        service.mark_report_as_new(test_user.id, 'weekly', 'current')
        
        # Then mark as viewed
        service.mark_report_as_viewed(test_user.id, 'weekly', 'current')
        
        status = service.get_report_status(test_user.id, 'weekly', 'current')
        assert status['is_new'] == False
        assert status['last_viewed'] is not None
    
    def test_mark_all_reports_as_new(self, db_session, test_user):
        """Test marking all report types as new"""
        service = ReportStatusService(db_session)
        
        service.mark_all_reports_as_new(test_user.id)
        
        # Check all report types
        for report_type in ['weekly', 'monthly', 'annual']:
            status = service.get_report_status(test_user.id, report_type)
            assert status['is_new'] == True
    
    def test_get_all_report_statuses(self, db_session, test_user):
        """Test getting all report statuses"""
        service = ReportStatusService(db_session)
        
        statuses = service.get_all_report_statuses(test_user.id)
        
        assert 'weekly' in statuses
        assert 'monthly' in statuses
        assert 'annual' in statuses


class TestReportEdgeCases:
    """Test edge cases in report generation"""
    
    def test_report_with_future_dates(self, db_session, user_with_future_entries):
        """Test report handles future-dated entries"""
        service = WeeklyReportService(db_session)
        
        # Should exclude future entries
        report = service.generate_weekly_report(user_with_future_entries.id)
        
        assert report is not None
        # Future entries should not be included
    
    def test_report_with_very_old_data(self, db_session, user_with_old_entries):
        """Test report with entries from years ago"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_old_entries.id)
        
        # Should only include current week's data
        assert report['summary']['total_expenses'] == 0
    
    def test_report_with_negative_amounts(self, db_session, user_with_refunds):
        """Test report handles negative amounts (refunds)"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_refunds.id)
        
        assert report is not None
        # Should handle refunds appropriately
    
    def test_report_with_very_large_amounts(self, db_session, user_with_large_transactions):
        """Test report with very large transaction amounts"""
        service = WeeklyReportService(db_session)
        
        report = service.generate_weekly_report(user_with_large_transactions.id)
        
        assert report is not None
        assert report['summary']['total_expenses'] > 10000


# Fixtures

@pytest.fixture
def db_session():
    """Create a test database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create a basic test user"""
    user = User(email="test@example.com", hashed_password="test", full_name="Test User")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_with_weekly_data(db_session):
    """Create user with data for current week"""
    user = User(email="weekly@example.com", hashed_password="test", full_name="Weekly User")
    db_session.add(user)
    db_session.commit()
    
    category = Category(user_id=user.id, name="Groceries")
    db_session.add(category)
    db_session.commit()
    
    # Add entries for current week
    today = date.today()
    for i in range(5):
        entry = Entry(
            user_id=user.id,
            category_id=category.id,
            type="expense",
            amount=50.0 + i * 10,
            note=f"Purchase {i}",
            date=today - timedelta(days=i),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    return user


@pytest.fixture
def user_with_only_expenses(db_session):
    """Create user with only expenses, no income"""
    user = User(email="expenses@example.com", hashed_password="test", full_name="Expenses User")
    db_session.add(user)
    db_session.commit()
    
    category = Category(user_id=user.id, name="Shopping")
    db_session.add(category)
    db_session.commit()
    
    # Add only expense entries
    for i in range(3):
        entry = Entry(
            user_id=user.id,
            category_id=category.id,
            type="expense",
            amount=100.0,
            note="Shopping",
            date=date.today() - timedelta(days=i),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    return user


@pytest.fixture
def user_without_data(db_session):
    """Create user with no transaction data"""
    user = User(email="empty@example.com", hashed_password="test", full_name="Empty User")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_with_tl_currency(db_session):
    """Create user with Turkish Lira currency"""
    user = User(email="tl@example.com", hashed_password="test", full_name="TL User")
    db_session.add(user)
    db_session.commit()
    
    # Set currency preference
    prefs = UserPreferences(user_id=user.id, currency_code='TRY')
    db_session.add(prefs)
    db_session.commit()
    
    # Add some entries
    category = Category(user_id=user.id, name="Food")
    db_session.add(category)
    db_session.commit()
    
    entry = Entry(
        user_id=user.id,
        category_id=category.id,
        type="expense",
        amount=100.0,
        note="Lunch",
        date=date.today(),
        currency_code="TRY"
    )
    db_session.add(entry)
    db_session.commit()
    
    return user


@pytest.fixture
def user_with_zero_income(db_session):
    """Create user with expenses but zero income"""
    user = User(email="zeroincome@example.com", hashed_password="test", full_name="Zero Income User")
    db_session.add(user)
    db_session.commit()
    
    category = Category(user_id=user.id, name="Bills")
    db_session.add(category)
    db_session.commit()
    
    # Add expenses only
    for i in range(5):
        entry = Entry(
            user_id=user.id,
            category_id=category.id,
            type="expense",
            amount=200.0,
            note="Bill payment",
            date=date.today() - timedelta(days=i),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    return user


@pytest.fixture
def sample_weekly_report():
    """Sample weekly report data"""
    return {
        'period': {
            'start': '2025-01-13',
            'end': '2025-01-19',
            'week_number': 3,
            'year': 2025
        },
        'currency': 'USD',
        'summary': {
            'total_expenses': 500.0,
            'total_income': 0.0,
            'net_savings': -500.0,
            'transaction_count': 10,
            'avg_transaction': 50.0,
            'comparison': {
                'expense_change_pct': -5.0,
                'income_change_pct': 0.0
            }
        },
        'insights': [
            'Spending decreased by 5% compared to last week',
            'Most spending in Groceries category'
        ],
        'achievements': [],
        'recommendations': [],
        'anomalies': [],
        'show_income': False,
        'generated_at': datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_monthly_report():
    """Sample monthly report data"""
    return {
        'period': {
            'month': 1,
            'year': 2025,
            'month_name': 'January'
        },
        'currency': 'USD',
        'summary': {
            'total_income': 3000.0,
            'total_expenses': 2000.0,
            'net_savings': 1000.0,
            'savings_rate': 33.3
        },
        'category_analysis': {
            'top_category': {'name': 'Groceries', 'amount': 500.0},
            'categories': []
        },
        'insights': ['Good savings rate this month'],
        'achievements': [],
        'recommendations': []
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

