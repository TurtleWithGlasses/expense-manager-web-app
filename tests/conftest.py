"""
Pytest configuration and fixtures for AI testing
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.models.user import User
from app.models.category import Category
from app.models.entry import Entry
from app.models.ai_model import UserAIPreferences


# Test database URL (in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_categories(db_session, test_user):
    """Create test categories"""
    categories = [
        Category(name="Food & Dining", user_id=test_user.id),
        Category(name="Transportation", user_id=test_user.id),
        Category(name="Shopping", user_id=test_user.id),
        Category(name="Entertainment", user_id=test_user.id),
        Category(name="Utilities", user_id=test_user.id),
    ]
    
    for category in categories:
        db_session.add(category)
    
    db_session.commit()
    
    for category in categories:
        db_session.refresh(category)
    
    return categories


@pytest.fixture
def test_entries(db_session, test_user, test_categories):
    """Create test entries for AI training"""
    from decimal import Decimal
    from datetime import date, timedelta
    
    entries = [
        Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("5.50"),
            note="Coffee at Starbucks",
            category_id=test_categories[0].id,  # Food & Dining
            date=date.today()
        ),
        Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("12.00"),
            note="Uber ride to work",
            category_id=test_categories[1].id,  # Transportation
            date=date.today() - timedelta(days=1)
        ),
        Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("25.99"),
            note="Amazon purchase",
            category_id=test_categories[2].id,  # Shopping
            date=date.today() - timedelta(days=2)
        ),
        Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("15.99"),
            note="Netflix subscription",
            category_id=test_categories[3].id,  # Entertainment
            date=date.today() - timedelta(days=3)
        ),
        Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("45.00"),
            note="Grocery shopping at Whole Foods",
            category_id=test_categories[0].id,  # Food & Dining
            date=date.today() - timedelta(days=4)
        ),
    ]
    
    for entry in entries:
        db_session.add(entry)
    
    db_session.commit()
    
    for entry in entries:
        db_session.refresh(entry)
    
    return entries


@pytest.fixture
def test_ai_preferences(db_session, test_user):
    """Create test AI preferences"""
    preferences = UserAIPreferences(
        user_id=test_user.id,
        auto_categorization_enabled=True,
        smart_suggestions_enabled=True,
        spending_insights_enabled=True,
        budget_predictions_enabled=True,
        min_confidence_threshold=0.7,
        auto_accept_threshold=0.9,
        learn_from_feedback=True,
        retrain_frequency_days=7,
        share_anonymized_data=False
    )
    
    db_session.add(preferences)
    db_session.commit()
    db_session.refresh(preferences)
    
    return preferences


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    with patch('app.api.v1.ai.AICategorizationService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        
        # Configure default return values
        mock_instance.suggest_category.return_value = (1, 0.85)
        mock_instance.get_user_ai_preferences.return_value = Mock(
            auto_categorization_enabled=True,
            min_confidence_threshold=0.7
        )
        mock_instance.get_smart_insights.return_value = {
            "top_spending_category": {
                "name": "Food & Dining",
                "amount": 150.50,
                "percentage": 45.2
            },
            "daily_average": 25.08
        }
        mock_instance.record_feedback.return_value = True
        
        yield mock_instance


@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authenticated user"""
    # Mock authentication
    with patch('app.deps.current_user') as mock_current_user:
        mock_current_user.return_value = test_user
        yield client


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Test data for performance testing"""
    return [
        {"note": "Coffee at Starbucks", "amount": 5.50, "type": "expense"},
        {"note": "Uber ride to work", "amount": 12.00, "type": "expense"},
        {"note": "Amazon purchase", "amount": 25.99, "type": "expense"},
        {"note": "Netflix subscription", "amount": 15.99, "type": "expense"},
        {"note": "Grocery shopping", "amount": 45.00, "type": "expense"},
        {"note": "Gas station", "amount": 35.00, "type": "expense"},
        {"note": "Restaurant dinner", "amount": 28.50, "type": "expense"},
        {"note": "Movie tickets", "amount": 18.00, "type": "expense"},
        {"note": "Online shopping", "amount": 75.99, "type": "expense"},
        {"note": "Public transport", "amount": 3.50, "type": "expense"},
    ]


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "ai: mark test as AI-related")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add markers based on test file names
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "integration" in item.nodeid or "api" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "ai" in item.nodeid:
            item.add_marker(pytest.mark.ai)
