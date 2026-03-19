"""Unit tests for savings challenges – challenge service and seed (Phase 3.2)"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.gamification.challenge_service import ChallengeService
from app.services.gamification.challenge_seed import seed_default_challenges, DEFAULT_CHALLENGES
from app.models.challenge import (
    Challenge, UserChallenge, ChallengeStatus, UserChallengeStatus, ChallengeType
)
from app.models.entry import Entry


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_challenge(db_session, **overrides):
    defaults = dict(
        code="test_challenge",
        name="Test Challenge",
        description="A test challenge",
        challenge_type=ChallengeType.WEEKLY,
        completion_criteria={"type": "entry_count", "target": 5},
        xp_reward=100,
        points_reward=50,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=6),
        status=ChallengeStatus.ACTIVE,
    )
    defaults.update(overrides)
    ch = Challenge(**defaults)
    db_session.add(ch)
    db_session.commit()
    db_session.refresh(ch)
    return ch


def _add_entries(db_session, user_id, count, entry_type="expense", amount=10.0):
    from datetime import date, timedelta
    for i in range(count):
        e = Entry(
            user_id=user_id,
            type=entry_type,
            amount=Decimal(str(amount)),
            date=date.today() - timedelta(days=i),
        )
        db_session.add(e)
    db_session.commit()


# ── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestChallengeSeed:
    def test_seed_creates_challenges(self, db_session):
        created = seed_default_challenges(db_session)
        assert created == len(DEFAULT_CHALLENGES)
        total = db_session.query(Challenge).count()
        assert total == len(DEFAULT_CHALLENGES)

    def test_seed_idempotent(self, db_session):
        seed_default_challenges(db_session)
        second = seed_default_challenges(db_session)
        assert second == 0  # nothing created on second call

    def test_seed_all_active(self, db_session):
        seed_default_challenges(db_session)
        challenges = db_session.query(Challenge).all()
        assert all(c.status == ChallengeStatus.ACTIVE for c in challenges)

    def test_seed_unique_codes(self, db_session):
        seed_default_challenges(db_session)
        codes = [c.code for c in db_session.query(Challenge).all()]
        assert len(codes) == len(set(codes))

    def test_seed_has_featured_challenge(self, db_session):
        seed_default_challenges(db_session)
        featured = db_session.query(Challenge).filter(Challenge.is_featured == True).count()
        assert featured >= 1


@pytest.mark.unit
class TestJoinChallenge:
    def test_join_challenge(self, db_session, test_user):
        ch = _make_challenge(db_session)
        service = ChallengeService(db_session)
        uc = service.join_challenge(test_user.id, ch.id)
        assert uc.user_id == test_user.id
        assert uc.challenge_id == ch.id
        assert uc.status == UserChallengeStatus.IN_PROGRESS

    def test_join_increments_participant_count(self, db_session, test_user):
        ch = _make_challenge(db_session)
        assert ch.participant_count == 0
        ChallengeService(db_session).join_challenge(test_user.id, ch.id)
        db_session.refresh(ch)
        assert ch.participant_count == 1

    def test_join_idempotent(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        uc1 = svc.join_challenge(test_user.id, ch.id)
        uc2 = svc.join_challenge(test_user.id, ch.id)
        assert uc1.id == uc2.id  # returns existing record

    def test_join_nonexistent_raises(self, db_session, test_user):
        svc = ChallengeService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.join_challenge(test_user.id, 99999)


@pytest.mark.unit
class TestProgressTracking:
    def test_update_progress(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        uc = svc.update_challenge_progress(test_user.id, ch.id, 3.0)
        assert float(uc.current_progress) == 3.0
        assert float(uc.progress_percentage) == pytest.approx(60.0)

    def test_progress_capped_at_100_percent(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        uc = svc.update_challenge_progress(test_user.id, ch.id, 999.0)
        assert float(uc.progress_percentage) == 100.0

    def test_completion_auto_detected(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        # target is 5
        uc = svc.update_challenge_progress(test_user.id, ch.id, 5.0)
        assert uc.status == UserChallengeStatus.COMPLETED
        assert uc.completed_at is not None

    def test_completion_increments_challenge_count(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        svc.update_challenge_progress(test_user.id, ch.id, 5.0)
        db_session.refresh(ch)
        assert ch.completion_count == 1

    def test_update_not_joined_raises(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        with pytest.raises(ValueError, match="not participating"):
            svc.update_challenge_progress(test_user.id, ch.id, 3.0)


@pytest.mark.unit
class TestClaimRewards:
    def test_claim_rewards(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        svc.update_challenge_progress(test_user.id, ch.id, 5.0)
        rewards = svc.claim_challenge_rewards(test_user.id, ch.id)
        assert rewards["xp_reward"] == ch.xp_reward
        assert rewards["points_reward"] == ch.points_reward

    def test_claim_marks_claimed(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        svc.update_challenge_progress(test_user.id, ch.id, 5.0)
        svc.claim_challenge_rewards(test_user.id, ch.id)
        uc = db_session.query(UserChallenge).filter_by(user_id=test_user.id, challenge_id=ch.id).first()
        assert uc.rewards_claimed is True

    def test_claim_twice_raises(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        svc.update_challenge_progress(test_user.id, ch.id, 5.0)
        svc.claim_challenge_rewards(test_user.id, ch.id)
        with pytest.raises(ValueError, match="already claimed"):
            svc.claim_challenge_rewards(test_user.id, ch.id)

    def test_claim_incomplete_raises(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        with pytest.raises(ValueError):
            svc.claim_challenge_rewards(test_user.id, ch.id)


@pytest.mark.unit
class TestProgressCalculation:
    def test_entry_count_progress(self, db_session, test_user):
        ch = _make_challenge(
            db_session,
            completion_criteria={"type": "entry_count", "target": 3},
            start_date=datetime.utcnow() - timedelta(days=5),
        )
        _add_entries(db_session, test_user.id, 2)
        svc = ChallengeService(db_session)
        progress = svc._calculate_challenge_progress(test_user.id, ch)
        assert progress == 2.0

    def test_no_spend_days_progress(self, db_session, test_user):
        ch = _make_challenge(
            db_session,
            completion_criteria={"type": "no_spend_days", "target": 5},
            start_date=datetime.utcnow() - timedelta(days=6),
        )
        # Add 1 entry today only – so 6 days in range, 1 has expense → 5 no-spend days
        _add_entries(db_session, test_user.id, 1)
        svc = ChallengeService(db_session)
        progress = svc._calculate_challenge_progress(test_user.id, ch)
        assert progress >= 5.0

    def test_save_amount_progress_positive(self, db_session, test_user):
        ch = _make_challenge(db_session, completion_criteria={"type": "save_amount", "target": 100})
        _add_entries(db_session, test_user.id, 1, entry_type="income", amount=200.0)
        _add_entries(db_session, test_user.id, 1, entry_type="expense", amount=50.0)
        svc = ChallengeService(db_session)
        progress = svc._calculate_challenge_progress(test_user.id, ch)
        assert progress == pytest.approx(150.0)

    def test_daily_streak_progress(self, db_session, test_user):
        from datetime import date, timedelta as td
        ch = _make_challenge(
            db_session,
            completion_criteria={"type": "daily_streak", "target": 3},
            start_date=datetime.utcnow() - timedelta(days=10),
        )
        for i in range(3):
            db_session.add(Entry(
                user_id=test_user.id, type="expense",
                amount=Decimal("5"), date=date.today() - td(days=i)
            ))
        db_session.commit()
        svc = ChallengeService(db_session)
        progress = svc._calculate_challenge_progress(test_user.id, ch)
        assert progress >= 3.0


@pytest.mark.unit
class TestChallengeStats:
    def test_stats_empty(self, db_session, test_user):
        stats = ChallengeService(db_session).get_user_challenge_stats(test_user.id)
        assert stats["total_joined"] == 0
        assert stats["completed"] == 0
        assert stats["completion_rate"] == 0

    def test_stats_after_join_and_complete(self, db_session, test_user):
        ch = _make_challenge(db_session)
        svc = ChallengeService(db_session)
        svc.join_challenge(test_user.id, ch.id)
        svc.update_challenge_progress(test_user.id, ch.id, 5.0)
        stats = svc.get_user_challenge_stats(test_user.id)
        assert stats["total_joined"] == 1
        assert stats["completed"] == 1
        assert stats["completion_rate"] == 100.0
