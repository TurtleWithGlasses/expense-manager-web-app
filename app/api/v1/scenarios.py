"""
Scenario Planning API Endpoints

What-If Analysis and Financial Scenario Planning
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.deps import current_user
from app.services.scenario_service import ScenarioService


router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


# Pydantic schemas for request validation
class ScenarioCreate(BaseModel):
    """Request schema for creating a scenario"""
    name: str = Field(..., min_length=1, max_length=200, description="Scenario name")
    scenario_type: str = Field(..., description="Type: spending_reduction, income_increase, goal_based, category_adjustment")
    parameters: Dict[str, Any] = Field(..., description="Scenario-specific parameters")
    description: Optional[str] = Field(None, description="Optional description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Reduce dining out by 30%",
                "scenario_type": "spending_reduction",
                "parameters": {
                    "category_id": 5,
                    "reduction_percent": 30,
                    "duration_months": 6
                },
                "description": "Test reducing restaurant spending to save for vacation"
            }
        }


class ScenarioUpdate(BaseModel):
    """Request schema for updating a scenario"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_active: Optional[bool] = None


class ScenarioCompare(BaseModel):
    """Request schema for comparing scenarios"""
    scenario_ids: List[int] = Field(..., min_items=2, max_items=4, description="2-4 scenario IDs to compare")
    comparison_name: Optional[str] = Field(None, description="Optional name for saved comparison")
    save_comparison: bool = Field(False, description="Whether to save this comparison")

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_ids": [1, 2, 3],
                "comparison_name": "Vacation savings options",
                "save_comparison": True
            }
        }


