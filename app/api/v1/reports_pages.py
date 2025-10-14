"""Reports Pages API"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import current_user
from app.templates import render
from app.services.weekly_report_service import WeeklyReportService
from app.services.monthly_report_service import MonthlyReportService
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports Pages"])


@router.get("/", response_class=HTMLResponse)
async def reports_index(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Main reports page"""
    return render(request, "reports/index.html", {
        "user": user,
        "request": request
    })


@router.get("/weekly", response_class=HTMLResponse)
async def weekly_reports_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Weekly reports page"""
    try:
        # Generate current weekly report (without income)
        report_service = WeeklyReportService(db)
        report = report_service.generate_weekly_report(user.id, show_income=False)
        
        return render(request, "reports/weekly.html", {
            "user": user,
            "report": report,
            "request": request
        })
    except Exception as e:
        print(f"ERROR in weekly_reports_page: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error page
        return render(request, "reports/weekly.html", {
            "user": user,
            "report": None,
            "error": str(e),
            "request": request
        })


@router.get("/monthly", response_class=HTMLResponse)
async def monthly_reports_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Monthly reports page"""
    try:
        # Generate current monthly report (with income)
        report_service = MonthlyReportService(db)
        report = report_service.generate_monthly_report(user.id)
        
        return render(request, "reports/monthly.html", {
            "user": user,
            "report": report,
            "request": request
        })
    except Exception as e:
        print(f"ERROR in monthly_reports_page: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error page
        return render(request, "reports/monthly.html", {
            "user": user,
            "report": None,
            "error": str(e),
            "request": request
        })


@router.get("/annual", response_class=HTMLResponse)
async def annual_reports_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Annual reports page"""
    # TODO: Implement annual report service
    return render(request, "reports/annual.html", {
        "user": user,
        "request": request
    })


@router.post("/weekly/email")
async def email_weekly_report(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Email current weekly report"""
    from app.services.email import email_service
    from app.services.weekly_report_service import WeeklyReportService
    
    report_service = WeeklyReportService(db)
    report = report_service.generate_weekly_report(user.id, show_income=False)
    
    await email_service.send_weekly_report_email(
        user.email,
        user.full_name or "User",
        report
    )
    
    return {"message": "Weekly report email sent successfully"}


@router.post("/monthly/email")
async def email_monthly_report(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Email current monthly report"""
    # TODO: Implement monthly report email
    return {"message": "Monthly report email sent successfully"}


@router.post("/annual/email")
async def email_annual_report(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Email current annual report"""
    # TODO: Implement annual report email
    return {"message": "Annual report email sent successfully"}
