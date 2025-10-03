import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.services.ai_service import AICategorizationService
from app.models.user import User
from app.models.category import Category
from app.models.entry import Entry
from app.models.ai_model import UserAIPreferences


class TestAICategorizationService:
    """Test suite for AI categorization service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_categories(self):
        """Mock categories"""
        categories = [
            Mock(spec=Category, id=1, name="Food & Dining", user_id=1),
            Mock(spec=Category, id=2, name="Transportation", user_id=1),
            Mock(spec=Category, id=3, name="Shopping", user_id=1),
            Mock(spec=Category, id=4, name="Entertainment", user_id=1),
        ]
        for cat in categories:
            cat.name = cat.name
        return categories
    
    @pytest.fixture
    def mock_entries(self):
        """Mock historical entries for testing"""
        entries = [
            Mock(spec=Entry, id=1, note="Coffee at Starbucks", amount=Decimal('5.50'), 
                 category_id=1, user_id=1, type='expense'),
            Mock(spec=Entry, id=2, note="Uber ride to work", amount=Decimal('12.00'), 
                 category_id=2, user_id=1, type='expense'),
            Mock(spec=Entry, id=3, note="Amazon purchase", amount=Decimal('25.99'), 
                 category_id=3, user_id=1, type='expense'),
            Mock(spec=Entry, id=4, note="Netflix subscription", amount=Decimal('15.99'), 
                 category_id=4, user_id=1, type='expense'),
        ]
        return entries
    
    def test_get_user_ai_preferences_creates_default(self, mock_db, mock_user):
        """Test that AI preferences are created with defaults if not exist"""
        # Mock empty query result
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock commit
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        service = AICategorizationService(mock_db)
        preferences = service.get_user_ai_preferences(mock_user.id)
        
        # Verify preferences were created with defaults
        assert preferences.user_id == mock_user.id
        assert preferences.auto_categorization_enabled == True
        assert preferences.min_confidence_threshold == 0.7
        assert preferences.auto_accept_threshold == 0.9
        assert preferences.learn_from_feedback == True
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_exact_text_match(self, mock_db, mock_user, mock_categories, mock_entries):
        """Test exact text matching functionality"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_entries
        
        service = AICategorizationService(mock_db)
        
        # Test exact match
        result = service._exact_text_match("coffee at starbucks", mock_categories, mock_user.id)
        
        assert result is not None
        assert result[0] == 1  # Food & Dining category ID
        assert result[1] > 0.7  # High confidence for exact match
    
    def test_keyword_based_match(self, mock_db, mock_user, mock_categories):
        """Test keyword-based matching"""
        service = AICategorizationService(mock_db)
        
        # Test food-related keywords
        result = service._keyword_based_match("restaurant dinner", mock_categories, mock_user.id)
        
        assert result is not None
        assert result[0] == 1  # Food & Dining category ID
        assert result[1] > 0.7  # High confidence for keyword match
    
    def test_amount_based_patterns(self, mock_db, mock_user, mock_categories, mock_entries):
        """Test amount-based pattern matching"""
        # Mock database query for similar amounts
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_entries
        
        service = AICategorizationService(mock_db)
        
        # Test amount in similar range
        result = service._amount_based_patterns(5.75, mock_categories, mock_user.id)
        
        assert result is not None
        assert result[0] == 1  # Should match coffee category
        assert result[1] > 0.5  # Moderate confidence for amount match
    
    def test_frequency_analysis(self, mock_db, mock_user, mock_categories, mock_entries):
        """Test frequency analysis"""
        # Mock recent entries query
        mock_db.query.return_value.filter.return_value.all.return_value = mock_entries
        
        service = AICategorizationService(mock_db)
        
        # Test frequency analysis
        result = service._frequency_analysis("some text", mock_categories, mock_user.id)
        
        assert result is not None
        assert result[0] in [1, 2, 3, 4]  # Should return one of the category IDs
        assert result[1] > 0.3  # Some confidence based on frequency
    
    def test_suggest_category_high_confidence(self, mock_db, mock_user, mock_categories, mock_entries):
        """Test category suggestion with high confidence"""
        # Mock all database queries
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            auto_categorization_enabled=True,
            min_confidence_threshold=0.7
        )
        mock_db.query.return_value.filter.return_value.all.return_value = mock_categories
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_entries
        
        service = AICategorizationService(mock_db)
        
        # Test with high-confidence data
        entry_data = {
            "note": "Coffee at Starbucks",
            "amount": 5.50,
            "type": "expense"
        }
        
        category_id, confidence = service.suggest_category(mock_user.id, entry_data)
        
        assert category_id is not None
        assert confidence >= 0.7
        assert category_id in [cat.id for cat in mock_categories]
    
    def test_suggest_category_low_confidence(self, mock_db, mock_user, mock_categories):
        """Test category suggestion with low confidence (should return None)"""
        # Mock preferences with high threshold
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            auto_categorization_enabled=True,
            min_confidence_threshold=0.9
        )
        mock_db.query.return_value.filter.return_value.all.return_value = mock_categories
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        service = AICategorizationService(mock_db)
        
        # Test with low-confidence data
        entry_data = {
            "note": "random text",
            "amount": 1000.0,
            "type": "expense"
        }
        
        category_id, confidence = service.suggest_category(mock_user.id, entry_data)
        
        assert category_id is None
        assert confidence < 0.9
    
    def test_suggest_category_disabled(self, mock_db, mock_user, mock_categories):
        """Test category suggestion when AI is disabled"""
        # Mock disabled preferences
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            auto_categorization_enabled=False
        )
        
        service = AICategorizationService(mock_db)
        
        entry_data = {
            "note": "Coffee at Starbucks",
            "amount": 5.50,
            "type": "expense"
        }
        
        category_id, confidence = service.suggest_category(mock_user.id, entry_data)
        
        assert category_id is None
        assert confidence == 0.0
    
    def test_create_suggestion(self, mock_db, mock_user):
        """Test creating AI suggestion record"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        service = AICategorizationService(mock_db)
        
        suggestion_data = {"method": "exact_match", "keywords": ["coffee"]}
        suggestion = service.create_suggestion(
            user_id=mock_user.id,
            entry_id=1,
            suggested_category_id=1,
            confidence_score=0.85,
            suggestion_data=suggestion_data
        )
        
        assert suggestion.user_id == mock_user.id
        assert suggestion.entry_id == 1
        assert suggestion.suggested_category_id == 1
        assert suggestion.confidence_score == 0.85
        assert suggestion.is_accepted is None  # Pending
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_feedback(self, mock_db):
        """Test recording user feedback"""
        # Mock suggestion query
        mock_suggestion = Mock()
        mock_suggestion.is_accepted = None
        mock_suggestion.feedback_updated_at = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_suggestion
        mock_db.commit = Mock()
        
        service = AICategorizationService(mock_db)
        
        success = service.record_feedback(suggestion_id=1, is_accepted=True)
        
        assert success == True
        assert mock_suggestion.is_accepted == True
        assert mock_suggestion.feedback_updated_at is not None
        mock_db.commit.assert_called_once()
    
    def test_record_feedback_not_found(self, mock_db):
        """Test recording feedback for non-existent suggestion"""
        # Mock empty query result
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service = AICategorizationService(mock_db)
        
        success = service.record_feedback(suggestion_id=999, is_accepted=True)
        
        assert success == False
    
    def test_get_smart_insights(self, mock_db, mock_user, mock_entries):
        """Test smart insights generation"""
        # Mock preferences
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            spending_insights_enabled=True
        )
        
        # Mock recent expenses query
        mock_db.query.return_value.filter.return_value.all.return_value = mock_entries
        
        # Mock category relationship
        for entry in mock_entries:
            entry.category = Mock(name=entry.note.split()[0].title())
        
        service = AICategorizationService(mock_db)
        
        insights = service.get_smart_insights(mock_user.id)
        
        assert isinstance(insights, dict)
        assert 'top_spending_category' in insights or 'daily_average' in insights
    
    def test_get_smart_insights_disabled(self, mock_db, mock_user):
        """Test smart insights when disabled"""
        # Mock disabled preferences
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            spending_insights_enabled=False
        )
        
        service = AICategorizationService(mock_db)
        
        insights = service.get_smart_insights(mock_user.id)
        
        assert insights == {}


class TestAIPerformance:
    """Performance tests for AI services"""
    
    def test_suggestion_response_time(self, mock_db, mock_user, mock_categories):
        """Test that AI suggestions return within acceptable time"""
        import time
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            auto_categorization_enabled=True,
            min_confidence_threshold=0.7
        )
        mock_db.query.return_value.filter.return_value.all.return_value = mock_categories
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        service = AICategorizationService(mock_db)
        
        entry_data = {
            "note": "Coffee at Starbucks",
            "amount": 5.50,
            "type": "expense"
        }
        
        start_time = time.time()
        category_id, confidence = service.suggest_category(mock_user.id, entry_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within 2 seconds
        assert response_time < 2.0
        print(f"AI suggestion response time: {response_time:.3f} seconds")
    
    def test_bulk_suggestions_performance(self, mock_db, mock_user, mock_categories):
        """Test performance with multiple suggestions"""
        import time
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            auto_categorization_enabled=True,
            min_confidence_threshold=0.7
        )
        mock_db.query.return_value.filter.return_value.all.return_value = mock_categories
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        service = AICategorizationService(mock_db)
        
        # Test with multiple entries
        test_entries = [
            {"note": "Coffee at Starbucks", "amount": 5.50, "type": "expense"},
            {"note": "Uber ride", "amount": 12.00, "type": "expense"},
            {"note": "Amazon purchase", "amount": 25.99, "type": "expense"},
            {"note": "Netflix subscription", "amount": 15.99, "type": "expense"},
            {"note": "Grocery shopping", "amount": 45.00, "type": "expense"},
        ]
        
        start_time = time.time()
        
        for entry_data in test_entries:
            category_id, confidence = service.suggest_category(mock_user.id, entry_data)
        
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_suggestion = total_time / len(test_entries)
        
        # Should average less than 0.5 seconds per suggestion
        assert avg_time_per_suggestion < 0.5
        print(f"Average time per suggestion: {avg_time_per_suggestion:.3f} seconds")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
