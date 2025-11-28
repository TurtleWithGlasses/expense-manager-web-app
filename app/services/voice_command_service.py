"""
Voice Command Service - NLP parser for voice commands

Parses natural language voice commands and extracts structured data:
- Intent (add, delete, edit, query)
- Entry type (expense, income)
- Amount (dollars, euros, etc.)
- Category (groceries, salary, etc.)
- Date (today, yesterday, last Monday, etc.)
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.entry import Entry, EntryType
from app.models.category import Category


class VoiceCommandService:
    """Service for parsing and executing voice commands"""

    # Number word mappings
    NUMBER_WORDS = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000
    }

    # Day of week mappings
    WEEKDAYS = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def parse_command(self, command_text: str) -> Dict[str, Any]:
        """
        Parse voice command text and extract structured data.

        Args:
            command_text: Raw voice command text

        Returns:
            Dict with intent, parameters, and confidence
        """
        command_lower = command_text.lower().strip()

        # Determine intent
        intent = self._get_intent(command_lower)

        if intent == "add_expense":
            return self._parse_add_expense(command_lower, command_text)
        elif intent == "add_income":
            return self._parse_add_income(command_lower, command_text)
        elif intent == "delete_entry":
            return self._parse_delete_entry(command_lower)
        elif intent == "edit_entry":
            return self._parse_edit_entry(command_lower)
        elif intent == "query":
            return self._parse_query(command_lower)
        elif intent == "create_category":
            return self._parse_create_category(command_lower, command_text)
        else:
            return {
                "intent": "unknown",
                "success": False,
                "message": "I didn't understand that command. Try 'add expense 50 dollars for groceries'",
                "confidence": 0.0
            }

    def _get_intent(self, text: str) -> str:
        """Determine the intent/action from command text"""
        # Add expense patterns
        if re.search(r'\b(add|create|spent|paid|bought)\b.*\b(expense|on|for)\b', text):
            return "add_expense"
        if re.search(r'\b(spent|paid|bought)\b', text) and not re.search(r'\b(income|earned|received)\b', text):
            return "add_expense"

        # Add income patterns
        if re.search(r'\b(add|create|earned|received|got)\b.*\b(income|salary|from)\b', text):
            return "add_income"
        if re.search(r'\b(earned|received)\b', text):
            return "add_income"

        # Delete patterns
        if re.search(r'\b(delete|remove|undo)\b.*\b(entry|expense|income|last|latest)\b', text):
            return "delete_entry"

        # Edit patterns
        if re.search(r'\b(edit|change|update|modify)\b.*\b(entry|expense|income|last|latest)\b', text):
            return "edit_entry"

        # Query patterns
        if re.search(r'\b(what|how much|show|tell|total|balance|spent)\b', text):
            return "query"

        # Create category
        if re.search(r'\b(create|add|new)\b.*\b(category)\b', text):
            return "create_category"

        return "unknown"

    def _parse_add_expense(self, text: str, original_text: str) -> Dict[str, Any]:
        """Parse add expense command"""
        # Extract amount
        amount = self._extract_amount(text)
        if not amount:
            return {
                "intent": "add_expense",
                "success": False,
                "message": "I couldn't find an amount. Try 'add expense 50 dollars for groceries'",
                "confidence": 0.3
            }

        # Extract category
        category = self._extract_category(text, original_text)

        # Extract date
        entry_date = self._extract_date(text)

        return {
            "intent": "add_expense",
            "success": True,
            "params": {
                "type": EntryType.EXPENSE,
                "amount": amount,
                "category": category,
                "date": entry_date,
                "description": f"Added via voice: {original_text[:100]}"
            },
            "message": f"Add ${amount:.2f} expense for {category} on {entry_date.strftime('%Y-%m-%d')}",
            "confidence": 0.85
        }

    def _parse_add_income(self, text: str, original_text: str) -> Dict[str, Any]:
        """Parse add income command"""
        amount = self._extract_amount(text)
        if not amount:
            return {
                "intent": "add_income",
                "success": False,
                "message": "I couldn't find an amount. Try 'add income 2000 dollars salary'",
                "confidence": 0.3
            }

        category = self._extract_category(text, original_text)
        entry_date = self._extract_date(text)

        return {
            "intent": "add_income",
            "success": True,
            "params": {
                "type": EntryType.INCOME,
                "amount": amount,
                "category": category,
                "date": entry_date,
                "description": f"Added via voice: {original_text[:100]}"
            },
            "message": f"Add ${amount:.2f} income for {category} on {entry_date.strftime('%Y-%m-%d')}",
            "confidence": 0.85
        }

    def _parse_delete_entry(self, text: str) -> Dict[str, Any]:
        """Parse delete entry command"""
        # For now, only support deleting last entry
        if re.search(r'\b(last|latest|recent)\b', text):
            return {
                "intent": "delete_entry",
                "success": True,
                "params": {
                    "target": "last"
                },
                "message": "Delete your last entry",
                "confidence": 0.9
            }

        return {
            "intent": "delete_entry",
            "success": False,
            "message": "I can only delete your last entry. Try 'delete last entry'",
            "confidence": 0.4
        }

    def _parse_edit_entry(self, text: str) -> Dict[str, Any]:
        """Parse edit entry command"""
        # Extract what to edit
        new_amount = self._extract_amount(text)
        new_category = None

        # Look for category change
        category_match = re.search(r'category\s+to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)', text)
        if category_match:
            new_category = category_match.group(1).strip()

        if new_amount:
            return {
                "intent": "edit_entry",
                "success": True,
                "params": {
                    "target": "last",
                    "new_amount": new_amount
                },
                "message": f"Update last entry amount to ${new_amount:.2f}",
                "confidence": 0.8
            }
        elif new_category:
            return {
                "intent": "edit_entry",
                "success": True,
                "params": {
                    "target": "last",
                    "new_category": new_category
                },
                "message": f"Update last entry category to {new_category}",
                "confidence": 0.8
            }

        return {
            "intent": "edit_entry",
            "success": False,
            "message": "I couldn't understand what to edit. Try 'edit last entry amount to 50 dollars'",
            "confidence": 0.3
        }

    def _parse_query(self, text: str) -> Dict[str, Any]:
        """Parse query/question command"""
        # Detect time period
        period = "this_month"  # default

        if re.search(r'\b(today|this day)\b', text):
            period = "today"
        elif re.search(r'\b(this week|past week)\b', text):
            period = "this_week"
        elif re.search(r'\b(this month|past month)\b', text):
            period = "this_month"
        elif re.search(r'\b(this year|past year)\b', text):
            period = "this_year"

        # Detect what to query
        query_type = "total"
        if re.search(r'\b(expense|spent|spending)\b', text):
            query_type = "expenses"
        elif re.search(r'\b(income|earned|revenue)\b', text):
            query_type = "income"
        elif re.search(r'\b(balance|net)\b', text):
            query_type = "balance"

        # Check for category filter
        category = None
        category_match = re.search(r'\bon\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)', text)
        if category_match:
            category = category_match.group(1).strip()

        return {
            "intent": "query",
            "success": True,
            "params": {
                "query_type": query_type,
                "period": period,
                "category": category
            },
            "message": f"Query {query_type} for {period}" + (f" in category {category}" if category else ""),
            "confidence": 0.75
        }

    def _parse_create_category(self, text: str, original_text: str) -> Dict[str, Any]:
        """Parse create category command"""
        # Extract category name
        category_match = re.search(r'category\s+(.+?)(?:\s+for|\s+in|$)', text)
        if category_match:
            category_name = category_match.group(1).strip()
            # Use original text for proper capitalization
            for word in original_text.split():
                if word.lower() == category_name.lower():
                    category_name = word
                    break

            return {
                "intent": "create_category",
                "success": True,
                "params": {
                    "name": category_name
                },
                "message": f"Create category '{category_name}'",
                "confidence": 0.85
            }

        return {
            "intent": "create_category",
            "success": False,
            "message": "I couldn't find the category name. Try 'create category Transportation'",
            "confidence": 0.3
        }

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text"""
        # Try numeric patterns first: $50, 50 dollars, 50.99, etc.
        patterns = [
            r'\$\s*(\d+(?:\.\d{2})?)',  # $50 or $50.99
            r'(\d+(?:\.\d{2})?)\s*(?:dollars?|usd|bucks?)',  # 50 dollars
            r'(\d+(?:\.\d{2})?)\s*(?:euros?|eur|€)',  # 50 euros
            r'(\d+(?:\.\d{2})?)\s*(?:pounds?|gbp|£)',  # 50 pounds
            r'\b(\d+(?:\.\d{2})?)\b',  # Just a number
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue

        # Try word numbers: "fifty dollars", "twenty five dollars"
        word_pattern = r'\b(' + '|'.join(self.NUMBER_WORDS.keys()) + r')\b'
        word_matches = re.findall(word_pattern, text)
        if word_matches:
            total = 0
            current = 0
            for word in word_matches:
                value = self.NUMBER_WORDS[word]
                if value >= 100:
                    current = current * value if current > 0 else value
                    total += current
                    current = 0
                else:
                    current += value
            total += current
            if total > 0:
                return float(total)

        return None

    def _extract_category(self, text: str, original_text: str) -> str:
        """Extract category name from text"""
        # Common patterns for category extraction
        patterns = [
            r'\bfor\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',  # "for groceries"
            r'\bon\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',   # "on groceries"
            r'\bcategory\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',  # "category groceries"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                category_lower = match.group(1).strip()
                # Find the word in original text to preserve capitalization
                for word in original_text.split():
                    if word.lower() == category_lower or category_lower in word.lower():
                        return word
                return category_lower.capitalize()

        # Default category
        return "Uncategorized"

    def _extract_date(self, text: str) -> date:
        """Extract date from text"""
        today = date.today()

        # Relative dates
        if re.search(r'\byesterday\b', text):
            return today - timedelta(days=1)

        if re.search(r'\btoday\b', text):
            return today

        if re.search(r'\btomorrow\b', text):
            return today + timedelta(days=1)

        # Last/this weekday: "last monday", "this friday"
        for day_name, day_num in self.WEEKDAYS.items():
            if re.search(rf'\blast\s+{day_name}\b', text):
                # Find last occurrence of this weekday
                days_ago = (today.weekday() - day_num) % 7
                if days_ago == 0:
                    days_ago = 7  # Last week's same day
                return today - timedelta(days=days_ago)

            if re.search(rf'\bthis\s+{day_name}\b', text):
                # Find this week's occurrence
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 0  # Today
                return today + timedelta(days=days_ahead)

        # Specific date patterns: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '-' in pattern:  # YYYY-MM-DD
                        year, month, day = match.groups()
                    else:  # MM/DD/YYYY
                        month, day, year = match.groups()
                    return date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    continue

        # Default to today
        return today
