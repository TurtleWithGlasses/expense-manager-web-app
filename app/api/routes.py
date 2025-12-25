from fastapi import APIRouter
from app.api.v1 import auth, categories, entries, metrics, dashboard, ai, reports, weekly_reports, reports_pages, report_status, theme, profile, settings, insights_pages, goals, goals_pages, calendar_pages, budget_intelligence, intelligence_pages, recurring_payments, payment_history, payment_analytics_pages, admin, feedback, voice, help_pages, forecasts, forecasts_pages, scenarios, scenarios_pages
from app.api.v1 import entries_rest, categories_rest, dashboard_rest, auth_rest
from app.api.currency import router as currency_router


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(settings.router)
api_router.include_router(profile.router)
api_router.include_router(categories.router)
api_router.include_router(entries.router)
api_router.include_router(metrics.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
api_router.include_router(budget_intelligence.router)
api_router.include_router(recurring_payments.router)
api_router.include_router(payment_history.router)  # Phase 29
api_router.include_router(payment_analytics_pages.router)  # Phase 30
api_router.include_router(reports.router)
api_router.include_router(weekly_reports.router)
api_router.include_router(reports_pages.router)
api_router.include_router(insights_pages.router)
api_router.include_router(goals.router)
api_router.include_router(goals_pages.router)
api_router.include_router(calendar_pages.router)
api_router.include_router(intelligence_pages.router)
api_router.include_router(report_status.router)
api_router.include_router(theme.router)
api_router.include_router(currency_router)
api_router.include_router(admin.router)  # Phase 33
api_router.include_router(feedback.router)  # Phase 33
api_router.include_router(voice.router)  # Phase 32 - Voice Commands
api_router.include_router(help_pages.router)  # Help & Documentation
api_router.include_router(forecasts.router)  # Phase 4 - Prophet Forecasting API
api_router.include_router(forecasts_pages.router)  # Phase 4 - Prophet Forecasting UI
api_router.include_router(scenarios.router)  # Phase 4 - Scenario Planning API
api_router.include_router(scenarios_pages.router)  # Phase 4 - Scenario Planning UI

# REST API endpoints (JSON-only, for mobile/external clients)
api_router.include_router(auth_rest.router)
api_router.include_router(entries_rest.router)
api_router.include_router(categories_rest.router)
api_router.include_router(dashboard_rest.router)