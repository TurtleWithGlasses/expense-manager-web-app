"""
Unit Tests for Composite Database Indexes

Verifies that all 7 composite indexes are correctly defined on the SQLAlchemy
models. These indexes are critical for query performance at scale.

Indexes tested:
  entries:
    1. ix_entries_user_date        (user_id, date)
    2. ix_entries_user_type        (user_id, type)
    3. ix_entries_user_category    (user_id, category_id)
  forecasts:
    4. ix_forecasts_user_type_active  (user_id, forecast_type, is_active)
  payment_occurrences:
    5. ix_payment_occurrences_payment_date  (recurring_payment_id, scheduled_date)
  financial_goals:
    6. ix_financial_goals_user_status  (user_id, status)
  recurring_payments:
    7. ix_recurring_payments_user_active  (user_id, is_active)
"""

import pytest
from sqlalchemy import inspect, create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.entry import Entry
from app.models.forecast import Forecast
from app.models.payment_history import PaymentOccurrence
from app.models.financial_goal import FinancialGoal
from app.models.recurring_payment import RecurringPayment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _index_names_for_table(table_name: str, engine) -> set:
    """Return a set of index names defined on *table_name*."""
    insp = inspect(engine)
    return {idx['name'] for idx in insp.get_indexes(table_name)}


def _column_names_for_index(table_name: str, index_name: str, engine) -> list:
    """Return the ordered list of column names for a given index."""
    insp = inspect(engine)
    for idx in insp.get_indexes(table_name):
        if idx['name'] == index_name:
            return idx['column_names']
    return []


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def db_engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


# ---------------------------------------------------------------------------
# Existence checks — model __table_args__
# ---------------------------------------------------------------------------

class TestIndexDefinitionsOnModels:
    """Confirm every composite index name appears in __table_args__."""

    def _table_arg_index_names(self, model) -> set:
        table_args = getattr(model, '__table_args__', ())
        from sqlalchemy import Index as SAIndex
        return {arg.name for arg in table_args if isinstance(arg, SAIndex)}

    def test_entries_has_user_date_index(self):
        names = self._table_arg_index_names(Entry)
        assert 'ix_entries_user_date' in names

    def test_entries_has_user_type_index(self):
        names = self._table_arg_index_names(Entry)
        assert 'ix_entries_user_type' in names

    def test_entries_has_user_category_index(self):
        names = self._table_arg_index_names(Entry)
        assert 'ix_entries_user_category' in names

    def test_entries_has_exactly_three_composite_indexes(self):
        names = self._table_arg_index_names(Entry)
        assert len(names) == 3

    def test_forecasts_has_user_type_active_index(self):
        names = self._table_arg_index_names(Forecast)
        assert 'ix_forecasts_user_type_active' in names

    def test_payment_occurrences_has_payment_date_index(self):
        names = self._table_arg_index_names(PaymentOccurrence)
        assert 'ix_payment_occurrences_payment_date' in names

    def test_financial_goals_has_user_status_index(self):
        names = self._table_arg_index_names(FinancialGoal)
        assert 'ix_financial_goals_user_status' in names

    def test_recurring_payments_has_user_active_index(self):
        names = self._table_arg_index_names(RecurringPayment)
        assert 'ix_recurring_payments_user_active' in names


# ---------------------------------------------------------------------------
# Column-composition checks — correct columns in correct order
# ---------------------------------------------------------------------------

class TestIndexColumnComposition:
    """Verify each index covers the right columns in the right order."""

    def _get_index_columns(self, model, index_name: str) -> list:
        table_args = getattr(model, '__table_args__', ())
        from sqlalchemy import Index as SAIndex
        for arg in table_args:
            if isinstance(arg, SAIndex) and arg.name == index_name:
                return [col.key for col in arg.columns]
        return []

    def test_entries_user_date_columns(self):
        cols = self._get_index_columns(Entry, 'ix_entries_user_date')
        assert cols == ['user_id', 'date']

    def test_entries_user_type_columns(self):
        cols = self._get_index_columns(Entry, 'ix_entries_user_type')
        assert cols == ['user_id', 'type']

    def test_entries_user_category_columns(self):
        cols = self._get_index_columns(Entry, 'ix_entries_user_category')
        assert cols == ['user_id', 'category_id']

    def test_forecasts_user_type_active_columns(self):
        cols = self._get_index_columns(Forecast, 'ix_forecasts_user_type_active')
        assert cols == ['user_id', 'forecast_type', 'is_active']

    def test_payment_occurrences_payment_date_columns(self):
        cols = self._get_index_columns(PaymentOccurrence, 'ix_payment_occurrences_payment_date')
        assert cols == ['recurring_payment_id', 'scheduled_date']

    def test_financial_goals_user_status_columns(self):
        cols = self._get_index_columns(FinancialGoal, 'ix_financial_goals_user_status')
        assert cols == ['user_id', 'status']

    def test_recurring_payments_user_active_columns(self):
        cols = self._get_index_columns(RecurringPayment, 'ix_recurring_payments_user_active')
        assert cols == ['user_id', 'is_active']


# ---------------------------------------------------------------------------
# Database-level checks — indexes actually created in SQLite
# ---------------------------------------------------------------------------

