import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.category import Category
from app.models.ai_model import UserAIPreferences


class TestAIApiEndpoints:
    """Integration tests for AI API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_categories(self):
        """Mock categories"""
        return [
            Mock(spec=Category, id=1, name="Food & Dining", user_id=1),
            Mock(spec=Category, id=2, name="Transportation", user_id=1),
            Mock(spec=Category, id=3, name="Shopping", user_id=1),
        ]
    
    @pytest.fixture
    def mock_ai_preferences(self):
        """Mock AI preferences"""
        preferences = Mock(spec=UserAIPreferences)
        preferences.user_id = 1
        preferences.auto_categorization_enabled = True
        preferences.smart_suggestions_enabled = True
        preferences.spending_insights_enabled = True
        preferences.budget_predictions_enabled = True
        preferences.min_confidence_threshold = 0.7
        preferences.auto_accept_threshold = 0.9
        preferences.learn_from_feedback = True
        preferences.retrain_frequency_days = 7
        preferences.share_anonymized_data = False
        return preferences
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_suggest_category_success(self, mock_get_db, mock_current_user, client, mock_user, mock_categories):
        """Test successful category suggestion"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.suggest_category.return_value = (1, 0.85)
            
            # Mock category query
            mock_category = Mock(spec=Category)
            mock_category.name = "Food & Dining"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            # Make request
            response = client.post("/ai/suggest-category", data={
                "note": "Coffee at Starbucks",
                "amount": "5.50",
                "entry_type": "expense"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "suggestion" in data
            assert data["suggestion"]["category_id"] == 1
            assert data["suggestion"]["category_name"] == "Food & Dining"
            assert data["suggestion"]["confidence_score"] == 0.85
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_suggest_category_no_suggestion(self, mock_get_db, mock_current_user, client, mock_user):
        """Test category suggestion when no confident suggestion available"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service returning no suggestion
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.suggest_category.return_value = (None, 0.3)
            
            # Make request
            response = client.post("/ai/suggest-category", data={
                "note": "random text",
                "amount": "1000.00",
                "entry_type": "expense"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == False
            assert "No confident suggestions available" in data["message"]
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_suggest_category_missing_data(self, mock_get_db, mock_current_user, client, mock_user):
        """Test category suggestion with missing required data"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Make request with missing data
        response = client.post("/ai/suggest-category", data={
            "note": "",
            "amount": "",
            "entry_type": "expense"
        })
        
        # Should still return a response (AI service handles empty data)
        assert response.status_code == 200
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_provide_feedback_success(self, mock_get_db, mock_current_user, client, mock_user):
        """Test successful feedback submission"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.record_feedback.return_value = True
            
            # Make request
            response = client.post("/ai/feedback", data={
                "suggestion_id": "1",
                "is_accepted": "true"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "Feedback recorded successfully" in data["message"]
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_provide_feedback_failure(self, mock_get_db, mock_current_user, client, mock_user):
        """Test feedback submission when suggestion not found"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service returning failure
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.record_feedback.return_value = False
            
            # Make request
            response = client.post("/ai/feedback", data={
                "suggestion_id": "999",
                "is_accepted": "true"
            })
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == False
            assert "Failed to record feedback" in data["message"]
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_get_insights_success(self, mock_get_db, mock_current_user, client, mock_user):
        """Test successful insights retrieval"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.get_smart_insights.return_value = {
                "top_spending_category": {
                    "name": "Food & Dining",
                    "amount": 150.50,
                    "percentage": 45.2
                },
                "daily_average": 25.08
            }
            
            # Make request
            response = client.get("/ai/insights")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "insights" in data
            assert "top_spending_category" in data["insights"]
            assert "daily_average" in data["insights"]
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_get_insights_empty(self, mock_get_db, mock_current_user, client, mock_user):
        """Test insights retrieval when no data available"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service returning empty insights
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.get_smart_insights.return_value = {}
            
            # Make request
            response = client.get("/ai/insights")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["insights"] == {}
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_ai_settings_page(self, mock_get_db, mock_current_user, client, mock_user, mock_ai_preferences):
        """Test AI settings page rendering"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.get_user_ai_preferences.return_value = mock_ai_preferences
            
            # Make request
            response = client.get("/ai/settings")
            
            # Verify response
            assert response.status_code == 200
            assert "AI Settings" in response.text
            assert "Auto-categorization" in response.text
            assert "Smart Suggestions" in response.text
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_update_ai_settings(self, mock_get_db, mock_current_user, client, mock_user, mock_ai_preferences):
        """Test updating AI settings"""
        # Mock dependencies
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.get_user_ai_preferences.return_value = mock_ai_preferences
            
            # Make request
            response = client.post("/ai/settings", data={
                "auto_categorization_enabled": "true",
                "smart_suggestions_enabled": "false",
                "spending_insights_enabled": "true",
                "budget_predictions_enabled": "false",
                "min_confidence_threshold": "0.8",
                "auto_accept_threshold": "0.95",
                "learn_from_feedback": "true",
                "retrain_frequency_days": "14",
                "share_anonymized_data": "false"
            })
            
            # Verify response
            assert response.status_code == 200
            assert "AI settings updated successfully!" in response.text


class TestAIPerformanceIntegration:
    """Performance integration tests for AI API"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_suggestion_response_time(self, mock_get_db, mock_current_user, client):
        """Test AI suggestion API response time"""
        import time
        
        # Mock dependencies
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.suggest_category.return_value = (1, 0.85)
            
            # Mock category query
            mock_category = Mock(spec=Category)
            mock_category.name = "Food & Dining"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            # Measure response time
            start_time = time.time()
            response = client.post("/ai/suggest-category", data={
                "note": "Coffee at Starbucks",
                "amount": "5.50",
                "entry_type": "expense"
            })
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Verify response
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds
            print(f"AI API response time: {response_time:.3f} seconds")
    
    @patch('app.api.v1.ai.current_user')
    @patch('app.api.v1.ai.get_db')
    def test_concurrent_suggestions(self, mock_get_db, mock_current_user, client):
        """Test concurrent AI suggestion requests"""
        import threading
        import time
        
        # Mock dependencies
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_current_user.return_value = mock_user
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock AI service
        with patch('app.api.v1.ai.AICategorizationService') as mock_ai_service:
            mock_service_instance = mock_ai_service.return_value
            mock_service_instance.suggest_category.return_value = (1, 0.85)
            
            # Mock category query
            mock_category = Mock(spec=Category)
            mock_category.name = "Food & Dining"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            # Test concurrent requests
            results = []
            errors = []
            
            def make_request():
                try:
                    response = client.post("/ai/suggest-category", data={
                        "note": "Coffee at Starbucks",
                        "amount": "5.50",
                        "entry_type": "expense"
                    })
                    results.append(response.status_code)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 5
            assert all(status == 200 for status in results)
            print(f"Successfully handled {len(results)} concurrent requests")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
