"""Gamification API Endpoints - Phase 3

Comprehensive gamification endpoints including:
- Leaderboards (XP, Level, Achievements)
- Financial Health Score
- User Level & XP Management
- Challenges
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services.gamification.level_service import LevelService
from app.services.gamification.health_score_service import HealthScoreService
from app.services.gamification.challenge_service import ChallengeService


router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


# ===== LEADERBOARD ENDPOINTS =====

@router.get("/leaderboard/xp")
async def get_xp_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get top users by total XP"""
    service = LevelService(db)
    top_users = service.get_top_users_by_xp(limit)

    # Get current user's rank
    user_rank = service.get_user_rank_position(user.id)

    return JSONResponse({
        'success': True,
        'leaderboard': top_users,
        'user_rank': user_rank,
        'total_users': user_rank['total_users']
    })


@router.get("/leaderboard/level")
async def get_level_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get top users by level"""
    service = LevelService(db)
    top_users = service.get_top_users_by_level(limit)

    # Get current user's rank
    user_rank = service.get_user_rank_position(user.id)

    return JSONResponse({
        'success': True,
        'leaderboard': top_users,
        'user_rank': user_rank,
        'total_users': user_rank['total_users']
    })


@router.get("/leaderboard/achievements")
async def get_achievement_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get top users by total achievement points"""
    from app.services.gamification.achievement_service import AchievementService

    service = AchievementService(db)

    # Get top users by achievement points
    from app.models.achievement import UserAchievement, Achievement
    from sqlalchemy import func

    top_users = db.query(
        User.id,
        User.username,
        User.email,
        func.sum(Achievement.points).label('total_points'),
        func.count(UserAchievement.id).label('achievement_count')
    ).join(
        UserAchievement, User.id == UserAchievement.user_id
    ).join(
        Achievement, UserAchievement.achievement_id == Achievement.id
    ).group_by(User.id).order_by(
        func.sum(Achievement.points).desc()
    ).limit(limit).all()

    leaderboard = [
        {
            'user_id': u.id,
            'username': u.username,
            'email': u.email,
            'total_points': int(u.total_points or 0),
            'achievement_count': u.achievement_count
        }
        for u in top_users
    ]

    # Get current user's stats
    user_stats = service.get_achievement_stats(user.id)

    return JSONResponse({
        'success': True,
        'leaderboard': leaderboard,
        'user_stats': user_stats
    })


# ===== USER LEVEL & XP ENDPOINTS =====

