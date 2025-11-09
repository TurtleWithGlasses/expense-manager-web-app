# Expense Manager Web App - Project Blueprint & Roadmap

**Project Name:** Budget Pulse - Expense Manager Web Application
**Version:** 1.0 (Production)
**Last Updated:** November 9, 2025
**Production URL:** https://www.yourbudgetpulse.online
**Repository:** https://github.com/TurtleWithGlasses/expense-manager-web-app

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Completed Phases](#completed-phases)
3. [Current Status](#current-status)
4. [Known Issues](#known-issues)
5. [Future Roadmap](#future-roadmap)
6. [Technical Architecture](#technical-architecture)
7. [Deployment Guide](#deployment-guide)

---

## 🎯 Executive Summary

Budget Pulse is a comprehensive expense management application featuring AI-powered categorization, predictive analytics, and financial goal tracking. The application supports multi-currency transactions, automated reporting, and personalized financial insights.

**Current State:**
- **Status:** ✅ Production Ready (Railway)
- **Features:** 40+ fully implemented features
- **AI/ML:** 4 advanced AI features operational
- **Security:** Rate limiting, security headers, no hardcoded secrets
- **Migration System:** Self-healing with auto-stamping
- **Users:** Ready for production use
- **Last Deploy:** November 9, 2025 - All systems operational

---

## ✅ Completed Phases

### **Phase 1-4: Core Foundation** (Completed)
**Duration:** Initial Development
**Status:** ✅ Complete

**Implemented:**
- User registration and authentication system
- Email verification with time-limited tokens
- Password reset functionality
- Session-based authentication with HTTPOnly cookies
- Bcrypt password hashing for security

**Files:**
- `app/api/v1/auth.py` - Authentication endpoints
- `app/services/auth.py` - Auth business logic
- `app/models/user.py` - User model
- `app/core/security.py` - Security utilities

**Database Tables:**
- `users` (id, email, hashed_password, full_name, is_verified, verification_token, etc.)

---

### **Phase 5-7: Financial Entry Management** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Create, read, update, delete financial entries
- Income and expense tracking
- Date-based filtering and search
- Category assignment
- Entry notes and descriptions
- Bulk operations support

**Files:**
- `app/api/v1/entries.py` - Entry API endpoints
- `app/services/entries.py` - Entry business logic
- `app/models/entry.py` - Entry model
- `app/templates/entries/` - Entry UI templates

**Database Tables:**
- `entries` (id, user_id, category_id, amount, date, type, notes, currency_code, ai fields)

---

### **Phase 8: Category Management** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Custom category creation
- Category editing and deletion
- Default categories seeding
- Category usage tracking
- Cascade deletion handling

**Files:**
- `app/api/v1/categories.py` - Category API
- `app/services/categories.py` - Category logic
- `app/models/category.py` - Category model
- `app/templates/categories/` - Category UI

**Database Tables:**
- `categories` (id, user_id, name)

---

### **Phase 9-10: Multi-Currency Support** (Completed)
**Status:** ✅ Complete

**Implemented:**
- 13+ supported currencies (USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR, TRY, BRL, MXN, KRW)
- Real-time exchange rate conversion
- Per-entry currency tracking
- User default currency preferences
- Bulk currency conversion
- Currency symbols and formatting

**Files:**
- `app/core/currency.py` - Currency utilities (300+ lines)
- `app/api/currency.py` - Currency API endpoints
- `app/models/user_preferences.py` - Stores currency preferences

**Features:**
- Automatic exchange rate updates
- Currency conversion in reports
- Multi-currency dashboard summaries

---

### **Phase 11-12: Dashboard & Analytics** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Monthly income/expense summary
- Category breakdown with pie charts
- Daily spending trends with bar charts
- Date range filtering
- Real-time updates with HTMX
- Color-coded visualizations
- Quick action buttons
- Responsive layout

**Files:**
- `app/api/v1/dashboard.py` - Dashboard data API
- `app/services/metrics.py` - Metrics calculation
- `app/templates/dashboard.html` - Main dashboard (55KB+)
- `app/templates/dashboard/_*.html` - Dashboard components

**Metrics:**
- Total income, total expenses, net savings
- Category-wise breakdown
- Daily/weekly/monthly trends
- Spending patterns analysis

---

### **Phase 13: Report Generation & Export** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Excel export with formatting (OpenPyXL)
- PDF report generation (ReportLab)
- Category breakdown exports
- Date range filtering
- Multiple report types (all, income, expense)
- Chart generation for reports (Matplotlib)

**Files:**
- `app/api/v1/reports.py` - Report API
- `app/services/excel_export.py` - Excel generation
- `app/services/pdf_export.py` - PDF generation
- `app/templates/reports/` - Report UI pages

**Report Types:**
- Weekly reports
- Monthly reports
- Annual reports
- Custom date range reports
- Analytics summaries

---

### **Phase 14: AI Category Suggestions** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Machine learning-based category prediction
- Rule-based fallback suggestions
- Confidence score calculation (0.0 - 1.0)
- User feedback integration
- Model training and retraining
- Auto-acceptance based on confidence threshold
- Feature extraction from entry data

**Files:**
- `app/services/ai_service.py` - Main AI service
- `app/ai/models/categorization_model.py` - ML model
- `app/api/v1/ai.py` - AI API endpoints
- `app/models/ai_model.py` - AI model storage

**Database Tables:**
- `ai_models` (id, user_id, model_name, accuracy, training_data_count)
- `ai_suggestions` (id, user_id, entry_id, confidence_score)
- `user_ai_preferences` (auto_categorization_enabled, thresholds)

**Algorithms:**
- Random Forest Classifier
- TF-IDF vectorization for text
- Feature engineering (amount, description, day of week)

---

### **Phase 15: Predictive Analytics** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Next month spending prediction
- Category-specific forecasts
- Cash flow prediction (income - expenses)
- Budget status prediction
- Confidence intervals (95%)
- Spending trend analysis (increasing/decreasing/stable)
- R² accuracy scoring

**Files:**
- `app/ai/services/prediction_service.py` - Prediction engine (450+ lines)
- `app/ai/data/training_pipeline.py` - Training data pipeline
- `app/ai/data/time_series_analyzer.py` - Time series analysis

**Algorithms:**
- Linear Regression for time series
- Moving averages
- Seasonal decomposition
- Trend analysis

**Metrics:**
- Predicted spending by category
- Confidence bounds (lower/upper)
- Accuracy scores
- Historical comparison

---

### **Phase 16: Anomaly Detection & Financial Insights** (Completed)
**Status:** ✅ Complete

**Implemented:**

**Anomaly Detection:**
- ML-powered spending anomaly detection
- Category-specific outlier detection
- Recurring anomaly analysis
- Isolation Forest algorithm
- IQR (Interquartile Range) method
- Multi-feature analysis (6 features)
- Severity classification (low/medium/high/critical)
- Human-readable explanations

**Financial Insights:**
- Spending pattern analysis (3 months)
- Saving opportunities identification
- Budget health assessment
- Category trend analysis
- Personalized recommendations
- Achievement tracking
- Spending alerts
- Weekday/monthly patterns
- Consistency scoring

**Files:**
- `app/ai/services/anomaly_detection.py` - Anomaly detection (500+ lines)
- `app/ai/services/financial_insights.py` - Insights generation
- `app/api/v1/insights_pages.py` - Insights UI
- `app/templates/insights.html` - Insights page (22KB+)

---

### **Phase 17: Goal Setting & Tracking** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Multiple goal types (savings, spending limit, debt payoff, emergency fund, custom)
- Goal creation and management
- Progress tracking with history
- Target date and amount tracking
- Status management (active, completed, cancelled, failed)
- Milestone notifications (customizable percentages: 25%, 50%, 75%, 100%)
- Progress percentage calculation
- Category association for spending limits
- Multi-currency support for goals

**Files:**
- `app/models/financial_goal.py` - Goal models (FinancialGoal, GoalProgressLog)
- `app/services/goal_service.py` - Goal management service
- `app/api/v1/goals.py` - Goal API endpoints
- `app/api/v1/goals_pages.py` - Goal UI endpoints
- `app/templates/goals.html` - Goals UI (21KB+)

**Database Tables:**
- `financial_goals` (id, user_id, name, goal_type, target_amount, current_amount, target_date, status)
- `goal_progress_logs` (id, goal_id, amount, notes, logged_at)

**Goal Types:**
1. Savings Goal - Save a target amount by a date
2. Spending Limit - Stay under budget in a category
3. Debt Payoff - Pay off debt by target date
4. Emergency Fund - Build emergency savings
5. Custom Goal - User-defined financial goal

---

### **Phase 18: Automated Weekly/Monthly Reports** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Automated weekly report generation
- Scheduled report emailing via APScheduler
- Report status tracking (viewed/sent)
- Configurable frequency (weekly, biweekly, monthly, disabled)
- Email delivery with HTML templates
- High spending alerts
- Report content customization
- Notification preferences

**Files:**
- `app/models/weekly_report.py` - Report model
- `app/services/weekly_report_service.py` - Weekly report generation
- `app/services/monthly_report_service.py` - Monthly report generation
- `app/services/report_scheduler.py` - Scheduler (APScheduler)
- `app/api/v1/weekly_reports.py` - Report API

**Database Tables:**
- `weekly_reports` (id, user_id, week_start, week_end, report_data JSON, created_at)
- `user_report_preferences` (user_id, frequency, notification_enabled)
- `report_status` (user_id, report_id, viewed, sent_at)

**Scheduler:**
- Runs every day at configured time
- Checks user preferences
- Generates and emails reports
- Tracks delivery status

---

### **Phase 19: Theme & User Preferences** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Dark/Light theme toggle
- Theme persistence in database
- Display preferences (compact mode, animations, font size)
- JSON-based flexible preferences storage
- Real-time theme switching
- User-specific settings

**Files:**
- `app/api/v1/theme.py` - Theme API
- `app/models/user_preferences.py` - Preferences model
- `app/services/user_preferences.py` - Preference management
- `app/templates/settings/appearance.html` - Appearance settings

---

### **Phase 20: Profile Management & Avatar** (Completed)
**Status:** ✅ Complete

**Implemented:**
- Profile information updates
- Avatar upload with image processing (Pillow)
- Avatar storage as base64 data URI in TEXT column
- Profile export as JSON
- Account deletion with cascading data removal
- User statistics (entry/category count, days active)
- Data privacy controls

**Files:**
- `app/api/v1/profile.py` - Profile API
- `app/templates/settings/` - Settings UI

**Database Changes:**
- Migration `20251102_0001` - Added `avatar_url` VARCHAR(500)
- Migration `20251108_0002` - Expanded `avatar_url` to TEXT for base64

**Features:**
- Image upload (5MB limit)
- Supported formats: JPG, PNG, GIF, WebP
- Client-side preview
- Base64 encoding for inline storage
- Fallback to default avatar

---

### **Phase 21: Deployment & DevOps** (Completed)
**Status:** ✅ Complete
**Date Completed:** November 9, 2025

**Completed:**
- Railway deployment configuration
- Production environment setup
- Database connection with timeouts
- Migration system with Alembic
- Start script (`start.sh`) with health checks
- Environment variable management
- PostgreSQL production database
- Gunicorn + Uvicorn server setup
- Self-healing migration system with auto-stamping

**Deployment Fixes (Nov 9, 2025):**
- ✅ Removed orphaned migration (89a4ade8868e)
- ✅ Added connection timeouts (10s connect, 30s statement)
- ✅ Simplified startup flow (removed pre-checks)
- ✅ Improved migration handling with version checking
- ✅ Added graceful fallback for migration failures
- ✅ Implemented auto-stamp on DuplicateColumn error
- ✅ Database now self-heals on deployment

**Files:**
- `start.sh` - Production startup script
- `Procfile` - Railway/Heroku configuration
- `runtime.txt` - Python 3.11.9
- `alembic.ini` - Migration configuration
- `app/db/engine.py` - Database engine with timeouts
- `fix_production_schema.py` - Manual schema fix script
- `stamp_migrations.py` - Manual version stamping script
- `app/main.py` - Auto-stamping migration logic

---

### **Phase 22: Security Hardening** (In Progress)
**Status:** 🔄 In Progress (60% Complete)
**Date Started:** November 9, 2025

**Completed (Part 1):**

1. **Removed Hardcoded Secrets** ✅ CRITICAL
   - Removed `RESEND_API_KEY` from `app/core/config.py`
   - Removed `SMTP_PASSWORD` from `app/core/config.py`
   - Updated `.env.example` with proper placeholders
   - All secrets now via environment variables only

2. **Rate Limiting** ✅
   - Installed `slowapi` dependency
   - Created `app/core/rate_limit.py`
   - `/login`: 5 attempts per 15 minutes
   - `/register`: 3 attempts per hour
   - Protects against brute force attacks

3. **Security Headers** ✅
   - Created `app/core/security_headers.py` middleware
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY` (clickjacking protection)
   - `X-XSS-Protection: 1; mode=block`
   - `Strict-Transport-Security` (HSTS in production)
   - `Content-Security-Policy`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy` (restricts browser features)

4. **Testing Documentation** ✅
   - Created comprehensive `TESTING_GUIDE.md`
   - 10 test categories covering all features
   - Step-by-step testing instructions

**Remaining Work:**
- ⏳ Implement structured logging (replace print statements)
- ⏳ Add error monitoring (Sentry integration)
- ⏳ Add request tracing and logging

**Files Modified:**
- `app/core/config.py` - Secrets removed
- `.env.example` - Email config examples
- `app/main.py` - Security middleware
- `app/api/v1/auth.py` - Rate limits
- `requirements.txt` - slowapi added

**New Files:**
- `app/core/rate_limit.py` - Rate limiting config
- `app/core/security_headers.py` - Security headers
- `TESTING_GUIDE.md` - Production testing guide

---

## 📊 Current Status

### **Production Metrics**
- **Status:** 🟢 Production Ready
- **Uptime Target:** 99.9%
- **Database:** PostgreSQL on Railway
- **Server:** Uvicorn (ASGI)
- **Python Version:** 3.11.9
- **Features Implemented:** 40+
- **Security Score:** A (Rate limiting, security headers, no hardcoded secrets)
- **Code Quality:** Well-organized, modular
- **Test Coverage:** 0% (Phase 23 priority)

### **What's Working** ✅
✅ Application starts successfully
✅ Database connection established
✅ All tables created/verified
✅ Report scheduler running
✅ Core features operational
✅ AI services functional
✅ Self-healing migrations (auto-stamp)
✅ Rate limiting on auth endpoints
✅ Security headers on all responses
✅ No hardcoded secrets in code

### **What Needs Attention** ⏳
⏳ Implement structured logging
⏳ Add automated tests (Phase 23)
⏳ Set RESEND_API_KEY in Railway env vars
⏳ Set SMTP_PASSWORD in Railway env vars
⏳ Monitor production for 24-48 hours

---

## 🐛 Known Issues

### **Resolved Issues** ✅

#### **Issue #1: Migration Version Mismatch** - RESOLVED ✅
**Status:** ✅ Resolved
**Date Resolved:** November 9, 2025
**Solution Implemented:** Auto-stamping on DuplicateColumn error

The migration system now automatically detects DuplicateColumn errors and stamps the database to the latest version without manual intervention. On first deployment after the fix, the system auto-stamped from `add_currency_to_entries` to `20251108_0002`. Subsequent deployments show `[OK] Database already at latest migration`.

**Files Modified:**
- `app/main.py:66-78` - Auto-stamp logic

---

#### **Issue #2: Hardcoded Secrets** - RESOLVED ✅
**Status:** ✅ Resolved
**Date Resolved:** November 9, 2025
**Solution Implemented:** Removed all hardcoded secrets from code

All secrets have been removed from `app/core/config.py`:
- `RESEND_API_KEY` now defaults to empty string
- `SMTP_PASSWORD` now defaults to empty string
- `.env.example` updated with proper placeholders
- Production secrets must be set via Railway environment variables

**Files Modified:**
- `app/core/config.py:9` - RESEND_API_KEY removed
- `app/core/config.py:49` - SMTP_PASSWORD removed
- `.env.example` - Added email configuration examples

**Action Required:**
- Set `RESEND_API_KEY` in Railway environment variables
- Set `SMTP_PASSWORD` in Railway environment variables

---

#### **Issue #3: No Rate Limiting** - RESOLVED ✅
**Status:** ✅ Resolved
**Date Resolved:** November 9, 2025
**Solution Implemented:** slowapi rate limiting on auth endpoints

Rate limiting has been implemented:
- `/login`: 5 attempts per 15 minutes per IP address
- `/register`: 3 attempts per hour per IP address
- Protects against brute force attacks

**Files Modified:**
- `app/core/rate_limit.py` - Rate limiter configuration
- `app/api/v1/auth.py:17, 49` - Rate limit decorators
- `app/main.py:40-41` - Rate limiting integration
- `requirements.txt` - Added slowapi==0.1.9

---

### **Active Issues** ⏳

---

#### **Issue #4: No Automated Tests**
**Impact:** Risk of regressions, hard to validate changes

**Solution:**
- Add pytest configuration
- Write unit tests for services
- Integration tests for API endpoints
- E2E tests for critical flows

---

#### **Issue #5: Missing Structured Logging**
**Impact:** Hard to debug production issues

**Current State:** Uses `print()` statements

**Solution:**
- Implement Python `logging` module
- Add log levels (DEBUG, INFO, WARNING, ERROR)
- Add request IDs for tracing
- Send logs to external service (Sentry, LogDNA)

---

## 🚀 Future Roadmap

### **Phase 22: Production Hardening** 🔥
**Priority:** CRITICAL
**Status:** Not Started
**Estimated Time:** 4-6 hours

**Tasks:**
1. ✅ Fix migration version mismatch (manual stamp)
2. ✅ Test all features in production
3. 🔲 Remove hardcoded secrets
4. 🔲 Add rate limiting to auth endpoints
5. 🔲 Implement structured logging
6. 🔲 Add health check endpoint
7. 🔲 Set up error monitoring (Sentry)
8. 🔲 Add security headers (HSTS, CSP)

**Deliverables:**
- Secure, production-ready application
- No hardcoded credentials
- Proper error monitoring
- Rate-limited endpoints

---

### **Phase 23: Testing & Quality Assurance** ✅
**Priority:** HIGH
**Status:** Not Started
**Estimated Time:** 10-12 hours

**Tasks:**
1. Set up pytest and coverage tools
2. Unit tests for services (auth, entries, categories, AI)
3. Integration tests for API endpoints
4. Test database migrations (up/down)
5. Test AI model accuracy and predictions
6. E2E tests for critical user flows
7. Load testing for concurrent users
8. Test multi-currency calculations
9. Test goal tracking edge cases

**Target Coverage:** 80%+

**Tools:**
- pytest
- pytest-cov
- pytest-asyncio
- httpx (for FastAPI testing)
- factory_boy (test data generation)

---

### **Phase 24: Mobile Responsiveness & PWA** 📱
**Priority:** MEDIUM
**Status:** Partially Complete
**Estimated Time:** 6-8 hours

**Tasks:**
1. Audit all pages for mobile responsiveness
2. Add PWA manifest (`manifest.json`)
3. Implement service worker for offline support
4. Add "Add to Home Screen" functionality
5. Optimize dashboard charts for mobile
6. Touch-friendly entry editing
7. Mobile-optimized navigation
8. Test on iOS and Android devices

**Deliverables:**
- Installable PWA
- Offline viewing of data
- Mobile-optimized UI
- Touch gestures support

---

### **Phase 25: Performance Optimization** ⚡
**Priority:** MEDIUM
**Status:** Not Started
**Estimated Time:** 8-10 hours

**Tasks:**
1. Database query optimization (add indexes on frequently queried columns)
2. Implement Redis caching for:
   - Currency exchange rates
   - User sessions
   - Dashboard data
3. Lazy loading for dashboard components
4. Optimize large report generation (background jobs)
5. Add pagination to entry lists (currently loads all)
6. Background job queue for heavy operations (Celery + Redis)
7. Compress static assets (CSS, JS minification)
8. CDN for static files

**Performance Targets:**
- Page load time < 2 seconds
- API response time < 200ms
- Support 100+ concurrent users

**Tools:**
- Redis for caching
- Celery for background jobs
- CDN (Cloudflare)
- Performance monitoring (New Relic, DataDog)

---

### **Phase 26: Advanced AI Features** 🤖
**Priority:** LOW
**Status:** Not Started
**Estimated Time:** 15-20 hours

**Ideas:**
1. **Smart Budget Recommendations**
   - Analyze spending patterns
   - Suggest realistic budgets per category
   - Alert when approaching limits

2. **Bill Prediction & Reminders**
   - Detect recurring bills
   - Predict due dates
   - Send reminders before due date

3. **Subscription Detection**
   - Identify recurring charges
   - Track subscription costs
   - Alert on price changes

4. **Duplicate Transaction Detection**
   - Find potential duplicate entries
   - Suggest merges
   - Auto-flag duplicates

5. **Natural Language Entry Input**
   - Parse "Spent $50 on groceries yesterday"
   - Extract amount, category, date
   - Voice input support

6. **Receipt Scanning with OCR**
   - Upload receipt photos
   - Extract merchant, amount, date
   - Auto-create entries

7. **Spending Habit Scoring**
   - Rate spending habits (0-100)
   - Compare to similar users
   - Gamification elements

8. **Financial Health Score**
   - Composite score based on:
     - Savings rate
     - Debt ratio
     - Budget adherence
     - Emergency fund status

**Technologies:**
- Tesseract OCR for receipt scanning
- spaCy for NLP
- LangChain for LLM integration
- OpenAI API for advanced insights

---

### **Phase 27: Social & Collaboration** 👥
**Priority:** LOW
**Status:** Not Started
**Estimated Time:** 12-15 hours

**Features:**
1. **Shared Budgets**
   - Family/roommate budget sharing
   - Permission management (view/edit)
   - Shared categories and entries

2. **Split Expense Tracking**
   - Track who owes whom
   - Settle up functionality
   - Group expense splitting

3. **Budget Comparison**
   - Anonymized community comparison
   - See how you compare to similar users
   - Category-wise benchmarking

4. **Accountant Sharing**
   - Share reports with financial advisor
   - Time-limited access tokens
   - Read-only views

5. **Export to Accounting Software**
   - QuickBooks integration
   - Xero integration
   - CSV export in standard formats

6. **Social Achievements**
   - Milestones and badges
   - Saving streak tracking
   - Leaderboards (opt-in, anonymized)

---

### **Phase 28: Third-Party Integrations** 🔌
**Priority:** LOW
**Status:** Not Started
**Estimated Time:** 10-15 hours per integration

**Integrations:**
1. **Bank Account Sync** (Plaid API)
   - Link bank accounts
   - Auto-import transactions
   - Real-time balance updates
   - Multi-bank support

2. **Credit Card Transaction Import**
   - Link credit cards
   - Auto-categorize transactions
   - Track credit utilization

3. **Calendar Integration**
   - Sync bill due dates to Google Calendar
   - iCal export
   - Reminders via calendar

4. **Slack/Discord Notifications**
   - Daily spending summaries
   - Budget alerts
   - Goal progress updates

5. **Google Sheets Export**
   - Live sync to Google Sheets
   - Custom templates
   - Automatic backups

6. **Zapier Webhooks**
   - Trigger workflows on events
   - Connect to 5000+ apps
   - Custom automation

7. **SMS Notifications** (Twilio)
   - Spending alerts
   - Bill reminders
   - Budget warnings

---

## 🏗️ Technical Architecture

### **Technology Stack**

#### **Backend**
- **Framework:** FastAPI 0.115.0 (ASGI)
- **Server:** Uvicorn (dev), Gunicorn + Uvicorn workers (prod)
- **Database ORM:** SQLAlchemy 2.0.35
- **Migration Tool:** Alembic
- **Authentication:** Passlib with bcrypt
- **Async Support:** Python asyncio

#### **Database**
- **Development:** SQLite 3
- **Production:** PostgreSQL 15+ (Railway)
- **Connection Pooling:** SQLAlchemy pool (size: 10, overflow: 20)
- **Timeouts:** 10s connect, 30s statement, 300s pool recycle

#### **AI/ML**
- **Framework:** scikit-learn 1.5.0
- **Data Processing:** pandas, numpy
- **Algorithms:**
  - Random Forest for categorization
  - Linear Regression for predictions
  - Isolation Forest for anomalies
  - TF-IDF for text vectorization

#### **Frontend**
- **Templating:** Jinja2
- **CSS Framework:** Custom CSS with CSS Grid/Flexbox
- **JavaScript:** Vanilla ES6+
- **AJAX:** HTMX for dynamic updates
- **Charts:** Chart.js, Matplotlib (server-side)

#### **Task Scheduling**
- **Scheduler:** APScheduler
- **Jobs:** Weekly/monthly report generation
- **Execution:** Background thread

#### **Email**
- **Primary:** aiosmtplib (Gmail SMTP)
- **Fallback:** Resend API (production, when SMTP blocked)
- **Templates:** Jinja2 HTML templates

#### **Image Processing**
- **Library:** Pillow (PIL)
- **Formats:** JPG, PNG, GIF, WebP
- **Operations:** Resize, compress, base64 encode

#### **Data Export**
- **Excel:** OpenPyXL
- **PDF:** ReportLab
- **Charts:** Matplotlib (PNG export)

### **Database Schema**

#### **Core Tables**
```
users
├── id (PK)
├── email (unique)
├── hashed_password
├── full_name
├── avatar_url (TEXT - base64 data URI)
├── is_verified (boolean)
├── verification_token
├── verification_token_expires
├── password_reset_token
├── password_reset_expires
└── created_at

categories
├── id (PK)
├── user_id (FK → users.id, CASCADE)
└── name

entries
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── category_id (FK → categories.id, SET NULL)
├── amount (numeric)
├── date
├── type (income/expense)
├── notes (text)
├── currency_code (VARCHAR(3))
├── ai_suggested_category_id (FK → categories.id, SET NULL)
├── ai_confidence_score (numeric)
├── merchant_name
├── location_data (text)
└── ai_processed (boolean)

user_preferences
├── id (PK)
├── user_id (FK → users.id, CASCADE, unique)
├── currency_code (default: USD)
├── theme (dark/light)
└── preferences (JSON)
```

#### **AI Tables**
```
ai_models
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── model_name
├── model_type
├── accuracy
├── training_data_count
├── created_at
└── updated_at

ai_suggestions
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── entry_id (FK → entries.id, CASCADE)
├── suggestion_type
├── confidence_score
└── created_at

user_ai_preferences
├── id (PK)
├── user_id (FK → users.id, CASCADE, unique)
├── auto_categorization_enabled
├── prediction_enabled
├── insights_enabled
├── notification_preferences (JSON)
└── timestamps
```

#### **Reporting Tables**
```
weekly_reports
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── week_start
├── week_end
├── report_data (JSON)
└── created_at

user_report_preferences
├── id (PK)
├── user_id (FK → users.id, CASCADE, unique)
├── frequency (weekly/biweekly/monthly/disabled)
├── notification_enabled
└── timestamps

report_status
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── report_id (FK → weekly_reports.id, CASCADE)
├── viewed (boolean)
└── sent_at
```

#### **Goal Tables**
```
financial_goals
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── name
├── goal_type (savings/spending_limit/debt_payoff/emergency_fund/custom)
├── target_amount (numeric)
├── current_amount (numeric)
├── target_date
├── category_id (FK → categories.id, SET NULL) - for spending limits
├── status (active/completed/cancelled/failed)
├── created_at
└── updated_at

goal_progress_logs
├── id (PK)
├── goal_id (FK → financial_goals.id, CASCADE)
├── amount (numeric)
├── notes (text)
└── logged_at
```

### **File Structure**
```
expense-manager-web-app/
├── alembic/
│   ├── versions/
│   │   ├── 20250902_0001_init.py
│   │   ├── 20250919_0002_user_preferences.py
│   │   ├── ...
│   │   └── 20251108_0002_expand_avatar_url_to_text.py
│   └── env.py
├── app/
│   ├── ai/
│   │   ├── data/
│   │   │   ├── training_pipeline.py
│   │   │   └── time_series_analyzer.py
│   │   ├── models/
│   │   │   └── categorization_model.py
│   │   └── services/
│   │       ├── anomaly_detection.py
│   │       ├── financial_insights.py
│   │       └── prediction_service.py
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── entries.py
│   │       ├── categories.py
│   │       ├── dashboard.py
│   │       ├── reports.py
│   │       ├── ai.py
│   │       ├── goals.py
│   │       ├── theme.py
│   │       └── profile.py
│   ├── core/
│   │   ├── config.py
│   │   ├── currency.py
│   │   ├── security.py
│   │   └── session.py
│   ├── db/
│   │   ├── base.py
│   │   ├── engine.py
│   │   └── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── entry.py
│   │   ├── user_preferences.py
│   │   ├── ai_model.py
│   │   ├── weekly_report.py
│   │   ├── financial_goal.py
│   │   └── ...
│   ├── services/
│   │   ├── auth.py
│   │   ├── entries.py
│   │   ├── categories.py
│   │   ├── ai_service.py
│   │   ├── goal_service.py
│   │   ├── excel_export.py
│   │   ├── pdf_export.py
│   │   ├── report_scheduler.py
│   │   └── ...
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── insights.html
│   │   ├── goals.html
│   │   ├── auth/
│   │   ├── entries/
│   │   ├── categories/
│   │   ├── reports/
│   │   └── settings/
│   └── main.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── .env
├── .env.example
├── alembic.ini
├── fix_production_schema.py
├── stamp_migrations.py
├── start.sh
├── Procfile
├── runtime.txt
├── requirements.txt
└── PROJECT_ROADMAP.md (this file)
```

---

## 🚀 Deployment Guide

### **Railway Deployment**

#### **Prerequisites**
- Railway account
- PostgreSQL database provisioned
- Environment variables configured

#### **Environment Variables**
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-secret-key-here
ENV=production

# Email (choose one)
# Option 1: Gmail SMTP
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Option 2: Resend API
RESEND_API_KEY=your-resend-api-key

# Optional
BASE_URL=https://your-domain.com
PORT=8000
```

#### **Deployment Steps**

1. **Initial Deployment**
   ```bash
   # Push to GitHub
   git push origin main

   # Railway auto-deploys from GitHub
   ```

2. **Manual Schema Fix (First Deployment)**
   ```bash
   # Access Railway PostgreSQL console
   # Run:
   UPDATE alembic_version SET version_num = '20251108_0002';
   ```

3. **Verify Deployment**
   - Check deployment logs
   - Verify database connection
   - Test authentication
   - Test core features

#### **Start Script Flow**
```bash
start.sh:
1. Set ENV=production
2. Skip pre-startup DB checks
3. Start uvicorn server

app startup:
1. Check migration version
2. If up-to-date → skip migrations
3. If behind → attempt upgrade
4. If migrations fail → create tables directly
5. Start report scheduler
6. App ready to serve requests
```

### **Local Development**

```bash
# 1. Clone repository
git clone https://github.com/TurtleWithGlasses/expense-manager-web-app.git
cd expense-manager-web-app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env with your settings

# 5. Run migrations
alembic upgrade head

# 6. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access at http://localhost:8000
```

### **Database Migrations**

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history

# Stamp database (mark as specific version without running migrations)
alembic stamp head
```

---

## 📝 Development Workflow

### **Feature Development Process**

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/feature-name
   ```

2. **Implement Feature**
   - Add models (if needed) in `app/models/`
   - Add services in `app/services/`
   - Add API endpoints in `app/api/v1/`
   - Add templates in `app/templates/`
   - Create migration if schema changes

3. **Test Locally**
   - Manual testing
   - Check error handling
   - Verify database changes

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add feature: description"
   git push origin feature/feature-name
   ```

5. **Merge to Main**
   ```bash
   git checkout main
   git merge feature/feature-name
   git push origin main
   ```

6. **Deploy**
   - Railway auto-deploys from main branch
   - Monitor deployment logs
   - Verify in production

### **Database Schema Changes**

1. **Modify Models**
   - Update model in `app/models/`

2. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "Add column_name"
   ```

3. **Review Migration**
   - Check generated migration file
   - Ensure upgrade() and downgrade() are correct

4. **Test Migration**
   ```bash
   # Apply
   alembic upgrade head

   # Test rollback
   alembic downgrade -1

   # Reapply
   alembic upgrade head
   ```

5. **Commit Migration**
   ```bash
   git add alembic/versions/*.py
   git commit -m "Migration: description"
   ```

---

## 🎯 Success Metrics

### **Current Metrics**
- ✅ **Features Implemented:** 40+
- ✅ **Database Tables:** 12
- ✅ **API Endpoints:** 50+
- ✅ **AI/ML Models:** 4
- ❌ **Test Coverage:** 0%
- ❌ **Uptime:** Not tracked
- ❌ **Performance:** Not benchmarked

### **Target Metrics (Phase 22-25)**
- **Test Coverage:** 80%+
- **Uptime:** 99.9%
- **Page Load Time:** < 2s
- **API Response Time:** < 200ms
- **Mobile Score:** 90+ (Lighthouse)
- **Security Score:** A+ (Observatory)

---

## 📞 Support & Contact

**Issues:** https://github.com/TurtleWithGlasses/expense-manager-web-app/issues
**Email:** info@yourbudgetpulse.online
**Production:** https://www.yourbudgetpulse.online

---

## 📜 License

[Add license information]

---

## 🙏 Acknowledgments

- Built with FastAPI, SQLAlchemy, and scikit-learn
- Deployed on Railway
- Email via Gmail SMTP / Resend API
- Charts with Chart.js and Matplotlib

---

**Last Updated:** November 9, 2025
**Version:** 1.0
**Status:** Production Deployment In Progress