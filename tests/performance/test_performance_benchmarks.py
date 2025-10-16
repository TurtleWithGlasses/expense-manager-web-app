"""
Performance benchmarks for critical operations

Tests performance requirements:
- AI predictions < 2 seconds
- Report generation < 5 seconds
- Database queries optimized
- Export operations efficient
- Page load times acceptable
"""

import pytest
import time
import asyncio
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.services.weekly_report_service import WeeklyReportService
from app.services.monthly_report_service import MonthlyReportService
from app.services.excel_export import ExcelExportService
from app.services.pdf_export import PDFExportService
from app.models.entry import Entry
from app.models.category import Category
from app.models.user import User
from app.db.session import SessionLocal


class TestAIPerformance:
    """Test AI service performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_ai_prediction_response_time(self, db_session, user_with_trained_model):
        """AI predictions should respond within 2 seconds"""
        ai_service = AIService(db_session)
        
        transaction_data = {
            'note': 'Grocery store purchase',
            'amount': 45.50,
            'type': 'expense',
            'date': date.today()
        }
        
        start_time = time.time()
        suggestion = await ai_service.suggest_category(user_with_trained_model.id, transaction_data)
        duration = time.time() - start_time
        
        assert duration < 2.0, f"AI prediction took {duration:.2f}s, should be < 2.0s"
        print(f"✓ AI prediction: {duration:.3f}s")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_model_training_time(self, db_session, user_with_training_data):
        """Model training should complete in reasonable time"""
        ai_service = AIService(db_session)
        
        start_time = time.time()
        result = await ai_service.train_user_model(user_with_training_data.id)
        duration = time.time() - start_time
        
        assert duration < 30.0, f"Model training took {duration:.2f}s, should be < 30.0s"
        print(f"✓ Model training ({result.get('trained_on', 0)} samples): {duration:.3f}s")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_batch_predictions(self, db_session, user_with_trained_model):
        """Test performance of multiple consecutive predictions"""
        ai_service = AIService(db_session)
        
        transactions = [
            {'note': f'Purchase {i}', 'amount': 50.0, 'type': 'expense', 'date': date.today()}
            for i in range(10)
        ]
        
        start_time = time.time()
        for transaction in transactions:
            await ai_service.suggest_category(user_with_trained_model.id, transaction)
        duration = time.time() - start_time
        
        avg_time = duration / len(transactions)
        assert avg_time < 1.0, f"Average prediction time {avg_time:.2f}s, should be < 1.0s"
        print(f"✓ Batch predictions (10): {duration:.3f}s (avg: {avg_time:.3f}s)")


class TestReportPerformance:
    """Test report generation performance"""
    
    @pytest.mark.performance
    def test_weekly_report_generation_time(self, db_session, user_with_weekly_data):
        """Weekly report should generate within 5 seconds"""
        service = WeeklyReportService(db_session)
        
        start_time = time.time()
        report = service.generate_weekly_report(user_with_weekly_data.id)
        duration = time.time() - start_time
        
        assert duration < 5.0, f"Weekly report took {duration:.2f}s, should be < 5.0s"
        print(f"✓ Weekly report generation: {duration:.3f}s")
    
    @pytest.mark.performance
    def test_monthly_report_generation_time(self, db_session, user_with_monthly_data):
        """Monthly report should generate within 5 seconds"""
        service = MonthlyReportService(db_session)
        
        start_time = time.time()
        report = service.generate_monthly_report(user_with_monthly_data.id)
        duration = time.time() - start_time
        
        assert duration < 5.0, f"Monthly report took {duration:.2f}s, should be < 5.0s"
        print(f"✓ Monthly report generation: {duration:.3f}s")
    
    @pytest.mark.performance
    def test_report_with_large_dataset(self, db_session, user_with_large_dataset):
        """Report generation with 1000+ entries should be reasonable"""
        service = WeeklyReportService(db_session)
        
        start_time = time.time()
        report = service.generate_weekly_report(user_with_large_dataset.id)
        duration = time.time() - start_time
        
        assert duration < 10.0, f"Report with large dataset took {duration:.2f}s, should be < 10.0s"
        print(f"✓ Large dataset report (1000+ entries): {duration:.3f}s")


class TestExportPerformance:
    """Test export operation performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_excel_export_time(self, db_session, user_with_export_data):
        """Excel export should complete within 10 seconds"""
        service = ExcelExportService(db_session)
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        start_time = time.time()
        buffer = await service.generate_entries_excel(
            user_id=user_with_export_data.id,
            start_date=start_date,
            end_date=end_date
        )
        duration = time.time() - start_time
        
        assert duration < 10.0, f"Excel export took {duration:.2f}s, should be < 10.0s"
        print(f"✓ Excel export: {duration:.3f}s")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_pdf_export_time(self, db_session, user_with_export_data):
        """PDF export should complete within 15 seconds"""
        service = PDFExportService(db_session)
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        start_time = time.time()
        buffer = await service.generate_financial_summary_pdf(
            user_id=user_with_export_data.id,
            start_date=start_date,
            end_date=end_date
        )
        duration = time.time() - start_time
        
        assert duration < 15.0, f"PDF export took {duration:.2f}s, should be < 15.0s"
        print(f"✓ PDF export: {duration:.3f}s")


