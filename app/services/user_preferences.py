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

# Global service instance
user_preferences_service = UserPreferencesService()