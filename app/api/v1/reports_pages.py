"""Reports Pages API"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
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
    try:
        # For now, generate a basic annual summary
        from app.services.metrics import range_summary_multi_currency
        from datetime import date, timedelta
        
        # Get current year data
        current_year = date.today().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        
        # Get user's currency
        from app.models.user_preferences import UserPreferences
        user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        user_currency = user_prefs.currency_code if user_prefs and user_prefs.currency_code else 'USD'
        
        # Generate basic annual summary
        annual_summary = await range_summary_multi_currency(db, user.id, year_start, year_end, user_currency)
        
        # Create a basic annual report structure
        annual_report = {
            'period': {
                'start': year_start.isoformat(),
                'end': year_end.isoformat(),
                'year': current_year
            },
            'currency': user_currency,
            'summary': annual_summary,
            'show_income': True,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return render(request, "reports/annual.html", {
            "user": user,
            "report": annual_report,
            "request": request
        })
    except Exception as e:
        print(f"ERROR in annual_reports_page: {e}")
        import traceback
        traceback.print_exc()
        
        return render(request, "reports/annual.html", {
            "user": user,
            "report": None,
            "error": str(e),
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
    from app.services.email import email_service
    from app.services.monthly_report_service import MonthlyReportService
    
    report_service = MonthlyReportService(db)
    report = report_service.generate_monthly_report(user.id)
    
    await email_service.send_monthly_report_email(
        user.email,
        user.full_name or "User",
        report
    )
    
    return {"message": "Monthly report email sent successfully"}


@router.post("/annual/email")
async def email_annual_report(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Email current annual report"""
    try:
        from app.services.email import email_service
        from app.services.metrics import range_summary_multi_currency
        from datetime import date
        
        # Get current year data
        current_year = date.today().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        
        # Get user's currency
        from app.models.user_preferences import UserPreferences
        user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        user_currency = user_prefs.currency_code if user_prefs and user_prefs.currency_code else 'USD'
        
        # Generate basic annual summary
        annual_summary = await range_summary_multi_currency(db, user.id, year_start, year_end, user_currency)
        
        # Create a basic annual report structure
        annual_report = {
            'period': {
                'start': year_start.isoformat(),
                'end': year_end.isoformat(),
                'year': current_year
            },
            'currency': user_currency,
            'summary': annual_summary,
            'show_income': True,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        await email_service.send_annual_report_email(
            user.email,
            user.full_name or "User",
            annual_report
        )
        
        return {"message": "Annual report email sent successfully"}
    except Exception as e:
        print(f"ERROR in email_annual_report: {e}")
        import traceback
        traceback.print_exc()
        return {"message": f"Failed to send annual report email: {str(e)}"}
