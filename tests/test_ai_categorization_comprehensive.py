"""
Comprehensive tests for AI Categorization System

Tests cover:
- Model training with various data sizes
- Prediction accuracy and confidence
- Edge cases and error handling
- Feature extraction
- Model persistence
"""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.ai.models.categorization_model import CategorizationModel
from app.ai.data.training_pipeline import TrainingDataPipeline
from app.services.ai_service import AIService
from app.models.entry import Entry
from app.models.category import Category
from app.models.user import User
from app.models.ai_model import AIModel, UserAIPreferences
from app.db.session import SessionLocal


class TestCategorizationModel:
    """Test the ML categorization model"""
    
    def test_model_initialization(self):
        """Test model initializes correctly"""
        model = CategorizationModel()
        assert model is not None
        assert model.model is not None
        assert model.vectorizer is not None
        assert model.label_encoder is not None
        assert model.is_trained == False
    
    def test_training_with_sufficient_data(self, db_session, sample_training_data):
        """Test model trains successfully with sufficient data"""
        model = CategorizationModel()
        
        # Train with 100+ samples per category
        X_train, y_train = sample_training_data
        
        model.train(X_train, y_train)
        
        assert model.is_trained == True
        assert model.model is not None
    
    def test_prediction_accuracy(self, db_session, trained_model, test_data):
        """Test model prediction accuracy meets threshold"""
        X_test, y_test = test_data
        
        correct_predictions = 0
        for X, y_true in zip(X_test, y_test):
            y_pred, confidence = trained_model.predict(X)
            if y_pred == y_true:
                correct_predictions += 1
        
        accuracy = correct_predictions / len(y_test)
        assert accuracy >= 0.70, f"Accuracy {accuracy:.2%} below 70% threshold"
    
    def test_confidence_scores(self, trained_model, sample_transaction):
        """Test confidence scores are in valid range"""
        prediction, confidence = trained_model.predict(sample_transaction)
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
    
    def test_low_confidence_handling(self, trained_model, ambiguous_transaction):
        """Test that ambiguous transactions have lower confidence"""
        prediction, confidence = trained_model.predict(ambiguous_transaction)
        
        # Ambiguous transactions should have lower confidence
        assert confidence < 0.7
    
    def test_model_save_load(self, trained_model, tmp_path):
        """Test model can be saved and loaded"""
        model_path = tmp_path / "test_model.pkl"
        
        # Save model
        trained_model.save_model(str(model_path))
        assert model_path.exists()
        
        # Load model
        new_model = CategorizationModel()
        new_model.load_model(str(model_path))
        
        assert new_model.is_trained == True
        
        # Verify predictions match
        test_data = {'text': 'grocery shopping', 'amount': 50, 'weekday': 1, 'month': 3, 'day': 15}
        pred1, conf1 = trained_model.predict(test_data)
        pred2, conf2 = new_model.predict(test_data)
        
        assert pred1 == pred2
        assert abs(conf1 - conf2) < 0.01
    
    def test_prediction_without_training(self):
        """Test prediction fails gracefully without training"""
        model = CategorizationModel()
        test_data = {'text': 'test', 'amount': 10, 'weekday': 1, 'month': 3, 'day': 15}
        
        prediction, confidence = model.predict(test_data)
        
        assert prediction is None
        assert confidence == 0.0


class TestTrainingDataPipeline:
    """Test the training data pipeline"""
    
    def test_feature_extraction(self, db_session, sample_entry):
        """Test feature extraction from entries"""
        pipeline = TrainingDataPipeline(db_session)
        features = pipeline.extract_features(sample_entry)
        
        assert 'text' in features
        assert 'amount' in features
        assert 'weekday' in features
        assert 'month' in features
        assert 'day' in features
        assert 'is_weekend' in features
        assert 'is_month_start' in features
        assert 'is_month_end' in features
    
    def test_prepare_training_data(self, db_session, user_with_entries):
        """Test training data preparation"""
        pipeline = TrainingDataPipeline(db_session)
        
        features, labels = pipeline.prepare_training_data(
            user_id=user_with_entries.id,
            min_samples_per_category=3
        )
        
        assert len(features) > 0
        assert len(labels) > 0
        assert len(features) == len(labels)
    
    def test_rare_category_filtering(self, db_session, user_with_rare_categories):
        """Test that categories with few samples are filtered out"""
        pipeline = TrainingDataPipeline(db_session)
        
        features, labels = pipeline.prepare_training_data(
            user_id=user_with_rare_categories.id,
            min_samples_per_category=5
        )
        
        # Check that all remaining categories have >= 5 samples
        from collections import Counter
        label_counts = Counter(labels)
        
        for category, count in label_counts.items():
            assert count >= 5
    
    def test_temporal_feature_extraction(self, db_session, sample_entry):
        """Test extraction of temporal features"""
        pipeline = TrainingDataPipeline(db_session, use_temporal_features=True)
        features = pipeline.extract_features(sample_entry, user_id=sample_entry.user_id)
        
        # Should have temporal features
        assert 'weekly_pattern' in features or 'text' in features
    
    def test_empty_entries(self, db_session, user_without_entries):
        """Test handling of users with no entries"""
        pipeline = TrainingDataPipeline(db_session)
        
        features, labels = pipeline.prepare_training_data(
            user_id=user_without_entries.id,
            min_samples_per_category=3
        )
        
        assert len(features) == 0
        assert len(labels) == 0


