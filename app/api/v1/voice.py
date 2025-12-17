"""
Voice Command API endpoints

Endpoints for processing voice commands and executing actions.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.models.entry import Entry, EntryType
from app.models.category import Category
from app.services.voice_command_service import VoiceCommandService
from app.services.entries import create_entry
from app.services.user_preferences import user_preferences_service
from app.core.currency import currency_service


router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceCommandRequest(BaseModel):
    """Request model for voice command"""
    command: str


class VoiceCommandResponse(BaseModel):
    """Response model for voice command"""
    success: bool
    message: str
    intent: str
    confidence: float
    data: dict = {}


@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    request_data: VoiceCommandRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    """
    Process a voice command and execute the corresponding action.

    Supports commands like:
    - "Add expense 50 dollars for groceries"
    - "Add income 2000 dollars salary yesterday"
    - "Delete last entry"
    - "What's my total this month?"
    """
    # Parse the command
    voice_service = VoiceCommandService(db, user.id)
    parsed = voice_service.parse_command(request_data.command)

    if not parsed.get("success"):
        return VoiceCommandResponse(
            success=False,
            message=parsed.get("message", "Command not understood"),
            intent=parsed.get("intent", "unknown"),
            confidence=parsed.get("confidence", 0.0),
            data={}
        )

    intent = parsed["intent"]
    params = parsed.get("params", {})

    # Get user's currency for formatting messages
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    try:
        # Execute the command based on intent
        if intent == "add_expense" or intent == "add_income":
            result = await _execute_add_entry(db, user, params, request)
            # Format confirmation message with user's currency
            amount = params.get("amount", 0)
            formatted_amount = currency_service.format_amount(float(amount), user_currency)
            category = params.get("category", "Uncategorized")
            entry_date = params.get("date")
            date_str = entry_date.strftime('%Y-%m-%d') if entry_date else "today"
            entry_type = "expense" if intent == "add_expense" else "income"
            formatted_message = f"Add {formatted_amount} {entry_type} for {category} on {date_str}"
            
            return VoiceCommandResponse(
                success=True,
                message=formatted_message,
                intent=intent,
                confidence=parsed["confidence"],
                data=result
            )

        elif intent == "delete_entry":
            result = await _execute_delete_entry(db, user, params)
            return VoiceCommandResponse(
                success=True,
                message=parsed["message"],
                intent=intent,
                confidence=parsed["confidence"],
                data=result
            )

        elif intent == "edit_entry":
            result = await _execute_edit_entry(db, user, params)
            return VoiceCommandResponse(
                success=True,
                message=parsed["message"],
                intent=intent,
                confidence=parsed["confidence"],
                data=result
            )

        elif intent == "query":
            result = await _execute_query(db, user, params)
            return VoiceCommandResponse(
                success=True,
                message=result["message"],
                intent=intent,
                confidence=parsed["confidence"],
                data=result
            )

        elif intent == "create_category":
            result = await _execute_create_category(db, user, params)
            return VoiceCommandResponse(
                success=True,
                message=parsed["message"],
                intent=intent,
                confidence=parsed["confidence"],
                data=result
            )

        else:
            return VoiceCommandResponse(
                success=False,
                message="Command understood but not yet implemented",
                intent=intent,
                confidence=parsed["confidence"],
                data={}
            )

    except Exception as e:
        return VoiceCommandResponse(
            success=False,
            message=f"Error executing command: {str(e)}",
            intent=intent,
            confidence=0.0,
            data={}
        )


async def _execute_add_entry(db: Session, user: User, params: dict, request: Request) -> dict:
    """Execute add entry command"""
    # Find or create category
    category_name = params.get("category", "Uncategorized")
    category = db.query(Category).filter(
        and_(
            Category.user_id == user.id,
            func.lower(Category.name) == category_name.lower()
        )
    ).first()

    if not category:
        # Create new category
        category = Category(
            name=category_name.capitalize(),
            user_id=user.id,
            color="#6366f1"  # Default color
        )
        db.add(category)
        db.flush()

    # Get user's preferred currency
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    
    # Create the entry using existing service
    entry_data = {
        "amount": params["amount"],
        "type": params["type"].value,
        "category_id": category.id,
        "date": params["date"].isoformat(),
        "description": params.get("description", ""),
        "currency": user_currency
    }

    entry = create_entry(db, user.id, entry_data, request)

    return {
        "entry_id": entry.id,
        "amount": entry.amount,
        "type": entry.type.value,
        "category": category.name,
        "date": entry.date.isoformat(),
        "description": entry.description
    }


async def _execute_delete_entry(db: Session, user: User, params: dict) -> dict:
    """Execute delete entry command"""
    if params.get("target") == "last":
        # Get last entry
        last_entry = db.query(Entry).filter(
            Entry.user_id == user.id
        ).order_by(Entry.date.desc(), Entry.id.desc()).first()

        if not last_entry:
            raise HTTPException(status_code=404, detail="No entries found to delete")

        entry_info = {
            "entry_id": last_entry.id,
            "amount": last_entry.amount,
            "type": last_entry.type.value,
            "date": last_entry.date.isoformat()
        }

        db.delete(last_entry)
        db.commit()

        return entry_info
    else:
        raise HTTPException(status_code=400, detail="Only deleting last entry is supported")


async def _execute_edit_entry(db: Session, user: User, params: dict) -> dict:
    """Execute edit entry command"""
    if params.get("target") == "last":
        # Get last entry
        last_entry = db.query(Entry).filter(
            Entry.user_id == user.id
        ).order_by(Entry.date.desc(), Entry.id.desc()).first()

        if not last_entry:
            raise HTTPException(status_code=404, detail="No entries found to edit")

        # Update amount if provided
        if "new_amount" in params:
            last_entry.amount = params["new_amount"]

        # Update category if provided
        if "new_category" in params:
            category_name = params["new_category"]
            category = db.query(Category).filter(
                and_(
                    Category.user_id == user.id,
                    func.lower(Category.name) == category_name.lower()
                )
            ).first()

            if category:
                last_entry.category_id = category.id

        db.commit()
        db.refresh(last_entry)

        return {
            "entry_id": last_entry.id,
            "amount": last_entry.amount,
            "type": last_entry.type.value,
            "category_id": last_entry.category_id,
            "date": last_entry.date.isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Only editing last entry is supported")


async def _execute_query(db: Session, user: User, params: dict) -> dict:
    """Execute query command"""
    query_type = params.get("query_type", "total")
    period = params.get("period", "this_month")
    category_name = params.get("category")

    # Get user's preferred currency for formatting
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    # Determine date range based on period
    today = datetime.now().date()
    if period == "today":
        start_date = today
        end_date = today
    elif period == "this_week":
        # Start of week (Monday)
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "this_month":
        start_date = today.replace(day=1)
        end_date = today
    elif period == "this_year":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = today.replace(day=1)
        end_date = today

    # Build query
    query = db.query(Entry).filter(
        and_(
            Entry.user_id == user.id,
            Entry.date >= start_date,
            Entry.date <= end_date
        )
    )

    # Filter by category if specified
    if category_name:
        category = db.query(Category).filter(
            and_(
                Category.user_id == user.id,
                func.lower(Category.name) == category_name.lower()
            )
        ).first()
        if category:
            query = query.filter(Entry.category_id == category.id)

    # Calculate totals based on query type
    if query_type == "expenses":
        total = query.filter(Entry.type == EntryType.EXPENSE).with_entities(
            func.sum(Entry.amount)
        ).scalar() or 0
        formatted_total = currency_service.format_amount(float(total), user_currency)
        message = f"You spent {formatted_total}"
    elif query_type == "income":
        total = query.filter(Entry.type == EntryType.INCOME).with_entities(
            func.sum(Entry.amount)
        ).scalar() or 0
        formatted_total = currency_service.format_amount(float(total), user_currency)
        message = f"You earned {formatted_total}"
    elif query_type == "balance":
        income = query.filter(Entry.type == EntryType.INCOME).with_entities(
            func.sum(Entry.amount)
        ).scalar() or 0
        expenses = query.filter(Entry.type == EntryType.EXPENSE).with_entities(
            func.sum(Entry.amount)
        ).scalar() or 0
        total = income - expenses
        formatted_total = currency_service.format_amount(float(total), user_currency)
        message = f"Your balance is {formatted_total}"
    else:  # total
        income = query.filter(Entry.type == EntryType.INCOME).with_entities(
            func.sum(Entry.amount)
        ).scalar() or 0
        expenses = query.filter(Entry.type == EntryType.EXPENSE).with_entities(
            func.sum(Entry.amount)
        ).scalar() or 0
        total = income - expenses
        formatted_income = currency_service.format_amount(float(income), user_currency)
        formatted_expenses = currency_service.format_amount(float(expenses), user_currency)
        formatted_total = currency_service.format_amount(float(total), user_currency)
        message = f"Income: {formatted_income}, Expenses: {formatted_expenses}, Balance: {formatted_total}"

    # Add period and category to message
    period_text = period.replace("_", " ")
    message += f" {period_text}"
    if category_name:
        message += f" for {category_name}"

    return {
        "query_type": query_type,
        "period": period,
        "category": category_name,
        "total": float(total) if query_type != "total" else float(income - expenses),
        "income": float(income) if query_type == "total" or query_type == "balance" else None,
        "expenses": float(expenses) if query_type == "total" or query_type == "balance" else None,
        "message": message
    }


async def _execute_create_category(db: Session, user: User, params: dict) -> dict:
    """Execute create category command"""
    category_name = params["name"]

    # Check if category already exists
    existing = db.query(Category).filter(
        and_(
            Category.user_id == user.id,
            func.lower(Category.name) == category_name.lower()
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Category '{category_name}' already exists")

    # Create new category
    category = Category(
        name=category_name.capitalize(),
        user_id=user.id,
        color="#6366f1"  # Default color
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "category_id": category.id,
        "name": category.name,
        "color": category.color
    }
