"""Unit tests for the split expense service (Phase 31)"""
import pytest
from datetime import date
from decimal import Decimal

from app.services import split_expense_service as svc
from app.models.split_expense import SplitContact, SplitExpense, SplitParticipant, SplitStatus


@pytest.mark.unit
class TestContactCRUD:
    def test_create_contact(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "Alice", "alice@example.com")
        assert contact.id is not None
        assert contact.name == "Alice"
        assert contact.email == "alice@example.com"
        assert contact.user_id == test_user.id

    def test_create_contact_strips_whitespace(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "  Bob  ")
        assert contact.name == "Bob"

    def test_list_contacts_only_own(self, db_session, test_user, test_user_2):
        svc.create_contact(db_session, test_user.id, "Alice")
        svc.create_contact(db_session, test_user_2.id, "Other")
        contacts = svc.list_contacts(db_session, test_user.id)
        assert len(contacts) == 1
        assert contacts[0].name == "Alice"

    def test_list_contacts_alphabetical(self, db_session, test_user):
        svc.create_contact(db_session, test_user.id, "Zara")
        svc.create_contact(db_session, test_user.id, "Alice")
        svc.create_contact(db_session, test_user.id, "Mike")
        contacts = svc.list_contacts(db_session, test_user.id)
        assert [c.name for c in contacts] == ["Alice", "Mike", "Zara"]

    def test_update_contact_name(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "Old Name")
        updated = svc.update_contact(db_session, test_user.id, contact.id, "New Name", None, None)
        assert updated.name == "New Name"

    def test_update_contact_wrong_user_returns_none(self, db_session, test_user, test_user_2):
        contact = svc.create_contact(db_session, test_user.id, "Alice")
        result = svc.update_contact(db_session, test_user_2.id, contact.id, "Hacker", None, None)
        assert result is None

    def test_delete_contact(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "ToDelete")
        assert svc.delete_contact(db_session, test_user.id, contact.id) is True
        assert svc.get_contact(db_session, test_user.id, contact.id) is None

    def test_delete_contact_wrong_user_returns_false(self, db_session, test_user, test_user_2):
        contact = svc.create_contact(db_session, test_user.id, "Alice")
        assert svc.delete_contact(db_session, test_user_2.id, contact.id) is False


@pytest.mark.unit
class TestSplitCRUD:
    def _make_participants(self, db_session, test_user, payer_name="Me", others=None):
        participants = [{"name": payer_name, "amount": Decimal("10"), "is_payer": True, "contact_id": None}]
        for name, amount in (others or [("Bob", "10")]):
            participants.append({"name": name, "amount": Decimal(str(amount)), "is_payer": False, "contact_id": None})
        return participants

    def test_create_split(self, db_session, test_user):
        participants = self._make_participants(db_session, test_user, others=[("Bob", "15")])
        split = svc.create_split(
            db_session,
            user_id=test_user.id,
            title="Dinner",
            total_amount=Decimal("25"),
            currency_code="USD",
            split_date=date.today(),
            participants=participants,
        )
        assert split.id is not None
        assert split.title == "Dinner"
        assert split.status == SplitStatus.OPEN
        assert len(split.participants) == 2

    def test_payer_auto_settled(self, db_session, test_user):
        participants = self._make_participants(db_session, test_user, others=[("Bob", "15")])
        split = svc.create_split(
            db_session, test_user.id, "Lunch", Decimal("25"), "USD", date.today(), participants
        )
        payer = next(p for p in split.participants if p.is_payer)
        assert payer.is_settled is True

    def test_list_splits_by_status(self, db_session, test_user):
        participants = self._make_participants(db_session, test_user, others=[("Bob", "10")])
        svc.create_split(db_session, test_user.id, "Open Split", Decimal("20"), "USD", date.today(), participants)
        open_splits = svc.list_splits(db_session, test_user.id, status="open")
        settled_splits = svc.list_splits(db_session, test_user.id, status="settled")
        assert len(open_splits) == 1
        assert len(settled_splits) == 0

    def test_list_splits_only_own(self, db_session, test_user, test_user_2):
        participants = self._make_participants(db_session, test_user, others=[("Bob", "10")])
        svc.create_split(db_session, test_user.id, "Mine", Decimal("20"), "USD", date.today(), participants)
        svc.create_split(db_session, test_user_2.id, "Theirs", Decimal("20"), "USD", date.today(), participants)
        assert len(svc.list_splits(db_session, test_user.id)) == 1

    def test_delete_split(self, db_session, test_user):
        participants = self._make_participants(db_session, test_user, others=[("Bob", "10")])
        split = svc.create_split(
            db_session, test_user.id, "ToDelete", Decimal("20"), "USD", date.today(), participants
        )
        assert svc.delete_split(db_session, test_user.id, split.id) is True
        assert svc.get_split(db_session, test_user.id, split.id) is None

    def test_delete_split_wrong_user(self, db_session, test_user, test_user_2):
        participants = self._make_participants(db_session, test_user, others=[("Bob", "10")])
        split = svc.create_split(
            db_session, test_user.id, "Mine", Decimal("20"), "USD", date.today(), participants
        )
        assert svc.delete_split(db_session, test_user_2.id, split.id) is False