@router.post("", response_model=Dict)
def create_scenario(
    scenario: ScenarioCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new financial scenario

    Supported scenario types:
    - **spending_reduction**: Reduce spending in a category
    - **income_increase**: Model additional income
    - **goal_based**: Plan to achieve a savings goal
    - **category_adjustment**: Adjust multiple categories

    Returns projected outcomes and AI insights.
    """
    service = ScenarioService(db)

    result = service.create_scenario(
        user_id=user.id,
        name=scenario.name,
        scenario_type=scenario.scenario_type,
        parameters=scenario.parameters,
        description=scenario.description
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.get("", response_model=List[Dict])
def get_scenarios(
    active_only: bool = Query(True, description="Only return active scenarios"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get all scenarios for the current user

    Query parameters:
    - **active_only**: If true, only returns active scenarios (default: true)

    Returns list of scenarios with projected outcomes.
    """
    service = ScenarioService(db)
    scenarios = service.get_user_scenarios(user.id, active_only=active_only)

    return scenarios


@router.get("/favorites", response_model=List[Dict])
def get_favorite_scenarios(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's favorite scenarios

    Returns only scenarios marked as favorites.
    """
    service = ScenarioService(db)
    all_scenarios = service.get_user_scenarios(user.id, active_only=True)

    # Filter favorites
    favorites = [s for s in all_scenarios if s.get('is_favorite', False)]

    return favorites


@router.get("/{scenario_id}", response_model=Dict)
def get_scenario(
    scenario_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific scenario by ID

    Returns full scenario details including projected outcome and timeline.
    """
    service = ScenarioService(db)
    scenario = service.get_scenario(scenario_id, user.id)

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return scenario


@router.put("/{scenario_id}", response_model=Dict)
def update_scenario(
    scenario_id: int,
    updates: ScenarioUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Update a scenario's metadata

    Can update:
    - name
    - description
    - is_favorite
    - is_active

    Cannot update scenario_type or parameters (create new scenario instead).
    """
    service = ScenarioService(db)

    # Convert to dict, removing None values
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}

    if not update_dict:
        raise HTTPException(status_code=400, detail="No updates provided")

    result = service.update_scenario(scenario_id, user.id, update_dict)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/{scenario_id}/favorite", response_model=Dict)
def toggle_favorite(
    scenario_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle a scenario's favorite status

    Toggles between favorite and not favorite.
    """
    service = ScenarioService(db)

    # Get current scenario
    scenario = service.get_scenario(scenario_id, user.id)

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Toggle favorite
    new_favorite_status = not scenario.get('is_favorite', False)

    result = service.update_scenario(
        scenario_id,
        user.id,
        {'is_favorite': new_favorite_status}
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return {
        'success': True,
        'is_favorite': new_favorite_status,
        'scenario': result['scenario']
    }


@router.delete("/{scenario_id}", response_model=Dict)
def delete_scenario(
    scenario_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a scenario

    Permanently removes the scenario and its data.
    """
    service = ScenarioService(db)
    result = service.delete_scenario(scenario_id, user.id)

    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])

    return result


@router.post("/compare", response_model=Dict)
def compare_scenarios(
    comparison: ScenarioCompare,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Compare multiple scenarios side-by-side

    Compares 2-4 scenarios and determines:
    - Which has the highest impact
    - Which is most achievable
    - Fastest path to goal
    - AI-generated insights

    Optionally save the comparison for later reference.
    """
    service = ScenarioService(db)

    result = service.compare_scenarios(
        user_id=user.id,
        scenario_ids=comparison.scenario_ids,
        comparison_name=comparison.comparison_name,
        save_comparison=comparison.save_comparison
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.get("/comparisons/saved", response_model=List[Dict])
def get_saved_comparisons(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's saved scenario comparisons

    Returns all comparisons previously saved by the user.
    """
    service = ScenarioService(db)
    comparisons = service.get_saved_comparisons(user.id)

    return comparisons


# Quick create endpoints for common scenarios

@router.post("/quick/spending-reduction", response_model=Dict)
def create_spending_reduction_scenario(
    category_id: int = Query(..., description="Category to reduce"),
    reduction_percent: float = Query(..., ge=1, le=100, description="Reduction percentage (1-100)"),
    duration_months: int = Query(6, ge=1, le=24, description="Duration in months"),
    name: Optional[str] = Query(None, description="Optional custom name"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Quick create: Spending reduction scenario

    Example: Reduce dining out by 30% for 6 months
    """
    service = ScenarioService(db)

    # Get category name for auto-naming
    from app.models.category import Category
    category = db.query(Category).filter(Category.id == category_id).first()
    category_name = category.name if category else "category"

    scenario_name = name or f"Reduce {category_name} by {reduction_percent}%"

    result = service.create_scenario(
        user_id=user.id,
        name=scenario_name,
        scenario_type='spending_reduction',
        parameters={
            'category_id': category_id,
            'reduction_percent': reduction_percent,
            'duration_months': duration_months
        }
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/quick/income-increase", response_model=Dict)
def create_income_increase_scenario(
    amount: float = Query(..., gt=0, description="Additional income amount"),
    frequency: str = Query(..., description="Frequency: monthly, biweekly, weekly, one_time"),
    duration_months: int = Query(12, ge=1, le=24, description="Duration in months"),
    name: Optional[str] = Query(None, description="Optional custom name"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Quick create: Income increase scenario

    Example: $500/month raise for 12 months
    """
    service = ScenarioService(db)

    if frequency not in ['monthly', 'biweekly', 'weekly', 'one_time']:
        raise HTTPException(status_code=400, detail="Invalid frequency")

    scenario_name = name or f"${amount} {frequency} income increase"

    result = service.create_scenario(
        user_id=user.id,
        name=scenario_name,
        scenario_type='income_increase',
        parameters={
            'amount': amount,
            'frequency': frequency,
            'duration_months': duration_months
        }
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/quick/savings-goal", response_model=Dict)
def create_savings_goal_scenario(
    target_amount: float = Query(..., gt=0, description="Target savings amount"),
    timeframe_months: int = Query(..., ge=1, le=60, description="Timeframe in months"),
    name: Optional[str] = Query(None, description="Optional custom name"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Quick create: Savings goal scenario

    Example: Save $5,000 in 12 months

    System will automatically suggest category adjustments if needed.
    """
    service = ScenarioService(db)

    scenario_name = name or f"Save ${target_amount:,.0f} in {timeframe_months} months"

    result = service.create_scenario(
        user_id=user.id,
        name=scenario_name,
        scenario_type='goal_based',
        parameters={
            'target_amount': target_amount,
            'timeframe_months': timeframe_months
        }
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


# Scenario templates endpoint

@router.get("/templates", response_model=List[Dict])
def get_scenario_templates():
    """
    Get pre-defined scenario templates

    Returns common scenario templates users can customize.
    """
    templates = [
        {
            'id': 'reduce_dining',
            'name': 'Reduce Dining Out',
            'description': 'Cut restaurant spending to save money',
            'scenario_type': 'spending_reduction',
            'suggested_params': {
                'reduction_percent': 30,
                'duration_months': 6
            },
            'icon': 'restaurant'
        },
        {
            'id': 'reduce_shopping',
            'name': 'Reduce Shopping',
            'description': 'Decrease discretionary shopping expenses',
            'scenario_type': 'spending_reduction',
            'suggested_params': {
                'reduction_percent': 40,
                'duration_months': 3
            },
            'icon': 'shopping-bag'
        },
        {
            'id': 'salary_increase',
            'name': 'Salary Increase',
            'description': 'Model the impact of a raise or promotion',
            'scenario_type': 'income_increase',
            'suggested_params': {
                'amount': 500,
                'frequency': 'monthly',
                'duration_months': 12
            },
            'icon': 'cash'
        },
        {
            'id': 'side_income',
            'name': 'Side Income',
            'description': 'Add freelance or part-time income',
            'scenario_type': 'income_increase',
            'suggested_params': {
                'amount': 200,
                'frequency': 'weekly',
                'duration_months': 12
            },
            'icon': 'briefcase'
        },
        {
            'id': 'emergency_fund',
            'name': 'Build Emergency Fund',
            'description': 'Save 3-6 months of expenses',
            'scenario_type': 'goal_based',
            'suggested_params': {
                'target_amount': 5000,
                'timeframe_months': 12
            },
            'icon': 'shield-check'
        },
        {
            'id': 'vacation_savings',
            'name': 'Vacation Savings',
            'description': 'Save for a vacation or trip',
            'scenario_type': 'goal_based',
            'suggested_params': {
                'target_amount': 3000,
                'timeframe_months': 6
            },
            'icon': 'airplane'
        },
        {
            'id': 'debt_payoff',
            'name': 'Debt Payoff Plan',
            'description': 'Accelerate debt repayment',
            'scenario_type': 'goal_based',
            'suggested_params': {
                'target_amount': 10000,
                'timeframe_months': 24
            },
            'icon': 'credit-card'
        },
        {
            'id': 'lifestyle_rebalance',
            'name': 'Lifestyle Rebalance',
            'description': 'Adjust multiple spending categories',
            'scenario_type': 'category_adjustment',
            'suggested_params': {
                'duration_months': 6
            },
            'icon': 'balance'
        }
    ]

    return templates