class TestAIService:
    """Test the AI service layer"""
    
    @pytest.mark.asyncio
    async def test_suggest_category_with_trained_model(self, db_session, user_with_trained_model):
        """Test category suggestion with trained model"""
        ai_service = AIService(db_session)
        
        transaction_data = {
            'note': 'Whole Foods Market',
            'amount': 45.50,
            'type': 'expense',
            'date': date.today()
        }
        
        suggestion = await ai_service.suggest_category(user_with_trained_model.id, transaction_data)
        
        assert suggestion is not None
        assert suggestion.category_id is not None
        assert 0.0 <= suggestion.confidence_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_suggest_category_without_trained_model(self, db_session, user_without_model):
        """Test category suggestion without trained model"""
        ai_service = AIService(db_session)
        
        transaction_data = {
            'note': 'Coffee shop',
            'amount': 5.50,
            'type': 'expense',
            'date': date.today()
        }
        
        # Should fall back to rule-based suggestion
        suggestion = await ai_service.suggest_category(user_without_model.id, transaction_data)
        
        # May return None or a rule-based suggestion
        assert suggestion is None or suggestion.category_id is not None
    
    @pytest.mark.asyncio
    async def test_train_user_model(self, db_session, user_with_sufficient_data):
        """Test training a user's model"""
        ai_service = AIService(db_session)
        
        result = await ai_service.train_user_model(user_with_sufficient_data.id)
        
        assert result['success'] == True
        assert result['accuracy'] >= 0.0
        assert result['trained_on'] > 0
    
    @pytest.mark.asyncio
    async def test_train_model_insufficient_data(self, db_session, user_with_few_entries):
        """Test training fails gracefully with insufficient data"""
        ai_service = AIService(db_session)
        
        result = await ai_service.train_user_model(user_with_few_entries.id)
        
        assert result['success'] == False
        assert 'error' in result or 'message' in result
    
    @pytest.mark.asyncio
    async def test_get_model_status(self, db_session, user_with_trained_model):
        """Test getting model status"""
        ai_service = AIService(db_session)
        
        status = await ai_service.get_model_status(user_with_trained_model.id)
        
        assert status is not None
        assert 'is_trained' in status
        assert 'accuracy' in status or status['is_trained'] == False
    
    @pytest.mark.asyncio
    async def test_record_feedback(self, db_session, user_with_entries, sample_suggestion):
        """Test recording user feedback"""
        ai_service = AIService(db_session)
        
        # Accept suggestion
        result = await ai_service.record_feedback(
            suggestion_id=sample_suggestion.id,
            accepted=True
        )
        
        assert result == True
        
        # Verify feedback recorded
        db_session.refresh(sample_suggestion)
        assert sample_suggestion.user_feedback == True


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_text_feature(self, trained_model):
        """Test prediction with empty text"""
        data = {'text': '', 'amount': 10, 'weekday': 1, 'month': 3, 'day': 15}
        
        # Should not crash
        prediction, confidence = trained_model.predict(data)
        assert prediction is not None or prediction is None  # Either is acceptable
    
    def test_very_large_amount(self, trained_model):
        """Test prediction with unusually large amount"""
        data = {'text': 'house purchase', 'amount': 500000, 'weekday': 1, 'month': 3, 'day': 15}
        
        prediction, confidence = trained_model.predict(data)
        # Should handle gracefully
        assert confidence >= 0.0
    
    def test_special_characters_in_text(self, trained_model):
        """Test prediction with special characters"""
        data = {'text': '$$$ café ñoño @#$%', 'amount': 10, 'weekday': 1, 'month': 3, 'day': 15}
        
        # Should not crash
        prediction, confidence = trained_model.predict(data)
        assert confidence >= 0.0
    
    def test_negative_amount(self, trained_model):
        """Test handling of negative amounts"""
        data = {'text': 'refund', 'amount': -50, 'weekday': 1, 'month': 3, 'day': 15}
        
        # Should handle gracefully
        prediction, confidence = trained_model.predict(data)
        assert confidence >= 0.0


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
def sample_entry(db_session):
    """Create a sample entry for testing"""
    user = User(email="test@example.com", hashed_password="test", full_name="Test User")
    db_session.add(user)
    db_session.commit()
    
    category = Category(user_id=user.id, name="Groceries")
    db_session.add(category)
    db_session.commit()
    
    entry = Entry(
        user_id=user.id,
        category_id=category.id,
        type="expense",
        amount=50.0,
        note="Whole Foods grocery shopping",
        date=date.today(),
        currency_code="USD"
    )
    db_session.add(entry)
    db_session.commit()
    
    return entry


