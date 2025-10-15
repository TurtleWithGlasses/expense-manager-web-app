from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.deps import current_user
from app.services.report_status_service import ReportStatusService

router = APIRouter(prefix="/reports/status", tags=["report-status"])


class MarkViewedRequest(BaseModel):
    report_type: str
    report_period: str = "current"


@router.get("/")
async def get_report_statuses(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get status for all reports"""
    status_service = ReportStatusService(db)
    statuses = status_service.get_all_report_statuses(user.id)
    return {"statuses": statuses}


@router.post("/mark-viewed")
async def mark_report_as_viewed(
    request: MarkViewedRequest,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific report as viewed"""
    status_service = ReportStatusService(db)
    status_service.mark_report_as_viewed(user.id, request.report_type, request.report_period)
    return {"success": True, "message": f"{request.report_type} report marked as viewed"}
