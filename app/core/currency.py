from typing import Dict, Optional
import httpx
from decimal import Decimal
from app.core.config import settings

CURRENCIES = {
    'USD': {'symbol': '$', 'name': 'US Dollar', 'decimal_places': 2, 'position': 'before'},
    'EUR': {'symbol': '€', 'name': 'Euro', 'decimal_places': 2, 'position': 'after'},
    'GBP': {'symbol': '£', 'name': 'British Pound', 'decimal_places': 2, 'position': 'before'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen', 'decimal_places': 0, 'position': 'before'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar', 'decimal_places': 2, 'position': 'before'},
    'AUD': {'symbol': 'A$', 'name': 'Australian Dollar', 'decimal_places': 2, 'position': 'before'},
    'CHF': {'symbol': 'Fr', 'name': 'Swiss Franc', 'decimal_places': 2, 'position': 'before'},
    'CNY': {'symbol': '¥', 'name': 'Chinese Yuan', 'decimal_places': 2, 'position': 'before'},
    'INR': {'symbol': '₹', 'name': 'Indian Rupee', 'decimal_places': 2, 'position': 'before'},
    'TRY': {'symbol': '₺', 'name': 'Turkish Lira', 'decimal_places': 2, 'position': 'before'},
    'BRL': {'symbol': 'R$', 'name': 'Brazilian Real', 'decimal_places': 2, 'position': 'before'},
    'MXN': {'symbol': '$', 'name': 'Mexican Peso', 'decimal_places': 2, 'position': 'before'},
    'KRW': {'symbol': '₩', 'name': 'South Korean Won', 'decimal_places': 0, 'position': 'before'},
    'RUB': {'symbol': '₽', 'name': 'Russian Ruble', 'decimal_places': 2, 'position': 'before'},
    'PHP': {'symbol': '₱', 'name': 'Philippine Peso', 'decimal_places': 2, 'position': 'before'},
    'MYR': {'symbol': 'RM', 'name': 'Malaysian Ringgit', 'decimal_places': 2, 'position': 'before'},
    'NZD': {'symbol': 'NZ$', 'name': 'New Zealand Dollar', 'decimal_places': 2, 'position': 'before'},
    'IDR': {'symbol': 'Rp', 'name': 'Indonesian Rupiah', 'decimal_places': 0, 'position': 'before'},
    'ZAR': {'symbol': 'R', 'name': 'South African Rand', 'decimal_places': 2, 'position': 'before'},
}

class CurrencyService:
    def __init__(self):
        self.base_currency = "USD"
        self._exchange_rates: Optional[Dict[str, float]] = None
    
    async def get_exchange_rates(self) -> Dict[str, float]:
        """Fetch current exchange rates from a free API"""
        if self._exchange_rates is not None:
            return self._exchange_rates
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}",
                    timeout = 5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    self._exchange_rates = data.get("rates", {})
                    self._exchange_rates[self.base_currency] = 1.0
                    return self._exchange_rates
                else:
                    return self._get_fallback_rates()
        except Exception:
            return self._get_fallback_rates()
    
    def _get_fallback_rates(self) -> Dict[str, float]:
        return {
            'USD': 1.0,
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0,
            'CAD': 1.25,
            'AUD': 1.35,
            'CHF': 0.92,
            'CNY': 6.45,
            'INR': 74.0,
            'TRY': 8.5,
            'BRL': 5.2,
            'MXN': 20.0,
            'KRW': 1180.0,
            'RUB': 75.0,
            'PHP': 50.0,
            'MYR': 4.2,
            'NZD': 1.42,
            'IDR': 14250.0,
            'ZAR': 15.0,
        }
    
    async def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount from one currency to another"""
        # Handle None or invalid amounts
        if amount is None:
            return 0.0
        
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return 0.0
        
        if from_currency == to_currency:
            return amount
        
        rates = await self.get_exchange_rates()
        
        # Convert to base currency (USD) first, then to target currency
        if from_currency != self.base_currency:
            from_rate = rates.get(from_currency, 1.0)
            if from_rate == 0:  # Avoid division by zero
                from_rate = 1.0
            amount_in_base = amount / from_rate
        else:
            amount_in_base = amount
        
        # Convert from base to target currency
        target_rate = rates.get(to_currency, 1.0)
        return amount_in_base * target_rate
    
    def format_amount(self, amount: float, currency_code: str) -> str:
        """Format amount with proper currency symbol and decimal places"""
        # Handle None or invalid amounts
        if amount is None:
            amount = 0.0
        
        # Ensure amount is a float
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0.0
        
        currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])
        
        decimal_places = currency_info['decimal_places']
        symbol = currency_info['symbol']
        position = currency_info['position']
        
        # Format the number
        if decimal_places == 0:
            formatted_amount = f"{amount:,.0f}"
        else:
            formatted_amount = f"{amount:,.{decimal_places}f}"
        
        # Add currency symbol
        if position == 'before':
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {symbol}"

currency_service = CurrencyService()


def get_currency_info(currency_code: str) -> Dict[str, str]:
    """
    Get currency information by currency code

    Args:
        currency_code: ISO currency code (e.g., 'USD', 'EUR', 'TRY')

    Returns:
        Dictionary containing currency symbol, name, decimal_places, and position
    """
    return CURRENCIES.get(currency_code, CURRENCIES['USD'])