"""Goals API Endpoints - Phase 17"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.models.financial_goal import GoalType, GoalStatus
from app.services.goal_service import GoalService


router = APIRouter(prefix="/api/goals", tags=["Goals"])


# Request/Response Models
class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    goal_type: GoalType = GoalType.SAVINGS
    target_amount: float = Field(..., gt=0)
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    category_id: Optional[int] = None
    target_date: Optional[datetime] = None
    notify_on_milestone: bool = True
    milestone_percentage: int = Field(default=25, ge=1, le=100)


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[datetime] = None
    status: Optional[GoalStatus] = None
    notify_on_milestone: Optional[bool] = None
    milestone_percentage: Optional[int] = Field(None, ge=1, le=100)


class GoalProgressUpdate(BaseModel):
    current_amount: float = Field(..., ge=0)
    note: Optional[str] = None


# ===== GOAL CRUD ENDPOINTS =====

@router.post("/")
async def create_goal(
    goal_data: GoalCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Create a new financial goal"""
    try:
        service = GoalService(db)

        # Use user's default currency if not specified
        if goal_data.currency_code == "USD":
            from app.services.user_preferences import user_preferences_service
            goal_data.currency_code = user_preferences_service.get_user_currency(db, user.id)

        goal = service.create_goal(
            user_id=user.id,
            name=goal_data.name,
            target_amount=goal_data.target_amount,
            goal_type=goal_data.goal_type,
            description=goal_data.description,
            category_id=goal_data.category_id,
            target_date=goal_data.target_date,
            currency_code=goal_data.currency_code,
            notify_on_milestone=goal_data.notify_on_milestone,
            milestone_percentage=goal_data.milestone_percentage
        )

        return JSONResponse({
            'success': True,
            'message': 'Goal created successfully',
            'goal': {
                'id': goal.id,
                'name': goal.name,
                'target_amount': float(goal.target_amount),
                'current_amount': float(goal.current_amount),
                'progress_percentage': float(goal.progress_percentage),
                'currency_code': goal.currency_code,
                'status': goal.status
            }
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_user_goals(
    include_completed: bool = False,
    status: Optional[GoalStatus] = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get all goals for current user"""
    service = GoalService(db)
    goals = service.get_user_goals(user.id, status=status, include_completed=include_completed)

    return JSONResponse({
        'success': True,
        'goals': [
            {
                'id': g.id,
                'name': g.name,
                'description': g.description,
                'goal_type': g.goal_type,
                'target_amount': float(g.target_amount),
                'current_amount': float(g.current_amount),
                'progress_percentage': float(g.progress_percentage),
                'currency_code': g.currency_code,
                'category_id': g.category_id,
                'status': g.status,
                'start_date': g.start_date.isoformat() if g.start_date else None,
                'target_date': g.target_date.isoformat() if g.target_date else None,
                'completed_date': g.completed_date.isoformat() if g.completed_date else None,
                'created_at': g.created_at.isoformat() if g.created_at else None
            }
            for g in goals
        ],
        'total': len(goals)
    })


@router.get("/{goal_id}")
async def get_goal(
    goal_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get a specific goal"""
    service = GoalService(db)
    goal = service.get_goal(goal_id, user.id)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return JSONResponse({
        'success': True,
        'goal': {
            'id': goal.id,
            'name': goal.name,
            'description': goal.description,
            'goal_type': goal.goal_type,
            'target_amount': float(goal.target_amount),
            'current_amount': float(goal.current_amount),
            'progress_percentage': float(goal.progress_percentage),
            'currency_code': goal.currency_code,
            'category_id': goal.category_id,
            'status': goal.status,
            'start_date': goal.start_date.isoformat() if goal.start_date else None,
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'completed_date': goal.completed_date.isoformat() if goal.completed_date else None,
            'notify_on_milestone': goal.notify_on_milestone,
            'milestone_percentage': goal.milestone_percentage,
            'created_at': goal.created_at.isoformat() if goal.created_at else None,
            'updated_at': goal.updated_at.isoformat() if goal.updated_at else None
        }
    })


@router.put("/{goal_id}")
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Update a goal's details"""
    service = GoalService(db)

    # Only include non-None fields
    updates = {k: v for k, v in goal_data.dict().items() if v is not None}

    goal = service.update_goal(goal_id, user.id, **updates)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return JSONResponse({
        'success': True,
        'message': 'Goal updated successfully',
        'goal': {
            'id': goal.id,
            'name': goal.name,
            'progress_percentage': float(goal.progress_percentage),
            'status': goal.status
        }
    })


@router.post("/{goal_id}/progress")
async def update_goal_progress(
    goal_id: int,
    progress_data: GoalProgressUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Update the progress of a goal"""
    service = GoalService(db)
    goal = service.update_goal_progress(
        goal_id,
        user.id,
        progress_data.current_amount,
        note=progress_data.note,
        is_manual=True
    )

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return JSONResponse({
        'success': True,
        'message': 'Progress updated successfully',
        'goal': {
            'id': goal.id,
            'name': goal.name,
            'current_amount': float(goal.current_amount),
            'target_amount': float(goal.target_amount),
            'progress_percentage': float(goal.progress_percentage),
            'status': goal.status,
            'completed': goal.status == GoalStatus.COMPLETED
        }
    })


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Delete a goal"""
    service = GoalService(db)
    success = service.delete_goal(goal_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")

    return JSONResponse({
        'success': True,
        'message': 'Goal deleted successfully'
    })


# ===== STATISTICS & ANALYTICS =====

@router.get("/statistics/overview")
async def get_goal_statistics(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about user's goals"""
    service = GoalService(db)
    stats = service.get_goal_statistics(user.id)

    # Get user's currency
    from app.services.user_preferences import user_preferences_service
    currency_code = user_preferences_service.get_user_currency(db, user.id)

    return JSONResponse({
        'success': True,
        'statistics': {
            **stats,
            'currency_code': currency_code
        }
    })


@router.get("/dashboard/summary")
async def get_goals_dashboard_summary(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get goals summary for dashboard widget"""
    service = GoalService(db)
    summary = service.get_goals_summary_for_dashboard(user.id)

    return JSONResponse({
        'success': True,
        **summary
    })


@router.get("/{goal_id}/history")
async def get_goal_progress_history(
    goal_id: int,
    limit: int = 50,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get progress history for a goal"""
    service = GoalService(db)
    logs = service.get_goal_progress_logs(goal_id, user.id, limit=limit)

    return JSONResponse({
        'success': True,
        'history': [
            {
                'id': log.id,
                'previous_amount': float(log.previous_amount),
                'new_amount': float(log.new_amount),
                'change_amount': float(log.change_amount),
                'note': log.note,
                'is_manual': log.is_manual,
                'recorded_at': log.recorded_at.isoformat() if log.recorded_at else None
            }
            for log in logs
        ],
        'total': len(logs)
    })


@router.post("/auto-update-spending-limits")
async def auto_update_spending_limits(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Automatically update spending limit goals based on actual spending"""
    service = GoalService(db)
    updated_goals = service.auto_update_spending_limit_goals(user.id)

    return JSONResponse({
        'success': True,
        'message': f'Updated {len(updated_goals)} spending limit goals',
        'updated_count': len(updated_goals),
        'goals': [
            {
                'id': g.id,
                'name': g.name,
                'current_amount': float(g.current_amount),
                'target_amount': float(g.target_amount),
                'status': g.status
            }
            for g in updated_goals
        ]
    })
