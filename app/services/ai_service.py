import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.entry import Entry
from app.models.category import Category
from app.models.ai_model import AIModel, AISuggestion, UserAIPreferences
from app.ai.models.categorization_model import CategorizationModel
from app.ai.data.training_pipeline import TrainingDataPipeline


class AICategorizationService:
    """AI service for smart categorization of expense entries"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_model = None  # Lazy loaded when needed
        self.training_pipeline = TrainingDataPipeline(db)
    
    def get_user_ai_preferences(self, user_id: int) -> Optional[UserAIPreferences]:
        """Get or create AI preferences for user"""
        preferences = self.db.query(UserAIPreferences).filter(
            UserAIPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            preferences = UserAIPreferences(
                user_id=user_id,
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
            self.db.add(preferences)
            self.db.commit()
        
        return preferences
    
    def suggest_category(self, user_id: int, entry_data: Dict) -> Tuple[Optional[int], float]:
        """
        Suggest a category for a new entry using ML model with rule-based fallback
        
        Args:
            user_id: User ID
            entry_data: Dictionary containing entry details (note, description, amount, etc.)
        
        Returns:
            Tuple of (suggested_category_id, confidence_score)
        """
        preferences = self.get_user_ai_preferences(user_id)
        if not preferences.auto_categorization_enabled:
            return None, 0.0
        
        # Try ML model first
        ml_suggestion = self._ml_suggest_category(user_id, entry_data)
        if ml_suggestion[0] is not None and ml_suggestion[1] >= preferences.min_confidence_threshold:
            return ml_suggestion
        
        # Fallback to rule-based system if ML doesn't provide confident suggestion
        rule_suggestion = self._rule_based_suggest_category(user_id, entry_data)
        
        # Return whichever has higher confidence
        if ml_suggestion[1] > rule_suggestion[1]:
            return ml_suggestion
        else:
            return rule_suggestion
    
    def _ml_suggest_category(self, user_id: int, entry_data: Dict) -> Tuple[Optional[int], float]:
        """
        ML-powered category suggestion
        
        Args:
            user_id: User ID
            entry_data: Dictionary with entry details
        
        Returns:
            Tuple of (category_id, confidence_score)
        """
        try:
            # Load user's ML model if not already loaded
            if self.ml_model is None:
                self.ml_model = CategorizationModel()

            # Try to load trained model for this user from database
            if not self.ml_model.is_trained:
                if not self.ml_model.load_model_from_db(user_id, self.db):
                    # No trained model available in database
                    return None, 0.0
            
            # Extract features for prediction
            from app.models.entry import Entry
            
            # Create a temporary Entry-like object to extract features
            temp_entry = type('obj', (object,), {
                'note': entry_data.get('note', ''),
                'description': entry_data.get('description', ''),
                'amount': entry_data.get('amount', 0),
                'type': entry_data.get('type', 'expense'),
                'date': entry_data.get('date', datetime.now().date())
            })()
            
            # Extract features using pipeline
            features = self.training_pipeline.extract_features(temp_entry)
            
            # Get prediction
            category_id, confidence = self.ml_model.predict(features)
            
            return category_id, confidence
            
        except Exception as e:
            print(f"Error in ML prediction: {e}")
            return None, 0.0
    
    def _rule_based_suggest_category(self, user_id: int, entry_data: Dict) -> Tuple[Optional[int], float]:
        """
        Rule-based category suggestion (fallback)
        
        Args:
            user_id: User ID
            entry_data: Dictionary with entry details
        
        Returns:
            Tuple of (category_id, confidence_score)
        """
        preferences = self.get_user_ai_preferences(user_id)
        
        # Extract text for analysis
        text_content = self._extract_text_content(entry_data)
        if not text_content:
            return None, 0.0
        
        # Get user's categories
        categories = self.db.query(Category).filter(Category.user_id == user_id).all()
        if not categories:
            return None, 0.0
        
        # Analyze patterns using multiple methods
        suggestions = []
        
        # Method 1: Exact text matching
        exact_match = self._exact_text_match(text_content, categories, user_id)
        if exact_match:
            suggestions.append((exact_match[0], exact_match[1] * 0.9))
        
        # Method 2: Keyword-based matching
        keyword_match = self._keyword_based_match(text_content, categories, user_id)
        if keyword_match:
            suggestions.append((keyword_match[0], keyword_match[1] * 0.8))
        
        # Method 3: Amount-based patterns
        amount_match = self._amount_based_patterns(entry_data.get('amount', 0), categories, user_id)
        if amount_match:
            suggestions.append((amount_match[0], amount_match[1] * 0.6))
        
        # Method 4: Historical frequency analysis
        frequency_match = self._frequency_analysis(text_content, categories, user_id)
        if frequency_match:
            suggestions.append((frequency_match[0], frequency_match[1] * 0.7))
        
        if not suggestions:
            return None, 0.0
        
        # Return the best suggestion
        best_suggestion = max(suggestions, key=lambda x: x[1])
        return best_suggestion
    
    def _extract_text_content(self, entry_data: Dict) -> str:
        """Extract and clean text content from entry data"""
        text_parts = []
        
        if entry_data.get('note'):
            text_parts.append(entry_data['note'].lower().strip())
        
        if entry_data.get('description'):
            text_parts.append(entry_data['description'].lower().strip())
        
        return ' '.join(text_parts)
    
    def _exact_text_match(self, text: str, categories: List[Category], user_id: int) -> Optional[Tuple[int, float]]:
        """Find exact text matches in historical data"""
        if not text:
            return None
        
        # Look for entries with similar text
        similar_entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.isnot(None),
            func.lower(Entry.note).like(f'%{text}%')
        ).limit(10).all()
        
        if similar_entries:
            # Count category frequency
            category_counts = {}
            for entry in similar_entries:
                cat_id = entry.category_id
                if cat_id:
                    category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
            
            if category_counts:
                best_category = max(category_counts.items(), key=lambda x: x[1])
                confidence = min(0.95, 0.7 + (best_category[1] * 0.05))
                return best_category
        
        return None
    
    def _keyword_based_match(self, text: str, categories: List[Category], user_id: int) -> Optional[Tuple[int, float]]:
        """Match based on keywords and patterns"""
        if not text:
            return None
        
        # Define keyword mappings
        keyword_mappings = {
            'food': ['restaurant', 'cafe', 'coffee', 'lunch', 'dinner', 'breakfast', 'food', 'meal', 'eat'],
            'transport': ['uber', 'taxi', 'bus', 'train', 'metro', 'gas', 'fuel', 'parking', 'transport'],
            'shopping': ['amazon', 'store', 'shop', 'mall', 'buy', 'purchase', 'online'],
            'entertainment': ['movie', 'cinema', 'game', 'netflix', 'spotify', 'entertainment', 'fun'],
            'health': ['doctor', 'pharmacy', 'medicine', 'health', 'medical', 'hospital'],
            'utilities': ['electric', 'water', 'internet', 'phone', 'utility', 'bill'],
            'income': ['salary', 'paycheck', 'bonus', 'income', 'work', 'job']
        }
        
        # Find matching keywords
        matched_categories = {}
        for category in categories:
            category_name_lower = category.name.lower()
            
            # Check if category name appears in text
            if category_name_lower in text:
                matched_categories[category.id] = 0.9
            
            # Check keyword mappings
            for keyword_type, keywords in keyword_mappings.items():
                if keyword_type in category_name_lower:
                    for keyword in keywords:
                        if keyword in text:
                            confidence = 0.8 if keyword in category_name_lower else 0.7
                            if category.id not in matched_categories or matched_categories[category.id] < confidence:
                                matched_categories[category.id] = confidence
        
        if matched_categories:
            best_match = max(matched_categories.items(), key=lambda x: x[1])
            return best_match
        
        return None
    
    def _amount_based_patterns(self, amount: float, categories: List[Category], user_id: int) -> Optional[Tuple[int, float]]:
        """Match based on amount patterns"""
        if amount <= 0:
            return None
        
        # Get entries with similar amounts (±20%)
        amount_range = (amount * 0.8, amount * 1.2)
        
        similar_entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.isnot(None),
            Entry.amount.between(amount_range[0], amount_range[1])
        ).limit(20).all()
        
        if similar_entries:
            category_counts = {}
            for entry in similar_entries:
                cat_id = entry.category_id
                if cat_id:
                    category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
            
            if category_counts:
                best_category = max(category_counts.items(), key=lambda x: x[1])
                confidence = min(0.8, 0.5 + (best_category[1] * 0.05))
                return best_category
        
        return None
    
    def _frequency_analysis(self, text: str, categories: List[Category], user_id: int) -> Optional[Tuple[int, float]]:
        """Analyze frequency of category usage for similar entries"""
        if not text:
            return None
        
        # Get recent entries (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.isnot(None),
            Entry.date >= thirty_days_ago.date()
        ).all()
        
        if not recent_entries:
            return None
        
        # Count category frequency
        category_counts = {}
        for entry in recent_entries:
            cat_id = entry.category_id
            if cat_id:
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
        
        if category_counts:
            # Find most frequently used category
            most_used = max(category_counts.items(), key=lambda x: x[1])
            total_entries = len(recent_entries)
            frequency_ratio = most_used[1] / total_entries
            
            # Base confidence on frequency
            confidence = min(0.6, 0.3 + (frequency_ratio * 0.5))
            return most_used[0], confidence
        
        return None
    
    def create_suggestion(self, user_id: int, entry_id: Optional[int], 
                         suggested_category_id: int, confidence_score: float,
                         suggestion_data: Optional[Dict] = None) -> AISuggestion:
        """Create a new AI suggestion record"""
        suggestion = AISuggestion(
            user_id=user_id,
            entry_id=entry_id,
            suggested_category_id=suggested_category_id,
            suggestion_type="category",
            confidence_score=confidence_score,
            suggestion_data=json.dumps(suggestion_data) if suggestion_data else None,
            is_accepted=None  # Pending
        )
        
        self.db.add(suggestion)
        self.db.commit()
        return suggestion
    
    def record_feedback(self, suggestion_id: int, is_accepted: bool) -> bool:
        """Record user feedback on AI suggestions"""
        suggestion = self.db.query(AISuggestion).filter(
            AISuggestion.id == suggestion_id
        ).first()
        
        if suggestion:
            suggestion.is_accepted = is_accepted
            suggestion.feedback_updated_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def train_user_model(self, user_id: int) -> Dict:
        """
        Train ML model for a specific user
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with training results and metrics
        """
        try:
            # Check if user has enough data
            stats = self.training_pipeline.get_training_stats(user_id)
            
            if not stats['is_ready_for_training']:
                return {
                    'success': False,
                    'message': f"Need at least {stats['min_samples_required']} categorized entries. You have {stats['total_categorized']}.",
                    'stats': stats
                }
            
            # Prepare training data (filters out rare categories)
            features_df, labels = self.training_pipeline.prepare_training_data(
                user_id, 
                min_samples=50,
                min_samples_per_category=3  # Need at least 3 samples per category
            )
            
            # Train model
            model = CategorizationModel()
            training_results = model.train(features_df, labels)

            # Add data quality warnings to results
            if training_results['accuracy'] < 0.60:
                training_results['warning'] = (
                    "Low accuracy detected. Model may not predict well. "
                    "Consider: 1) Adding more transactions, "
                    "2) Reducing number of categories, "
                    "3) Ensuring each category has 10+ examples"
                )

            # Save model to database (new method for Railway persistence)
            model.save_model_to_db(user_id, self.db)

            # Note: The save_model_to_db() method already creates/updates the AIModel record,
            # so we don't need the duplicate code below anymore.
            # The model metadata (accuracy, training_data_count, last_trained) is now
            # automatically saved within save_model_to_db().

            training_results['model_saved'] = 'database'
            training_results['persistence'] = 'persistent_across_restarts'

            # Old file-based save (kept for backward compatibility in development)
            # model_path = model.save_model(user_id)

            self.db.commit()

            return {
                'success': True,
                'message': 'Model trained successfully!',
                'results': training_results,
                'model_location': 'database'
            }
            
        except Exception as e:
            print(f"Error training model: {e}")
            return {
                'success': False,
                'message': f"Training failed: {str(e)}",
                'error': str(e)
            }
    
    def get_model_status(self, user_id: int) -> Dict:
        """
        Get status of user's ML model
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with model status information
        """
        # Get training data stats
        stats = self.training_pipeline.get_training_stats(user_id)
        
        # Get model info from database
        ai_model = self.db.query(AIModel).filter(
            AIModel.user_id == user_id,
            AIModel.model_type == "categorization"
        ).first()
        
        if ai_model:
            model_info = {
                'has_model': True,
                'is_active': ai_model.is_active,
                'accuracy': float(ai_model.accuracy_score) if ai_model.accuracy_score else 0.0,
                'training_data_count': ai_model.training_data_count,
                'last_trained': ai_model.last_trained.isoformat() if ai_model.last_trained else None,
                'last_trained_ago': self._time_ago(ai_model.last_trained) if ai_model.last_trained else None
            }
        else:
            model_info = {
                'has_model': False,
                'is_active': False,
                'accuracy': 0.0,
                'training_data_count': 0,
                'last_trained': None,
                'last_trained_ago': None
            }
        
        return {
            **model_info,
            'training_stats': stats,
            'can_train': stats['is_ready_for_training'],
            'needs_retraining': self._needs_retraining(ai_model, stats) if ai_model else True
        }
    
    def _needs_retraining(self, ai_model: AIModel, stats: Dict) -> bool:
        """Check if model needs retraining based on user preferences and data changes"""
        if not ai_model or not ai_model.last_trained:
            return True

        # Get user's retrain frequency preference
        preferences = self.get_user_ai_preferences(ai_model.user_id)
        retrain_frequency_days = preferences.retrain_frequency_days if preferences else 7

        # Check if it's been longer than user's preferred frequency since last training
        days_since_training = (datetime.utcnow() - ai_model.last_trained).days
        if days_since_training >= retrain_frequency_days:
            return True

        # Check if there's significantly more data now (20% increase triggers retraining)
        current_data_count = stats['total_categorized']
        trained_data_count = ai_model.training_data_count

        if current_data_count > trained_data_count * 1.2:  # 20% more data
            return True

        return False
    
    def _time_ago(self, dt: datetime) -> str:
        """Convert datetime to human-readable time ago string"""
        if not dt:
            return "Never"
        
        delta = datetime.utcnow() - dt
        
        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def get_smart_insights(self, user_id: int) -> Dict:
        """Generate smart insights for the user"""
        preferences = self.get_user_ai_preferences(user_id)
        if not preferences.spending_insights_enabled:
            return {}
        
        insights = {}
        
        # Get recent spending patterns
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_expenses = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= thirty_days_ago.date()
        ).all()
        
        if recent_expenses:
            # Category spending analysis
            category_spending = {}
            total_spent = 0
            
            for entry in recent_expenses:
                cat_name = entry.category.name if entry.category else "Uncategorized"
                amount = float(entry.amount)
                
                if cat_name not in category_spending:
                    category_spending[cat_name] = 0
                category_spending[cat_name] += amount
                total_spent += amount
            
            # Find top spending category
            if category_spending:
                top_category = max(category_spending.items(), key=lambda x: x[1])
                insights['top_spending_category'] = {
                    'name': top_category[0],
                    'amount': top_category[1],
                    'percentage': (top_category[1] / total_spent) * 100
                }
            
            # Daily average spending
            days_count = (datetime.now() - thirty_days_ago).days
            insights['daily_average'] = total_spent / days_count if days_count > 0 else 0
        
        return insights
