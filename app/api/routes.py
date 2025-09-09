from fastapi import APIRouter
from app.api.v1 import auth, categories, entries, metrics, dashboard


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(entries.router)
api_router.include_router(metrics.router)
api_router.include_router(dashboard.router)