@pytest.mark.unit
class TestSettlement:
    def _create_split_with_contact(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "Bob")
        participants = [
            {"name": "Me", "amount": Decimal("10"), "is_payer": True, "contact_id": None},
            {"name": "Bob", "amount": Decimal("15"), "is_payer": False, "contact_id": contact.id},
        ]
        split = svc.create_split(
            db_session, test_user.id, "Test Split", Decimal("25"), "USD", date.today(), participants
        )
        return split, contact

    def test_settle_participant(self, db_session, test_user):
        split, _ = self._create_split_with_contact(db_session, test_user)
        non_payer = next(p for p in split.participants if not p.is_payer)
        result = svc.settle_participant(db_session, test_user.id, split.id, non_payer.id)
        assert result.is_settled is True
        assert result.settled_at is not None

    def test_settling_all_marks_split_settled(self, db_session, test_user):
        split, _ = self._create_split_with_contact(db_session, test_user)
        non_payer = next(p for p in split.participants if not p.is_payer)
        svc.settle_participant(db_session, test_user.id, split.id, non_payer.id)
        db_session.refresh(split)
        assert split.status == SplitStatus.SETTLED

    def test_unsettle_participant(self, db_session, test_user):
        split, _ = self._create_split_with_contact(db_session, test_user)
        non_payer = next(p for p in split.participants if not p.is_payer)
        svc.settle_participant(db_session, test_user.id, split.id, non_payer.id)
        result = svc.unsettle_participant(db_session, test_user.id, split.id, non_payer.id)
        assert result.is_settled is False
        assert result.settled_at is None
        db_session.refresh(split)
        assert split.status == SplitStatus.OPEN

    def test_settle_wrong_user_returns_none(self, db_session, test_user, test_user_2):
        split, _ = self._create_split_with_contact(db_session, test_user)
        non_payer = next(p for p in split.participants if not p.is_payer)
        result = svc.settle_participant(db_session, test_user_2.id, split.id, non_payer.id)
        assert result is None


@pytest.mark.unit
class TestBalances:
    def test_empty_balances_when_no_splits(self, db_session, test_user):
        result = svc.get_balances(db_session, test_user.id)
        assert result["contacts"] == []
        assert result["total_you_are_owed"] == 0
        assert result["total_you_owe"] == 0

    def test_contact_owes_after_open_split(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "Alice")
        participants = [
            {"name": "Me", "amount": Decimal("50"), "is_payer": True, "contact_id": None},
            {"name": "Alice", "amount": Decimal("25"), "is_payer": False, "contact_id": contact.id},
        ]
        svc.create_split(db_session, test_user.id, "Dinner", Decimal("75"), "USD", date.today(), participants)

        result = svc.get_balances(db_session, test_user.id)
        assert len(result["contacts"]) == 1
        assert result["contacts"][0]["contact_name"] == "Alice"
        assert result["contacts"][0]["they_owe_you"] == 25.0
        assert result["total_you_are_owed"] == 25.0

    def test_settled_split_excluded_from_balances(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "Bob")
        participants = [
            {"name": "Me", "amount": Decimal("30"), "is_payer": True, "contact_id": None},
            {"name": "Bob", "amount": Decimal("30"), "is_payer": False, "contact_id": contact.id},
        ]
        split = svc.create_split(
            db_session, test_user.id, "Lunch", Decimal("60"), "USD", date.today(), participants
        )
        non_payer = next(p for p in split.participants if not p.is_payer)
        svc.settle_participant(db_session, test_user.id, split.id, non_payer.id)

        result = svc.get_balances(db_session, test_user.id)
        # Settled split — no balance owed
        assert result["total_you_are_owed"] == 0


@pytest.mark.unit
class TestSerializers:
    def test_split_to_dict_structure(self, db_session, test_user):
        participants = [
            {"name": "Me", "amount": Decimal("20"), "is_payer": True, "contact_id": None},
            {"name": "Bob", "amount": Decimal("20"), "is_payer": False, "contact_id": None},
        ]
        split = svc.create_split(
            db_session, test_user.id, "Test", Decimal("40"), "USD", date.today(), participants
        )
        d = svc.split_to_dict(split)
        assert d["title"] == "Test"
        assert d["status"] == SplitStatus.OPEN
        assert len(d["participants"]) == 2
        assert all("id" in p and "amount" in p and "is_payer" in p for p in d["participants"])

    def test_contact_to_dict_structure(self, db_session, test_user):
        contact = svc.create_contact(db_session, test_user.id, "Alice", "alice@example.com", "note")
        d = svc.contact_to_dict(contact)
        assert d["name"] == "Alice"
        assert d["email"] == "alice@example.com"
        assert d["notes"] == "note"
        assert "created_at" in d
