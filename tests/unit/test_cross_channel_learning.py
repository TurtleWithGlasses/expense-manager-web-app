"""
G-5d: Cross-channel merchant→category learning tests.

Verifies that merchant mappings written by the web app are visible to the
Telegram bot and vice versa, because both share the same
merchant_category_mappings table filtered by user_id.
"""
import pytest
from datetime import datetime

from app.models.merchant_mapping import MerchantCategoryMapping
from app.services.category_suggester import normalise_merchant_key, suggest_category


# ---------------------------------------------------------------------------
# Helpers that mimic the upsert logic in entries.py and telegram_bot.py
# ---------------------------------------------------------------------------

def _upsert_mapping(db, user_id: int, merchant: str, category_id: int) -> MerchantCategoryMapping:
    """Replicate the upsert used by both channels."""
    key = normalise_merchant_key(merchant)
    existing = db.query(MerchantCategoryMapping).filter_by(
        user_id=user_id, merchant_key=key
    ).first()
    if existing:
        existing.category_id = category_id
        existing.use_count = (existing.use_count or 0) + 1
        existing.last_used = datetime.utcnow()
        db.flush()
        return existing
    mapping = MerchantCategoryMapping(
        user_id=user_id,
        merchant_key=key,
        category_id=category_id,
        use_count=1,
        last_used=datetime.utcnow(),
    )
    db.add(mapping)
    db.flush()
    return mapping


# ---------------------------------------------------------------------------
# normalise_merchant_key
# ---------------------------------------------------------------------------

class TestNormaliseMerchantKey:
    def test_lowercases(self):
        assert normalise_merchant_key("STARBUCKS") == "starbucks"

    def test_removes_punctuation(self):
        assert normalise_merchant_key("McDonald's") == "mcdonald s"

    def test_keeps_first_three_words(self):
        key = normalise_merchant_key("Defacto Perakende Ticaret A.S.")
        assert key == "defacto perakende ticaret"

    def test_ocr_variant_same_key(self):
        """OCR variants with different tails produce the same key (first 3 words)."""
        # Both start with "Defacto Perakende Ticaret"; only the tail differs
        a = normalise_merchant_key("Defacto Perakende Ticaret A.Ş.")
        b = normalise_merchant_key("Defacto Perakende Ticaret Ltd. Şirketi")
        assert a == b == "defacto perakende ticaret"

    def test_single_word(self):
        assert normalise_merchant_key("Carrefour") == "carrefour"


# ---------------------------------------------------------------------------
# Web app → Bot direction
# ---------------------------------------------------------------------------

class TestWebAppToBot:
    def test_web_saves_bot_reads(self, db_session, test_user, test_categories):
        """Mapping written by web app is returned by suggest_category (bot would call same fn)."""
        food_cat = test_categories[0]  # "Food & Dining"

        # Simulate web app saving a mapping
        _upsert_mapping(db_session, test_user.id, "Starbucks", food_cat.id)
        db_session.commit()

        result = suggest_category(
            merchant="STARBUCKS",
            ocr_text="",
            user_categories=test_categories,
            db=db_session,
            user_id=test_user.id,
        )

        assert result is not None
        assert result["category_id"] == food_cat.id
        assert result["matched_type"] == "learned"

    def test_web_update_reflected(self, db_session, test_user, test_categories):
        """After web app reassigns a merchant, new category is returned."""
        food_cat = test_categories[0]
        transport_cat = test_categories[1]

        _upsert_mapping(db_session, test_user.id, "Shell", food_cat.id)
        db_session.commit()

        # User corrects it on the web → upsert overwrites
        _upsert_mapping(db_session, test_user.id, "Shell", transport_cat.id)
        db_session.commit()

        result = suggest_category(
            merchant="Shell",
            ocr_text="",
            user_categories=test_categories,
            db=db_session,
            user_id=test_user.id,
        )

        assert result is not None
        assert result["category_id"] == transport_cat.id


# ---------------------------------------------------------------------------
# Bot → Web app direction
# ---------------------------------------------------------------------------

class TestBotToWebApp:
    def test_bot_saves_web_reads(self, db_session, test_user, test_categories):
        """Mapping written by bot is returned by suggest_category (web app calls same fn)."""
        shopping_cat = test_categories[2]  # "Shopping"

        # Simulate bot saving a mapping (same upsert logic)
        _upsert_mapping(db_session, test_user.id, "Zara", shopping_cat.id)
        db_session.commit()

        result = suggest_category(
            merchant="ZARA",
            ocr_text="",
            user_categories=test_categories,
            db=db_session,
            user_id=test_user.id,
        )

        assert result is not None
        assert result["category_id"] == shopping_cat.id
        assert result["matched_type"] == "learned"


# ---------------------------------------------------------------------------
# User isolation
# ---------------------------------------------------------------------------

