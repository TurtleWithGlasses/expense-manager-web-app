"""
Gamification Seed Data - Phase 1.1

Seeds default achievements and badges for testing and production.
Run with: python -m app.seeds.gamification_seeds
"""

from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal

# Import all models to ensure SQLAlchemy relationships are properly registered
# This is necessary because User has relationships to all these models
from app.models.user import User
from app.models.category import Category
from app.models.entry import Entry
from app.models.user_preferences import UserPreferences
from app.models.ai_model import AIModel, AISuggestion, UserAIPreferences
from app.models.weekly_report import WeeklyReport, UserReportPreferences
from app.models.report_status import ReportStatus
from app.models.financial_goal import FinancialGoal, GoalProgressLog
from app.models.recurring_payment import RecurringPayment, PaymentReminder
from app.models.payment_history import PaymentOccurrence, PaymentLinkSuggestion
from app.models.forecast import Forecast
from app.models.scenario import Scenario, ScenarioComparison
from app.models.historical_report import HistoricalReport
from app.models.achievement import Achievement, Badge, UserAchievement, UserBadge


def seed_achievements(db: Session):
    """Seed default achievements"""

    achievements = [
        # ===== TRACKING CATEGORY =====
        Achievement(
            code='first_entry',
            name='First Step',
            description='Log your very first transaction',
            category='tracking',
            tier='bronze',
            icon_name='trophy',
            color_hex='#cd7f32',
            points=10,
            unlock_criteria={'type': 'entry_count', 'threshold': 1},
            is_active=True,
            is_secret=False,
            sort_order=1
        ),
        Achievement(
            code='streak_7',
            name='Week Warrior',
            description='Log entries for 7 consecutive days',
            category='tracking',
            tier='silver',
            icon_name='fire',
            color_hex='#c0c0c0',
            points=50,
            unlock_criteria={'type': 'daily_streak', 'days': 7},
            is_active=True,
            is_secret=False,
            sort_order=2
        ),
        Achievement(
            code='streak_14',
            name='Fortnight Champion',
            description='Log entries for 14 consecutive days',
            category='tracking',
            tier='gold',
            icon_name='fire',
            color_hex='#ffd700',
            points=100,
            unlock_criteria={'type': 'daily_streak', 'days': 14},
            is_active=True,
            is_secret=False,
            sort_order=3
        ),
        Achievement(
            code='streak_30',
            name='Monthly Master',
            description='Log entries for 30 consecutive days',
            category='tracking',
            tier='platinum',
            icon_name='fire',
            color_hex='#e5e4e2',
            points=200,
            unlock_criteria={'type': 'daily_streak', 'days': 30},
            is_active=True,
            is_secret=False,
            sort_order=4
        ),
        Achievement(
            code='entry_100',
            name='Century Club',
            description='Log 100 total transactions',
            category='tracking',
            tier='gold',
            icon_name='star',
            color_hex='#ffd700',
            points=150,
            unlock_criteria={'type': 'entry_count', 'threshold': 100},
            is_active=True,
            is_secret=False,
            sort_order=5
        ),

        # ===== SAVINGS CATEGORY =====
        Achievement(
            code='savings_rate_10',
            name='Saver Starter',
            description='Save 10% of your income in a month',
            category='saving',
            tier='bronze',
            icon_name='piggy-bank',
            color_hex='#cd7f32',
            points=30,
            unlock_criteria={'type': 'savings_rate', 'percentage': 10},
            is_active=True,
            is_secret=False,
            sort_order=10
        ),
        Achievement(
            code='savings_rate_20',
            name='Savings Champion',
            description='Save 20% of your income in a month',
            category='saving',
            tier='silver',
            icon_name='piggy-bank',
            color_hex='#c0c0c0',
            points=60,
            unlock_criteria={'type': 'savings_rate', 'percentage': 20},
            is_active=True,
            is_secret=False,
            sort_order=11
        ),
        Achievement(
            code='savings_rate_30',
            name='Savings Legend',
            description='Save 30% of your income in a month',
            category='saving',
            tier='gold',
            icon_name='piggy-bank',
            color_hex='#ffd700',
            points=120,
            unlock_criteria={'type': 'savings_rate', 'percentage': 30},
            is_active=True,
            is_secret=False,
            sort_order=12
        ),
        Achievement(
            code='saved_1000',
            name='Four Figures',
            description='Save a total of $1,000',
            category='saving',
            tier='silver',
            icon_name='dollar',
            color_hex='#c0c0c0',
            points=100,
            unlock_criteria={'type': 'total_saved', 'amount': 1000},
            is_active=True,
            is_secret=False,
            sort_order=13
        ),
        Achievement(
            code='saved_5000',
            name='Five Grand',
            description='Save a total of $5,000',
            category='saving',
            tier='gold',
            icon_name='dollar',
            color_hex='#ffd700',
            points=250,
            unlock_criteria={'type': 'total_saved', 'amount': 5000},
            is_active=True,
            is_secret=False,
            sort_order=14
        ),

        # ===== SPENDING CATEGORY =====
        Achievement(
            code='no_spend_day_1',
            name='First No-Spend Day',
            description='Go one day without spending',
            category='spending',
            tier='bronze',
            icon_name='ban',
            color_hex='#cd7f32',
            points=20,
            unlock_criteria={'type': 'no_spend_days', 'count': 1, 'period': 'month'},
            is_active=True,
            is_secret=False,
            sort_order=20
        ),
        Achievement(
            code='no_spend_days_3',
            name='Spending Discipline',
            description='Have 3 no-spend days in a month',
            category='spending',
            tier='silver',
            icon_name='ban',
            color_hex='#c0c0c0',
            points=50,
            unlock_criteria={'type': 'no_spend_days', 'count': 3, 'period': 'month'},
            is_active=True,
            is_secret=False,
            sort_order=21
        ),
        Achievement(
            code='no_spend_days_7',
            name='Spending Control',
            description='Have 7 no-spend days in a month',
            category='spending',
            tier='gold',
            icon_name='ban',
            color_hex='#ffd700',
            points=100,
            unlock_criteria={'type': 'no_spend_days', 'count': 7, 'period': 'month'},
            is_active=True,
            is_secret=False,
            sort_order=22
        ),
        Achievement(
            code='expense_reduction_10',
            name='Cutter',
            description='Reduce expenses by 10% compared to last month',
            category='spending',
            tier='silver',
            icon_name='scissors',
            color_hex='#c0c0c0',
            points=75,
            unlock_criteria={'type': 'expense_reduction', 'percentage': 10},
            is_active=True,
            is_secret=False,
            sort_order=23
        ),
        Achievement(
            code='expense_reduction_25',
            name='Budget Boss',
            description='Reduce expenses by 25% compared to last month',
            category='spending',
            tier='gold',
            icon_name='scissors',
            color_hex='#ffd700',
            points=150,
            unlock_criteria={'type': 'expense_reduction', 'percentage': 25},
            is_active=True,
            is_secret=False,
            sort_order=24
        ),

        # ===== SECRET ACHIEVEMENTS =====
        Achievement(
            code='perfect_month',
            name='Perfect Month',
            description='Complete a month with all goals met and no budget overruns',
            category='goal',
            tier='platinum',
            icon_name='crown',
            color_hex='#e5e4e2',
            points=300,
            unlock_criteria={'type': 'special', 'condition': 'perfect_month'},
            is_active=True,
            is_secret=True,
            sort_order=100
        ),
        Achievement(
            code='early_bird',
            name='Early Adopter',
            description='One of the first 100 users!',
            category='special',
            tier='gold',
            icon_name='bird',
            color_hex='#ffd700',
            points=100,
            unlock_criteria={'type': 'special', 'condition': 'early_adopter'},
            is_active=True,
            is_secret=True,
            sort_order=101
        ),
    ]

    # Check if achievements already exist
    existing_codes = {a.code for a in db.query(Achievement.code).all()}

    new_achievements = [a for a in achievements if a.code not in existing_codes]

    if new_achievements:
        db.add_all(new_achievements)
        db.commit()
        print(f"[OK] Seeded {len(new_achievements)} achievements")
    else:
        print("[OK] Achievements already seeded")


