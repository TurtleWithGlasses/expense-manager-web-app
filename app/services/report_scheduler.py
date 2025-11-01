"""Automated Report Scheduler"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import asyncio
import json

from app.db.session import SessionLocal
from app.services.weekly_report_service import WeeklyReportService
from app.services.monthly_report_service import MonthlyReportService
from app.services.email import email_service
from app.models.weekly_report import UserReportPreferences, WeeklyReport
from app.models.user import User


class ReportScheduler:
    """Scheduler for automated financial reports"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_started = False
    
    def start(self):
        """Start the scheduler"""
        if self.is_started:
            return
        
        # Schedule weekly reports - Every Monday at 9 AM
        self.scheduler.add_job(
            self.send_weekly_reports,
            CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_reports',
            name='Send Weekly Financial Reports',
            replace_existing=True
        )

        # Schedule monthly reports - 1st day of every month at 9 AM
        self.scheduler.add_job(
            self.send_monthly_reports,
            CronTrigger(day=1, hour=9, minute=0),
            id='monthly_reports',
            name='Send Monthly Financial Reports',
            replace_existing=True
        )

        # Schedule daily check for custom preferences - Every day at 9 AM
        self.scheduler.add_job(
            self.send_custom_reports,
            CronTrigger(hour=9, minute=0),
            id='custom_reports',
            name='Send Custom Schedule Reports',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_started = True
        print("📅 Report scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_started = False
            print("📅 Report scheduler stopped")
    
    async def send_weekly_reports(self):
        """Send weekly reports to all users who have it enabled"""
        print(f"📊 Starting weekly report generation at {datetime.now()}")

        db = SessionLocal()
        try:
            # Get all users with weekly reports enabled
            preferences = db.query(UserReportPreferences).filter(
                UserReportPreferences.frequency == "weekly",
                UserReportPreferences.send_email == True
            ).all()

            print(f"📧 Found {len(preferences)} users to send reports to")

            for pref in preferences:
                try:
                    await self._send_report_to_user(db, pref.user_id)
                except Exception as e:
                    print(f"❌ Error sending report to user {pref.user_id}: {e}")

            print(f"✅ Weekly reports sent successfully")

        except Exception as e:
            print(f"❌ Error in weekly report job: {e}")
        finally:
            db.close()

    async def send_monthly_reports(self):
        """Send monthly reports to all users on the 1st day of the month"""
        print(f"📊 Starting monthly report generation at {datetime.now()}")

        db = SessionLocal()
        try:
            # Get all users with monthly reports enabled
            preferences = db.query(UserReportPreferences).filter(
                UserReportPreferences.frequency == "monthly",
                UserReportPreferences.send_email == True
            ).all()

            # Also send to all active users (fallback)
            if not preferences:
                # Get all users who have entries in the last 30 days
                all_users = db.query(User).all()
                print(f"📧 Sending monthly reports to all {len(all_users)} active users")

                for user in all_users:
                    try:
                        await self._send_monthly_report_to_user(db, user.id)
                    except Exception as e:
                        print(f"❌ Error sending monthly report to user {user.id}: {e}")
            else:
                print(f"📧 Found {len(preferences)} users to send monthly reports to")

                for pref in preferences:
                    try:
                        await self._send_monthly_report_to_user(db, pref.user_id)
                    except Exception as e:
                        print(f"❌ Error sending monthly report to user {pref.user_id}: {e}")

            print(f"✅ Monthly reports sent successfully")

        except Exception as e:
            print(f"❌ Error in monthly report job: {e}")
        finally:
            db.close()

    async def send_custom_reports(self):
        """Send reports based on custom user preferences"""
        print(f"📊 Checking custom report schedules at {datetime.now()}")
        
        db = SessionLocal()
        try:
            today = datetime.now()
            current_weekday = today.weekday()
            current_hour = today.hour
            
            # Get users with custom schedules matching today
            preferences = db.query(UserReportPreferences).filter(
                UserReportPreferences.send_email == True,
                UserReportPreferences.email_day_of_week == current_weekday,
                UserReportPreferences.email_hour == current_hour
            ).all()
            
            for pref in preferences:
                try:
                    # Check frequency
                    if await self._should_send_report(db, pref):
                        await self._send_report_to_user(db, pref.user_id)
                except Exception as e:
                    print(f"❌ Error sending custom report to user {pref.user_id}: {e}")
            
        except Exception as e:
            print(f"❌ Error in custom report job: {e}")
        finally:
            db.close()
    
    async def _send_report_to_user(self, db: Session, user_id: int):
        """Generate and send report to a specific user"""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"⚠️  User {user_id} not found")
            return
        
        # Generate report
        report_service = WeeklyReportService(db)
        report = report_service.generate_weekly_report(user_id)
        
        # Save to database
        week_start = date.fromisoformat(report['period']['start'])
        week_end = date.fromisoformat(report['period']['end'])
        
        # Check if already exists
        existing = db.query(WeeklyReport).filter(
            WeeklyReport.user_id == user_id,
            WeeklyReport.week_start == week_start
        ).first()
        
        if not existing:
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
        
        # Send email
        try:
            await email_service.send_weekly_report_email(
                user.email,
                user.full_name or user.email,
                report
            )
            
            # Mark as sent
            report_record = existing or new_report
            report_record.is_sent_via_email = True
            report_record.email_sent_at = datetime.utcnow()
            db.commit()
            
            print(f"✅ Sent weekly report to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send email to {user.email}: {e}")
    
    async def _send_monthly_report_to_user(self, db: Session, user_id: int):
        """Generate and send monthly report to a specific user"""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"⚠️  User {user_id} not found")
            return

        # Generate monthly report for previous month
        today = datetime.now()
        if today.month == 1:
            prev_month = date(today.year - 1, 12, 1)
        else:
            prev_month = date(today.year, today.month - 1, 1)

        # Generate report
        report_service = MonthlyReportService(db)
        report = report_service.generate_monthly_report(user_id, prev_month)

        # Send email
        try:
            await email_service.send_monthly_report_email(
                user.email,
                user.full_name or user.email,
                report
            )

            print(f"✅ Sent monthly report to {user.email}")

        except Exception as e:
            print(f"❌ Failed to send monthly report email to {user.email}: {e}")

    async def _should_send_report(self, db: Session, pref: UserReportPreferences) -> bool:
        """Check if report should be sent based on frequency"""
        # Get last sent report
        last_report = db.query(WeeklyReport).filter(
            WeeklyReport.user_id == pref.user_id,
            WeeklyReport.is_sent_via_email == True
        ).order_by(WeeklyReport.created_at.desc()).first()

        if not last_report:
            return True  # First report

        days_since_last = (date.today() - last_report.week_start).days

        # Check frequency
        if pref.frequency == "weekly" and days_since_last >= 7:
            return True
        elif pref.frequency == "biweekly" and days_since_last >= 14:
            return True
        elif pref.frequency == "monthly" and days_since_last >= 30:
            return True

        return False


# Global scheduler instance
report_scheduler = ReportScheduler()