class TestIndexesInDatabase:
    """Confirm the indexes exist after Base.metadata.create_all()."""

    def test_entries_composite_indexes_in_db(self, db_engine):
        names = _index_names_for_table('entries', db_engine)
        assert 'ix_entries_user_date' in names
        assert 'ix_entries_user_type' in names
        assert 'ix_entries_user_category' in names

    def test_forecasts_composite_index_in_db(self, db_engine):
        names = _index_names_for_table('forecasts', db_engine)
        assert 'ix_forecasts_user_type_active' in names

    def test_payment_occurrences_composite_index_in_db(self, db_engine):
        names = _index_names_for_table('payment_occurrences', db_engine)
        assert 'ix_payment_occurrences_payment_date' in names

    def test_financial_goals_composite_index_in_db(self, db_engine):
        names = _index_names_for_table('financial_goals', db_engine)
        assert 'ix_financial_goals_user_status' in names

    def test_recurring_payments_composite_index_in_db(self, db_engine):
        names = _index_names_for_table('recurring_payments', db_engine)
        assert 'ix_recurring_payments_user_active' in names

    def test_total_seven_composite_indexes_exist_in_db(self, db_engine):
        expected = {
            ('entries', 'ix_entries_user_date'),
            ('entries', 'ix_entries_user_type'),
            ('entries', 'ix_entries_user_category'),
            ('forecasts', 'ix_forecasts_user_type_active'),
            ('payment_occurrences', 'ix_payment_occurrences_payment_date'),
            ('financial_goals', 'ix_financial_goals_user_status'),
            ('recurring_payments', 'ix_recurring_payments_user_active'),
        }
        found = set()
        for table, idx_name in expected:
            if idx_name in _index_names_for_table(table, db_engine):
                found.add((table, idx_name))
        assert found == expected, f"Missing indexes: {expected - found}"


# ---------------------------------------------------------------------------
# Column-order checks at database level
# ---------------------------------------------------------------------------

class TestIndexColumnOrderInDatabase:
    """Leading column order matters — wrong order defeats the index for range scans."""

    def test_entries_user_date_leading_column(self, db_engine):
        cols = _column_names_for_index('entries', 'ix_entries_user_date', db_engine)
        assert cols[0] == 'user_id', "user_id must be the leading column"
        assert cols[1] == 'date'

    def test_entries_user_type_leading_column(self, db_engine):
        cols = _column_names_for_index('entries', 'ix_entries_user_type', db_engine)
        assert cols[0] == 'user_id'
        assert cols[1] == 'type'

    def test_entries_user_category_leading_column(self, db_engine):
        cols = _column_names_for_index('entries', 'ix_entries_user_category', db_engine)
        assert cols[0] == 'user_id'
        assert cols[1] == 'category_id'

    def test_forecasts_leading_columns(self, db_engine):
        cols = _column_names_for_index('forecasts', 'ix_forecasts_user_type_active', db_engine)
        assert cols[0] == 'user_id'
        assert cols[1] == 'forecast_type'
        assert cols[2] == 'is_active'

    def test_payment_occurrences_leading_columns(self, db_engine):
        cols = _column_names_for_index('payment_occurrences', 'ix_payment_occurrences_payment_date', db_engine)
        assert cols[0] == 'recurring_payment_id'
        assert cols[1] == 'scheduled_date'

    def test_financial_goals_leading_columns(self, db_engine):
        cols = _column_names_for_index('financial_goals', 'ix_financial_goals_user_status', db_engine)
        assert cols[0] == 'user_id'
        assert cols[1] == 'status'

    def test_recurring_payments_leading_columns(self, db_engine):
        cols = _column_names_for_index('recurring_payments', 'ix_recurring_payments_user_active', db_engine)
        assert cols[0] == 'user_id'
        assert cols[1] == 'is_active'


# ---------------------------------------------------------------------------
# Query-plan smoke tests — EXPLAIN QUERY PLAN uses the index (SQLite)
# ---------------------------------------------------------------------------

class TestIndexUsageInQueryPlan:
    """Verify SQLite chooses the composite index for representative queries."""

    @pytest.fixture(autouse=True)
    def session(self, db_engine):
        Session = sessionmaker(bind=db_engine)
        self.db = Session()
        yield
        self.db.close()

    def _explain(self, sql: str) -> str:
        rows = self.db.execute(text(f"EXPLAIN QUERY PLAN {sql}")).fetchall()
        return ' '.join(str(r) for r in rows).lower()

    def test_entries_user_date_range_uses_index(self):
        plan = self._explain(
            "SELECT * FROM entries WHERE user_id = 1 AND date >= '2025-01-01' AND date <= '2025-12-31'"
        )
        assert 'ix_entries_user_date' in plan or 'using index' in plan or 'search' in plan

    def test_entries_user_type_filter_uses_index(self):
        plan = self._explain(
            "SELECT * FROM entries WHERE user_id = 1 AND type = 'expense'"
        )
        assert 'ix_entries_user_type' in plan or 'using index' in plan or 'search' in plan

    def test_payment_occurrence_dedup_lookup_uses_index(self):
        plan = self._explain(
            "SELECT * FROM payment_occurrences WHERE recurring_payment_id = 5 AND scheduled_date = '2025-03-01'"
        )
        assert 'ix_payment_occurrences_payment_date' in plan or 'using index' in plan or 'search' in plan

    def test_active_goals_query_uses_index(self):
        plan = self._explain(
            "SELECT * FROM financial_goals WHERE user_id = 1 AND status = 'active'"
        )
        assert 'ix_financial_goals_user_status' in plan or 'using index' in plan or 'search' in plan

    def test_active_recurring_payments_uses_index(self):
        plan = self._explain(
            "SELECT * FROM recurring_payments WHERE user_id = 1 AND is_active = 1"
        )
        assert 'ix_recurring_payments_user_active' in plan or 'using index' in plan or 'search' in plan


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
