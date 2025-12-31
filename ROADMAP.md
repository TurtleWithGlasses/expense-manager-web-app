# 🗺️ BudgetPulse Development Roadmap
## Advanced Analytics & Gamification Implementation Plan

**Version:** 3.3
**Last Updated:** 2025-12-31
**Timeline:** 16 weeks (4 months)
**Status:** Phase 1 & 2 Complete ✅ | Phase 4 & 5 Complete ✅ | Phase 3 Partial ~50%

---

## 🎉 Recent Completion Status

### ✅ Completed Phases

**Phase 1: Foundation & Infrastructure** - **100% Complete** (December 31, 2025)
- ✅ Achievement System Persistence
  - AchievementService with comprehensive unlock logic
  - Support for 7 criteria types (entry_count, daily_streak, no_spend_days, savings_rate, goal_completion, budget_discipline, category_usage)
  - 17 default achievements with XP rewards and icons
  - Achievement progress tracking and "NEW" badge system
- ✅ Financial Health Score Algorithm
  - FinancialHealthScore model with 6 component scores (0-100 each)
  - Database migration for financial_health_scores table
  - Health score API endpoints (current, history, recommendations, comparison)
  - 0-100 scoring system with historical tracking
- ✅ Chart.js Integration
  - Interactive category pie chart (doughnut chart)
  - Daily trend line chart with time-based x-axis
  - Category bar chart for comparisons
  - Responsive design with tooltips and legends
- **Commits:** 9119e2a, 3be9203

**Phase 2.1: Advanced Custom Reports** - **100% Complete** (December 31, 2025)
- ✅ Saveable report templates with category filtering
  - Full CRUD operations for templates
  - Category-specific report filtering
  - Favorite/starred templates
  - Usage tracking and statistics
  - Template management UI with dark theme support
- ✅ Report scheduling for automatic generation
  - Weekly reports (Every Monday at 9 AM)
  - Monthly reports (1st day of month at 9 AM)
  - Custom schedule support (user-defined day/hour)
  - Email delivery via professional HTML templates
  - APScheduler background job integration
  - Duplicate prevention and error handling
- **Commits:** [various report commits]

**Phase 4: Advanced ML & Predictions** - **100% Complete** (December 2025)
- ✅ Prophet forecasting with seasonal patterns
- ✅ What-If scenario planning and analysis
- ✅ Recurring bills integration in forecasts
- ✅ Multi-horizon projections (90, 180, 365 days)
- **Commits:** f4e111a, 42c8d51, 2500889

**Phase 5: Polish & Testing** - **100% Complete** (December 2025)
- ✅ Database optimization (7 composite indexes, 6-8x faster queries)
- ✅ Redis caching system (35,000x faster forecast retrieval)
- ✅ Three-tier caching strategy (Redis → DB → Fresh)
- ✅ Comprehensive test suite (55 tests: unit, integration, performance, load)
- ✅ Performance documentation and benchmarks
- **Commits:** 3211cb0, c34b673, 0b2409c

**Performance Achievements:**
- Cache GET: 0.098ms avg (20x better than target)
- Cache SET: 0.114ms avg (44x better than target)
- Forecast retrieval: 3500ms → 0.1ms (35,000x faster with Redis)
- Database queries: 800ms → 120ms (6.7x faster with indexes)

**Financial Goals System** - **100% Complete** (December 2025)
- ✅ Complete CRUD operations for financial goals
- ✅ Progress tracking with history logs
- ✅ Multiple goal types (savings, spending limits, debt payoff, emergency fund)
- ✅ Automatic overdue goal handling
- ✅ Goal reactivation with new deadlines
- ✅ Completed goals summary with total savings
- ✅ XP rewards for goal creation and completion
- **Commits:** 0cf2f14, 7c076e7, 6a5f9ef, 9096874, 87075fc

**Auto-Add to Expenses for Recurring Bills** - **Complete** (December 31, 2025)
- ✅ Auto-add checkbox in Bills & Subscriptions UI
- ✅ Scheduled job (daily at 1 AM) to process due payments
- ✅ Automatic expense entry creation on due dates
- ✅ Smart duplicate prevention
- ✅ Support for all recurrence frequencies (weekly, biweekly, monthly, quarterly, annually)
- ✅ Manual test endpoint for verification
- ✅ Comprehensive testing documentation
- ✅ AUTO-ADD visibility column in Bills & Subscriptions table
  - Green checkmark icon for enabled subscriptions
  - Clear visual indicator for auto-add status
  - Integrated with edit modal for easy status updates
- **Commits:** 8c8d919, a85876a, 17d3495

### 📅 Deferred for Future Implementation

**Phase 3.2: Savings Challenges** - **Deferred**
- Weekly/monthly challenges (No-Spend Weekend, $5 Daily Challenge)
- Community challenges with leaderboards
- Progress tracking and rewards
- Challenge templates (models exist at `app/models/challenge.py`)

---

## 📊 Executive Summary

This roadmap outlines the implementation plan for two major feature sets:

1. **Advanced Analytics** - Custom reports, interactive visualizations, ML-driven predictions
2. **Gamification** - Achievements, badges, savings challenges, financial health scoring

**Current State:** 90% complete - Phase 1, 2, 4 & 5 fully complete, Phase 3 (Gamification) 50% complete
**Target State:** Production-ready analytics platform with engagement features

---

## 🎯 Strategic Goals

### Advanced Analytics Goals
- Enable users to create custom reports with flexible metrics and date ranges
- Provide interactive, drill-down capable visualizations
- Deliver accurate ML-based spending forecasts with seasonal patterns
- Export reports in multiple formats (PDF, Excel, CSV)

### Gamification Goals
- Increase user engagement through achievements and badges
- Motivate better financial behavior via challenges and scoring
- Build community features around savings competitions
- Provide clear financial health metrics (0-100 score)

---

## 📋 Implementation Phases Overview

| Phase | Status | Priority | Duration | Completion |
|-------|--------|----------|----------|------------|
| **Phase 1: Foundation & Infrastructure** | ✅ Complete | 🔴 Critical | 3 weeks | **100%** ✅ |
| **Phase 2: Advanced Analytics** | ✅ Complete | 🟠 High | 4 weeks | **100%** ✅ |
| **Phase 3: Gamification System** | 🟡 Partial | 🟡 Medium | 3 weeks | ~50% |
| **Phase 4: Advanced ML & Predictions** | ✅ Complete | 🟡 Medium-Low | 4 weeks | **100%** ✅ |
| **Phase 5: Polish & Testing** | ✅ Complete | 🟠 High | 2 weeks | **100%** ✅ |
| **Financial Goals** | ✅ Complete | 🟢 Medium | 2 weeks | **100%** ✅ |

**Overall Progress: ~90% Complete**

---

### **Phase 1: Foundation & Infrastructure** (Weeks 1-3)
**Priority:** 🔴 **CRITICAL** - Required for all other features
**Effort:** 3 weeks | **Team Size:** 2 developers

#### 1.1 Achievement System Persistence (Week 1)

**Problem:** Achievements are currently recalculated on every report generation instead of being persisted.

**Database Schema:**
```sql
-- New Models

CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,           -- e.g., 'no_spend_days_bronze'
    name VARCHAR(200) NOT NULL,                  -- 'No-Spend Champion'
    description TEXT,
    category VARCHAR(50),                        -- 'saving', 'spending', 'tracking'
    tier VARCHAR(20),                            -- 'bronze', 'silver', 'gold', 'platinum'
    icon_name VARCHAR(100),                      -- Icon identifier
    points INTEGER DEFAULT 0,
    unlock_criteria JSONB NOT NULL,              -- {'type': 'no_spend_days', 'threshold': 2}
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INTEGER REFERENCES achievements(id),
    earned_at TIMESTAMP DEFAULT NOW(),
    progress_data JSONB,                         -- Current progress towards next tier
    is_new BOOLEAN DEFAULT TRUE,                 -- Show "NEW" badge
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_earned ON user_achievements(earned_at DESC);
```

**Python Models:**
```python
# app/models/achievement.py

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # saving, spending, tracking, goal
    tier = Column(String(20))       # bronze, silver, gold, platinum
    icon_name = Column(String(100))
    points = Column(Integer, default=0)
    unlock_criteria = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    earned_at = Column(DateTime, default=datetime.utcnow)
    progress_data = Column(JSONB)  # {'current': 5, 'target': 10, 'percentage': 50}
    is_new = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id'),
    )
```

**Service Layer:**
```python
# app/services/achievement_service.py

class AchievementService:
    """Manages achievement unlocking and tracking"""

    @staticmethod
    async def check_and_unlock_achievements(user_id: int, db: Session) -> List[UserAchievement]:
        """Check all achievement criteria and unlock new ones"""
        # Get all achievements
        # Check unlock criteria against user data
        # Award new achievements
        # Return list of newly unlocked achievements
        pass

    @staticmethod
    async def get_user_achievements(user_id: int, db: Session) -> Dict:
        """Get all achievements for a user with progress"""
        pass

    @staticmethod
    async def get_achievement_progress(user_id: int, achievement_code: str, db: Session) -> Dict:
        """Get progress towards a specific achievement"""
        pass

    @staticmethod
    async def seed_default_achievements(db: Session):
        """Create default achievement definitions"""
        # 20+ achievements covering:
        # - Tracking consistency (7, 14, 30 day streaks)
        # - No-spend days (1, 3, 7, 14 days per month)
        # - Savings milestones (10%, 20%, 30% rate)
        # - Goal completion (1, 3, 5, 10 goals)
        # - Budget discipline (under budget 7, 14, 30 days)
        # - Category balance (5+, 10+ categories used)
        pass
```

**API Endpoints:**
```python
# app/api/v1/achievements.py

@router.get("/achievements")
async def get_user_achievements(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Get all user achievements with progress"""

@router.get("/achievements/{achievement_id}/progress")
async def get_achievement_progress(achievement_id: int, user: User = Depends(current_user)):
    """Get detailed progress for specific achievement"""

@router.post("/achievements/{achievement_id}/mark-seen")
async def mark_achievement_seen(achievement_id: int, user: User = Depends(current_user)):
    """Mark new achievement as seen"""
```

