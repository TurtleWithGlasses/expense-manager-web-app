"""Machine Learning Model for Transaction Categorization"""

import joblib
import io
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from typing import Tuple, Optional, Dict, List
import pandas as pd
from datetime import datetime


class CategorizationModel:
    """
    Random Forest-based categorization model for financial transactions
    
    Features:
    - TF-IDF vectorization for text features
    - Numerical feature scaling
    - Random Forest classifier
    - Model persistence (save/load)
    - Per-user model training
    """
    
    def __init__(self):
        """Initialize the categorization model with default parameters"""
        self.model = RandomForestClassifier(
            n_estimators=100,          # Number of trees in the forest
            max_depth=15,              # Maximum depth of trees
            min_samples_split=5,       # Minimum samples required to split
            min_samples_leaf=2,        # Minimum samples required at leaf
            max_features='sqrt',       # Number of features to consider for split
            random_state=42,
            n_jobs=-1                  # Use all CPU cores
        )
        
        self.text_vectorizer = TfidfVectorizer(
            max_features=500,          # Limit to top 500 features
            ngram_range=(1, 2),        # Unigrams and bigrams
            stop_words='english',      # Remove common English words
            min_df=2,                  # Ignore terms that appear in < 2 documents
            max_df=0.8                 # Ignore terms that appear in > 80% of documents
        )
        
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        self.is_trained = False
        self.accuracy = 0.0
        self.cv_scores = []
        self.feature_importances = {}
        self.training_date = None
        self.n_training_samples = 0
    
    def train(self, features_df: pd.DataFrame, labels: List[int], test_size: float = 0.2) -> Dict:
        """
        Train the categorization model on user's historical data
        
        Args:
            features_df: DataFrame with extracted features (from TrainingDataPipeline)
            labels: List of category IDs (target variable)
            test_size: Proportion of data to use for testing (default 0.2)
        
        Returns:
            Dictionary with training metrics and results
        """
        print(f"Starting model training with {len(features_df)} samples...")
        
        # Validate input
        if len(features_df) < 10:
            raise ValueError("Need at least 10 samples for training")
        
        if len(set(labels)) < 2:
            raise ValueError("Need at least 2 different categories for training")
        
        # Encode labels
        y = self.label_encoder.fit_transform(labels)
        print(f"Found {len(self.label_encoder.classes_)} unique categories")
        
        # Process text features with TF-IDF
        print("Vectorizing text features...")
        X_text = self.text_vectorizer.fit_transform(features_df['text'])
        
        # Process numeric features
        numeric_features = [
            'amount_log', 'weekday', 'month', 'day',
            'is_weekend', 'is_month_start', 'is_month_end'
        ]
        
        print("Scaling numeric features...")
        X_numeric = self.scaler.fit_transform(features_df[numeric_features])
        
        # Combine text and numeric features
        X_combined = np.hstack([X_text.toarray(), X_numeric])
        print(f"Combined feature matrix shape: {X_combined.shape}")
        
        # Split into train/test sets with stratification
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X_combined, y,
                test_size=test_size,
                random_state=42,
                stratify=y
            )
        except ValueError:
            # Fallback if stratification fails (too few samples in some classes)
            X_train, X_test, y_train, y_test = train_test_split(
                X_combined, y,
                test_size=test_size,
                random_state=42
            )
        
        print(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
        
        # Train the model
        print("Training Random Forest model...")
        self.model.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation (if we have enough samples)
        if len(X_train) >= 10:
            print("Performing cross-validation...")
            cv_scores = cross_val_score(
                self.model, X_train, y_train,
                cv=min(5, len(X_train) // 2),  # Use fewer folds if limited data
                scoring='accuracy'
            )
            self.cv_scores = cv_scores.tolist()
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
        else:
            self.cv_scores = []
            cv_mean = test_accuracy
            cv_std = 0.0
        
        # Feature importance
        feature_names = (
            self.text_vectorizer.get_feature_names_out().tolist() +
            numeric_features
        )
        importances = self.model.feature_importances_
        
        # Get top 20 most important features
        top_indices = np.argsort(importances)[-20:][::-1]
        self.feature_importances = {
            feature_names[i]: float(importances[i])
            for i in top_indices
        }
        
        # Mark as trained
        self.is_trained = True
        self.accuracy = test_accuracy
        self.training_date = datetime.utcnow()
        self.n_training_samples = len(X_train)
        
        print(f"✅ Training complete! Test accuracy: {test_accuracy:.2%}")
        
        # Generate classification report
        # Only use labels that actually appear in y_test to avoid mismatch errors
        unique_test_labels = np.unique(y_test)
        test_category_names = self.label_encoder.inverse_transform(unique_test_labels)
        
        try:
            class_report = classification_report(
                y_test, y_pred,
                labels=unique_test_labels,
                target_names=[str(cat) for cat in test_category_names],
                output_dict=True,
                zero_division=0
            )
        except Exception as e:
            print(f"⚠️  Could not generate detailed classification report: {e}")
            class_report = {
                'accuracy': float(test_accuracy),
                'note': 'Detailed metrics unavailable'
            }
        
        return {
            'accuracy': float(test_accuracy),
            'cv_mean': float(cv_mean),
            'cv_std': float(cv_std),
            'cv_scores': self.cv_scores,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'n_categories': len(self.label_encoder.classes_),
            'categories': self.label_encoder.classes_.tolist(),
            'feature_importances': self.feature_importances,
            'classification_report': class_report,
            'training_date': self.training_date.isoformat() if self.training_date else None
        }
    
    def predict(self, entry_data: Dict) -> Tuple[Optional[int], float]:
        """
        Predict category for a new transaction
        
        Args:
            entry_data: Dictionary with entry features (from extract_features)
        
        Returns:
            Tuple of (predicted_category_id, confidence_score)
            Returns (None, 0.0) if model is not trained
        """
        if not self.is_trained:
            return None, 0.0
        
        try:
            # Extract text feature
            text = entry_data.get('text', '')
            X_text = self.text_vectorizer.transform([text])
            
            # Extract numeric features (in same order as training)
            numeric_values = [
                entry_data.get('amount_log', 0),
                entry_data.get('weekday', 0),
                entry_data.get('month', 1),
                entry_data.get('day', 1),
                entry_data.get('is_weekend', 0),
                entry_data.get('is_month_start', 0),
                entry_data.get('is_month_end', 0)
            ]
            X_numeric = self.scaler.transform([numeric_values])
            
            # Combine features
            X_combined = np.hstack([X_text.toarray(), X_numeric])
            
            # Get prediction
            prediction = self.model.predict(X_combined)[0]
            probabilities = self.model.predict_proba(X_combined)[0]
            confidence = float(np.max(probabilities))
            
            # Decode label back to original category ID
            category_id = int(self.label_encoder.inverse_transform([prediction])[0])
            
            return category_id, confidence
            
        except Exception as e:
            print(f"Error during prediction: {e}")
            return None, 0.0
    
    def predict_top_k(self, entry_data: Dict, k: int = 3) -> List[Tuple[int, float]]:
        """
        Predict top k categories with their probabilities
        
        Args:
            entry_data: Dictionary with entry features
            k: Number of top predictions to return
        
        Returns:
            List of (category_id, probability) tuples, sorted by probability
        """
        if not self.is_trained:
            return []
        
        try:
            # Extract features (same as predict)
            text = entry_data.get('text', '')
            X_text = self.text_vectorizer.transform([text])
            
            numeric_values = [
                entry_data.get('amount_log', 0),
                entry_data.get('weekday', 0),
                entry_data.get('month', 1),
                entry_data.get('day', 1),
                entry_data.get('is_weekend', 0),
                entry_data.get('is_month_start', 0),
                entry_data.get('is_month_end', 0)
            ]
            X_numeric = self.scaler.transform([numeric_values])
            X_combined = np.hstack([X_text.toarray(), X_numeric])
            
            # Get probabilities for all classes
            probabilities = self.model.predict_proba(X_combined)[0]
            
            # Get top k predictions
            top_k_indices = np.argsort(probabilities)[-k:][::-1]
            
            results = []
            for idx in top_k_indices:
                category_id = int(self.label_encoder.inverse_transform([idx])[0])
                probability = float(probabilities[idx])
                results.append((category_id, probability))
            
            return results
            
        except Exception as e:
            print(f"Error during top-k prediction: {e}")
            return []
    
    def save_model_to_db(self, user_id: int, db) -> bytes:
        """
        Save trained model to database as serialized bytes

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Serialized model as bytes
        """
        from app.models.ai_model import AIModel

        # Package all model components
        model_data = {
            'model': self.model,
            'text_vectorizer': self.text_vectorizer,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'accuracy': self.accuracy,
            'cv_scores': self.cv_scores,
            'feature_importances': self.feature_importances,
            'is_trained': self.is_trained,
            'training_date': self.training_date,
            'n_training_samples': self.n_training_samples
        }

        # Serialize to bytes
        buffer = io.BytesIO()
        joblib.dump(model_data, buffer)
        model_blob = buffer.getvalue()

        # Save or update in database
        ai_model = db.query(AIModel).filter(
            AIModel.user_id == user_id,
            AIModel.model_name == "categorization_v1"
        ).first()

        if ai_model:
            # Update existing model
            ai_model.model_blob = model_blob
            ai_model.accuracy_score = self.accuracy
            ai_model.training_data_count = self.n_training_samples
            ai_model.last_trained = datetime.utcnow()
        else:
            # Create new model record
            ai_model = AIModel(
                user_id=user_id,
                model_name="categorization_v1",
                model_type="classification",
                model_blob=model_blob,
                accuracy_score=self.accuracy,
                training_data_count=self.n_training_samples,
                last_trained=datetime.utcnow(),
                is_active=True
            )
            db.add(ai_model)

        db.commit()
        print(f"✅ Model saved to database for user {user_id}")
        print(f"   Accuracy: {self.accuracy:.2%}, Trained on: {self.n_training_samples} samples")
        print(f"   Model size: {len(model_blob) / 1024:.2f} KB")
        return model_blob

    def save_model(self, user_id: int, model_dir: str = "models") -> str:
        """
        DEPRECATED: Save trained model to disk (legacy method)
        Use save_model_to_db() for production deployments

        Args:
            user_id: User ID (used in filename)
            model_dir: Directory to save model in

        Returns:
            Path to saved model file
        """
        # Create directory if it doesn't exist
        Path(model_dir).mkdir(parents=True, exist_ok=True)

        # Package all model components
        model_data = {
            'model': self.model,
            'text_vectorizer': self.text_vectorizer,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'accuracy': self.accuracy,
            'cv_scores': self.cv_scores,
            'feature_importances': self.feature_importances,
            'is_trained': self.is_trained,
            'training_date': self.training_date,
            'n_training_samples': self.n_training_samples
        }

        # Save to file
        filepath = Path(model_dir) / f"user_{user_id}_model.joblib"
        joblib.dump(model_data, filepath)

        print(f"✅ Model saved to: {filepath}")
        return str(filepath)
    
    def load_model_from_db(self, user_id: int, db) -> bool:
        """
        Load trained model from database

        Args:
            user_id: User ID
            db: Database session

        Returns:
            True if model loaded successfully, False otherwise
        """
        from app.models.ai_model import AIModel

        try:
            # Query for user's model
            ai_model = db.query(AIModel).filter(
                AIModel.user_id == user_id,
                AIModel.model_name == "categorization_v1",
                AIModel.is_active == True
            ).first()

            if not ai_model or not ai_model.model_blob:
                print(f"❌ No model found in database for user {user_id}")
                return False

            # Deserialize from bytes
            buffer = io.BytesIO(ai_model.model_blob)
            model_data = joblib.load(buffer)

            # Restore all model components
            self.model = model_data['model']
            self.text_vectorizer = model_data['text_vectorizer']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.accuracy = model_data.get('accuracy', 0.0)
            self.cv_scores = model_data.get('cv_scores', [])
            self.feature_importances = model_data.get('feature_importances', {})
            self.is_trained = model_data.get('is_trained', True)
            self.training_date = model_data.get('training_date')
            self.n_training_samples = model_data.get('n_training_samples', 0)

            print(f"✅ Model loaded from database for user {user_id}")
            print(f"   Accuracy: {self.accuracy:.2%}, Trained on: {self.n_training_samples} samples")
            print(f"   Model size: {len(ai_model.model_blob) / 1024:.2f} KB")
            return True

        except Exception as e:
            print(f"❌ Error loading model from database: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_model(self, user_id: int, model_dir: str = "models") -> bool:
        """
        DEPRECATED: Load trained model from disk (legacy method)
        Use load_model_from_db() for production deployments

        Args:
            user_id: User ID (used in filename)
            model_dir: Directory to load model from

        Returns:
            True if model loaded successfully, False otherwise
        """
        filepath = Path(model_dir) / f"user_{user_id}_model.joblib"

        if not filepath.exists():
            print(f"❌ Model file not found: {filepath}")
            return False

        try:
            model_data = joblib.load(filepath)

            # Restore all model components
            self.model = model_data['model']
            self.text_vectorizer = model_data['text_vectorizer']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.accuracy = model_data.get('accuracy', 0.0)
            self.cv_scores = model_data.get('cv_scores', [])
            self.feature_importances = model_data.get('feature_importances', {})
            self.is_trained = model_data.get('is_trained', True)
            self.training_date = model_data.get('training_date')
            self.n_training_samples = model_data.get('n_training_samples', 0)

            print(f"✅ Model loaded successfully from: {filepath}")
            print(f"   Accuracy: {self.accuracy:.2%}, Trained on: {self.n_training_samples} samples")
            return True

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """
        Get information about the current model
        
        Returns:
            Dictionary with model metadata
        """
        return {
            'is_trained': self.is_trained,
            'accuracy': self.accuracy,
            'cv_mean': np.mean(self.cv_scores) if self.cv_scores else 0.0,
            'cv_std': np.std(self.cv_scores) if self.cv_scores else 0.0,
            'n_categories': len(self.label_encoder.classes_) if self.is_trained else 0,
            'n_training_samples': self.n_training_samples,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'top_features': list(self.feature_importances.keys())[:10] if self.feature_importances else []
        }

