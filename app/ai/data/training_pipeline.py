"""Training Data Preparation Pipeline for ML Models"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.entry import Entry
from app.models.category import Category


class TrainingDataPipeline:
    """Pipeline for preparing training data from user's historical entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def prepare_training_data(self, user_id: int, min_samples: int = 50) -> Tuple[pd.DataFrame, List[int]]:
        """
        Prepare training data from user's historical entries
        
        Args:
            user_id: User ID to prepare data for
            min_samples: Minimum number of samples required for training
        
        Returns:
            Tuple of (features_df, labels) where:
            - features_df: DataFrame with extracted features
            - labels: List of category IDs (targets)
        
        Raises:
            ValueError: If insufficient training data available
        """
        # Get categorized entries for this user
        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.isnot(None)
        ).all()
        
        if len(entries) < min_samples:
            raise ValueError(
                f"Insufficient training data. Need at least {min_samples} categorized entries. "
                f"Found {len(entries)}. Please categorize more entries before training."
            )
        
        # Extract features and labels
        features_list = []
        labels = []
        
        for entry in entries:
            features = self.extract_features(entry)
            features_list.append(features)
            labels.append(entry.category_id)
        
        # Convert to DataFrame
        features_df = pd.DataFrame(features_list)
        
        return features_df, labels
    
    def extract_features(self, entry: Entry) -> Dict:
        """
        Extract ML features from a single entry
        
        Features extracted:
        - text: Combined note and description
        - amount: Raw amount value
        - amount_log: Log-transformed amount (handles large values better)
        - amount_rounded: Amount rounded to nearest 10
        - type: Entry type (income/expense)
        - weekday: Day of week (0=Monday, 6=Sunday)
        - month: Month of year (1-12)
        - day: Day of month (1-31)
        - is_weekend: Boolean indicator for weekend
        - is_month_start: Boolean indicator for first week of month
        - is_month_end: Boolean indicator for last week of month
        
        Args:
            entry: Entry model instance
        
        Returns:
            Dictionary of extracted features
        """
        # Text content - combine note and description
        text_parts = []
        if entry.note:
            text_parts.append(entry.note)
        if hasattr(entry, 'description') and entry.description:
            text_parts.append(entry.description)
        
        text = ' '.join(text_parts).lower().strip()
        
        # Date features
        weekday = entry.date.weekday()  # 0=Monday, 6=Sunday
        month = entry.date.month  # 1-12
        day = entry.date.day  # 1-31
        is_weekend = weekday >= 5
        is_month_start = day <= 7
        is_month_end = day >= 23
        
        # Amount features
        amount = float(entry.amount)
        amount_log = np.log1p(amount)  # log(1 + amount) - handles 0s and makes distribution more normal
        amount_rounded = round(amount, -1)  # Round to nearest 10
        
        # Amount range categories (helps with pattern recognition)
        if amount < 10:
            amount_range = 'micro'  # < $10
        elif amount < 50:
            amount_range = 'small'  # $10-50
        elif amount < 200:
            amount_range = 'medium'  # $50-200
        elif amount < 1000:
            amount_range = 'large'  # $200-1000
        else:
            amount_range = 'xlarge'  # > $1000
        
        return {
            'text': text,
            'amount': amount,
            'amount_log': amount_log,
            'amount_rounded': amount_rounded,
            'amount_range': amount_range,
            'type': entry.type,
            'weekday': weekday,
            'month': month,
            'day': day,
            'is_weekend': int(is_weekend),
            'is_month_start': int(is_month_start),
            'is_month_end': int(is_month_end)
        }
    
    def get_training_stats(self, user_id: int) -> Dict:
        """
        Get statistics about available training data
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with training data statistics
        """
        # Total categorized entries
        total_categorized = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.isnot(None)
        ).count()
        
        # Total uncategorized entries
        total_uncategorized = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.is_(None)
        ).count()
        
        # Category distribution
        category_counts = self.db.query(
            Category.name,
            Entry.category_id
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id
        ).all()
        
        # Count entries per category
        category_distribution = {}
        for cat_name, cat_id in category_counts:
            if cat_name not in category_distribution:
                category_distribution[cat_name] = 0
            category_distribution[cat_name] += 1
        
        # Check if ready for training
        is_ready = total_categorized >= 50
        
        return {
            'total_categorized': total_categorized,
            'total_uncategorized': total_uncategorized,
            'total_entries': total_categorized + total_uncategorized,
            'category_distribution': category_distribution,
            'unique_categories': len(category_distribution),
            'is_ready_for_training': is_ready,
            'min_samples_required': 50,
            'progress_percentage': min(100, (total_categorized / 50) * 100)
        }