**Migration:**
```bash
alembic revision -m "Add achievement system"
# Create migration with above schema
alembic upgrade head
```

**Testing Checklist:**
- [ ] Achievement models save and retrieve correctly
- [ ] Unlock criteria evaluation works for all types
- [ ] Progress calculation is accurate
- [ ] API endpoints return correct data
- [ ] New achievements trigger notifications

---

#### 1.2 Financial Health Score Algorithm (Week 2)

**Goal:** Implement a 0-100 score that reflects user's financial health

**Database Schema:**
```sql
CREATE TABLE financial_health_scores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    score_date DATE NOT NULL,

    -- Component scores (0-100 each)
    savings_rate_score INTEGER,
    expense_consistency_score INTEGER,
    budget_adherence_score INTEGER,
    debt_management_score INTEGER,
    goal_progress_score INTEGER,
    emergency_fund_score INTEGER,

    -- Supporting data
    calculation_data JSONB,
    recommendations JSONB,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, score_date)
);

CREATE INDEX idx_health_scores_user_date ON financial_health_scores(user_id, score_date DESC);
```

**Algorithm Design:**
```python
# app/ai/services/financial_health_service.py

class FinancialHealthScoreCalculator:
    """
    Calculates comprehensive financial health score (0-100)

    Components (weighted):
    1. Savings Rate (25%):
       - 0%: 0 points
       - 10%: 40 points
       - 20%: 70 points
       - 30%+: 100 points

    2. Expense Consistency (20%):
       - High variance: 0-40 points
       - Medium variance: 41-70 points
       - Low variance: 71-100 points
       (Measured by coefficient of variation)

    3. Budget Adherence (20%):
       - Over budget 20%+: 0 points
       - Over budget 10-20%: 30 points
       - On budget ±10%: 70 points
       - Under budget 10%+: 100 points

    4. Debt Management (15%):
       - Debt/income ratio > 50%: 0 points
       - 30-50%: 40 points
       - 10-30%: 70 points
       - < 10%: 100 points

    5. Goal Progress (10%):
       - 0 goals: 0 points
       - Active goals with < 25% progress: 30 points
       - Active goals with 25-75% progress: 70 points
       - Completed goals: 100 points

    6. Emergency Fund (10%):
       - No emergency fund: 0 points
       - < 1 month expenses: 30 points
       - 1-3 months: 70 points
       - 3+ months: 100 points
    """

    WEIGHTS = {
        'savings_rate': 0.25,
        'expense_consistency': 0.20,
        'budget_adherence': 0.20,
        'debt_management': 0.15,
        'goal_progress': 0.10,
        'emergency_fund': 0.10
    }

    @staticmethod
    async def calculate_score(user_id: int, db: Session, date: date = None) -> Dict:
        """
        Calculate comprehensive financial health score

        Returns:
        {
            'overall_score': 75,
            'component_scores': {
                'savings_rate': 80,
                'expense_consistency': 65,
                ...
            },
            'grade': 'Good',  # Excellent (90-100), Good (70-89), Fair (50-69), Poor (0-49)
            'recommendations': [
                'Increase savings rate by 5% to reach Excellent grade',
                'Reduce spending variance in Transportation category'
            ],
            'historical_trend': 'improving',  # improving, stable, declining
            'percentile': 68  # Compared to other users (privacy-respecting)
        }
        """
        pass

    @staticmethod
    def _calculate_savings_rate_score(savings_rate: float) -> int:
        """Calculate savings rate component score"""
        if savings_rate >= 0.30:
            return 100
        elif savings_rate >= 0.20:
            return 70 + int((savings_rate - 0.20) * 300)
        elif savings_rate >= 0.10:
            return 40 + int((savings_rate - 0.10) * 300)
        elif savings_rate >= 0:
            return int(savings_rate * 400)
        else:  # Negative savings
            return 0

    @staticmethod
    def _calculate_expense_consistency_score(entries: List[Entry]) -> int:
        """Calculate expense consistency using coefficient of variation"""
        # Lower variance = higher score
        pass

    @staticmethod
    def _calculate_budget_adherence_score(actual: float, budget: float) -> int:
        """Calculate budget adherence score"""
        pass

    # ... more component calculators
```

**API Endpoints:**
```python
# app/api/v1/health_score.py

@router.get("/health-score")
async def get_financial_health_score(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Get current financial health score with breakdown"""

@router.get("/health-score/history")
async def get_health_score_history(
    days: int = 90,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get historical health scores for trend analysis"""

@router.get("/health-score/recommendations")
async def get_health_recommendations(user: User = Depends(current_user)):
    """Get personalized recommendations to improve score"""
```

**Scheduled Job:**
```python
# Calculate daily health score for active users
# Run at 00:00 UTC daily
scheduler.add_job(
    func=calculate_daily_health_scores,
    trigger='cron',
    hour=0,
    minute=0
)
```

---

#### 1.3 Chart.js Integration (Week 3)

**Goal:** Replace basic HTML charts with interactive Chart.js visualizations

**Dependencies:**
```json
// package.json (if using npm) or CDN
{
  "dependencies": {
    "chart.js": "^4.4.0",
    "chartjs-adapter-date-fns": "^3.0.0"
  }
}
```

**Base Template:**
```html
<!-- app/templates/components/_chart_base.html -->
{% block head_extra %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
{% endblock %}

<canvas id="{{ chart_id }}" width="400" height="200"></canvas>

<script>
const ctx = document.getElementById('{{ chart_id }}').getContext('2d');
const chart = new Chart(ctx, {
    type: '{{ chart_type }}',
    data: {{ chart_data | tojson }},
    options: {{ chart_options | tojson }}
});
</script>
```

**Chart Components to Create:**

1. **Category Pie Chart** (Replace `_chart_pie.html`)
```javascript
// static/js/charts/category-pie-chart.js
function createCategoryPieChart(containerId, data) {
    return new Chart(document.getElementById(containerId), {
        type: 'doughnut',
        data: {
            labels: data.categories,
            datasets: [{
                data: data.amounts,
                backgroundColor: data.colors,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: $${context.parsed.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    // Drill down to category details
                    const categoryIndex = elements[0].index;
                    window.location.href = `/categories/${categoryIndex}/details`;
                }
            }
        }
    });
}
```

2. **Daily Spending Trend** (Replace `_chart_daily.html`)
```javascript
// static/js/charts/daily-trend-chart.js
function createDailyTrendChart(containerId, data) {
    return new Chart(document.getElementById(containerId), {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Expenses',
                    data: data.expenses,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Income',
                    data: data.income,
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'day' }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '$' + value.toFixed(2)
                    }
                }
            },
            plugins: {
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x'
                    },
                    pan: {
                        enabled: true,
                        mode: 'x'
                    }
                }
            }
        }
    });
}
```

3. **Category Bar Chart** (New)
```javascript
// static/js/charts/category-bar-chart.js
function createCategoryBarChart(containerId, data) {
    return new Chart(document.getElementById(containerId), {
        type: 'bar',
        data: {
            labels: data.categories,
            datasets: [{
                label: 'Spending',
                data: data.amounts,
                backgroundColor: 'rgba(59, 130, 246, 0.8)'
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',  // Horizontal bars
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '$' + value
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx => `$${ctx.parsed.x.toFixed(2)}`
                    }
                }
            }
        }
    });
}
```

**Chart Configuration Service:**
```python
# app/services/chart_config_service.py

class ChartConfigService:
    """Generate Chart.js compatible data structures"""

    @staticmethod
    def category_pie_data(entries: List[Entry], user: User) -> Dict:
        """Generate pie chart data from entries"""
        # Group by category
        # Calculate totals
        # Format for Chart.js
        return {
            'categories': ['Food', 'Transport', 'Entertainment'],
            'amounts': [450.50, 230.00, 120.75],
            'colors': ['#ef4444', '#3b82f6', '#10b981']
        }

    @staticmethod
    def daily_trend_data(entries: List[Entry], start_date: date, end_date: date) -> Dict:
        """Generate line chart data for daily trends"""
        pass

    @staticmethod
    def category_comparison_data(entries: List[Entry], previous_entries: List[Entry]) -> Dict:
        """Generate comparison bar chart data"""
        pass
```

**Updated API Endpoints:**
```python
# app/api/v1/charts.py (new file)

@router.get("/charts/category-pie")
async def get_category_pie_chart(
    start_date: date = None,
    end_date: date = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get category pie chart data"""
    entries = # fetch entries
    return ChartConfigService.category_pie_data(entries, user)

@router.get("/charts/daily-trend")
async def get_daily_trend_chart(...):
    """Get daily trend chart data"""

@router.get("/charts/category-bar")
async def get_category_bar_chart(...):
    """Get category bar chart data"""
```

---

### **Phase 2: Advanced Analytics** (Weeks 4-7)
**Priority:** 🟠 **HIGH** - Core user-facing features
**Effort:** 4 weeks | **Team Size:** 2-3 developers

#### 2.1 Custom Reports Builder (Weeks 4-5)

**Goal:** Enable users to create, save, and run custom reports with flexible metrics

**Database Schema:**
```sql
CREATE TABLE custom_report_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Report configuration
    metrics JSONB NOT NULL,              -- ['total_income', 'total_expenses', 'avg_daily']
    date_range_type VARCHAR(50),         -- 'custom', 'last_7_days', 'this_month'
    custom_start_date DATE,
    custom_end_date DATE,

    -- Filters
    category_ids INTEGER[],
    entry_types VARCHAR(20)[],           -- ['expense', 'income']
    min_amount NUMERIC(12, 2),
    max_amount NUMERIC(12, 2),

    -- Grouping & visualization
    group_by VARCHAR(50)[],              -- ['category', 'date', 'type']
    chart_types JSONB,                   -- {'primary': 'pie', 'secondary': 'line'}

    -- Scheduling
    is_scheduled BOOLEAN DEFAULT FALSE,
    schedule_frequency VARCHAR(20),      -- 'daily', 'weekly', 'monthly'
    next_run_date TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE custom_report_runs (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES custom_report_templates(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    report_data JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    date_range_start DATE,
    date_range_end DATE,
    total_entries INTEGER,
    execution_time_ms INTEGER
);

CREATE INDEX idx_custom_templates_user ON custom_report_templates(user_id);
CREATE INDEX idx_custom_runs_template ON custom_report_runs(template_id, generated_at DESC);
```

