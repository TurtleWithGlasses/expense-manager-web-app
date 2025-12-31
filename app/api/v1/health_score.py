"""
Financial Health Score API Endpoints - Phase 1.2

Provides REST API for financial health score system including:
- Fetching current health score with breakdown
- Viewing historical scores
- Getting personalized recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, datetime, timedelta
from typing import Optional

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.models.financial_health_score import FinancialHealthScore
from app.services.gamification.health_score_service import HealthScoreService

router = APIRouter(prefix="/api/v1/health-score", tags=["Health Score"])


@router.get("")
async def get_financial_health_score(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get current financial health score with breakdown

    Returns:
    - overall_score: Total score (0-100)
    - grade: Excellent/Good/Fair/Poor
    - component_scores: Breakdown by component
    - recommendations: Personalized improvement suggestions
    """
    service = HealthScoreService(db)
    score_data = service.calculate_health_score(user.id)

    # Save to database for historical tracking
    today = date.today()

    # Check if score already exists for today
    existing_score = db.query(FinancialHealthScore).filter(
        FinancialHealthScore.user_id == user.id,
        FinancialHealthScore.score_date == today
    ).first()

    if existing_score:
        # Update existing score
        existing_score.score = int(score_data['total_score'])
        existing_score.savings_rate_score = int(score_data['components']['savings_rate']['score'])
        existing_score.expense_consistency_score = int(score_data['components']['spending_consistency']['score'])
        existing_score.budget_adherence_score = int(score_data['components']['budget_adherence']['score'])
        existing_score.goal_progress_score = int(score_data['components']['goal_progress']['score'])
        existing_score.calculation_data = {
            'components': score_data['components'],
            'calculated_at': score_data['calculated_at']
        }
        existing_score.recommendations = {'items': score_data['recommendations']}
    else:
        # Create new score
        new_score = FinancialHealthScore(
            user_id=user.id,
            score=int(score_data['total_score']),
            score_date=today,
            savings_rate_score=int(score_data['components']['savings_rate']['score']),
            expense_consistency_score=int(score_data['components']['spending_consistency']['score']),
            budget_adherence_score=int(score_data['components']['budget_adherence']['score']),
            goal_progress_score=int(score_data['components']['goal_progress']['score']),
            calculation_data={
                'components': score_data['components'],
                'calculated_at': score_data['calculated_at']
            },
            recommendations={'items': score_data['recommendations']}
        )
        db.add(new_score)

    db.commit()

    return {
        'overall_score': score_data['total_score'],
        'grade': score_data['rating'],
        'components': score_data['components'],
        'recommendations': score_data['recommendations'],
        'calculated_at': score_data['calculated_at']
    }


@router.get("/history")
async def get_health_score_history(
    days: int = Query(90, ge=1, le=365, description="Number of days of history to retrieve"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get historical health scores for trend analysis

    Query params:
    - days: Number of days of history (1-365, default 90)

    Returns:
    - scores: List of historical scores
    - trend: Overall trend (improving/stable/declining)
    - average_score: Average score over the period
    """
    start_date = date.today() - timedelta(days=days)

    scores = db.query(FinancialHealthScore).filter(
        FinancialHealthScore.user_id == user.id,
        FinancialHealthScore.score_date >= start_date
    ).order_by(desc(FinancialHealthScore.score_date)).all()

    if not scores:
        return {
            'scores': [],
            'trend': 'no_data',
            'average_score': 0,
            'data_points': 0
        }

    # Calculate trend
    recent_scores = [s.score for s in scores[:min(7, len(scores))]]
    older_scores = [s.score for s in scores[-min(7, len(scores)):]]

    recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    older_avg = sum(older_scores) / len(older_scores) if older_scores else 0

    if recent_avg > older_avg + 5:
        trend = 'improving'
    elif recent_avg < older_avg - 5:
        trend = 'declining'
    else:
        trend = 'stable'

    # Calculate overall average
    all_scores = [s.score for s in scores]
    average_score = sum(all_scores) / len(all_scores) if all_scores else 0

    return {
        'scores': [
            {
                'date': score.score_date.isoformat(),
                'score': score.score,
                'grade': score.get_grade(),
                'components': {
                    'savings_rate': score.savings_rate_score,
                    'expense_consistency': score.expense_consistency_score,
                    'budget_adherence': score.budget_adherence_score,
                    'goal_progress': score.goal_progress_score
                }
            }
            for score in scores
        ],
        'trend': trend,
        'average_score': round(average_score, 1),
        'data_points': len(scores),
        'period_days': days
    }


@router.get("/recommendations")
async def get_health_recommendations(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations to improve score

    Returns:
    - priority_recommendations: Top 3 most impactful improvements
    - all_recommendations: Complete list of suggestions
    - estimated_impact: Potential score improvement for each
    """
    service = HealthScoreService(db)
    score_data = service.calculate_health_score(user.id)

    recommendations = score_data['recommendations']

    # Sort by priority (recommendations for lowest scoring components first)
    components = score_data['components']
    component_scores = {
        'savings_rate': components['savings_rate']['score'],
        'expense_consistency': components['spending_consistency']['score'],
        'budget_adherence': components['budget_adherence']['score'],
        'goal_progress': components['goal_progress']['score']
    }

    # Get priority recommendations (lowest scoring areas)
    sorted_components = sorted(component_scores.items(), key=lambda x: x[1])
    priority_areas = [comp[0] for comp in sorted_components[:3]]

    return {
        'priority_recommendations': recommendations[:3] if len(recommendations) >= 3 else recommendations,
        'all_recommendations': recommendations,
        'priority_areas': priority_areas,
        'current_score': score_data['total_score'],
        'potential_improvement': '10-15 points' if score_data['total_score'] < 70 else '5-10 points'
    }


@router.get("/comparison")
async def get_score_comparison(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get anonymous comparison with other users

    Returns:
    - user_score: Current user's score
    - percentile: Where user ranks among all users
    - average_score: Platform average
    """
    # Get user's current score
    user_score = db.query(FinancialHealthScore).filter(
        FinancialHealthScore.user_id == user.id
    ).order_by(desc(FinancialHealthScore.score_date)).first()

    if not user_score:
        # Calculate score if doesn't exist
        service = HealthScoreService(db)
        score_data = service.calculate_health_score(user.id)
        current_score = score_data['total_score']
    else:
        current_score = user_score.score

    # Get all latest scores for percentile calculation
    from sqlalchemy import func
    latest_scores = db.query(
        FinancialHealthScore.user_id,
        func.max(FinancialHealthScore.score_date).label('latest_date')
    ).group_by(FinancialHealthScore.user_id).subquery()

    all_scores = db.query(FinancialHealthScore.score).join(
        latest_scores,
        (FinancialHealthScore.user_id == latest_scores.c.user_id) &
        (FinancialHealthScore.score_date == latest_scores.c.latest_date)
    ).all()

    scores_list = [s[0] for s in all_scores]

    if not scores_list:
        return {
            'user_score': current_score,
            'percentile': 0,
            'average_score': 0,
            'total_users': 0
        }

    # Calculate percentile
    lower_scores = sum(1 for s in scores_list if s < current_score)
    percentile = int((lower_scores / len(scores_list)) * 100) if scores_list else 0

    # Calculate average
    average_score = sum(scores_list) / len(scores_list)

    return {
        'user_score': round(current_score, 1),
        'percentile': percentile,
        'average_score': round(average_score, 1),
        'total_users': len(scores_list),
        'rank': lower_scores + 1
    }