@router.get("/level/info")
async def get_user_level_info(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive level information for current user"""
    service = LevelService(db)
    info = service.get_user_level_info(user.id)

    return JSONResponse({
        'success': True,
        **info
    })


class AddXPRequest(BaseModel):
    amount: int
    reason: Optional[str] = None


@router.post("/level/add-xp")
async def add_xp(
    request: AddXPRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Add XP to user (admin/testing endpoint)"""
    service = LevelService(db)
    result = service.add_xp(user.id, request.amount, request.reason)

    return JSONResponse({
        'success': True,
        **result
    })


# ===== FINANCIAL HEALTH SCORE ENDPOINTS =====

@router.get("/health-score")
async def get_health_score(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive financial health score for current user"""
    service = HealthScoreService(db)
    score = service.calculate_health_score(user.id)

    return JSONResponse({
        'success': True,
        **score
    })


@router.get("/health-score/history")
async def get_health_score_history(
    months: int = Query(6, ge=1, le=12),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get historical health scores (placeholder)"""
    service = HealthScoreService(db)
    history = service.get_score_history(user.id, months)

    return JSONResponse({
        'success': True,
        'history': history,
        'note': 'Historical tracking not yet implemented'
    })


# ===== CHALLENGE ENDPOINTS =====

@router.get("/challenges")
async def get_active_challenges(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get all currently active challenges"""
    service = ChallengeService(db)
    challenges = service.get_active_challenges()

    return JSONResponse({
        'success': True,
        'challenges': [
            {
                'id': c.id,
                'code': c.code,
                'name': c.name,
                'description': c.description,
                'challenge_type': c.challenge_type,
                'xp_reward': c.xp_reward,
                'points_reward': c.points_reward,
                'start_date': c.start_date.isoformat(),
                'end_date': c.end_date.isoformat(),
                'difficulty_level': c.difficulty_level,
                'participant_count': c.participant_count,
                'completion_count': c.completion_count,
                'is_featured': c.is_featured
            }
            for c in challenges
        ],
        'total': len(challenges)
    })


@router.get("/challenges/my-challenges")
async def get_my_challenges(
    include_completed: bool = Query(True),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get challenges user is participating in"""
    service = ChallengeService(db)
    user_challenges = service.get_user_challenges(
        user.id,
        include_completed=include_completed
    )

    return JSONResponse({
        'success': True,
        'challenges': [
            {
                'id': uc.id,
                'challenge_id': uc.challenge_id,
                'challenge_name': uc.challenge.name,
                'status': uc.status,
                'current_progress': float(uc.current_progress),
                'target_progress': float(uc.target_progress),
                'progress_percentage': float(uc.progress_percentage),
                'joined_at': uc.joined_at.isoformat(),
                'completed_at': uc.completed_at.isoformat() if uc.completed_at else None,
                'rewards_claimed': uc.rewards_claimed
            }
            for uc in user_challenges
        ],
        'total': len(user_challenges)
    })


@router.post("/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Join a challenge"""
    service = ChallengeService(db)

    try:
        user_challenge = service.join_challenge(user.id, challenge_id)

        return JSONResponse({
            'success': True,
            'message': 'Successfully joined challenge',
            'user_challenge': {
                'id': user_challenge.id,
                'challenge_id': user_challenge.challenge_id,
                'status': user_challenge.status,
                'target_progress': float(user_challenge.target_progress)
            }
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenges/{challenge_id}/claim-rewards")
async def claim_challenge_rewards(
    challenge_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Claim rewards for completed challenge"""
    service = ChallengeService(db)
    level_service = LevelService(db)

    try:
        rewards = service.claim_challenge_rewards(user.id, challenge_id)

        # Award XP
        if rewards['xp_reward'] > 0:
            xp_result = level_service.add_xp(
                user.id,
                rewards['xp_reward'],
                f"Challenge {challenge_id} completed"
            )
            rewards['xp_result'] = xp_result

        return JSONResponse({
            'success': True,
            'message': 'Rewards claimed successfully',
            'rewards': rewards
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/challenges/stats")
async def get_challenge_stats(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get user's challenge participation statistics"""
    service = ChallengeService(db)
    stats = service.get_user_challenge_stats(user.id)

    return JSONResponse({
        'success': True,
        'stats': stats
    })


# ===== DASHBOARD SUMMARY =====

@router.get("/dashboard/summary")
async def get_gamification_dashboard(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive gamification summary for dashboard"""
    level_service = LevelService(db)
    health_service = HealthScoreService(db)
    challenge_service = ChallengeService(db)

    from app.services.gamification.achievement_service import AchievementService
    achievement_service = AchievementService(db)

    # Get all data
    level_info = level_service.get_user_level_info(user.id)
    health_score = health_service.calculate_health_score(user.id)
    achievement_stats = achievement_service.get_achievement_stats(user.id)
    challenge_stats = challenge_service.get_user_challenge_stats(user.id)
    user_rank = level_service.get_user_rank_position(user.id)

    return JSONResponse({
        'success': True,
        'level': level_info,
        'health_score': {
            'total_score': health_score['total_score'],
            'rating': health_score['rating'],
            'top_recommendation': health_score['recommendations'][0] if health_score['recommendations'] else None
        },
        'achievements': {
            'total_points': achievement_stats['total_points'],
            'unlocked_count': achievement_stats['unlocked_count'],
            'completion_percentage': achievement_stats['completion_percentage']
        },
        'challenges': challenge_stats,
        'rank': user_rank
    })