**Available Metrics:**
```python
# app/services/custom_reports/metrics.py

class ReportMetrics:
    """All available metrics for custom reports"""

    METRICS_CATALOG = {
        'total_income': {
            'name': 'Total Income',
            'description': 'Sum of all income entries',
            'calculation': lambda entries: sum(e.amount for e in entries if e.type == 'income'),
            'format': 'currency'
        },
        'total_expenses': {
            'name': 'Total Expenses',
            'description': 'Sum of all expense entries',
            'calculation': lambda entries: sum(e.amount for e in entries if e.type == 'expense'),
            'format': 'currency'
        },
        'net_savings': {
            'name': 'Net Savings',
            'description': 'Income minus Expenses',
            'calculation': lambda entries: # calculate,
            'format': 'currency'
        },
        'avg_daily_expense': {
            'name': 'Average Daily Expense',
            'calculation': lambda entries, days: # calculate,
            'format': 'currency'
        },
        'transaction_count': {
            'name': 'Transaction Count',
            'calculation': lambda entries: len(entries),
            'format': 'number'
        },
        'unique_categories': {
            'name': 'Unique Categories',
            'calculation': lambda entries: len(set(e.category_id for e in entries)),
            'format': 'number'
        },
        'savings_rate': {
            'name': 'Savings Rate',
            'calculation': lambda income, expenses: (income - expenses) / income * 100 if income > 0 else 0,
            'format': 'percentage'
        },
        'largest_expense': {
            'name': 'Largest Single Expense',
            'calculation': lambda entries: max((e.amount for e in entries if e.type == 'expense'), default=0),
            'format': 'currency'
        },
        'category_diversity': {
            'name': 'Category Diversity Score',
            'description': 'How evenly spending is distributed (0-100)',
            'calculation': lambda entries: # calculate Shannon entropy,
            'format': 'score'
        }
        # ... 20+ more metrics
    }
```

**Report Builder Service:**
```python
# app/services/custom_reports/report_builder.py

class CustomReportBuilder:
    """Generates custom reports based on templates"""

    @staticmethod
    async def generate_report(template: CustomReportTemplate, db: Session) -> Dict:
        """
        Generate a report from a template

        Steps:
        1. Fetch entries based on filters
        2. Calculate all requested metrics
        3. Group data as specified
        4. Generate chart configurations
        5. Create summary and insights
        """
        # Fetch entries
        entries = await CustomReportBuilder._fetch_entries(template, db)

        # Calculate metrics
        metrics_results = {}
        for metric_code in template.metrics:
            metric_def = ReportMetrics.METRICS_CATALOG[metric_code]
            metrics_results[metric_code] = metric_def['calculation'](entries)

        # Group data
        grouped_data = await CustomReportBuilder._group_data(entries, template.group_by)

        # Generate charts
        charts = await CustomReportBuilder._generate_charts(grouped_data, template.chart_types)

        return {
            'template_id': template.id,
            'template_name': template.name,
            'date_range': {
                'start': template.custom_start_date,
                'end': template.custom_end_date
            },
            'metrics': metrics_results,
            'grouped_data': grouped_data,
            'charts': charts,
            'summary': await CustomReportBuilder._generate_summary(metrics_results),
            'insights': await CustomReportBuilder._generate_insights(entries, metrics_results)
        }

    @staticmethod
    async def _fetch_entries(template: CustomReportTemplate, db: Session) -> List[Entry]:
        """Fetch entries based on template filters"""
        query = db.query(Entry).filter(Entry.user_id == template.user_id)

        # Date range filter
        if template.date_range_type == 'custom':
            query = query.filter(Entry.date >= template.custom_start_date)
            query = query.filter(Entry.date <= template.custom_end_date)
        elif template.date_range_type == 'last_7_days':
            query = query.filter(Entry.date >= date.today() - timedelta(days=7))
        # ... more date range types

        # Category filter
        if template.category_ids:
            query = query.filter(Entry.category_id.in_(template.category_ids))

        # Amount range filter
        if template.min_amount:
            query = query.filter(Entry.amount >= template.min_amount)
        if template.max_amount:
            query = query.filter(Entry.amount <= template.max_amount)

        return query.all()
```

**Frontend UI:**
```html
<!-- app/templates/reports/custom_builder.html -->
<div class="custom-report-builder">
    <h2>Create Custom Report</h2>

    <form id="report-builder-form">
        <!-- Step 1: Basic Info -->
        <div class="form-section">
            <h3>1. Report Details</h3>
            <input type="text" name="name" placeholder="Report Name" required>
            <textarea name="description" placeholder="Description"></textarea>
        </div>

        <!-- Step 2: Date Range -->
        <div class="form-section">
            <h3>2. Date Range</h3>
            <select name="date_range_type">
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="last_7_days">Last 7 Days</option>
                <option value="last_30_days">Last 30 Days</option>
                <option value="this_month">This Month</option>
                <option value="last_month">Last Month</option>
                <option value="this_year">This Year</option>
                <option value="custom">Custom Range</option>
            </select>

            <div id="custom-date-range" style="display: none;">
                <input type="date" name="start_date">
                <input type="date" name="end_date">
            </div>
        </div>

        <!-- Step 3: Metrics Selection -->
        <div class="form-section">
            <h3>3. Metrics to Include</h3>
            <div class="metrics-grid">
                {% for metric_code, metric_info in available_metrics.items() %}
                <label class="metric-option">
                    <input type="checkbox" name="metrics" value="{{ metric_code }}">
                    <div class="metric-card">
                        <h4>{{ metric_info.name }}</h4>
                        <p>{{ metric_info.description }}</p>
                    </div>
                </label>
                {% endfor %}
            </div>
        </div>

        <!-- Step 4: Filters -->
        <div class="form-section">
            <h3>4. Filters</h3>
            <select name="categories" multiple>
                {% for category in categories %}
                <option value="{{ category.id }}">{{ category.name }}</option>
                {% endfor %}
            </select>

            <div class="amount-range">
                <input type="number" name="min_amount" placeholder="Min Amount" step="0.01">
                <input type="number" name="max_amount" placeholder="Max Amount" step="0.01">
            </div>
        </div>

        <!-- Step 5: Visualization -->
        <div class="form-section">
            <h3>5. Charts & Visualizations</h3>
            <select name="primary_chart">
                <option value="pie">Pie Chart</option>
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="area">Area Chart</option>
            </select>

            <select name="group_by" multiple>
                <option value="category">By Category</option>
                <option value="date">By Date</option>
                <option value="type">By Type (Income/Expense)</option>
                <option value="week">By Week</option>
                <option value="month">By Month</option>
            </select>
        </div>

        <!-- Step 6: Scheduling (Optional) -->
        <div class="form-section">
            <h3>6. Schedule (Optional)</h3>
            <label>
                <input type="checkbox" name="is_scheduled">
                Run this report automatically
            </label>

            <select name="schedule_frequency">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
            </select>
        </div>

        <div class="form-actions">
            <button type="button" onclick="previewReport()">Preview Report</button>
            <button type="submit">Save Template</button>
            <button type="button" onclick="generateReport()">Generate Now</button>
        </div>
    </form>
</div>

<div id="report-preview" style="display: none;">
    <!-- Live preview of report as user configures -->
</div>
```

**API Endpoints:**
```python
# app/api/v1/custom_reports.py

@router.post("/custom-reports/templates")
async def create_report_template(template_data: CustomReportTemplateCreate, user: User = Depends(current_user)):
    """Create a new custom report template"""

@router.get("/custom-reports/templates")
async def get_user_templates(user: User = Depends(current_user)):
    """Get all report templates for user"""

@router.get("/custom-reports/templates/{template_id}")
async def get_template(template_id: int, user: User = Depends(current_user)):
    """Get specific template"""

@router.put("/custom-reports/templates/{template_id}")
async def update_template(template_id: int, updates: Dict, user: User = Depends(current_user)):
    """Update template"""

@router.delete("/custom-reports/templates/{template_id}")
async def delete_template(template_id: int, user: User = Depends(current_user)):
    """Delete template"""

@router.post("/custom-reports/templates/{template_id}/generate")
async def generate_custom_report(template_id: int, user: User = Depends(current_user)):
    """Generate report from template"""

@router.get("/custom-reports/runs/{run_id}")
async def get_report_run(run_id: int, user: User = Depends(current_user)):
    """Get previously generated report"""

@router.get("/custom-reports/metrics")
async def get_available_metrics():
    """Get catalog of all available metrics"""
```

---

#### 2.2 Advanced Dashboard (Week 6)

**Goal:** Create a comprehensive, interactive dashboard with 8-10 key visualizations

