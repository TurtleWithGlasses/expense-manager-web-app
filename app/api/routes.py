from fastapi import APIRouter
from app.api.v1 import auth, categories, entries, metrics, dashboard, ai, reports, weekly_reports, reports_pages, report_status, theme, profile, settings, insights_pages, goals, goals_pages, calendar_pages, budget_intelligence, intelligence_pages
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

# REST API endpoints (JSON-only, for mobile/external clients)
api_router.include_router(auth_rest.router)
api_router.include_router(entries_rest.router)
api_router.include_router(categories_rest.router)
api_router.include_router(dashboard_rest.router)