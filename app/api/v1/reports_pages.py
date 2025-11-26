"""Reports Pages API"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.db.session import get_db
from app.deps import current_user
from app.templates import render
from app.services.weekly_report_service import WeeklyReportService
from app.services.monthly_report_service import MonthlyReportService
from app.services.historical_report_service import HistoricalReportService

router = APIRouter(prefix="/reports", tags=["Reports Pages"])


@router.get("/", response_class=HTMLResponse)
async def reports_index(
    request: Request,
    user=Depends(current_user),
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
    period: str = None,  # Optional: '2024-W45' for historical reports
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Weekly reports page"""
    try:
        historical_service = HistoricalReportService(db)

        # If period is specified, try to load historical report
        if period and period != 'current':
            historical_report = historical_service.get_report(user.id, 'weekly', period)
            if historical_report:
                return render(request, "reports/weekly.html", {
                    "user": user,
                    "report": historical_report,
                    "is_historical": True,
                    "request": request
                })

        # Generate current weekly report (without income)
        report_service = WeeklyReportService(db)
        report = report_service.generate_weekly_report(user.id, show_income=False)

        # Save to historical reports
        from datetime import datetime
        period_str = datetime.strptime(report['period']['start'], '%Y-%m-%d').strftime('%Y-W%W')
        period_start = datetime.strptime(report['period']['start'], '%Y-%m-%d').date()
        period_end = datetime.strptime(report['period']['end'], '%Y-%m-%d').date()

        historical_service.save_report(
            user_id=user.id,
            report_type='weekly',
            report_period=period_str,
            period_start=period_start,
            period_end=period_end,
            report_data=report,
            currency_code=report.get('currency', 'USD')
        )

        return render(request, "reports/weekly.html", {
            "user": user,
            "report": report,
            "is_historical": False,
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
    period: str = None,  # Optional: '2024-10' for historical reports
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Monthly reports page"""
    try:
        historical_service = HistoricalReportService(db)

        # If period is specified, try to load historical report
        if period and period != 'current':
            historical_report = historical_service.get_report(user.id, 'monthly', period)
            if historical_report:
                return render(request, "reports/monthly.html", {
                    "user": user,
                    "report": historical_report,
                    "is_historical": True,
                    "request": request
                })

        # Generate current monthly report (with income)
        report_service = MonthlyReportService(db)
        report = report_service.generate_monthly_report(user.id)

        # Save to historical reports
        period_str = f"{report['period']['year']}-{report['period']['month']:02d}"
        period_start = datetime.strptime(report['period']['start'], '%Y-%m-%d').date()
        period_end = datetime.strptime(report['period']['end'], '%Y-%m-%d').date()

        historical_service.save_report(
            user_id=user.id,
            report_type='monthly',
            report_period=period_str,
            period_start=period_start,
            period_end=period_end,
            report_data=report,
            currency_code=report.get('currency', 'USD')
        )

        return render(request, "reports/monthly.html", {
            "user": user,
            "report": report,
            "is_historical": False,
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
    year: int = None,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Comprehensive annual reports page with advanced analytics"""
    try:
        from app.services.annual_reports import get_comprehensive_annual_report
        from app.services.user_preferences import user_preferences_service
        from app.core.currency import currency_service

        historical_service = HistoricalReportService(db)

        # Get year parameter or use current year
        current_year = year if year else date.today().year
        period_str = str(current_year)

        # Check if we should load historical report
        if year and year != date.today().year:
            historical_report = historical_service.get_report(user.id, 'annual', period_str)
            if historical_report:
                # Get user's currency for formatting
                currency_code = user_preferences_service.get_user_currency(db, user.id)
                from app.core.currency import CURRENCIES
                currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])

                def format_currency(amount: float):
                    return currency_service.format_amount(amount, currency_code)

                return render(request, "reports/annual.html", {
                    "user": user,
                    "report": historical_report,
                    "current_year": current_year,
                    "format_currency": format_currency,
                    "user_currency_code": currency_code,
                    "user_currency": currency_info,
                    "is_historical": True,
                    "request": request
                })

        # Get user's currency
        currency_code = user_preferences_service.get_user_currency(db, user.id)
        from app.core.currency import CURRENCIES
        currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])

        # Create currency formatter
        def format_currency(amount: float):
            return currency_service.format_amount(amount, currency_code)

        # Generate comprehensive annual report
        report_data = get_comprehensive_annual_report(db, user.id, current_year)

        # Create report structure
        annual_report = {
            'period': {
                'start': date(current_year, 1, 1).isoformat(),
                'end': date(current_year, 12, 31).isoformat(),
                'year': current_year
            },
            'currency': currency_code,
            'summary': report_data['summary'],
            'year_over_year': report_data['year_over_year'],
            'monthly_breakdown': report_data['monthly_breakdown'],
            'seasonal_analysis': report_data['seasonal_analysis'],
            'category_analysis': report_data['category_analysis'],
            'achievements': report_data['achievements'],
            'generated_at': datetime.utcnow().isoformat()
        }

        # Save to historical reports
        historical_service.save_report(
            user_id=user.id,
            report_type='annual',
            report_period=period_str,
            period_start=date(current_year, 1, 1),
            period_end=date(current_year, 12, 31),
            report_data=annual_report,
            currency_code=currency_code
        )

        return render(request, "reports/annual.html", {
            "user": user,
            "report": annual_report,
            "current_year": current_year,
            "format_currency": format_currency,
            "user_currency_code": currency_code,
            "user_currency": currency_info,
            "is_historical": False,
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


@router.get("/api/historical")
async def list_historical_reports(
    report_type: str = None,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """API endpoint to list available historical reports"""
    historical_service = HistoricalReportService(db)
    reports = historical_service.list_reports(user.id, report_type=report_type)

    return JSONResponse(content={
        "success": True,
        "reports": reports,
        "count": len(reports)
    })


@router.post("/weekly/email")
async def email_weekly_report(
    user=Depends(current_user),
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
    
    return {"success": True, "message": "Weekly report email sent successfully"}


@router.post("/monthly/email")
async def email_monthly_report(
    user=Depends(current_user),
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
    
    return {"success": True, "message": "Monthly report email sent successfully"}


@router.post("/annual/email")
async def email_annual_report(
    user=Depends(current_user),
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
        
        return {"success": True, "message": "Annual report email sent successfully"}
    except Exception as e:
        print(f"ERROR in email_annual_report: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Failed to send annual report email: {str(e)}"}