**Dashboard Layout:**
```html
<!-- app/templates/dashboard/advanced_dashboard.html -->
<div class="advanced-dashboard">
    <!-- Top KPI Row -->
    <div class="kpi-row">
        <div class="kpi-card">
            <h3>Financial Health Score</h3>
            <div class="score-display">
                <canvas id="health-score-gauge"></canvas>
                <span class="score-value">{{ health_score }}</span>
            </div>
        </div>

        <div class="kpi-card">
            <h3>This Month</h3>
            <div class="kpi-values">
                <div class="kpi-income">+$2,450</div>
                <div class="kpi-expenses">-$1,820</div>
                <div class="kpi-net positive">+$630</div>
            </div>
        </div>

        <div class="kpi-card">
            <h3>Savings Rate</h3>
            <div class="savings-rate">25.7%</div>
            <div class="trend positive">+3.2% from last month</div>
        </div>

        <div class="kpi-card">
            <h3>Active Goals</h3>
            <div class="goal-summary">
                <span>3 of 5 on track</span>
                <div class="mini-progress-bars"></div>
            </div>
        </div>
    </div>

    <!-- Main Charts Grid -->
    <div class="charts-grid">
        <!-- 1. Cash Flow Trend (6-month) -->
        <div class="chart-card span-2">
            <h3>Cash Flow Trend</h3>
            <canvas id="cash-flow-chart"></canvas>
        </div>

        <!-- 2. Category Breakdown -->
        <div class="chart-card">
            <h3>Spending by Category</h3>
            <canvas id="category-pie-chart"></canvas>
        </div>

        <!-- 3. Budget Progress Bars -->
        <div class="chart-card">
            <h3>Budget Status</h3>
            <div id="budget-bars"></div>
        </div>

        <!-- 4. Daily Spending Pattern -->
        <div class="chart-card span-2">
            <h3>Daily Spending Pattern</h3>
            <canvas id="daily-pattern-chart"></canvas>
        </div>

        <!-- 5. Top Expenses -->
        <div class="chart-card">
            <h3>Top 10 Expenses</h3>
            <canvas id="top-expenses-bar"></canvas>
        </div>

        <!-- 6. Income vs Expenses Comparison -->
        <div class="chart-card">
            <h3>Income vs Expenses (6-month)</h3>
            <canvas id="comparison-bar-chart"></canvas>
        </div>

        <!-- 7. Recurring Payments Timeline -->
        <div class="chart-card span-2">
            <h3>Upcoming Bills & Subscriptions</h3>
            <div id="payments-timeline"></div>
        </div>

        <!-- 8. Goal Progress -->
        <div class="chart-card">
            <h3>Goal Progress</h3>
            <canvas id="goal-progress-chart"></canvas>
        </div>

        <!-- 9. Anomalies & Alerts -->
        <div class="chart-card">
            <h3>Recent Anomalies</h3>
            <div id="anomalies-list"></div>
        </div>

        <!-- 10. AI Insights -->
        <div class="chart-card span-2">
            <h3>AI Insights & Recommendations</h3>
            <div id="ai-insights"></div>
        </div>
    </div>

    <!-- Filter Controls -->
    <div class="dashboard-filters">
        <select id="date-range-filter">
            <option value="7">Last 7 Days</option>
            <option value="30" selected>Last 30 Days</option>
            <option value="90">Last 90 Days</option>
            <option value="365">Last Year</option>
            <option value="custom">Custom Range</option>
        </select>

        <select id="category-filter" multiple>
            <option value="all" selected>All Categories</option>
            <!-- Dynamic categories -->
        </select>

        <button onclick="refreshDashboard()">Refresh</button>
        <button onclick="exportDashboard()">Export as PDF</button>
    </div>
</div>
```

**Dashboard Controller:**
```javascript
// static/js/dashboard/advanced-dashboard.js

class AdvancedDashboard {
    constructor() {
        this.charts = {};
        this.filters = {
            dateRange: 30,
            categories: 'all'
        };
    }

    async init() {
        await this.loadData();
        this.initializeCharts();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    async loadData() {
        const response = await fetch(`/api/dashboard/advanced?days=${this.filters.dateRange}`);
        this.data = await response.json();
    }

    initializeCharts() {
        // 1. Cash Flow Chart
        this.charts.cashFlow = new Chart(document.getElementById('cash-flow-chart'), {
            type: 'line',
            data: {
                datasets: [
                    { label: 'Income', data: this.data.cash_flow.income, borderColor: 'green' },
                    { label: 'Expenses', data: this.data.cash_flow.expenses, borderColor: 'red' },
                    { label: 'Net', data: this.data.cash_flow.net, borderColor: 'blue' }
                ]
            },
            options: { /* ... */ }
        });

        // 2. Category Pie
        this.charts.categoryPie = createCategoryPieChart('category-pie-chart', this.data.categories);

        // 3. Daily Pattern
        this.charts.dailyPattern = new Chart(document.getElementById('daily-pattern-chart'), {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Average Daily Spending',
                    data: this.data.daily_pattern
                }]
            }
        });

        // ... initialize remaining charts
    }

    setupEventListeners() {
        document.getElementById('date-range-filter').addEventListener('change', (e) => {
            this.filters.dateRange = e.target.value;
            this.refresh();
        });
    }

    async refresh() {
        await this.loadData();
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.initializeCharts();
    }

    startAutoRefresh() {
        // Refresh every 5 minutes
        setInterval(() => this.refresh(), 300000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new AdvancedDashboard();
    dashboard.init();
});
```

---

#### 2.3 Export Functionality (Week 7)

**Goal:** Export reports in PDF, Excel, and CSV formats

**PDF Export (reportlab):**
```python
# app/services/export/pdf_export_service.py

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from io import BytesIO

class PDFExportService:
    """Generate PDF reports with charts and tables"""

    @staticmethod
    async def generate_report_pdf(report_data: Dict, user: User) -> BytesIO:
        """
        Generate a PDF report from report data

        Includes:
        - Header with logo and user info
        - Summary metrics table
        - Charts (converted to images)
        - Detailed transaction tables
        - Footer with generation timestamp
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30
        )

        # Title
        title = Paragraph(f"Financial Report - {report_data['period']}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))

        # Summary Metrics Table
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Income', f"${report_data['total_income']:,.2f}"],
            ['Total Expenses', f"${report_data['total_expenses']:,.2f}"],
            ['Net Savings', f"${report_data['net_savings']:,.2f}"],
            ['Savings Rate', f"{report_data['savings_rate']:.1f}%"],
        ]

        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.5*inch))

        # Charts (convert matplotlib to images)
        if 'charts' in report_data:
            for chart_name, chart_data in report_data['charts'].items():
                # Generate chart as image
                chart_image = PDFExportService._generate_chart_image(chart_data)
                story.append(Image(chart_image, width=5*inch, height=3*inch))
                story.append(Spacer(1, 0.3*inch))

        # Category Breakdown Table
        if 'category_breakdown' in report_data:
            story.append(Paragraph("Category Breakdown", styles['Heading2']))
            category_data = [['Category', 'Amount', 'Percentage']]
            for cat in report_data['category_breakdown']:
                category_data.append([
                    cat['name'],
                    f"${cat['amount']:,.2f}",
                    f"{cat['percentage']:.1f}%"
                ])

            category_table = Table(category_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(category_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _generate_chart_image(chart_data: Dict) -> BytesIO:
        """Generate chart as image using matplotlib"""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        # Generate chart based on chart_data
        # ...

        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)
        return buffer
```

**Excel Export (openpyxl):**
```python
# app/services/export/excel_export_service.py

from openpyxl import Workbook
from openpyxl.styles import Font, Fill, Alignment, Border, Side, PatternFill
from openpyxl.chart import PieChart, BarChart, LineChart, Reference
from io import BytesIO

class ExcelExportService:
    """Generate Excel reports with multiple sheets and charts"""

    @staticmethod
    async def generate_report_excel(report_data: Dict, user: User) -> BytesIO:
        """
        Generate Excel workbook with multiple sheets:
        - Summary (metrics and KPIs)
        - Transactions (detailed list)
        - Categories (breakdown)
        - Charts (visualizations)
        """
        wb = Workbook()

        # Sheet 1: Summary
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ExcelExportService._create_summary_sheet(ws_summary, report_data)

        # Sheet 2: Transactions
        ws_transactions = wb.create_sheet("Transactions")
        ExcelExportService._create_transactions_sheet(ws_transactions, report_data['entries'])

        # Sheet 3: Category Breakdown
        ws_categories = wb.create_sheet("Categories")
        ExcelExportService._create_category_sheet(ws_categories, report_data['category_breakdown'])

        # Sheet 4: Charts
        ws_charts = wb.create_sheet("Charts")
        ExcelExportService._create_charts_sheet(ws_charts, report_data)

        # Save to BytesIO
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _create_summary_sheet(ws, data):
        """Create formatted summary sheet"""
        # Headers
        ws['A1'] = 'BudgetPulse Financial Report'
        ws['A1'].font = Font(size=18, bold=True, color='1E3A8A')
        ws.merge_cells('A1:D1')

        # Metrics
        ws['A3'] = 'Metric'
        ws['B3'] = 'Value'
        ws['A3'].font = Font(bold=True)
        ws['B3'].font = Font(bold=True)

        metrics = [
            ('Total Income', data.get('total_income', 0)),
            ('Total Expenses', data.get('total_expenses', 0)),
            ('Net Savings', data.get('net_savings', 0)),
            ('Savings Rate', f"{data.get('savings_rate', 0):.1f}%"),
            ('Transaction Count', data.get('transaction_count', 0)),
        ]

        for idx, (metric, value) in enumerate(metrics, start=4):
            ws[f'A{idx}'] = metric
            ws[f'B{idx}'] = value
            if isinstance(value, (int, float)) and not isinstance(value, str):
                ws[f'B{idx}'].number_format = '$#,##0.00'

        # Styling
        for row in ws['A3:B8']:
            for cell in row:
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

    @staticmethod
    def _create_transactions_sheet(ws, entries):
        """Create detailed transactions sheet"""
        headers = ['Date', 'Type', 'Category', 'Amount', 'Note']
        ws.append(headers)

        # Style header
        for cell in ws[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='3B82F6', end_color='3B82F6', fill_type='solid')

        # Add data
        for entry in entries:
            ws.append([
                entry['date'].strftime('%Y-%m-%d'),
                entry['type'].capitalize(),
                entry['category'],
                entry['amount'],
                entry.get('note', '')
            ])

        # Format amount column
        for row in range(2, ws.max_row + 1):
            ws[f'D{row}'].number_format = '$#,##0.00'

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

    @staticmethod
    def _create_charts_sheet(ws, data):
        """Create sheet with embedded charts"""
        # Pie Chart for Categories
        pie_chart = PieChart()
        pie_chart.title = "Spending by Category"

        # Data for chart
        ws.append(['Category', 'Amount'])
        for cat in data['category_breakdown']:
            ws.append([cat['name'], cat['amount']])

        data_ref = Reference(ws, min_col=2, min_row=1, max_row=len(data['category_breakdown']) + 1)
        labels_ref = Reference(ws, min_col=1, min_row=2, max_row=len(data['category_breakdown']) + 1)
        pie_chart.add_data(data_ref, titles_from_data=True)
        pie_chart.set_categories(labels_ref)

        ws.add_chart(pie_chart, 'E2')
```

