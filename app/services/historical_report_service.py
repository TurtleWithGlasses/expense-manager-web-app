"""
Historical Report Service

Manages saving and retrieving historical financial reports.
"""

import json
from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.historical_report import HistoricalReport


class HistoricalReportService:
    """Service for managing historical report storage and retrieval"""

    def __init__(self, db: Session):
        self.db = db

    def save_report(
        self,
        user_id: int,
        report_type: str,
        report_period: str,
        period_start: date,
        period_end: date,
        report_data: Dict,
        currency_code: str = 'USD'
    ) -> HistoricalReport:
        """
        Save a generated report to historical storage

        Args:
            user_id: User ID
            report_type: Type of report ('weekly', 'monthly', 'annual')
            report_period: Period identifier ('2024-W45', '2024-10', '2024')
            period_start: Start date of report period
            period_end: End date of report period
            report_data: Complete report data dictionary
            currency_code: Currency used in report

        Returns:
            HistoricalReport object
        """
        # Calculate summary metrics (convert to cents for storage)
        summary = report_data.get('summary', {})
        total_income = int((summary.get('total_income', 0) or 0) * 100)
        total_expenses = int((summary.get('total_expenses', 0) or 0) * 100)
        net_savings = int((summary.get('net_savings', 0) or 0) * 100)
        transaction_count = summary.get('transaction_count', 0) or 0

        # Check if report already exists for this period
        existing = self.db.query(HistoricalReport).filter(
            and_(
                HistoricalReport.user_id == user_id,
                HistoricalReport.report_type == report_type,
                HistoricalReport.report_period == report_period
            )
        ).first()

        if existing:
            # Update existing report
            existing.report_data = json.dumps(report_data)
            existing.total_income = total_income
            existing.total_expenses = total_expenses
            existing.net_savings = net_savings
            existing.transaction_count = transaction_count
            existing.currency_code = currency_code
            existing.generated_at = datetime.utcnow()
            existing.period_start = period_start
            existing.period_end = period_end
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new report
            report = HistoricalReport(
                user_id=user_id,
                report_type=report_type,
                report_period=report_period,
                period_start=period_start,
                period_end=period_end,
                report_data=json.dumps(report_data),
                total_income=total_income,
                total_expenses=total_expenses,
                net_savings=net_savings,
                transaction_count=transaction_count,
                currency_code=currency_code
            )
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            return report

    def get_report(
        self,
        user_id: int,
        report_type: str,
        report_period: str
    ) -> Optional[Dict]:
        """
        Retrieve a specific historical report

        Args:
            user_id: User ID
            report_type: Type of report ('weekly', 'monthly', 'annual')
            report_period: Period identifier

        Returns:
            Report data dictionary or None if not found
        """
        report = self.db.query(HistoricalReport).filter(
            and_(
                HistoricalReport.user_id == user_id,
                HistoricalReport.report_type == report_type,
                HistoricalReport.report_period == report_period
            )
        ).first()

        if report:
            data = json.loads(report.report_data)
            # Add metadata
            data['_metadata'] = {
                'generated_at': report.generated_at.isoformat(),
                'is_historical': True,
                'report_id': report.id
            }
            return data
        return None

    def list_reports(
        self,
        user_id: int,
        report_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List historical reports for a user

        Args:
            user_id: User ID
            report_type: Optional filter by report type
            limit: Maximum number of reports to return

        Returns:
            List of report summary dictionaries
        """
        query = self.db.query(HistoricalReport).filter(
            HistoricalReport.user_id == user_id
        )

        if report_type:
            query = query.filter(HistoricalReport.report_type == report_type)

        reports = query.order_by(desc(HistoricalReport.period_end)).limit(limit).all()

        return [
            {
                'id': r.id,
                'report_type': r.report_type,
                'report_period': r.report_period,
                'period_start': r.period_start.isoformat(),
                'period_end': r.period_end.isoformat(),
                'total_income': r.total_income / 100.0,  # Convert back from cents
                'total_expenses': r.total_expenses / 100.0,
                'net_savings': r.net_savings / 100.0,
                'transaction_count': r.transaction_count,
                'currency_code': r.currency_code,
                'generated_at': r.generated_at.isoformat()
            }
            for r in reports
        ]

    def delete_report(
        self,
        user_id: int,
        report_id: int
    ) -> bool:
        """
        Delete a historical report

        Args:
            user_id: User ID (for security)
            report_id: Report ID to delete

        Returns:
            True if deleted, False if not found
        """
        report = self.db.query(HistoricalReport).filter(
            and_(
                HistoricalReport.id == report_id,
                HistoricalReport.user_id == user_id
            )
        ).first()

        if report:
            self.db.delete(report)
            self.db.commit()
            return True
        return False

    def get_available_periods(
        self,
        user_id: int,
        report_type: str
    ) -> List[str]:
        """
        Get list of available report periods for a user

        Args:
            user_id: User ID
            report_type: Type of report ('weekly', 'monthly', 'annual')

        Returns:
            List of period identifiers sorted by most recent first
        """
        reports = self.db.query(HistoricalReport.report_period).filter(
            and_(
                HistoricalReport.user_id == user_id,
                HistoricalReport.report_type == report_type
            )
        ).order_by(desc(HistoricalReport.period_end)).all()

        return [r[0] for r in reports]