class TestUserIsolation:
    def test_user_a_mapping_invisible_to_user_b(
        self, db_session, test_user, test_user_2, test_categories
    ):
        """User A's mapping must not affect User B's suggestions."""
        food_cat = test_categories[0]

        # User B has no categories — create one
        from app.models.category import Category
        cat_b = Category(name="Misc", user_id=test_user_2.id)
        db_session.add(cat_b)
        db_session.flush()

        # User A saves a mapping
        _upsert_mapping(db_session, test_user.id, "Migros", food_cat.id)
        db_session.commit()

        # User B scans the same merchant — should get no learned result
        result = suggest_category(
            merchant="Migros",
            ocr_text="",
            user_categories=[cat_b],
            db=db_session,
            user_id=test_user_2.id,
        )

        # No learned mapping for user B → either keyword match or None; never user A's mapping
        if result is not None:
            assert result["matched_type"] != "learned", (
                "User B should not receive User A's learned mapping"
            )

    def test_both_users_same_merchant_different_categories(
        self, db_session, test_user, test_user_2, test_categories
    ):
        """Two users can map the same merchant to different categories independently."""
        from app.models.category import Category

        food_cat = test_categories[0]   # belongs to test_user

        cat_b = Category(name="Groceries", user_id=test_user_2.id)
        db_session.add(cat_b)
        db_session.flush()

        _upsert_mapping(db_session, test_user.id, "A101", food_cat.id)
        _upsert_mapping(db_session, test_user_2.id, "A101", cat_b.id)
        db_session.commit()

        res_a = suggest_category("A101", "", test_categories, db_session, test_user.id)
        res_b = suggest_category("A101", "", [cat_b], db_session, test_user_2.id)

        assert res_a is not None and res_a["category_id"] == food_cat.id
        assert res_b is not None and res_b["category_id"] == cat_b.id


# ---------------------------------------------------------------------------
# use_count increments
# ---------------------------------------------------------------------------

class TestUseCountIncrement:
    def test_use_count_starts_at_one(self, db_session, test_user, test_categories):
        food_cat = test_categories[0]
        mapping = _upsert_mapping(db_session, test_user.id, "Eataly", food_cat.id)
        db_session.commit()
        assert mapping.use_count == 1

    def test_use_count_increments_on_repeat(self, db_session, test_user, test_categories):
        food_cat = test_categories[0]
        _upsert_mapping(db_session, test_user.id, "Eataly", food_cat.id)
        db_session.commit()

        mapping = _upsert_mapping(db_session, test_user.id, "Eataly", food_cat.id)
        db_session.commit()
        assert mapping.use_count == 2

    def test_use_count_increments_across_channels(self, db_session, test_user, test_categories):
        """Web save + bot save of same merchant → use_count 2."""
        food_cat = test_categories[0]

        # "Web" save
        _upsert_mapping(db_session, test_user.id, "Lidl", food_cat.id)
        db_session.commit()

        # "Bot" save
        mapping = _upsert_mapping(db_session, test_user.id, "Lidl", food_cat.id)
        db_session.commit()

        assert mapping.use_count == 2


# ---------------------------------------------------------------------------
# Deleted category (SET NULL) handled gracefully
# ---------------------------------------------------------------------------

class TestDeletedCategory:
    def test_null_category_id_returns_no_learned_match(
        self, db_session, test_user, test_categories
    ):
        """If the mapped category was deleted (category_id=NULL), fall through to keyword match."""
        from app.models.category import Category

        # Create a throwaway category and map a merchant to it
        throwaway = Category(name="Throwaway", user_id=test_user.id)
        db_session.add(throwaway)
        db_session.flush()

        _upsert_mapping(db_session, test_user.id, "SomeStore", throwaway.id)
        db_session.commit()

        # Simulate cascade SET NULL — set category_id to None directly
        key = normalise_merchant_key("SomeStore")
        row = db_session.query(MerchantCategoryMapping).filter_by(
            user_id=test_user.id, merchant_key=key
        ).one()
        row.category_id = None
        db_session.commit()

        # suggest_category must not crash and must not return learned result
        result = suggest_category(
            merchant="SomeStore",
            ocr_text="",
            user_categories=test_categories,
            db=db_session,
            user_id=test_user.id,
        )

        if result is not None:
            assert result["matched_type"] != "learned"


# ---------------------------------------------------------------------------
# OCR variant normalisation
# ---------------------------------------------------------------------------

class TestOCRVariantNormalisation:
    def test_ocr_variants_resolve_to_same_mapping(
        self, db_session, test_user, test_categories
    ):
        """Minor OCR tail variation should still hit the stored mapping."""
        food_cat = test_categories[0]

        # Stored key is first 3 words of "Burger King Turkiye Ltd"
        _upsert_mapping(db_session, test_user.id, "Burger King Turkiye Ltd", food_cat.id)
        db_session.commit()

        # OCR variant has extra noise after the third word
        result = suggest_category(
            merchant="Burger King Turkiye A.S. Restorant",
            ocr_text="",
            user_categories=test_categories,
            db=db_session,
            user_id=test_user.id,
        )

        assert result is not None
        assert result["category_id"] == food_cat.id
        assert result["matched_type"] == "learned"

    def test_case_and_punctuation_insensitive(
        self, db_session, test_user, test_categories
    ):
        shopping_cat = test_categories[2]
        _upsert_mapping(db_session, test_user.id, "H&M", shopping_cat.id)
        db_session.commit()

        result = suggest_category(
            merchant="h&m",
            ocr_text="",
            user_categories=test_categories,
            db=db_session,
            user_id=test_user.id,
        )

        assert result is not None
        assert result["category_id"] == shopping_cat.id