**CSV Export:**
```python
# app/services/export/csv_export_service.py

import csv
from io import StringIO

class CSVExportService:
    """Generate CSV files for transactions and reports"""

    @staticmethod
    async def export_transactions_csv(entries: List[Entry]) -> StringIO:
        """Export transactions to CSV"""
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Currency', 'Note', 'Description'])

        # Data
        for entry in entries:
            writer.writerow([
                entry.date.strftime('%Y-%m-%d'),
                entry.type,
                entry.category.name if entry.category else 'Uncategorized',
                f"{entry.amount:.2f}",
                entry.currency_code,
                entry.note or '',
                entry.description or ''
            ])

        output.seek(0)
        return output
```

**API Endpoints:**
```python
# app/api/v1/export.py

@router.get("/export/report/{report_id}/pdf")
async def export_report_pdf(report_id: int, user: User = Depends(current_user)):
    """Export report as PDF"""
    report = # get report
    pdf_buffer = await PDFExportService.generate_report_pdf(report, user)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
    )

@router.get("/export/report/{report_id}/excel")
async def export_report_excel(report_id: int, user: User = Depends(current_user)):
    """Export report as Excel"""

@router.get("/export/transactions/csv")
async def export_transactions_csv(
    start_date: date,
    end_date: date,
    user: User = Depends(current_user)
):
    """Export transactions as CSV"""
```

---

### **Phase 3: Gamification System** (Weeks 8-10)
**Priority:** 🟡 **MEDIUM** - Engagement features
**Effort:** 3 weeks | **Team Size:** 2 developers

#### 3.1 Comprehensive Achievement & Badge System (Week 8)

**Achievement Categories & Tiers:**

```python
# app/services/gamification/achievement_definitions.py

ACHIEVEMENT_DEFINITIONS = [
    # TRACKING CONSISTENCY
    {
        'code': 'tracker_bronze',
        'name': 'Consistent Tracker',
        'description': 'Log transactions for 7 consecutive days',
        'category': 'tracking',
        'tier': 'bronze',
        'icon': 'streak-7',
        'points': 50,
        'unlock_criteria': {'type': 'daily_streak', 'days': 7}
    },
    {
        'code': 'tracker_silver',
        'name': 'Dedicated Tracker',
        'description': 'Log transactions for 30 consecutive days',
        'category': 'tracking',
        'tier': 'silver',
        'icon': 'streak-30',
        'points': 200,
        'unlock_criteria': {'type': 'daily_streak', 'days': 30}
    },
    {
        'code': 'tracker_gold',
        'name': 'Master Tracker',
        'description': 'Log transactions for 90 consecutive days',
        'category': 'tracking',
        'tier': 'gold',
        'icon': 'streak-90',
        'points': 500,
        'unlock_criteria': {'type': 'daily_streak', 'days': 90}
    },

    # NO-SPEND CHALLENGES
    {
        'code': 'no_spend_bronze',
        'name': 'Spender Restraint',
        'description': 'Have 3 no-spend days in a month',
        'category': 'spending',
        'tier': 'bronze',
        'icon': 'piggy-bank',
        'points': 30,
        'unlock_criteria': {'type': 'no_spend_days_monthly', 'count': 3}
    },
    {
        'code': 'no_spend_silver',
        'name': 'Mindful Spender',
        'description': 'Have 7 no-spend days in a month',
        'category': 'spending',
        'tier': 'silver',
        'icon': 'wallet-closed',
        'points': 100,
        'unlock_criteria': {'type': 'no_spend_days_monthly', 'count': 7}
    },

    # SAVINGS ACHIEVEMENTS
    {
        'code': 'saver_bronze',
        'name': 'Savings Starter',
        'description': 'Achieve 10% savings rate for a month',
        'category': 'saving',
        'tier': 'bronze',
        'icon': 'savings-10',
        'points': 75,
        'unlock_criteria': {'type': 'monthly_savings_rate', 'rate': 0.10}
    },
    {
        'code': 'saver_silver',
        'name': 'Smart Saver',
        'description': 'Achieve 20% savings rate for a month',
        'category': 'saving',
        'tier': 'silver',
        'icon': 'savings-20',
        'points': 150,
        'unlock_criteria': {'type': 'monthly_savings_rate', 'rate': 0.20}
    },
    {
        'code': 'saver_gold',
        'name': 'Savings Champion',
        'description': 'Achieve 30% savings rate for a month',
        'category': 'saving',
        'tier': 'gold',
        'icon': 'trophy-gold',
        'points': 300,
        'unlock_criteria': {'type': 'monthly_savings_rate', 'rate': 0.30}
    },

    # GOAL ACHIEVEMENTS
    {
        'code': 'goal_achiever',
        'name': 'Goal Achiever',
        'description': 'Complete your first financial goal',
        'category': 'goal',
        'tier': 'bronze',
        'icon': 'target-hit',
        'points': 100,
        'unlock_criteria': {'type': 'goals_completed', 'count': 1}
    },
    {
        'code': 'goal_master',
        'name': 'Goal Master',
        'description': 'Complete 5 financial goals',
        'category': 'goal',
        'tier': 'gold',
        'icon': 'trophy-goals',
        'points': 500,
        'unlock_criteria': {'type': 'goals_completed', 'count': 5}
    },

    # BUDGET DISCIPLINE
    {
        'code': 'budget_keeper',
        'name': 'Budget Keeper',
        'description': 'Stay under budget for 7 consecutive days',
        'category': 'budget',
        'tier': 'bronze',
        'icon': 'shield-check',
        'points': 60,
        'unlock_criteria': {'type': 'under_budget_streak', 'days': 7}
    },

    # CATEGORY DIVERSITY
    {
        'code': 'category_explorer',
        'name': 'Category Explorer',
        'description': 'Use 10+ different categories in a month',
        'category': 'tracking',
        'tier': 'silver',
        'icon': 'grid-diverse',
        'points': 80,
        'unlock_criteria': {'type': 'unique_categories_monthly', 'count': 10}
    },

    # MILESTONE ACHIEVEMENTS
    {
        'code': 'first_entry',
        'name': 'Getting Started',
        'description': 'Log your first transaction',
        'category': 'milestone',
        'tier': 'bronze',
        'icon': 'rocket',
        'points': 10,
        'unlock_criteria': {'type': 'total_entries', 'count': 1}
    },
    {
        'code': 'hundred_entries',
        'name': 'Century Club',
        'description': 'Log 100 transactions',
        'category': 'milestone',
        'tier': 'silver',
        'icon': 'milestone-100',
        'points': 150,
        'unlock_criteria': {'type': 'total_entries', 'count': 100}
    },
    {
        'code': 'thousand_entries',
        'name': 'Data Master',
        'description': 'Log 1000 transactions',
        'category': 'milestone',
        'tier': 'platinum',
        'icon': 'milestone-1000',
        'points': 1000,
        'unlock_criteria': {'type': 'total_entries', 'count': 1000}
    },

    # SPECIAL ACHIEVEMENTS
    {
        'code': 'early_bird',
        'name': 'Early Bird',
        'description': 'Log transaction before 8 AM',
        'category': 'special',
        'tier': 'bronze',
        'icon': 'sunrise',
        'points': 25,
        'unlock_criteria': {'type': 'entry_before_time', 'hour': 8}
    },
    {
        'code': 'perfectionist',
        'name': 'Perfectionist',
        'description': 'Have all entries categorized for a month',
        'category': 'tracking',
        'tier': 'gold',
        'icon': 'check-perfect',
        'points': 250,
        'unlock_criteria': {'type': 'all_categorized_monthly', 'percentage': 100}
    }

    # Total: 20+ achievements
]
```

**Achievement Checker:**
```python
# app/services/gamification/achievement_checker.py

class AchievementChecker:
    """Check and unlock achievements based on user activity"""

    @staticmethod
    async def check_all_achievements(user_id: int, db: Session) -> List[UserAchievement]:
        """Check all achievement criteria and unlock new ones"""
        newly_unlocked = []

        for achievement_def in ACHIEVEMENT_DEFINITIONS:
            # Check if already unlocked
            existing = db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement.has(code=achievement_def['code'])
            ).first()

            if existing:
                continue

            # Check unlock criteria
            criteria = achievement_def['unlock_criteria']
            if await AchievementChecker._check_criteria(user_id, criteria, db):
                # Unlock achievement
                achievement = db.query(Achievement).filter(
                    Achievement.code == achievement_def['code']
                ).first()

                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    is_new=True
                )
                db.add(user_achievement)
                newly_unlocked.append(user_achievement)

        db.commit()
        return newly_unlocked

    @staticmethod
    async def _check_criteria(user_id: int, criteria: Dict, db: Session) -> bool:
        """Check if user meets specific criteria"""
        criteria_type = criteria['type']

        if criteria_type == 'daily_streak':
            return await AchievementChecker._check_daily_streak(user_id, criteria['days'], db)
        elif criteria_type == 'no_spend_days_monthly':
            return await AchievementChecker._check_no_spend_days(user_id, criteria['count'], db)
        elif criteria_type == 'monthly_savings_rate':
            return await AchievementChecker._check_savings_rate(user_id, criteria['rate'], db)
        elif criteria_type == 'goals_completed':
            return await AchievementChecker._check_goals_completed(user_id, criteria['count'], db)
        # ... more criteria checks

        return False

    @staticmethod
    async def _check_daily_streak(user_id: int, required_days: int, db: Session) -> bool:
        """Check if user has logged entries for N consecutive days"""
        # Get dates with entries in last N+5 days
        cutoff_date = date.today() - timedelta(days=required_days + 5)

        entry_dates = db.query(func.date(Entry.date)).filter(
            Entry.user_id == user_id,
            Entry.date >= cutoff_date
        ).distinct().order_by(func.date(Entry.date).desc()).all()

        if not entry_dates:
            return False

        # Check consecutive streak
        current_streak = 1
        for i in range(len(entry_dates) - 1):
            date1 = entry_dates[i][0]
            date2 = entry_dates[i + 1][0]

            if (date1 - date2).days == 1:
                current_streak += 1
                if current_streak >= required_days:
                    return True
            else:
                current_streak = 1

        return current_streak >= required_days
```

