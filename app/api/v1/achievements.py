"""
Achievement API Endpoints - Phase 1.1

Gamification system - achievements, badges, and progress tracking.
Provides endpoints for viewing achievements, stats, and unlocking.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services.gamification.achievement_service import AchievementService


router = APIRouter(prefix="/api/achievements", tags=["Achievements"])


# ===== ACHIEVEMENT ENDPOINTS =====

@router.get("/")
async def get_user_achievements(
    include_locked: bool = True,
    category: Optional[str] = None,
    tier: Optional[str] = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get all achievements for current user with progress information

    Query params:
    - include_locked: Include locked/secret achievements (default: True)
    - category: Filter by category ('tracking', 'saving', 'spending', 'goal')
    - tier: Filter by tier ('bronze', 'silver', 'gold', 'platinum')
    """
    achievements = AchievementService.get_user_achievements(
        db, user.id, include_locked=include_locked
    )

    # Apply filters
    if category:
        achievements = [a for a in achievements if a.get('category') == category]

    if tier:
        achievements = [a for a in achievements if a.get('tier') == tier]

    return JSONResponse({
        'success': True,
        'achievements': achievements,
        'total': len(achievements)
    })


@router.post("/check")
async def check_achievements(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger achievement check for current user

    This is automatically called after user actions (entries, goals, etc.),
    but can be manually triggered if needed.

    Returns newly unlocked achievements.
    """
    newly_unlocked = AchievementService.check_and_unlock_achievements(db, user.id)

    return JSONResponse({
        'success': True,
        'message': f'Unlocked {len(newly_unlocked)} new achievements' if newly_unlocked else 'No new achievements unlocked',
        'newly_unlocked': [ua.to_dict() for ua in newly_unlocked],
        'count': len(newly_unlocked)
    })


@router.get("/stats")
async def get_achievement_stats(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get achievement statistics for current user

    Returns:
    - total_points: Total achievement points earned
    - unlocked_count: Number of unlocked achievements
    - total_count: Total available achievements
    - completion_percentage: Percentage of achievements unlocked
    - tier_counts: Count by tier (bronze, silver, gold, platinum)
    - recent_achievements: Last 5 unlocked achievements
    """
    stats = AchievementService.get_achievement_stats(db, user.id)

    return JSONResponse({
        'success': True,
        'stats': stats
    })


@router.post("/mark-viewed")
async def mark_achievements_viewed(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all new achievements as viewed

    This removes the "NEW" badge from achievements in the UI
    """
    count = AchievementService.mark_achievements_viewed(db, user.id)

    return JSONResponse({
        'success': True,
        'message': f'Marked {count} achievements as viewed',
        'count': count
    })


@router.get("/categories")
async def get_achievement_categories(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get achievement categories with counts

    Returns list of categories with:
    - category name
    - total achievements in category
    - unlocked achievements in category
    - completion percentage
    """
    from app.models.achievement import Achievement, UserAchievement
    from sqlalchemy import func

    # Get all achievements grouped by category
    categories = db.query(
        Achievement.category,
        func.count(Achievement.id).label('total')
    ).filter(
        Achievement.is_active == True,
        Achievement.is_secret == False
    ).group_by(Achievement.category).all()

    # Get user's unlocked achievements by category
    user_unlocked = db.query(
        Achievement.category,
        func.count(UserAchievement.id).label('unlocked')
    ).join(
        UserAchievement,
        Achievement.id == UserAchievement.achievement_id
    ).filter(
        UserAchievement.user_id == user.id,
        Achievement.is_active == True
    ).group_by(Achievement.category).all()

    # Create lookup for unlocked counts
    unlocked_map = {cat: count for cat, count in user_unlocked}

    result = []
    for category, total in categories:
        unlocked = unlocked_map.get(category, 0)
        result.append({
            'category': category,
            'total': total,
            'unlocked': unlocked,
            'completion_percentage': int((unlocked / total * 100)) if total > 0 else 0
        })

    return JSONResponse({
        'success': True,
        'categories': result
    })


@router.get("/tiers")
async def get_achievement_tiers(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get achievement tiers with counts

    Returns list of tiers with:
    - tier name
    - total achievements in tier
    - unlocked achievements in tier
    - completion percentage
    """
    from app.models.achievement import Achievement, UserAchievement
    from sqlalchemy import func

    # Get all achievements grouped by tier
    tiers = db.query(
        Achievement.tier,
        func.count(Achievement.id).label('total')
    ).filter(
        Achievement.is_active == True,
        Achievement.is_secret == False
    ).group_by(Achievement.tier).all()

    # Get user's unlocked achievements by tier
    user_unlocked = db.query(
        Achievement.tier,
        func.count(UserAchievement.id).label('unlocked')
    ).join(
        UserAchievement,
        Achievement.id == UserAchievement.achievement_id
    ).filter(
        UserAchievement.user_id == user.id,
        Achievement.is_active == True
    ).group_by(Achievement.tier).all()

    # Create lookup for unlocked counts
    unlocked_map = {tier: count for tier, count in user_unlocked}

    result = []
    for tier, total in tiers:
        unlocked = unlocked_map.get(tier, 0)
        result.append({
            'tier': tier,
            'total': total,
            'unlocked': unlocked,
            'completion_percentage': int((unlocked / total * 100)) if total > 0 else 0
        })

    return JSONResponse({
        'success': True,
        'tiers': result
    })


@router.get("/recent")
async def get_recent_achievements(
    limit: int = 10,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get recently unlocked achievements

    Query params:
    - limit: Number of achievements to return (default: 10, max: 50)
    """
    from app.models.achievement import UserAchievement

    limit = min(limit, 50)  # Cap at 50

    user_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id
    ).order_by(
        UserAchievement.earned_at.desc()
    ).limit(limit).all()

    return JSONResponse({
        'success': True,
        'achievements': [ua.to_dict() for ua in user_achievements],
        'total': len(user_achievements)
    })


# ===== BADGE ENDPOINTS =====

@router.get("/badges")
async def get_user_badges(
    include_locked: bool = True,
    equipped_only: bool = False,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get all badges for current user

    Query params:
    - include_locked: Include locked badges (default: True)
    - equipped_only: Only show equipped badges (default: False)
    """
    from app.models.achievement import Badge, UserBadge

    if equipped_only:
        # Only equipped badges
        user_badges = db.query(UserBadge).filter(
            UserBadge.user_id == user.id,
            UserBadge.is_equipped == True
        ).all()

        return JSONResponse({
            'success': True,
            'badges': [ub.to_dict() for ub in user_badges],
            'total': len(user_badges)
        })

    # Get all badges
    badges = db.query(Badge).filter(
        Badge.is_active == True
    ).all()

    # Get user's earned badges
    user_badges = db.query(UserBadge).filter(
        UserBadge.user_id == user.id
    ).all()

    earned_ids = {ub.badge_id for ub in user_badges}
    user_badge_map = {ub.badge_id: ub for ub in user_badges}

    result = []
    for badge in badges:
        badge_data = badge.to_dict()
        badge_data['is_earned'] = badge.id in earned_ids

        if badge.id in earned_ids:
            ub = user_badge_map[badge.id]
            badge_data['is_equipped'] = ub.is_equipped
            badge_data['is_new'] = ub.is_new
            badge_data['earned_at'] = ub.earned_at.isoformat() if ub.earned_at else None
        else:
            if not include_locked:
                continue
            badge_data['is_equipped'] = False
            badge_data['is_new'] = False
            badge_data['earned_at'] = None

        result.append(badge_data)

    return JSONResponse({
        'success': True,
        'badges': result,
        'total': len(result)
    })


@router.post("/badges/{badge_id}/equip")
async def equip_badge(
    badge_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Equip a badge (display on profile)

    Only one badge can be equipped at a time
    """
    from app.models.achievement import UserBadge

    # Verify user has this badge
    user_badge = db.query(UserBadge).filter(
        UserBadge.user_id == user.id,
        UserBadge.badge_id == badge_id
    ).first()

    if not user_badge:
        raise HTTPException(status_code=404, detail="Badge not found or not earned")

    # Unequip all other badges
    db.query(UserBadge).filter(
        UserBadge.user_id == user.id,
        UserBadge.is_equipped == True
    ).update({'is_equipped': False, 'equipped_at': None})

    # Equip this badge
    from datetime import datetime
    user_badge.is_equipped = True
    user_badge.equipped_at = datetime.utcnow()

    db.commit()

    return JSONResponse({
        'success': True,
        'message': 'Badge equipped successfully'
    })


@router.post("/badges/{badge_id}/unequip")
async def unequip_badge(
    badge_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Unequip a badge
    """
    from app.models.achievement import UserBadge

    # Verify user has this badge
    user_badge = db.query(UserBadge).filter(
        UserBadge.user_id == user.id,
        UserBadge.badge_id == badge_id
    ).first()

    if not user_badge:
        raise HTTPException(status_code=404, detail="Badge not found or not earned")

    # Unequip badge
    user_badge.is_equipped = False
    user_badge.equipped_at = None

    db.commit()

    return JSONResponse({
        'success': True,
        'message': 'Badge unequipped successfully'
    })


@router.post("/badges/mark-viewed")
async def mark_badges_viewed(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all new badges as viewed
    """
    from app.models.achievement import UserBadge
    from datetime import datetime

    count = db.query(UserBadge).filter(
        UserBadge.user_id == user.id,
        UserBadge.is_new == True
    ).update({'is_new': False})

    db.commit()

    return JSONResponse({
        'success': True,
        'message': f'Marked {count} badges as viewed',
        'count': count
    })


# ===== LEADERBOARD & SOCIAL =====

@router.get("/leaderboard")
async def get_achievement_leaderboard(
    limit: int = 10,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get achievement points leaderboard

    Shows top users by achievement points with current user's rank

    Query params:
    - limit: Number of top users to return (default: 10, max: 100)
    """
    from app.models.achievement import Achievement, UserAchievement
    from sqlalchemy import func, desc

    limit = min(limit, 100)  # Cap at 100

    # Get top users by points
    leaderboard = db.query(
        User.id,
        User.full_name,
        User.avatar_url,
        func.sum(Achievement.points).label('total_points'),
        func.count(UserAchievement.id).label('achievement_count')
    ).join(
        UserAchievement,
        User.id == UserAchievement.user_id
    ).join(
        Achievement,
        UserAchievement.achievement_id == Achievement.id
    ).group_by(
        User.id, User.full_name, User.avatar_url
    ).order_by(
        desc('total_points')
    ).limit(limit).all()

    # Get current user's rank and stats
    user_stats = db.query(
        func.sum(Achievement.points).label('total_points'),
        func.count(UserAchievement.id).label('achievement_count')
    ).join(
        UserAchievement,
        Achievement.id == UserAchievement.achievement_id
    ).filter(
        UserAchievement.user_id == user.id
    ).first()

    user_points = user_stats.total_points or 0
    user_achievement_count = user_stats.achievement_count or 0

    # Calculate user rank
    higher_ranked = db.query(
        func.count(func.distinct(User.id))
    ).join(
        UserAchievement,
        User.id == UserAchievement.user_id
    ).join(
        Achievement,
        UserAchievement.achievement_id == Achievement.id
    ).group_by(User.id).having(
        func.sum(Achievement.points) > user_points
    ).scalar() or 0

    user_rank = higher_ranked + 1

    return JSONResponse({
        'success': True,
        'leaderboard': [
            {
                'rank': idx + 1,
                'user_id': row.id,
                'full_name': row.full_name,
                'avatar_url': row.avatar_url,
                'total_points': int(row.total_points or 0),
                'achievement_count': row.achievement_count
            }
            for idx, row in enumerate(leaderboard)
        ],
        'current_user': {
            'rank': user_rank,
            'total_points': int(user_points),
            'achievement_count': user_achievement_count
        }
    })
