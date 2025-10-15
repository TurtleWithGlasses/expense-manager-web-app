from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.report_status import ReportStatus


class ReportStatusService:
    def __init__(self, db: Session):
        self.db = db
    
    def mark_report_as_new(self, user_id: int, report_type: str, report_period: str = "current"):
        """Mark a report as new (when expenses are added)"""
        existing = self.db.query(ReportStatus).filter(
            and_(
                ReportStatus.user_id == user_id,
                ReportStatus.report_type == report_type,
                ReportStatus.report_period == report_period
            )
        ).first()
        
        if existing:
            existing.is_new = True
            existing.last_updated = datetime.utcnow()
        else:
            new_status = ReportStatus(
                user_id=user_id,
                report_type=report_type,
                report_period=report_period,
                is_new=True
            )
            self.db.add(new_status)
        
        self.db.commit()
    
    def mark_report_as_viewed(self, user_id: int, report_type: str, report_period: str = "current"):
        """Mark a report as viewed"""
        existing = self.db.query(ReportStatus).filter(
            and_(
                ReportStatus.user_id == user_id,
                ReportStatus.report_type == report_type,
                ReportStatus.report_period == report_period
            )
        ).first()
        
        if existing:
            existing.is_new = False
            existing.last_viewed = datetime.utcnow()
            existing.last_updated = datetime.utcnow()
        else:
            new_status = ReportStatus(
                user_id=user_id,
                report_type=report_type,
                report_period=report_period,
                is_new=False,
                last_viewed=datetime.utcnow()
            )
            self.db.add(new_status)
        
        self.db.commit()
    
    def get_report_status(self, user_id: int, report_type: str, report_period: str = "current") -> dict:
        """Get the status of a specific report"""
        status = self.db.query(ReportStatus).filter(
            and_(
                ReportStatus.user_id == user_id,
                ReportStatus.report_type == report_type,
                ReportStatus.report_period == report_period
            )
        ).first()
        
        if status:
            return {
                "is_new": status.is_new,
                "last_viewed": status.last_viewed,
                "last_updated": status.last_updated
            }
        else:
            # If no status exists, consider it new
            return {
                "is_new": True,
                "last_viewed": None,
                "last_updated": None
            }
    
    def get_all_report_statuses(self, user_id: int) -> dict:
        """Get status for all report types"""
        statuses = {}
        report_types = ["weekly", "monthly", "annual"]
        
        for report_type in report_types:
            statuses[report_type] = self.get_report_status(user_id, report_type)
        
        return statuses
    
    def mark_all_reports_as_new(self, user_id: int):
        """Mark all reports as new (when new expenses are added)"""
        report_types = ["weekly", "monthly", "annual"]
        for report_type in report_types:
            self.mark_report_as_new(user_id, report_type)
