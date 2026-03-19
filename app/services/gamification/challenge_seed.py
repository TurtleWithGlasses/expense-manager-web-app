"""Default Savings Challenges Seed Data"""
from datetime import datetime, date


# Default challenges to seed when the table is empty.
# Each dict maps directly to Challenge model fields.
DEFAULT_CHALLENGES = [
    {
        "code": "no_spend_weekend_2026",
        "name": "No-Spend Weekend",
        "description": "Go an entire weekend (Saturday + Sunday) without spending any money. Plan ahead and use what you already have!",
        "challenge_type": "weekly",
        "completion_criteria": {"type": "no_spend_days", "target": 2},
        "xp_reward": 150,
        "points_reward": 50,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": True,
        "difficulty_level": 2,
        "icon_name": "moon-stars",
        "color_hex": "#8b5cf6",
    },
    {
        "code": "weekly_tracker_2026",
        "name": "Weekly Expense Tracker",
        "description": "Log at least 7 expenses this week. Building the habit of tracking every purchase is the first step to financial control.",
        "challenge_type": "weekly",
        "completion_criteria": {"type": "entry_count", "target": 7},
        "xp_reward": 100,
        "points_reward": 30,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": True,
        "difficulty_level": 1,
        "icon_name": "pencil-square",
        "color_hex": "#3b82f6",
    },
    {
        "code": "monthly_saver_100_2026",
        "name": "Save $100 This Month",
        "description": "Achieve $100 in net savings (income minus expenses) during the challenge period. Cut back on one luxury and watch the savings add up!",
        "challenge_type": "monthly",
        "completion_criteria": {"type": "save_amount", "target": 100},
        "xp_reward": 300,
        "points_reward": 100,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": True,
        "difficulty_level": 3,
        "icon_name": "piggy-bank",
        "color_hex": "#10b981",
    },
    {
        "code": "no_spend_5_days_2026",
        "name": "5 No-Spend Days",
        "description": "Have 5 days with zero expenses in the challenge period. Cook at home, walk instead of ride, and rediscover free activities.",
        "challenge_type": "monthly",
        "completion_criteria": {"type": "no_spend_days", "target": 5},
        "xp_reward": 200,
        "points_reward": 75,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": False,
        "difficulty_level": 2,
        "icon_name": "ban",
        "color_hex": "#f59e0b",
    },
    {
        "code": "daily_streak_7_2026",
        "name": "7-Day Logging Streak",
        "description": "Log at least one entry every day for 7 consecutive days. Consistency is the key to understanding your spending.",
        "challenge_type": "weekly",
        "completion_criteria": {"type": "daily_streak", "target": 7},
        "xp_reward": 250,
        "points_reward": 80,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": False,
        "difficulty_level": 2,
        "icon_name": "fire",
        "color_hex": "#ef4444",
    },
    {
        "code": "monthly_saver_500_2026",
        "name": "Save $500 This Month",
        "description": "Achieve $500 in net savings this month. This takes serious discipline — review every subscription, cut dining out, and stay focused.",
        "challenge_type": "monthly",
        "completion_criteria": {"type": "save_amount", "target": 500},
        "xp_reward": 750,
        "points_reward": 250,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": False,
        "difficulty_level": 5,
        "icon_name": "trophy",
        "color_hex": "#f59e0b",
    },
    {
        "code": "budget_master_2026",
        "name": "Budget Master",
        "description": "Log 30 or more expense entries this month. The more you track, the better you understand where your money goes.",
        "challenge_type": "monthly",
        "completion_criteria": {"type": "entry_count", "target": 30},
        "xp_reward": 400,
        "points_reward": 120,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": False,
        "difficulty_level": 3,
        "icon_name": "bar-chart",
        "color_hex": "#6366f1",
    },
    {
        "code": "daily_streak_30_2026",
        "name": "30-Day Logging Streak",
        "description": "Log entries every single day for 30 consecutive days. The ultimate habit-building challenge for serious budgeters.",
        "challenge_type": "one_time",
        "completion_criteria": {"type": "daily_streak", "target": 30},
        "xp_reward": 1000,
        "points_reward": 350,
        "start_date": datetime(2026, 1, 1),
        "end_date": datetime(2026, 12, 31),
        "status": "active",
        "is_featured": False,
        "difficulty_level": 5,
        "icon_name": "calendar-check",
        "color_hex": "#ec4899",
    },
]


def seed_default_challenges(db) -> int:
    """
    Insert default challenges if the challenges table is empty.
    Returns the number of challenges created.
    """
    from app.models.challenge import Challenge

    existing = db.query(Challenge).count()
    if existing > 0:
        return 0

    created = 0
    for data in DEFAULT_CHALLENGES:
        challenge = Challenge(**data)
        db.add(challenge)
        created += 1

    db.commit()
    return created