**Points & Levels System:**
```python
# app/models/user_gamification.py

class UserGamificationProfile(Base):
    """Gamification profile for each user"""
    __tablename__ = "user_gamification_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Points & Levels
    total_points = Column(Integer, default=0)
    current_level = Column(Integer, default=1)
    points_to_next_level = Column(Integer, default=100)

    # Statistics
    achievements_unlocked = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)

    # Challenges
    active_challenges = Column(Integer, default=0)
    completed_challenges = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="gamification_profile")

# Level calculation
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 1000,
    6: 2000,
    7: 4000,
    8: 7500,
    9: 12000,
    10: 20000,
    # ... up to level 50+
}

def calculate_level(points: int) -> Tuple[int, int]:
    """Calculate level and points to next level"""
    level = 1
    for lvl, threshold in LEVEL_THRESHOLDS.items():
        if points >= threshold:
            level = lvl
        else:
            return (level, threshold - points)
    return (level, 0)  # Max level reached
```

---

#### 3.2 Savings Challenges (Week 9)

**Database Schema:**
```sql
CREATE TABLE savings_challenges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    challenge_type VARCHAR(50),              -- 'personal', 'community', 'system'

    -- Challenge parameters
    target_amount NUMERIC(12, 2),
    duration_days INTEGER,
    start_date DATE,
    end_date DATE,

    -- Rules
    rules JSONB,                             -- Custom challenge rules
    difficulty VARCHAR(20),                  -- 'easy', 'medium', 'hard'

    -- Rewards
    points_reward INTEGER,
    badge_reward VARCHAR(100),

    -- Community challenge specifics
    max_participants INTEGER,
    is_public BOOLEAN DEFAULT TRUE,
    created_by_user_id INTEGER REFERENCES users(id),

    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'      -- 'active', 'completed', 'cancelled'
);

CREATE TABLE challenge_participants (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER REFERENCES savings_challenges(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- Progress
    current_amount NUMERIC(12, 2) DEFAULT 0,
    progress_percentage NUMERIC(5, 2) DEFAULT 0,

    -- Status
    joined_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',     -- 'active', 'completed', 'failed', 'withdrawn'

    -- Ranking
    rank INTEGER,

    UNIQUE(challenge_id, user_id)
);

CREATE TABLE challenge_updates (
    id SERIAL PRIMARY KEY,
    participant_id INTEGER REFERENCES challenge_participants(id) ON DELETE CASCADE,

    update_type VARCHAR(50),                 -- 'progress', 'milestone', 'completion'
    amount NUMERIC(12, 2),
    message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_challenges_status ON savings_challenges(status, end_date);
CREATE INDEX idx_participants_challenge ON challenge_participants(challenge_id, status);
```

**Pre-defined Challenge Templates:**
```python
# app/services/gamification/challenge_templates.py

CHALLENGE_TEMPLATES = [
    {
        'name': 'No-Spend Weekend',
        'description': 'Go a full weekend (Sat-Sun) without spending any money',
        'challenge_type': 'personal',
        'duration_days': 2,
        'rules': {
            'allowed_categories': [],  # No spending allowed
            'weekend_only': True
        },
        'difficulty': 'medium',
        'points_reward': 150,
        'badge_reward': 'weekend_warrior'
    },
    {
        'name': '$5 Daily Challenge',
        'description': 'Spend no more than $5 per day for a week',
        'challenge_type': 'personal',
        'duration_days': 7,
        'rules': {
            'daily_limit': 5.00,
            'excluded_categories': ['Bills', 'Rent']  # Essentials excluded
        },
        'difficulty': 'hard',
        'points_reward': 300,
        'badge_reward': 'frugal_master'
    },
    {
        'name': 'Save $500 in 30 Days',
        'description': 'Save $500 over the next month',
        'challenge_type': 'community',
        'target_amount': 500.00,
        'duration_days': 30,
        'rules': {
            'savings_goal': 500.00,
            'tracking_method': 'net_savings'
        },
        'difficulty': 'medium',
        'points_reward': 500,
        'badge_reward': 'saver_500'
    },
    {
        'name': 'Coffee Shop Freeze',
        'description': 'No coffee shop purchases for 14 days',
        'challenge_type': 'personal',
        'duration_days': 14,
        'rules': {
            'banned_categories': ['Coffee', 'Dining Out'],
            'banned_keywords': ['starbucks', 'cafe', 'coffee']
        },
        'difficulty': 'medium',
        'points_reward': 200,
        'badge_reward': 'coffee_free'
    },
    {
        'name': 'Meal Prep Master',
        'description': 'Cook at home for all meals for 7 days',
        'challenge_type': 'personal',
        'duration_days': 7,
        'rules': {
            'banned_categories': ['Dining Out', 'Fast Food', 'Restaurants'],
            'allowed_categories': ['Groceries']
        },
        'difficulty': 'hard',
        'points_reward': 250,
        'badge_reward': 'home_chef'
    }
]
```

**Challenge Service:**
```python
# app/services/gamification/challenge_service.py

class ChallengeService:
    """Manage savings challenges"""

    @staticmethod
    async def create_challenge_from_template(
        template_name: str,
        user_id: int,
        db: Session
    ) -> SavingsChallenge:
        """Create a new challenge from a template"""
        template = next(t for t in CHALLENGE_TEMPLATES if t['name'] == template_name)

        challenge = SavingsChallenge(
            name=template['name'],
            description=template['description'],
            challenge_type='personal',
            target_amount=template.get('target_amount'),
            duration_days=template['duration_days'],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=template['duration_days']),
            rules=template['rules'],
            difficulty=template['difficulty'],
            points_reward=template['points_reward'],
            badge_reward=template['badge_reward'],
            created_by_user_id=user_id
        )

        db.add(challenge)
        db.commit()

        # Auto-join user as participant
        participant = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=user_id
        )
        db.add(participant)
        db.commit()

        return challenge

    @staticmethod
    async def check_challenge_progress(participant_id: int, db: Session) -> Dict:
        """Check and update participant's progress"""
        participant = db.query(ChallengeParticipant).get(participant_id)
        challenge = participant.challenge

        # Get user's entries during challenge period
        entries = db.query(Entry).filter(
            Entry.user_id == participant.user_id,
            Entry.date >= challenge.start_date,
            Entry.date <= challenge.end_date
        ).all()

        # Apply challenge rules
        rules = challenge.rules
        progress = 0

        if 'daily_limit' in rules:
            # Check daily spending limit
            progress = ChallengeService._check_daily_limit(entries, rules['daily_limit'])
        elif 'savings_goal' in rules:
            # Check savings target
            income = sum(e.amount for e in entries if e.type == 'income')
            expenses = sum(e.amount for e in entries if e.type == 'expense')
            savings = income - expenses
            progress = (savings / rules['savings_goal']) * 100
        elif 'banned_categories' in rules:
            # Check no spending in banned categories
            violations = [e for e in entries if e.category.name in rules['banned_categories']]
            progress = 100 if not violations else 0

        # Update participant
        participant.current_amount = # calculate
        participant.progress_percentage = min(progress, 100)

        # Check for completion
        if progress >= 100 and not participant.completed_at:
            participant.status = 'completed'
            participant.completed_at = datetime.utcnow()

            # Award points and badge
            user_profile = db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == participant.user_id
            ).first()
            user_profile.total_points += challenge.points_reward

            # Unlock badge
            # ...

        db.commit()
        return {'progress': progress, 'status': participant.status}

    @staticmethod
    async def get_community_leaderboard(challenge_id: int, db: Session) -> List[Dict]:
        """Get leaderboard for a community challenge"""
        participants = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.challenge_id == challenge_id
        ).order_by(
            ChallengeParticipant.progress_percentage.desc(),
            ChallengeParticipant.joined_at.asc()
        ).all()

        leaderboard = []
        for idx, participant in enumerate(participants, start=1):
            participant.rank = idx
            leaderboard.append({
                'rank': idx,
                'user_id': participant.user_id,
                'username': participant.user.name,
                'progress': participant.progress_percentage,
                'amount': participant.current_amount,
                'status': participant.status
            })

        db.commit()
        return leaderboard
```

**Frontend UI:**
```html
<!-- app/templates/challenges/challenges_hub.html -->
<div class="challenges-hub">
    <h1>Savings Challenges</h1>

    <!-- Active Challenges -->
    <section class="active-challenges">
        <h2>Your Active Challenges</h2>
        <div class="challenge-cards">
            {% for challenge in active_challenges %}
            <div class="challenge-card">
                <div class="challenge-header">
                    <span class="difficulty-badge {{ challenge.difficulty }}">
                        {{ challenge.difficulty.capitalize() }}
                    </span>
                    <h3>{{ challenge.name }}</h3>
                </div>

                <p class="challenge-description">{{ challenge.description }}</p>

                <div class="challenge-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ challenge.progress }}%"></div>
                    </div>
                    <span class="progress-text">{{ challenge.progress }}% Complete</span>
                </div>

                <div class="challenge-stats">
                    <div class="stat">
                        <span class="label">Days Remaining:</span>
                        <span class="value">{{ challenge.days_remaining }}</span>
                    </div>
                    <div class="stat">
                        <span class="label">Reward:</span>
                        <span class="value">{{ challenge.points_reward }} pts</span>
                    </div>
                </div>

                <div class="challenge-actions">
                    <button onclick="viewChallengeDetails({{ challenge.id }})">View Details</button>
                    <button onclick="withdrawFromChallenge({{ challenge.id }})" class="secondary">Withdraw</button>
                </div>
            </div>
            {% endfor %}
        </div>
    </section>

    <!-- Available Challenges -->
    <section class="available-challenges">
        <h2>Join a New Challenge</h2>

        <div class="challenge-filters">
            <button class="filter-btn active" data-type="all">All</button>
            <button class="filter-btn" data-type="personal">Personal</button>
            <button class="filter-btn" data-type="community">Community</button>
            <button class="filter-btn" data-difficulty="easy">Easy</button>
            <button class="filter-btn" data-difficulty="medium">Medium</button>
            <button class="filter-btn" data-difficulty="hard">Hard</button>
        </div>

        <div class="challenge-grid">
            {% for template in challenge_templates %}
            <div class="challenge-template-card" data-difficulty="{{ template.difficulty }}">
                <div class="challenge-icon">
                    <i class="bi bi-trophy"></i>
                </div>
                <h3>{{ template.name }}</h3>
                <p>{{ template.description }}</p>

                <div class="template-info">
                    <span class="duration">{{ template.duration_days }} days</span>
                    <span class="reward">+{{ template.points_reward }} pts</span>
                </div>

                <button onclick="joinChallenge('{{ template.name }}')" class="btn-join">
                    Join Challenge
                </button>
            </div>
            {% endfor %}
        </div>
    </section>

    <!-- Community Leaderboards -->
    <section class="community-leaderboards">
        <h2>Community Leaderboards</h2>

        {% for challenge in community_challenges %}
        <div class="leaderboard-card">
            <h3>{{ challenge.name }}</h3>
            <p>{{ challenge.participants_count }} participants</p>

            <table class="leaderboard-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>User</th>
                        <th>Progress</th>
                        <th>Amount Saved</th>
                    </tr>
                </thead>
                <tbody>
                    {% for participant in challenge.leaderboard[:10] %}
                    <tr class="{% if participant.user_id == current_user.id %}current-user{% endif %}">
                        <td>{{ participant.rank }}</td>
                        <td>{{ participant.username }}</td>
                        <td>{{ participant.progress }}%</td>
                        <td>${{ participant.amount }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </section>
</div>
```

