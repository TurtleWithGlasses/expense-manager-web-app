"""Weekly Reports API"""

from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
import json

from app.deps import current_user
from app.db.session import get_db
from app.templates import render
from app.services.weekly_report_service import WeeklyReportService
from app.services.email import email_service
from app.models.weekly_report import WeeklyReport, UserReportPreferences
from app.models.user import User

router = APIRouter(prefix="/reports/weekly", tags=["weekly_reports"])


@router.get("/current", response_class=JSONResponse)
async def get_current_week_report(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get the current week's report"""
    report_service = WeeklyReportService(db)
    report = report_service.generate_weekly_report(user.id)
    
    # Save to database
    _save_report(db, user.id, report)
    
    return JSONResponse({
        "success": True,
        "report": report
    })


@router.get("/widget", response_class=HTMLResponse)
async def get_weekly_report_widget(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get weekly report widget for dashboard (full report)"""
    # Check user preferences
    prefs = db.query(UserReportPreferences).filter(
        UserReportPreferences.user_id == user.id
    ).first()
    
    if prefs and not prefs.show_on_dashboard:
        return HTMLResponse("")  # Don't show if disabled
    
    # Get or generate current week report
    report = _get_or_generate_report(db, user.id)
    
    return render(request, "dashboard/_weekly_report.html", {
        "user": user,
        "report": report
    })


@router.get("/summary", response_class=HTMLResponse)
async def get_weekly_summary_widget(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get compact weekly summary widget for dashboard"""
    # Check user preferences
    prefs = db.query(UserReportPreferences).filter(
        UserReportPreferences.user_id == user.id
    ).first()
    
    if prefs and not prefs.show_on_dashboard:
        return HTMLResponse("")  # Don't show if disabled
    
    # Generate fresh compact report (without income)
    report_service = WeeklyReportService(db)
    report = report_service.generate_weekly_report(user.id, show_income=False)
    
    return render(request, "dashboard/_weekly_summary.html", {
        "user": user,
        "report": report
    })


@router.get("/", response_class=HTMLResponse)
async def weekly_reports_page(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Full weekly reports page with history"""
    # Get last 12 weeks of reports
    reports = db.query(WeeklyReport).filter(
        WeeklyReport.user_id == user.id
    ).order_by(WeeklyReport.week_start.desc()).limit(12).all()
    
    # Parse report data
    reports_data = []
    for report_record in reports:
        report_data = json.loads(report_record.report_data)
        reports_data.append({
            'id': report_record.id,
            'period': report_data['period'],
            'summary': report_data['summary'],
            'is_viewed': report_record.is_viewed
        })
    
    return render(request, "reports/weekly.html", {
        "user": user,
        "reports": reports_data
    })


@router.post("/email", response_class=JSONResponse)
async def email_weekly_report(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Send current week's report via email"""
    # Get or generate report
    report = _get_or_generate_report(db, user.id)
    
    if not report:
        return JSONResponse({
            "success": False,
            "message": "No report available"
        }, status_code=404)
    
    # Send email
    try:
        await email_service.send_weekly_report_email(
            user.email,
            user.full_name or user.email,
            report
        )
        
        # Mark as sent
        week_start = date.fromisoformat(report['period']['start'])
        report_record = db.query(WeeklyReport).filter(
            WeeklyReport.user_id == user.id,
            WeeklyReport.week_start == week_start
        ).first()
        
        if report_record:
            report_record.is_sent_via_email = True
            report_record.email_sent_at = datetime.utcnow()
            db.commit()
        
        return JSONResponse({
            "success": True,
            "message": "Weekly report sent to your email!"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }, status_code=500)


@router.get("/preferences", response_class=HTMLResponse)
async def report_preferences_page(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Report preferences page"""
    prefs = _get_or_create_preferences(db, user.id)
    
    return render(request, "settings/report_preferences.html", {
        "user": user,
        "preferences": prefs
    })


@router.post("/preferences", response_class=JSONResponse)
async def update_report_preferences(
    show_on_dashboard: bool = Form(False),
    send_email: bool = Form(False),
    frequency: str = Form("weekly"),
    include_achievements: bool = Form(True),
    include_recommendations: bool = Form(True),
    include_anomalies: bool = Form(True),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Update report preferences"""
    prefs = _get_or_create_preferences(db, user.id)
    
    # Update preferences
    prefs.frequency = frequency
    prefs.send_email = send_email
    prefs.show_on_dashboard = show_on_dashboard
    prefs.include_achievements = include_achievements
    prefs.include_recommendations = include_recommendations
    prefs.include_anomalies = include_anomalies
    
    db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Preferences updated successfully!"
    })


# Helper functions

def _get_or_generate_report(db: Session, user_id: int) -> dict:
    """Get existing report or generate new one"""
    # Always generate fresh report to ensure latest code changes are applied
    # This prevents cached reports with old currency symbols from being displayed
    report_service = WeeklyReportService(db)
    report = report_service.generate_weekly_report(user_id, show_income=False)
    
    # Save to database
    _save_report(db, user_id, report)
    
    return report


def _save_report(db: Session, user_id: int, report: dict) -> WeeklyReport:
    """Save report to database"""
    week_start = date.fromisoformat(report['period']['start'])
    week_end = date.fromisoformat(report['period']['end'])
    
    # Check if already exists
    existing = db.query(WeeklyReport).filter(
        WeeklyReport.user_id == user_id,
        WeeklyReport.week_start == week_start
    ).first()
    
    if existing:
        # Update existing
        existing.report_data = json.dumps(report)
        existing.total_expenses = report['summary']['total_expenses']
        existing.total_income = report['summary']['total_income']
        existing.net_savings = report['summary']['net_savings']
        existing.transaction_count = report['summary']['transaction_count']
        db.commit()
        return existing
    
    # Create new
    from datetime import datetime
    new_report = WeeklyReport(
        user_id=user_id,
        week_start=week_start,
        week_end=week_end,
        week_number=report['period']['week_number'],
        year=report['period']['year'],
        report_data=json.dumps(report),
        total_expenses=report['summary']['total_expenses'],
        total_income=report['summary']['total_income'],
        net_savings=report['summary']['net_savings'],
        transaction_count=report['summary']['transaction_count']
    )
    
    db.add(new_report)
    db.commit()
    
    return new_report


def _get_or_create_preferences(db: Session, user_id: int) -> UserReportPreferences:
    """Get or create user report preferences"""
    prefs = db.query(UserReportPreferences).filter(
        UserReportPreferences.user_id == user_id
    ).first()
    
    if not prefs:
        prefs = UserReportPreferences(
            user_id=user_id,
            frequency="weekly",
            send_email=True,
            show_on_dashboard=True,
            email_day_of_week=0,  # Monday
            email_hour=9,  # 9 AM
            include_achievements=True,
            include_recommendations=True,
            include_anomalies=True,
            include_category_breakdown=True
        )
        db.add(prefs)
        db.commit()
    
    return prefs

