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
from app.models.recurring_payment import RecurringPayment, RecurrenceFrequency
from app.models.payment_history import PaymentOccurrence
from app.models.entry import Entry


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

        # Schedule daily recurring payment processing - Every day at 1 AM
        self.scheduler.add_job(
            self.process_recurring_payments,
            CronTrigger(hour=1, minute=0),
            id='process_recurring_payments',
            name='Process Due Recurring Payments',
            replace_existing=True
        )

        # Schedule automatic ML model retraining - Every day at 2 AM
        self.scheduler.add_job(
            self.auto_retrain_models,
            CronTrigger(hour=2, minute=0),
            id='auto_retrain_models',
            name='Automatic ML Model Retraining',
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

        # Calculate previous week's end date (last Sunday)
        # Today is Monday, so previous Sunday is yesterday
        today = date.today()
        previous_sunday = today - timedelta(days=1)

        # Generate report for the previous week (Monday to Sunday)
        report_service = WeeklyReportService(db)
        report = report_service.generate_weekly_report(user_id, week_end_date=previous_sunday)
        
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

    async def process_recurring_payments(self):
        """Process recurring payments and auto-add to expenses if due today.

        Duplicate prevention: checks PaymentOccurrence for (recurring_payment_id, scheduled_date)
        before creating a new entry so we never double-post the same bill on the same day.
        """
        print(f"💰 Processing recurring payments at {datetime.now()}")

        db = SessionLocal()
        try:
            today = date.today()

            # Get all active recurring payments with auto-add enabled
            payments = db.query(RecurringPayment).filter(
                RecurringPayment.is_active == True,
                RecurringPayment.auto_add_to_expenses == True
            ).all()

            print(f"📋 Found {len(payments)} payments with auto-add enabled")
            created = skipped = errors = 0

            for payment in payments:
                try:
                    # Check if payment is due today
                    if not self._is_payment_due_today(payment, today):
                        continue

                    # Duplicate check via PaymentOccurrence (source of truth)
                    already_processed = db.query(PaymentOccurrence).filter(
                        PaymentOccurrence.recurring_payment_id == payment.id,
                        PaymentOccurrence.scheduled_date == today
                    ).first()

                    if already_processed:
                        print(f"⏭️  Skipping '{payment.name}' - PaymentOccurrence already exists for {today}")
                        skipped += 1
                        continue

                    # Create the expense entry
                    new_entry = Entry(
                        user_id=payment.user_id,
                        category_id=payment.category_id,
                        type="expense",
                        amount=payment.amount,
                        currency_code=payment.currency_code,
                        date=today,
                        description=f"{payment.name} (Auto-added)"
                    )
                    db.add(new_entry)
                    db.flush()  # Get new_entry.id before creating occurrence

                    # Record the occurrence so we never re-process this bill today
                    occurrence = PaymentOccurrence(
                        user_id=payment.user_id,
                        recurring_payment_id=payment.id,
                        scheduled_date=today,
                        actual_date=today,
                        amount=payment.amount,
                        currency_code=payment.currency_code,
                        is_paid=True,
                        linked_entry_id=new_entry.id,
                        note="Auto-added by scheduler",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        paid_at=datetime.utcnow()
                    )
                    db.add(occurrence)
                    db.commit()

                    print(f"✅ Auto-added '{payment.name}' — {payment.currency_code} {payment.amount} (entry #{new_entry.id})")
                    created += 1

                except Exception as e:
                    print(f"❌ Error processing payment '{payment.name}': {e}")
                    db.rollback()
                    errors += 1

            print(f"✅ Recurring payments done: {created} created, {skipped} skipped, {errors} errors")

        except Exception as e:
            print(f"❌ Error in recurring payments job: {e}")
        finally:
            db.close()

    def _is_payment_due_today(self, payment: RecurringPayment, today: date) -> bool:
        """Check if a recurring payment is due today"""
        # Check if payment has ended
        if payment.end_date and today > payment.end_date:
            return False

        # Check if payment hasn't started yet
        if today < payment.start_date:
            return False

        # Check based on frequency
        if payment.frequency == RecurrenceFrequency.WEEKLY:
            # due_day is day of week (0 = Monday, 6 = Sunday)
            return today.weekday() == payment.due_day

        elif payment.frequency == RecurrenceFrequency.BIWEEKLY:
            # Check if today is the due day of week
            if today.weekday() != payment.due_day:
                return False
            # Check if it's been 2 weeks since start_date
            days_since_start = (today - payment.start_date).days
            weeks_since_start = days_since_start // 7
            return weeks_since_start % 2 == 0

        elif payment.frequency == RecurrenceFrequency.MONTHLY:
            # due_day is day of month (1-31)
            return today.day == payment.due_day

        elif payment.frequency == RecurrenceFrequency.QUARTERLY:
            # Check if this month is a quarter month (1, 4, 7, 10)
            # and today is the due day
            quarter_months = [1, 4, 7, 10]
            return today.month in quarter_months and today.day == payment.due_day

        elif payment.frequency == RecurrenceFrequency.ANNUALLY:
            # Check if today matches the start date's month and day
            return (today.month == payment.start_date.month and
                   today.day == payment.due_day)

        return False

    async def auto_retrain_models(self):
        """
        Automatically retrain ML models for users based on their preferences

        This job runs daily at 2 AM and checks each user's model to see if it needs
        retraining based on:
        1. User's retrain_frequency_days preference
        2. Amount of new data since last training
        """
        print("🤖 Starting automatic model retraining check...")

        db = SessionLocal()
        try:
            from app.services.ai_service import AICategorizationService
            from app.models.ai_model import AIModel

            # Get all users who have trained models
            ai_models = db.query(AIModel).all()

            retrained_count = 0
            skipped_count = 0

            for ai_model in ai_models:
                try:
                    ai_service = AICategorizationService(db)

                    # Get model status to check if retraining is needed
                    status = ai_service.get_model_status(ai_model.user_id)

                    if status.get('needs_retraining', False):
                        user = db.query(User).filter(User.id == ai_model.user_id).first()
                        if not user:
                            continue

                        print(f"🔄 Retraining model for user {user.email}...")

                        # Trigger retraining
                        result = ai_service.retrain_model(ai_model.user_id)

                        if result['success']:
                            retrained_count += 1
                            accuracy = result['results']['accuracy']
                            samples = result['results']['training_samples']
                            print(f"  ✅ Success! Accuracy: {accuracy*100:.1f}%, Samples: {samples}")
                        else:
                            print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")
                    else:
                        skipped_count += 1

                except Exception as e:
                    print(f"  ❌ Error processing model for user {ai_model.user_id}: {e}")
                    continue

            print(f"🎯 Automatic retraining completed: {retrained_count} retrained, {skipped_count} skipped")

        except Exception as e:
            print(f"❌ Error in auto_retrain_models: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()


# Global scheduler instance
report_scheduler = ReportScheduler()

