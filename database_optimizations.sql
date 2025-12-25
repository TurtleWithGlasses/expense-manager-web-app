-- Performance Optimization: Composite Indexes
-- Run this after activating venv: python -m alembic upgrade head
-- Or run directly: sqlite3 app.db < database_optimizations.sql

-- =======================
-- ENTRIES TABLE INDEXES
-- =======================

-- 1. User + Date + Type (forecasting, reports, dashboard queries)
CREATE INDEX IF NOT EXISTS idx_entries_user_date_type
ON entries(user_id, date, type);

-- 2. User + Type + Date DESC (recent entries, sorted queries)
CREATE INDEX IF NOT EXISTS idx_entries_user_type_date_desc
ON entries(user_id, type, date DESC);

-- 3. User + Category + Date (category-specific analysis)
CREATE INDEX IF NOT EXISTS idx_entries_user_category_date
ON entries(user_id, category_id, date);

-- 4. User + Date (total spending without type filter)
CREATE INDEX IF NOT EXISTS idx_entries_user_date
ON entries(user_id, date);

-- =======================
-- RECURRING PAYMENTS INDEXES
-- =======================

-- User + Active + Start Date (finding active recurring payments for forecasts)
CREATE INDEX IF NOT EXISTS idx_recurring_payments_user_active_start
ON recurring_payments(user_id, is_active, start_date);

-- =======================
-- FORECASTS TABLE INDEXES
-- =======================

-- User + Type + Created (finding cached forecasts)
CREATE INDEX IF NOT EXISTS idx_forecasts_user_type_created
ON forecasts(user_id, forecast_type, created_at DESC);

-- =======================
-- SCENARIOS TABLE INDEXES
-- =======================

-- User + Active + Created (listing active scenarios)
CREATE INDEX IF NOT EXISTS idx_scenarios_user_active_created
ON scenarios(user_id, is_active, created_at DESC);

-- =======================
-- VERIFY INDEXES
-- =======================

-- Run this to see all indexes:
-- SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name;