def seed_badges(db: Session):
    """Seed default badges"""

    badges = [
        # Achievement-based badges
        Badge(
            code='bronze_collector',
            name='Bronze Collector',
            description='Unlock all bronze tier achievements',
            icon_url='/static/badges/bronze-collector.png',
            color_hex='#cd7f32',
            rarity='common',
            requirement_type='tier_collection',
            requirement_data={'tier': 'bronze'},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='silver_collector',
            name='Silver Collector',
            description='Unlock all silver tier achievements',
            icon_url='/static/badges/silver-collector.png',
            color_hex='#c0c0c0',
            rarity='uncommon',
            requirement_type='tier_collection',
            requirement_data={'tier': 'silver'},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='gold_collector',
            name='Gold Collector',
            description='Unlock all gold tier achievements',
            icon_url='/static/badges/gold-collector.png',
            color_hex='#ffd700',
            rarity='rare',
            requirement_type='tier_collection',
            requirement_data={'tier': 'gold'},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='platinum_collector',
            name='Platinum Collector',
            description='Unlock all platinum tier achievements',
            icon_url='/static/badges/platinum-collector.png',
            color_hex='#e5e4e2',
            rarity='epic',
            requirement_type='tier_collection',
            requirement_data={'tier': 'platinum'},
            is_active=True,
            is_displayable=True
        ),

        # Points-based badges
        Badge(
            code='points_500',
            name='Rising Star',
            description='Earn 500 achievement points',
            icon_url='/static/badges/rising-star.png',
            color_hex='#3b82f6',
            rarity='uncommon',
            requirement_type='points',
            requirement_data={'threshold': 500},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='points_1000',
            name='Achievement Master',
            description='Earn 1,000 achievement points',
            icon_url='/static/badges/achievement-master.png',
            color_hex='#8b5cf6',
            rarity='rare',
            requirement_type='points',
            requirement_data={'threshold': 1000},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='points_2000',
            name='Legend',
            description='Earn 2,000 achievement points',
            icon_url='/static/badges/legend.png',
            color_hex='#ec4899',
            rarity='legendary',
            requirement_type='points',
            requirement_data={'threshold': 2000},
            is_active=True,
            is_displayable=True
        ),

        # Category-based badges
        Badge(
            code='tracking_master',
            name='Tracking Master',
            description='Complete all tracking achievements',
            icon_url='/static/badges/tracking-master.png',
            color_hex='#10b981',
            rarity='rare',
            requirement_type='category_collection',
            requirement_data={'category': 'tracking'},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='savings_guru',
            name='Savings Guru',
            description='Complete all savings achievements',
            icon_url='/static/badges/savings-guru.png',
            color_hex='#10b981',
            rarity='rare',
            requirement_type='category_collection',
            requirement_data={'category': 'saving'},
            is_active=True,
            is_displayable=True
        ),
        Badge(
            code='spending_ninja',
            name='Spending Ninja',
            description='Complete all spending achievements',
            icon_url='/static/badges/spending-ninja.png',
            color_hex='#ef4444',
            rarity='rare',
            requirement_type='category_collection',
            requirement_data={'category': 'spending'},
            is_active=True,
            is_displayable=True
        ),
    ]

    # Check if badges already exist
    existing_codes = {b.code for b in db.query(Badge.code).all()}

    new_badges = [b for b in badges if b.code not in existing_codes]

    if new_badges:
        db.add_all(new_badges)
        db.commit()
        print(f"[OK] Seeded {len(new_badges)} badges")
    else:
        print("[OK] Badges already seeded")


def main():
    """Run all seed functions"""
    print("Starting gamification seed data...")
    print()

    db = SessionLocal()

    try:
        seed_achievements(db)
        seed_badges(db)
        print()
        print("[SUCCESS] Gamification seed data completed successfully!")
    except Exception as e:
        print(f"[ERROR] Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