class TestDatabasePerformance:
    """Test database query performance"""
    
    @pytest.mark.performance
    def test_entry_list_query_time(self, db_session, user_with_many_entries):
        """Listing entries should be fast even with many entries"""
        start_time = time.time()
        
        entries = db_session.query(Entry).filter(
            Entry.user_id == user_with_many_entries.id
        ).order_by(Entry.date.desc()).limit(100).all()
        
        duration = time.time() - start_time
        
        assert duration < 1.0, f"Entry list query took {duration:.2f}s, should be < 1.0s"
        print(f"✓ Entry list query (100 from {len(entries)}): {duration:.3f}s")
    
    @pytest.mark.performance
    def test_category_aggregation_query(self, db_session, user_with_many_entries):
        """Category aggregation should be optimized"""
        from sqlalchemy import func
        
        start_time = time.time()
        
        results = db_session.query(
            Category.name,
            func.sum(Entry.amount).label('total')
        ).join(
            Entry, Category.id == Entry.category_id
        ).filter(
            Entry.user_id == user_with_many_entries.id
        ).group_by(Category.name).all()
        
        duration = time.time() - start_time
        
        assert duration < 2.0, f"Category aggregation took {duration:.2f}s, should be < 2.0s"
        print(f"✓ Category aggregation: {duration:.3f}s")
    
    @pytest.mark.performance
    def test_date_range_query(self, db_session, user_with_many_entries):
        """Date range queries should be indexed and fast"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        start_time = time.time()
        
        entries = db_session.query(Entry).filter(
            Entry.user_id == user_with_many_entries.id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).all()
        
        duration = time.time() - start_time
        
        assert duration < 1.0, f"Date range query took {duration:.2f}s, should be < 1.0s"
        print(f"✓ Date range query: {duration:.3f}s")


class TestMemoryUsage:
    """Test memory usage of operations"""
    
    @pytest.mark.performance
    def test_report_generation_memory(self, db_session, user_with_large_dataset):
        """Report generation should not consume excessive memory"""
        import tracemalloc
        
        tracemalloc.start()
        
        service = WeeklyReportService(db_session)
        report = service.generate_weekly_report(user_with_large_dataset.id)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory should be reasonable (< 100MB)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Peak memory usage {peak_mb:.2f}MB, should be < 100MB"
        print(f"✓ Report generation memory: {peak_mb:.2f}MB peak")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_model_training_memory(self, db_session, user_with_training_data):
        """Model training should not consume excessive memory"""
        import tracemalloc
        
        tracemalloc.start()
        
        ai_service = AIService(db_session)
        await ai_service.train_user_model(user_with_training_data.id)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory should be reasonable (< 200MB)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 200, f"Peak memory usage {peak_mb:.2f}MB, should be < 200MB"
        print(f"✓ Model training memory: {peak_mb:.2f}MB peak")


class TestConcurrency:
    """Test concurrent operation handling"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_ai_predictions(self, db_session, user_with_trained_model):
        """Test handling multiple concurrent AI prediction requests"""
        ai_service = AIService(db_session)
        
        transactions = [
            {'note': f'Purchase {i}', 'amount': 50.0, 'type': 'expense', 'date': date.today()}
            for i in range(5)
        ]
        
        start_time = time.time()
        
        # Run predictions concurrently
        tasks = [
            ai_service.suggest_category(user_with_trained_model.id, transaction)
            for transaction in transactions
        ]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        # Should be faster than sequential
        assert duration < 5.0, f"Concurrent predictions took {duration:.2f}s, should be < 5.0s"
        print(f"✓ 5 concurrent predictions: {duration:.3f}s")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_report_generation(self, db_session, multiple_users):
        """Test generating reports for multiple users concurrently"""
        service = WeeklyReportService(db_session)
        
        start_time = time.time()
        
        # Generate reports for all users concurrently
        async def generate_report(user_id):
            return service.generate_weekly_report(user_id)
        
        tasks = [generate_report(user.id) for user in multiple_users]
        reports = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        # Should handle concurrent generation
        assert duration < 15.0, f"Concurrent report generation took {duration:.2f}s"
        print(f"✓ {len(multiple_users)} concurrent reports: {duration:.3f}s")


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
def user_with_weekly_data(db_session):
    """Create user with weekly data"""
    user = User(email="weekly@perf.test", hashed_password="test", full_name="Weekly User")
    db_session.add(user)
    db_session.commit()
    
    category = Category(user_id=user.id, name="Test")
    db_session.add(category)
    db_session.commit()
    
    for i in range(20):
        entry = Entry(
            user_id=user.id,
            category_id=category.id,
            type="expense",
            amount=50.0 + i,
            note=f"Purchase {i}",
            date=date.today() - timedelta(days=i % 7),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    return user


@pytest.fixture
def user_with_large_dataset(db_session):
    """Create user with 1000+ entries"""
    user = User(email="large@perf.test", hashed_password="test", full_name="Large User")
    db_session.add(user)
    db_session.commit()
    
    categories = []
    for i in range(5):
        cat = Category(user_id=user.id, name=f"Category {i}")
        db_session.add(cat)
        db_session.commit()
        categories.append(cat)
    
    # Add 1000 entries
    for i in range(1000):
        entry = Entry(
            user_id=user.id,
            category_id=categories[i % 5].id,
            type="expense",
            amount=30.0 + (i % 100),
            note=f"Transaction {i}",
            date=date.today() - timedelta(days=i % 365),
            currency_code="USD"
        )
        db_session.add(entry)
        
        if i % 100 == 0:
            db_session.commit()
    
    db_session.commit()
    return user


@pytest.fixture
def user_with_training_data(db_session):
    """Create user with sufficient training data"""
    user = User(email="training@perf.test", hashed_password="test", full_name="Training User")
    db_session.add(user)
    db_session.commit()
    
    categories = ['Groceries', 'Transportation', 'Entertainment', 'Utilities']
    cat_objs = {}
    
    for cat_name in categories:
        cat = Category(user_id=user.id, name=cat_name)
        db_session.add(cat)
        db_session.commit()
        cat_objs[cat_name] = cat
    
    # Add 200 entries (50 per category)
    for i in range(200):
        cat_name = categories[i % 4]
        entry = Entry(
            user_id=user.id,
            category_id=cat_objs[cat_name].id,
            type="expense",
            amount=30.0 + i,
            note=f"{cat_name} purchase {i}",
            date=date.today() - timedelta(days=i),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    return user


@pytest.fixture
def user_with_many_entries(db_session):
    """Create user with many entries for query performance testing"""
    return user_with_large_dataset(db_session)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])