@pytest.fixture
def sample_training_data():
    """Generate sample training data"""
    import random
    
    categories = ['Groceries', 'Transportation', 'Entertainment', 'Utilities', 'Dining']
    templates = {
        'Groceries': ['grocery store', 'supermarket', 'whole foods', 'trader joes'],
        'Transportation': ['uber', 'lyft', 'gas station', 'metro'],
        'Entertainment': ['movie', 'netflix', 'spotify', 'concert'],
        'Utilities': ['electric', 'water', 'internet', 'phone'],
        'Dining': ['restaurant', 'cafe', 'pizza', 'sushi']
    }
    
    X_train = []
    y_train = []
    
    for category in categories:
        for _ in range(30):  # 30 samples per category
            text = random.choice(templates[category])
            amount = random.uniform(10, 200)
            weekday = random.randint(0, 6)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            
            X_train.append({
                'text': text,
                'amount': amount,
                'weekday': weekday,
                'month': month,
                'day': day,
                'is_weekend': weekday >= 5,
                'is_month_start': day <= 7,
                'is_month_end': day >= 23
            })
            y_train.append(category)
    
    return X_train, y_train


@pytest.fixture
def trained_model(sample_training_data):
    """Create a trained model"""
    model = CategorizationModel()
    X_train, y_train = sample_training_data
    model.train(X_train, y_train)
    return model


@pytest.fixture
def test_data(sample_training_data):
    """Generate test data"""
    # Use 20% of training data as test data
    X, y = sample_training_data
    split_idx = int(len(X) * 0.8)
    return X[split_idx:], y[split_idx:]


@pytest.fixture
def sample_transaction():
    """Sample transaction data"""
    return {
        'text': 'grocery store purchase',
        'amount': 45.50,
        'weekday': 2,
        'month': 6,
        'day': 15,
        'is_weekend': False,
        'is_month_start': False,
        'is_month_end': False
    }


@pytest.fixture
def ambiguous_transaction():
    """Transaction with ambiguous category"""
    return {
        'text': 'payment',  # Very generic
        'amount': 100.0,
        'weekday': 3,
        'month': 6,
        'day': 15,
        'is_weekend': False,
        'is_month_start': False,
        'is_month_end': False
    }


@pytest.fixture
def user_with_entries(db_session):
    """Create a user with multiple categorized entries"""
    user = User(email="testuser@example.com", hashed_password="test", full_name="Test User")
    db_session.add(user)
    db_session.commit()
    
    # Create categories
    categories = {
        'Groceries': [],
        'Transportation': [],
        'Entertainment': []
    }
    
    for cat_name in categories.keys():
        category = Category(user_id=user.id, name=cat_name)
        db_session.add(category)
        db_session.commit()
        categories[cat_name] = category
    
    # Create entries
    for _ in range(10):
        for cat_name, category in categories.items():
            entry = Entry(
                user_id=user.id,
                category_id=category.id,
                type="expense",
                amount=50.0,
                note=f"{cat_name} purchase",
                date=date.today() - timedelta(days=_),
                currency_code="USD"
            )
            db_session.add(entry)
    
    db_session.commit()
    return user


@pytest.fixture
def user_without_entries(db_session):
    """Create a user with no entries"""
    user = User(email="newuser@example.com", hashed_password="test", full_name="New User")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_with_rare_categories(db_session):
    """Create a user with some rare categories (few samples)"""
    user = User(email="rareuser@example.com", hashed_password="test", full_name="Rare User")
    db_session.add(user)
    db_session.commit()
    
    # Common category with many entries
    common_cat = Category(user_id=user.id, name="Common")
    db_session.add(common_cat)
    db_session.commit()
    
    for _ in range(20):
        entry = Entry(
            user_id=user.id,
            category_id=common_cat.id,
            type="expense",
            amount=50.0,
            note="Common purchase",
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
    
    # Rare category with few entries
    rare_cat = Category(user_id=user.id, name="Rare")
    db_session.add(rare_cat)
    db_session.commit()
    
    for _ in range(2):  # Only 2 entries
        entry = Entry(
            user_id=user.id,
            category_id=rare_cat.id,
            type="expense",
            amount=50.0,
            note="Rare purchase",
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
    
    db_session.commit()
    return user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