---

#### 3.3 Financial Health Score Dashboard (Week 10)

**Dashboard Component:**
```html
<!-- app/templates/gamification/financial_health.html -->
<div class="financial-health-dashboard">
    <h1>Financial Health Score</h1>

    <!-- Overall Score Card -->
    <div class="score-card-main">
        <div class="score-gauge">
            <canvas id="health-score-gauge" width="300" height="200"></canvas>
        </div>

        <div class="score-details">
            <h2 class="score-value" data-score="{{ health_score.overall_score }}">
                {{ health_score.overall_score }}
            </h2>
            <p class="score-grade {{ health_score.grade.lower() }}">
                {{ health_score.grade }}
            </p>
            <p class="score-trend">
                {% if health_score.trend == 'improving' %}
                <i class="bi bi-arrow-up text-success"></i> Improving
                {% elif health_score.trend == 'declining' %}
                <i class="bi bi-arrow-down text-danger"></i> Declining
                {% else %}
                <i class="bi bi-dash text-warning"></i> Stable
                {% endif %}
            </p>
        </div>
    </div>

    <!-- Component Breakdown -->
    <div class="score-components">
        <h3>Score Breakdown</h3>

        <div class="component-cards">
            {% for component, score in health_score.component_scores.items() %}
            <div class="component-card">
                <div class="component-header">
                    <h4>{{ component.replace('_', ' ').title() }}</h4>
                    <span class="component-score">{{ score }}/100</span>
                </div>

                <div class="component-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ score }}%; background: {{ get_score_color(score) }}"></div>
                    </div>
                </div>

                <p class="component-description">
                    {{ get_component_description(component, score) }}
                </p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Historical Trend -->
    <div class="score-history">
        <h3>Health Score History</h3>
        <canvas id="score-history-chart" height="100"></canvas>
    </div>

    <!-- Recommendations -->
    <div class="recommendations">
        <h3>How to Improve Your Score</h3>

        <div class="recommendation-list">
            {% for rec in health_score.recommendations %}
            <div class="recommendation-card">
                <div class="rec-icon">
                    <i class="bi bi-lightbulb"></i>
                </div>
                <div class="rec-content">
                    <h4>{{ rec.title }}</h4>
                    <p>{{ rec.description }}</p>
                    <span class="impact">Potential Impact: +{{ rec.points }} points</span>
                </div>
                <button onclick="applyRecommendation('{{ rec.id }}')" class="btn-apply">
                    Take Action
                </button>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Comparison (Optional - Privacy Respecting) -->
    <div class="score-comparison">
        <h3>How You Compare</h3>
        <p>Your score is in the <strong>{{ health_score.percentile }}th percentile</strong> of BudgetPulse users.</p>

        <div class="percentile-chart">
            <!-- Visual distribution chart -->
        </div>
    </div>
</div>
```

**Gauge Chart (Chart.js):**
```javascript
// static/js/charts/health-score-gauge.js

function createHealthScoreGauge(canvasId, score) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Determine color based on score
    const getScoreColor = (score) => {
        if (score >= 90) return '#10b981'; // Excellent - Green
        if (score >= 70) return '#3b82f6'; // Good - Blue
        if (score >= 50) return '#f59e0b'; // Fair - Yellow
        return '#ef4444'; // Poor - Red
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [getScoreColor(score), '#e5e7eb'],
                borderWidth: 0
            }]
        },
        options: {
            rotation: -90,
            circumference: 180,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        },
        plugins: [{
            id: 'centerText',
            afterDraw: (chart) => {
                const { ctx, chartArea: { width, height } } = chart;
                ctx.save();

                ctx.font = 'bold 48px Arial';
                ctx.fillStyle = getScoreColor(score);
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(score, width / 2, height / 2 + 20);

                ctx.restore();
            }
        }]
    });
}
```

---

### **Phase 4: Advanced ML & Predictions** (Weeks 11-14)
**Priority:** 🟡 **MEDIUM-LOW** - Advanced features
**Effort:** 4 weeks | **Team Size:** 1-2 ML engineers

#### 4.1 Seasonal Forecasting with Prophet (Weeks 11-12)

**Dependencies:**
```bash
pip install prophet
pip install holidays
```

**Prophet Model Service:**
```python
# app/ai/services/prophet_forecast_service.py

from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import pandas as pd
import holidays

class ProphetForecastService:
    """Advanced forecasting using Facebook Prophet"""

    @staticmethod
    async def forecast_spending(
        user_id: int,
        db: Session,
        forecast_days: int = 90
    ) -> Dict:
        """
        Generate spending forecast with seasonality detection

        Features:
        - Trend detection (increasing/decreasing/stable)
        - Weekly seasonality (day-of-week patterns)
        - Monthly seasonality (beginning/end of month)
        - Holiday effects (spending patterns around holidays)
        - Confidence intervals (80%, 95%)
        """
        # Fetch historical data (minimum 6 months for good seasonality detection)
        min_date = date.today() - timedelta(days=365)
        entries = db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= min_date
        ).all()

        if len(entries) < 60:  # Minimum 60 data points
            raise ValueError("Insufficient data for Prophet forecasting. Need at least 2 months of data.")

        # Prepare data for Prophet
        df = pd.DataFrame([
            {'ds': entry.date, 'y': float(entry.amount)}
            for entry in entries
        ])

        # Aggregate daily totals
        df = df.groupby('ds').sum().reset_index()

        # Initialize Prophet model
        model = Prophet(
            growth='linear',                    # or 'logistic' for bounded growth
            seasonality_mode='additive',        # or 'multiplicative'
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05        # Flexibility of trend (0.001-0.5)
        )

        # Add custom seasonalities
        model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=5
        )

        # Add country holidays
        us_holidays = holidays.US()
        model.add_country_holidays(country_name='US')

        # Fit model
        model.fit(df)

        # Generate forecast
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        # Cross-validation for accuracy assessment
        cv_results = cross_validation(
            model,
            initial='180 days',
            period='30 days',
            horizon='30 days'
        )
        metrics = performance_metrics(cv_results)

        # Extract results
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend', 'weekly', 'yearly']].tail(forecast_days)

        return {
            'forecast': forecast_data.to_dict('records'),
            'model_performance': {
                'mae': metrics['mae'].mean(),
                'mape': metrics['mape'].mean(),
                'rmse': metrics['rmse'].mean()
            },
            'components': {
                'trend': model.params['trend'].tolist(),
                'weekly': model.params['weekly'].tolist(),
                'yearly': model.params['yearly'].tolist() if model.yearly_seasonality else None
            },
            'insights': ProphetForecastService._generate_insights(forecast, model)
        }

    @staticmethod
    def _generate_insights(forecast: pd.DataFrame, model: Prophet) -> List[str]:
        """Generate natural language insights from forecast"""
        insights = []

        # Trend analysis
        trend = forecast['trend'].iloc[-1] - forecast['trend'].iloc[0]
        if trend > 0:
            insights.append(f"Your spending is trending upward by ${abs(trend):.2f}/day")
        elif trend < 0:
            insights.append(f"Your spending is trending downward by ${abs(trend):.2f}/day")
        else:
            insights.append("Your spending trend is stable")

        # Weekly pattern
        weekly_component = forecast['weekly'].mean()
        if weekly_component > 0:
            insights.append("You tend to spend more on weekends")
        else:
            insights.append("You tend to spend more on weekdays")

        # Seasonal pattern
        if model.yearly_seasonality:
            yearly_component = forecast['yearly'].mean()
            insights.append("Seasonal spending patterns detected")

        return insights
```

**API Endpoint:**
```python
# app/api/v1/forecasting.py

@router.get("/forecast/prophet")
async def get_prophet_forecast(
    forecast_days: int = 90,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get advanced spending forecast using Prophet"""
    try:
        forecast = await ProphetForecastService.forecast_spending(
            user_id=user.id,
            db=db,
            forecast_days=forecast_days
        )
        return forecast
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

#### 4.2 What-If Analysis & Scenario Planning (Week 13)

**Scenario Model:**
```python
# app/ai/services/scenario_analyzer.py

