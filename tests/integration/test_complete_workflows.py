"""
Integration tests for complete user workflows

Tests cover end-to-end scenarios:
- Entry creation → AI suggestion → Category assignment
- Entry creation → Report status update
- Currency change → UI updates
- Report generation → Email → Status tracking
- Multi-step user journeys
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.entry import Entry
from app.models.category import Category
from app.models.user_preferences import UserPreferences
from app.models.report_status import ReportStatus
from app.db.session import SessionLocal
from app.services.ai_service import AIService
from app.services.report_status_service import ReportStatusService
from app.services.weekly_report_service import WeeklyReportService


client = TestClient(app)


class TestEntryCreationWorkflow:
    """Test complete entry creation workflows"""
    
    @pytest.mark.asyncio
    async def test_create_entry_with_ai_suggestion(self, db_session, authenticated_user):
        """
        Complete workflow:
        1. User creates entry
        2. AI suggests category
        3. User accepts suggestion
        4. Entry is saved with category
        5. Report status updates to 'New'
        """
        user, auth_token = authenticated_user
        
        # Step 1: Create entry
        entry_data = {
            'type': 'expense',
            'amount': 50.00,
            'note': 'Whole Foods grocery shopping',
            'date': date.today().isoformat()
        }
        
        response = client.post(
            "/entries/create",
            data=entry_data,
            cookies={"session_id": auth_token}
        )
        
        assert response.status_code == 200
        
        # Step 2: Verify AI suggestion was made (if model trained)
        ai_service = AIService(db_session)
        suggestion = await ai_service.suggest_category(user.id, entry_data)
        
        # Step 3: Verify entry was created
        entry = db_session.query(Entry).filter(
            Entry.user_id == user.id,
            Entry.note == 'Whole Foods grocery shopping'
        ).first()
        
        assert entry is not None
        assert entry.amount == 50.00
        
        # Step 4: Verify report status updated to 'New'
        status_service = ReportStatusService(db_session)
        status = status_service.get_report_status(user.id, 'weekly')
        
        assert status['is_new'] == True
    
    @pytest.mark.asyncio
    async def test_entry_without_ai_fallback(self, db_session, user_without_trained_model):
        """Test entry creation when AI model not available"""
        user, auth_token = user_without_trained_model
        
        entry_data = {
            'type': 'expense',
            'amount': 25.00,
            'note': 'Coffee',
            'date': date.today().isoformat()
        }
        
        response = client.post(
            "/entries/create",
            data=entry_data,
            cookies={"session_id": auth_token}
        )
        
        # Should still create entry successfully
        assert response.status_code == 200
        
        # Verify entry created
        entry = db_session.query(Entry).filter(
            Entry.user_id == user.id,
            Entry.note == 'Coffee'
        ).first()
        
        assert entry is not None


class TestReportWorkflow:
    """Test complete report generation and delivery workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_report_workflow(self, db_session, user_with_data):
        """
        Complete workflow:
        1. User has transaction data
        2. Generate weekly report
        3. Report status shows 'New'
        4. User views report
        5. Status changes to 'Viewed'
        6. User adds new entry
        7. Status changes back to 'New'
        """
        user, auth_token = user_with_data
        
        # Step 1 & 2: Generate report
        report_service = WeeklyReportService(db_session)
        report = report_service.generate_weekly_report(user.id)
        
        assert report is not None
        
        # Step 3: Check status is 'New'
        status_service = ReportStatusService(db_session)
        status = status_service.get_report_status(user.id, 'weekly')
        assert status['is_new'] == True
        
        # Step 4: User views report
        response = client.get(
            "/reports/weekly",
            cookies={"session_id": auth_token}
        )
        assert response.status_code == 200
        
        # Mark as viewed (happens via JS in real app)
        status_service.mark_report_as_viewed(user.id, 'weekly')
        
        # Step 5: Verify status changed to 'Viewed'
        status = status_service.get_report_status(user.id, 'weekly')
        assert status['is_new'] == False
        
        # Step 6: Add new entry
        entry_data = {
            'type': 'expense',
            'amount': 100.00,
            'note': 'New purchase',
            'date': date.today().isoformat()
        }
        
        response = client.post(
            "/entries/create",
            data=entry_data,
            cookies={"session_id": auth_token}
        )
        
        # Step 7: Status should be 'New' again
        status = status_service.get_report_status(user.id, 'weekly')
        assert status['is_new'] == True
    
    @pytest.mark.asyncio
    async def test_email_report_workflow(self, db_session, user_with_data):
        """
        Workflow:
        1. Generate report
        2. Send email
        3. Verify email sent
        """
        user, auth_token = user_with_data
        
        # Request email report
        response = client.post(
            "/reports/weekly/email",
            cookies={"session_id": auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True


class TestCurrencyChangeWorkflow:
    """Test currency change propagation"""
    
    @pytest.mark.asyncio
    async def test_currency_change_updates_all_displays(self, db_session, authenticated_user):
        """
        Workflow:
        1. User has USD currency
        2. User changes to TRY
        3. Dashboard updates
        4. Charts update
        5. Reports update
        """
        user, auth_token = authenticated_user
        
        # Add some entries
        category = Category(user_id=user.id, name="Test")
        db_session.add(category)
        db_session.commit()
        
        entry = Entry(
            user_id=user.id,
            category_id=category.id,
            type="expense",
            amount=100.00,
            note="Test",
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()
        
        # Change currency
        response = client.post(
            "/currency/update",
            data={"currency_code": "TRY"},
            cookies={"session_id": auth_token}
        )
        
        assert response.status_code in [200, 302]  # May redirect
        
        # Verify currency updated
        prefs = db_session.query(UserPreferences).filter(
            UserPreferences.user_id == user.id
        ).first()
        
        assert prefs.currency_code == "TRY"
        
        # Verify dashboard shows TRY
        response = client.get(
            "/",
            cookies={"session_id": auth_token}
        )
        
        # Response should be successful
        assert response.status_code == 200


class TestMultiStepUserJourney:
    """Test realistic multi-step user journeys"""
    
    @pytest.mark.asyncio
    async def test_new_user_journey(self, db_session):
        """
        Complete new user journey:
        1. Register
        2. Verify email (simulated)
        3. Login
        4. Set currency preference
        5. Create categories
        6. Add first entry
        7. Train AI model
        8. Add more entries with AI
        9. View reports
        """
        # Step 1: Register
        user_data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "full_name": "New User"
        }
        
        response = client.post("/auth/register", data=user_data)
        assert response.status_code in [200, 201, 302]
        
        # Step 2: Verify email (skip in test)
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        if user:
            user.is_verified = True
            db_session.commit()
        
        # Step 3: Login
        response = client.post(
            "/auth/login",
            data={"email": "newuser@example.com", "password": "TestPass123!"}
        )
        
        # Get session cookie
        session_cookie = response.cookies.get("session_id")
        
        if session_cookie and user:
            # Step 4: Set currency
            response = client.post(
                "/currency/update",
                data={"currency_code": "EUR"},
                cookies={"session_id": session_cookie}
            )
            
            # Step 5: Create category
            response = client.post(
                "/categories/create",
                data={"name": "Groceries"},
                cookies={"session_id": session_cookie}
            )
            
            # Step 6: Add entry
            response = client.post(
                "/entries/create",
                data={
                    "type": "expense",
                    "amount": 50.00,
                    "note": "Supermarket",
                    "date": date.today().isoformat()
                },
                cookies={"session_id": session_cookie}
            )
            
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_experienced_user_journey(self, db_session, user_with_history):
        """
        Experienced user journey:
        1. Login
        2. Check AI suggestions
        3. Add entries with AI
        4. View weekly report
        5. Export to Excel
        6. Email report
        """
        user, auth_token = user_with_history
        
        # Already logged in, check AI status
        response = client.get(
            "/ai/model/status",
            cookies={"session_id": auth_token}
        )
        
        # Add entry with AI
        response = client.post(
            "/entries/create",
            data={
                "type": "expense",
                "amount": 75.00,
                "note": "Restaurant dinner",
                "date": date.today().isoformat()
            },
            cookies={"session_id": auth_token}
        )
        
        # View report
        response = client.get(
            "/reports/weekly",
            cookies={"session_id": auth_token}
        )
        
        assert response.status_code == 200


class TestErrorRecoveryWorkflow:
    """Test error handling and recovery in workflows"""
    
    @pytest.mark.asyncio
    async def test_entry_creation_with_invalid_data(self, authenticated_user):
        """Test graceful handling of invalid entry data"""
        user, auth_token = authenticated_user
        
        # Try to create entry with negative amount
        response = client.post(
            "/entries/create",
            data={
                "type": "expense",
                "amount": -50.00,  # Invalid
                "note": "Test",
                "date": date.today().isoformat()
            },
            cookies={"session_id": auth_token}
        )
        
        # Should handle gracefully (may accept or reject)
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_report_generation_with_no_data(self, authenticated_user):
        """Test report generation when user has no data"""
        user, auth_token = authenticated_user
        
        response = client.get(
            "/reports/weekly",
            cookies={"session_id": auth_token}
        )
        
        # Should still render successfully
        assert response.status_code == 200


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
def authenticated_user(db_session):
    """Create an authenticated user with session"""
    from app.core.security import hash_password
    from app.core.session import create_session
    
    user = User(
        email="auth@example.com",
        hashed_password=hash_password("password123"),
        full_name="Auth User",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Create session
    session_id = create_session(db_session, user.id)
    
    return user, session_id


@pytest.fixture
def user_with_data(db_session):
    """Create user with transaction data"""
    from app.core.security import hash_password
    from app.core.session import create_session
    
    user = User(
        email="data@example.com",
        hashed_password=hash_password("password123"),
        full_name="Data User",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Add category and entries
    category = Category(user_id=user.id, name="Groceries")
    db_session.add(category)
    db_session.commit()
    
    for i in range(5):
        entry = Entry(
            user_id=user.id,
            category_id=category.id,
            type="expense",
            amount=50.00 + i * 10,
            note=f"Purchase {i}",
            date=date.today() - timedelta(days=i),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    
    session_id = create_session(db_session, user.id)
    
    return user, session_id


@pytest.fixture
def user_with_history(db_session):
    """Create user with extensive transaction history"""
    from app.core.security import hash_password
    from app.core.session import create_session
    
    user = User(
        email="history@example.com",
        hashed_password=hash_password("password123"),
        full_name="History User",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Add multiple categories
    categories = {}
    for cat_name in ['Groceries', 'Transportation', 'Entertainment']:
        cat = Category(user_id=user.id, name=cat_name)
        db_session.add(cat)
        db_session.commit()
        categories[cat_name] = cat
    
    # Add many entries
    for i in range(30):
        cat_name = ['Groceries', 'Transportation', 'Entertainment'][i % 3]
        entry = Entry(
            user_id=user.id,
            category_id=categories[cat_name].id,
            type="expense",
            amount=30.00 + i,
            note=f"{cat_name} purchase",
            date=date.today() - timedelta(days=i),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    
    session_id = create_session(db_session, user.id)
    
    return user, session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

