from sqlalchemy.orm import Session
from app.models.user_preferences import UserPreferences
from app.core.currency import CURRENCIES, currency_service
from typing import Dict, Any

class UserPreferencesService:
    
    def get_user_preferences(self, db: Session, user_id: int) -> UserPreferences:
        """Get user preferences, create default if not exists"""
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            preferences = UserPreferences(
                user_id=user_id,
                currency_code='USD',
                preferences={}
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        
        return preferences
    
    def update_currency(self, db: Session, user_id: int, currency_code: str) -> UserPreferences:
        """Update user's preferred currency"""
        if currency_code not in CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency_code}")
        
        preferences = self.get_user_preferences(db, user_id)
        preferences.currency_code = currency_code
        db.commit()
        db.refresh(preferences)
        return preferences
    
    def get_user_currency(self, db: Session, user_id: int) -> str:
        """Get user's preferred currency code"""
        preferences = self.get_user_preferences(db, user_id)
        return preferences.currency_code
    
    async def convert_amounts_for_user(
        self, 
        db: Session, 
        user_id: int, 
        amounts: Dict[str, float],
        from_currency: str = 'USD'
    ) -> Dict[str, str]:
        """Convert amounts to user's preferred currency and format them"""
        user_currency = self.get_user_currency(db, user_id)
        converted_amounts = {}
        
        for key, amount in amounts.items():
            converted_amount = await currency_service.convert_amount(
                amount, from_currency, user_currency
            )
            converted_amounts[key] = currency_service.format_amount(
                converted_amount, user_currency
            )
        
        return converted_amounts
    
    async def convert_single_amount(
        self,
        db: Session,
        user_id: int,
        amount: float,
        from_currency: str = 'USD'
    ) -> tuple[float, str]:
        """Convert single amount and return both raw value and formatted string"""
        user_currency = self.get_user_currency(db, user_id)
        converted_amount = await currency_service.convert_amount(
            amount, from_currency, user_currency
        )
        formatted_amount = currency_service.format_amount(converted_amount, user_currency)
        return converted_amount, formatted_amount

    def get_sort_preference(self, db: Session, user_id: int, page: str) -> tuple[str, str]:
        """
        Get user's sort preference for a specific page (entries or dashboard).
        Returns (sort_by, order) tuple with defaults if not set.

        Args:
            db: Database session
            user_id: User ID
            page: Page identifier ('entries' or 'dashboard')

        Returns:
            Tuple of (sort_by, order) - e.g., ('date', 'desc')
        """
        preferences = self.get_user_preferences(db, user_id)
        sort_prefs = preferences.preferences.get('sort_preferences', {})
        page_prefs = sort_prefs.get(page, {})

        # Default to date descending (newest first)
        sort_by = page_prefs.get('sort_by', 'date')
        order = page_prefs.get('order', 'desc')

        return sort_by, order

    def save_sort_preference(self, db: Session, user_id: int, page: str, sort_by: str, order: str) -> None:
        """
        Save user's sort preference for a specific page.

        Args:
            db: Database session
            user_id: User ID
            page: Page identifier ('entries' or 'dashboard')
            sort_by: Sort field ('date', 'amount', 'category')
            order: Sort order ('asc' or 'desc')
        """
        preferences = self.get_user_preferences(db, user_id)

        # Initialize sort_preferences if it doesn't exist
        if not preferences.preferences:
            preferences.preferences = {}

        if 'sort_preferences' not in preferences.preferences:
            preferences.preferences['sort_preferences'] = {}

        # Save the preference for this page
        preferences.preferences['sort_preferences'][page] = {
            'sort_by': sort_by,
            'order': order
        }

        # Mark as modified for SQLAlchemy to detect JSON changes
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(preferences, 'preferences')

        db.commit()

# Global service instance
user_preferences_service = UserPreferencesService()