class ScenarioAnalyzer:
    """Analyze financial scenarios and their outcomes"""

    @staticmethod
    async def analyze_scenario(
        user_id: int,
        scenario_params: Dict,
        db: Session
    ) -> Dict:
        """
        Analyze a financial scenario

        Scenario types:
        1. "What if I cut spending in category X by Y%?"
        2. "What if my income increases by $Z?"
        3. "What if I save $X per month?"
        4. "What if I eliminate subscription Y?"
        5. "What if I have an unexpected expense of $X?"

        Returns projections for 3, 6, and 12 months
        """
        scenario_type = scenario_params['type']

        # Get baseline forecast
        baseline = await ScenarioAnalyzer._get_baseline_forecast(user_id, db)

        # Apply scenario modifications
        if scenario_type == 'spending_reduction':
            modified = ScenarioAnalyzer._apply_spending_reduction(
                baseline,
                scenario_params['category_id'],
                scenario_params['reduction_percentage']
            )
        elif scenario_type == 'income_increase':
            modified = ScenarioAnalyzer._apply_income_increase(
                baseline,
                scenario_params['monthly_increase']
            )
        elif scenario_type == 'savings_increase':
            modified = ScenarioAnalyzer._apply_savings_plan(
                baseline,
                scenario_params['monthly_savings']
            )
        elif scenario_type == 'expense_elimination':
            modified = ScenarioAnalyzer._eliminate_expense(
                baseline,
                scenario_params['expense_id']
            )
        elif scenario_type == 'unexpected_expense':
            modified = ScenarioAnalyzer._add_unexpected_expense(
                baseline,
                scenario_params['amount'],
                scenario_params['month']
            )

        # Calculate outcomes
        outcomes = ScenarioAnalyzer._calculate_outcomes(baseline, modified)

        return {
            'scenario': scenario_params,
            'baseline': baseline,
            'modified': modified,
            'outcomes': outcomes,
            'recommendations': ScenarioAnalyzer._generate_recommendations(outcomes)
        }

    @staticmethod
    def _calculate_outcomes(baseline: Dict, modified: Dict) -> Dict:
        """Calculate scenario outcomes compared to baseline"""
        return {
            '3_months': {
                'baseline_balance': baseline['balance_3m'],
                'scenario_balance': modified['balance_3m'],
                'difference': modified['balance_3m'] - baseline['balance_3m'],
                'percentage_change': ((modified['balance_3m'] - baseline['balance_3m']) / baseline['balance_3m'] * 100) if baseline['balance_3m'] != 0 else 0
            },
            '6_months': {
                'baseline_balance': baseline['balance_6m'],
                'scenario_balance': modified['balance_6m'],
                'difference': modified['balance_6m'] - baseline['balance_6m'],
                'percentage_change': ((modified['balance_6m'] - baseline['balance_6m']) / baseline['balance_6m'] * 100) if baseline['balance_6m'] != 0 else 0
            },
            '12_months': {
                'baseline_balance': baseline['balance_12m'],
                'scenario_balance': modified['balance_12m'],
                'difference': modified['balance_12m'] - baseline['balance_12m'],
                'percentage_change': ((modified['balance_12m'] - baseline['balance_12m']) / baseline['balance_12m'] * 100) if baseline['balance_12m'] != 0 else 0
            }
        }
```

**UI Component:**
```html
<!-- app/templates/analytics/scenario_planner.html -->
<div class="scenario-planner">
    <h1>What-If Scenario Planner</h1>

    <div class="scenario-builder">
        <h3>Create a Scenario</h3>

        <select id="scenario-type" onchange="updateScenarioForm()">
            <option value="">Select scenario type...</option>
            <option value="spending_reduction">Reduce Spending in Category</option>
            <option value="income_increase">Increase Income</option>
            <option value="savings_increase">Increase Monthly Savings</option>
            <option value="expense_elimination">Eliminate a Subscription/Bill</option>
            <option value="unexpected_expense">Plan for Unexpected Expense</option>
        </select>

        <div id="scenario-form">
            <!-- Dynamic form based on scenario type -->
        </div>

        <button onclick="runScenario()">Run Scenario</button>
    </div>

    <div id="scenario-results" style="display: none;">
        <h3>Scenario Results</h3>

        <div class="comparison-charts">
            <div class="chart-container">
                <h4>3-Month Projection</h4>
                <canvas id="chart-3m"></canvas>
            </div>
            <div class="chart-container">
                <h4>6-Month Projection</h4>
                <canvas id="chart-6m"></canvas>
            </div>
            <div class="chart-container">
                <h4>12-Month Projection</h4>
                <canvas id="chart-12m"></canvas>
            </div>
        </div>

        <div class="outcome-summary">
            <h4>Impact Summary</h4>
            <table class="impact-table">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Baseline</th>
                        <th>With Changes</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Dynamic content -->
                </tbody>
            </table>
        </div>

        <div class="recommendations">
            <h4>Recommendations</h4>
            <ul id="scenario-recommendations"></ul>
        </div>
    </div>
</div>
```

---

### **Phase 5: Polish & Testing** (Weeks 15-16)

#### 5.1 Performance Optimization (Week 15)

**Caching Strategy:**
```python
# app/core/cache.py

from functools import lru_cache
from redis import Redis
import json

class CacheService:
    """Redis-based caching for reports and forecasts"""

    def __init__(self):
        self.redis = Redis(host='localhost', port=6379, db=0)

    def get_cached_report(self, user_id: int, report_type: str, period: str) -> Optional[Dict]:
        """Get cached report"""
        key = f"report:{user_id}:{report_type}:{period}"
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None

    def cache_report(self, user_id: int, report_type: str, period: str, data: Dict, ttl: int = 3600):
        """Cache report with TTL"""
        key = f"report:{user_id}:{report_type}:{period}"
        self.redis.setex(key, ttl, json.dumps(data))

    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cached data for user"""
        pattern = f"report:{user_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
```

**Database Query Optimization:**
```sql
-- Add composite indexes for common queries

CREATE INDEX idx_entries_user_date_type ON entries(user_id, date DESC, type);
CREATE INDEX idx_entries_user_category ON entries(user_id, category_id);
CREATE INDEX idx_entries_date_range ON entries(date) WHERE user_id = current_user_id;

-- Materialized view for monthly summaries (PostgreSQL)
CREATE MATERIALIZED VIEW monthly_summaries AS
SELECT
    user_id,
    DATE_TRUNC('month', date) as month,
    type,
    SUM(amount) as total_amount,
    COUNT(*) as transaction_count
FROM entries
GROUP BY user_id, DATE_TRUNC('month', date), type;

CREATE INDEX ON monthly_summaries(user_id, month);

-- Refresh materialized view daily
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_summaries;
```

---

#### 5.2 Comprehensive Testing (Week 16)

**Test Coverage Goals:**
- Unit tests: 80%+ coverage
- Integration tests: All critical paths
- End-to-end tests: Major user journeys

```python
# tests/test_achievements.py

import pytest
from app.services.gamification.achievement_checker import AchievementChecker
from app.models.achievement import Achievement, UserAchievement

class TestAchievementSystem:
    """Test achievement unlocking logic"""

    @pytest.fixture
    def user(self, db):
        """Create test user"""
        user = User(email="test@example.com", name="Test User")
        db.add(user)
        db.commit()
        return user

    @pytest.mark.asyncio
    async def test_daily_streak_achievement(self, user, db):
        """Test that 7-day streak unlocks bronze achievement"""
        # Create entries for 7 consecutive days
        for i in range(7):
            entry = Entry(
                user_id=user.id,
                type='expense',
                amount=10.0,
                date=date.today() - timedelta(days=i)
            )
            db.add(entry)
        db.commit()

        # Check achievements
        unlocked = await AchievementChecker.check_all_achievements(user.id, db)

        # Assert bronze streak achievement was unlocked
        assert any(ua.achievement.code == 'tracker_bronze' for ua in unlocked)

    @pytest.mark.asyncio
    async def test_savings_rate_achievement(self, user, db):
        """Test that 20% savings rate unlocks silver achievement"""
        # Create income and expense entries for this month
        start_of_month = date.today().replace(day=1)

        # Add income: $2000
        income = Entry(user_id=user.id, type='income', amount=2000, date=start_of_month)
        db.add(income)

        # Add expenses: $1600 (20% savings rate)
        expense = Entry(user_id=user.id, type='expense', amount=1600, date=start_of_month)
        db.add(expense)
        db.commit()

        # Check achievements
        unlocked = await AchievementChecker.check_all_achievements(user.id, db)

        # Assert silver saver achievement was unlocked
        assert any(ua.achievement.code == 'saver_silver' for ua in unlocked)
```

---

## 🚀 Deployment & Launch Strategy

### Week 17-18: Beta Testing
- Deploy to staging environment
- Invite 50-100 beta testers
- Collect feedback via in-app surveys
- Monitor performance metrics
- Fix critical bugs

### Week 19: Production Release
- Gradual rollout (10% → 50% → 100% users)
- Monitor error rates and performance
- A/B test gamification features
- Adjust based on user behavior

### Week 20+: Iteration & Enhancement
- Analyze user engagement data
- Prioritize most-used features
- Deprecate unused features
- Plan next major release

---

## 📊 Success Metrics

### Advanced Analytics
- **Adoption Rate:** 60%+ users create at least one custom report
- **Engagement:** 40%+ weekly active users view dashboard
- **Export Usage:** 20%+ users export reports monthly
- **Prediction Accuracy:** MAPE < 15% for spending forecasts

### Gamification
- **Achievement Rate:** 80%+ users unlock at least 3 achievements in first month
- **Challenge Participation:** 30%+ users join at least one challenge
- **Score Engagement:** 50%+ users view health score weekly
- **Retention Impact:** 15%+ increase in 30-day retention

---

## 💰 Resource Requirements

### Development Team
- 2 Full-Stack Developers (Weeks 1-16)
- 1 ML Engineer (Weeks 11-14)
- 1 UI/UX Designer (Weeks 4-10)
- 1 QA Engineer (Weeks 15-16)

### Infrastructure
- PostgreSQL database upgrades (more storage for history)
- Redis caching layer
- Background job workers (Celery/APScheduler)
- Increased API rate limits

### Third-Party Services
- Prophet library (open-source, free)
- Chart.js (open-source, free)
- reportlab & openpyxl (open-source, free)

---

## 🎯 Next Steps

1. **Review & Approve Roadmap** - Stakeholder sign-off
2. **Prioritize Phases** - Adjust based on business needs
3. **Allocate Resources** - Assign team members
4. **Create Detailed Tickets** - Break down into sprint-sized tasks
5. **Begin Phase 1** - Start with achievement system

---

**Document Status:** DRAFT v1.0
**Estimated Total Effort:** 16-20 weeks
**Last Updated:** 2025-12-24
